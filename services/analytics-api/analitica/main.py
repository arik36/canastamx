"""La interfaz analítica: las cuatro rutas de T058 y la salud.

    uvicorn analitica.main:app --port 8000      # desde services/analytics-api, con el .env cargado

Rutas, de analitica.yaml 0.2.1:
  GET /api/v1/entidades                  listarEntidades     sin sesión
  GET /api/v1/articulos                  buscarArticulos     sin sesión
  GET /api/v1/precios                    compararPrecios     sin sesión
  GET /api/v1/articulos/establecimientos desgloseDeArticulo  x-rol: ANALISTA
"""

import datetime as dt
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from . import modelos as m
from .datos import Almacen, canonica, mayusculas_sin_acentos
from .problemas import DatosInvalidos, Problema, SinDatos
from .sesion import clave_de_jwt_secret, requiere_rol


@asynccontextmanager
async def _arranque(_app):
    clave_de_jwt_secret()      # sin una clave válida no arranca, como el dominio (ADR 020)
    yield


app = FastAPI(title="CanastaMX · Interfaz analítica", version="0.2.1", lifespan=_arranque)


def almacen():
    return Almacen()


Datos = Annotated[Almacen, Depends(almacen)]
Producto = Annotated[str, Query(min_length=1)]
Quincena = Annotated[str | None, Query(pattern=m.QUINCENA)]


@app.exception_handler(Problema)
async def _problema(_peticion, e):
    return JSONResponse(e.cuerpo(), status_code=e.status, media_type="application/problem+json")


@app.exception_handler(RequestValidationError)
async def _invalidos(_peticion, e):
    campos = sorted({str(error["loc"][-1]) for error in e.errors()})
    return await _problema(None, DatosInvalidos(f"Revisa: {', '.join(campos)}."))


def _entidad(datos, texto):
    """El nombre con que la capa guarda la entidad, sin importar mayúsculas ni acentos."""
    cubiertas = [e for e, _ in datos.entidades()]
    buscada = mayusculas_sin_acentos(texto)
    return next((e for e in cubiertas if mayusculas_sin_acentos(e) == buscada), None), cubiertas


def _articulo(producto, presentacion):
    return m.Articulo(producto=canonica(producto), presentacion=canonica(presentacion))


@app.get("/health", response_model=m.Salud, operation_id="salud", tags=["Salud"])
def salud():
    return m.Salud(service="analytics-api", time=dt.datetime.now(dt.UTC))


@app.get("/api/v1/entidades", response_model=m.Entidades, operation_id="listarEntidades",
         tags=["Consumo"])
def listar_entidades(datos: Datos):
    return m.Entidades(entidades=[m.EntidadConDatos(entidad=e, ultima_quincena=q)
                                  for e, q in datos.entidades()])


@app.get("/api/v1/articulos", response_model=m.ResultadoDeBusqueda,
         response_model_exclude_none=True, operation_id="buscarArticulos", tags=["Consumo"])
def buscar_articulos(datos: Datos, q: Annotated[str, Query(min_length=2)], entidad: str,
                     catalogo: m.Catalogo | None = None,
                     limit: Annotated[int, Query(ge=1, le=100)] = 20,
                     offset: Annotated[int, Query(ge=0)] = 0):
    nombre, cubiertas = _entidad(datos, entidad)
    if nombre is None:          # CU-12 · 2b: no es un error (P-06)
        return m.ResultadoDeBusqueda(cobertura=False, entidad=entidad,
                                     entidades_cubiertas=cubiertas)
    palabras = canonica(q).split()
    if not palabras:
        raise DatosInvalidos("Revisa: q. No trae letras ni números.")
    quincena, total, filas = datos.buscar(palabras, nombre, catalogo, limit, offset)
    return m.ResultadoDeBusqueda(
        cobertura=True, entidad=nombre, quincena=quincena, total=total,
        resultados=[m.Encontrado(articulo=m.Articulo(producto=pr, presentacion=pe),
                                 nombre=n, catalogo=c, precio_tipico=m.Dinero.de(p),
                                 observaciones=o)
                    for pr, pe, n, c, p, o in filas])


@app.get("/api/v1/precios", response_model=m.ComparacionDePrecios, response_model_exclude_none=True,
         operation_id="compararPrecios", tags=["Consumo"])
def comparar_precios(datos: Datos, producto: Producto, presentacion: Producto, entidad: str):
    articulo = _articulo(producto, presentacion)
    nombre, _ = _entidad(datos, entidad)
    quincena, filas = (datos.precios(articulo.producto, articulo.presentacion, nombre)
                       if nombre else (None, []))
    if not filas:
        raise SinDatos("No hay precios de ese artículo en esa entidad.")
    return m.ComparacionDePrecios(
        articulo=articulo, entidad=nombre, quincena=quincena,
        establecimientos=[m.PrecioEnEstablecimiento(
            nombre=n, direccion=d, municipio=mu, cadena=c, marca=ma, precio=m.Dinero.de(p),
            fecha_registro=f) for n, d, mu, c, ma, p, f in filas])


@app.get("/api/v1/articulos/establecimientos", response_model=m.Desglose,
         operation_id="desgloseDeArticulo", tags=["Análisis"],
         dependencies=[Depends(requiere_rol("ANALISTA"))],
         openapi_extra={"x-rol": "ANALISTA"},
         responses={401: {"description": "Falta la sesión o no tiene el rol que pide la ruta"}})
def desglose_de_articulo(datos: Datos, producto: Producto, presentacion: Producto,
                         entidad: str, desde: Quincena = None, hasta: Quincena = None):
    articulo = _articulo(producto, presentacion)
    nombre, _ = _entidad(datos, entidad)
    filas = (datos.desglose(articulo.producto, articulo.presentacion, nombre, desde, hasta)
             if nombre else [])
    if not filas:
        raise SinDatos("No hay observaciones de ese artículo en esa entidad y periodo.")
    return m.Desglose(
        establecimientos=[m.DesgloseDeEstablecimiento(
            nombre=n, cadena=c, maximo=m.Dinero.de(mx), minimo=m.Dinero.de(mn),
            promedio=m.Dinero.de(pr), observaciones=o) for n, c, mx, mn, pr, o, _, _ in filas],
        # La población es la de las filas que entraron, no la del periodo pedido.
        poblacion=m.Poblacion(entidades=[nombre], desde=min(f[6] for f in filas),
                              hasta=max(f[7] for f in filas),
                              observaciones=sum(f[5] for f in filas)))
