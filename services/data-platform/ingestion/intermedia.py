#!/usr/bin/env python3
"""CanastaMX · T048 · la capa intermedia (CU-02, paso 6).

QUÉ ES
------
La capa entre la cruda —el Parquet del bucket tal como llegó— y la de consumo —la
estrella de T053—. Sus filas ya están **reparadas, tipadas y sin captura doble**,
pero todavía no son hechos ni dimensiones. Vive en `postgres-analytics`, en
`intermedia.observacion`.

Es el puerto de lo que `docs/datos/probar-modelo-dimensional.py` (T031) hacía
antes de las dimensiones —`limpio`, `clasif` y `plana`—, con tres diferencias que
no son de estilo:

  · **No se salta nada en silencio.** `clasif` filtraba `WHERE NOT
    con_interrogante`: las filas con `?` desaparecían sin motivo. Aquí ya no llegan
    así: `reparacion.py` las apartó a cuarentena con su motivo antes del 5% de
    D-07, y si alguna llegara, `construir()` se detiene.
  · **El desempate no depende del orden del archivo.** `clasif` ordenaba por
    `precio_d, rid`, y `rid` era el número de fila al leer: con el lote en otro
    orden quedaba otra fila (RF-25). Aquí, a igual precio, decide la huella de la
    fila, que sale de su contenido.
  · **Ninguna regla está escrita aquí.** La reparación es la de `reparacion.py`; la
    clave de fila, la misma consulta de `lote.py` (`sql_con_clave()`); el $1 de la
    captura doble y el $50 de la colisión, `clave_de_fila`; el tipo del precio,
    `columnas.precio.tipo`.

QUÉ PASA EN CADA LOTE
---------------------
    1. reparar      cada texto de `aplica_a` con las reparaciones del contrato
    2. tipar        el precio a su DECIMAL, la fecha a DATE
    3. clasificar   los grupos de la clave de fila: única, captura doble u
                    observaciones múltiples
    4. deduplicar   de cada captura doble queda una: la de menor precio
                    (`desempate: min_precio`) y, a igual precio, la de menor huella
    5. cargar       la partición del lote se REEMPLAZA en una transacción: se
                    borran sus filas y se escriben las nuevas, o nada (CU-02 · 6a)

Un lote detenido carga cero filas: su partición queda vacía. Así, materializar dos
veces la misma partición deja exactamente lo mismo (RF-25), y lo que hay en la capa
de un lote es siempre lo de su última corrida.

`ingerido_en` es la hora de la ingesta, según el registro de la corrida. Al
reprocesar se vuelve a ingerir, así que cambia: por eso no entra en la huella de la
capa, igual que la duración no entra en la huella de la capa cruda.

DÓNDE ESCRIBE
-------------
Con `CANASTAMX_SIMULAR`, en un DuckDB de la carpeta de corridas
(`capa-intermedia.duckdb`), que es donde las compuertas ya dejan su evidencia. Sin
simular, en `postgres-analytics`, con las `ANALYTICS_*` del `.env` y la extensión
`postgres` de DuckDB: no hay dependencia nueva de pip. La primera vez, DuckDB la
descarga de extensions.duckdb.org, igual que la ingesta descarga httpfs. La
contraseña nunca va en una cadena de SQL: viaja en las variables de libpq.

No importa Dagster (ADR 016): si la orquestación se va, esto sigue corriendo.

USO
---
    # lo que quedó de un lote en la capa, contra su registro: la evidencia de #186
    python services/data-platform/ingestion/intermedia.py --verificar 07-2026_Q2
    python services/data-platform/ingestion/intermedia.py --verificar 07-2026_Q2 --simular
"""

import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lote as reglas_de_lote
import reparacion
from ingesta import (
    CORRIDAS,
    QUINCENA,
    columnas_del_contrato,
    leer_contrato,
    recorte_del_contrato,
)
from salida_segura import preparar_salida

