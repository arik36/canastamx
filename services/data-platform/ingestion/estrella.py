#!/usr/bin/env python3
"""CanastaMX · T053 · la capa de consumo: el esquema estrella.

QUÉ ES
------
La capa que leen la interfaz analítica y la consola: `hechos_precio`, las cuatro
dimensiones y los tres agregados de `docs/datos/modelo-dimensional.md`. Vive en
`postgres-analytics`, en el esquema `consumo`, y sólo la escribe la plataforma
(P-08).

Es el puerto de la segunda mitad de `docs/datos/probar-modelo-dimensional.py`
(T031): las dimensiones, los hechos y los agregados. La primera mitad —reparar,
tipar y quitar la captura doble— ya la hace la capa intermedia (T048), así que aquí
se lee `intermedia.observacion` y nada más. Lo que cambia respecto de T031, y por
qué:

  · **Se recalcula entera.** Las dimensiones y los agregados cruzan quincenas: un
    artículo aparece en muchos lotes y su nombre es el más frecuente de todos. Por
    eso la estrella no está particionada: se reconstruye desde toda la capa
    intermedia y se reemplaza en una sola transacción. Las llaves subrogadas se
    regeneran al recargar, como dice el modelo.
  · **Nada depende del orden ni del azar (RF-25).** El valor más frecuente se
    desempata por el valor mismo, y la ubicación de una tienda es la pareja de
    coordenadas más frecuente, no un promedio que cambia con el orden de la suma.
  · **Los precios no pasan por punto flotante (P-02).** Los cuantiles son
    `quantile_disc`: un precio que sí se observó, como el precio típico de la
    interfaz analítica (T058). T031 usaba `quantile_cont`.
  · **Ninguna regla está escrita aquí.** Las formas canónicas son las de
    `normalizacion` del contrato (`lote.expresion()`), el tipo del precio es
    `columnas.precio.tipo`, la ventana de `dim_fecha` es `alcance.ventana` y las
    categorías ocultas son `presentacion.ocultar_por_defecto_en_canasta_basica`.

Los tres agregados se calculan sobre `articulo_canonico_key`. Hoy es igual a
`articulo_key`; la reconciliación (#206) lo reescribe y vuelve a llamar a
`agregados()`, sin tocar los hechos.

DÓNDE ESCRIBE
-------------
En la misma base que la capa intermedia (`intermedia.adjuntar_destino()`): con
`CANASTAMX_SIMULAR`, el DuckDB de la carpeta de corridas; sin simular,
`postgres-analytics`, con las `ANALYTICS_*` del `.env`. La contraseña nunca va en
una cadena de SQL.

No importa Dagster (ADR 016): si la orquestación se va, esto sigue corriendo.

USO
---
    # recalcular la estrella desde la capa intermedia, sin Dagster
    python services/data-platform/ingestion/estrella.py --cargar
    # cuántas filas tiene cada tabla de la capa de consumo: la evidencia de #200
    python services/data-platform/ingestion/estrella.py --contar
    # las dos, contra el DuckDB de la simulación
    python services/data-platform/ingestion/estrella.py --cargar --simular
"""

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import intermedia
import lote as reglas_de_lote
from ingesta import leer_contrato
from salida_segura import preparar_salida

ESQUEMA = "consumo"
ORIGEN = f"destino.{intermedia.ESQUEMA}.{intermedia.TABLA}"
# En el orden en que se escriben: primero las dimensiones, después los hechos que
# las usan y al final los agregados, que salen de los hechos.
DIMENSIONES = ("dim_fecha", "dim_articulo", "dim_establecimiento", "dim_cadena")
AGREGADOS = ("agg_articulo_entidad_quincena", "agg_articulo_cadena_entidad_quincena",
             "rango_historico")
