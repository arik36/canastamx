#!/usr/bin/env bash
#
# verificar-base.sh — CanastaMX
#
# Córrelo ANTES de crear tu primera rama, y cada vez que tengas duda.
# Comprueba que tu copia del repositorio tiene la línea base y que tus
# herramientas están instaladas.
#
# Uso, desde la raíz del repositorio clonado:
#   bash infra/scripts/verificar-base.sh A      (Ariadne · datos)
#   bash infra/scripts/verificar-base.sh B      (Ari Adair · infraestructura)
#   bash infra/scripts/verificar-base.sh C1     (Liseth · dominio)
#   bash infra/scripts/verificar-base.sh C2     (Oscar · móvil)
#   bash infra/scripts/verificar-base.sh D      (Karen · web)
#
# No modifica nada. Solo mira y te dice qué falta.

set -uo pipefail

FRENTE="${1:-}"
OK=0; FALLA=0; AVISO=0

verde()   { printf '  \033[0;32m✓\033[0m  %s\n' "$1"; OK=$((OK+1)); }
rojo()    { printf '  \033[0;31m✗\033[0m  %s\n' "$1"; [[ -n "${2:-}" ]] && printf '       → %s\n' "$2"; FALLA=$((FALLA+1)); }
amaril()  { printf '  \033[0;33m!\033[0m  %s\n' "$1"; [[ -n "${2:-}" ]] && printf '       → %s\n' "$2"; AVISO=$((AVISO+1)); }
titulo()  { printf '\n\033[1m%s\033[0m\n' "$1"; }

if [[ -z "$FRENTE" ]]; then
  echo "Falta tu clave. Ejemplo:  bash infra/scripts/verificar-base.sh C1" >&2
  echo "Claves: A (datos) · B (infra) · C1 (dominio) · C2 (móvil) · D (web)" >&2
  exit 2
fi

case "$FRENTE" in
  A)  NOMBRE="Ariadne · datos y plataforma" ;;
  B)  NOMBRE="Ari Adair · infraestructura y CI" ;;
  C1) NOMBRE="Liseth · servicio de dominio" ;;
  C2) NOMBRE="Oscar · cliente móvil" ;;
  D)  NOMBRE="Karen · cliente web y maquetación" ;;
  *)  echo "Clave no reconocida: $FRENTE. Usa A, B, C1, C2 o D." >&2; exit 2 ;;
esac

echo "════════════════════════════════════════════════════════════"
echo " CanastaMX · verificación previa a crear rama"
echo " Frente $FRENTE — $NOMBRE"
echo "════════════════════════════════════════════════════════════"

# ── 1. Estás en un clon del repositorio ──────────────────────────────────────
titulo "1 · El repositorio"

if [[ -d .git ]]; then
  verde "Estás dentro del repositorio"
else
  rojo "No estás en la raíz del repositorio" \
       "cd a la carpeta donde clonaste canastamx"
  echo; echo "No puedo seguir sin esto."; exit 1
fi

REMOTO=$(git remote get-url origin 2>/dev/null || echo "")
if [[ "$REMOTO" == *"canastamx"* ]]; then
  verde "El remoto apunta a canastamx"
else
  amaril "El remoto no parece ser canastamx: $REMOTO"
fi

# ── 2. Tu main está al día ───────────────────────────────────────────────────
titulo "2 · Tu copia está al día"

git fetch --tags --quiet 2>/dev/null || amaril "No pude contactar a GitHub" "¿Tienes internet? ¿Aceptaste la invitación de colaborador?"

RAMA=$(git branch --show-current 2>/dev/null || echo "")
if [[ "$RAMA" == "main" ]]; then
  verde "Estás en main"
else
  amaril "Estás en la rama '$RAMA', no en main" "git switch main"
fi

DETRAS=$(git rev-list --count HEAD..origin/main 2>/dev/null || echo "?")
if [[ "$DETRAS" == "0" ]]; then
  verde "Tu main está al día con GitHub"
elif [[ "$DETRAS" == "?" ]]; then
  amaril "No pude comparar contra origin/main"
else
  rojo "Tu main está $DETRAS commits atrás" "git switch main && git pull"
fi

