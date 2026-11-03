#!/usr/bin/env bash
#
# sembrar-cuentas.sh — CanastaMX
#
# Crea una cuenta ANALISTA y una OPERADOR en la base transaccional, porque la
# app sólo registra cuentas CONSUMIDOR. Se puede correr las veces que haga falta:
# si el correo ya existe, no hace nada (ON CONFLICT DO NOTHING).
#
# La contraseña sale de SEMILLA_CONTRASENA en el .env que corresponda. Nunca se
# imprime, ni va en la línea de órdenes (se vería en `ps`): viaja por la entrada
# estándar, codificada en Base64 sólo para no tener que escapar comillas.
#
# Uso, desde la raíz del repositorio:
#   bash infra/scripts/sembrar-cuentas.sh           # docker-compose.yml y .env de la raíz
#   bash infra/scripts/sembrar-cuentas.sh --test    # infra/envs/test/
#
# Requisitos: el servicio postgres-oltp arriba y la tabla usuario creada. La
# tabla la crea Flyway al arrancar el dominio o sus pruebas; este guion no
# agrega migraciones.
#
# Si cambias SEMILLA_CONTRASENA después de sembrar, las cuentas existentes
# conservan la anterior: este guion no las actualiza.

set -euo pipefail

CUENTAS_SQL="('analista@canastamx.mx', 'ANALISTA'), ('operador@canastamx.mx', 'OPERADOR')"

[[ -d .git ]] || { echo "Córrelo desde la raíz del repositorio." >&2; exit 1; }

case "${1:-}" in
  "")     COMPOSE=(docker compose);                                  ENV_FILE=".env" ;;
  --test) COMPOSE=(docker compose -f infra/envs/test/docker-compose.yml)
          ENV_FILE="infra/envs/test/.env" ;;
  *)      echo "Uso: bash $0 [--test]" >&2; exit 2 ;;
esac

[[ -f "$ENV_FILE" ]] || { echo "No existe $ENV_FILE. Copia su .env.example y complétalo." >&2; exit 1; }

# ── La contraseña: se lee del archivo sin ejecutarlo (nada de `source`) ───────
CLAVE=$(grep -m1 '^SEMILLA_CONTRASENA=' "$ENV_FILE" | cut -d= -f2- | tr -d '\r' || true)
if [[ -z "$CLAVE" ]]; then
  echo "SEMILLA_CONTRASENA está vacía o falta en $ENV_FILE. Complétala y vuelve a correrlo." >&2
  exit 1
fi
# Misma regla que RegistroCuentaService: 8 caracteres, una mayúscula y un número.
if [[ ${#CLAVE} -lt 8 || ! "$CLAVE" =~ [A-Z] || ! "$CLAVE" =~ [0-9] ]]; then
  echo "SEMILLA_CONTRASENA debe tener al menos 8 caracteres, una mayúscula y un número." >&2
  exit 1
fi
CLAVE_B64=$(printf '%s' "$CLAVE" | base64 | tr -d '\n')
unset CLAVE

# psql dentro del contenedor; POSTGRES_USER y POSTGRES_DB ya traen OLTP_USER y OLTP_DB.
psql_oltp() {
  "${COMPOSE[@]}" exec -T postgres-oltp sh -c \
    'exec psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 "$@"' sh "$@"
}

# ── ¿Hay base y tabla? ────────────────────────────────────────────────────────
EXISTE=$(psql_oltp -tAc "SELECT to_regclass('public.usuario') IS NOT NULL" </dev/null) || {
  echo "No pude entrar a postgres-oltp. ¿Está arriba? Prueba: ${COMPOSE[*]} up -d postgres-oltp" >&2
  exit 1
}
if [[ "$EXISTE" != "t" ]]; then
  echo "La tabla usuario no existe todavía. Primero hay que correr el dominio" >&2
  echo "(./mvnw spring-boot:run) o sus pruebas (./mvnw test) en services/domain-service:" >&2
  echo "Flyway la crea con V1__crear_usuario.sql." >&2
  exit 1
fi

# ── Siembra ───────────────────────────────────────────────────────────────────
# El primer renglón le da a psql la contraseña ya codificada; el SELECT ... \gset
# la decodifica en :clave, y el INSERT la usa con crypt(:'clave', gen_salt('bf', 10)).
# bf produce $2a$..., que BCryptPasswordEncoder acepta y el dominio exige ($2).
INSERTADAS=$(
  {
    printf "\\\\set clave_b64 '%s'\n" "$CLAVE_B64"
    cat <<SQL
SET client_min_messages = warning;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
SELECT convert_from(decode(:'clave_b64', 'base64'), 'UTF8') AS clave \\gset
INSERT INTO usuario (id, correo_electronico, contrasena_hash, rol)
SELECT gen_random_uuid()::text, v.correo, crypt(:'clave', gen_salt('bf', 10)), v.rol
FROM (VALUES $CUENTAS_SQL) AS v(correo, rol)
ON CONFLICT (correo_electronico) DO NOTHING
RETURNING correo_electronico || ' (' || rol || ')';
SQL
  } | psql_oltp -q -tA
)

if [[ -n "$INSERTADAS" ]]; then
  echo "Cuentas creadas:"
  echo "$INSERTADAS" | sed 's/^/  · /'
else
  echo "Las cuentas ya existían; no se cambió nada."
fi
