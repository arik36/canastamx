#!/usr/bin/env bash
#
# sembrar-tablero.sh — CanastaMX
#
# Crea en GitHub las etiquetas, los hitos y los issues de las semanas 1 a 3,
# más las dos tareas que la replaneación del 5 de septiembre recorrió a la
# semana 4. Todo sale de docs/equipo/cronograma.md.
#
# Requisitos:
#   1. GitHub CLI instalado ......... https://cli.github.com
#   2. Sesión iniciada .............. gh auth login
#   3. Ejecutarse desde la raíz del repositorio clonado
#
# Uso:
#   bash infra/scripts/sembrar-tablero.sh            # crea todo
#   bash infra/scripts/sembrar-tablero.sh --simular  # solo muestra qué haría
#
# Se puede volver a correr sin miedo: las etiquetas y los hitos que ya existen
# se omiten. Los issues NO se deduplican, así que si ya los sembraste, no lo
# corras otra vez o tendrás duplicados.

set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURA ESTO ANTES DE CORRERLO
# Pon el usuario de GitHub de cada quien. Si dejas un valor vacío, el issue se
# crea sin asignar y lo asignan a mano después.
# ─────────────────────────────────────────────────────────────────────────────
USER_A="arik36"            # Ariadne  · datos y plataforma
USER_B="Wolff"             # Ari Adair · infraestructura y CI
USER_C1="lisslar"          # Liseth   · servicio de dominio
USER_C2="Renato"           # Oscar    · cliente móvil
USER_D="alesitaK"          # Karen    · cliente web y maquetación

REPO="arik36/canastamx"

# ─────────────────────────────────────────────────────────────────────────────

SIMULAR=0
[[ "${1:-}" == "--simular" ]] && SIMULAR=1

if [[ $SIMULAR -eq 0 ]]; then
  if ! command -v gh >/dev/null 2>&1; then
    echo "ERROR: no encuentro 'gh'. Instálalo desde https://cli.github.com" >&2
    echo "       (puedes correr 'bash $0 --simular' para ver qué haría sin instalarlo)" >&2
    exit 1
  fi
  if ! gh auth status >/dev/null 2>&1; then
    echo "ERROR: no has iniciado sesión. Corre:  gh auth login" >&2
    exit 1
  fi
fi

echo "Repositorio: $REPO"
[[ $SIMULAR -eq 1 ]] && echo ">>> MODO SIMULACIÓN: no se crea nada <<<"
echo

# ── Etiquetas ────────────────────────────────────────────────────────────────
echo "── Etiquetas ──"
crear_etiqueta() {
  local nombre="$1" color="$2" desc="$3"
  if [[ $SIMULAR -eq 1 ]]; then
    echo "  [simulado] $nombre"
    return
  fi
  if gh label create "$nombre" --color "$color" --description "$desc" --repo "$REPO" 2>/dev/null; then
    echo "  creada: $nombre"
  else
    echo "  ya existía: $nombre"
  fi
}

crear_etiqueta "datos"       "1D76DB" "Frente A — ingesta, contratos, calidad, analítica"
crear_etiqueta "infra"       "5A5A5A" "Frente B — contenedores, CI, despliegue"
crear_etiqueta "dominio"     "D93F0B" "Frente C1 — servicio de dominio en Java"
crear_etiqueta "movil"       "8B5CF6" "Frente C2 — cliente móvil en Expo"
crear_etiqueta "web"         "0E8A16" "Frente D — cliente web y maquetación"
crear_etiqueta "docs"        "FBCA04" "Documentación"
crear_etiqueta "entrega"     "B60205" "Atado a una entrega institucional"
crear_etiqueta "bloqueo"     "7A0000" "Detenido esperando a otro integrante"
crear_etiqueta "experimento" "6B4423" "Semana 13 — corridas y análisis"
echo

# ── Hitos ────────────────────────────────────────────────────────────────────
echo "── Hitos ──"
crear_hito() {
  local titulo="$1" fecha="$2"
  if [[ $SIMULAR -eq 1 ]]; then
    echo "  [simulado] $titulo ($fecha)"
    return
  fi
  if gh api "repos/$REPO/milestones" -f title="$titulo" -f due_on="${fecha}T23:59:59Z" >/dev/null 2>&1; then
    echo "  creado: $titulo"
  else
    echo "  ya existía: $titulo"
  fi
}

