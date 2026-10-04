#!/usr/bin/env python3
"""
ingesta.py — CanastaMX · T020 · primer guión de ingesta a la capa cruda

QUÉ HACE
--------
Toma un archivo del corpus congelado de QQP y lo deposita **tal como llegó** en
la capa cruda (MinIO, bucket `canastamx-bronze`), en Parquet particionado por
`estado` y por `quincena`.

EL RECORTE DEL ALCANCE SE APLICA AQUÍ
-------------------------------------
Los TRES recortes que `medicion.poblacion` nombra —«entidades del alcance ∩
ventana ∩ catálogos del ADR 005»— se leen del contrato y se aplican antes de
escribir. Son **7 entidades**, **5 catálogos** y una ventana: el «5» es de los
catálogos, no de los estados.

**Por qué al ingerir y no después.** Porque el corpus está congelado y vive en
disco: si el ADR 001 o el ADR 005 cambian, volver a ingerir los 38 archivos
cuesta unos ochenta segundos. El argumento de «guardar todo para poder
reprocesar» pesa cuando volver a conseguir el dato es caro, y aquí no lo es. A
cambio, la capa cruda deja de contener dos poblaciones a la vez, que es la
confusión que este contrato ya cometió tres veces (ver `medicion.advertencia`).

Para reprocesar sin recorte: `--sin-recorte`.

QUÉ **NO** HACE, a propósito
----------------------------
    · No limpia.       Los `?` de la codificación rota se quedan como están.
    · No valida.       Ningún precio se rechaza por imposible.
    · No normaliza.    `S/m` y `S/M` siguen siendo dos literales distintos.
    · No deduplica.    Las filas que colisionan por clave siguen las dos.
    · No descarga.     El corpus está congelado en 2026-07-Q2 (ADR 010 · 9).

Todo eso es de la **semana 6**, cuando entra la compuerta de calidad contra
`contracts/qqp-v1.yaml`. La capa cruda guarda la basura a propósito: es lo que
permite reprocesar si mañana se descubre que la limpieza estaba mal, sin volver
a bajar nada.

LA CODIFICACIÓN Y LA FECHA LAS DECLARA EL CONTRATO, NO LAS ADIVINA DUCKDB
------------------------------------------------------------------------
Éste es el punto que distingue este guión de un `read_csv_auto` cualquiera.
`archivo.codificacion` y `archivo.formato_de_fecha` del contrato se leen y se
pasan explícitos. Sin eso, DuckDB adivina — y `05/03/2026` es el 5 de marzo o
el 3 de mayo según lo que adivine, **sin dejar rastro**: la fecha sale válida y
la partición sale plausible. perfilado.md §1 lo midió: un solo formato para
todos intercambiaría día y mes en 1,007,082 filas.

Con un `.parquet` no aplica: los tipos ya vienen resueltos.

LAS DOS COLUMNAS QUE SE AGREGAN
-------------------------------
Dos, y las dos son **llaves de partición**, no limpieza. Las 15 columnas del
contrato entran intactas, con sus acentos como vinieron.

`quincena`, derivada de `fecha_registro`: día 1 al 15 → `Q1`, del 16 en
adelante → `Q2`. La fuente publica por quincena.

`entidad`, derivada de `estado`: el literal normalizado y devuelto a la
escritura canónica del contrato. Existe porque la fuente trae **37 literales
para 30 entidades** —2025 escribe `Michoacan`, 2026 `Michoacán`— y particionar
por el literal crudo deja el mismo estado en DOS carpetas, en silencio, hasta
que un conteo por estado sale partido a la mitad.

IDEMPOTENCIA
------------
Correrlo dos veces deja exactamente el mismo resultado. Se consigue en dos
pasos, y los dos importan:

    1. antes de escribir, se **borran los objetos de las particiones que este
       lote va a tocar** —no el bucket entero, sólo esas—;
    2. el COPY usa `OVERWRITE_OR_IGNORE`, que conserva las particiones que no
       toca y reusa el nombre `data_0.parquet` dentro de las que sí.

**NO se usa `OVERWRITE`**, y la diferencia no se deduce del nombre: `OVERWRITE`
borra el DIRECTORIO COMPLETO en cada `COPY`, así que con un lote por archivo cada
uno borraría al anterior y el bucket terminaría con el último nada más. Tampoco
`APPEND`, que conserva lo demás pero nombra con UUID y duplicaría al reescribir.

El borrado explícito sigue haciendo falta aun con la opción correcta: si una
partición tenía `data_0` y `data_1` y ahora sólo se escribe `data_0`, el viejo
sobreviviría.

CONFIGURACIÓN — nada de esto va escrito en el código
----------------------------------------------------
    S3_ENDPOINT     http://minio:9000
    S3_ACCESS_KEY
    S3_SECRET_KEY
    S3_BUCKET       canastamx-bronze

Son los nombres nuevos que decidió el ADR 009. Si tu `.env` todavía dice
`MINIO_*`, ése es el error de `Access Denied` más común.

USO
---
    python services/data-platform/ingestion/ingesta.py <archivo> [--simular]

    # lote con nombre propio, para el registro de la corrida
    python services/data-platform/ingestion/ingesta.py datos.parquet --lote 2026-07-Q2
"""

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

