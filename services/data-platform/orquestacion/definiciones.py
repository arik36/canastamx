"""CanastaMX · los cuatro activos particionados y el sensor (ADR 016).

## Qué es un activo, y por qué no es «la tarea de ingerir»

Un **activo** es una cosa que existe después de correr: la capa cruda de una
quincena en el bucket, la cuarentena de ese lote, la decisión de promoverlo. Se
declara qué produce y de qué depende, y Dagster deduce el orden. Eso es lo que da
el **linaje** que pide RF-12 sin construirlo a mano.

Una **partición** es una rebanada que se materializa sola. Aquí la partición es la
**quincena**, que es exactamente un lote (ADR 016 · 1). Por eso «reprocesar
`2026-07-Q2`» (RF-25) es re-materializar su partición, y significa lo mismo en la
consola, en el experimento y en el código.

Las 38 particiones **no están escritas aquí**: salen de `alcance.ventana` del
contrato. Si la ventana cambia, cambian las particiones sin tocar este archivo.

## Los cuatro activos

    capa_cruda ──> filas_revisadas ──> lote_promovido ──> capa_intermedia
    (ingesta.py)   (compuerta.py)      (reparacion.py,    (intermedia.py)
                                        lote.py + D-07)

1. **`capa_cruda`** envuelve `ingestion/ingesta.py`. No lo reescribe: lo corre y
   lee su registro de corrida. Lo que ya hacía —controles C1, `?` en los filtros,
   filas de otra quincena, escritura particionada— sigue siendo suyo.
2. **`filas_revisadas`** llama a `compuerta.revisar_lote()`: Pandera contra el
   contrato, fila por fila, y la cuarentena con un motivo por fila.
3. **`lote_promovido`** llama a `reparacion.apartar_irreparables()` —el `?` que no
   se puede reparar (CU-03)—, a `lote.revisar_grupos()` y
   `lote.revisar_frescura()` —lo que necesita el lote completo— y después a
   `compuerta.decidir_promocion()`, que aplica el 5% de D-07 **sobre las tres
   cuarentenas juntas**. Ése es el orden correcto y no es un detalle: si el umbral
   se evaluara antes del `?` o de las reglas de grupo, un lote lleno de texto
   irreparable o de colisiones altas pasaría por debajo del 5% y se promovería.
4. **`capa_intermedia`** (T048) llama a `intermedia.construir()` con las filas que
   el lote dejó salir —repara, tipa y quita la captura doble— y a
   `intermedia.cargar()`, que reemplaza la partición del lote en
   `postgres-analytics`. Comprueba que la cuenta cuadre con el linaje: exactamente
   las que `lote_promovido` dejó salir menos las sobrantes de captura doble. Un
   lote detenido deja su partición vacía.

## El sensor y H2

El sensor mira la carpeta de llegada cada pocos segundos. Al ver un archivo nuevo
pide una corrida de la partición que le toca, y **anota la marca de tiempo del
disparo** en las etiquetas de la corrida. Ese instante es el cero desde el que H2
cuenta sus 15 minutos (SLA-D-05): sin él, los 15 minutos no tienen desde cuándo.

## Cómo se corre

    cd services/data-platform
    export DAGSTER_HOME=~/.dagster                # si no, avisa en cada arranque
    mkdir -p "$DAGSTER_HOME"
    export CANASTAMX_LOTES=/ruta/a/los/lotes      # dónde están los archivos
    export CANASTAMX_SIMULAR=1                    # sin bucket, para probar
    export CANASTAMX_FECHA_REFERENCIA=2026-08-10  # la frescura la pide (ver abajo)
    # CANASTAMX_CORRIDAS es opcional: dónde queda la evidencia. Por omisión,
    # ingestion/corridas/, que no entra al repositorio.
    dagster dev -m orquestacion.definiciones

Necesita `dagster` **y** `dagster-webserver`, las dos en la misma versión. Están
en `requirements.txt`; con sólo la primera, `dagster dev` falla pidiendo la otra.

Sin `CANASTAMX_SIMULAR`, la capa cruda va a MinIO y la intermedia a
`postgres-analytics`: hacen falta las `S3_*` y las `ANALYTICS_*` del `.env`
(`set -a; source .env; set +a`). Con simulación, la intermedia queda en
`capa-intermedia.duckdb`, dentro de la carpeta de corridas.
"""

