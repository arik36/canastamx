"""Pruebas de `ingestion/intermedia.py` · la capa intermedia de T048.

Contra el criterio de la tarjeta (#186), frase por frase:

  · «sin un solo `?` en las once columnas de aplica_a»
  · «el precio a DECIMAL(12,2)»
  · «la captura doble con desempate: min_precio y un desempate que dependa del
    contenido de la fila, no de su posición»
  · «exactamente las filas que lote_promovido dejó salir menos las sobrantes de
    captura doble de su linaje»
  · «materializarla dos veces deja las mismas filas (RF-25), y un lote detenido no
    deja ninguna»
  · «cada una con su lote y su ingerido_en»

Las filas entran como en la plataforma: escritas en un CSV del lote y leídas con
`compuerta.leer_alcance()`, que es la misma lectura de la ingesta. La carga va a un
DuckDB en una carpeta temporal; la de PostgreSQL está al final y sólo corre si se
le pide (ver `test_la_carga_a_postgres_reemplaza_la_particion`).
"""

import copy
import csv
import json
import os
import sys
from decimal import Decimal
from pathlib import Path

import duckdb
import pytest

PLATAFORMA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATAFORMA / "ingestion"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import compuerta
import intermedia
import lote
import reparacion
from ambiguos import CANDIDATOS, con_candidatos
from ingesta import columnas_del_contrato, leer_contrato

INGERIDO = "2026-10-30T18:00:00+00:00"


@pytest.fixture(scope="module")
def contrato():
    return leer_contrato()


@pytest.fixture(scope="module")
def columnas(contrato):
    return columnas_del_contrato(contrato)


def fila(columnas, **kw):
    r = {c: "x" for c in columnas}
    r.update({"estado": "Guanajuato", "catalogo": "Basicos",
              "fecha_registro": "2026/07/20", "precio": "25.00",
              "latitud": "21.123456", "longitud": "-101.682109"})
    r.update(kw)
    return r


def alcance(carpeta, columnas, filas, contrato, nombre="07-2026_Q2.csv"):
    """Las filas como las ve la plataforma: un CSV del lote, leído por la compuerta."""
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / nombre
    with ruta.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columnas)
        w.writeheader()
        w.writerows(filas)
    return compuerta.leer_alcance(ruta, contrato)


def promover(df, contrato):
    """Lo que `lote_promovido` deja salir de un lote que pasa D-07."""
    reparables, _, _ = reparacion.apartar_irreparables(df, contrato)
    salen, _, res_grupo = lote.revisar_grupos(reparables, contrato)
    return salen, res_grupo


def capa(con, orden="producto, precio, huella_fila"):
    return con.execute(f"SELECT * FROM capa ORDER BY {orden}").df()


# ── Las columnas, del contrato ─────────────────────────────────────────────

def test_las_columnas_de_la_capa_salen_del_contrato(contrato):
    cols = {c[0]: c for c in intermedia.columnas_de_la_capa(contrato)}
    assert set(contrato["columnas"]) <= set(cols)
    assert cols["precio"][1:3] == ("DECIMAL(12,2)", "numeric(12,2)")
    assert cols["fecha_registro"][1:3] == ("DATE", "date")
    # latitud y longitud: `decimal` sin precisión no puede ser el DECIMAL(18,3) de
    # DuckDB, que redondearía la coordenada.
    assert cols["latitud"][1:3] == ("DOUBLE", "double precision")
    for c in ("lote", "ingerido_en", "huella_fila", "version_contrato"):
        assert cols[c][3] is False, f"{c} no puede quedar vacía (SLA-D-10)"


def test_el_tipo_del_precio_lo_decide_el_contrato(contrato):
    otro = copy.deepcopy(contrato)
    otro["columnas"]["precio"]["tipo"] = "decimal(14,3)"
    sentencias = intermedia.ddl(otro, "postgres")
    assert '"precio" numeric(14,3) NOT NULL' in sentencias[1]


def test_el_ddl_corre_en_una_base_adjunta(contrato, tmp_path):
    con = duckdb.connect()
    con.execute(f"ATTACH '{tmp_path / 'x.duckdb'}' AS destino")
    for s in intermedia.ddl(contrato, "duckdb", "destino."):
        con.execute(s)
    tipos = dict(con.execute("SELECT column_name, data_type FROM information_schema.columns "
                             "WHERE table_schema = 'intermedia'").fetchall())
    assert tipos["precio"] == "DECIMAL(12,2)" and tipos["ingerido_en"].startswith("TIMESTAMP")


