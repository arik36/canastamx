#!/usr/bin/env bash
#
# comparar-paquete.sh — CanastaMX
#
# Compara TU repositorio contra el paquete descomprimido, y te dice exactamente
# qué se agrega, qué se fusiona y qué no se toca. No modifica nada.
#
# IMPORTANTE: la primera vez, este script todavía NO está en tu repositorio
# (viene dentro del paquete). Párate en tu repositorio y llámalo por su ruta
# completa dentro del paquete:
#
#   cd ~/projects/canastamx
#   bash ~/paquete-canastamx/entrega/infra/scripts/comparar-paquete.sh \
#        ~/paquete-canastamx/entrega
#
# Después de fusionar el paquete, ya vive en tu repositorio y basta:
#
#   bash infra/scripts/comparar-paquete.sh ~/paquete-canastamx/entrega
#
# El argumento SIEMPRE es la carpeta 'entrega' que sale al descomprimir el zip.
# El script lee tu repositorio desde el directorio actual, así que lo que
# importa es DESDE DÓNDE lo corres, no dónde está el archivo.
#
# No descomprimas el paquete DENTRO del repositorio: se colaría al commit.

set -uo pipefail

V=$'\033[0;32m'; R=$'\033[0;31m'; Y=$'\033[0;33m'; A=$'\033[0;36m'
N=$'\033[0m'; B=$'\033[1m'

PAQ="${1:-}"

if [[ -z "$PAQ" ]]; then
  echo "Falta la ruta del paquete descomprimido." >&2
  echo >&2
  echo "  cd ~/projects/canastamx" >&2
  echo "  bash ~/paquete-canastamx/entrega/infra/scripts/comparar-paquete.sh ~/paquete-canastamx/entrega" >&2
  echo >&2
  echo "El argumento es la carpeta 'entrega' que sale al descomprimir el zip." >&2
  exit 2
fi
FORZAR=0
[[ "${2:-}" == "--forzar" || "${1:-}" == "--forzar" ]] && FORZAR=1
[[ "$PAQ" == "--forzar" ]] && PAQ="${2:-}"

PAQ="${PAQ%/}"
[[ -d "$PAQ" ]] || { echo "${R}No existe la carpeta: $PAQ${N}" >&2; exit 2; }
[[ -d .git   ]] || { echo "${R}No estás en la raíz de un repositorio de Git.${N}" >&2; exit 2; }

# ── ¿Es EL repositorio correcto? ────────────────────────────────────────────
# Tener un .git no basta: cualquier repositorio tuyo lo tiene. Si te paras en
# otro por error, el siguiente paso (cp -r) le vuelca 53 archivos que no van ahí.
REMOTO=$(git remote get-url origin 2>/dev/null || echo "")
CARPETA=$(basename "$PWD")
if [[ "$REMOTO" != *canastamx* && "$CARPETA" != *canastamx* ]]; then
  echo >&2
  echo "${R}════════════════════════════════════════════════════════════${N}" >&2
  echo "${R}${B} ALTO. Esto no parece el repositorio de CanastaMX.${N}" >&2
  echo "${R}════════════════════════════════════════════════════════════${N}" >&2
  echo >&2
  echo "  Estás en:  ${B}$PWD${N}" >&2
  [[ -n "$REMOTO" ]] && echo "  Remoto:    $REMOTO" >&2 \
                     || echo "  Remoto:    (este repositorio no tiene remoto)" >&2
  echo >&2
  echo "  Ni la carpeta ni el remoto mencionan 'canastamx'." >&2
  echo >&2
  echo "  ${B}No sigas aquí.${N} El paso siguiente de la guía es 'cp -r', y" >&2
  echo "  volcaría 53 archivos de CanastaMX en este repositorio." >&2
  echo >&2
  echo "  Ve al correcto:" >&2
  echo "      cd ~/projects/canastamx" >&2
  echo >&2
  echo "  Si de verdad querías compararlo aquí, repite con --forzar." >&2
  echo >&2
  exit 3
fi
[[ -f "$PAQ/docs/equipo/README.md" ]] || {
  echo "${R}$PAQ no parece el paquete: falta docs/equipo/README.md${N}" >&2
  echo "¿Apuntaste a la carpeta 'entrega' de adentro del zip?" >&2; exit 2; }

lista() {  # archivos relativos, sin .git, sin .gitkeep y sin ADS de Windows
  ( cd "$1" && find . -path ./.git -prune -o -type f -print ) \
    | sed 's|^\./||' \
    | grep -v '/\.gitkeep$' | grep -v '^\.gitkeep$' \
    | grep -v ':Zone\.Identifier$' \
    | sort
}

# Cuenta los ADS que Windows deja pegados al descomprimir del lado de Windows
ads() { ( cd "$1" && find . -name '*:Zone.Identifier' 2>/dev/null ) | wc -l | tr -d ' '; }

TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
lista .      > "$TMP/mio"
lista "$PAQ" > "$TMP/paq"

NUEVOS=$(comm -13 "$TMP/mio" "$TMP/paq")
SOLO_MIOS=$(comm -23 "$TMP/mio" "$TMP/paq")
COMUNES=$(comm -12 "$TMP/mio" "$TMP/paq")

echo
echo "${B}════════════════════════════════════════════════════════════${N}"
echo "${B} CanastaMX · tu repositorio  vs  el paquete${N}"
echo "${B}════════════════════════════════════════════════════════════${N}"
echo "  repositorio: $PWD"
echo "  paquete:     $PAQ"