TABLAS = DIMENSIONES + ("hechos_precio",) + AGREGADOS
LLAVES = {
    "dim_fecha": ("fecha_key",),
    "dim_articulo": ("articulo_key",),
    "dim_establecimiento": ("establecimiento_key",),
    "dim_cadena": ("cadena_key",),
    "hechos_precio": ("observacion_id",),
    "agg_articulo_entidad_quincena": ("articulo_canonico_key", "entidad", "quincena"),
    "agg_articulo_cadena_entidad_quincena": ("articulo_canonico_key", "cadena_key",
                                             "entidad", "quincena"),
    "rango_historico": ("articulo_canonico_key", "entidad"),
}
# Las llaves naturales: la misma combinación no puede tener dos llaves subrogadas.
NATURALES = {
    "dim_articulo": ("producto_c", "presentacion_c"),
    "dim_establecimiento": ("nombre_c", "direccion_c", "municipio_c", "entidad"),
    "dim_cadena": ("cadena_c",),
}


def _t(nombre, duck, pg, nulo=False):
    return (nombre, duck, pg, nulo)


def columnas(contrato):
    """{tabla: [(nombre, tipo DuckDB, tipo PostgreSQL, admite nulo)]}, en orden.

    Son las del modelo, más dos en los hechos: `huella_fila` y `ocurrencia`, que con
    el `lote` ligan cada observación con su fila de la capa intermedia y, por la
    huella, con la fila tal como llegó a la cruda.
    """
    precio = intermedia._tipo_de(contrato["columnas"]["precio"])
    entero, chico, texto = ("INTEGER", "integer"), ("SMALLINT", "smallint"), ("VARCHAR", "text")
    real, si_no = ("DOUBLE", "double precision"), ("BOOLEAN", "boolean")
    return {
        "dim_fecha": [_t("fecha_key", *entero), _t("fecha", "DATE", "date"),
                      _t("anio", *chico), _t("mes", *chico), _t("quincena", *texto),
                      _t("dia_semana", *chico), _t("es_fin_de_semana", *si_no)],
        "dim_articulo": [_t("articulo_key", *entero), _t("producto_c", *texto),
                         _t("presentacion_c", *texto), _t("producto", *texto),
                         _t("presentacion", *texto), _t("categoria", *texto, True),
                         _t("catalogo_principal", *texto), _t("oculto_por_omision", *si_no),
                         _t("articulo_canonico_key", *entero)],
        "dim_establecimiento": [_t("establecimiento_key", *entero), _t("nombre_c", *texto),
                                _t("direccion_c", *texto), _t("municipio_c", *texto),
                                _t("entidad", *texto), _t("nombre_comercial", *texto),
                                _t("direccion", *texto), _t("municipio", *texto),
                                _t("giro", *texto, True), _t("latitud", *real, True),
                                _t("longitud", *real, True)],
        "dim_cadena": [_t("cadena_key", *chico), _t("cadena_c", *texto),
                       _t("cadena_comercial", *texto)],
        "hechos_precio": [_t("observacion_id", "BIGINT", "bigint"), _t("fecha_key", *entero),
                          _t("articulo_key", *entero), _t("establecimiento_key", *entero),
                          _t("cadena_key", *chico), _t("marca", *texto),
                          _t("es_generico", *si_no), _t("catalogo", *texto),
                          _t("precio", *precio), _t("lote", *texto),
                          _t("huella_fila", *texto), _t("ocurrencia", *entero),
                          _t("ingerido_en", "TIMESTAMPTZ", "timestamptz")],
        "agg_articulo_entidad_quincena": [
            _t("articulo_canonico_key", *entero), _t("entidad", *texto), _t("quincena", *texto),
            _t("n", *entero), _t("minimo", *precio), _t("p25", *precio),
            _t("mediana", *precio), _t("p75", *precio), _t("maximo", *precio)],
        "agg_articulo_cadena_entidad_quincena": [
            _t("articulo_canonico_key", *entero), _t("cadena_key", *chico),
            _t("entidad", *texto), _t("quincena", *texto), _t("n", *entero),
            _t("n_tiendas", *entero), _t("mediana", *precio)],
        "rango_historico": [_t("articulo_canonico_key", *entero), _t("entidad", *texto),
                            _t("desde", *precio), _t("hasta", *precio),
                            _t("quincenas", *entero)],
    }