# ── Reparar, sin dejar un solo `?` ─────────────────────────────────────────

def test_repara_en_las_once_columnas_y_no_queda_un_interrogante(contrato, columnas, tmp_path):
    df = alcance(tmp_path, columnas, [
        fila(columnas, producto="Camar?n", giro="Panader?as", direccion="D1"),
        fila(columnas, producto="F?rmula L?ctea", categoria="Art?culos Deportivos",
             direccion="D2"),
    ], contrato)
    salen, _ = promover(df, contrato)
    con, r = intermedia.construir(salen, contrato, "07-2026_Q2", INGERIDO)
    t = capa(con)
    assert sorted(t["producto"]) == ["Camarón", "Fórmula Láctea"]
    assert "Panaderías" in set(t["giro"]) and "Artículos Deportivos" in set(t["categoria"])
    aplica = contrato["normalizacion"]["reparar_interrogantes"]["aplica_a"]
    assert not any(t[c].astype(str).str.contains("?", regex=False).any() for c in aplica)
    assert r["reparadas_por_columna"] == {"producto": 2, "categoria": 1, "giro": 1}


def test_si_llega_un_interrogante_irreparable_se_detiene(contrato, columnas, tmp_path):
    """Postcondición de CU-03. Si la compuerta no lo apartó, cargarlo escondería
    el fallo; la capa prefiere no cargar."""
    df = alcance(tmp_path, columnas, [fila(columnas, producto="Nada?Igual")], contrato)
    with pytest.raises(ValueError, match="no se puede reparar"):
        intermedia.construir(df, contrato, "07-2026_Q2", INGERIDO)


def test_lo_que_la_frecuencia_repara_tambien_se_escribe_reparado(contrato, columnas, tmp_path):
    otro = con_candidatos(contrato, tmp_path / "t", CANDIDATOS)
    df = alcance(tmp_path, columnas, [fila(columnas, marca="Kellogg?s")], otro)
    salen, _ = promover(df, otro)
    con, _ = intermedia.construir(salen, otro, "07-2026_Q2", INGERIDO)
    t = capa(con)
    assert t["marca"].tolist() == ["Kellogg's"] and t["clave_marca"].tolist() == ["KELLOGG'S"]


# ── Tipar ──────────────────────────────────────────────────────────────────

def test_el_precio_queda_en_decimal_y_la_fecha_en_date(contrato, columnas, tmp_path):
    df = alcance(tmp_path, columnas, [fila(columnas, precio="30.5")], contrato)
    salen, _ = promover(df, contrato)
    con, _ = intermedia.construir(salen, contrato, "07-2026_Q2", INGERIDO)
    tipos = {r[0]: r[1] for r in con.execute("DESCRIBE capa").fetchall()}
    assert tipos["precio"] == "DECIMAL(12,2)" and tipos["fecha_registro"] == "DATE"
    precio, lat = con.execute("SELECT precio, latitud FROM capa").fetchone()
    assert precio == Decimal("30.50")
    assert lat == pytest.approx(21.123456), "la coordenada no se puede redondear"


def test_cada_fila_lleva_su_lote_su_ingesta_y_su_contrato(contrato, columnas, tmp_path):
    df = alcance(tmp_path, columnas, [fila(columnas, producto=f"P{i}") for i in range(3)],
                 contrato)
    salen, _ = promover(df, contrato)
    con, _ = intermedia.construir(salen, contrato, "07-2026_Q2", INGERIDO)
    t = capa(con)
    assert set(t["lote"]) == {"07-2026_Q2"} and set(t["quincena"]) == {"2026-07-Q2"}
    assert set(t["entidad"]) == {"Guanajuato"}
    assert set(t["version_contrato"]) == {str(contrato["version"])}
    assert t["ingerido_en"].notna().all() and t["huella_fila"].str.len().eq(64).all()


# ── Deduplicar la captura doble ────────────────────────────────────────────