RAIZ = Path(__file__).resolve().parents[3]
CONTRATO = RAIZ / "contracts" / "qqp-v1.yaml"
CORRIDAS = Path(__file__).resolve().parent / "corridas"
PREFIJO = "qqp"

# Día 1–15 → Q1 · 16 en adelante → Q2. Es la convención de la fuente.
QUINCENA = ("strftime(fecha_registro, '%Y-%m') || '-Q' || "
            "CASE WHEN extract(day FROM fecha_registro) <= 15 THEN '1' ELSE '2' END")


# Contrato · `archivo.codificacion.compuerta_extra`. Los caracteres de control C1
# (U+0080 a U+009F) son bytes de Windows-1252 o de DOS leídos como latin-1: no se
# ven, no rompen el parseo y contaminan el texto en silencio.
COMPUERTA_C1 = "detectar_controles_C1"
PATRON_C1 = r"[\x{80}-\x{9F}]"
# Los dos rastros visibles de una codificación rota: el `?` y el carácter de
# reemplazo. En `estado` o `catalogo` impiden saber si la fila es del alcance.
PATRON_ROTO = r"[?\x{FFFD}]"
# Nombre de archivo de la fuente → quincena del lote: 01-2025_01, 07-2026_Q2.
NOMBRE_DE_LOTE = re.compile(r"^(\d{2})-(\d{4})_(?:Q|0)?([12])$")


def morir(mensaje):
    print(f"\n✗ {mensaje}", file=sys.stderr)
    sys.exit(1)


def leer_contrato():
    try:
        import yaml
    except ImportError:
        morir("falta PyYAML.  pip install pyyaml")
    if not CONTRATO.exists():
        morir(f"no encuentro el contrato en {CONTRATO}")
    with open(CONTRATO, encoding="utf-8") as f:
        return yaml.safe_load(f)


def columnas_del_contrato(contrato):
    """Las 15 columnas, en el orden que el contrato declara. No se escriben
    aquí: si el contrato cambia, este guión cambia con él."""
    cols = list(contrato["columnas"].keys())
    if len(cols) != 15:
        morir(f"el contrato declara {len(cols)} columnas y se esperaban 15")
    return cols


# Traductor de los formatos que el contrato escribe a los que DuckDB entiende.
# Se escribe aquí y no en el contrato porque el contrato declara la REGLA en
# notación humana; traducirla es cosa de quien la implementa.
_FMT = {"YYYY/MM/DD": "%Y/%m/%d", "DD/MM/YYYY": "%d/%m/%Y",
        "YYYY-MM-DD": "%Y-%m-%d", "MM/DD/YYYY": "%m/%d/%Y"}


def lectura_declarada(contrato, nombre):
    """Codificación y formato de fecha que el contrato declara PARA ESTE ARCHIVO.

    Por qué existe esta función, y es el punto entero: DuckDB adivina las dos
    cosas si no se le dicen, y adivinar `DD/MM/YYYY` contra `MM/DD/YYYY` es
    imposible cuando todos los días del archivo son <= 12. `05/03/2026` es el
    5 de marzo o el 3 de mayo según lo que se elija, y el error NO deja rastro:
    la fecha sale válida, la partición sale plausible, y nadie se entera.

    perfilado.md §1 lo midió: leer todo con un solo formato intercambiaría día
    y mes en 1,007,082 filas. El contrato ya declara el formato por archivo
    (`archivo.formato_de_fecha`). Este guión lo OBEDECE en vez de dejar que se
    adivine, que es la diferencia entre un contrato ejecutado y un contrato
    decorativo.
    """
    arch = contrato.get("archivo", {})
    cod = arch.get("codificacion", {})
    fec = arch.get("formato_de_fecha", {})

    encoding = cod.get("excepciones", {}).get(nombre) or cod.get("por_defecto", "utf-8")
    humano = fec.get("excepciones", {}).get(nombre) or fec.get("por_defecto", "YYYY/MM/DD")
    if humano not in _FMT:
        morir(f"el contrato declara el formato de fecha {humano!r} y este guión "
              f"no sabe traducirlo. Formatos conocidos: {', '.join(_FMT)}")

    es_excepcion = (nombre in cod.get("excepciones", {})
                    or nombre in fec.get("excepciones", {}))
    return {
        "encoding": "utf-8" if encoding == "utf-8-sig" else encoding,
        "dateformat": _FMT[humano],
        "humano": humano,
        "es_excepcion": es_excepcion,
    }


