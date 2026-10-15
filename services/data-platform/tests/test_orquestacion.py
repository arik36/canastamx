"""Pruebas de `orquestacion/definiciones.py` · los tres activos y el sensor.

Están escritas **contra el criterio de cierre de T043**, frase por frase, y no
contra lo que el código hace. Cada prueba lleva arriba la frase que comprueba:

  «`dagster dev` muestra tres activos, uno particionado por quincena»
  «Materializar la partición 2026-07-Q2 escribe la capa cruda y deja su linaje»
  «hacerlo dos veces da la misma huella (RF-25)»
  «Un lote con filas defectuosas no las promueve»
  «Cambiar `largo_maximo` de una columna en el contrato cambia la compuerta sin
   tocar código»

Hay además una prueba que no sale del criterio sino del diseño, y es la que más
importa de este archivo: que **el umbral de D-07 se evalúa sobre las dos
cuarentenas juntas**. Si se evaluara sólo sobre la de fila, un lote lleno de
colisiones altas pasaría por debajo del 5% y se promovería.
"""

import csv
import sys
from pathlib import Path

import pandas as pd
import pytest

PLATAFORMA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATAFORMA))
sys.path.insert(0, str(PLATAFORMA / "ingestion"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from codigo import codigo_sin_comentarios
from ingesta import columnas_del_contrato, leer_contrato

dagster = pytest.importorskip("dagster", reason="dagster no está instalado")


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
              "latitud": "21.12", "longitud": "-101.68"})
    r.update(kw)
    return r


def escribir_lote(carpeta, nombre, filas, columnas):
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / nombre
    with ruta.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columnas)
        w.writeheader()
        w.writerows(filas)
    return ruta


@pytest.fixture
def entorno(tmp_path, monkeypatch):
    """Recarga el módulo con la carpeta de llegada apuntando al tmp_path.

    Hace falta recargar porque las rutas se leen del entorno al importar: eso es
    deliberado —son cosas de la máquina, no del dato— y obliga a esta gimnasia en
    las pruebas.
    """
    import importlib

    llegada = tmp_path / "lotes"
    llegada.mkdir()
    monkeypatch.setenv("CANASTAMX_LOTES", str(llegada))
    monkeypatch.setenv("CANASTAMX_SIMULAR", "1")
    monkeypatch.setenv("CANASTAMX_FECHA_REFERENCIA", "2026-08-10")
    import orquestacion.definiciones as d
    importlib.reload(d)
    return d, llegada


# ── «tres activos, uno particionado por quincena» ──────────────────────────

def test_hay_tres_activos_y_los_tres_estan_particionados(entorno):
    d, _ = entorno
    repo = d.defs.get_repository_def()
    activos = repo.assets_defs_by_key
    assert len(activos) == 3, f"hay {len(activos)} activos, el criterio pide tres"
    for clave, definicion in activos.items():
        assert definicion.partitions_def is not None, (
            f"{clave.to_user_string()} no está particionado")


def test_las_particiones_son_las_quincenas_y_salen_del_contrato(entorno, contrato):
    """Hoy son 38, y ese 38 **no está escrito**: sale de `alcance.ventana`. Se
    comprueba moviendo la ventana en una copia del contrato."""
    d, _ = entorno
    claves = d.quincenas_del_contrato(contrato)
    assert len(claves) == 38
    assert claves[0] == "2025-01-Q1" and claves[-1] == "2026-07-Q2"

    corta = dict(contrato)
    corta["alcance"] = {**contrato["alcance"],
                        "ventana": {"desde": "2026-01-01", "hasta": "2026-03-31"}}
    assert d.quincenas_del_contrato(corta) == [
        "2026-01-Q1", "2026-01-Q2", "2026-02-Q1", "2026-02-Q2",
        "2026-03-Q1", "2026-03-Q2"], (
        "las particiones no siguieron a la ventana del contrato")


def test_el_sensor_y_el_trabajo_existen(entorno):
    d, _ = entorno
    repo = d.defs.get_repository_def()
    assert [s.name for s in repo.sensor_defs] == ["archivo_nuevo"]
    assert "corrida_del_lote" in [j.name for j in repo.get_all_jobs()]