# OJO · aquí NO va `from __future__ import annotations`. Con él, las anotaciones
# quedan como cadenas y Dagster deja de reconocer `context: AssetExecutionContext`:
# falla al cargar con un mensaje que se contradice solo («context must be annotated
# with AssetExecutionContext»). Costó un rato encontrarlo; que quede escrito.

import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from dagster import (
    AssetExecutionContext,
    Definitions,
    MetadataValue,
    RunRequest,
    SensorEvaluationContext,
    SensorResult,
    SkipReason,
    StaticPartitionsDefinition,
    asset,
    define_asset_job,
    sensor,
)

AQUI = Path(__file__).resolve().parent
PLATAFORMA = AQUI.parent
INGESTA = PLATAFORMA / "ingestion"
sys.path.insert(0, str(INGESTA))

import compuerta
import intermedia
import lote as reglas_de_lote
import reparacion
from ingesta import CORRIDAS, leer_contrato, sha256_de
from salida_segura import CODIFICACION_DE_LOS_HIJOS, entorno_utf8

# La misma carpeta que escribe ingesta.py, y no una copia de la ruta: el activo
# de capa cruda LEE ahí el registro de la ingesta, así que si fueran dos rutas que
# se separan, el activo dejaría de encontrarlo.
SALIDAS = CORRIDAS

# Dónde llegan los lotes y si se escribe al bucket. Son de entorno y no del
# contrato a propósito: son cosas de la máquina, no del dato.
LOTES = Path(os.environ.get("CANASTAMX_LOTES", INGESTA / "lotes"))
SIMULAR = os.environ.get("CANASTAMX_SIMULAR", "") not in ("", "0", "no")
# La frescura se mide contra una fecha que es parámetro de la corrida, no TODAY():
# el contrato explica que con el corpus congelado cualquier corrida daría
# «bloquea». Sin este parámetro la compuerta no puede mostrar «ok» ni «avisa».
FECHA_REFERENCIA = os.environ.get("CANASTAMX_FECHA_REFERENCIA") or None


def quincenas_del_contrato(contrato=None):
    """Las particiones, derivadas de `alcance.ventana`. Hoy son 38; no está escrito.

    Día 1–15 → Q1 · 16 en adelante → Q2, que es la convención de la fuente y la
    misma que usa `ingesta.py` para partir.
    """
    contrato = contrato or leer_contrato()
    ven = contrato["alcance"]["ventana"]
    desde = dt.date.fromisoformat(str(ven["desde"]))
    hasta = dt.date.fromisoformat(str(ven["hasta"]))
    claves, y, m = [], desde.year, desde.month
    while (y, m) <= (hasta.year, hasta.month):
        for q in (1, 2):
            inicio = dt.date(y, m, 1 if q == 1 else 16)
            if inicio <= hasta and inicio >= dt.date(desde.year, desde.month, 1):
                claves.append(f"{y:04d}-{m:02d}-Q{q}")
        m, y = (1, y + 1) if m == 12 else (m + 1, y)
    return claves


QUINCENAS = StaticPartitionsDefinition(quincenas_del_contrato())


def nombres_de_lote(quincena):
    """`2026-07-Q2` → `["07-2026_Q2", "07-2026_02"]`, las dos formas que usa la fuente.

    **La fuente no nombra igual los dos años, y esto costó un error.** Los 24
    archivos de 2025 se llaman `01-2025_01`, `01-2025_02`; los 14 de 2026,
    `01-2026_Q1`, `01-2026_Q2`. Están los 38 listados con su sha256 en
    `docs/datos/ingesta-capa-cruda.md` §«Identidad de los archivos de entrada».

    `ingesta.py` ya lo sabía: su `NOMBRE_DE_LOTE` trae `(?:Q|0)?`, que acepta las
    dos. La primera versión de este envoltorio generaba sólo la forma con `Q`, así
    que las 24 particiones de 2025 no encontraban su archivo. Se devuelven las dos
    y se prueba cada una, en vez de adivinar por año: si la fuente cambia de
    criterio otra vez, sigue funcionando.
    """
    anio, mes, q = quincena.split("-")
    numero = q.removeprefix("Q")
    return [f"{mes}-{anio}_Q{numero}", f"{mes}-{anio}_0{numero}"]


