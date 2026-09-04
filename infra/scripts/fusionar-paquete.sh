#!/usr/bin/env bash
#
# fusionar-paquete.sh — CanastaMX
#
# Copia el paquete sobre tu repositorio SIN perder nada:
#   · respalda todo archivo que vaya a ser pisado, antes de tocarlo
#   · fusiona el .gitignore uniendo las dos listas, en vez de reemplazarla
#   · omite la basura de Windows (:Zone.Identifier)
#   · te deja una lista concreta de qué revisar al final
#
# Uso, parada en tu repositorio:
#   bash ~/paquete-canastamx/entrega/infra/scripts/fusionar-paquete.sh \
#        ~/paquete-canastamx/entrega
#
# Antes de correrlo: crea tu rama. El script se niega si estás en main.
#
# NO hace commit. Al terminar, tú revisas y decides.

set -uo pipefail

V=$'\033[0;32m'; R=$'\033[0;31m'; Y=$'\033[0;33m'; A=$'\033[0;36m'
N=$'\033[0m'; B=$'\033[1m'

PAQ="${1:-}"
[[ -n "$PAQ" ]] || { echo "Falta la ruta del paquete. Ejemplo:" >&2
  echo "  bash ~/paquete-canastamx/entrega/infra/scripts/fusionar-paquete.sh ~/paquete-canastamx/entrega" >&2
  exit 2; }
PAQ="${PAQ%/}"

[[ -d "$PAQ" ]] || { echo "${R}No existe la carpeta: $PAQ${N}" >&2; exit 2; }
[[ -d .git   ]] || { echo "${R}No estás en la raíz de un repositorio de Git.${N}" >&2; exit 2; }
[[ -f "$PAQ/docs/equipo/README.md" ]] || {
  echo "${R}$PAQ no parece el paquete: falta docs/equipo/README.md${N}" >&2; exit 2; }

# ── ¿El repositorio correcto? ───────────────────────────────────────────────
REMOTO=$(git remote get-url origin 2>/dev/null || echo "")
if [[ "$REMOTO" != *canastamx* && "$(basename "$PWD")" != *canastamx* ]]; then
  echo "${R}${B}ALTO. Esto no parece el repositorio de CanastaMX.${N}" >&2
  echo "  Estás en: $PWD" >&2
  echo "  Ve al correcto:  cd ~/projects/canastamx" >&2
  exit 3
fi

# ── ¿En una rama, no en main? ───────────────────────────────────────────────
RAMA=$(git branch --show-current 2>/dev/null || echo "")
if [[ "$RAMA" == "main" || "$RAMA" == "master" ]]; then
  echo "${R}${B}Estás en '$RAMA'. Crea una rama primero:${N}" >&2
  echo "    git switch -c chore/alm-linea-base" >&2
  exit 4
fi

# ── ¿Árbol limpio? ──────────────────────────────────────────────────────────
if [[ -n "$(git status --porcelain)" ]]; then
  echo "${Y}${B}Tienes cambios sin confirmar.${N}" >&2
  echo "  Confírmalos o guárdalos antes, para que el 'git diff' de después" >&2
  echo "  muestre solo lo que trajo el paquete:" >&2
  echo "      git stash        # y al final:  git stash pop" >&2
  echo >&2
  read -rp "  ¿Seguir de todos modos? [s/N] " r
  [[ "${r,,}" == "s" ]] || exit 5
fi

echo
echo "${B}════════════════════════════════════════════════════════════${N}"
echo "${B} Fusionando el paquete${N}"
echo "${B}════════════════════════════════════════════════════════════${N}"
echo "  repositorio: $PWD"
echo "  rama:        $RAMA"
echo "  paquete:     $PAQ"

# ── Basura de Windows ───────────────────────────────────────────────────────
ADS=$(find "$PAQ" -name '*:Zone.Identifier' 2>/dev/null | wc -l | tr -d ' ')
if [[ "$ADS" -gt 0 ]]; then
  echo
  echo "${Y}!  El paquete trae $ADS archivos ':Zone.Identifier'. No se copian.${N}"
fi

# ── Respaldo de lo que va a ser pisado ──────────────────────────────────────
SELLO=$(date +%Y%m%d-%H%M%S)
RESP="../respaldo-canastamx-$SELLO"
mkdir -p "$RESP"