# ── Basura de Windows en el paquete ─────────────────────────────────────────
ADS_PAQ=$(ads "$PAQ")
if [[ "$ADS_PAQ" -gt 0 ]]; then
  echo
  echo "${Y}${B}!  El paquete trae $ADS_PAQ archivos ':Zone.Identifier'${N}"
  echo "   Son marcas que Windows pega a lo que se descarga de internet. Aparecen"
  echo "   cuando el zip se descomprime del lado de Windows en vez de dentro de WSL."
  echo "   No los ignoro por gusto: si copias el paquete tal cual, se van al commit."
  echo
  echo "   Bórralos antes de copiar nada:"
  echo "       ${B}find $PAQ -name '*:Zone.Identifier' -delete${N}"
  echo
  echo "   (De aquí en adelante los omito del reporte.)"
fi

# ── 1. Se agregan ────────────────────────────────────────────────────────────
n=$(echo "$NUEVOS" | grep -c . || true)
echo
echo "${B}1 · SE AGREGAN — $n archivos, no pisan nada${N}"
echo "$NUEVOS" | grep . | sed "s/^/  ${V}+${N} /" | head -40
[[ $n -gt 40 ]] && echo "     ... y $((n-40)) más"

# ── 2. Se fusionan ───────────────────────────────────────────────────────────
echo
echo "${B}2 · ESTÁN EN LOS DOS — revisa el diff antes de decidir${N}"
hubo=0
while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  if cmp -s "$f" "$PAQ/$f"; then
    echo "  ${V}=${N} idéntico  $f"
  else
    a=$(wc -c < "$f"); b=$(wc -c < "$PAQ/$f")
    echo "  ${Y}≠${N} DIFIEREN  $f   (tuyo ${a}B · paquete ${b}B)"
    echo "       diff -u \"$f\" \"$PAQ/$f\" | less"
    hubo=1
  fi
done <<< "$COMUNES"
[[ $hubo -eq 0 ]] && echo "  (ninguno difiere)"

# ── 3. Solo tuyos ────────────────────────────────────────────────────────────
echo
echo "${B}3 · SOLO TUYOS — el paquete no los trae, se quedan como están${N}"
s=$(echo "$SOLO_MIOS" | grep -c . || true)
if [[ $s -eq 0 ]]; then
  echo "  (ninguno)"
else
  echo "$SOLO_MIOS" | grep . | sed "s/^/  ${A}!${N} /" | head -30
  [[ $s -gt 30 ]] && echo "     ... y $((s-30)) más"
fi

# ── 4. Variables de entorno · el choque que sí rompe ────────────────────────
echo
echo "${B}4 · VARIABLES DE ENTORNO${N}"
if [[ -f .env.example && -f "$PAQ/docker-compose.yml" ]]; then
  MIAS=$(grep -oE '^[A-Z_]+' .env.example | sort -u)

  # Obligatorias: ${VAR} sin valor por defecto. Si faltan, el servicio arranca
  # con el valor VACÍO y sin error visible.
  OBLIG=$(grep -oE '\$\{[A-Z_]+\}' "$PAQ/docker-compose.yml" | tr -d '${}' | sort -u)
  # Opcionales: ${VAR:-algo}. Si faltan, se usa el valor por defecto.
  OPCION=$(grep -oE '\$\{[A-Z_]+:-' "$PAQ/docker-compose.yml" | sed 's/[${:-]//g' | sort -u)

  FALTAN_OB=$(comm -13 <(echo "$MIAS") <(echo "$OBLIG"))
  FALTAN_OP=$(comm -13 <(echo "$MIAS") <(echo "$OPCION"))

  if [[ -z "$FALTAN_OB" ]]; then
    echo "  ${V}✓${N}  Tu .env.example define todas las variables obligatorias del compose"
  else
    echo "  ${R}✗${N}  BLOQUEANTE — el compose pide variables sin valor por defecto que tu"
    echo "      .env.example NO define:"
    echo "$FALTAN_OB" | sed 's/^/       /'
    echo "      → El servicio levantaría con ese valor VACÍO y sin error visible."
    echo "      → Agrégalas a tu .env.example antes de correr docker compose up."
  fi

  if [[ -n "$FALTAN_OP" ]]; then
    echo "  ${Y}!${N}  Opcionales — tienen valor por defecto en el compose, así que"
    echo "      funciona sin ellas. Agrégalas solo si quieres poder cambiar el puerto:"
    echo "$FALTAN_OP" | sed 's/^/       /'
  fi
else
  echo "  (no pude comparar: falta .env.example o docker-compose.yml)"
fi

# ── 5. Carpetas que faltan ───────────────────────────────────────────────────
echo
echo "${B}5 · CARPETAS QUE AGREGA crear-estructura.sh${N}"
for d in .github/ISSUE_TEMPLATE docs/equipo docs/equipo/fichas docs/equipo/entregas \
         docs/analisis docs/datos infra/envs/dev infra/envs/test; do
  [[ -d "$d" ]] || echo "  ${V}+${N} $d"
done
echo "  (córrelo después de copiar: bash infra/scripts/crear-estructura.sh)"

# ── Resumen ──────────────────────────────────────────────────────────────────
echo
echo "${B}════════════════════════════════════════════════════════════${N}"
echo " $n se agregan · $(echo "$COMUNES" | grep -c . || true) coinciden en nombre · $s son solo tuyos"
echo "${B}════════════════════════════════════════════════════════════${N}"
echo
echo " ${B}No se pierde ningún archivo tuyo.${N} Los que aparecen en la sección 2"
echo " marcados como DIFIEREN son los únicos que hay que mirar con calma."
echo
echo " Detalle: docs/equipo/fusion-con-el-repo.md"
if [[ "$ADS_PAQ" -gt 0 ]]; then
  echo
  echo " ${Y}Antes de copiar:${N} find $PAQ -name '*:Zone.Identifier' -delete"
fi
echo