ESQUEMA = "intermedia"
TABLA = "observacion"
ARCHIVO_DE_SIMULACION = "capa-intermedia.duckdb"
VARIABLES_DE_LA_BASE = ("ANALYTICS_DB", "ANALYTICS_USER", "ANALYTICS_PASSWORD",
                        "ANALYTICS_PORT")


def _con():
    import duckdb

    return duckdb.connect(":memory:")


def _texto_sql(valor):
    return str(valor).replace("'", "''")


# ── Las columnas de la capa, leídas del contrato ───────────────────────────

def _tipo_de(decl):
    """(DuckDB, PostgreSQL) para una columna del contrato.

    `decimal(p,s)` va a DECIMAL(p,s): es el precio, y su precisión la declara el
    contrato. `decimal` sin precisión —latitud y longitud— va a DOUBLE: en DuckDB,
    un DECIMAL sin precisión es (18,3), y redondearía la coordenada a cien metros.
    """
    tipo = str(decl.get("tipo", "texto")).strip().lower()
    if tipo == "texto":
        return "VARCHAR", "text"
    if tipo == "fecha":
        return "DATE", "date"
    exacto = re.fullmatch(r"decimal\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)", tipo)
    if exacto:
        p, s = exacto.groups()
        return f"DECIMAL({p},{s})", f"numeric({p},{s})"
    if tipo == "decimal":
        return "DOUBLE", "double precision"
    raise ValueError(f"no sé guardar una columna de tipo «{tipo}» en la capa intermedia")


def _texto_de_la_clave(contrato):
    """Las columnas de la clave de fila que se normalizan: todas menos la fecha."""
    return [c for c in contrato["clave_de_fila"]["columnas"]
            if reglas_de_lote._normalizacion_de(contrato, c) != "ninguna"]


def columnas_de_la_capa(contrato):
    """[(nombre, tipo DuckDB, tipo PostgreSQL, admite nulo)], en el orden de la tabla.

    Las 15 del contrato con su tipo, más lo que la capa agrega: el lote, la
    quincena y la entidad; las columnas de la clave de fila ya normalizadas, que
    son las que T053 agrupa; el catálogo normalizado; la huella de la fila tal como
    llegó y su ocurrencia, que con el lote forman la llave; la versión del contrato
    con que se construyó, y `ingerido_en`.
    """
    cols = [("lote", "VARCHAR", "text", False),
            ("quincena", "VARCHAR", "text", False),
            ("entidad", "VARCHAR", "text", False)]
    for nombre, decl in contrato["columnas"].items():
        duck, pg = _tipo_de(decl)
        cols.append((nombre, duck, pg, not decl.get("valor_requerido")))
    for c in _texto_de_la_clave(contrato):
        cols.append((f"clave_{c}", "VARCHAR", "text",
                     not contrato["columnas"][c].get("valor_requerido")))
    cols += [("catalogo_normalizado", "VARCHAR", "text", False),
             # `text` y no `char(64)`: la huella siempre mide 64, así que el largo
             # fijo no agrega nada, y `text` es el tipo al que DuckDB escribe su
             # VARCHAR sin convertirlo.
             ("huella_fila", "VARCHAR", "text", False),
             ("ocurrencia", "INTEGER", "integer", False),
             ("version_contrato", "VARCHAR", "text", False),
             ("ingerido_en", "TIMESTAMPTZ", "timestamptz", False)]
    if len({c[0] for c in cols}) != len(cols):
        raise ValueError("dos columnas de la capa intermedia se llaman igual")
    return cols


def ddl(contrato, motor, prefijo=""):
    """Las sentencias que crean el esquema y la tabla, generadas del contrato.

    `motor` es `duckdb` o `postgres`. Con `prefijo` (`destino.`) se escriben para
    una base adjunta de DuckDB; sin él, para correrlas en PostgreSQL mismo.
    """
    i = {"duckdb": 1, "postgres": 2}[motor]
    defs = ",\n  ".join(f'"{c[0]}" {c[i]}{"" if c[3] else " NOT NULL"}'
                        for c in columnas_de_la_capa(contrato))
    tabla = (f"CREATE TABLE IF NOT EXISTS {prefijo}{ESQUEMA}.{TABLA} (\n  {defs},\n"
             f"  PRIMARY KEY (lote, huella_fila, ocurrencia)\n)")
    return [f"CREATE SCHEMA IF NOT EXISTS {prefijo}{ESQUEMA}", tabla]