crear_hito "E1 — Definición"           "2026-09-18"
crear_hito "E2 — Análisis"             "2026-10-09"
crear_hito "E3 — Construcción"         "2026-11-04"
crear_hito "E4 — Versión desplegada"   "2026-11-18"
crear_hito "E5 — Presentación"         "2026-12-09"
echo

# ── Issues ───────────────────────────────────────────────────────────────────
# Formato por línea, separado por |
#   1 semana | 2 responsable | 3 etiqueta | 4 hito | 5 fecha límite
#   6 título | 7 qué hay que hacer | 8 cómo saber que quedó | 9 dónde queda
# ─────────────────────────────────────────────────────────────────────────────
TAREAS=$(cat <<'FIN'
1|A|datos|E1 — Definición|7 sep|[S1][Datos] Cerrar la estructura del repositorio|Carpetas con .gitkeep, .gitignore, README inicial, main protegida, los cuatro colaboradores invitados. Crear el tablero en GitHub Projects con las cinco columnas.|Los cinco clonan y ven la misma estructura; git status limpio en las cinco máquinas.|raíz del repositorio
1|A|datos|E1 — Definición|7 sep|[S1][Datos] Localizar y descargar la fuente QQP|Encontrar el conjunto QQP en el portal de PROFECO. Descargar el archivo más reciente y el de 2025. Verificar que abren; anotar tamaño y formato.|Los archivos abren. Tamaño y formato anotados en docs/datos/fuente-qqp.md.|docs/datos/fuente-qqp.md
1|A|datos|E1 — Definición|7 sep|[S1][Datos] Perfilado nivel 1|Contar filas y columnas. Tipos de dato reales por columna. Porcentaje de nulos por columna. Rango de fechas cubierto. Entidades federativas presentes.|Cuaderno de análisis con la tabla de resultados guardado en docs/datos/perfilado/.|docs/datos/perfilado/
1|A|datos|E1 — Definición|8 sep|[S1][Datos] Perfilado nivel 2|Distribución de precios: mínimo, máximo, mediana y percentiles por categoría. Precios en cero, negativos o absurdos. Duplicados exactos. Número de establecimientos y cadenas.|La sección de rangos y anomalías está escrita con números concretos, no con adjetivos.|docs/datos/perfilado/
1|A|datos|E1 — Definición|9 sep|[S1][Datos] Perfilado nivel 3 — variantes de escritura|Tomar veinte productos comunes y contar cuántas formas distintas de escribirlos aparecen entre cadenas. Este número decide si la meta de 85% de cobertura de H3 es realista.|La tabla de variantes por producto está en el perfilado, con el conteo de los veinte productos.|docs/datos/perfilado/
1|A|datos|E1 — Definición|10 sep|[S1][Datos] Informe de perfilado versión cero|Redactar el informe con las tres secciones del perfilado y una conclusión explícita: la fuente sirve, o no sirve, y por qué.|docs/datos/informe-perfilado-v0.md existe y termina con una recomendación clara.|docs/datos/informe-perfilado-v0.md
1|B|infra|E1 — Definición|7 sep|[S1][Infra] docker-compose con los cuatro servicios base|Escribir docker-compose.yml con postgres-oltp, postgres-analytics, minio y adminer. Levantar y verificar que los cuatro responden.|docker compose up levanta los cuatro sin error. MinIO y Adminer abren en el navegador.|docker-compose.yml
1|B|infra|E1 — Definición|8 sep|[S1][Infra] Traefik y enrutamiento local|Agregar Traefik a la composición y resolver el enrutamiento local por nombre de servicio. Crear .env.example con las llaves y valores vacíos.|Los servicios responden por nombre de dominio local en lugar de por puerto.|docker-compose.yml, .env.example
1|B|infra|E1 — Definición|9 sep|[S1][Infra] Integración continua mínima|Configurar el flujo de trabajo para que al abrir una solicitud corra el análisis estático y la compilación.|Una solicitud de prueba dispara la canalización y aparece en verde.|.github/workflows/ci.yml
1|B|infra|E1 — Definición|9 sep|[S1][Infra] Cuentas de Oracle Cloud y GitHub Student Pack|Registrarse en Oracle Cloud y solicitar el GitHub Student Pack. Ambos trámites tardan, por eso van la primera semana.|Ambos registros enviados, con captura del acuse en el issue.|—
1|C1|dominio|E1 — Definición|7 sep|[S1][Dominio] Esqueleto de Spring Boot con las tres capas|Instalar JDK 21 y Maven. Crear el proyecto con las tres capas separadas y exponer un endpoint de salud.|GET /health responde. El servicio arranca con mvn spring-boot:run.|services/domain-service/
1|C1|dominio|E1 — Definición|8 sep|[S1][Dominio] Primer borrador del modelo de dominio|Definir qué son entidades, qué son objetos de valor y dónde están los límites de los agregados Usuario, Canasta y Alerta.|Existe docs/analisis/modelo-dominio.md con la lista y su justificación.|docs/analisis/modelo-dominio.md
1|C2|movil|E1 — Definición|7 sep|[S1][Móvil] Diccionario de datos de QQP|Descargar y leer el diccionario de datos de QQP. Anotar qué columnas existen y qué significa cada una.|Existe docs/datos/diccionario-qqp.md con la lista de columnas y su significado.|docs/datos/diccionario-qqp.md
1|C2|movil|E1 — Definición|8 sep|[S1][Móvil] Proyecto base de Expo corriendo|Instalar Node 20 y Expo. Crear el proyecto y dejarlo arrancando en un teléfono real o emulador, con navegación entre dos pantallas vacías.|La app abre en un teléfono. Captura adjunta en el issue.|clients/mobile/
1|D|web|E1 — Definición|7 sep|[S1][Web] Inventario de las ocho vistas|Crear el archivo de Figma del proyecto. Escribir el inventario de las ocho vistas con una línea de contenido por cada una.|El enlace de Figma está en el README y el inventario en docs/analisis/inventario-vistas.md.|docs/analisis/inventario-vistas.md
1|D|web|E1 — Definición|8 sep|[S1][Web] Wireframe del tablero analítico|Wireframe de baja fidelidad: qué gráficas van, en qué orden y con qué filtros.|El wireframe existe en Figma y se ve desde el enlace compartido.|Figma
1|D|web|E1 — Definición|9 sep|[S1][Web] Wireframe de la consola de observabilidad|Wireframe de la consola. Se revisa con A antes de darlo por bueno, porque los seis indicadores tienen que leerse de un vistazo.|El wireframe existe y A dio su visto bueno por escrito en este issue.|Figma
1|A|entrega|E1 — Definición|11 sep|[S1][Equipo] Reunión de decisión y ADR de la fuente|Reunión de 45 minutos. A presenta el perfilado. El equipo decide si la fuente sirve y fija el recorte geográfico con datos en mano. Se acuerda el horario fijo de la reunión semanal.|docs/adr/001-fuente-de-datos.md escrito con fecha, contexto, decisión y alternativas descartadas. Horario de reunión en el calendario de los cinco.|docs/adr/001-fuente-de-datos.md
2|A|datos|E1 — Definición|16 sep|[S2][Datos] Contrato de datos v1 para QQP|Escribir el contrato en YAML: columnas, tipos, obligatoriedad, rangos y umbral de frescura.|El archivo existe en contracts/ y Pandera lo carga sin error.|contracts/
4|A|datos|E2 — Análisis|27 sep|[S4][Datos] Primer guión de ingesta a MinIO|Guión que descarga el archivo de PROFECO y lo guarda como Parquet particionado en MinIO.|El guión corre de principio a fin y el Parquet aparece en el bucket.|services/data-platform/ingestion/
4|B|infra|E2 — Análisis|27 sep|[S4][Infra] Separar entornos y manejo de secretos|Separar los entornos de desarrollo y pruebas. Configurar el manejo de secretos. Extender la integración continua para que corra pytest.|Los dos entornos levantan por separado y la canalización corre pytest en verde.|infra/envs/, .github/workflows/
2|C1|dominio|E1 — Definición|16 sep|[S2][Dominio] Cerrar el modelo y estructurar el servicio|Definir atributos de cada entidad y las reglas de negocio dentro del agregado. Estructurar el servicio en capas. Implementar Usuario y Canasta con sus reglas.|El documento del modelo está completo. Las clases de Usuario y Canasta existen con sus reglas y compilan.|docs/analisis/, services/domain-service/
2|C2|movil|E1 — Definición|16 sep|[S2][Móvil] Navegación con las cuatro pantallas|Navegación completa de la app con las cuatro pantallas vacías: búsqueda, detalle, mi canasta, alertas.|Se navega entre las cuatro pantallas en el teléfono. Video corto adjunto.|clients/mobile/
2|D|web|E1 — Definición|16 sep|[S2][Web] Sistema de diseño mínimo y ocho wireframes|Definir paleta, tipografía y componentes base en Figma. Aplicarlos a los wireframes existentes y completar los de las ocho vistas.|El sistema de diseño está en Figma y las ocho vistas lo usan.|Figma
3|A|entrega|E1 — Definición|18 sep|[S3][Datos] Cerrar el informe de perfilado y el recorte|Cerrar el informe. Documentar el recorte geográfico y de productos definitivo con su justificación cuantitativa.|El informe está cerrado y el recorte tiene números que lo sustentan.|docs/datos/
3|B|entrega|E1 — Definición|18 sep|[S3][Infra] Guía de arranque verificada|Escribir la guía de arranque en el README y verificarla: otro integrante clona en máquina limpia y levanta sin preguntar nada.|Alguien que no es B levantó el sistema siguiendo solo el README, y lo confirma en este issue.|README.md
3|C1|entrega|E1 — Definición|18 sep|[S3][Dominio] Diagrama de clases del modelo de dominio|Diagrama de clases con entidades, objetos de valor, agregados y sus relaciones.|El diagrama está en docs/analisis/ y corresponde al modelo escrito.|docs/analisis/
3|C2|entrega|E1 — Definición|18 sep|[S3][Móvil] Prototipo móvil con el sistema de diseño|Aplicar el sistema de diseño de D al prototipo navegable de la app.|Las cuatro pantallas usan la paleta y tipografía definidas.|clients/mobile/
3|D|entrega|E1 — Definición|18 sep|[S3][Web] Prototipo navegable presentable|Cerrar el prototipo navegable de las ocho vistas, listo para mostrarse en la entrega.|El prototipo se recorre completo desde el enlace de Figma.|Figma
3|A|entrega|E1 — Definición|18 sep|[S3][Equipo] Entrega del 18 de septiembre|Definición del proyecto, integrantes y responsabilidades, más la presentación. Ver docs/equipo/entregas/2026-09-18-definicion.md.|El documento está entregado, la presentación ensayada y el enlace registrado en docs/entregas/2026-09-18/.|docs/entregas/2026-09-18/
FIN
)

