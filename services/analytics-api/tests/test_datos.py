"""Una conexión que falla no enseña la contraseña, ni en el mensaje ni en el traceback
que pytest imprime con los argumentos y las variables de cada función."""

import pytest
from analitica.datos import Almacen

SECRETO = "clave-que-no-debe-salir"


def _base_que_no_responde(monkeypatch):
    for variable, valor in {"ANALYTICS_HOST": "127.0.0.1", "ANALYTICS_PORT": "1",
                            "ANALYTICS_DB": "base", "ANALYTICS_USER": "usuario",
                            "ANALYTICS_PASSWORD": SECRETO}.items():
        monkeypatch.setenv(variable, valor)
    monkeypatch.delenv("PGPASSWORD", raising=False)    # al final queda como estaba


def test_una_conexion_fallida_no_muestra_la_contrasena(monkeypatch):
    _base_que_no_responde(monkeypatch)
    with pytest.raises(RuntimeError, match="no se pudo conectar") as error:
        Almacen().consulta("SELECT 1")
    assert SECRETO not in str(error.getrepr(style="long", funcargs=True, showlocals=True))