# ── La huella de la fila tal como llegó ────────────────────────────────────

def huellas(df, columnas):
    """La huella de cada fila, igual a la de `compuerta.huella()`.

    Es la misma que lleva la cuarentena: con ella, una fila de la capa intermedia
    se liga con su fila de la capa cruda, y dos filas que llegaron idénticas tienen
    la misma. Se calcula por columnas y no fila por fila con `iloc`, porque un lote
    del alcance tiene unas setenta mil.
    """
    import pandas as pd

    def texto(v):
        if v is None or (not isinstance(v, str) and pd.isna(v)):
            return ""
        return v.isoformat() if hasattr(v, "isoformat") else str(v)

    if not len(df):
        return []
    partes = [df[c].astype(object).map(texto).tolist() for c in columnas]
    return [hashlib.sha256("\x1f".join(valores).encode("utf-8")).hexdigest()
            for valores in zip(*partes)]


# ── La construcción ────────────────────────────────────────────────────────

def construir(df, contrato, lote, ingerido_en):
    """La capa de un lote promovido: (conexión con la tabla `capa`, resumen).

    `df` son las filas que dejó salir `lote_promovido`, tal como llegaron. La
    conexión es de DuckDB, en memoria; `cargar()` la usa para escribir.
    """
    import pandas as pd

    columnas = columnas_del_contrato(contrato)
    clave = contrato["clave_de_fila"]
    if clave["colision_precio_alta"]["a_cuarentena"] != "grupo_completo":
        raise ValueError("`colision_precio_alta.a_cuarentena` cambió; esta capa sólo "
                         "sabe que el grupo completo ya se apartó")
    menos_de = clave["captura_doble"]["menos_de"]
    mas_de = clave["colision_precio_alta"]["mas_de"]
    particion = ", ".join(f"k_{c}" for c in clave["columnas"])
    aplica = reparacion.regla(contrato)["aplica_a"]

    entrada = df.reset_index(drop=True)
    entrada = entrada.assign(__i__=range(len(entrada)))
    mapa = reparacion.reparaciones_del_contrato(contrato)
    tabla_rep = pd.DataFrame([{"columna": k[0], "valor_roto": k[1], "reparado": v}
                              for k, v in mapa.items()],
                             columns=["columna", "valor_roto", "reparado"])

    con = _con()
    con.register("promovidas", entrada)
    con.register("reparaciones", tabla_rep)
    con.register("huellas", pd.DataFrame({"__i__": range(len(entrada)),
                                          "__huella__": huellas(entrada, columnas)}))

    # 1 · reparar y tipar · el `limpio` de T031, en las once columnas y no en seis.
    seleccion, uniones = [], []
    for c in columnas:
        duck, _ = _tipo_de(contrato["columnas"][c])
        if c in aplica:
            seleccion.append(f'COALESCE(r_{c}.reparado, CAST(p."{c}" AS VARCHAR)) AS "{c}"')
            uniones.append(f"LEFT JOIN reparaciones r_{c} ON r_{c}.columna = '{c}' "
                           f'AND r_{c}.valor_roto = CAST(p."{c}" AS VARCHAR)')
        else:
            seleccion.append(f'CAST(p."{c}" AS {duck}) AS "{c}"')
    con.execute(f"""CREATE TABLE reparadas AS
                    SELECT p.__i__, {', '.join(seleccion)}
                    FROM promovidas p {' '.join(uniones)}""")
    con_q = " OR ".join(f'contains("{c}", \'{reparacion.INTERROGANTE}\')' for c in aplica)
    quedan = con.execute(f"SELECT count(*) FROM reparadas WHERE {con_q}").fetchone()[0]
    if quedan:
        # Postcondición de CU-03: ningún `?` pasa. Si llega uno aquí, la compuerta
        # de `reparacion.py` no lo apartó, y cargarlo sería esconder el fallo.
        raise ValueError(f"{quedan} filas llegaron con un `?` que no se puede reparar; "
                         "tenían que ir a cuarentena antes del 5% de D-07")

    # 2 · clasificar · el `clasif` de T031, con la consulta de la compuerta de grupo.
    con.execute("CREATE TABLE con_clave AS "
                + reglas_de_lote.sql_con_clave(contrato, "promovidas", "reparaciones"))
    if con.execute("SELECT count(*) FROM con_clave WHERE __precio__ IS NULL").fetchone()[0]:
        raise ValueError("llegaron filas con un precio que no se puede leer: la "
                         "compuerta de fila tenía que apartarlas (`tipo_invalido`)")
    con.execute(f"""
        CREATE TABLE clasificadas AS
        SELECT c.*,
               CASE WHEN count(*) OVER w = 1 THEN 'unica'
                    WHEN max(c.__precio__) OVER w - min(c.__precio__) OVER w < $menos_de
                        THEN 'captura_doble'
                    WHEN max(c.__precio__) OVER w - min(c.__precio__) OVER w > $mas_de
                        THEN 'colision'
                    ELSE 'observaciones_multiples' END AS cubo,
               -- `desempate: min_precio` y, a igual precio, el contenido de la
               -- fila, que es su huella. Nunca su posición en el archivo (RF-25).
               row_number() OVER (PARTITION BY {particion}
                                  ORDER BY c.__precio__, h.__huella__) AS orden
        FROM con_clave c JOIN huellas h USING (__i__)
        WINDOW w AS (PARTITION BY {particion})
    """, {"menos_de": menos_de, "mas_de": mas_de})
    colisiones = con.execute(
        "SELECT count(*) FROM clasificadas WHERE cubo = 'colision'").fetchone()[0]
    if colisiones:
        raise ValueError(f"{colisiones} filas de grupos en colisión alta llegaron a la "
                         "capa intermedia; la compuerta de grupo tenía que apartarlas")

    # 3 · deduplicar y armar · el `plana` de T031.
    catalogo = reglas_de_lote.expresion(
        contrato, contrato["normalizacion"]["catalogo"]["a"], "catalogo")
    entidad = recorte_del_contrato(contrato)["entidad_sql"]
    finales = ", ".join(f'r."{c}"' for c in columnas)
    claves = ", ".join(f'k.k_{c} AS "clave_{c}"' for c in _texto_de_la_clave(contrato))
    con.execute(f"""
        CREATE TABLE capa AS
        SELECT $lote AS lote,
               {QUINCENA} AS quincena,
               {entidad} AS entidad,
               {finales},
               {claves},
               {catalogo} AS catalogo_normalizado,
               h.__huella__ AS huella_fila,
               CAST(row_number() OVER (PARTITION BY h.__huella__ ORDER BY h.__huella__)
                    AS INTEGER) AS ocurrencia,
               $version AS version_contrato,
               CAST($ingerido_en AS TIMESTAMPTZ) AS ingerido_en
        FROM reparadas r
        JOIN clasificadas k USING (__i__)
        JOIN huellas h USING (__i__)
        WHERE k.cubo IN ('unica', 'observaciones_multiples')
           OR (k.cubo = 'captura_doble' AND k.orden = 1)
    """, {"lote": lote, "version": str(contrato["version"]),
          "ingerido_en": str(ingerido_en)})

    sobrantes, grupos = con.execute(f"""
        SELECT count(*) FILTER (WHERE cubo = 'captura_doble' AND orden > 1),
               count(DISTINCT CASE WHEN cubo = 'captura_doble'
                                   THEN md5(concat_ws(chr(31), {particion})) END)
        FROM clasificadas""").fetchone()
    reparadas_por_columna = {}
    for c in aplica:
        n = con.execute(f"""SELECT count(*) FROM promovidas p JOIN reparadas r USING (__i__)
                            WHERE CAST(p."{c}" AS VARCHAR) IS DISTINCT FROM r."{c}" """
                        ).fetchone()[0]
        if n:
            reparadas_por_columna[c] = int(n)
    resumen = {
        "lote": lote,
        "filas_entrada": len(entrada),
        "sobrantes_captura_doble": int(sobrantes),
        "grupos_captura_doble": int(grupos),
        "filas_salida": con.execute("SELECT count(*) FROM capa").fetchone()[0],
        "reparadas_por_columna": reparadas_por_columna,
        "umbral_de_captura_doble": menos_de,
    }
    return con, resumen


