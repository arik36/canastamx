#!/usr/bin/env bash
# ============================================================
# CanastaMX — creacion de la estructura del monorepo
#
# Lo corre B una sola vez, DENTRO DE WSL, con:
#   bash bootstrap.sh
#
# Antes de correrlo, coloca .gitattributes y .gitignore en la
# misma carpeta que este script.
# ============================================================
set -euo pipefail

echo "==> Creando estructura de carpetas"

DIRS=(
  ".github/workflows"
  "docs/adr"
  "docs/analisis/casos-uso"
  "docs/analisis/openapi"
  "docs/datos/perfilado"
  "docs/experimento"
  "docs/entregas"
  "contracts"
  "services/data-platform/ingestion"
  "services/data-platform/dbt"
  "services/data-platform/tests/fixtures"
  "services/analytics-api"
  "services/domain-service"
  "clients/web"
  "clients/mobile"
  "packages/types"
  "infra/traefik"
  "infra/envs"
  "infra/scripts"
)

for d in "${DIRS[@]}"; do
  mkdir -p "$d"
  # .gitkeep para que Git conserve la carpeta vacia
  [ -z "$(ls -A "$d" 2>/dev/null)" ] && touch "$d/.gitkeep"
done

echo "==> Escribiendo README.md"
cat > README.md <<'MARKDOWN'
# CanastaMX

Plataforma de inteligencia de precios de canasta basica con validacion
automatica de calidad de datos.

## Que hace

Toma los datos publicos de precios de PROFECO, los procesa mediante un flujo
con contratos de datos y compuertas de calidad, y los expone a tres perfiles:
consumidor (movil), analista (web) y operador de datos (consola de
observabilidad).

Cuando llega un dato defectuoso, el sistema lo bloquea, lo aisla en una tabla
de cuarentena con el motivo y senala el incidente. No lo deja pasar.

## Arquitectura

Cuatro componentes desplegables de forma independiente detras de un gateway:

| Componente | Ruta | Stack | Responsable |
|---|---|---|---|
| Plataforma de datos | `services/data-platform` | Python, Dagster, dbt, Pandera | A |
| Interfaz analitica | `services/analytics-api` | Python, FastAPI | A |
| Servicio de dominio | `services/domain-service` | Java 21, Spring Boot | C |
| Cliente web | `clients/web` | Next.js, TypeScript | D |
| Cliente movil | `clients/mobile` | React Native, Expo | C |
| Infraestructura | `infra/`, `docker-compose.yml` | Docker, Traefik, GH Actions | B |

## Como levantarlo

Requisitos: Docker Desktop y Git. En Windows, Docker Desktop con backend WSL2.

```bash
git clone <url-del-repo>
cd canastamx
cp .env.example .env     # completa los valores
docker compose up -d
```

Servicios disponibles despues del arranque:

| Servicio | URL |
|---|---|
| MinIO (consola) | http://localhost:9001 |
| Adminer (bases de datos) | http://localhost:8080 |

> Esta seccion se verifica de verdad: alguien que no sea B clona en una
> maquina limpia y sigue estos pasos sin preguntar nada. Si se atora, el
> README esta incompleto.

## Estructura del repositorio

```
docs/         documentacion tecnica (Markdown, no Word)
contracts/    contratos de datos en YAML
services/     los tres servicios de backend
clients/      web y movil
packages/     codigo compartido entre clientes
infra/        contenedores, gateway, scripts de operacion
```

## Convenciones

- Ramas: `tipo/iniciales-descripcion-corta` (ej. `feat/alm-ingesta-profeco`)
- Commits: `tipo(ambito): descripcion en presente`
- Nadie escribe directo en `main`. Todo entra por PR con una aprobacion.
- Decisiones tecnicas: un archivo corto en `docs/adr/`.

## Equipo

| | Integrante | Rol |
|---|---|---|
| A | Macias Campos Ariadne Lizett | Datos y plataforma |
| B | (por definir) | Infraestructura, entrega continua y calidad |
| C | (por definir) | Dominio y cliente movil |
| D | (por definir) | Cliente web y maquetacion |

## Fuentes de datos

- PROFECO — Quien es Quien en los Precios: https://datos.profeco.gob.mx
- INEGI — Indice Nacional de Precios al Consumidor

## Documentacion

- Tecnica: carpeta `docs/`
- Entregas y presentaciones: (enlace al Drive compartido)
MARKDOWN

echo "==> Escribiendo .env.example"
cat > .env.example <<'ENVFILE'
# Copia este archivo como .env y completa los valores.
# .env NUNCA se sube al repositorio.

# --- PostgreSQL transaccional (servicio de dominio) ---
OLTP_DB=canastamx_oltp
OLTP_USER=canastamx
OLTP_PASSWORD=
OLTP_PORT=5432

# --- PostgreSQL analitico (capas silver, gold, cuarentena) ---
ANALYTICS_DB=canastamx_analytics
ANALYTICS_USER=canastamx
ANALYTICS_PASSWORD=
ANALYTICS_PORT=5433

# --- MinIO (capa bronze) ---
MINIO_ROOT_USER=
MINIO_ROOT_PASSWORD=
MINIO_BUCKET=canastamx-bronze

# --- Servicio de dominio ---
JWT_SECRET=
JWT_EXPIRATION_MINUTES=60

# --- Fuentes externas ---
INEGI_API_TOKEN=
ENVFILE

echo "==> Inicializando Git"
if [ ! -d .git ]; then
  git init -b main
fi

# .gitattributes debe entrar en el primer commit
if [ ! -f .gitattributes ]; then
  echo "!! FALTA .gitattributes. Colocalo aqui antes de continuar." >&2
  exit 1
fi

git config core.autocrlf false

git add .gitattributes .gitignore README.md .env.example
git add -A
git commit -m "chore: estructura inicial del monorepo y convenciones de Git"

echo ""
echo "==> Listo. Siguientes pasos:"
echo "    1. Crea el repositorio 'canastamx' PRIVADO en GitHub (sin README)."
echo "    2. git remote add origin git@github.com:<org-o-usuario>/canastamx.git"
echo "    3. git push -u origin main"
echo "    4. En GitHub: Settings > Branches > proteger 'main'"
echo "       (requerir PR y una aprobacion)."
echo "    5. Invita a los otros tres como colaboradores."