if [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
  amaril "Tienes cambios sin confirmar" "git status — decide si van a tu rama nueva o se descartan"
else
  verde "No tienes cambios sueltos"
fi

# ── 3. La línea base v0 ──────────────────────────────────────────────────────
titulo "3 · La línea base v0"

if git rev-parse -q --verify refs/tags/base-v0 >/dev/null 2>&1; then
  if git merge-base --is-ancestor base-v0 HEAD 2>/dev/null; then
    verde "Tu copia contiene la línea base v0"
  else
    rojo "La etiqueta base-v0 existe pero tu copia no la tiene" "git switch main && git pull"
  fi
else
  rojo "No existe la etiqueta base-v0" \
       "A todavía no marcó la línea base. NO ramifiques; avisa en el chat."
fi

# ── 4. Los archivos que no pueden faltar ─────────────────────────────────────
titulo "4 · Archivos bloqueantes"

for f in .gitignore .env.example README.md; do
  [[ -f "$f" ]] && verde "$f" || rojo "Falta $f" "A no ha subido la línea base completa"
done

# El .gitignore tiene que ignorar lo de TU frente, o vas a subir basura
faltan_ig=""
for pat in "node_modules/" ".venv/" "target/" ".env"; do
  grep -qF "$pat" .gitignore 2>/dev/null || faltan_ig="$faltan_ig $pat"
done
if [[ -z "$faltan_ig" ]]; then
  verde ".gitignore cubre node_modules, .venv, target y .env"
else
  rojo ".gitignore NO ignora:$faltan_ig" \
       "Si ramificas así vas a subir cientos de archivos generados. Avisa a B."
fi

for d in docs/equipo docs/equipo/fichas .github infra/scripts; do
  [[ -d "$d" ]] && verde "$d/" || rojo "Falta la carpeta $d/"
done

# ── 5. Tu carpeta de trabajo ─────────────────────────────────────────────────
titulo "5 · La carpeta de tu frente"

case "$FRENTE" in
  A)  MIAS=("services/data-platform" "services/analytics-api" "contracts" "docs/datos") ;;
  B)  MIAS=("infra" "infra/envs" ".github/workflows") ;;
  C1) MIAS=("services/domain-service" "docs/analisis") ;;
  C2) MIAS=("clients/mobile" "docs/datos") ;;
  D)  MIAS=("clients/web" "packages/types" "docs/analisis") ;;
esac
for d in "${MIAS[@]}"; do
  [[ -d "$d" ]] && verde "$d/" || rojo "Falta $d/" "Corre: bash infra/scripts/crear-estructura.sh"
done

# ── 5b. Higiene · que no se te haya colado basura ────────────────────────────
titulo "5b · Higiene del repositorio"

if git ls-files 2>/dev/null | grep -qE '(^|/)\.env$'; then
  rojo "Hay un archivo .env versionado" \
       "NO lo borres tú. Avisa a B: si trae contraseñas reales hay que rotarlas"
else
  verde "Sin archivos .env versionados"
fi

BASURA=$(git ls-files 2>/dev/null | grep -E '(^|/)(node_modules|\.venv|target|__pycache__)/' | head -3)
if [[ -n "$BASURA" ]]; then
  rojo "Hay carpetas de dependencias versionadas" \
       "Ver docs/equipo/linea-base.md, sección 'si ya ramificaste antes de tiempo'"
  echo "$BASURA" | sed 's/^/         /'
else
  verde "Sin carpetas de dependencias versionadas"
fi

PESADOS=$(git ls-files -z 2>/dev/null | xargs -0 -r ls -l 2>/dev/null \
          | awk '$5 > 10485760 {print $9 " (" int($5/1048576) " MB)"}' | head -3)
if [[ -n "$PESADOS" ]]; then
  rojo "Hay archivos de más de 10 MB" "Los datos crudos no van al repositorio"
  echo "$PESADOS" | sed 's/^/         /'
else
  verde "Sin archivos pesados"
fi

# ── 6. Tu Git está configurado ───────────────────────────────────────────────
titulo "6 · Tu identidad en Git"

GN=$(git config user.name  || echo "")
GE=$(git config user.email || echo "")
[[ -n "$GN" ]] && verde "user.name: $GN" \
               || rojo "Falta user.name" 'git config --global user.name "Tu Nombre Completo"'
