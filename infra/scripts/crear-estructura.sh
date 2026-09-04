#!/usr/bin/env bash
#
# crear-estructura.sh — CanastaMX
#
# Crea la estructura de carpetas del monorepo. Cada carpeta lleva un .gitkeep
# adentro, porque Git no versiona carpetas vacías.
#
# Uso, desde la raíz del repositorio clonado:
#   bash infra/scripts/crear-estructura.sh
#
# Es idempotente: se puede correr varias veces sin romper nada. No sobrescribe
# ningún archivo que ya exista.

set -euo pipefail

if [[ ! -d .git ]]; then
  echo "ERROR: córrelo desde la raíz del repositorio (donde está la carpeta .git)." >&2
  exit 1
fi

CARPETAS=(
  ".github/workflows"
  ".github/ISSUE_TEMPLATE"
  "docs/adr"
  "docs/analisis"
  "docs/analisis/casos-uso"
  "docs/analisis/openapi"
  "docs/datos"
  "docs/datos/perfilado"
  "docs/equipo"
  "docs/equipo/fichas"
  "docs/equipo/entregas"
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
  "infra/envs/dev"
  "infra/envs/test"
  "infra/scripts"
)

echo "Creando estructura..."
nuevas=0
for c in "${CARPETAS[@]}"; do
  if [[ ! -d "$c" ]]; then
    mkdir -p "$c"
    nuevas=$((nuevas + 1))
  fi
  # .gitkeep solo si la carpeta está vacía
  if [[ -z "$(ls -A "$c" 2>/dev/null)" ]]; then
    touch "$c/.gitkeep"
  fi
done

echo "  $nuevas carpetas nuevas de ${#CARPETAS[@]}."
echo
echo "Revisa qué vas a subir antes de agregarlo:"
echo "  git status"
echo
echo "Recuerda que .env NUNCA se sube. Solo .env.example, con valores vacíos."