def recorte_del_contrato(contrato):
    """Los TRES recortes del alcance, leídos del contrato. No se escriben aquí.

    `medicion.poblacion` los nombra: «entidades del alcance ∩ ventana ∩ catálogos
    del ADR 005». Son tres y conviene no confundirlos: **7 entidades**, **5
    catálogos** y una ventana. El «5» es de los catálogos, no de los estados.

    `estado` y `catalogo` se comparan NORMALIZADOS —mayúsculas sin acentos, que es
    lo que declara `normalizacion.estado.a` y `normalizacion.catalogo.a`— porque la
    fuente trae `Michoacan` junto a `Michoacán` y `Basicos` junto a `Básicos`. Sin
    normalizar se pierden 121,491 filas de Básicos y 8,704 de PACIC, medidas.
    """
    al = contrato["alcance"]
    ent = al["entidades"]
    cat = al["catalogos_normalizados"]
    ven = al["ventana"]
    if not ven.get("desde") or not ven.get("hasta"):
        morir("`alcance.ventana` no está cerrada en el contrato; el recorte "
              "temporal no se puede aplicar. Corre con --sin-recorte o cierra la "
              "ventana (ADR 010 · 9).")

    def lista(valores):
        return ", ".join(
            f"upper(strip_accents('{v.replace(chr(39), chr(39) * 2)}'))"
            for v in valores)

    # Llave de partición canónica para `estado`. La fuente trae 37 literales
    # para 30 entidades: 2025 escribe `Michoacan` y 2026 `Michoacán`
    # (perfilado.md §1). Si se particiona por el literal crudo, el mismo estado
    # cae en DOS carpetas y nadie se entera hasta que un conteo por estado sale
    # partido. `entidad` es la llave; el literal crudo se conserva intacto en la
    # columna `estado`, que es lo que la capa cruda promete.
    casos = " ".join(
        f"WHEN upper(strip_accents(trim(estado))) = "
        f"upper(strip_accents('{e.replace(chr(39), chr(39) * 2)}')) "
        f"THEN '{e.replace(chr(39), chr(39) * 2)}'"
        for e in ent)
    entidad_sql = (f"CASE {casos} ELSE upper(strip_accents(trim(estado))) END")

    return {
        "entidades": ent,
        "catalogos": cat,
        "ventana": (ven["desde"], ven["hasta"]),
        "entidad_sql": entidad_sql,
        "sql": {
            "estado":   f"upper(strip_accents(trim(estado))) IN ({lista(ent)})",
            "catalogo": f"upper(strip_accents(trim(catalogo))) IN ({lista(cat)})",
            "ventana":  (f"CAST(fecha_registro AS DATE) BETWEEN "
                         f"DATE '{ven['desde']}' AND DATE '{ven['hasta']}'"),
        },
    }


def entorno(exigir=True):
    """Con `exigir=False` (modo simulación) no reclama las variables: una corrida
    en seco tiene que poder hacerse SIN levantar MinIO. Si no, el ensayo obliga a
    tener en pie justamente lo que se quería ensayar sin tocar."""
    faltan = [v for v in ("S3_ENDPOINT", "S3_ACCESS_KEY", "S3_SECRET_KEY", "S3_BUCKET")
              if not os.environ.get(v)]
    if faltan and exigir:
        morir("faltan variables de entorno: " + ", ".join(faltan)
              + "\n  Si tu .env todavía usa MINIO_*, renómbralas (ADR 009).")
    if faltan:
        print("· simulación sin S3: faltan " + ", ".join(faltan)
              + " y no hacen falta para leer\n")
        return None
    url = urlparse(os.environ["S3_ENDPOINT"])
    if not url.netloc:
        morir(f"S3_ENDPOINT mal formado: {os.environ['S3_ENDPOINT']!r}. "
              "Se espera algo como http://minio:9000")
    return {
        "host": url.netloc,
        "ssl": url.scheme == "https",
        "endpoint": os.environ["S3_ENDPOINT"],
        "llave": os.environ["S3_ACCESS_KEY"],
        "secreto": os.environ["S3_SECRET_KEY"],
        "bucket": os.environ["S3_BUCKET"],
    }