def test_de_la_captura_doble_queda_la_de_menor_precio(contrato, columnas, tmp_path):
    df = alcance(tmp_path, columnas, [fila(columnas, producto="Frijol", precio="30.50"),
                                      fila(columnas, producto="Frijol", precio="30.00")],
                 contrato)
    salen, res = promover(df, contrato)
    con, r = intermedia.construir(salen, contrato, "07-2026_Q2", INGERIDO)
    assert capa(con)["precio"].tolist() == [Decimal("30.00")]
    assert r["sobrantes_captura_doble"] == res["sobrantes_captura_doble"] == 1


def test_las_observaciones_multiples_se_quedan_todas(contrato, columnas, tmp_path):
    df = alcance(tmp_path, columnas, [fila(columnas, producto="Arroz", precio="20.00"),
                                      fila(columnas, producto="Arroz", precio="37.00")],
                 contrato)
    salen, _ = promover(df, contrato)
    con, r = intermedia.construir(salen, contrato, "07-2026_Q2", INGERIDO)
    assert len(capa(con)) == 2 and r["sobrantes_captura_doble"] == 0


def test_a_igual_precio_decide_el_contenido_y_no_la_posicion(contrato, columnas, tmp_path):
    """El error de `clasif` en T031: desempataba por `rid`, el número de fila al
    leer. Con el lote al revés, la fila que queda tiene que ser la misma."""
    a = fila(columnas, producto="Frijol", precio="30.00", cadena_comercial="Uno")
    b = fila(columnas, producto="Frijol", precio="30.00", cadena_comercial="Dos")
    quedan = []
    for i, orden in enumerate(([a, b], [b, a])):
        df = alcance(tmp_path / str(i), columnas, orden, contrato)
        salen, _ = promover(df, contrato)
        con, _ = intermedia.construir(salen, contrato, "07-2026_Q2", INGERIDO)
        quedan.append((capa(con)["cadena_comercial"].tolist(), intermedia.huella_de_la_capa(con)))
    assert quedan[0] == quedan[1] and len(quedan[0][0]) == 1


def test_el_umbral_de_la_captura_doble_lo_decide_el_contrato(contrato, columnas, tmp_path):
    df = alcance(tmp_path, columnas, [fila(columnas, producto="P", precio="10.00"),
                                      fila(columnas, producto="P", precio="12.00")], contrato)
    salen, _ = promover(df, contrato)
    con, _ = intermedia.construir(salen, contrato, "07-2026_Q2", INGERIDO)
    assert len(capa(con)) == 2, "$2 son observaciones múltiples con el $1 del contrato"

    otro = copy.deepcopy(contrato)
    otro["clave_de_fila"]["captura_doble"]["menos_de"] = 5
    salen, res = promover(df, otro)
    con, _ = intermedia.construir(salen, otro, "07-2026_Q2", INGERIDO)
    assert len(capa(con)) == 1 and res["sobrantes_captura_doble"] == 1


def test_dos_filas_identicas_que_se_quedan_tienen_su_ocurrencia(contrato, columnas, tmp_path):
    """El contrato decide por grupo: en un grupo de observaciones múltiples se
    quedan todas, aun dos que llegaron idénticas. Comparten huella; la ocurrencia
    las distingue y la llave no se repite."""
    gemela = fila(columnas, producto="Huevo", precio="10.00")
    df = alcance(tmp_path, columnas, [gemela, dict(gemela),
                                      fila(columnas, producto="Huevo", precio="20.00")],
                 contrato)
    salen, _ = promover(df, contrato)
    con, _ = intermedia.construir(salen, contrato, "07-2026_Q2", INGERIDO)
    t = capa(con)
    assert len(t) == 3
    repetida = t[t["precio"] == Decimal("10.00")]
    assert repetida["huella_fila"].nunique() == 1
    assert sorted(repetida["ocurrencia"]) == [1, 2]


