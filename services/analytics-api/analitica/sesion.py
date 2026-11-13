"""La sesión del dominio, verificada como dice el ADR 020.

- Sólo HS256. Un token con otro algoritmo, incluido `none`, no pasa.
- La clave son los 32 bytes que decodifica `JWT_SECRET` (Base64 estándar), no el
  texto: la misma que usa `JwtService` del dominio para firmar.
- `sub`, `rol`, `iat` y `exp` son obligatorios, sin tolerancia de reloj.

El rol de cada ruta (`x-rol`, P-07) se exige aquí. Sin token, con uno que no pasa o
con otro rol, la respuesta es la misma: 401 `SinSesion`, como dice analitica.yaml.
"""

import base64
import binascii
import os
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .problemas import SinSesion

ALGORITMO = "HS256"
CLAIMS = ("sub", "rol", "iat", "exp")
BYTES_DE_LA_CLAVE = 32

# `auto_error=False`: sin encabezado, FastAPI respondería 403 con su propio cuerpo;
# así llega `None` y la respuesta es el 401 del contrato.
_portador = HTTPBearer(scheme_name="sesion", bearerFormat="JWT", auto_error=False)


def clave_de_jwt_secret(texto=None):
    """Los 32 bytes de la clave. Con otra cosa no se arranca, igual que el dominio."""
    texto = (os.environ.get("JWT_SECRET", "") if texto is None else texto).strip()
    try:
        clave = base64.b64decode(texto, validate=True)
    except (binascii.Error, ValueError):
        clave = b""
    if len(clave) != BYTES_DE_LA_CLAVE:
        raise RuntimeError("JWT_SECRET tiene que ser Base64 de 32 bytes aleatorios "
                           "(ADR 020). Genérala con: openssl rand -base64 32")
    return clave


def verificar(token, clave):
    """Los claims de un token que lo pasa todo. Si no, `jwt.InvalidTokenError`."""
    claims = jwt.decode(token, clave, algorithms=[ALGORITMO],
                        options={"require": list(CLAIMS)}, leeway=0)
    if not isinstance(claims["rol"], str):
        raise jwt.InvalidTokenError("el claim rol tiene que ser texto")
    return claims


def requiere_rol(rol):
    """La dependencia de una ruta con `x-rol: <rol>`."""

    def sesion_con_rol(
            credenciales: Annotated[HTTPAuthorizationCredentials | None, Depends(_portador)]):
        if credenciales is None:
            raise SinSesion("Falta la sesión.")
        try:
            claims = verificar(credenciales.credentials, clave_de_jwt_secret())
        except jwt.InvalidTokenError:
            raise SinSesion("La sesión no es válida o ya venció.") from None
        if claims["rol"] != rol:
            raise SinSesion(f"Esta ruta pide una sesión con el rol {rol}.")
        return claims

    return sesion_con_rol


def token_de_la_sesion(
        credenciales: Annotated[HTTPAuthorizationCredentials | None, Depends(_portador)]):
    """El token tal como llegó, para presentárselo al dominio (`cuenta.py`, D-11).
    Sólo tiene sentido en una ruta que ya pasó por `requiere_rol`."""
    return credenciales.credentials if credenciales else None
