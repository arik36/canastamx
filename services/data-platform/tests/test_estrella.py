"""Pruebas de `ingestion/estrella.py` · la capa de consumo (T053), sin Dagster.

Contra el criterio de #200: «`hechos_precio` y las cuatro dimensiones tienen datos
[...]. Los tres agregados se calculan sobre `articulo_canonico_key`, así que la
reconciliación los recalcula sin tocar los hechos.» La carga de punta a punta, desde
los activos, está en `test_orquestacion.py`.

Aquí la capa intermedia es una tabla hecha a mano con sus columnas: lo que se prueba
es cómo se arma la estrella, no cómo llegaron las filas.
"""

import datetime as dt
import sys
from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest

PLATAFORMA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATAFORMA / "ingestion"))

import estrella
from ingesta import leer_contrato

duckdb = pytest.importorskip("duckdb")


@pytest.fixture(scope="module")
def contrato():
    return leer_contrato()


BASE = {"lote": "07-2026_Q2", "ocurrencia": 1, "ingerido_en": "2026-08-01 00:00:00+00",
        "entidad": "Guanajuato", "clave_producto": "leche", "clave_presentacion": "1 l",
        "producto": "Leche", "presentacion": "1 L", "categoria": "Lácteos",
        "catalogo_normalizado": "BASICOS", "clave_marca": "LALA",
        "clave_nombre_comercial": "soriana centro", "clave_direccion": "juarez 1",
        "municipio": "León", "nombre_comercial": "Soriana Centro", "direccion": "Juárez 1",
        "giro": "Supermercado", "latitud": 21.12, "longitud": -101.68,
        "cadena_comercial": "Soriana", "fecha_registro": "2026-07-20", "precio": "25.00"}


def _capa(con, filas):
    """La tabla `origen`, con las columnas de la capa intermedia que lee la estrella."""
    crudo = pd.DataFrame([{**BASE, "huella_fila": f"h{i:03d}", **f} for i, f in enumerate(filas)])
    con.register("crudo", crudo)
    con.execute("""CREATE OR REPLACE TABLE origen AS
        SELECT * REPLACE (CAST(ocurrencia AS INTEGER) AS ocurrencia,
                          CAST(ingerido_en AS TIMESTAMPTZ) AS ingerido_en,
                          CAST(latitud AS DOUBLE) AS latitud,
                          CAST(longitud AS DOUBLE) AS longitud,
                          CAST(fecha_registro AS DATE) AS fecha_registro,
                          CAST(precio AS DECIMAL(12,2)) AS precio)
        FROM crudo""")


def _estrella(contrato, filas):
    con = duckdb.connect()
    _capa(con, filas)
    cuentas = estrella.construir(con, contrato, origen="origen")
    return con, cuentas


def test_cada_observacion_es_un_hecho_y_ninguno_queda_huerfano(contrato):
    con, cuentas = _estrella(contrato, [
        {}, {"clave_producto": "huevo", "producto": "Huevo", "precio": "52.00"},
        {"clave_nombre_comercial": "mercado hidalgo", "nombre_comercial": "Mercado Hidalgo",
         "cadena_comercial": "Central de Abastos"}])
    assert cuentas["hechos_precio"] == 3
    assert (cuentas["dim_articulo"], cuentas["dim_establecimiento"]) == (2, 2)
    for dim, llave in (("dim_articulo", "articulo_key"), ("dim_fecha", "fecha_key"),
                       ("dim_establecimiento", "establecimiento_key"),
                       ("dim_cadena", "cadena_key")):
        huerfanos = con.execute(f"SELECT count(*) FROM hechos_precio ANTI JOIN {dim} "
                                f"USING ({llave})").fetchone()[0]
        assert huerfanos == 0, f"{huerfanos} hechos sin su {dim}"


def test_la_cadena_con_y_sin_s_final_es_la_misma(contrato):
    """El modelo: «Central de Abasto» y «Central de Abastos» son la misma cadena."""
    con, cuentas = _estrella(contrato, [{"cadena_comercial": "Central de Abasto"},
                                        {"cadena_comercial": "Central de Abastos"},
                                        {"cadena_comercial": "Central de Abastos"}])
    assert cuentas["dim_cadena"] == 1
    assert con.execute("SELECT cadena_c, cadena_comercial FROM dim_cadena").fetchone() == (
        "central de abasto", "Central de Abastos")


def test_el_nombre_que_se_muestra_es_el_mas_frecuente_y_el_empate_no_depende_del_orden(
        contrato):
    con, _ = _estrella(contrato, [{"producto": "Leche"}, {"producto": "LECHE"},
                                  {"producto": "Leche"}])
    assert con.execute("SELECT producto FROM dim_articulo").fetchone()[0] == "Leche"

    empate = [{"producto": "Leche"}, {"producto": "LECHE"}]
    elegidos = [_estrella(contrato, orden)[0].execute(
        "SELECT producto FROM dim_articulo").fetchone()[0] for orden in (empate, empate[::-1])]
    assert elegidos == ["LECHE", "LECHE"], "el empate cambió con el orden de las filas"