def test_la_quincena_se_traduce_al_nombre_de_archivo_de_la_fuente(entorno):
    d, _ = entorno
    assert d.nombre_de_lote("2026-07-Q2") == "07-2026_Q2"
    assert d.nombre_de_lote("2025-01-Q1") == "01-2025_Q1"


# ── «materializar la partición … y hacerlo dos veces da la misma huella» ───

def test_materializar_la_particion_corre_los_tres_activos(entorno, columnas):
    d, llegada = entorno
    escribir_lote(llegada, "07-2026_Q2.csv",
                  [fila(columnas, producto=f"P{i}", direccion=f"C{i}")
                   for i in range(10)], columnas)

    r = dagster.materialize([d.capa_cruda, d.filas_revisadas, d.lote_promovido],
                            partition_key="2026-07-Q2")
    assert r.success
    for nombre in ("capa_cruda", "filas_revisadas", "lote_promovido"):
        assert r.asset_materializations_for_node(nombre), (
            f"{nombre} no dejó materialización, así que no dejó linaje")


def test_materializar_dos_veces_da_la_misma_huella(entorno, columnas):
    """RF-25 · reprocesar un lote es re-materializar su partición, y tiene que dar
    lo mismo. La huella son el sha256 de la entrada y las cifras que `ingesta.py`
    declara estables; la duración queda fuera a propósito, porque esa cambia
    siempre."""
    d, llegada = entorno
    escribir_lote(llegada, "07-2026_Q2.csv",
                  [fila(columnas, producto=f"P{i}") for i in range(5)], columnas)

    def huella():
        r = dagster.materialize([d.capa_cruda], partition_key="2026-07-Q2")
        assert r.success
        md = r.asset_materializations_for_node("capa_cruda")[0].metadata
        return md["huella"].value

    primera, segunda = huella(), huella()
    assert primera == segunda, "la misma partición dio dos huellas distintas"


def test_cambiar_el_archivo_cambia_la_huella(entorno, columnas):
    """La otra mitad de RF-25: si la huella no cambiara al cambiar la entrada, no
    estaría midiendo nada."""
    d, llegada = entorno

    def huella():
        r = dagster.materialize([d.capa_cruda], partition_key="2026-07-Q2")
        md = r.asset_materializations_for_node("capa_cruda")[0].metadata
        return md["huella"].value

    escribir_lote(llegada, "07-2026_Q2.csv",
                  [fila(columnas, producto="A")], columnas)
    primera = huella()
    escribir_lote(llegada, "07-2026_Q2.csv",
                  [fila(columnas, producto="B")], columnas)
    assert huella() != primera


def test_si_no_hay_archivo_para_la_particion_lo_dice_claro(entorno):
    d, _ = entorno
    r = dagster.materialize([d.capa_cruda], partition_key="2025-03-Q1",
                            raise_on_error=False)
    assert not r.success


# ── «un lote con filas defectuosas no las promueve» ───────────────────────

def test_las_filas_defectuosas_no_se_promueven_y_quedan_con_su_motivo(
        entorno, columnas):
    d, llegada = entorno
    filas = [fila(columnas, producto=f"P{i}", direccion=f"C{i}") for i in range(40)]
    filas.append(fila(columnas, producto="", direccion="sin producto"))
    filas.append(fila(columnas, producto="L" * 80))
    escribir_lote(llegada, "07-2026_Q2.csv", filas, columnas)

    r = dagster.materialize([d.capa_cruda, d.filas_revisadas, d.lote_promovido],
                            partition_key="2026-07-Q2")
    assert r.success
    md = r.asset_materializations_for_node("filas_revisadas")[0].metadata
    assert md["filas_en_cuarentena"].value == 2
    assert md["filas_salida"].value == 40
    motivos = md["por_motivo"].value
    assert set(motivos) == {"valor_requerido_vacio", "largo_excedido"}, (
        "la cuarentena no guardó un motivo por fila")