def ddl(contrato, motor, prefijo=""):
    """Las sentencias que crean el esquema y sus ocho tablas.

    `motor` es `duckdb` o `postgres`. Con `prefijo` (`destino.`) se escriben para
    una base adjunta de DuckDB; sin él, para correrlas en PostgreSQL mismo. Las
    llaves foráneas no se declaran: la estrella se reemplaza entera en una
    transacción, y las pruebas comprueban que ningún hecho quede huérfano.
    """
    i = {"duckdb": 1, "postgres": 2}[motor]
    sentencias = [f"CREATE SCHEMA IF NOT EXISTS {prefijo}{ESQUEMA}"]
    for tabla, cols in columnas(contrato).items():
        defs = [f'"{c[0]}" {c[i]}{"" if c[3] else " NOT NULL"}' for c in cols]
        defs.append(f"PRIMARY KEY ({', '.join(LLAVES[tabla])})")
        if tabla in NATURALES:
            defs.append(f"UNIQUE ({', '.join(NATURALES[tabla])})")
        sentencias.append(f"CREATE TABLE IF NOT EXISTS {prefijo}{ESQUEMA}.{tabla} (\n  "
                          + ",\n  ".join(defs) + "\n)")
    return sentencias


# ── La construcción, en tablas locales de DuckDB ───────────────────────────

def _moda(llaves, columna, alias, donde=""):
    """El valor más frecuente de `columna` por `llaves`, desempatado por el valor.

    `mode()` de DuckDB no dice cómo desempata, y con varios hilos el empate puede
    caer distinto en cada corrida: dos materializaciones darían dimensiones
    distintas (RF-25)."""
    ks = ", ".join(llaves)
    filtro = f"WHERE {columna} IS NOT NULL" + (f" AND {donde}" if donde else "")
    return (f"{alias} AS (SELECT {ks}, first(v ORDER BY n DESC, v) AS {alias} "
            f"FROM (SELECT {ks}, {columna} AS v, count(*) AS n FROM obs {filtro} "
            f"GROUP BY ALL) GROUP BY ALL)")


def _ocultas(contrato):
    """Las categorías que la vista oculta por omisión, en forma canónica."""
    regla = contrato["presentacion"]["ocultar_por_defecto_en_canasta_basica"]
    if regla.get("por_columna") != "categoria":
        raise ValueError("`ocultar_por_defecto_en_canasta_basica` ya no es por categoría: "
                         "esta capa no sabe a qué columna aplicarla")
    valores = ", ".join(f"('{intermedia._texto_sql(v)}')" for v in regla["valores"])
    return (f"SELECT {reglas_de_lote.expresion(contrato, 'canonica', 'v')} "
            f"FROM (VALUES {valores}) t(v)")