def test_la_cuenta_cuadra_con_la_compuerta_de_grupo(contrato, columnas, tmp_path):
    """**El criterio de T048:** las que dejó salir el lote menos las sobrantes de
    captura doble. Un lote con todo junto: texto que repara el diccionario y la
    frecuencia, capturas dobles de dos y de tres, observaciones múltiples, una
    colisión alta y filas únicas."""
    otro = con_candidatos(contrato, tmp_path / "t", CANDIDATOS)
    filas = [fila(columnas, producto=f"P{i}", direccion=f"C{i}") for i in range(20)]
    filas += [fila(columnas, producto="Camarón", precio="100.00"),
              fila(columnas, producto="Camar?n", precio="100.40")]           # doble, reparada
    filas += [fila(columnas, producto="Cereal", marca="Kellogg's", precio="40.00"),
              fila(columnas, producto="Cereal", marca="Kellogg?s", precio="40.00"),
              fila(columnas, producto="Cereal", marca="Kellogg's", precio="40.90")]  # triple
    filas += [fila(columnas, producto="Arroz", precio="20.00"),
              fila(columnas, producto="Arroz", precio="37.00")]              # múltiples
    filas += [fila(columnas, producto="Aceite", precio="40.00"),
              fila(columnas, producto="Aceite", precio="200.00")]            # colisión
    df = alcance(tmp_path, columnas, filas, otro)
    salen, res = promover(df, otro)
    _, r = intermedia.construir(salen, otro, "07-2026_Q2", INGERIDO)
    assert res["grupos_en_colision"] == 1 and res["sobrantes_captura_doble"] == 3
    assert r["filas_salida"] == res["filas_salida"] - res["sobrantes_captura_doble"] == 24
    assert r["sobrantes_captura_doble"] == res["sobrantes_captura_doble"]


# ── Las huellas ────────────────────────────────────────────────────────────

def test_las_huellas_son_las_de_la_compuerta_de_fila(contrato, columnas, tmp_path):
    df = alcance(tmp_path, columnas, [fila(columnas, producto="Camar?n"),
                                      fila(columnas, latitud="", longitud="")], contrato)
    for i, h in enumerate(intermedia.huellas(df, columnas)):
        crudo = {c: (None if df[c].isna().iloc[i] else df.iloc[i][c]) for c in columnas}
        crudo = {c: (v.isoformat() if hasattr(v, "isoformat") else
                     (str(v) if v is not None else None)) for c, v in crudo.items()}
        assert h == compuerta.huella(crudo, columnas)


def test_la_huella_de_la_capa_no_depende_del_orden_ni_de_la_hora(contrato, columnas, tmp_path):
    filas = [fila(columnas, producto=f"P{i}", precio=f"{10 + i}.00") for i in range(5)]
    huellas = set()
    for i, (orden, hora) in enumerate(((filas, INGERIDO),
                                       (filas[::-1], "2026-11-01T09:00:00+00:00"))):
        df = alcance(tmp_path / str(i), columnas, orden, contrato)
        salen, _ = promover(df, contrato)
        con, _ = intermedia.construir(salen, contrato, "07-2026_Q2", hora)
        huellas.add(intermedia.huella_de_la_capa(con))
    assert len(huellas) == 1


# ── Cargar: reemplazar la partición, todo o nada ───────────────────────────

def _construida(contrato, columnas, carpeta, filas, nombre="07-2026_Q2"):
    df = alcance(carpeta, columnas, filas, contrato, nombre=f"{nombre}.csv")
    salen, _ = promover(df, contrato)
    return intermedia.construir(salen, contrato, nombre, INGERIDO)[0]


def _en_destino(carpeta, lote_nombre):
    con = duckdb.connect(str(carpeta / intermedia.ARCHIVO_DE_SIMULACION), read_only=True)
    try:
        return con.execute("SELECT count(*) FROM intermedia.observacion WHERE lote = ?",
                           [lote_nombre]).fetchone()[0]
    finally:
        con.close()


def test_cargar_dos_veces_deja_las_mismas_filas_y_un_lote_detenido_ninguna(
        contrato, columnas, tmp_path):
    destino = tmp_path / "destino"
    filas = [fila(columnas, producto=f"P{i}") for i in range(3)]
    for _ in range(2):
        r = intermedia.cargar(_construida(contrato, columnas, tmp_path / "a", filas),
                              "07-2026_Q2", contrato, simular=True, carpeta=destino)
    assert r["borradas"] == 3 and r["en_destino"] == 3 == _en_destino(destino, "07-2026_Q2")

    otras = [fila(columnas, producto=f"Q{i}", fecha_registro="2026/07/05") for i in range(2)]
    intermedia.cargar(_construida(contrato, columnas, tmp_path / "b", otras, "07-2026_Q1"),
                      "07-2026_Q1", contrato, simular=True, carpeta=destino)
    r = intermedia.cargar(intermedia.capa_vacia(contrato), "07-2026_Q2", contrato,
                          simular=True, carpeta=destino)
    assert r["en_destino"] == 0 == _en_destino(destino, "07-2026_Q2")
    assert _en_destino(destino, "07-2026_Q1") == 2, "vaciar un lote no toca a los demás"