def nombre_de_lote(quincena):
    """El nombre del lote para el registro de la corrida y las etiquetas.

    Se queda con la forma del archivo que de verdad está en la carpeta, para que
    el registro y la evidencia digan el mismo nombre que el archivo. Si no hay
    archivo, la forma con `Q`, que es la que usa el contrato para las quincenas.
    """
    nombres = nombres_de_lote(quincena)
    for nombre in nombres:
        for sufijo in (".parquet", ".csv"):
            if (LOTES / f"{nombre}{sufijo}").exists():
                return nombre
    return nombres[0]


def archivo_del_lote(quincena):
    """El archivo de esa quincena en la carpeta de llegada, o None."""
    for nombre in nombres_de_lote(quincena):
        for sufijo in (".parquet", ".csv"):
            ruta = LOTES / f"{nombre}{sufijo}"
            if ruta.exists():
                return ruta
    return None


def huella_del_lote(registro):
    """La huella que RF-25 compara entre dos materializaciones de la misma partición.

    Son las cifras que `ingesta.py` declara estables al repetir la corrida: el
    sha256 del archivo de entrada y las tres cifras de en medio. La **duración no
    entra**, porque esa cambia siempre y metería ruido en la comparación. Esa
    distinción es de `ingesta.py`, no de aquí.
    """
    cinco = registro.get("cinco_cifras", {})
    material = json.dumps({
        "sha256_entrada": registro.get("sha256_entrada"),
        "filas_escritas": cinco.get("filas_escritas"),
        "objetos": cinco.get("objetos"),
        "bytes": cinco.get("bytes"),
    }, sort_keys=True)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _disparo(context):
    """La marca de tiempo que el sensor dejó en las etiquetas, si la corrida salió
    de un disparo. `None` si alguien materializó a mano."""
    corrida = getattr(context, "run", None)
    etiquetas = getattr(corrida, "tags", None) or {}
    return etiquetas.get("canastamx/disparo")


# ── Activo 1 · la capa cruda ───────────────────────────────────────────────