def capa_vacia(contrato):
    """Una conexión con la tabla `capa` sin filas: lo que carga un lote detenido."""
    con = _con()
    defs = ", ".join(f'"{c[0]}" {c[1]}' for c in columnas_de_la_capa(contrato))
    con.execute(f"CREATE TABLE capa ({defs})")
    return con


def huella_de_la_capa(con, tabla="capa", excluir=("ingerido_en",), donde=None, valores=()):
    """sha256 de las filas de la capa, ordenadas, sin `ingerido_en`.

    Es la huella que RF-25 compara entre dos materializaciones: no depende del
    orden en que llegaron las filas ni de la hora de la ingesta.
    """
    cols = [r[0] for r in con.execute(f"DESCRIBE {tabla}").fetchall() if r[0] not in excluir]
    fila = ", ".join(f'COALESCE(CAST("{c}" AS VARCHAR), chr(0))' for c in cols)
    filtro = f" WHERE {donde}" if donde else ""
    return con.execute(f"""
        SELECT sha256(COALESCE(string_agg(fila, chr(30) ORDER BY fila), ''))
        FROM (SELECT concat_ws(chr(31), {fila}) AS fila FROM {tabla}{filtro})""",
                       list(valores)).fetchone()[0]


# ── La carga ───────────────────────────────────────────────────────────────

