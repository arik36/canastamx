"""La prueba cruzada de T058, en la CI: el token del ADR 020 contra una ruta con
`x-rol: ANALISTA`. Los tokens se firman como `JwtService` (ver conftest.py); la
vuelta de punta a punta contra el dominio real está en test_dominio.py.

Desde T069, además, quién puede pedir cada una de las rutas con `x-rol`: las seis de
la consola piden OPERADOR y las de análisis, ANALISTA. Con otro rol o sin token,
401 `SinSesion`."""

import base64
import secrets

import pytest
from analitica.sesion import clave_de_jwt_secret
from conftest import alterar_rol, token
from contrato import errores, esquema

RUTA = "/api/v1/articulos/establecimientos"
PARAMS = {"producto": "huevo", "presentacion": "paquete c 30 blanco", "entidad": "Guanajuato"}


def _pedir(cliente, valor=None, esquema_http="Bearer"):
    cabeceras = {"Authorization": f"{esquema_http} {valor}"} if valor else {}
    return cliente.get(RUTA, params=PARAMS, headers=cabeceras)


def _sin_firma():
    """`alg: none`, el clásico: los mismos claims y ninguna firma."""
    _, cuerpo, _ = token().split(".")
    cabecera = base64.urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}').rstrip(b"=").decode()
    return f"{cabecera}.{cuerpo}."


def test_el_token_de_una_cuenta_analista_pasa(cliente):
    r = _pedir(cliente, token(rol="ANALISTA"))
    assert r.status_code == 200, r.text


QUE_NO_PASAN = {
    "sin token": lambda: None,
    "de una cuenta OPERADOR": lambda: token(rol="OPERADOR"),
    "de una cuenta CONSUMIDOR": lambda: token(rol="CONSUMIDOR"),
    "de OPERADOR con el rol cambiado a ANALISTA": lambda: alterar_rol(token(rol="OPERADOR"), "ANALISTA"),
    "vencido hace un segundo": lambda: token(vence_en=-1),
    "emitido en el futuro": lambda: token(iat=10**10),
    "firmado con otra clave": lambda: token(clave=secrets.token_bytes(32)),
    "firmado con HS512": lambda: token(algoritmo="HS512", clave=secrets.token_bytes(64)),
    "sin firma (alg none)": _sin_firma,
    **{f"sin el claim {c}": (lambda c=c: token(sin=(c,))) for c in ("sub", "rol", "iat", "exp")},
}


@pytest.mark.parametrize("caso", list(QUE_NO_PASAN))
def test_el_que_no_pasa_recibe_401_sin_sesion(cliente, caso):
    r = _pedir(cliente, QUE_NO_PASAN[caso]())
    assert r.status_code == 401, r.text
    assert r.headers["content-type"].startswith("application/problem+json")
    assert r.json()["type"] == "/problemas/sin-sesion"
    assert not errores(r.json(), esquema(RUTA, "get", 401, "application/problem+json"))


def test_otro_esquema_que_no_es_bearer_recibe_401(cliente):
    assert _pedir(cliente, token(), esquema_http="Basic").status_code == 401


@pytest.mark.parametrize("texto", ["", "no-es-base64!", secrets.token_hex(32),
                                   base64.b64encode(secrets.token_bytes(48)).decode()])
def test_un_jwt_secret_que_no_es_base64_de_32_bytes_no_arranca(texto):
    with pytest.raises(RuntimeError, match="openssl rand -base64 32"):
        clave_de_jwt_secret(texto)


# ── T069 · el rol de cada ruta ────────────────────────────────────────────────

