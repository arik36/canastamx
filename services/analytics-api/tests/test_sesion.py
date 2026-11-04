"""La prueba cruzada de T058, en la CI: el token del ADR 020 contra una ruta con
`x-rol: ANALISTA`. Los tokens se firman como `JwtService` (ver conftest.py); la
vuelta de punta a punta contra el dominio real está en test_dominio.py."""

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