def adjuntar_destino(con, contrato, simular, carpeta=None):
    """Adjunta la base de la capa intermedia como `destino` y crea su tabla.

    Devuelve a dónde se escribe, sin ningún secreto.
    """
    import duckdb

    if simular:
        ruta = Path(carpeta or CORRIDAS) / ARCHIVO_DE_SIMULACION
        ruta.parent.mkdir(parents=True, exist_ok=True)
        # Dos lotes que terminan a la vez quieren el mismo archivo, y DuckDB deja
        # escribir a uno solo: el otro espera su turno.
        for intento in range(60):
            try:
                con.execute(f"ATTACH '{_texto_sql(ruta)}' AS destino")
                break
            except duckdb.IOException:
                if intento == 59:
                    raise
                time.sleep(0.5)
        for sentencia in ddl(contrato, "duckdb", "destino."):
            con.execute(sentencia)
        return {"motor": "duckdb", "donde": str(ruta), "tabla": f"{ESQUEMA}.{TABLA}"}

    faltan = [v for v in VARIABLES_DE_LA_BASE if not os.environ.get(v)]
    if faltan:
        raise RuntimeError(
            "faltan variables de entorno para postgres-analytics: " + ", ".join(faltan)
            + ". Carga tu .env: set -a; source .env; set +a")
    try:
        con.execute("INSTALL postgres")
        con.execute("LOAD postgres")
    except duckdb.Error as e:
        raise RuntimeError(
            "no se pudo cargar la extensión postgres de DuckDB. La primera vez se "
            "descarga de extensions.duckdb.org, igual que httpfs para la ingesta: "
            f"hace falta red. DuckDB dijo: {e}") from None
    variables = {"PGHOST": "localhost", "PGPORT": os.environ["ANALYTICS_PORT"],
                 "PGDATABASE": os.environ["ANALYTICS_DB"],
                 "PGUSER": os.environ["ANALYTICS_USER"],
                 "PGPASSWORD": os.environ["ANALYTICS_PASSWORD"]}
    # La conexión va por las variables de libpq, no por una cadena: así la
    # contraseña no aparece en ningún SQL ni en los errores de DuckDB.
    #
    # Y se QUEDAN puestas, no sólo durante el ATTACH. La extensión abre conexiones
    # nuevas después, y cada una lee las variables al abrirse. La primera versión
    # las quitaba al terminar el ATTACH; en la primera corrida real, la cuenta que
    # sigue a la carga abrió otra conexión y, ya sin ellas, buscó el servidor por
    # omisión (/tmp/.s.PGSQL.5432). Son las mismas ANALYTICS_* del .env, que ya
    # están en el entorno del proceso, con el nombre que libpq lee.
    os.environ.update(variables)
    try:
        con.execute("ATTACH '' AS destino (TYPE postgres)")
    except duckdb.Error as e:
        mensaje = str(e).replace(variables["PGPASSWORD"], "***")
        raise RuntimeError(
            f"no se pudo conectar a postgres-analytics (localhost:{variables['PGPORT']}, "
            f"base {variables['PGDATABASE']}, usuario {variables['PGUSER']}): "
            f"{mensaje}") from None
    for sentencia in ddl(contrato, "postgres"):
        con.execute(f"CALL postgres_execute('destino', '{_texto_sql(sentencia)}')")
    # DuckDB guarda en caché qué tablas tiene la base adjunta; la que se acaba de
    # crear con postgres_execute no está en esa caché hasta limpiarla.
    con.execute("CALL pg_clear_cache()")
    return {"motor": "postgres",
            "donde": f"localhost:{variables['PGPORT']}/{variables['PGDATABASE']}",
            "tabla": f"{ESQUEMA}.{TABLA}"}