PISADOS=()
while IFS= read -r rel; do
  [[ -f "$rel" ]] || continue
  cmp -s "$rel" "$PAQ/$rel" && continue      # idéntico, no hace falta respaldar
  mkdir -p "$RESP/$(dirname "$rel")"
  cp -p "$rel" "$RESP/$rel"
  PISADOS+=("$rel")
done < <( cd "$PAQ" && find . -type f ! -name '*:Zone.Identifier' | sed 's|^\./||' )

echo
if [[ ${#PISADOS[@]} -eq 0 ]]; then
  echo "${V}✓${N}  Ningún archivo tuyo va a ser reemplazado."
  rmdir "$RESP" 2>/dev/null
  RESP=""
else
  echo "${B}Respaldados antes de tocarlos${N} → ${A}$RESP${N}"
  printf '  · %s\n' "${PISADOS[@]}"
fi

# ── .gitignore: se unen las dos listas, no se reemplaza ─────────────────────
UNIDO=0
if [[ -f .gitignore && -f "$PAQ/.gitignore" ]] && ! cmp -s .gitignore "$PAQ/.gitignore"; then
  ANTES=$(grep -cvE '^\s*(#|$)' .gitignore || echo 0)
  {
    cat .gitignore
    echo
    echo "# ─────────────────────────────────────────────────────────────────────────"
    echo "# Agregado desde el paquete del equipo — $(date +%Y-%m-%d)"
    echo "# ─────────────────────────────────────────────────────────────────────────"
    # solo las reglas del paquete que tú todavía no tenías
    grep -vE '^\s*(#|$)' "$PAQ/.gitignore" | while IFS= read -r regla; do
      grep -qxF "$regla" .gitignore || echo "$regla"
    done
  } > /tmp/.gitignore-unido-$$
  mv /tmp/.gitignore-unido-$$ .gitignore
  DESPUES=$(grep -cvE '^\s*(#|$)' .gitignore || echo 0)
  UNIDO=$((DESPUES - ANTES))
fi

# ── Copia, omitiendo el .gitignore que ya fusionamos y los ADS ──────────────
echo
echo "${B}Copiando...${N}"
COPIADOS=0
while IFS= read -r rel; do
  [[ "$rel" == ".gitignore"  ]] && continue
  [[ "$rel" == "INSTALAR.md" ]] && continue   # es para ti, no para el repositorio
  mkdir -p "$(dirname "$rel")"
  cp -p "$PAQ/$rel" "$rel"
  COPIADOS=$((COPIADOS + 1))
done < <( cd "$PAQ" && find . -type f ! -name '*:Zone.Identifier' | sed 's|^\./||' )
echo "  $COPIADOS archivos copiados"
[[ $UNIDO -gt 0 ]] && echo "  .gitignore: $UNIDO reglas nuevas agregadas a las tuyas (no se reemplazó)"

# ── Carpetas que faltaban ───────────────────────────────────────────────────
if [[ -f infra/scripts/crear-estructura.sh ]]; then
  echo
  bash infra/scripts/crear-estructura.sh
fi

# ── Qué revisar ─────────────────────────────────────────────────────────────
echo
echo "${B}════════════════════════════════════════════════════════════${N}"
echo "${B} Listo. Nada se subió todavía.${N}"
echo "${B}════════════════════════════════════════════════════════════${N}"
echo
echo "${B}1. Revisa lo que cambió de lo tuyo:${N}"
echo
if [[ ${#PISADOS[@]} -gt 0 ]]; then
  for f in "${PISADOS[@]}"; do
    [[ "$f" == ".gitignore" ]] && continue
    echo "     diff -u \"$RESP/$f\" \"$f\" | less"
  done
  echo
  echo "   Tu versión original está completa en ${A}$RESP${N}"
  echo "   Si algo tuyo te gustaba más, recupéralo de ahí antes de confirmar."
else
  echo "     (no se reemplazó nada tuyo)"
fi
echo
echo "${B}2. Mira todo el cambio:${N}"
echo "     git status"
echo "     git diff"
echo
echo "${B}3. Cuando estés conforme:${N}"
echo "     git add ."
echo "     git commit -m \"chore(repo): línea base — manual, fichas y plantillas\""
echo "     git push -u origin $RAMA"
echo
echo "${B}4. Y marca la línea base en main, después de incorporar:${N}"
echo "     git switch main && git pull"
echo "     git tag -a base-v0 -m \"Línea base del repositorio\""
echo "     git push origin base-v0"
echo
