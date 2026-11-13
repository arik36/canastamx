"""De quién es la sesión (D-11): `cuenta.Dominio` contra un dominio de mentira que
escucha en esta máquina. El de verdad está en test_dominio.py, que corre a mano.

Lo que se cuida: que al dominio le llegue el mismo token, que sólo se acepte la
cuenta del `sub`, y que ningún error repita el token."""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from analitica.cuenta import Dominio, url_del_dominio
from analitica.problemas import DominioNoDisponible, SinSesion

TOKEN = "cabecera.cuerpo.firma-que-no-debe-salir"
CUENTA = "002a0c53-30d7-40a5-bb59-9a25130fd1ed"
SUYA = {"id": CUENTA, "correo": "operador@canastamx.mx", "rol": "OPERADOR",
        "fechaDeRegistro": "2026-10-20T10:00:00Z"}


@pytest.fixture
def dominio(monkeypatch):
    """Un servidor que contesta `cuentas/yo` con lo que la prueba le deje en
    `respuesta`, y apunta en `pedidos` qué le pidieron."""
    estado = {"respuesta": (200, json.dumps(SUYA)), "pedidos": []}

    class Manejador(BaseHTTPRequestHandler):
        def do_GET(self):
            estado["pedidos"].append((self.path, self.headers.get("Authorization")))
            codigo, cuerpo = estado["respuesta"]
            self.send_response(codigo)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(cuerpo.encode())

        def log_message(self, *_):
            pass

    servidor = HTTPServer(("127.0.0.1", 0), Manejador)
    threading.Thread(target=servidor.serve_forever, args=(0.01,), daemon=True).start()
    monkeypatch.setenv("DOMINIO_URL", f"http://127.0.0.1:{servidor.server_port}/")
    yield estado
    servidor.shutdown()
    servidor.server_close()


def test_pregunta_con_el_mismo_token_y_devuelve_el_correo(dominio):
    assert Dominio().correo(TOKEN, CUENTA) == "operador@canastamx.mx"
    assert dominio["pedidos"] == [("/api/v1/cuentas/yo", f"Bearer {TOKEN}")]


def test_si_el_dominio_no_reconoce_la_sesion_es_sin_sesion(dominio):
    dominio["respuesta"] = (401, json.dumps({"type": "/problemas/sin-sesion"}))
    with pytest.raises(SinSesion):
        Dominio().correo(TOKEN, CUENTA)


@pytest.mark.parametrize("respuesta", [
    (500, "{}"), (404, "{}"), (200, "no es json"), (200, "[]"), (200, "{}"),
    (200, json.dumps({**SUYA, "correo": None})),
    (200, json.dumps({**SUYA, "correo": "sin-arroba"})),
    (200, json.dumps({**SUYA, "id": "la-cuenta-de-otra-persona"}))])
def test_cualquier_otra_respuesta_es_dominio_no_disponible(dominio, respuesta):
    dominio["respuesta"] = respuesta
    with pytest.raises(DominioNoDisponible) as error:
        Dominio().correo(TOKEN, CUENTA)
    assert error.value.status == 503


def test_un_dominio_que_no_responde_no_ensena_el_token(monkeypatch):
    monkeypatch.setenv("DOMINIO_URL", "http://127.0.0.1:1")
    with pytest.raises(DominioNoDisponible) as error:
        Dominio().correo(TOKEN, CUENTA)
    assert "firma-que-no-debe-salir" not in str(error.getrepr(style="long"))
    # `from None`: el traceback de urllib, que trae el pedido con el token, no se muestra.
    assert error.value.__cause__ is None and error.value.__suppress_context__


@pytest.mark.parametrize(("valor", "url"), [(None, "http://localhost:8081"),
                                            ("", "http://localhost:8081"),
                                            ("http://dominio:8081/", "http://dominio:8081")])
def test_sin_dominio_url_es_el_de_desarrollo(monkeypatch, valor, url):
    if valor is None:
        monkeypatch.delenv("DOMINIO_URL", raising=False)
    else:
        monkeypatch.setenv("DOMINIO_URL", valor)
    assert url_del_dominio() == url