CIERRE = {"causa": "INFRAESTRUCTURA", "decision": "Se reinició el servicio."}
# (método, ruta, parámetros, cuerpo), con lo que cada una necesita para dar 200.
DEL_OPERADOR = {
    "estadoDeLaPlataforma": ("get", "/api/v1/operacion/estado", None, None),
    "listarCorridas": ("get", "/api/v1/operacion/corridas", None, None),
    "linajeDeLote": ("get", "/api/v1/operacion/corridas/07-2026_Q2", None, None),
    "listarCuarentena": ("get", "/api/v1/operacion/cuarentena", None, None),
    "listarIncidentes": ("get", "/api/v1/operacion/incidentes", None, None),
    "cerrarIncidente": ("post", "/api/v1/operacion/incidentes/2/cierre", None, CIERRE),
}
DEL_ANALISTA = {
    "articulosAnomalos": ("get", "/api/v1/anomalias", None, None),
    "serieDeArticulo": ("get", "/api/v1/articulos/serie", PARAMS, None),
    "desgloseDeArticulo": ("get", RUTA, PARAMS, None),
}
CON_ROL = [(rol, operacion, pedido)
           for rol, suyas in (("OPERADOR", DEL_OPERADOR), ("ANALISTA", DEL_ANALISTA))
           for operacion, pedido in suyas.items()]
OTROS = {"OPERADOR": ("ANALISTA", "CONSUMIDOR"), "ANALISTA": ("OPERADOR", "CONSUMIDOR")}


def _con(cliente, pedido, valor=None):
    metodo, ruta, params, cuerpo = pedido
    cabeceras = {"Authorization": f"Bearer {valor}"} if valor else {}
    return cliente.request(metodo, ruta, params=params, json=cuerpo, headers=cabeceras)


def test_cada_ruta_con_x_rol_del_contrato_esta_en_esta_prueba():
    from analitica.main import app

    con_rol = {o["operationId"]: o["x-rol"] for metodos in app.openapi()["paths"].values()
               for o in metodos.values() if "x-rol" in o}
    assert con_rol == {operacion: rol for rol, operacion, _ in CON_ROL}


@pytest.mark.parametrize(("rol", "operacion", "pedido"), CON_ROL)
def test_con_el_rol_de_la_ruta_responde_200(cliente, rol, operacion, pedido):
    r = _con(cliente, pedido, token(rol=rol))
    assert r.status_code == 200, r.text


@pytest.mark.parametrize(("rol", "operacion", "pedido"), CON_ROL)
def test_con_otro_rol_o_sin_token_responde_401_sin_sesion(cliente, rol, operacion, pedido):
    de_otro = token(rol=OTROS[rol][0])
    for valor in (None, de_otro, token(rol=OTROS[rol][1]), alterar_rol(de_otro, rol),
                  token(rol=rol, vence_en=-1), token(rol=rol, clave=secrets.token_bytes(32))):
        r = _con(cliente, pedido, valor)
        assert r.status_code == 401, r.text
        assert r.headers["content-type"].startswith("application/problem+json")
        assert r.json()["type"] == "/problemas/sin-sesion"


def test_sin_el_rol_de_operador_el_incidente_sigue_abierto(cliente):
    from conftest import AlmacenDePrueba, DominioDePrueba

    for valor in (None, token(rol="ANALISTA"), alterar_rol(token(rol="ANALISTA"), "OPERADOR")):
        assert _con(cliente, DEL_OPERADOR["cerrarIncidente"], valor).status_code == 401
    assert AlmacenDePrueba.incidentes_guardados[2][6] == "ABIERTO"
    assert DominioDePrueba.pedidos == []          # ni siquiera se le pregunta al dominio


def test_sin_sesion_la_respuesta_es_401_aunque_el_cuerpo_este_mal(cliente):
    """Primero la sesión: quien no la tiene no se entera de qué pide el cuerpo."""
    r = cliente.post("/api/v1/operacion/incidentes/2/cierre", json={"causa": "OTRA"})
    assert r.status_code == 401 and r.json()["type"] == "/problemas/sin-sesion"


def test_las_de_consumo_no_piden_sesion(cliente):
    r = cliente.post("/api/v1/canastas/costo", json={"entidad": "Guanajuato", "lineas": []})
    assert r.status_code == 200, r.text