def cargar(con, lote, contrato, simular, carpeta=None):
    """Reemplaza la partición del lote con la tabla `capa` de `con`: todo o nada.

    Borra las filas del lote y escribe las nuevas en una sola transacción. Si algo
    falla a la mitad, se revierte y la capa queda como estaba (CU-02 · 6a).

    Sólo escribe filas de `lote`. El DELETE va por el lote que se pide y el INSERT
    copia lo que traiga `capa`: si `capa` fuera de otro lote, se borraría la
    partición pedida y se escribiría en la ajena, sin ningún error la primera vez.
    Por eso se comprueba antes de tocar el destino.
    """
    ajenos = [str(r[0]) for r in con.execute(
        "SELECT DISTINCT lote FROM capa WHERE lote IS DISTINCT FROM ? ORDER BY 1",
        [lote]).fetchall()]
    if ajenos:
        raise ValueError(
            f"la capa trae filas de {', '.join(ajenos)} y se iba a cargar como {lote}: "
            "reemplazar la partición de un lote sólo escribe filas de ese lote. "
            "No se tocó el destino.")
    destino = adjuntar_destino(con, contrato, simular, carpeta)
    tabla = f"destino.{ESQUEMA}.{TABLA}"
    cols = ", ".join(f'"{c[0]}"' for c in columnas_de_la_capa(contrato))
    try:
        antes = con.execute(f"SELECT count(*) FROM {tabla} WHERE lote = ?", [lote]).fetchone()[0]
        con.execute("BEGIN TRANSACTION")
        try:
            con.execute(f"DELETE FROM {tabla} WHERE lote = ?", [lote])
            con.execute(f"INSERT INTO {tabla} ({cols}) SELECT {cols} FROM capa")
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise
        despues = con.execute(f"SELECT count(*) FROM {tabla} WHERE lote = ?",
                              [lote]).fetchone()[0]
    finally:
        con.execute("DETACH destino")
    return {**destino, "borradas": int(antes), "en_destino": int(despues)}


# ── La comprobación, para la evidencia ─────────────────────────────────────