def test_la_tienda_queda_en_su_ubicacion_mas_frecuente(contrato):
    """Un promedio de coordenadas cambia con el orden de la suma (RF-25) y pone la
    tienda donde no está; la pareja más frecuente, no."""
    con, _ = _estrella(contrato, [{"latitud": 21.10, "longitud": -101.60},
                                  {"latitud": 21.12, "longitud": -101.68},
                                  {"latitud": 21.12, "longitud": -101.68},
                                  {"latitud": None, "longitud": None}])
    assert con.execute("SELECT latitud, longitud FROM dim_establecimiento").fetchone() == (
        21.12, -101.68)


def test_las_categorias_ocultas_salen_del_contrato(contrato):
    con, _ = _estrella(contrato, [{}, {"clave_producto": "cerveza clara",
                                       "producto": "Cerveza Clara", "categoria": "Cerveza"}])
    ocultos = dict(con.execute(
        "SELECT producto, oculto_por_omision FROM dim_articulo").fetchall())
    assert ocultos == {"Leche": False, "Cerveza Clara": True}


def test_los_agregados_salen_de_articulo_canonico_key(contrato):
    """**La prueba del criterio.** Dos variantes del mismo artículo son dos grupos;
    al reconciliarlas (#206) se reescribe `articulo_canonico_key`, se vuelven a
    calcular los agregados y quedan en uno, con los hechos intactos."""
    con, _ = _estrella(contrato, [
        {"clave_producto": "frijol", "producto": "Frijol", "precio": "30.00"},
        {"clave_producto": "frijol", "producto": "Frijol", "precio": "32.00"},
        {"clave_producto": "frijoles", "producto": "Frijoles", "precio": "40.00"}])
    assert con.execute("SELECT count(*) FROM agg_articulo_entidad_quincena").fetchone()[0] == 2
    assert con.execute("SELECT bool_and(articulo_canonico_key = articulo_key) "
                       "FROM dim_articulo").fetchone()[0], "sin reconciliar, son iguales"
    hechos = con.execute("SELECT * FROM hechos_precio ORDER BY observacion_id").df()

    con.execute("""UPDATE dim_articulo SET articulo_canonico_key =
                     (SELECT articulo_key FROM dim_articulo WHERE producto_c = 'frijol')
                   WHERE producto_c = 'frijoles'""")
    estrella.agregados(con)

    assert con.execute("SELECT n, minimo, mediana, maximo FROM "
                       "agg_articulo_entidad_quincena").fetchall() == [
        (3, Decimal("30.00"), Decimal("32.00"), Decimal("40.00"))]
    assert con.execute("SELECT quincenas FROM rango_historico").fetchall() == [(1,)]
    assert con.execute("SELECT * FROM hechos_precio ORDER BY observacion_id").df().equals(hechos)


def test_la_mediana_es_un_precio_que_se_observo(contrato):
    """P-02: con dos precios, `quantile_cont` daría 26.50, que nadie cobró."""
    con, _ = _estrella(contrato, [{"precio": "25.00"}, {"precio": "28.00"}])
    mediana = con.execute("SELECT mediana FROM agg_articulo_entidad_quincena").fetchone()[0]
    assert mediana in (Decimal("25.00"), Decimal("28.00"))


def test_dim_fecha_cubre_la_ventana_del_contrato(contrato):
    con, cuentas = _estrella(contrato, [{}])
    ventana = contrato["alcance"]["ventana"]
    desde, hasta = (dt.date.fromisoformat(str(ventana[k])) for k in ("desde", "hasta"))
    assert cuentas["dim_fecha"] == (hasta - desde).days + 1
    quincenas = dict(con.execute("SELECT fecha, quincena FROM dim_fecha WHERE fecha IN "
                                 "(DATE '2026-07-15', DATE '2026-07-16')").fetchall())
    assert quincenas == {dt.date(2026, 7, 15): "2026-07-Q1", dt.date(2026, 7, 16): "2026-07-Q2"}


def test_el_ddl_sale_del_contrato_y_trae_sus_llaves(contrato):
    pg = estrella.ddl(contrato, "postgres")
    assert pg[0] == "CREATE SCHEMA IF NOT EXISTS consumo"
    assert len(pg) == 1 + len(estrella.TABLAS)
    assert all("PRIMARY KEY" in s for s in pg[1:])
    assert sum("UNIQUE" in s for s in pg) == 3, "las tres dimensiones con llave natural"
    hechos = next(s for s in pg if "consumo.hechos_precio " in s)
    assert '"precio" numeric(12,2) NOT NULL' in hechos

    otro = {**contrato, "columnas": {**contrato["columnas"], "precio": {
        **contrato["columnas"]["precio"], "tipo": "decimal(14,2)"}}}
    assert '"precio" numeric(14,2) NOT NULL' in next(
        s for s in estrella.ddl(otro, "postgres") if "consumo.hechos_precio " in s), (
        "el tipo del precio está escrito en el código y no sale del contrato")


def test_el_orden_de_la_capa_intermedia_no_cambia_la_estrella(contrato):
    """RF-25: las mismas filas en otro orden dan la misma estrella, llaves incluidas."""
    filas = [{"precio": "25.00"}, {"clave_producto": "huevo", "producto": "Huevo"},
             {"cadena_comercial": "Chedraui"}]
    con1, _ = _estrella(contrato, filas)
    con2 = duckdb.connect()
    _capa(con2, filas)
    con2.execute("CREATE OR REPLACE TABLE origen AS SELECT * FROM origen ORDER BY random()")
    estrella.construir(con2, contrato, origen="origen")
    assert estrella.huella(con1) == estrella.huella(con2)
