"""Lo común de las pruebas de la interfaz analítica.

Los tokens se firman como `JwtService` del dominio: HS256, con los 32 bytes que
decodifica `JWT_SECRET`, y con `sub`, `rol`, `iat` y `exp`. La clave de las pruebas
se genera aquí; nunca es la de un `.env`, salvo en las dos pruebas que se piden
(`test_postgres.py` y `test_dominio.py`).
"""

import base64
import datetime as dt
import json
import os
import secrets
import sys
import time
from decimal import Decimal
from pathlib import Path

import jwt
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if not os.environ.get("JWT_SECRET"):
    os.environ["JWT_SECRET"] = base64.b64encode(secrets.token_bytes(32)).decode()

from analitica.main import almacen, app
from analitica.sesion import clave_de_jwt_secret


def token(rol="ANALISTA", clave=None, algoritmo="HS256", sin=(), vence_en=3600, **extra):
    ahora = int(time.time())
    claims = {"sub": "002a0c53-30d7-40a5-bb59-9a25130fd1ed", "rol": rol, "iat": ahora,
              "exp": ahora + vence_en, **extra}
    for claim in sin:
        claims.pop(claim)
    return jwt.encode(claims, clave_de_jwt_secret() if clave is None else clave,
                      algorithm=algoritmo)


def alterar_rol(valor, rol):
    """El mismo token con otro rol en los claims, sin volver a firmarlo."""
    cabecera, cuerpo, firma = valor.split(".")
    claims = json.loads(base64.urlsafe_b64decode(cuerpo + "=" * (-len(cuerpo) % 4)))
    claims["rol"] = rol
    cuerpo = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    return f"{cabecera}.{cuerpo}.{firma}"


class AlmacenDePrueba:
    """Lo que devolvería la capa intermedia, sin base: para la CI."""

    def entidades(self):
        return [("Guanajuato", "2026-07-Q2"), ("Querétaro", "2026-07-Q2")]

    def buscar(self, palabras, entidad, catalogo, limit, offset):
        filas = [("huevo", "paquete c 30 blanco", "HUEVO", "BASICOS", Decimal("65.00"), 12)]
        return "2026-07-Q2", len(filas), filas[offset:offset + limit]

    def precios(self, producto, presentacion, entidad):
        if producto != "huevo":
            return None, []
        return "2026-07-Q2", [
            ("SORIANA LEON", "BLVD. LOPEZ MATEOS 1", "LEON", "SORIANA", "BACHOCO",
             Decimal("62.5"), dt.date(2026, 7, 20)),
            ("MERCADO", None, None, "MERCADO", "S/M", Decimal(60), dt.date(2026, 7, 18))]

    def desglose(self, producto, presentacion, entidad, desde, hasta):
        if producto != "huevo":
            return []
        return [("SORIANA LEON", "SORIANA", Decimal("66.90"), Decimal("62.50"),
                 Decimal("64.333"), 3, "2026-07-Q1", "2026-07-Q2")]


@pytest.fixture
def cliente():
    from fastapi.testclient import TestClient

    app.dependency_overrides[almacen] = AlmacenDePrueba
    yield TestClient(app)
    app.dependency_overrides.clear()
