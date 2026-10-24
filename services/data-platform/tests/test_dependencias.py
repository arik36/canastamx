"""DuckDB va anclado, y el código de services/ no depende de lo que la 2.0 quitó.

DuckDB 2.0 quitó `fetchone()` de las relaciones (lo que devuelve `con.sql(...)`).
Ver la EXCEPCIÓN de duckdb en requirements.txt.
"""

import ast
import re
from pathlib import Path

import duckdb

PLATAFORMA = Path(__file__).resolve().parents[1]
REQUISITOS = PLATAFORMA / "requirements.txt"


def _ancla_de_duckdb():
    for linea in REQUISITOS.read_text(encoding="utf-8").splitlines():
        encontrada = re.match(r"\s*duckdb\s*(==|>=|<=|~=|!=|>|<)\s*([0-9][^\s#]*)", linea)
        if encontrada:
            return encontrada.group(1), encontrada.group(2)
    raise AssertionError("requirements.txt no declara duckdb")


def test_duckdb_va_anclado_a_una_version_exacta():
    operador, version = _ancla_de_duckdb()
    assert operador == "==", (
        f"duckdb{operador}{version}: sin ancla, cada instalación toma la última versión")


def test_la_version_instalada_es_la_anclada():
    _, version = _ancla_de_duckdb()
    assert duckdb.__version__ == version, (
        f"instalada {duckdb.__version__}, anclada {version}: "
        "pip install -r services/data-platform/requirements.txt")


def _fetchone_sobre_relaciones(ruta):
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    return [nodo.lineno for nodo in ast.walk(arbol)
            if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute)
            and nodo.func.attr == "fetchone"
            and isinstance(nodo.func.value, ast.Call)
            and isinstance(nodo.func.value.func, ast.Attribute)
            and nodo.func.value.func.attr == "sql"]


def test_services_no_llama_fetchone_sobre_una_relacion():
    """Para que el código del servicio no sea lo que impida pasar a DuckDB 2.0."""
    encontrados = {}
    for carpeta in ("ingestion", "orquestacion", "tests"):
        for ruta in sorted((PLATAFORMA / carpeta).glob("*.py")):
            lineas = _fetchone_sobre_relaciones(ruta)
            if lineas:
                encontrados[f"{carpeta}/{ruta.name}"] = lineas
    assert not encontrados, f"fetchone() sobre con.sql(...): {encontrados}"
