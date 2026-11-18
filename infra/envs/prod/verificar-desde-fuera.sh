#!/usr/bin/env bash
#
# verificar-desde-fuera.sh — CanastaMX (T054 · #201)
#
# Revisa el despliegue como lo ve cualquiera desde internet, con los criterios de
# #201: que la web, el dominio y la interfaz analítica contesten por HTTPS con un
# certificado válido, que las cuentas ANALISTA y OPERADOR de la semilla inicien
# sesión, que haya datos, y que ninguna base, MinIO ni Dagster se alcance desde
# fuera.
#
# Córrelo desde una computadora que NO sea la VM y desde una red que no sea la de
# nadie del equipo (por ejemplo, con los datos del teléfono). No lee ningún .env.
#
# Uso, desde la raíz del repositorio:
#   bash infra/envs/prod/verificar-desde-fuera.sh canastamx.duckdns.org
#
# Pide la contraseña de las cuentas semilla sin mostrarla. Nunca imprime la
# contraseña ni los tokens. Necesita curl y python3.
#
# Sale con 1 si algo falló.

set -uo pipefail

DIRECCION=${1:-}
if [[ -z "$DIRECCION" || "$DIRECCION" == http* || "$DIRECCION" == */* ]]; then
  echo "Uso: bash $0 <dirección pública, sin https:// ni barra>   p. ej. canastamx.duckdns.org" >&2
  exit 2
fi
for programa in curl python3; do
  command -v "$programa" >/dev/null || { echo "Falta $programa." >&2; exit 2; }
done

WEB="$DIRECCION"
DOMINIO="dominio.$DIRECCION"
ANALITICA="analitica.$DIRECCION"
# Los puertos que NO deben contestar desde fuera: las dos bases (también los de
# pruebas), los servicios directos, MinIO, Dagster, Adminer y el panel de Traefik.
CERRADOS=(5432 5433 5442 5443 8000 8081 9000 9001 9010 9011 3000 8080 8090)

TEMPORAL=$(mktemp -d)
trap 'rm -rf "$TEMPORAL"' EXIT
FALLAS=0
ok()  { printf '  ✓ %s\n' "$*"; }
mal() { printf '  ✗ %s\n' "$*"; FALLAS=$((FALLAS + 1)); }

# pedir MÉTODO URL [cuerpo-json]: deja la respuesta en $TEMPORAL/cuerpo e imprime
# el código HTTP, o «000» si no hubo respuesta.
pedir() {
  local metodo=$1 url=$2
  local argumentos=(-sS -o "$TEMPORAL/cuerpo" -w '%{http_code}' --max-time 25 -X "$metodo")
  if [[ $# -ge 3 ]]; then
    argumentos+=(-H 'Content-Type: application/json' --data-binary @-)
    printf '%s' "$3" | curl "${argumentos[@]}" "$url" 2>"$TEMPORAL/error"
  else
    curl "${argumentos[@]}" "$url" 2>"$TEMPORAL/error"
  fi
}
campo() {   # campo NOMBRE: un campo del JSON de la última respuesta, o vacío
  python3 -c 'import json, sys
try:
    valor = json.load(open(sys.argv[1])).get(sys.argv[2], "")
except Exception:
    valor = ""
print(len(valor) if isinstance(valor, list) else valor)' "$TEMPORAL/cuerpo" "$1"
}
por_que() { tr '\n' ' ' < "$TEMPORAL/error" | cut -c1-160; }

echo "Despliegue de CanastaMX en $DIRECCION · $(date '+%Y-%m-%d %H:%M %Z')"

# ── 1 · Los nombres apuntan a la VM ──────────────────────────────────────────
echo
echo "Nombres"
for nombre in "$WEB" "$DOMINIO" "$ANALITICA"; do
  ip=$(python3 -c 'import socket, sys; print(socket.gethostbyname(sys.argv[1]))' "$nombre" 2>/dev/null)
  if [[ -n "$ip" ]]; then ok "$nombre → $ip"; else mal "$nombre no resuelve a ninguna IP"; fi
done

# ── 2 · HTTPS con certificado válido ─────────────────────────────────────────
echo
echo "Certificados (verificados contra las autoridades del sistema)"
for nombre in "$WEB" "$DOMINIO" "$ANALITICA"; do
  if salida=$(python3 - "$nombre" 2>&1 <<'PY'
import socket, ssl, sys
nombre = sys.argv[1]
contexto = ssl.create_default_context()
try:
    with socket.create_connection((nombre, 443), timeout=20) as s:
        with contexto.wrap_socket(s, server_hostname=nombre) as t:
            cert = t.getpeercert()
except (OSError, ssl.SSLError) as e:
    print(str(e)[:160])
    sys.exit(1)
emisor = dict(par[0] for par in cert["issuer"])
print(f'{emisor.get("organizationName", "?")} · {emisor.get("commonName", "?")} · vence {cert["notAfter"]}')
PY
  ); then ok "$nombre: $salida"; else mal "$nombre: $salida"; fi
done
codigo=$(pedir GET "http://$WEB/")
destino=$(curl -sS -o /dev/null -w '%{redirect_url}' --max-time 20 "http://$WEB/" 2>/dev/null)
if [[ "$codigo" =~ ^30[1278]$ && "$destino" == https://* ]]; then
  ok "http://$WEB/ manda a HTTPS ($codigo)"
else
  mal "http://$WEB/ no manda a HTTPS (respondió $codigo $destino) $(por_que)"
fi

# ── 3 · Cada servicio contesta ───────────────────────────────────────────────
echo
echo "Servicios"
codigo=$(pedir GET "https://$WEB/acceso")
if [[ "$codigo" == 200 ]]; then ok "web: https://$WEB/acceso → 200"; else mal "web: https://$WEB/acceso → $codigo $(por_que)"; fi

codigo=$(pedir POST "https://$DOMINIO/api/v1/sesiones" '{"correo":"nadie@canastamx.mx","contrasena":"NoEsLaClave1"}')
if [[ "$codigo" == 401 ]]; then
  ok "dominio: una sesión con credenciales falsas → 401, como debe"
else
  mal "dominio: una sesión con credenciales falsas → $codigo (se esperaba 401) $(por_que)"
fi

codigo=$(pedir GET "https://$ANALITICA/health")
if [[ "$codigo" == 200 && "$(campo service)" == analytics-api ]]; then
  ok "interfaz analítica: https://$ANALITICA/health → 200"
else
  mal "interfaz analítica: https://$ANALITICA/health → $codigo $(por_que)"
fi

# ── 4 · Hay datos ────────────────────────────────────────────────────────────
echo
echo "Datos"
codigo=$(pedir GET "https://$ANALITICA/api/v1/entidades")
entidades=$(campo entidades)
if [[ "$codigo" == 200 && "${entidades:-0}" -gt 0 ]]; then
  ok "la capa intermedia tiene datos: $entidades entidades en /api/v1/entidades"
else
  mal "/api/v1/entidades → $codigo con ${entidades:-0} entidades: ¿ya se procesaron los lotes?"
fi

# ── 5 · Las cuentas de la semilla inician sesión ─────────────────────────────
echo
echo "Cuentas semilla"
CLAVE=""
if [[ -t 0 ]]; then
  read -rsp "  Contraseña de las cuentas semilla (no se muestra): " CLAVE; echo
else
  read -r CLAVE
fi
for par in "analista@canastamx.mx:ANALISTA" "operador@canastamx.mx:OPERADOR"; do
  correo=${par%%:*}; rol=${par##*:}
  cuerpo=$(CORREO="$correo" CLAVE="$CLAVE" python3 -c 'import json, os
print(json.dumps({"correo": os.environ["CORREO"], "contrasena": os.environ["CLAVE"]}))')
  codigo=$(pedir POST "https://$DOMINIO/api/v1/sesiones" "$cuerpo")
  if [[ "$codigo" == 200 && "$(campo rol)" == "$rol" ]]; then
    ok "$correo inicia sesión en el dominio: $rol"
  else
    mal "$correo en el dominio → $codigo (rol «$(campo rol)»)"
  fi
  codigo=$(pedir POST "https://$WEB/api/login" "$cuerpo")
  if [[ "$codigo" == 200 && "$(campo rol)" == "$rol" ]]; then
    ok "$correo inicia sesión en la web: $rol → $(campo destino)"
  else
    mal "$correo en la web → $codigo (rol «$(campo rol)»)"
  fi
done
unset CLAVE cuerpo

# ── 6 · Las bases, MinIO y Dagster no se alcanzan desde fuera ────────────────
echo
echo "Puertos que no deben contestar"
abiertos=$(python3 - "$WEB" "${CERRADOS[@]}" <<'PY'
import socket, sys
nombre, puertos = sys.argv[1], [int(p) for p in sys.argv[2:]]
abiertos = []
for puerto in puertos:
    with socket.socket() as s:
        s.settimeout(3)
        if s.connect_ex((nombre, puerto)) == 0:
            abiertos.append(str(puerto))
print(" ".join(abiertos))
PY
)
if [[ -z "$abiertos" ]]; then
  ok "ninguno de ${CERRADOS[*]} contesta"
else
  mal "contestan desde fuera: $abiertos"
fi

echo
if [[ $FALLAS -eq 0 ]]; then
  echo "OK: el despliegue cumple lo que se revisa desde fuera."
else
  echo "FALLÓ: $FALLAS revisión(es). Ver infra/envs/prod/README.md, «Si algo falla»."
fi
[[ $FALLAS -eq 0 ]]