usuario_de() {
  case "$1" in
    A)  echo "$USER_A"  ;;
    B)  echo "$USER_B"  ;;
    C1) echo "$USER_C1" ;;
    C2) echo "$USER_C2" ;;
    D)  echo "$USER_D"  ;;
    *)  echo ""         ;;
  esac
}

echo "── Issues ──"
CREADOS=0
while IFS='|' read -r semana resp etiqueta hito fecha titulo que criterio donde; do
  [[ -z "${semana// }" ]] && continue

  cuerpo=$(cat <<CUERPO
## Qué hay que hacer

$que

## Cómo saber que quedó

$criterio

## Dónde queda

\`$donde\`

---

Semana $semana · Frente: $etiqueta · Responsable: $resp · Fecha límite: $fecha de 2026

<sub>Sembrado desde \`docs/equipo/cronograma.md\`. Si el criterio de cierre no es verificable, corrígelo aquí antes de empezar.</sub>
CUERPO
)

  if [[ $SIMULAR -eq 1 ]]; then
    echo "  [simulado] $titulo"
    CREADOS=$((CREADOS + 1))
    continue
  fi

  asignado=$(usuario_de "$resp")
  args=(--repo "$REPO" --title "$titulo" --body "$cuerpo" --label "$etiqueta" --milestone "$hito")
  [[ -n "$asignado" ]] && args+=(--assignee "$asignado")

  if url=$(gh issue create "${args[@]}" 2>&1); then
    echo "  ✓ $titulo"
    echo "    $url"
    CREADOS=$((CREADOS + 1))
  else
    echo "  ✗ FALLÓ: $titulo" >&2
    echo "    $url" >&2
  fi
done <<< "$TAREAS"

echo
echo "Listo. $CREADOS issues procesados."
echo
echo "Siguiente paso, a mano en la web:"
echo "  1. Abre el proyecto y agrega los issues al tablero (Add item → busca por #)."
echo "  2. Llena los campos Semana, Frente y Fecha límite de cada tarjeta."
echo "  3. Mueve a 'Esta semana' lo que toca del 7 al 11 de septiembre."
echo "  4. El resto de la semana 4 en adelante se siembra en la reunión semanal, no ahora."
