"""
Pruebas de la compuerta de calidad contra el contrato · T043.

No necesitan MinIO, ni Dagster, ni los datos del corpus: arman lotes chicos a
mano y le pasan el contrato a la compuerta como diccionario, así que una prueba
puede modificarlo sin tocar el archivo del repositorio.

    python -m pytest services/data-platform/tests -q
"""
import copy
import json
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

INGESTION = Path(__file__).resolve().parents[1] / "ingestion"
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(INGESTION))

from compuerta import (
    MOTIVOS,
    NOMBRE_COMPUERTA,
    decidir_promocion,
    huella,
    motivos_que_el_contrato_no_declara,
    revisar_lote,
)

CONTRATO = yaml.safe_load((RAIZ / "contracts" / "qqp-v1.yaml").read_text(encoding="utf-8"))
COLUMNAS = list(CONTRATO["columnas"])
ESQUEMA_SQL = (RAIZ / "docs" / "datos" / "esquema-de-operacion.sql").read_text(encoding="utf-8")


@pytest.fixture
def contrato():
    """Una copia, para que una prueba pueda cambiarlo sin afectar a las demás."""
    return copy.deepcopy(CONTRATO)


def fila(**cambios):
    v = {"producto": "Frijol", "presentacion": "Bolsa 1 Kg", "marca": "S/m",
         "categoria": "legumbres", "cadena_comercial": "Soriana", "giro": "Supermercado",
         "nombre_comercial": "Soriana Centro", "direccion": "Av. Juarez 100",
         "estado": "Guanajuato", "municipio": "Leon", "catalogo": "Basicos",
         "fecha_registro": "2025/01/10", "latitud": "21.1", "longitud": "-101.6",
         "precio": "32.50"}
    v.update(cambios)
    return v


def lote(*filas):
    return pd.DataFrame([fila(**f) for f in filas], columns=COLUMNAS).astype("string")


def motivos_de(registros):
    return sorted(r["motivo"] for r in registros)


# ── Los cinco motivos de fila ──────────────────────────────────────────────

@pytest.mark.parametrize("cambio,motivo", [
    ({"producto": ""},                      "valor_requerido_vacio"),
    ({"presentacion": "X" * 181},           "largo_excedido"),
    ({"precio": "no-es-un-numero"},         "tipo_invalido"),
    ({"fecha_registro": "2024/01/01"},      "fecha_fuera_de_ventana"),
    ({"precio": "5000.00"},                 "precio_fuera_de_rango"),
])
def test_cada_regla_del_contrato_da_su_motivo(contrato, cambio, motivo):
    _, cuarentena, resumen = revisar_lote(lote({}, cambio), contrato)
    assert motivos_de(cuarentena) == [motivo]
    assert resumen["filas_en_cuarentena"] == 1
    assert resumen["filas_salida"] == 1          # la fila buena sigue su camino


def test_un_valor_requerido_vacio_se_detecta_sea_nulo_o_en_blanco(contrato):
    """El contrato dice «la celda no puede venir vacía». En un CSV eso llega
    como cadena vacía y desde la capa cruda como nulo: los dos son el mismo
    defecto y tienen que dar el mismo motivo."""
    df = lote({"producto": ""}, {"producto": None})
    _, cuarentena, resumen = revisar_lote(df, contrato)
    assert motivos_de(cuarentena) == ["valor_requerido_vacio"] * 2
    assert resumen["filas_en_cuarentena"] == 2


def test_latitud_vacia_no_es_defecto(contrato):
    """`valor_requerido: false`, medido: 0.0086% viene vacío (perfilado §1)."""
    _, cuarentena, resumen = revisar_lote(lote({"latitud": "", "longitud": ""}), contrato)
    assert cuarentena == []
    assert resumen["filas_en_cuarentena"] == 0


def test_el_techo_del_precio_es_el_de_su_catalogo(contrato):
    """1000 en BASICOS y 400 en PACIC: el mismo precio pasa en uno y no en otro."""
    df = lote({"catalogo": "Basicos", "precio": "900.00"},
              {"catalogo": "PACIC",   "precio": "900.00"})
    _, cuarentena, resumen = revisar_lote(df, contrato)
    assert motivos_de(cuarentena) == ["precio_fuera_de_rango"]
    assert resumen["filas_en_cuarentena"] == 1


# ── Una fila puede llevar varios motivos ───────────────────────────────────

