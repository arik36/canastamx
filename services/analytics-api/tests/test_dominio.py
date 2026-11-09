"""La prueba cruzada de punta a punta (T058): el dominio real emite los tokens de las
cuentas de la semilla de T044 y la interfaz analítica los verifica.

La prueba es del token, no de los datos: la ruta lee la capa simulada. Necesita el
dominio corriendo (`DOMINIO_URL`, por omisión http://localhost:8081), la semilla
sembrada y, del `.env`, `JWT_SECRET` y `SEMILLA_CONTRASENA`. No imprime ni tokens ni
contraseñas: sólo qué se pidió y qué se respondió.

    CANASTAMX_PRUEBA_DOMINIO=1 python -m pytest services/analytics-api/tests/test_dominio.py -v -s
"""

import json
import os
import urllib.request

import pytest
from conftest import AlmacenDePrueba, alterar_rol

pytestmark = pytest.mark.skipif(os.environ.get("CANASTAMX_PRUEBA_DOMINIO") != "1",
                                reason="contra el dominio real: CANASTAMX_PRUEBA_DOMINIO=1")

DOMINIO = os.environ.get("DOMINIO_URL", "http://localhost:8081")
RUTA = "/api/v1/articulos/establecimientos"
PARAMS = {"producto": "huevo", "presentacion": "paquete c 30 blanco", "entidad": "Guanajuato"}


def _sesion(correo):
    cuerpo = json.dumps({"correo": correo,
                         "contrasena": os.environ["SEMILLA_CONTRASENA"]}).encode()
    pedido = urllib.request.Request(f"{DOMINIO}/api/v1/sesiones", data=cuerpo,
                                    headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(pedido, timeout=10) as r:
        return json.load(r)


def test_punta_a_punta_contra_el_dominio():
    from analitica.main import almacen, app
    from fastapi.testclient import TestClient

    analista, operador = _sesion("analista@canastamx.mx"), _sesion("operador@canastamx.mx")
    print(f"dominio {DOMINIO} · sesiones: {analista['rol']} y {operador['rol']}")
    assert (analista["rol"], operador["rol"]) == ("ANALISTA", "OPERADOR")
    casos = [("token de ANALISTA", analista["token"], 200),
             ("token de OPERADOR", operador["token"], 401),
             ("sin token", None, 401),
             ("OPERADOR con el rol cambiado a ANALISTA",
              alterar_rol(operador["token"], "ANALISTA"), 401)]
    app.dependency_overrides[almacen] = AlmacenDePrueba
    try:
        cliente = TestClient(app)
        for caso, valor, esperado in casos:
            r = cliente.get(RUTA, params=PARAMS,
                            headers={"Authorization": f"Bearer {valor}"} if valor else {})
            print(f"GET {RUTA} · {caso:<40} → {r.status_code}")
            assert r.status_code == esperado, r.text
    finally:
        app.dependency_overrides.clear()