@asset(
    partitions_def=QUINCENAS,
    description="La capa cruda de una quincena en el bucket. Envuelve ingesta.py: "
                "no reescribe lo que ya hacía, lo corre y lee su registro.",
    compute_kind="duckdb",
)
def capa_cruda(context: AssetExecutionContext) -> dict:
    quincena = context.partition_key
    archivo = archivo_del_lote(quincena)
    if archivo is None:
        buscados = ", ".join(f"{n}{s}" for n in nombres_de_lote(quincena)
                             for s in (".parquet", ".csv"))
        raise FileNotFoundError(
            f"no hay archivo para la quincena {quincena} en {LOTES}. "
            f"Se buscó: {buscados}. "
            "La carpeta se configura con CANASTAMX_LOTES."
        )

    orden = [sys.executable, str(INGESTA / "ingesta.py"), str(archivo),
             "--lote", nombre_de_lote(quincena), "--quincena", quincena]
    if SIMULAR:
        orden.append("--simular")

    context.log.info("corriendo la ingesta: %s", " ".join(orden))
    # check=False a propósito: el código de salida se revisa abajo, para poder
    # dejar la salida completa de la ingesta en el registro antes de fallar.
    # La ingesta escribe → ✓ ⚠ ✗: en UTF-8 de los dos lados, para que en Windows no
    # truene ni se pierda un carácter de la evidencia (ver ingestion/salida_segura.py).
    hecho = subprocess.run(orden, capture_output=True, text=True,
                           encoding=CODIFICACION_DE_LOS_HIJOS, errors="backslashreplace",
                           env=entorno_utf8(), cwd=str(INGESTA), check=False)
    if hecho.returncode != 0:
        # La salida de la ingesta entra al registro de la corrida tal cual: es la
        # evidencia que RF-13 pide para levantar el incidente.
        context.log.error(hecho.stdout[-4000:])
        context.log.error(hecho.stderr[-4000:])
        raise RuntimeError(
            f"la ingesta del lote {quincena} terminó con código "
            f"{hecho.returncode}. Su salida va arriba, completa."
        )
    context.log.info(hecho.stdout[-4000:])

    # En simulación `ingesta.py` no escribe registro —no escribe nada—, así que la
    # huella se arma con lo único que sí está definido: el sha256 del archivo de
    # entrada. Así RF-25 se puede comprobar sin bucket, que es como se prueba.
    registro = {"sha256_entrada": sha256_de(archivo)}
    if not SIMULAR:
        hoy = dt.datetime.now(dt.UTC).date().isoformat()
        ruta = SALIDAS / f"{hoy}-{nombre_de_lote(quincena)}.json"
        if ruta.exists():
            registro = json.loads(ruta.read_text(encoding="utf-8"))

    # `ingerido_en` (SLA-D-10): la hora que el registro de la ingesta le pone a su
    # corrida. En simulación no hay registro —no se escribe nada— y se toma la hora
    # de este activo, que es cuando terminó la ingesta simulada.
    ingerido_en = (registro.get("corrida")
                   or dt.datetime.now(dt.UTC).isoformat(timespec="seconds"))

    cinco = registro.get("cinco_cifras", {})
    context.add_output_metadata({
        "quincena": quincena,
        "archivo": str(archivo),
        "simulado": SIMULAR,
        "filas_escritas": cinco.get("filas_escritas"),
        "objetos": cinco.get("objetos"),
        "huella": huella_del_lote(registro),
        "ingerido_en": ingerido_en,
        "salida": MetadataValue.md(f"```\n{hecho.stdout[-2000:]}\n```"),
    })
    return {"quincena": quincena, "archivo": str(archivo),
            "lote": nombre_de_lote(quincena), "ingerido_en": ingerido_en,
            "simulado": SIMULAR, "registro": registro,
            "huella": huella_del_lote(registro)}


# ── Activo 2 · las filas revisadas, una por una ────────────────────────────

@asset(
    partitions_def=QUINCENAS,
    description="Pandera contra el contrato, fila por fila. La cuarentena lleva un "
                "motivo por fila, y el esquema se genera del contrato: ninguna "
                "regla escrita a mano (ADR 018).",
    compute_kind="pandera",
)
def filas_revisadas(context: AssetExecutionContext, capa_cruda: dict) -> dict:
    contrato = leer_contrato()
    ruta = Path(capa_cruda["archivo"])
    # El ALCANCE, no el archivo: las mismas filas que la ingesta escribió al
    # bucket en el activo anterior. Ver `compuerta.leer_alcance()` y por qué
    # leer el archivo entero medía el 5% de D-07 sobre la población equivocada.
    df = compuerta.leer_alcance(ruta, contrato)

    # Lo que el linaje lleva hasta la capa intermedia: de qué lote y a qué hora.
    traza = {"lote": capa_cruda.get("lote") or nombre_de_lote(capa_cruda["quincena"]),
             "ingerido_en": capa_cruda.get("ingerido_en")}

    limpias, registros, resumen = compuerta.revisar_lote(df, contrato, ruta.name)
    if limpias is None:
        # Nivel LOTE: le falta una columna al archivo entero. No hay filas que
        # revisar, y el lote no se ingiere a medias (CU-02 · 2b).
        context.add_output_metadata({"resultado": resumen["resultado"],
                                     "motivo_lote": resumen["motivo_lote"]})
        return {"quincena": capa_cruda["quincena"], "resumen": resumen,
                "detenido": True, "registros": [], "limpias": None, **traza}

    SALIDAS.mkdir(parents=True, exist_ok=True)
    lote_nombre = nombre_de_lote(capa_cruda["quincena"])
    jsonl = SALIDAS / f"cuarentena-fila-{lote_nombre}.jsonl"
    with jsonl.open("w", encoding="utf-8") as f:
        for r in registros:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    context.add_output_metadata({
        "filas_entrada": resumen["filas_entrada"],
        "filas_en_cuarentena": resumen["filas_en_cuarentena"],
        "filas_salida": resumen["filas_salida"],
        "por_motivo": MetadataValue.json(resumen["por_motivo"]),
        "cuarentena": str(jsonl),
    })
    return {"quincena": capa_cruda["quincena"], "resumen": resumen,
            "detenido": False, "registros": registros,
            # El marco viaja tal cual: conserva sus tipos —la fecha tipada del
            # parquet— y sus columnas aunque no sobreviva ninguna fila.
            "limpias": limpias, **traza}