def verificar(lote, contrato=None, simular=False, carpeta=None, corridas=None):
    """Lo que la capa tiene de un lote, contra lo que dice su registro.

    Comprueba el criterio de T048 sobre la base de verdad, no sobre los metadatos
    del activo: cero `?` en las once columnas, `lote` e `ingerido_en` en cada fila,
    y exactamente las filas que `lote_promovido` dejó salir menos las sobrantes de
    captura doble de su linaje (`lote-<lote>.json`). Devuelve (correcto, informe).
    """
    contrato = contrato or leer_contrato()
    con = _con()
    destino = adjuntar_destino(con, contrato, simular, carpeta)
    tabla = f"destino.{ESQUEMA}.{TABLA}"
    aplica = reparacion.regla(contrato)["aplica_a"]
    try:
        filas = con.execute(f"SELECT count(*) FROM {tabla} WHERE lote = ?", [lote]).fetchone()[0]
        con_q = con.execute(
            f"SELECT count(*) FROM {tabla} WHERE lote = ? AND ("
            + " OR ".join(f'contains("{c}", \'{reparacion.INTERROGANTE}\')' for c in aplica)
            + ")", [lote]).fetchone()[0]
        sin_traza = con.execute(f"SELECT count(*) FROM {tabla} WHERE lote = ? AND "
                                "(ingerido_en IS NULL OR huella_fila IS NULL)",
                                [lote]).fetchone()[0]
        horas, versiones = con.execute(
            f"SELECT string_agg(DISTINCT CAST(ingerido_en AS VARCHAR), ', '), "
            f"string_agg(DISTINCT version_contrato, ', ') FROM {tabla} WHERE lote = ?",
            [lote]).fetchone()
        huella = huella_de_la_capa(con, tabla, donde="lote = ?", valores=[lote])
    finally:
        con.execute("DETACH destino")

    registro = Path(corridas or CORRIDAS) / f"lote-{lote}.json"
    informe = [f"capa intermedia · {destino['motor']} · {destino['donde']} · {destino['tabla']}",
               f"lote {lote} · {filas:,} filas · versión del contrato {versiones or '—'}",
               f"  ingerido_en: {horas or '—'}",
               f"  huella de la capa (sin ingerido_en): {huella}"]
    correcto = con_q == 0 and sin_traza == 0
    informe.append(f"  {'✓' if con_q == 0 else '✗'} filas con `?` en las {len(aplica)} "
                   f"columnas de aplica_a: {con_q:,}")
    informe.append(f"  {'✓' if sin_traza == 0 else '✗'} filas sin ingerido_en o sin huella: "
                   f"{sin_traza:,}")
    if registro.exists():
        r = json.loads(registro.read_text(encoding="utf-8"))["resumen"]
        detenido = r.get("resultado") == "DETENIDO"
        sobrantes = (r.get("por_grupo") or {}).get("sobrantes_captura_doble", 0)
        esperadas = 0 if detenido else r["filas_salida"] - sobrantes
        cuadra = filas == esperadas
        correcto = correcto and cuadra
        informe.append(
            f"  {'✓' if cuadra else '✗'} contra el linaje ({registro.name}): "
            f"{r.get('resultado')} · dejó salir {r['filas_salida']:,} − {sobrantes:,} "
            f"sobrantes de captura doble = {esperadas:,} · en la capa {filas:,}")
    else:
        correcto = False
        informe.append(f"  ✗ no encontré el registro del lote en {registro}; "
                       "CANASTAMX_CORRIDAS tiene que ser la de la corrida")
    return correcto, informe


def main():
    preparar_salida()
    import argparse

    ap = argparse.ArgumentParser(description="La capa intermedia de un lote, comprobada")
    ap.add_argument("--verificar", metavar="LOTE", required=True,
                    help="el nombre del lote, como 07-2026_Q2")
    ap.add_argument("--simular", action="store_true",
                    help="lee el DuckDB de simulación de la carpeta de corridas, no "
                         "postgres-analytics")
    a = ap.parse_args()
    simular = a.simular or os.environ.get("CANASTAMX_SIMULAR", "") not in ("", "0", "no")
    correcto, informe = verificar(a.verificar, simular=simular)
    print("\n".join(informe))
    return 0 if correcto else 1


if __name__ == "__main__":
    sys.exit(main())