[[ -n "$GE" ]] && verde "user.email: $GE" \
               || rojo "Falta user.email" 'git config --global user.email "tu-correo-de-github@ejemplo.com"'
[[ -n "$GE" ]] && amaril "Confirma que $GE es el correo de tu cuenta de GitHub" \
                         "Si no, tus commits no cuentan como contribución tuya"

# ── 7. Tus herramientas ──────────────────────────────────────────────────────
titulo "7 · Herramientas de tu frente"

hay() { command -v "$1" >/dev/null 2>&1; }

case "$FRENTE" in
  A)
    hay python3 && verde "python3 · $(python3 --version 2>&1)" || rojo "Falta Python 3.12"
    python3 -c "import pandas" 2>/dev/null && verde "pandas" \
      || amaril "Falta pandas" "pip install pandas pyarrow jupyter"
    hay docker && verde "docker" || amaril "Falta Docker Desktop" "Lo necesitas desde la semana 2"
    ;;
  B)
    hay docker && verde "docker · $(docker --version 2>&1 | head -1)" || rojo "Falta Docker Desktop"
    docker compose version >/dev/null 2>&1 && verde "docker compose" \
      || rojo "Falta el complemento compose" "Viene con Docker Desktop"
    hay gh && verde "gh (GitHub CLI)" || amaril "Falta gh" "https://cli.github.com — lo usa el guión de siembra"
    ;;
  C1)
    # Se filtra "Picked up JAVA_TOOL_OPTIONS", que algunas máquinas imprimen
    # antes de la versión y se comería la comprobación.
    if hay java; then
      V=$(java -version 2>&1 | grep -i "version" | grep -v "Picked up" | head -1)
      [[ "$V" == *'"21'* ]] && verde "java · $V" \
        || amaril "java instalado pero no parece ser 21: $V" "El proyecto exige JDK 21"
    else
      rojo "Falta el JDK 21" "Instálalo antes de ramificar"
    fi
    if hay mvn; then
      V=$(mvn -v 2>&1 | grep -i "^Apache Maven" | head -1 | cut -c1-40)
      verde "maven · ${V:-instalado}"
    else
      rojo "Falta Maven"
    fi
    ;;
  C2)
    if hay node; then
      V=$(node -v)
      [[ "$V" == v20* ]] && verde "node · $V" || amaril "node instalado pero no es 20: $V"
    else
      rojo "Falta Node 20"
    fi
    hay npx && verde "npx" || rojo "Falta npx" "Viene con Node"
    ;;
  D)
    if hay node; then
      V=$(node -v)
      [[ "$V" == v20* ]] && verde "node · $V" || amaril "node instalado pero no es 20: $V"
    else
      rojo "Falta Node 20"
    fi
    amaril "Figma se usa desde el navegador; no hay nada que verificar aquí"
    ;;
esac

# ── Veredicto ────────────────────────────────────────────────────────────────
echo
echo "════════════════════════════════════════════════════════════"
printf " %d correctos · %d avisos · %d bloqueantes\n" "$OK" "$AVISO" "$FALLA"
echo "════════════════════════════════════════════════════════════"
echo

if [[ $FALLA -eq 0 ]]; then
  printf '\033[0;32m PUEDES CREAR TU RAMA.\033[0m\n\n'
  echo " git switch -c feat/<tus-iniciales>-<descripcion-corta>"
  echo
  echo " Iniciales:  A→alm   B→aas   C1→lyl   C2→orf   D→kah"
  echo " Tipos:      feat · fix · docs · test · chore · refactor"
  echo
  echo " Y antes de escribir la primera línea, lee tu ficha completa:"
  echo "   docs/equipo/fichas/semana-01.md"
  exit 0
else
  printf '\033[0;31m TODAVÍA NO RAMIFIQUES.\033[0m\n\n'
  echo " Hay $FALLA punto(s) bloqueante(s) arriba, marcados con ✗."
  echo " Arregla los que sean tuyos. Si el problema es que falta algo en el"
  echo " repositorio, NO lo subas por tu cuenta: avisa en el chat, porque"
  echo " la línea base la sube A en un solo commit."
  echo
  echo " Detalle: docs/equipo/linea-base.md"
  exit 1
fi
