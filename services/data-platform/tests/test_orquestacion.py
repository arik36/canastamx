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


def test_la_quincena_se_traduce_a_LAS_DOS_formas_que_usa_la_fuente(entorno):
    """Los 24 archivos de 2025 se llaman `01-2025_01`; los 14 de 2026,
    `01-2026_Q1`. Están los 38 con su sha256 en
    `docs/datos/ingesta-capa-cruda.md`. Generar sólo la forma con `Q` dejaba 24
    de las 38 particiones sin encontrar su archivo."""
    d, _ = entorno
    assert d.nombres_de_lote("2026-07-Q2") == ["07-2026_Q2", "07-2026_02"]
    assert d.nombres_de_lote("2025-01-Q1") == ["01-2025_Q1", "01-2025_01"]


def test_encuentra_el_archivo_con_el_nombre_de_2025(entorno, columnas):
    """La prueba que faltaba. Con el nombre que de verdad traen los 24 archivos de
    2025, la partición tiene que encontrar su archivo."""
    d, llegada = entorno
    escribir_lote(llegada, "03-2025_02.csv",
                  [fila(columnas, producto="P")], columnas)
    ruta = d.archivo_del_lote("2025-03-Q2")
    assert ruta is not None, "no encontró 03-2025_02.csv para la quincena 2025-03-Q2"
    assert ruta.name == "03-2025_02.csv"
    # Y el nombre del lote queda con la forma del archivo que sí está, para que el
    # registro de la corrida diga el mismo nombre que el archivo.
    assert d.nombre_de_lote("2025-03-Q2") == "03-2025_02"


def test_encuentra_el_archivo_con_el_nombre_de_2026(entorno, columnas):
    d, llegada = entorno
    escribir_lote(llegada, "07-2026_Q2.csv",
                  [fila(columnas, producto="P")], columnas)
    ruta = d.archivo_del_lote("2026-07-Q2")
    assert ruta is not None and ruta.name == "07-2026_Q2.csv"
    assert d.nombre_de_lote("2026-07-Q2") == "07-2026_Q2"


def test_el_inverso_cuadra_con_como_ingesta_lee_el_nombre(entorno):
    """La comprobación cruzada que importa: para las 38 quincenas, al menos uno de
    los nombres que genera este envoltorio tiene que ser un nombre que
    `ingesta.quincena_del_lote()` sepa leer, y tiene que devolver la misma
    quincena. Si alguien cambia uno de los dos lados, esto lo dice."""
    from ingesta import quincena_del_lote

    d, _ = entorno
    for quincena in d.quincenas_del_contrato():
        leidas = {quincena_del_lote(n) for n in d.nombres_de_lote(quincena)}
        assert leidas == {quincena}, (
            f"para {quincena} el envoltorio genera nombres que ingesta.py lee "
            f"como {leidas}")


def test_materializar_una_particion_de_2025_tambien_corre(entorno, columnas):
    """La mitad del corpus es de 2025. Si esto falla, 24 de los 38 lotes no se
    pueden procesar, que es justo lo que pasaba."""
    d, llegada = entorno
    escribir_lote(llegada, "11-2025_01.csv",
                  [fila(columnas, producto=f"P{i}", direccion=f"C{i}",
                        fecha_registro="2025/11/10") for i in range(5)], columnas)
    r = dagster.materialize([d.capa_cruda, d.filas_revisadas, d.lote_promovido],
                            partition_key="2025-11-Q1")
    assert r.success
    md = r.asset_materializations_for_node("capa_cruda")[0].metadata
    assert md["archivo"].value.endswith("11-2025_01.csv")


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


# ── Con un lote con la forma del corpus: parquet, y casi todo fuera del alcance ─

def _parquet_mezclado(llegada, columnas, nombre="07-2026_Q2.parquet"):
    """20 filas del alcance limpias, y 140 de Nuevo León —fuera del alcance— de
    las que 30 vienen con defecto. Si la compuerta revisara el archivo entero,
    esas 30 la harían detener el lote."""
    from lotes import escribir_parquet

    filas = [fila(columnas, producto=f"D{i}", direccion=f"C{i}") for i in range(20)]
    filas += [fila(columnas, estado="Nuevo León", producto=f"F{i}", direccion=f"N{i}")
              for i in range(110)]
    filas += [fila(columnas, estado="Nuevo León", producto="L" * 90, direccion=f"M{i}")
              for i in range(30)]
    return escribir_parquet(llegada / nombre, filas, columnas)


def test_el_activo_juzga_el_alcance_y_no_el_archivo(entorno, columnas):
    """**La prueba que habría detenido la primera corrida real.** Las 30 filas
    defectuosas son de Nuevo León, que no es del alcance. Sobre el archivo entero
    serían 30 de 160, el 18.75%, y el lote se detendría. Sobre el alcance son 0
    de 20, y el lote pasa. Ésa es la diferencia entre medir el 5% de D-07 sobre la
    población del contrato o sobre otra."""
    d, llegada = entorno
    _parquet_mezclado(llegada, columnas)

    r = dagster.materialize([d.capa_cruda, d.filas_revisadas, d.lote_promovido],
                            partition_key="2026-07-Q2")
    assert r.success
    revisadas = r.asset_materializations_for_node("filas_revisadas")[0].metadata
    assert revisadas["filas_entrada"].value == 20, (
        f"la compuerta revisó {revisadas['filas_entrada'].value} filas; "
        "el alcance son 20")
    promovido = r.asset_materializations_for_node("lote_promovido")[0].metadata
    assert promovido["resultado"].value == "PASO", (
        "el lote se detuvo por filas que no son del alcance")
    assert promovido["filas_salida"].value == 20