def test_una_fila_con_dos_defectos_deja_dos_registros_y_cuenta_una_vez(contrato):
    """`cuarentena` tiene UNIQUE (corrida_id, huella_fila, motivo): la misma fila
    admite motivos distintos. El umbral del 5%, en cambio, cuenta FILAS."""
    _, cuarentena, resumen = revisar_lote(lote({"marca": "", "precio": "9999.00"}), contrato)
    assert motivos_de(cuarentena) == ["precio_fuera_de_rango", "valor_requerido_vacio"]
    assert len({r["huella_fila"] for r in cuarentena}) == 1
    assert resumen["filas_en_cuarentena"] == 1
    assert resumen["registros_de_cuarentena"] == 2


# ── La regla de lote · D-07 ────────────────────────────────────────────────

def test_por_debajo_del_umbral_el_lote_pasa_con_aviso(contrato):
    df = lote(*([{}] * 39 + [{"precio": "5000.00"}]))
    _, _, resumen = revisar_lote(df, contrato)
    resumen = decidir_promocion(resumen, contrato)
    assert resumen["proporcion_en_cuarentena"] == 0.025
    assert resumen["resultado"] == "AVISO"
    assert resumen["filas_salida"] == 39


def test_por_encima_del_umbral_no_se_promueve_ni_lo_que_paso(contrato):
    """«Un lote así no está casi bien»: se detiene completo (D-07)."""
    df = lote(*([{}] * 10 + [{"precio": "5000.00"}] * 2))
    _, _, resumen = revisar_lote(df, contrato)
    resumen = decidir_promocion(resumen, contrato)
    assert resumen["resultado"] == "DETENIDO"
    assert resumen["motivo_lote"] == "rechazo_mayor_al_umbral"
    assert resumen["filas_salida"] == 0

def test_el_umbral_sale_del_contrato(contrato):
    """Si D-07 cambia el 5% en el contrato, la decisión cambia con él."""
    df = lote(*([{}] * 10 + [{"precio": "5000.00"}] * 2))   # 16.7%
    contrato["promocion_del_lote"]["rechazo_maximo"] = 0.5
    _, _, resumen = revisar_lote(df, contrato)
    assert decidir_promocion(resumen, contrato)["resultado"] == "AVISO"


# ── Lo que hace que todo esto valga: el esquema sale del contrato ──────────

def test_cambiar_el_contrato_cambia_la_compuerta_sin_tocar_codigo(contrato):
    """La prueba de la afirmación central del módulo.

    Un lote que pasa limpio empieza a quedar en cuarentena sólo porque el
    contrato cambió `largo_maximo`. Si alguna vez esta prueba falla, es que
    alguien escribió una regla en el código.
    """
    df = lote({}, {}, {})
    _, cuarentena, _ = revisar_lote(df, contrato)
    assert cuarentena == []

    contrato["columnas"]["presentacion"]["largo_maximo"] = 5
    _, cuarentena, resumen = revisar_lote(df, contrato)
    assert motivos_de(cuarentena) == ["largo_excedido"] * 3
    assert resumen["filas_en_cuarentena"] == 3


def test_ninguna_cifra_del_contrato_esta_escrita_en_el_codigo():
    """Los largos y los techos viven en el YAML. Si aparecen en el .py, son una
    segunda copia, que es justo la falla que este proyecto estudia."""
    codigo = (INGESTION / "compuerta.py").read_text(encoding="utf-8")
    codigo = re.sub(r'^\s*#.*$', '', codigo, flags=re.MULTILINE)   # sin comentarios
    codigo = re.sub(r'""".*?"""', '', codigo, flags=re.DOTALL)     # sin docstrings
    cifras = {str(c["largo_maximo"]) for c in CONTRATO["columnas"].values()
              if isinstance(c, dict) and c.get("largo_maximo")}
    cifras |= {str(v) for v in CONTRATO["columnas"]["precio"]["maximo_por_catalogo"].values()}
    escritas = sorted(c for c in cifras if re.search(rf"\b{c}\b", codigo))
    assert escritas == [], f"cifras del contrato escritas en el código: {escritas}"


# ── Acuerdo con el esquema de operación ────────────────────────────────────