def test_el_umbral_de_d07_cuenta_las_dos_cuarentenas_juntas(entorno, columnas):
    """**La prueba que justifica el orden de los activos.**

    100 filas: 2 con defecto de fila (2%) y 4 en dos colisiones altas (4%). Por
    separado ninguna pasa del 5% de D-07; juntas son el 6% y el lote se detiene.
    Si esta prueba dice PASO, el umbral se está evaluando antes de las reglas de
    grupo y un lote lleno de colisiones se promovería.
    """
    d, llegada = entorno
    filas = [fila(columnas, producto=f"P{i}", direccion=f"C{i}") for i in range(94)]
    filas += [fila(columnas, producto="", direccion="sin producto 1"),
              fila(columnas, producto="", direccion="sin producto 2")]
    filas += [fila(columnas, producto="Aceite", direccion="Centro", precio="40.00"),
              fila(columnas, producto="Aceite", direccion="Centro", precio="200.00"),
              fila(columnas, producto="Atun", direccion="Norte", precio="30.00"),
              fila(columnas, producto="Atun", direccion="Norte", precio="150.00")]
    assert len(filas) == 100
    escribir_lote(llegada, "07-2026_Q2.csv", filas, columnas)

    r = dagster.materialize([d.capa_cruda, d.filas_revisadas, d.lote_promovido],
                            partition_key="2026-07-Q2")
    assert r.success

    por_fila = r.asset_materializations_for_node("filas_revisadas")[0].metadata
    assert por_fila["filas_en_cuarentena"].value == 2, "2 de 100 es el 2%"

    md = r.asset_materializations_for_node("lote_promovido")[0].metadata
    assert md["grupos_en_colision"].value == 2
    assert md["proporcion_en_cuarentena"].value == pytest.approx(0.06)
    assert md["resultado"].value == "DETENIDO", (
        "el lote se promovió con el 6% en cuarentena: el umbral se evaluó antes "
        "de las reglas de grupo")
    assert md["filas_salida"].value == 0, (
        "D-07 dice que no se promueve ni la parte que pasó")


def test_un_lote_limpio_se_promueve(entorno, columnas):
    d, llegada = entorno
    escribir_lote(llegada, "07-2026_Q2.csv",
                  [fila(columnas, producto=f"P{i}", direccion=f"C{i}")
                   for i in range(20)], columnas)
    r = dagster.materialize([d.capa_cruda, d.filas_revisadas, d.lote_promovido],
                            partition_key="2026-07-Q2")
    md = r.asset_materializations_for_node("lote_promovido")[0].metadata
    assert md["resultado"].value == "PASO"
    assert md["filas_salida"].value == 20


def test_la_frescura_viaja_en_el_linaje_del_lote(entorno, columnas):
    """La consola la lee de ahí para escribir «no aplica», que es lo que pide
    `diseno.md` §7 · 3."""
    d, llegada = entorno
    escribir_lote(llegada, "07-2026_Q2.csv",
                  [fila(columnas, producto="P", fecha_registro="2026/07/31")],
                  columnas)
    r = dagster.materialize([d.capa_cruda, d.filas_revisadas, d.lote_promovido],
                            partition_key="2026-07-Q2")
    frescura = r.asset_materializations_for_node(
        "lote_promovido")[0].metadata["frescura"].value
    assert frescura["aplica"] is False
    assert "corpus_congelado" in frescura["razon"]
    assert frescura["dias"] == 10, "la fecha de referencia de la corrida no se usó"


# ── «cambiar el contrato cambia la compuerta sin tocar código» ─────────────

def test_cambiar_largo_maximo_en_el_contrato_cambia_lo_que_se_aparta(
        entorno, columnas, tmp_path, monkeypatch):
    """La frase literal del criterio. Se cambia el contrato en una copia y se mira
    que la misma fila pase de limpia a cuarentena."""
    import compuerta

    contrato = leer_contrato()
    larga = fila(columnas, producto="P" * 40)
    df = pd.DataFrame([larga], columns=columnas, dtype="string")

    _, _, antes = compuerta.revisar_lote(df, contrato, "07-2026_Q2.csv")
    assert antes["filas_en_cuarentena"] == 0, "40 caracteres caben en 65"

    recortado = dict(contrato)
    recortado["columnas"] = {**contrato["columnas"],
                             "producto": {**contrato["columnas"]["producto"],
                                          "largo_maximo": 10}}
    _, _, despues = compuerta.revisar_lote(df, recortado, "07-2026_Q2.csv")
    assert despues["por_motivo"] == {"largo_excedido": 1}, (
        "bajar largo_maximo a 10 en el contrato no cambió la compuerta")


# ── El sensor ──────────────────────────────────────────────────────────────