def test_el_activo_lee_parquet_sin_pyarrow(entorno, columnas):
    """Los 38 archivos del corpus son parquet, y en el CI pyarrow no está instalado:
    la partición tiene que materializarse igual.

    **Se corre en un intérprete aparte, y la razón es la lección de esta prueba.**
    La primera versión bloqueaba pyarrow con `monkeypatch` dentro de pytest, y en
    una máquina que SÍ tiene pyarrow eso deja un estado que no existe en ningún
    lado: pandas ya había cargado con pyarrow —sus columnas de texto son
    `ArrowStringArray`— y después pyarrow deja de poder importarse. Dagster guarda
    el marco entre activos con pickle, pickle necesita `pyarrow.lib` para guardar
    esas columnas, y truena. Falló así en la máquina de A el 15 de octubre, con
    83 de 84 pasando.

    El código estaba bien; la prueba simulaba mal. Las dos situaciones reales
    funcionan: con pyarrow instalado pickle lo importa sin problema, y sin pyarrow
    pandas usa columnas de Python desde el principio. Para simular la segunda hay
    que bloquear pyarrow ANTES de que pandas cargue, y eso sólo se puede en un
    intérprete nuevo.
    """
    import subprocess
    import textwrap

    _parquet_mezclado(entorno[1], columnas)
    codigo = textwrap.dedent(f"""
        import sys
        sys.modules["pyarrow"] = None          # ANTES de pandas: como en el CI
        sys.modules["fastparquet"] = None
        sys.path.insert(0, {str(PLATAFORMA)!r})
        sys.path.insert(0, {str(PLATAFORMA / "ingestion")!r})
        import pandas as pd
        from dagster import materialize
        from orquestacion.definiciones import (
            capa_cruda, filas_revisadas, lote_promovido)
        r = materialize([capa_cruda, filas_revisadas, lote_promovido],
                        partition_key="2026-07-Q2")
        md = r.asset_materializations_for_node("filas_revisadas")[0].metadata
        texto = pd.Series(["x"]).array
        print("RESULTADO", r.success, md["filas_entrada"].value,
              type(texto).__name__)
    """)
    # El entorno ya trae CANASTAMX_LOTES y los demás: los puso la fixture.
    hecho = subprocess.run([sys.executable, "-c", codigo], capture_output=True,
                           text=True, check=False)
    ultima = [linea for linea in hecho.stdout.splitlines()
              if linea.startswith("RESULTADO")]
    assert ultima, hecho.stderr[-3000:]
    _, exito, filas, arreglo = ultima[-1].split()
    assert exito == "True", hecho.stderr[-3000:]
    assert filas == "20", f"revisó {filas} filas; el alcance son 20"
    assert "Arrow" not in arreglo, (
        f"pandas usó {arreglo}: el bloqueo llegó tarde y la prueba no simula el CI")


def test_un_parquet_de_2025_tambien(entorno, columnas):
    """Los dos errores juntos: el nombre de 2025 (#169) y el parquet."""
    d, llegada = entorno
    from lotes import escribir_parquet

    escribir_parquet(llegada / "11-2025_01.parquet",
                     [fila(columnas, producto=f"P{i}", direccion=f"C{i}",
                           fecha_registro="2025/11/10") for i in range(8)], columnas)
    r = dagster.materialize([d.capa_cruda, d.filas_revisadas, d.lote_promovido],
                            partition_key="2025-11-Q1")
    assert r.success
    md = r.asset_materializations_for_node("filas_revisadas")[0].metadata
    assert md["filas_entrada"].value == 8


def test_los_tres_cubos_viajan_en_el_linaje_del_lote(entorno, columnas):
    """Son la cifra que el contrato 1.3.3 pidió volver a medir en la primera
    corrida, y contra la que se compara la deduplicación de la semana del 19."""
    d, llegada = entorno
    escribir_lote(llegada, "07-2026_Q2.csv", [
        fila(columnas, producto="Frijol", precio="30.00"),
        fila(columnas, producto="Frijol", precio="30.50"),
        fila(columnas, producto="Arroz", precio="20.00"),
        fila(columnas, producto="Arroz", precio="37.00"),
    ] + [fila(columnas, producto=f"P{i}", direccion=f"C{i}") for i in range(40)],
        columnas)
    r = dagster.materialize([d.capa_cruda, d.filas_revisadas, d.lote_promovido],
                            partition_key="2026-07-Q2")
    cubos = r.asset_materializations_for_node(
        "lote_promovido")[0].metadata["cubos_de_la_clave"].value
    assert cubos["captura_doble"] == {"grupos": 1, "sobrantes": 1}
    assert cubos["observaciones_multiples"] == {"grupos": 1, "sobrantes": 1}
    assert cubos["en_colision"] == {"grupos": 0, "sobrantes": 0}


def test_ninguna_lectura_de_lotes_pasa_por_pandas():
    """La guardia de fondo: ni las compuertas ni la orquestación leen el lote con
    pandas. Si alguien lo vuelve a hacer, el parquet vuelve a necesitar pyarrow y
    la población vuelve a ser el archivo entero.

    `lote.py` se agregó el 15 de octubre: su línea de comandos seguía leyendo el
    archivo entero con pandas después del #170, porque esta guardia no la miraba."""
    for ruta in (PLATAFORMA / "ingestion" / "compuerta.py",
                 PLATAFORMA / "ingestion" / "lote.py",
                 PLATAFORMA / "orquestacion" / "definiciones.py"):
        codigo = codigo_sin_comentarios(ruta)
        assert "read_parquet" not in codigo and "read_csv" not in codigo, (
            f"{ruta.name} lee el lote con pandas; tiene que ser con "
            "compuerta.leer_alcance()")