@pytest.mark.parametrize("motivo", sorted(MOTIVOS))
def test_cada_motivo_existe_en_el_catalogo_con_nivel_fila(motivo):
    """El catálogo vive en `esquema-de-operacion.sql`. Si allá renombran un
    motivo, esta prueba truena aquí en vez de dejar la cuarentena con un código
    que la llave foránea va a rechazar el día que exista la base."""
    fila_sql = re.search(rf"\('{motivo}',\s*'(\w+)',\s*'(\w+)'", ESQUEMA_SQL)
    assert fila_sql, f"{motivo} no está en el catálogo de esquema-de-operacion.sql"
    assert fila_sql.group(1) == "FILA"
    assert fila_sql.group(2) == "CUARENTENA"


def test_ningun_motivo_queda_sin_declarar_y_el_catalogo_lo_dice():
    """Era el pendiente del 9 de noviembre, y lo cerró la 1.3.5: la compuerta no
    emite ningún motivo que el contrato no declare como dato, y el catálogo del
    esquema ya no marca ninguno de nivel FILA con `en_contrato = false`."""
    assert motivos_que_el_contrato_no_declara() == []
    sin_declarar = re.findall(r"\('(\w+)',\s*'FILA',[^)]*?,\s*false,", ESQUEMA_SQL)
    assert sin_declarar == []


# ── Los motivos de fila, en los tres lugares que los nombran (1.3.5) ───────

ANALITICA = (RAIZ / "docs" / "analisis" / "openapi" / "analitica.yaml").read_text(
    encoding="utf-8")


def _catalogo_sql_de_fila():
    """{codigo: regla} de las filas del catálogo con nivel FILA."""
    return dict(re.findall(
        r"\('(\w+)',\s*'FILA',\s*'\w+',\s*'([^']+)'", ESQUEMA_SQL))


def test_los_motivos_de_fila_son_los_mismos_en_contrato_esquema_e_interfaz():
    """**La prueba que justifica la 1.3.5.** Tres documentos nombran los motivos
    de cuarentena: el contrato, el catálogo del esquema de operación y el `enum`
    `MotivoDeCuarentena` de la interfaz analítica. Si se separan, la consola
    filtra por un motivo que la compuerta no emite, o la base rechaza uno que sí
    emite. Es la falla que este proyecto estudia, aplicada a sus propios papeles.
    """
    del_contrato = CONTRATO["motivos_de_fila"]
    del_esquema = _catalogo_sql_de_fila()
    enum = re.search(r"MotivoDeCuarentena:.*?enum:\s*\[([^\]]+)\]", ANALITICA, re.DOTALL)
    assert enum, "no encontré el enum MotivoDeCuarentena en analitica.yaml"
    de_la_interfaz = {m.strip() for m in enum.group(1).split(",")}

    assert set(del_contrato) == set(del_esquema) == de_la_interfaz
    assert del_contrato == del_esquema, (
        "mismos motivos, distinta regla: "
        + str({m: (del_contrato[m], del_esquema[m]) for m in del_contrato
               if del_contrato[m] != del_esquema[m]}))


def test_la_regla_de_cada_motivo_existe_en_el_contrato():
    """Una regla que no existe es un nombre que apunta al vacío. `*` quiere decir
    «alguna columna»: basta con que una la declare."""
    for motivo, regla in CONTRATO["motivos_de_fila"].items():
        pasos, nodos = regla.split("."), [CONTRATO]
        for paso in pasos:
            siguientes = []
            for nodo in nodos:
                if not isinstance(nodo, dict):
                    continue
                if paso == "*":
                    siguientes += list(nodo.values())
                elif paso in nodo:
                    siguientes.append(nodo[paso])
            nodos = siguientes
        assert nodos, f"{motivo} dice venir de `{regla}`, y el contrato no la trae"


def test_cada_motivo_de_la_compuerta_esta_en_el_contrato_con_la_misma_regla():
    for motivo, regla in MOTIVOS.items():
        assert CONTRATO["motivos_de_fila"].get(motivo) == regla, motivo


def test_un_comentario_ya_no_cuenta_como_declaracion(contrato):
    """Hasta la 1.3.4 la función buscaba sobre el texto del contrato, y dos
    motivos «estaban» porque los nombraba un comentario. Sin el catálogo como
    dato, ahora los cinco faltan, aunque el texto siga mencionándolos."""
    sin_catalogo = {k: v for k, v in contrato.items() if k != "motivos_de_fila"}
    assert set(motivos_que_el_contrato_no_declara(sin_catalogo)) == set(MOTIVOS)