def test_el_sensor_dispara_al_aparecer_un_archivo_y_anota_el_instante(
        entorno, columnas):
    """El disparo es el cero de H2 (SLA-D-05), así que la marca de tiempo tiene que
    quedar escrita al disparar, no después."""
    d, llegada = entorno
    escribir_lote(llegada, "07-2026_Q2.csv",
                  [fila(columnas, producto="P")], columnas)

    ctx = dagster.build_sensor_context()
    r = d.archivo_nuevo(ctx)
    assert isinstance(r, dagster.SensorResult)
    assert len(r.run_requests) == 1
    peticion = r.run_requests[0]
    assert peticion.partition_key == "2026-07-Q2"
    assert peticion.tags["canastamx/disparo"], "el disparo no trae instante"
    assert peticion.tags["canastamx/lote"] == "07-2026_Q2"


def test_el_sensor_no_vuelve_a_disparar_el_mismo_archivo(entorno, columnas):
    """Sin esto el sensor relanzaría la misma corrida cada 30 segundos."""
    d, llegada = entorno
    escribir_lote(llegada, "07-2026_Q2.csv",
                  [fila(columnas, producto="P")], columnas)

    primera = d.archivo_nuevo(dagster.build_sensor_context())
    segunda = d.archivo_nuevo(dagster.build_sensor_context(cursor=primera.cursor))
    assert isinstance(segunda, dagster.SkipReason)


def test_el_sensor_vuelve_a_disparar_si_el_archivo_cambio(entorno, columnas):
    d, llegada = entorno
    escribir_lote(llegada, "07-2026_Q2.csv",
                  [fila(columnas, producto="P")], columnas)
    primera = d.archivo_nuevo(dagster.build_sensor_context())

    import os
    import time
    ruta = llegada / "07-2026_Q2.csv"
    escribir_lote(llegada, "07-2026_Q2.csv",
                  [fila(columnas, producto="P"), fila(columnas, producto="Q")],
                  columnas)
    os.utime(ruta, (time.time() + 5, time.time() + 5))

    segunda = d.archivo_nuevo(dagster.build_sensor_context(cursor=primera.cursor))
    assert isinstance(segunda, dagster.SensorResult)
    assert len(segunda.run_requests) == 1


def test_el_sensor_se_salta_sin_carpeta_en_lugar_de_reventar(tmp_path, monkeypatch):
    import importlib

    monkeypatch.setenv("CANASTAMX_LOTES", str(tmp_path / "no-existe"))
    import orquestacion.definiciones as d
    importlib.reload(d)
    r = d.archivo_nuevo(dagster.build_sensor_context())
    assert isinstance(r, dagster.SkipReason)


# ── Que la orquestación siga siendo delgada (ADR 016 · fecha de salida) ────

def test_la_orquestacion_no_tiene_ninguna_regla_del_contrato():
    """ADR 016 le puso a Dagster fecha de salida el 25 de octubre. Para que irse
    cueste poco, en `orquestacion/` no puede vivir ninguna cifra del contrato: las
    reglas están en `compuerta.py` y `lote.py`, que no saben que Dagster existe."""
    contrato = leer_contrato()
    # Sin comentarios ni textos: un comentario que explica una cifra es
    # documentación, no una regla. Ver tests/codigo.py.
    cuerpo = codigo_sin_comentarios(PLATAFORMA / "orquestacion" / "definiciones.py")
    cifras = {
        "el umbral de D-07": contrato["promocion_del_lote"]["rechazo_maximo"],
        "el umbral de la colisión":
            contrato["clave_de_fila"]["colision_precio_alta"]["mas_de"],
        "los días del bloqueo de frescura": contrato["frescura"]["bloquea_dias"],
        "las 38 quincenas": 38,
    }
    for que, valor in cifras.items():
        assert str(valor) not in cuerpo, (
            f"{que} ({valor}) está escrito en orquestacion/definiciones.py")


def test_las_compuertas_no_importan_dagster():
    """La prueba de que la fecha de salida del ADR 016 es ejecutable: si Dagster se
    va, estos dos archivos siguen corriendo."""
    for nombre in ("compuerta.py", "lote.py"):
        texto = codigo_sin_comentarios(PLATAFORMA / "ingestion" / nombre)
        assert "dagster" not in texto.lower(), (
            f"{nombre} menciona dagster; entonces irse de Dagster costaría "
            "reescribir las compuertas")
