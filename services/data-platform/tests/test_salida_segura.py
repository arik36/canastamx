"""La salida tolera una codificación limitada (ingestion/salida_segura.py).

Las pruebas de punta a punta, con PYTHONIOENCODING=cp1252, están junto a cada línea
de comandos (test_ingesta, test_compuerta y test_orquestacion). Éstas prueban la
pieza y que ninguna línea de comandos ni ningún proceso hijo se quede sin ella. Una
corrida en Windows de verdad sigue haciendo falta: esto prueba el mecanismo.
"""

import ast
import io
import os
import sys
from pathlib import Path

PLATAFORMA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATAFORMA / "ingestion"))

from salida_segura import CODIFICACION_DE_LOS_HIJOS, entorno_utf8, preparar_salida


def test_lo_que_cp1252_no_tiene_queda_con_su_codigo_y_lo_demas_igual(monkeypatch):
    crudos = {}
    for nombre in ("stdout", "stderr"):
        crudos[nombre] = io.BytesIO()
        monkeypatch.setattr(sys, nombre, io.TextIOWrapper(
            crudos[nombre], encoding="cp1252", errors="strict", write_through=True))

    preparar_salida()
    print("ventana 2025-01-Q1 → 2026-07-Q2 ✓ · Michoacán")
    print("✗ detenido", file=sys.stderr)

    assert crudos["stdout"].getvalue().decode("cp1252") == (
        "ventana 2025-01-Q1 \\u2192 2026-07-Q2 \\u2713 · Michoacán\n")
    assert crudos["stderr"].getvalue().decode("cp1252") == "\\u2717 detenido\n"


def test_el_entorno_del_hijo_pide_utf8_sin_tocar_el_del_proceso(monkeypatch):
    monkeypatch.setenv("PYTHONIOENCODING", "cp1252")

    entorno = entorno_utf8()

    assert entorno["PYTHONIOENCODING"] == CODIFICACION_DE_LOS_HIJOS == "utf-8"
    assert os.environ["PYTHONIOENCODING"] == "cp1252"
    assert entorno_utf8({"A": "1"}) == {"A": "1", "PYTHONIOENCODING": "utf-8"}


def _arbol(ruta):
    return ast.parse(ruta.read_text(encoding="utf-8"))


def test_cada_linea_de_comandos_prepara_su_salida_antes_que_nada():
    """Una línea de comandos nueva sin preparar_salida() vuelve a tronar en Windows."""
    sin_preparar = []
    for ruta in sorted((PLATAFORMA / "ingestion").glob("*.py")):
        for nodo in _arbol(ruta).body:
            if isinstance(nodo, ast.FunctionDef) and nodo.name == "main":
                primera = nodo.body[0]
                llama = (isinstance(primera, ast.Expr) and isinstance(primera.value, ast.Call)
                         and getattr(primera.value.func, "id", None) == "preparar_salida")
                if not llama:
                    sin_preparar.append(ruta.name)
    assert not sin_preparar, f"main() sin preparar_salida() al empezar: {sin_preparar}"


def test_cada_proceso_hijo_de_la_orquestacion_se_lee_en_utf8():
    """Quien lee la salida de un hijo declara la codificación de los dos lados."""
    sueltos = []
    for ruta in sorted((PLATAFORMA / "orquestacion").glob("*.py")):
        for nodo in ast.walk(_arbol(ruta)):
            if (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute)
                    and nodo.func.attr in ("run", "Popen", "check_output")
                    and getattr(nodo.func.value, "id", None) == "subprocess"):
                claves = {k.arg for k in nodo.keywords}
                if not {"encoding", "env"} <= claves:
                    sueltos.append(f"{ruta.name}:{nodo.lineno}")
    assert not sueltos, f"subprocess sin encoding y env: {sueltos}"