def test_una_regla_cambiada_tambien_es_no_declarar(contrato):
    contrato["motivos_de_fila"]["largo_excedido"] = "columnas.*.otra_cosa"
    assert motivos_que_el_contrato_no_declara(contrato) == ["largo_excedido"]


def test_el_registro_de_cuarentena_tiene_la_forma_de_la_tabla(contrato):
    _, cuarentena, _ = revisar_lote(lote({"producto": ""}), contrato)
    r = cuarentena[0]
    assert set(r) == {"motivo", "nivel", "compuerta", "huella_fila", "grupo", "fila"}
    assert r["nivel"] == "FILA"
    assert r["compuerta"] == NOMBRE_COMPUERTA
    assert len(r["huella_fila"]) == 64        # char(64) en la tabla
    assert set(r["fila"]) == set(COLUMNAS)    # la fila tal como llegó
    assert r["grupo"] is None                 # sólo colision_precio_alta lleva grupo


def test_la_huella_es_estable_y_distingue_filas():
    a, b = fila(), fila(precio="99.00")
    assert huella(a, COLUMNAS) == huella(dict(a), COLUMNAS)
    assert huella(a, COLUMNAS) != huella(b, COLUMNAS)


# ── Nivel LOTE: le falta una columna al archivo (CU-02 · 2b) ───────────────

def test_si_falta_una_columna_el_lote_se_detiene_sin_revisar_filas(contrato):
    df = lote({}, {}).drop(columns=["precio"])
    limpias, cuarentena, resumen = revisar_lote(df, contrato)
    assert limpias is None and cuarentena is None
    assert resumen["motivo_lote"] == "columna_requerida_faltante"
    assert resumen["columnas_faltantes"] == ["precio"]


# ── La línea de comandos, como la usa quien corre el lote ──────────────────