def construir(con, contrato, origen=ORIGEN):
    """Crea en `con` las ocho tablas de la estrella a partir de `origen`.

    `origen` es la capa intermedia: `destino.intermedia.observacion` en la carga, o
    cualquier tabla con sus columnas en las pruebas. Devuelve cuántas filas quedó
    en cada tabla.
    """
    def canon(columna):
        return reglas_de_lote.expresion(contrato, "canonica", columna)

    con.execute(f"""CREATE OR REPLACE TABLE obs AS
        SELECT lote, huella_fila, ocurrencia, ingerido_en, entidad,
               clave_producto AS producto_c, clave_presentacion AS presentacion_c,
               producto, presentacion, {canon('categoria')} AS categoria_c,
               catalogo_normalizado AS catalogo, clave_marca AS marca,
               clave_nombre_comercial AS nombre_c, clave_direccion AS direccion_c,
               {canon('municipio')} AS municipio_c,
               nombre_comercial, direccion, municipio, giro, latitud, longitud,
               regexp_replace({canon('cadena_comercial')}, 's$', '') AS cadena_c,
               cadena_comercial, CAST(fecha_registro AS DATE) AS fecha, precio
        FROM {origen}""")

    art = ("producto_c", "presentacion_c")
    con.execute(f"""CREATE OR REPLACE TABLE dim_articulo AS
        WITH llaves AS (SELECT DISTINCT {', '.join(art)} FROM obs),
             {_moda(art, 'producto', 'producto')},
             {_moda(art, 'presentacion', 'presentacion')},
             {_moda(art, 'categoria_c', 'categoria')},
             {_moda(art, 'catalogo', 'catalogo_principal')},
             numeradas AS (
                SELECT CAST(row_number() OVER (ORDER BY producto_c, presentacion_c)
                            AS INTEGER) AS articulo_key, *
                FROM llaves)
        SELECT n.articulo_key, n.producto_c, n.presentacion_c, p.producto, r.presentacion,
               c.categoria, k.catalogo_principal,
               coalesce(c.categoria IN ({_ocultas(contrato)}), false) AS oculto_por_omision,
               n.articulo_key AS articulo_canonico_key
        FROM numeradas n
        LEFT JOIN producto p USING (producto_c, presentacion_c)
        LEFT JOIN presentacion r USING (producto_c, presentacion_c)
        LEFT JOIN categoria c USING (producto_c, presentacion_c)
        LEFT JOIN catalogo_principal k USING (producto_c, presentacion_c)""")

    est = ("nombre_c", "direccion_c", "municipio_c", "entidad")
    ks = ", ".join(est)
    con.execute(f"""CREATE OR REPLACE TABLE dim_establecimiento AS
        WITH llaves AS (SELECT DISTINCT {ks} FROM obs),
             {_moda(est, 'nombre_comercial', 'nombre_comercial')},
             {_moda(est, 'direccion', 'direccion')},
             {_moda(est, 'municipio', 'municipio')},
             {_moda(est, 'giro', 'giro')},
             ubicacion AS (
                SELECT {ks}, first(latitud ORDER BY n DESC, latitud, longitud) AS latitud,
                       first(longitud ORDER BY n DESC, latitud, longitud) AS longitud
                FROM (SELECT {ks}, latitud, longitud, count(*) AS n FROM obs
                      WHERE latitud IS NOT NULL AND longitud IS NOT NULL GROUP BY ALL)
                GROUP BY ALL),
             numeradas AS (
                SELECT CAST(row_number() OVER (ORDER BY entidad, municipio_c, nombre_c,
                            direccion_c) AS INTEGER) AS establecimiento_key, *
                FROM llaves)
        SELECT n.establecimiento_key, n.nombre_c, n.direccion_c, n.municipio_c, n.entidad,
               a.nombre_comercial, b.direccion, m.municipio, g.giro, u.latitud, u.longitud
        FROM numeradas n
        LEFT JOIN nombre_comercial a USING ({ks})
        LEFT JOIN direccion b USING ({ks})
        LEFT JOIN municipio m USING ({ks})
        LEFT JOIN giro g USING ({ks})
        LEFT JOIN ubicacion u USING ({ks})""")

    con.execute(f"""CREATE OR REPLACE TABLE dim_cadena AS
        WITH llaves AS (SELECT DISTINCT cadena_c FROM obs),
             {_moda(('cadena_c',), 'cadena_comercial', 'cadena_comercial')}
        SELECT CAST(row_number() OVER (ORDER BY cadena_c) AS SMALLINT) AS cadena_key,
               l.cadena_c, c.cadena_comercial
        FROM llaves l LEFT JOIN cadena_comercial c USING (cadena_c)""")

    ventana = contrato["alcance"]["ventana"]
    desde, hasta = (intermedia._texto_sql(ventana[k]) for k in ("desde", "hasta"))
    con.execute(f"""CREATE OR REPLACE TABLE dim_fecha AS
        SELECT CAST(strftime(d, '%Y%m%d') AS INTEGER) AS fecha_key, d AS fecha,
               CAST(year(d) AS SMALLINT) AS anio, CAST(month(d) AS SMALLINT) AS mes,
               strftime(d, '%Y-%m') || '-Q' || CASE WHEN day(d) <= 15 THEN '1' ELSE '2' END
                   AS quincena,
               CAST(isodow(d) AS SMALLINT) AS dia_semana, isodow(d) >= 6 AS es_fin_de_semana
        FROM (SELECT CAST(unnest(generate_series(DATE '{desde}', DATE '{hasta}',
                                                 INTERVAL 1 DAY)) AS DATE) AS d)""")

    con.execute("""CREATE OR REPLACE TABLE hechos_precio AS
        SELECT CAST(row_number() OVER (ORDER BY o.lote, o.huella_fila, o.ocurrencia)
                    AS BIGINT) AS observacion_id,
               CAST(strftime(o.fecha, '%Y%m%d') AS INTEGER) AS fecha_key,
               a.articulo_key, e.establecimiento_key, c.cadena_key,
               o.marca, o.marca = 'S/M' AS es_generico, o.catalogo, o.precio,
               o.lote, o.huella_fila, o.ocurrencia, o.ingerido_en
        FROM obs o
        JOIN dim_articulo a USING (producto_c, presentacion_c)
        JOIN dim_establecimiento e USING (nombre_c, direccion_c, municipio_c, entidad)
        JOIN dim_cadena c USING (cadena_c)""")

    agregados(con)
    return {t: con.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in TABLAS}