def sha256_de(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloque)
    return h.hexdigest()


def conectar_duckdb(cfg):
    """Sin `cfg` (simulación) no carga httpfs: leer un archivo local no necesita
    la extensión de S3, y cargarla exige red. Un ensayo en seco no debe depender
    de que haya internet ni de que MinIO esté arriba."""
    import duckdb
    con = duckdb.connect()
    if cfg is None:
        return con
    con.sql("INSTALL httpfs; LOAD httpfs;")
    con.sql(f"SET s3_endpoint='{cfg['host']}'")
    con.sql(f"SET s3_access_key_id='{cfg['llave']}'")
    con.sql(f"SET s3_secret_access_key='{cfg['secreto']}'")
    con.sql("SET s3_url_style='path'")          # MinIO no usa subdominios
    con.sql(f"SET s3_use_ssl={'true' if cfg['ssl'] else 'false'}")
    con.sql("SET s3_region='us-east-1'")        # MinIO la ignora, boto3 la exige
    return con


def cliente_s3(cfg):
    try:
        import boto3
    except ImportError:
        morir("falta boto3.  pip install boto3")
    return boto3.client("s3", endpoint_url=cfg["endpoint"],
                        aws_access_key_id=cfg["llave"],
                        aws_secret_access_key=cfg["secreto"],
                        region_name="us-east-1")


def lector(ruta, decl):
    ext = Path(ruta).suffix.lower()
    if ext == ".parquet":
        # El parquet ya trae los tipos resueltos; no hay nada que adivinar.
        return f"read_parquet('{ruta}')"
    if ext in (".csv", ".txt"):
        return (f"read_csv('{ruta}', header=true, "
                f"encoding='{decl['encoding']}', "
                f"dateformat='{decl['dateformat']}')")
    morir(f"no sé leer {ext}. Se esperaba .parquet o .csv")


def controles_c1(con, columnas_texto):
    """Cuántas filas traen un control C1 en alguna columna de texto, y ejemplos."""
    cond = " OR ".join(f"regexp_matches({c}, '{PATRON_C1}')" for c in columnas_texto)
    n = con.sql(f"SELECT count(*) FROM entrada WHERE {cond}").fetchone()[0]
    ejemplos = []
    for c in columnas_texto if n else []:
        ejemplos += [(c, v) for (v,) in con.sql(
            f"SELECT DISTINCT {c} FROM entrada "
            f"WHERE regexp_matches({c}, '{PATRON_C1}') LIMIT 3").fetchall()]
        if len(ejemplos) >= 3:
            break
    return n, ejemplos[:3]


def interrogantes_en_filtros(con):
    """Filas con `?` o con el carácter de reemplazo en estado o catalogo."""
    filas = con.sql(f"""SELECT estado, catalogo, count(*) AS n FROM entrada
                        WHERE regexp_matches(estado, '{PATRON_ROTO}')
                           OR regexp_matches(catalogo, '{PATRON_ROTO}')
                        GROUP BY ALL ORDER BY n DESC""").fetchall()
    return sum(f[2] for f in filas), filas[:5]


def quincena_del_lote(nombre):
    """La quincena que le toca a un lote por su nombre, o None si no la dice."""
    m = NOMBRE_DE_LOTE.match(nombre)
    return f"{m.group(2)}-{m.group(1)}-Q{m.group(3)}" if m else None


def borrar_prefijo(s3, bucket, prefijo):
    """Borra todos los objetos bajo un prefijo. Devuelve cuántos borró."""
    borrados = 0
    pag = s3.get_paginator("list_objects_v2")
    for pagina in pag.paginate(Bucket=bucket, Prefix=prefijo):
        claves = [{"Key": o["Key"]} for o in pagina.get("Contents", [])]
        if claves:
            s3.delete_objects(Bucket=bucket, Delete={"Objects": claves})
            borrados += len(claves)
    return borrados


def inventario(s3, bucket, prefijo):
    objetos = bytes_ = 0
    pag = s3.get_paginator("list_objects_v2")
    for pagina in pag.paginate(Bucket=bucket, Prefix=prefijo):
        for o in pagina.get("Contents", []):
            objetos += 1
            bytes_ += o["Size"]
    return objetos, bytes_