def test_si_la_escritura_falla_la_capa_queda_como_estaba(contrato, columnas, tmp_path):
    """CU-02 · 6a: «no deja filas a medias». Se fuerza un fallo a mitad de la
    escritura —dos filas con la misma llave— y el lote conserva lo que tenía."""
    destino = tmp_path / "destino"
    filas = [fila(columnas, producto=f"P{i}") for i in range(3)]
    intermedia.cargar(_construida(contrato, columnas, tmp_path / "a", filas),
                      "07-2026_Q2", contrato, simular=True, carpeta=destino)
    con = _construida(contrato, columnas, tmp_path / "b", filas)
    con.execute("INSERT INTO capa SELECT * FROM capa LIMIT 1")      # la llave se repite
    with pytest.raises(duckdb.ConstraintException):
        intermedia.cargar(con, "07-2026_Q2", contrato, simular=True, carpeta=destino)
    assert _en_destino(destino, "07-2026_Q2") == 3


def test_cargar_se_niega_a_escribir_filas_de_otro_lote(contrato, columnas, tmp_path):
    """Reemplazar la partición de un lote sólo escribe filas de ese lote. Si la capa
    trae filas de otro, `cargar()` se niega antes de tocar el destino: si no, borraría
    la partición pedida y escribiría en la ajena, que crecería sin aviso. Así pasó
    la primera vez que la prueba de PostgreSQL corrió contra la base real."""
    destino = tmp_path / "destino"
    reales = [fila(columnas, producto=f"Q{i}") for i in range(3)]
    intermedia.cargar(_construida(contrato, columnas, tmp_path / "a", reales),
                      "07-2026_Q2", contrato, simular=True, carpeta=destino)
    de_otro_lote = _construida(contrato, columnas, tmp_path / "b",
                               [fila(columnas, producto=f"P{i}") for i in range(3)])
    with pytest.raises(ValueError, match="07-2026_Q2"):
        intermedia.cargar(de_otro_lote, "12-2099_Q1", contrato, simular=True, carpeta=destino)
    assert _en_destino(destino, "07-2026_Q2") == 3, "el lote ajeno quedó como estaba"
    assert _en_destino(destino, "12-2099_Q1") == 0


# ── La comprobación para la evidencia ──────────────────────────────────────

def test_verificar_cuadra_con_el_registro_del_lote(contrato, columnas, tmp_path):
    destino, corridas = tmp_path / "destino", tmp_path / "corridas"
    corridas.mkdir()
    filas = [fila(columnas, producto="Frijol", precio="30.00"),
             fila(columnas, producto="Frijol", precio="30.50")]
    filas += [fila(columnas, producto=f"P{i}") for i in range(3)]
    df = alcance(tmp_path / "a", columnas, filas, contrato)
    salen, res = promover(df, contrato)
    con, _ = intermedia.construir(salen, contrato, "07-2026_Q2", INGERIDO)
    intermedia.cargar(con, "07-2026_Q2", contrato, simular=True, carpeta=destino)

    def registro(filas_salida, sobrantes, resultado="PASO"):
        (corridas / "lote-07-2026_Q2.json").write_text(json.dumps({"resumen": {
            "resultado": resultado, "filas_salida": filas_salida,
            "por_grupo": {"sobrantes_captura_doble": sobrantes}}}), encoding="utf-8")

    registro(res["filas_salida"], res["sobrantes_captura_doble"])
    correcto, informe = intermedia.verificar("07-2026_Q2", contrato, simular=True,
                                             carpeta=destino, corridas=corridas)
    assert correcto, "\n".join(informe)
    registro(res["filas_salida"], 0)
    correcto, informe = intermedia.verificar("07-2026_Q2", contrato, simular=True,
                                             carpeta=destino, corridas=corridas)
    assert not correcto and any("✗ contra el linaje" in x for x in informe)


# ── PostgreSQL: cómo se conecta ────────────────────────────────────────────

class _ConexionQueAnota:
    """Hace las veces de DuckDB: anota cada sentencia y no se conecta a nada."""

    def __init__(self):
        self.sentencias = []

    def execute(self, sql, *args):
        self.sentencias.append(sql)
        return self