def agregados(con):
    """Los tres agregados de §4, sobre `articulo_canonico_key`.

    Leen las tablas locales `hechos_precio` y las dimensiones. La reconciliación
    (#206) reescribe `articulo_canonico_key` y vuelve a llamar a esta función: los
    hechos no se tocan."""
    junta = """FROM hechos_precio h
        JOIN dim_articulo a USING (articulo_key)
        JOIN dim_establecimiento e USING (establecimiento_key)
        JOIN dim_fecha f USING (fecha_key)"""
    con.execute(f"""CREATE OR REPLACE TABLE agg_articulo_entidad_quincena AS
        SELECT a.articulo_canonico_key, e.entidad, f.quincena, CAST(count(*) AS INTEGER) AS n,
               min(h.precio) AS minimo, quantile_disc(h.precio, 0.25) AS p25,
               quantile_disc(h.precio, 0.5) AS mediana, quantile_disc(h.precio, 0.75) AS p75,
               max(h.precio) AS maximo
        {junta}
        GROUP BY ALL""")
    con.execute(f"""CREATE OR REPLACE TABLE agg_articulo_cadena_entidad_quincena AS
        SELECT a.articulo_canonico_key, h.cadena_key, e.entidad, f.quincena,
               CAST(count(*) AS INTEGER) AS n,
               CAST(count(DISTINCT h.establecimiento_key) AS INTEGER) AS n_tiendas,
               quantile_disc(h.precio, 0.5) AS mediana
        {junta}
        GROUP BY ALL""")
    con.execute("""CREATE OR REPLACE TABLE rango_historico AS
        SELECT articulo_canonico_key, entidad, min(mediana) AS desde, max(mediana) AS hasta,
               CAST(count(*) AS INTEGER) AS quincenas
        FROM agg_articulo_entidad_quincena
        GROUP BY ALL""")


def huella(con, prefijo="", excluir=("ingerido_en",)):
    """Una huella de las ocho tablas que no depende del orden de las filas.

    Por tabla, la cuenta y la suma del hash de cada fila: con 2.6 millones de
    hechos, juntar las filas en un solo texto, como hace la capa intermedia con un
    lote, no cabe en memoria. `ingerido_en` queda fuera por la misma razón que
    allá: reprocesar es volver a ingerir."""
    partes = []
    for t in TABLAS:
        tabla = f"{prefijo}{t}"
        cols = [r[0] for r in con.execute(f"DESCRIBE {tabla}").fetchall()
                if r[0] not in excluir]
        fila = ", ".join(f'COALESCE(CAST("{c}" AS VARCHAR), chr(0))' for c in cols)
        n, suma = con.execute(f"SELECT count(*), COALESCE(sum(hash(concat_ws(chr(31), "
                              f"{fila}))), 0) FROM {tabla}").fetchone()
        partes.append(f"{t}:{n}:{suma}")
    return hashlib.sha256("|".join(partes).encode()).hexdigest()


# ── La carga ────────────────────────────────────────────────────────────────

def crear_tablas(con, contrato, motor):
    """El esquema y las tablas en `destino`, si no existen."""
    if motor == "postgres":
        for sentencia in ddl(contrato, "postgres"):
            con.execute(f"CALL postgres_execute('destino', '{intermedia._texto_sql(sentencia)}')")
        # Igual que en la capa intermedia: lo creado con postgres_execute no está en
        # la caché de DuckDB hasta limpiarla.
        con.execute("CALL pg_clear_cache()")
    else:
        for sentencia in ddl(contrato, "duckdb", "destino."):
            con.execute(sentencia)


