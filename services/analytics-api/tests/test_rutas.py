"""Las cuatro rutas de T058 contra analitica.yaml 0.2.1, con la capa simulada.

Lo que se comprueba es la forma: cada respuesta contra su esquema del contrato, y
que la ruta, su `operationId` y su `x-rol` sean los del contrato. Las consultas de
verdad, contra `postgres-analytics`, están en test_postgres.py.
"""

import pytest
from analitica.main import app
from conftest import token
from contrato import CONTRATO, errores, esquema

HUEVO = {"producto": "Huevo", "presentacion": "PAQUETE C/30 blanco", "entidad": "guanajuato"}
CUATRO = [("/api/v1/entidades", "listarEntidades", None),
          ("/api/v1/articulos", "buscarArticulos", None),
          ("/api/v1/precios", "compararPrecios", None),
          ("/api/v1/articulos/establecimientos", "desgloseDeArticulo", "ANALISTA")]


@pytest.mark.parametrize(("ruta", "operacion", "rol"), CUATRO)
def test_la_ruta_es_la_del_contrato(ruta, operacion, rol):
    del_contrato = CONTRATO["paths"][ruta]["get"]
    generada = app.openapi()["paths"][ruta]["get"]
    assert del_contrato["operationId"] == generada["operationId"] == operacion
    assert del_contrato.get("x-rol") == generada.get("x-rol") == rol


def _cumple(r, ruta, estado=200, medio="application/json"):
    assert r.status_code == estado, r.text
    assert r.headers["content-type"].startswith(medio)
    assert not errores(r.json(), esquema(ruta, "get", estado, medio)), r.json()
    return r.json()


def test_entidades(cliente):
    cuerpo = _cumple(cliente.get("/api/v1/entidades"), "/api/v1/entidades")
    assert cuerpo["entidades"][0] == {"entidad": "Guanajuato", "ultimaQuincena": "2026-07-Q2"}


def test_buscar_en_una_entidad_cubierta(cliente):
    r = cliente.get("/api/v1/articulos", params={"q": "huevo", "entidad": "GUANAJUATO"})
    cuerpo = _cumple(r, "/api/v1/articulos")
    assert cuerpo["cobertura"] and cuerpo["entidad"] == "Guanajuato" and cuerpo["total"] == 1
    assert cuerpo["resultados"][0]["precioTipico"] == {"monto": "65.00", "moneda": "MXN"}


def test_buscar_fuera_del_alcance_es_200_con_cobertura_false(cliente):
    r = cliente.get("/api/v1/articulos", params={"q": "huevo", "entidad": "Yucatán"})
    cuerpo = _cumple(r, "/api/v1/articulos")
    assert cuerpo == {"cobertura": False, "entidad": "Yucatán",
                      "entidadesCubiertas": ["Guanajuato", "Querétaro"]}


@pytest.mark.parametrize("params", [{"q": "h", "entidad": "Guanajuato"},
                                    {"q": "huevo", "entidad": "Guanajuato", "limit": 101},
                                    {"q": "huevo", "entidad": "Guanajuato", "catalogo": "OTRO"}])
def test_datos_invalidos_es_400(cliente, params):
    _cumple(cliente.get("/api/v1/articulos", params=params), "/api/v1/articulos", 400,
            "application/problem+json")


def test_precios_con_la_marca_generica_al_final(cliente):
    cuerpo = _cumple(cliente.get("/api/v1/precios", params=HUEVO), "/api/v1/precios")
    assert cuerpo["articulo"] == {"producto": "huevo", "presentacion": "paquete c 30 blanco"}
    assert [e["precio"]["monto"] for e in cuerpo["establecimientos"]] == ["62.50", "60.00"]


def test_precios_sin_datos_es_404(cliente):
    r = cliente.get("/api/v1/precios", params={**HUEVO, "producto": "caviar"})
    _cumple(r, "/api/v1/precios", 404, "application/problem+json")


def test_desglose_trae_su_poblacion(cliente):
    r = cliente.get("/api/v1/articulos/establecimientos", params=HUEVO,
                    headers={"Authorization": f"Bearer {token()}"})
    cuerpo = _cumple(r, "/api/v1/articulos/establecimientos")
    assert cuerpo["establecimientos"][0]["promedio"]["monto"] == "64.33"
    assert cuerpo["poblacion"] == {"entidades": ["Guanajuato"], "desde": "2026-07-Q1",
                                   "hasta": "2026-07-Q2", "observaciones": 3}