def test_las_variables_de_libpq_se_quedan_despues_de_adjuntar(contrato, monkeypatch):
    """La extensión de PostgreSQL abre conexiones nuevas después del ATTACH, y cada
    una lee las variables de libpq al abrirse. La primera versión las quitaba al
    terminar el ATTACH; en la primera corrida real, la cuenta que sigue a la carga
    abrió otra conexión y buscó el servidor por omisión (`/tmp/.s.PGSQL.5432`).
    Se quedan puestas, y la contraseña sigue sin aparecer en ningún SQL."""
    for variable in ("PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD"):
        monkeypatch.delenv(variable, raising=False)     # al final quedan como estaban
    monkeypatch.setenv("ANALYTICS_DB", "base_de_prueba")
    monkeypatch.setenv("ANALYTICS_USER", "usuario_de_prueba")
    monkeypatch.setenv("ANALYTICS_PASSWORD", "clave-de-prueba")
    monkeypatch.setenv("ANALYTICS_PORT", "5999")
    con = _ConexionQueAnota()
    destino = intermedia.adjuntar_destino(con, contrato, simular=False)
    assert any("ATTACH" in s for s in con.sentencias)
    assert {v: os.environ.get(v) for v in ("PGHOST", "PGPORT", "PGDATABASE", "PGUSER",
                                           "PGPASSWORD")} == {
        "PGHOST": "localhost", "PGPORT": "5999", "PGDATABASE": "base_de_prueba",
        "PGUSER": "usuario_de_prueba", "PGPASSWORD": "clave-de-prueba"}
    assert not any("clave-de-prueba" in s for s in con.sentencias)
    assert "clave-de-prueba" not in json.dumps(destino)


# ── PostgreSQL de verdad · sólo si se pide ─────────────────────────────────

def _otros_lotes_en_postgres(contrato, nombre):
    con = duckdb.connect()
    intermedia.adjuntar_destino(con, contrato, simular=False)
    try:
        return dict(con.execute(
            f"SELECT lote, count(*) FROM destino.{intermedia.ESQUEMA}.{intermedia.TABLA} "
            "WHERE lote <> ? GROUP BY lote", [nombre]).fetchall())
    finally:
        con.execute("DETACH destino")


@pytest.mark.skipif(os.environ.get("CANASTAMX_PRUEBA_POSTGRES") != "1",
                    reason="contra postgres-analytics: CANASTAMX_PRUEBA_POSTGRES=1 y las "
                           "ANALYTICS_* cargadas (la primera vez DuckDB descarga su "
                           "extensión postgres)")
def test_la_carga_a_postgres_reemplaza_la_particion(contrato, columnas, tmp_path):
    """La misma carga, contra la base de verdad. Usa un lote que no existe en la
    fuente (`12-2099_Q1`) para no tocar ninguno real, y lo deja vacío al final.

    La capa se construye con ESE lote. La primera versión la construía con el de por
    omisión de `_construida()`, y su primera corrida contra la base real escribió
    tres filas inventadas en `07-2026_Q2`. Por eso ahora comprueba que los demás
    lotes quedan igual, y `cargar()` se niega a escribir filas de otro lote."""
    nombre = "12-2099_Q1"
    filas = [fila(columnas, producto=f"P{i}", precio=f"{20 + i}.50") for i in range(3)]
    otros = _otros_lotes_en_postgres(contrato, nombre)
    try:
        for _ in range(2):
            r = intermedia.cargar(_construida(contrato, columnas, tmp_path / "a", filas, nombre),
                                  nombre, contrato, simular=False)
        assert r["motor"] == "postgres" and r["borradas"] == 3 and r["en_destino"] == 3
        con = duckdb.connect()
        intermedia.adjuntar_destino(con, contrato, simular=False)
        tipo = con.execute("SELECT * FROM postgres_query('destino', 'SELECT data_type, "
                           "numeric_precision, numeric_scale FROM information_schema.columns "
                           "WHERE table_schema = ''intermedia'' AND column_name = ''precio''')"
                           ).fetchone()
        con.execute("DETACH destino")
        assert tipo == ("numeric", 12, 2)
    finally:
        r = intermedia.cargar(intermedia.capa_vacia(contrato), nombre, contrato, simular=False)
    assert r["en_destino"] == 0
    assert _otros_lotes_en_postgres(contrato, nombre) == otros, "la prueba tocó otro lote"