def test_la_linea_de_comandos_escribe_las_dos_salidas(tmp_path, contrato):
    csv = tmp_path / "07-2026_Q2.csv"
    filas = [fila()] * 39 + [fila(precio="5000.00")]
    csv.write_text(",".join(COLUMNAS) + "\n"
                   + "\n".join(",".join(str(f[c]) for c in COLUMNAS) for f in filas) + "\n",
                   encoding="utf-8")
    r = subprocess.run([sys.executable, str(INGESTION / "compuerta.py"), str(csv),
                        "--lote", "07-2026_Q2"], capture_output=True, text=True, check=False)
    assert r.returncode == 0, r.stderr
    assert "2.50%" in r.stdout
    corridas = INGESTION / "corridas"
    paso = json.loads((corridas / "compuerta-07-2026_Q2.json").read_text(encoding="utf-8"))
    assert paso["capa"] == "COMPUERTA" and paso["resultado"] == "AVISO"
    assert paso["filas_entrada"] == 40 and paso["filas_salida"] == 39
    lineas = (corridas / "cuarentena-07-2026_Q2.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lineas) == 1
    assert json.loads(lineas[0])["motivo"] == "precio_fuera_de_rango"
    for f in ("compuerta-07-2026_Q2.json", "cuarentena-07-2026_Q2.jsonl"):
        (corridas / f).unlink()


# ── La población: el alcance del contrato, no el archivo ───────────────────
#
# Estas pruebas llegaron el 15 de octubre de 2026, después de que la compuerta ya
# estaba en `main`. Las de arriba arman lotes con todas sus filas dentro del
# alcance y en CSV, y por eso no vieron que un archivo del corpus real es parquet
# y trae las 32 entidades. Éstas usan un lote con la forma del corpus.

sys.path.insert(0, str(Path(__file__).resolve().parent))


def _lote_mezclado(tmp_path):
    """11 filas del alcance (1 con defecto) y 80 fuera (9 con defecto), en parquet
    tipado. Es la proporción real: alrededor del 12% del archivo es del alcance."""
    from lotes import escribir_parquet

    filas = [fila(producto=f"Dentro {i}", direccion=f"Calle {i}") for i in range(10)]
    filas.append(fila(producto="L" * 80, direccion="Dentro con defecto"))
    filas += [fila(estado="Nuevo León", producto=f"Fuera {i}", direccion=f"Norte {i}")
              for i in range(51)]
    filas += [fila(estado="Nuevo León", producto="L" * 90, direccion=f"Norte mal {i}")
              for i in range(9)]
    filas += [fila(catalogo="Medicamentos", producto=f"Med {i}", direccion=f"Farmacia {i}")
              for i in range(20)]
    return escribir_parquet(tmp_path / "07-2026_Q2.parquet", filas, COLUMNAS)


def test_la_compuerta_juzga_el_alcance_no_el_archivo(tmp_path, contrato):
    """**La que faltaba.** El 5% de D-07 y la contención de H1 son sobre el alcance
    (2,658,906 filas), no sobre el corpus (21,357,873). Si la compuerta revisara
    el archivo entero, las 9 filas defectuosas de Nuevo León contarían contra un
    lote del que no son parte."""
    from compuerta import leer_alcance

    df = leer_alcance(_lote_mezclado(tmp_path), contrato)
    assert len(df) == 11, f"la compuerta va a revisar {len(df)} filas; el alcance son 11"
    assert set(df["estado"]) == {"Guanajuato"}
    assert set(df["catalogo"]) == {"Basicos"}

    _, cuarentena, resumen = revisar_lote(df, contrato, "07-2026_Q2.parquet")
    assert resumen["filas_entrada"] == 11
    assert resumen["filas_en_cuarentena"] == 1, (
        "se apartaron filas que no son del alcance")
    assert [r["motivo"] for r in cuarentena] == ["largo_excedido"]


def test_el_recorte_es_el_mismo_que_aplica_la_ingesta(tmp_path, contrato):
    """La compuerta no escribe su propio recorte: usa el de `ingesta.py`. Se
    comprueba contando con la ingesta y con la compuerta sobre el mismo archivo."""
    import duckdb
    from compuerta import leer_alcance
    from ingesta import lector, lectura_declarada, recorte_del_contrato

    ruta = _lote_mezclado(tmp_path)
    s = recorte_del_contrato(contrato)["sql"]
    segun_ingesta = duckdb.connect().sql(
        f"SELECT count(*) FROM {lector(ruta, lectura_declarada(contrato, ruta.name))} "
        f"WHERE ({s['estado']}) AND ({s['ventana']}) AND ({s['catalogo']})"
    ).fetchone()[0]
    assert len(leer_alcance(ruta, contrato)) == segun_ingesta == 11


def test_sin_recorte_revisa_el_archivo_completo(tmp_path, contrato):
    """Igual que `ingesta.py --sin-recorte`: para reprocesar si el ADR 001 o el 005
    cambian. Existe, pero no es lo que se usa por omisión."""
    from compuerta import leer_alcance

    assert len(leer_alcance(_lote_mezclado(tmp_path), contrato, sin_recorte=True)) == 91


def test_lee_el_corpus_en_parquet_aunque_no_haya_pyarrow(tmp_path, contrato, monkeypatch):
    """Los 38 archivos del corpus son parquet, y `pd.read_parquet` necesita pyarrow,
    que no está en `requirements.txt`. Se bloquean pyarrow y fastparquet como si no
    estuvieran instalados: si alguien vuelve a leer con pandas, esto truena."""
    from compuerta import leer_alcance

    ruta = _lote_mezclado(tmp_path)
    monkeypatch.setitem(sys.modules, "pyarrow", None)
    monkeypatch.setitem(sys.modules, "fastparquet", None)
    df = leer_alcance(ruta, contrato)
    assert len(df) == 11


def test_la_fecha_tipada_del_parquet_no_es_tipo_invalido(tmp_path, contrato):
    """En parquet la fecha llega como fecha, no como texto con el formato que el
    contrato declara para el CSV. No puede caer en `tipo_invalido`."""
    from compuerta import leer_alcance

    df = leer_alcance(_lote_mezclado(tmp_path), contrato)
    _, _, resumen = revisar_lote(df, contrato, "07-2026_Q2.parquet")
    assert "tipo_invalido" not in resumen["por_motivo"]


def test_la_linea_de_comandos_reporta_el_alcance_de_un_parquet(tmp_path):
    ruta = _lote_mezclado(tmp_path)
    r = subprocess.run([sys.executable, str(INGESTION / "compuerta.py"), str(ruta),
                        "--lote", "07-2026_Q2", "--simular"],
                       capture_output=True, text=True, check=False)
    # 1 de 11 es el 9.09%, arriba del 5% de D-07: el lote se detiene y la línea de
    # comandos sale con 2, que es lo que hace con un lote DETENIDO.
    assert r.returncode == 2, r.stderr
    assert "11 filas" in r.stdout, r.stdout
    assert "1 en cuarentena" in r.stdout, r.stdout
    assert "(9.09%" in r.stdout, "la proporción no es sobre el alcance"