def escribir(con, contrato):
    """Reemplaza las ocho tablas de `destino` con las locales: todo o nada.

    Se borra en el orden inverso al de la escritura y se escribe primero lo que
    los demás usan. Si algo falla a la mitad, se revierte y la estrella queda como
    estaba: la consola nunca lee una estrella a medias."""
    cols = columnas(contrato)
    con.execute("BEGIN TRANSACTION")
    try:
        for t in reversed(TABLAS):
            con.execute(f"DELETE FROM destino.{ESQUEMA}.{t}")
        for t in TABLAS:
            lista = ", ".join(f'"{c[0]}"' for c in cols[t])
            con.execute(f"INSERT INTO destino.{ESQUEMA}.{t} ({lista}) SELECT {lista} FROM {t}")
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise


def cargar(contrato=None, simular=False, carpeta=None):
    """Recalcula la estrella desde la capa intermedia y la escribe en el destino.

    Comprueba que cada observación de la capa intermedia sea un hecho: un artículo
    o una tienda sin su dimensión perdería filas en silencio en el JOIN, y una
    cuenta que no cuadra no se carga."""
    contrato = contrato or leer_contrato()
    con = intermedia._con()
    destino = intermedia.adjuntar_destino(con, contrato, simular, carpeta)
    try:
        crear_tablas(con, contrato, destino["motor"])
        observaciones = con.execute(f"SELECT count(*) FROM {ORIGEN}").fetchone()[0]
        cuentas = construir(con, contrato)
        if cuentas["hechos_precio"] != observaciones:
            raise RuntimeError(
                f"la capa intermedia tiene {observaciones:,} observaciones y salieron "
                f"{cuentas['hechos_precio']:,} hechos. No se carga una estrella que pierde "
                "filas: alguna no encontró su dimensión")
        firma = huella(con)
        escribir(con, contrato)
        en_destino = {t: con.execute(f"SELECT count(*) FROM destino.{ESQUEMA}.{t}").fetchone()[0]
                      for t in TABLAS}
        if en_destino != cuentas:
            raise RuntimeError(f"el destino quedó con {en_destino} y se escribieron {cuentas}")
    finally:
        con.execute("DETACH destino")
    return {"motor": destino["motor"], "donde": destino["donde"], "esquema": ESQUEMA,
            "observaciones": int(observaciones), "filas": {t: int(n) for t, n in cuentas.items()},
            "en_destino": {t: int(n) for t, n in en_destino.items()}, "huella": firma}


def contar(contrato=None, simular=False, carpeta=None):
    """Cuántas filas tiene cada tabla de la capa de consumo en el destino."""
    contrato = contrato or leer_contrato()
    con = intermedia._con()
    destino = intermedia.adjuntar_destino(con, contrato, simular, carpeta)
    try:
        crear_tablas(con, contrato, destino["motor"])
        return destino, {t: con.execute(f"SELECT count(*) FROM destino.{ESQUEMA}.{t}").fetchone()[0]
                         for t in TABLAS}
    finally:
        con.execute("DETACH destino")


def main():
    preparar_salida()
    import argparse

    ap = argparse.ArgumentParser(description="La capa de consumo: el esquema estrella, "
                                             "desde la capa intermedia")
    ap.add_argument("--cargar", action="store_true",
                    help="recalcula la estrella y la reemplaza en el destino")
    ap.add_argument("--contar", action="store_true",
                    help="cuántas filas tiene cada tabla en el destino")
    ap.add_argument("--simular", action="store_true",
                    help="el DuckDB de la carpeta de corridas, no postgres-analytics")
    a = ap.parse_args()
    if not (a.cargar or a.contar):
        ap.error("di --cargar, --contar o las dos")

    contrato = leer_contrato()
    if a.cargar:
        r = cargar(contrato, simular=a.simular)
        print(f"✓ estrella recalculada desde {r['observaciones']:,} observaciones de la capa "
              f"intermedia · {r['motor']} {r['donde']} · huella {r['huella'][:12]}")
    destino, cuentas = contar(contrato, simular=a.simular)
    print(f"\n{destino['motor']} {destino['donde']} · esquema {ESQUEMA}\n")
    for t in TABLAS:
        print(f"  {t:<38}{cuentas[t]:>12,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
