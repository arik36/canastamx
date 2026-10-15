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


def test_los_tres_motivos_sin_declarar_son_los_que_el_catalogo_marca():
    """`en_contrato = false` en el catálogo y «sin declarar» en la compuerta
    tienen que ser la misma lista. Es el pendiente del 9 de noviembre."""
    del_catalogo = {m for m in MOTIVOS
                    if re.search(rf"\('{m}',[^)]*?,\s*false,", ESQUEMA_SQL)}
    assert set(motivos_que_el_contrato_no_declara()) == del_catalogo
    assert del_catalogo == {"valor_requerido_vacio", "largo_excedido", "tipo_invalido"}


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
