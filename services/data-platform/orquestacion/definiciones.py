"""CanastaMX · los tres activos particionados y el sensor (ADR 016).

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

## Los tres activos

    capa_cruda ──> filas_revisadas ──> lote_promovido
    (ingesta.py)   (compuerta.py)      (lote.py + D-07)

1. **`capa_cruda`** envuelve `ingestion/ingesta.py`. No lo reescribe: lo corre y
   lee su registro de corrida. Lo que ya hacía —controles C1, `?` en los filtros,
   filas de otra quincena, escritura particionada— sigue siendo suyo.
2. **`filas_revisadas`** llama a `compuerta.revisar_lote()`: Pandera contra el
   contrato, fila por fila, y la cuarentena con un motivo por fila.
3. **`lote_promovido`** llama a `lote.revisar_grupos()` y
   `lote.revisar_frescura()` —lo que necesita el lote completo— y después a
   `compuerta.decidir_promocion()`, que aplica el 5% de D-07 **sobre las dos
   cuarentenas juntas**. Ése es el orden correcto y no es un detalle: si el umbral
   se evaluara antes de las reglas de grupo, un lote con muchas colisiones altas
   pasaría por debajo del 5% y se promovería.

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
    dagster dev -m orquestacion.definiciones

Necesita `dagster` **y** `dagster-webserver`, las dos en la misma versión. Están
en `requirements.txt`; con sólo la primera, `dagster dev` falla pidiendo la otra.
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
import lote as reglas_de_lote
from ingesta import leer_contrato, sha256_de

SALIDAS = INGESTA / "corridas"

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


def _leer_lote(ruta):
    import pandas as pd

    if ruta.suffix.lower() == ".parquet":
        return pd.read_parquet(ruta)
    return pd.read_csv(ruta, dtype="string", keep_default_na=False, na_values=[""])


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
    hecho = subprocess.run(orden, capture_output=True, text=True,
                           cwd=str(INGESTA), check=False)
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

    cinco = registro.get("cinco_cifras", {})
    context.add_output_metadata({
        "quincena": quincena,
        "archivo": str(archivo),
        "simulado": SIMULAR,
        "filas_escritas": cinco.get("filas_escritas"),
        "objetos": cinco.get("objetos"),
        "huella": huella_del_lote(registro),
        "salida": MetadataValue.md(f"```\n{hecho.stdout[-2000:]}\n```"),
    })
    return {"quincena": quincena, "archivo": str(archivo),
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
    df = _leer_lote(ruta)

    limpias, registros, resumen = compuerta.revisar_lote(df, contrato, ruta.name)
    if limpias is None:
        # Nivel LOTE: le falta una columna al archivo entero. No hay filas que
        # revisar, y el lote no se ingiere a medias (CU-02 · 2b).
        context.add_output_metadata({"resultado": resumen["resultado"],
                                     "motivo_lote": resumen["motivo_lote"]})
        return {"quincena": capa_cruda["quincena"], "resumen": resumen,
                "detenido": True, "registros": [], "limpias": None}

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
            # Las columnas viajan aparte: un lote del que no sobrevive ninguna
            # fila es un resultado posible, y `DataFrame([])` pierde las columnas.
            "columnas": list(limpias.columns),
            "limpias": limpias.to_dict("records")}


# ── Activo 3 · la decisión de promover el lote ─────────────────────────────

@asset(
    partitions_def=QUINCENAS,
    description="Lo que necesita el lote completo: colisión de precio alta por "
                "grupo y frescura, en DuckDB. Después el 5% de D-07 sobre las dos "
                "cuarentenas juntas.",
    compute_kind="duckdb",
)
def lote_promovido(context: AssetExecutionContext, filas_revisadas: dict) -> dict:
    import pandas as pd

    contrato = leer_contrato()
    quincena = filas_revisadas["quincena"]
    lote_nombre = nombre_de_lote(quincena)

    if filas_revisadas["detenido"]:
        resumen = dict(filas_revisadas["resumen"])
        context.add_output_metadata({"resultado": resumen["resultado"],
                                     "motivo_lote": resumen.get("motivo_lote")})
        return {"quincena": quincena, "resumen": resumen}

    limpias = pd.DataFrame(filas_revisadas["limpias"],
                           columns=filas_revisadas["columnas"],
                           dtype="string")
    por_fila = filas_revisadas["resumen"]

    _, grupos, res_grupo = reglas_de_lote.revisar_grupos(limpias, contrato)
    frescura = reglas_de_lote.revisar_frescura(
        limpias, contrato, FECHA_REFERENCIA)

    # El umbral de D-07 se evalúa sobre las DOS cuarentenas. Si se evaluara sólo
    # sobre la de fila, un lote lleno de colisiones altas pasaría por debajo del 5%.
    resumen = {
        "filas_entrada": por_fila["filas_entrada"],
        "filas_en_cuarentena": (por_fila["filas_en_cuarentena"]
                                + res_grupo["filas_en_cuarentena"]),
        "registros_de_cuarentena": (por_fila["registros_de_cuarentena"]
                                    + res_grupo["registros_de_cuarentena"]),
        "filas_salida": res_grupo["filas_salida"],
        "por_motivo": {**por_fila["por_motivo"], **res_grupo["por_motivo"]},
        "por_fila": por_fila,
        "por_grupo": res_grupo,
        "frescura": frescura,
    }
    resumen = compuerta.decidir_promocion(resumen, contrato)

    SALIDAS.mkdir(parents=True, exist_ok=True)
    jsonl = SALIDAS / f"cuarentena-grupo-{lote_nombre}.jsonl"
    with jsonl.open("w", encoding="utf-8") as f:
        for r in grupos:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    registro = SALIDAS / f"lote-{lote_nombre}.json"
    registro.write_text(json.dumps({
        "lote": lote_nombre, "quincena": quincena,
        "corrida": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        # El instante del disparo lo pone el sensor en las etiquetas. En una
        # corrida hecha a mano no hay, y eso no es un error: es que nadie la
        # disparó. H2 sólo se mide sobre las que disparó el sensor.
        "disparo": _disparo(context),
        "resumen": resumen,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    context.add_output_metadata({
        "resultado": resumen["resultado"],
        "proporcion_en_cuarentena": resumen["proporcion_en_cuarentena"],
        "umbral": resumen["umbral"],
        "filas_salida": resumen["filas_salida"],
        "grupos_en_colision": res_grupo["grupos_en_colision"],
        "frescura": MetadataValue.json(frescura),
        "por_motivo": MetadataValue.json(resumen["por_motivo"]),
        "registro": str(registro),
    })
    return {"quincena": quincena, "resumen": resumen}


# ── El sensor ──────────────────────────────────────────────────────────────

# La partición NO se repite aquí: Dagster la deduce de los activos
# seleccionados, y pasarla es redundante desde la 1.11.
corrida_del_lote = define_asset_job(
    "corrida_del_lote",
    selection=[capa_cruda, filas_revisadas, lote_promovido],
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
    assets=[capa_cruda, filas_revisadas, lote_promovido],
    jobs=[corrida_del_lote],
    sensors=[archivo_nuevo],
)