def main():
    ap = argparse.ArgumentParser(description="Ingesta a la capa cruda")
    ap.add_argument("archivo", help="archivo del corpus congelado (.parquet o .csv)")
    ap.add_argument("--lote", help="nombre del lote para el registro de la corrida")
    ap.add_argument("--simular", action="store_true",
                    help="lee y reporta, pero no borra ni escribe nada")
    ap.add_argument("--sin-recorte", action="store_true", dest="sin_recorte",
                    help="ingiere el archivo COMPLETO, sin aplicar el alcance. "
                         "Para reprocesar si el ADR 001 o el ADR 005 cambian")
    ap.add_argument("--quincena", help="la quincena del lote (AAAA-MM-Q1) si su "
                                       "nombre no sigue el de la fuente")
    a = ap.parse_args()

    origen = Path(a.archivo).expanduser().resolve()
    if not origen.exists():
        morir(f"no existe el archivo {origen}")

    contrato = leer_contrato()
    cols = columnas_del_contrato(contrato)
    decl = lectura_declarada(contrato, origen.name)
    rec = None if a.sin_recorte else recorte_del_contrato(contrato)
    cfg = entorno(exigir=not a.simular)
    lote = a.lote or origen.stem
    destino = (f"s3://{cfg['bucket']}/{PREFIJO}" if cfg
               else f"s3://<S3_BUCKET>/{PREFIJO}")
    arranque = time.time()

    print(f"archivo  : {origen}")
    print(f"destino  : {destino}")
    print(f"lote     : {lote}")
    print(f"modo     : {'SIMULACIÓN — no se escribe nada' if a.simular else 'ESCRITURA'}")
    if origen.suffix.lower() == ".parquet":
        print("lectura  : parquet · los tipos vienen resueltos, no se adivina nada\n")
    else:
        marca = "  ← EXCEPCIÓN declarada en el contrato" if decl["es_excepcion"] else ""
        print(f"lectura  : codificación {decl['encoding']} · fecha {decl['humano']}"
              f"{marca}")
        print("           las dos las declara el contrato; NO las adivina DuckDB\n")

    con = conectar_duckdb(cfg)
    seleccion = ", ".join(cols)

    # Aviso de deriva de esquema · contrato `columnas_extra.aviso`.
    # Se emite ANTES de seleccionar las 15, porque después ya no se ven.
    presentes = [c[0] for c in con.sql(
        f"DESCRIBE SELECT * FROM {lector(origen, decl)}").fetchall()]
    faltan = [c for c in cols if c not in presentes]
    if faltan:
        morir("el archivo no trae estas columnas del contrato: "
              + ", ".join(faltan)
              + "\n  Es DERIVA DE ESQUEMA, no un descuido de captura. "
                "El lote no se ingiere a medias.")
    extra = [c for c in presentes if c not in cols]
    if extra:
        print(f"⚠ AVISO · el archivo trae {len(presentes)} columnas; "
              f"se ignoraron: {', '.join(extra)}")
        print("  Severidad: advertencia. El lote entra completo "
              "(contrato · columnas_extra).\n")

    con.sql(f"CREATE VIEW entrada AS SELECT {seleccion} FROM {lector(origen, decl)}")

    # Contrato · `columnas.fecha_registro.al_no_parsear: cuarentena`.
    # Si la fecha NO cuadra con el formato declarado, DuckDB no falla: deja la
    # columna como texto y sigue. El error aparece cien líneas después como un
    # «Binder Error» de strftime que no dice nada del problema real. Aquí se
    # atrapa donde ocurre y con el motivo que el contrato le da.
    tipo_fecha = {c[0]: c[1] for c in
                  con.sql("DESCRIBE SELECT * FROM entrada").fetchall()}["fecha_registro"]
    if not tipo_fecha.startswith(("DATE", "TIMESTAMP")):
        morir(f"`fecha_registro` llegó como {tipo_fecha}, no como fecha.\n"
              f"  El contrato declara {decl['humano']} para este archivo y los "
              f"valores no cuadran con ese formato.\n"
              f"  Motivo del contrato: fecha_ilegible → cuarentena del lote.\n"
              f"  Revisa `archivo.formato_de_fecha` en el contrato: si este "
              f"archivo trae otro formato, va como excepción con su nombre.")

    # Contrato · `archivo.codificacion.compuerta_extra: detectar_controles_C1`, con
    # `al_fallar: cuarentena_del_lote`: el lote no se ingiere a medias.
    texto = [c for c in cols if contrato["columnas"][c].get("tipo") == "texto"]
    n_c1, ej_c1 = controles_c1(con, texto)
    if n_c1:
        morir(f"{n_c1:,} filas traen caracteres de control C1 (U+0080 a U+009F).\n"
              f"  Ejemplos: " + "; ".join(f"{c} = {v!r}" for c, v in ej_c1) + "\n"
              f"  Casi siempre es un archivo leído con la codificación equivocada.\n"
              f"  Contrato · archivo.codificacion · {COMPUERTA_C1} → cuarentena del lote.\n"
              f"  Revisa `archivo.codificacion.excepciones`: si este archivo viene en "
              f"otra codificación, va ahí con su nombre.")

    # ── El recorte del alcance ────────────────────────────────────────────────
    # Se aplica ANTES de derivar la quincena y de escribir. Se reporta por motivo
    # y no sólo el total, porque una fila puede caer fuera por más de uno y el
    # desglose es lo que dice si un descarte es el esperado o una sorpresa.
    if rec is None:
        print("recorte  : NINGUNO · se ingiere el archivo completo (--sin-recorte)\n")
        con.sql("CREATE VIEW dentro AS SELECT * FROM entrada")
        filas_archivo = con.sql("SELECT count(*) FROM entrada").fetchone()[0]
        fuera = {}
    else:
        # Un `?` en `estado` o `catalogo` no es «fuera del alcance»: es «no se
        # sabe». Filtrarlo lo perdería sin incidente, que es justo la pérdida
        # silenciosa que el contrato 1.3.0 dice evitar.
        n_q, ej_q = interrogantes_en_filtros(con)
        if n_q:
            morir(f"{n_q:,} filas traen `?` en estado o catalogo, y con eso no se "
                  f"puede saber si son del alcance.\n  Ejemplos (estado · catalogo · "
                  f"filas): " + "; ".join(f"{e!r} · {c!r} · {n:,}" for e, c, n in ej_q)
                  + "\n  No se filtran en silencio: agrega la reparación al "
                  "diccionario del contrato, o decide en el contrato qué se hace "
                  "con ellas.")
        s = rec["sql"]
        filas_archivo = con.sql("SELECT count(*) FROM entrada").fetchone()[0]
        fuera = dict(zip(
            ("estado", "ventana", "catalogo"),
            con.sql(f"""SELECT count(*) FILTER (WHERE NOT ({s['estado']})),
                               count(*) FILTER (WHERE NOT ({s['ventana']})),
                               count(*) FILTER (WHERE NOT ({s['catalogo']}))
                        FROM entrada""").fetchone()))
        con.sql(f"""CREATE VIEW dentro AS SELECT * FROM entrada
                    WHERE ({s['estado']}) AND ({s['ventana']}) AND ({s['catalogo']})""")
        dentro = con.sql("SELECT count(*) FROM dentro").fetchone()[0]
        pct = 100 * dentro / filas_archivo if filas_archivo else 0
        print("recorte del alcance · los tres, leídos del contrato")
        print(f"   {len(rec['entidades'])} entidades · {len(rec['catalogos'])} catálogos"
              f" · ventana {rec['ventana'][0]} → {rec['ventana'][1]}")
        print(f"   filas del archivo        {filas_archivo:>12,}")
        print(f"   fuera por estado         {fuera['estado']:>12,}")
        print(f"   fuera por ventana        {fuera['ventana']:>12,}")
        print(f"   fuera por catálogo       {fuera['catalogo']:>12,}")
        print(f"   DENTRO del alcance       {dentro:>12,}   ({pct:.2f}%)")
        print("   (los tres «fuera» se solapan: una fila puede fallar en más de uno)\n")
        if dentro == 0:
            morir("ninguna fila de este archivo cae dentro del alcance. "
                  "Revisa que sea un archivo del corpus y no otro.")

    # Dos columnas derivadas, y las dos son LLAVES DE PARTICIÓN, no limpieza:
    # `quincena` porque la fuente publica por quincena, y `entidad` porque el
    # mismo estado llega escrito de dos maneras. Las 15 del contrato entran
    # intactas, con sus acentos como vinieron.
    entidad_sql = (rec["entidad_sql"] if rec
                   else "upper(strip_accents(trim(estado)))")
    con.sql(f"""CREATE VIEW listo AS
                SELECT *, {QUINCENA} AS quincena, {entidad_sql} AS entidad
                FROM dentro""")

    filas_leidas = con.sql("SELECT count(*) FROM listo").fetchone()[0]
    particiones = [(e, q) for e, q in con.sql(
        "SELECT DISTINCT entidad, quincena FROM listo ORDER BY 1, 2").fetchall()]
    literales = con.sql(
        "SELECT count(DISTINCT estado), count(DISTINCT entidad) FROM listo").fetchone()
    if literales[0] != literales[1]:
        print(f"· {literales[0]} literales de `estado` se unifican en "
              f"{literales[1]} entidades para particionar "
              f"(el literal crudo se conserva en la columna)")
    # Cada lote escribe SOLO su quincena. Antes de escribir se borran las
    # particiones que el lote toca; si una fila cayera en otra quincena, se
    # borraría lo que otro lote dejó ahí y la comprobación por lote no lo vería.
    esperada = a.quincena or quincena_del_lote(origen.stem)
    if esperada is None:
        morir(f"no sé de qué quincena es el lote {origen.stem!r}: su nombre no sigue "
              f"el de la fuente (MM-AAAA_01 o MM-AAAA_Q1).\n  Pásala con --quincena "
              f"AAAA-MM-Q1. Sin eso no puedo garantizar que no sobrescriba la "
              f"partición de otro lote.")
    ajenas = sorted({q for _, q in particiones} - {esperada})
    if ajenas:
        n_aj = con.sql(f"SELECT count(*) FROM listo WHERE quincena <> '{esperada}'"
                       ).fetchone()[0]
        morir(f"{n_aj:,} filas caen en otra quincena ({', '.join(ajenas)}) y no en "
              f"{esperada}, la quincena del lote.\n  Escribirlas borraría lo que otro "
              f"lote dejó en esa partición. Revisa las fechas de esas filas antes de "
              f"ingerir.")

    print(f"filas leídas    : {filas_leidas:,}")
    print(f"particiones     : {len(particiones)}")
    for e, q in particiones:
        print(f"   entidad={e} · quincena={q}")

    if a.simular:
        print("\nNada escrito. Lo que esta corrida SÍ comprueba:")
        print("  · el contrato se lee y declara 15 columnas")
        print("  · el archivo las trae todas")
        print("  · se leyó con la codificación y el formato de fecha del contrato")
        print("  · cuántas filas caen dentro del alcance, y por qué salen las demás")
        print("  · las particiones que se van a crear, una por (entidad, quincena)")
        print("  · que ningún texto trae controles C1 y ningún filtro trae `?`")
        print(f"  · que todas las filas son de {esperada}, la quincena del lote")
        print("Vuelve a correrlo sin --simular para escribir.")
        return

    s3 = cliente_s3(cfg)
    from botocore.exceptions import ClientError
    try:
        s3.head_bucket(Bucket=cfg["bucket"])
    except ClientError:
        # SÓLO ClientError, no cualquier excepción. Un `except Exception` aquí
        # trataba igual «el bucket no existe» que «MinIO está apagado», y en el
        # segundo caso el create_bucket de abajo fallaba con un error que no
        # decía nada. Ahora un problema de conexión sube tal cual.
        print(f"\nel bucket {cfg['bucket']} no existe; creándolo")
        s3.create_bucket(Bucket=cfg["bucket"])

    # 1 · idempotencia: se vacían SÓLO las particiones que este lote va a tocar
    print("\nborrando las particiones que toca este lote")
    borrados = 0
    for e, q in particiones:
        from urllib.parse import quote
        pref = f"{PREFIJO}/entidad={quote(str(e))}/quincena={quote(str(q))}/"
        borrados += borrar_prefijo(s3, cfg["bucket"], pref)
    print(f"   objetos borrados: {borrados}")

    # 2 · escritura
    print("escribiendo")
    # OVERWRITE_OR_IGNORE y NO `OVERWRITE`. Medido, porque la diferencia no se
    # deduce del nombre y costó una ingesta entera:
    #
    #   OVERWRITE            borra el DIRECTORIO COMPLETO en cada COPY. Con un
    #                        lote por archivo, cada uno borra al anterior y el
    #                        bucket termina con el último, nada más.
    #   APPEND               conserva lo demás, pero nombra los archivos con un
    #                        UUID: reescribir el mismo lote DUPLICA las filas.
    #   OVERWRITE_OR_IGNORE  conserva las particiones que no toca y reusa el
    #                        nombre `data_0.parquet`, así que reescribir el
    #                        mismo lote reemplaza en vez de sumar.  <- ésta
    #
    # El borrado explícito de arriba sigue haciendo falta: si una partición tenía
    # `data_0` y `data_1` y ahora sólo se escribe `data_0`, el `data_1` viejo
    # sobreviviría. Las dos cosas juntas son lo que da la garantía.
    con.sql(f"""COPY listo TO '{destino}'
                (FORMAT PARQUET, PARTITION_BY (entidad, quincena),
                 OVERWRITE_OR_IGNORE)""")

    # Las cifras del LOTE: sólo las particiones que este archivo escribió. Antes
    # se contaba todo el destino, que con `OVERWRITE` daba lo mismo porque el
    # destino sólo tenía este lote. Ya no: ahora el bucket acumula, y comparar el
    # total contra las filas de UN archivo fallaría siempre a partir del segundo.
    from urllib.parse import quote as _q
    objetos = bytes_ = 0
    for e, q in particiones:
        o, b = inventario(s3, cfg["bucket"],
                          f"{PREFIJO}/entidad={_q(str(e))}/quincena={_q(str(q))}/")
        objetos += o
        bytes_ += b
    pares = " OR ".join(
        f"(entidad = '{str(e).replace(chr(39), chr(39) * 2)}' "
        f"AND quincena = '{str(q).replace(chr(39), chr(39) * 2)}')"
        for e, q in particiones)
    filas_escritas = con.sql(
        f"SELECT count(*) FROM read_parquet('{destino}/**/*.parquet', "
        f"hive_partitioning=1) WHERE {pares}").fetchone()[0]

    # Y el acumulado del bucket, que es otra cosa y conviene no confundirla.
    obj_tot, byt_tot = inventario(s3, cfg["bucket"], PREFIJO + "/")
    filas_tot = con.sql(
        f"SELECT count(*) FROM read_parquet('{destino}/**/*.parquet', "
        "hive_partitioning=1)").fetchone()[0]
    duracion = round(time.time() - arranque, 2)

    print(f"\nfilas escritas  : {filas_escritas:,}")
    print(f"objetos         : {objetos}")
    print(f"tamaño          : {bytes_/1024/1024:.2f} MiB")
    print(f"duración        : {duracion} s")
    print(f"\nacumulado en el bucket · {filas_tot:,} filas · {obj_tot} objetos "
          f"· {byt_tot/1024/1024:.2f} MiB")

    if filas_escritas != filas_leidas:
        morir(f"se leyeron {filas_leidas:,} filas y se escribieron "
              f"{filas_escritas:,}. Algo se quedó en el camino.")

    CORRIDAS.mkdir(parents=True, exist_ok=True)
    # UTC a propósito: así el nombre del registro coincide con la marca de
    # tiempo que MinIO le pone a los objetos. Con la hora local de México
    # (UTC-6) una corrida de las 20:15 quedaba fechada un día antes que sus
    # propios objetos, y eso confunde al revisar la evidencia.
    hoy = dt.datetime.now(dt.timezone.utc).date().isoformat()
    registro = CORRIDAS / f"{hoy}-{lote}.json"

    # Las cinco cifras van agrupadas y con ese nombre a propósito: son el
    # criterio de cierre de T020 y así se comprueban de un vistazo, sin tener
    # que saber cuáles de los campos del registro son las que cuentan.
    cinco_cifras = {
        "filas_leidas": filas_leidas,
        "filas_escritas": filas_escritas,
        "objetos": objetos,
        "bytes": bytes_,
        "duracion_segundos": duracion,
    }

    registro.write_text(json.dumps({
        "lote": lote,
        "archivo": str(origen),
        "sha256_entrada": sha256_de(origen),
        "recorte": ("ninguno (--sin-recorte)" if rec is None else {
            "entidades": rec["entidades"],
            "catalogos": rec["catalogos"],
            "ventana": {"desde": rec["ventana"][0], "hasta": rec["ventana"][1]},
            "filas_del_archivo": filas_archivo,
            "fuera_por_estado": fuera.get("estado"),
            "fuera_por_ventana": fuera.get("ventana"),
            "fuera_por_catalogo": fuera.get("catalogo"),
            "dentro_del_alcance": filas_leidas,
        }),
        "lectura_declarada": {"encoding": decl["encoding"],
                              "formato_de_fecha": decl["humano"],
                              "es_excepcion_del_contrato": decl["es_excepcion"]},
        "columnas_extra_ignoradas": extra,
        "cinco_cifras": cinco_cifras,
        "objetos_borrados_antes": borrados,
        "acumulado_en_el_bucket": {"filas": filas_tot, "objetos": obj_tot,
                                   "bytes": byt_tot},
        "particiones": [{"entidad": e, "quincena": q} for e, q in particiones],
        "destino": destino,
        "corrida": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"registro        : {registro}")
    print("\n" + "─" * 58)
    print("LAS CINCO CIFRAS")
    print("─" * 58)
    print(f"  filas leídas    {filas_leidas:>14,}")
    print(f"  filas escritas  {filas_escritas:>14,}")
    print(f"  objetos         {objetos:>14,}")
    print(f"  bytes           {bytes_:>14,}")
    print(f"  duración        {duracion:>13,.2f} s")
    print("─" * 58)
    print("\n✓ Listo. Para comprobar la idempotencia, corre exactamente lo mismo")
    print("  otra vez: las tres cifras de en medio —filas escritas, objetos y")
    print("  bytes— tienen que salir idénticas. La duración no: esa cambia.")


if __name__ == "__main__":
    main()