# ── Activo 3 · la decisión de promover el lote ─────────────────────────────

def _registrar_lote(context, contrato, lote_nombre, quincena, resumen, frescura):
    """El registro del lote, que `intermedia.py --verificar` lee para comprobar la
    capa contra su linaje. Se escribe en TODA corrida, también en la que se detiene
    porque al archivo le falta una columna: si no, quedaría el de la corrida
    anterior, y la comprobación cuadraría contra otro resultado."""
    SALIDAS.mkdir(parents=True, exist_ok=True)
    registro = SALIDAS / f"lote-{lote_nombre}.json"
    registro.write_text(json.dumps({
        "lote": lote_nombre, "quincena": quincena,
        # Con qué contrato se juzgó y contra qué fecha se midió la frescura. Las
        # dos son columnas NOT NULL de la tabla `corrida` del esquema de
        # operación, y sin ellas un registro viejo y uno nuevo se ven iguales: el
        # 15 de octubre, después de la 1.3.5, se leyó un registro de la 1.3.4 y lo
        # único que avisó fue un KeyError.
        "version_contrato": contrato["version"],
        "fecha_de_referencia": (frescura or {}).get("fecha_referencia") or FECHA_REFERENCIA,
        "corrida": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        # El instante del disparo lo pone el sensor en las etiquetas. En una
        # corrida hecha a mano no hay, y eso no es un error: es que nadie la
        # disparó. H2 sólo se mide sobre las que disparó el sensor.
        "disparo": _disparo(context),
        "resumen": resumen,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return registro


@asset(
    partitions_def=QUINCENAS,
    description="Lo que necesita el lote completo: el `?` que no se puede reparar "
                "(CU-03), la colisión de precio alta por grupo y la frescura, en "
                "DuckDB. Después el 5% de D-07 sobre las tres cuarentenas juntas.",
    compute_kind="duckdb",
)
def lote_promovido(context: AssetExecutionContext, filas_revisadas: dict) -> dict:
    contrato = leer_contrato()
    quincena = filas_revisadas["quincena"]
    lote_nombre = filas_revisadas.get("lote") or nombre_de_lote(quincena)
    traza = {"quincena": quincena, "lote": lote_nombre,
             "ingerido_en": filas_revisadas.get("ingerido_en")}

    if filas_revisadas["detenido"]:
        resumen = dict(filas_revisadas["resumen"])
        registro = _registrar_lote(context, contrato, lote_nombre, quincena, resumen, None)
        context.add_output_metadata({"resultado": resumen["resultado"],
                                     "motivo_lote": resumen.get("motivo_lote"),
                                     "registro": str(registro)})
        return {**traza, "resumen": resumen, "promovidas": None}

    limpias = filas_revisadas["limpias"]
    por_fila = filas_revisadas["resumen"]

    # CU-03 · el `?` que no se puede reparar va a cuarentena ANTES de las reglas de
    # grupo y del 5%: así cuenta para D-07, y los grupos se forman con el texto ya
    # reparado (las filas siguen tal como llegaron; la reparación la aplica la
    # capa intermedia, con el mismo mapa).
    reparables, rep_registros, res_rep = reparacion.apartar_irreparables(limpias, contrato)
    promovibles, grupos, res_grupo = reglas_de_lote.revisar_grupos(reparables, contrato)
    frescura = reglas_de_lote.revisar_frescura(
        limpias, contrato, FECHA_REFERENCIA)

    # El umbral de D-07 se evalúa sobre las TRES cuarentenas. Si se evaluara sólo
    # sobre la de fila, un lote lleno de colisiones altas o de texto irreparable
    # pasaría por debajo del 5%. Son conjuntos de filas que no se tocan: cada etapa
    # recibe lo que la anterior dejó pasar.
    etapas = (por_fila, res_rep, res_grupo)
    resumen = {
        "filas_entrada": por_fila["filas_entrada"],
        "filas_en_cuarentena": sum(e["filas_en_cuarentena"] for e in etapas),
        "registros_de_cuarentena": sum(e["registros_de_cuarentena"] for e in etapas),
        "filas_salida": res_grupo["filas_salida"],
        "por_motivo": {**por_fila["por_motivo"], **res_rep["por_motivo"],
                       **res_grupo["por_motivo"]},
        "por_fila": por_fila,
        "por_reparacion": res_rep,
        "por_grupo": res_grupo,
        "frescura": frescura,
    }
    resumen = compuerta.decidir_promocion(resumen, contrato)

    SALIDAS.mkdir(parents=True, exist_ok=True)
    for nombre, filas in (("reparacion", rep_registros), ("grupo", grupos)):
        with (SALIDAS / f"cuarentena-{nombre}-{lote_nombre}.jsonl").open(
                "w", encoding="utf-8") as f:
            for r in filas:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    registro = _registrar_lote(context, contrato, lote_nombre, quincena, resumen, frescura)

    context.add_output_metadata({
        "resultado": resumen["resultado"],
        "proporcion_en_cuarentena": resumen["proporcion_en_cuarentena"],
        "umbral": resumen["umbral"],
        "filas_salida": resumen["filas_salida"],
        "grupos_en_colision": res_grupo["grupos_en_colision"],
        # Los tres cubos de la clave de fila, en grupos y filas sobrantes: es lo
        # que el contrato 1.3.3 pidió volver a medir en la primera corrida, y
        # contra lo que `capa_intermedia` comprueba su deduplicación.
        "cubos_de_la_clave": MetadataValue.json({
            cubo: {"grupos": res_grupo[f"grupos_{cubo}"],
                   "sobrantes": res_grupo[f"sobrantes_{cubo}"]}
            for cubo in ("captura_doble", "observaciones_multiples", "en_colision")}),
        # CU-03 · paso 4: cuántos valores se repararon en cada columna, y cuántas
        # filas se apartaron y por qué.
        "reparacion": MetadataValue.json({
            "por_columna": res_rep["por_columna"],
            "valores_reparados": res_rep["valores_reparados"],
            "filas_en_cuarentena": res_rep["filas_en_cuarentena"],
            "por_motivo": res_rep["por_motivo"]}),
        "frescura": MetadataValue.json(frescura),
        "por_motivo": MetadataValue.json(resumen["por_motivo"]),
        "registro": str(registro),
        "version_contrato": contrato["version"],
    })
    # Un lote detenido no deja salir nada: D-07 dice que no se promueve ni la parte
    # que pasó.
    salen = None if resumen["resultado"] == "DETENIDO" else promovibles
    return {**traza, "resumen": resumen, "promovidas": salen}


# ── Activo 4 · la capa intermedia (T048) ───────────────────────────────────

@asset(
    partitions_def=QUINCENAS,
    description="La capa intermedia del lote: el texto reparado, el precio tipado "
                "y sin captura doble, en postgres-analytics. Reemplaza la "
                "partición; un lote detenido la deja vacía.",
    compute_kind="duckdb",
)
def capa_intermedia(context: AssetExecutionContext, lote_promovido: dict) -> dict:
    contrato = leer_contrato()
    quincena, lote_nombre = lote_promovido["quincena"], lote_promovido["lote"]
    resumen = lote_promovido["resumen"]
    promovidas = lote_promovido.get("promovidas")
    ingerido_en = lote_promovido.get("ingerido_en")

    if promovidas is None:
        con, res_capa = intermedia.capa_vacia(contrato), {
            "filas_entrada": 0, "sobrantes_captura_doble": 0, "filas_salida": 0,
            "reparadas_por_columna": {}}
        esperadas = 0
    else:
        if not ingerido_en:
            raise RuntimeError(f"el lote {lote_nombre} llegó sin `ingerido_en`: la capa "
                               "cruda tenía que dejarlo en el linaje (SLA-D-10)")
        con, res_capa = intermedia.construir(promovidas, contrato, lote_nombre, ingerido_en)
        # El criterio de T048, comprobado en cada corrida y no sólo en las pruebas:
        # exactamente las que dejó salir el lote menos las sobrantes de captura
        # doble que contó la compuerta de grupo.
        esperadas = (resumen["filas_salida"]
                     - resumen["por_grupo"]["sobrantes_captura_doble"])
        if res_capa["filas_salida"] != esperadas:
            raise RuntimeError(
                f"la capa intermedia de {lote_nombre} tiene {res_capa['filas_salida']:,} "
                f"filas y el linaje dice {esperadas:,} ({resumen['filas_salida']:,} que "
                f"dejó salir el lote − {resumen['por_grupo']['sobrantes_captura_doble']:,} "
                "sobrantes de captura doble). No se carga una cuenta que no cuadra")

    huella = intermedia.huella_de_la_capa(con)
    destino = intermedia.cargar(con, lote_nombre, contrato, simular=SIMULAR)

    context.add_output_metadata({
        "lote": lote_nombre,
        "resultado_del_lote": resumen["resultado"],
        "filas_cargadas": res_capa["filas_salida"],
        "filas_esperadas": esperadas,
        "sobrantes_quitadas": res_capa["sobrantes_captura_doble"],
        "reparadas_por_columna": MetadataValue.json(res_capa["reparadas_por_columna"]),
        "huella": huella,
        "ingerido_en": ingerido_en,
        "destino": MetadataValue.json({k: v for k, v in destino.items()}),
        "version_contrato": contrato["version"],
    })
    return {"quincena": quincena, "lote": lote_nombre,
            "filas": res_capa["filas_salida"], "huella": huella}


# ── El sensor ──────────────────────────────────────────────────────────────

# La partición NO se repite aquí: Dagster la deduce de los activos
# seleccionados, y pasarla es redundante desde la 1.11.
corrida_del_lote = define_asset_job(
    "corrida_del_lote",
    selection=[capa_cruda, filas_revisadas, lote_promovido, capa_intermedia],
)


@sensor(
    job=corrida_del_lote,
    minimum_interval_seconds=30,
    description="Dispara al aparecer un archivo nuevo en la carpeta de llegada. "
                "La marca de tiempo del disparo es el cero de H2 (SLA-D-05).",
)
def archivo_nuevo(context: SensorEvaluationContext):
    if not LOTES.exists():
        return SkipReason(f"la carpeta de llegada no existe: {LOTES}")

    visto = json.loads(context.cursor) if context.cursor else {}
    peticiones, nuevo = [], dict(visto)

    for quincena in quincenas_del_contrato():
        ruta = archivo_del_lote(quincena)
        if ruta is None:
            continue
        # La firma es tamaño y fecha de modificación: con eso basta para saber que
        # el archivo cambió, y no hay que leerlo entero en cada vuelta del sensor.
        st = ruta.stat()
        firma = f"{st.st_size}:{int(st.st_mtime)}"
        if visto.get(quincena) == firma:
            continue
        nuevo[quincena] = firma
        disparo = dt.datetime.now(dt.UTC).isoformat(timespec="seconds")
        peticiones.append(RunRequest(
            run_key=f"{quincena}:{firma}",
            partition_key=quincena,
            # El instante del disparo viaja con la corrida. H2 se mide de aquí al
            # incidente, así que tiene que quedar escrito al disparar, no después.
            tags={"canastamx/disparo": disparo,
                  "canastamx/lote": nombre_de_lote(quincena)},
        ))
        context.log.info("archivo nuevo para %s · disparo %s", quincena, disparo)

    if not peticiones:
        return SkipReason("ningún archivo nuevo en la carpeta de llegada")
    return SensorResult(run_requests=peticiones,
                        cursor=json.dumps(nuevo, sort_keys=True))


defs = Definitions(
    assets=[capa_cruda, filas_revisadas, lote_promovido, capa_intermedia],
    jobs=[corrida_del_lote],
    sensors=[archivo_nuevo],
)
