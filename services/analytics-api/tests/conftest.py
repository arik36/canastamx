"""Lo común de las pruebas de la interfaz analítica.

Los tokens se firman como `JwtService` del dominio: HS256, con los 32 bytes que
decodifica `JWT_SECRET`, y con `sub`, `rol`, `iat` y `exp`. La clave de las pruebas
se genera aquí; nunca es la de un `.env`, salvo en las dos pruebas que se piden
(`test_postgres.py` y `test_dominio.py`).

`AlmacenDePrueba` y `DominioDePrueba` hacen de la base y del dominio en la CI: lo
que se prueba con ellos es la forma de cada respuesta y quién puede pedirla.
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

from analitica.main import almacen, app, dominio
from analitica.sesion import clave_de_jwt_secret

CUENTA = "002a0c53-30d7-40a5-bb59-9a25130fd1ed"
CORREO = "operador@canastamx.mx"
UTC = dt.UTC


def token(rol="ANALISTA", clave=None, algoritmo="HS256", sin=(), vence_en=3600, **extra):
    ahora = int(time.time())
    claims = {"sub": CUENTA, "rol": rol, "iat": ahora,
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


def _corrida(lote, dia, hora, resultado, leidas, aceptadas, apartadas, segundos=42.5):
    return (lote, dt.datetime(2026, 11, dia, hora, tzinfo=UTC), resultado, leidas, aceptadas,
            apartadas, Decimal(str(segundos)))


# Un lote que se rechazó y después se reprocesó, y dos que pasaron: uno con aviso.
CORRIDAS = [_corrida("07-2026_Q2", 10, 18, "CORRECTA", 70120, 69980, 140),
            _corrida("06-2026_Q2", 10, 17, "CON_AVISOS", 69000, 68900, 100),
            _corrida("04-2026_Q2", 9, 12, "CORRECTA", 100, 100, 0, 180),
            _corrida("04-2026_Q2", 9, 10, "RECHAZADA", 100, 0, 9, 240)]
CUARENTENA = [("07-2026_Q2", "revision_humana", "contrato_por_fila",
               {"producto": "HUEVO", "marca": "BACH?CO", "precio": "65.00"}),
              ("07-2026_Q2", "colision_precio_alta", "reglas_de_lote",
               {"producto": "LECHE", "marca": "LALA", "precio": "250.00"}),
              ("06-2026_Q2", "precio_fuera_de_rango", "contrato_por_fila",
               {"producto": "HUEVO", "marca": "S/M", "precio": "6500.00"})]


def _incidentes():
    """{id: fila}, en las columnas de `Almacen.INCIDENTE`: un aviso, un incidente
    abierto y uno ya cerrado."""
    abierto = dt.datetime(2026, 11, 9, 10, 4, tzinfo=UTC)
    return {
        1: (1, "AVISO", "06-2026_Q2", "deriva_de_esquema", "columnas_extra", 0, "INFORMATIVO",
            dt.datetime(2026, 11, 10, 17, 1, tzinfo=UTC), None, None, None, None, False),
        2: (2, "INCIDENTE", "04-2026_Q2", "promocion_del_lote", "rechazo_mayor_al_umbral", 9,
            "ABIERTO", abierto, None, None, None, None, False),
        3: (3, "INCIDENTE", "05-2026_Q1", "contrato_por_fila", "columna_requerida_faltante",
            68000, "CERRADO", abierto, abierto + dt.timedelta(hours=1), "otra@canastamx.mx",
            "ARCHIVO_DE_LA_FUENTE", "Se pidió el archivo corregido.", True)}


class AlmacenDePrueba:
    """Lo que devolverían la capa intermedia, la estrella y el esquema de operación,
    sin base: para la CI. Los incidentes se reinician en cada prueba."""

    incidentes_guardados = _incidentes()
    sin_corridas = False

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

    # ── La estrella ────────────────────────────────────────────────────────────

    def costo(self, entidad, articulos):
        # El mercado no vende leche; Soriana tiene las dos cosas y sale más cara.
        precios = [("Soriana", "huevo", "paquete c 30 blanco", Decimal("66.90")),
                   ("Soriana", "leche", "1 l", Decimal("27.505")),
                   ("Bodega Aurrera", "huevo", "paquete c 30 blanco", Decimal("62.00")),
                   ("Bodega Aurrera", "leche", "1 l", Decimal("26.00")),
                   ("Mercado", "huevo", "paquete c 30 blanco", Decimal("58.00"))]
        return "2026-07-Q2", [f for f in precios if (f[1], f[2]) in articulos]

    def anomalos(self, entidad, catalogo, desde, hasta, umbral, minimo, limit):
        if entidad not in (None, "Guanajuato", "Querétaro"):
            return [], ([], desde or "2025-01-Q1", hasta or "2026-07-Q2", 0)
        filas = [("jitomate saladette", "1 kg", "Guanajuato", "2026-07-Q1", Decimal("0.4426"), 9),
                 ("limon", "1 kg", "Guanajuato", "2026-06-Q2", Decimal("-0.2511"), 6)]
        filas = [f for f in filas if abs(f[4]) > umbral and f[5] >= minimo]
        return filas[:limit], (["Guanajuato", "Querétaro"], "2025-01-Q1", "2026-07-Q2", 286489)

    def serie(self, producto, presentacion, entidad, desde, hasta):
        if producto != "huevo":
            return []
        return [("2026-07-Q1", "Guanajuato", Decimal("65.00"), Decimal("62.00"),
                 Decimal("68.50"), Decimal("59.00"), Decimal("91.00"), 47),
                ("2026-07-Q2", "Guanajuato", Decimal("66.00"), Decimal("63.00"),
                 Decimal("69.00"), Decimal("60.00"), Decimal("90.00"), 45)]

    # ── El esquema de operación ────────────────────────────────────────────────

    def estado(self):
        if self.sin_corridas:
            return None
        return ({"ultimo_dato": "2026-07-Q2", "frescura_estado": "NO_APLICA",
                 "frescura_dias": 102, "filas_procesadas": 139220, "cuarentena_filas": 240,
                 "cuarentena_porcentaje": Decimal("0.172"),
                 "cuarentena_poblacion": "lotes vigentes del alcance", "avisos_de_esquema": 1,
                 "incidentes_abiertos": 1}, CORRIDAS[0])

    def corridas(self, limit, offset):
        return len(CORRIDAS), CORRIDAS[offset:offset + limit]

    def linaje(self, lote):
        return sorted((c for c in CORRIDAS if c[0] == lote), key=lambda c: c[1])

    def cuarentena(self, lote, motivo, limit, offset):
        filas = [f for f in CUARENTENA if lote in (None, f[0]) and motivo in (None, f[1])]
        return len(filas), filas[offset:offset + limit]

    def incidentes(self, estado, severidad, limit, offset):
        filas = [f for f in self.incidentes_guardados.values()
                 if estado in (None, f[6]) and severidad in (None, f[1])]
        return len(filas), filas[offset:offset + limit]

    def incidente(self, incidente_id):
        return self.incidentes_guardados.get(incidente_id)

    def cerrar_incidente(self, incidente_id, causa, decision, reprocesar_lote, correo):
        fila = self.incidentes_guardados.get(incidente_id)
        if fila is None or fila[6] != "ABIERTO":
            return None
        cerrada = (*fila[:6], "CERRADO", fila[7], dt.datetime.now(UTC), correo, causa, decision,
                   reprocesar_lote)
        self.incidentes_guardados[incidente_id] = cerrada
        return cerrada


class DominioDePrueba:
    """El dominio que contesta `cuentas/yo`: el correo de la cuenta de la sesión."""

    pedidos = ()         # (token, cuenta) de cada pregunta; la prueba lo reinicia

    def correo(self, token, cuenta):
        DominioDePrueba.pedidos = [*self.pedidos, (token, cuenta)]
        return CORREO


@pytest.fixture
def cliente():
    from fastapi.testclient import TestClient

    AlmacenDePrueba.incidentes_guardados = _incidentes()
    AlmacenDePrueba.sin_corridas = False
    DominioDePrueba.pedidos = []
    app.dependency_overrides[almacen] = AlmacenDePrueba
    app.dependency_overrides[dominio] = DominioDePrueba
    yield TestClient(app)
    app.dependency_overrides.clear()
