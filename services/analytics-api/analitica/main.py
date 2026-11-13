"""La interfaz analítica: la salud, las cuatro rutas de T058 y las nueve de T069.

    uvicorn analitica.main:app --port 8000      # desde services/analytics-api, con el .env cargado

Rutas, de analitica.yaml 0.2.1:
  GET  /api/v1/entidades                       listarEntidades       sin sesión
  GET  /api/v1/articulos                       buscarArticulos       sin sesión
  GET  /api/v1/precios                         compararPrecios       sin sesión
  POST /api/v1/canastas/costo                  costearCanasta        sin sesión
  GET  /api/v1/anomalias                       articulosAnomalos     x-rol: ANALISTA
  GET  /api/v1/articulos/serie                 serieDeArticulo       x-rol: ANALISTA
  GET  /api/v1/articulos/establecimientos      desgloseDeArticulo    x-rol: ANALISTA
  GET  /api/v1/operacion/estado                estadoDeLaPlataforma  x-rol: OPERADOR
  GET  /api/v1/operacion/corridas              listarCorridas        x-rol: OPERADOR
  GET  /api/v1/operacion/corridas/{lote}       linajeDeLote          x-rol: OPERADOR
  GET  /api/v1/operacion/cuarentena            listarCuarentena      x-rol: OPERADOR
  GET  /api/v1/operacion/incidentes            listarIncidentes      x-rol: OPERADOR
  POST /api/v1/operacion/incidentes/{incidenteId}/cierre
                                               cerrarIncidente       x-rol: OPERADOR
"""

import datetime as dt
from contextlib import asynccontextmanager
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Path, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from . import modelos as m
from .cuenta import Dominio
from .datos import Almacen, canonica, mayusculas_sin_acentos
from .problemas import DatosInvalidos, NoSeCierra, Problema, SinDatos
from .sesion import clave_de_jwt_secret, requiere_rol, token_de_la_sesion


@asynccontextmanager
async def _arranque(_app):
    clave_de_jwt_secret()      # sin una clave válida no arranca, como el dominio (ADR 020)
    yield


app = FastAPI(title="CanastaMX · Interfaz analítica", version="0.2.1", lifespan=_arranque)


def almacen():
    return Almacen()


def dominio():
    return Dominio()


Datos = Annotated[Almacen, Depends(almacen)]
Producto = Annotated[str, Query(min_length=1)]
Quincena = Annotated[str | None, Query(pattern=m.QUINCENA)]
Limit = Annotated[int, Query(ge=1, le=100)]
Offset = Annotated[int, Query(ge=0)]
SIN_SESION = {401: {"description": "Falta la sesión o no tiene el rol que pide la ruta"}}


def _con_rol(rol):
    """Lo que lleva una ruta con `x-rol`: la dependencia, la marca en el OpenAPI y su 401."""
    return {"dependencies": [Depends(requiere_rol(rol))], "openapi_extra": {"x-rol": rol},
            "responses": SIN_SESION}


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
         operation_id="desgloseDeArticulo", tags=["Análisis"], **_con_rol("ANALISTA"))
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


# ── Los clientes, sobre la estrella (T069) ─────────────────────────────────────

@app.post("/api/v1/canastas/costo", response_model=m.CostoPorCadena,
          operation_id="costearCanasta", tags=["Consumo"])
def costear_canasta(datos: Datos, pedido: m.PedidoDeCosto):
    """La única regla de costo del sistema (P-10): cantidad por la mediana de las
    tiendas de la cadena, en la quincena más reciente de la entidad (R-09). No guarda
    nada. Un artículo sin precio en una cadena va en `null` y se cuenta en `faltan`;
    el total no lo incluye."""
    nombre, _ = _entidad(datos, pedido.entidad)
    lineas = [(_articulo(li.articulo.producto, li.articulo.presentacion), li.cantidad)
              for li in pedido.lineas]
    pares = sorted({(a.producto, a.presentacion) for a, _ in lineas})
    quincena, filas = datos.costo(nombre, pares) if nombre else (None, [])
    if quincena is None:
        raise DatosInvalidos("Revisa: entidad. No hay precios de esa entidad.")
    precios = {}
    for cadena, producto, presentacion, mediana in filas:
        precios.setdefault(cadena, {})[producto, presentacion] = mediana
    cadenas = []
    for cadena, suyos in precios.items():
        con_precio = [(a, n, suyos.get((a.producto, a.presentacion))) for a, n in lineas]
        cadenas.append(m.CostoDeCadena(
            cadena=cadena,
            total=m.Dinero.de(sum((n * p for _, n, p in con_precio if p is not None),
                                  Decimal(0))),
            faltan=sum(p is None for _, _, p in con_precio),
            lineas=[m.LineaConPrecio(articulo=a, cantidad=n,
                                     precio=None if p is None else m.Dinero.de(p))
                    for a, n, p in con_precio]))
    # Primero la cadena a la que le faltan menos artículos: un total más bajo porque
    # faltan tres no es una canasta más barata.
    cadenas.sort(key=lambda c: (c.faltan, Decimal(c.total.monto), c.cadena))
    return m.CostoPorCadena(entidad=nombre, quincena=quincena, cadenas=cadenas)


@app.get("/api/v1/anomalias", response_model=m.Anomalos, operation_id="articulosAnomalos",
         tags=["Análisis"], **_con_rol("ANALISTA"))
def articulos_anomalos(datos: Datos, entidad: str | None = None,
                       catalogo: m.Catalogo | None = None, desde: Quincena = None,
                       hasta: Quincena = None, umbral: Annotated[float, Query(ge=0)] = 0.2,
                       minimo_de_observaciones: Annotated[
                           int, Query(alias="minimoDeObservaciones", ge=1)] = 5,
                       limit: Limit = 20):
    nombre = None
    if entidad is not None:
        nombre, _ = _entidad(datos, entidad)
        if nombre is None:
            # Fuera del alcance no hay nada que examinar, y la población lo dice (P-06).
            nombre = entidad
    filas, (entidades, primera, ultima, observaciones) = datos.anomalos(
        nombre, catalogo, desde, hasta, Decimal(str(umbral)), minimo_de_observaciones, limit)
    if primera is None:          # ni `dim_fecha` tiene quincenas: la estrella está vacía
        raise SinDatos("La capa de consumo todavía no tiene datos.")
    return m.Anomalos(
        articulos=[m.ArticuloAnomalo(articulo=m.Articulo(producto=pr, presentacion=pe),
                                     entidad=e, quincena=q, variacion=float(v), observaciones=o)
                   for pr, pe, e, q, v, o in filas],
        poblacion=m.Poblacion(entidades=entidades, desde=primera, hasta=ultima,
                              observaciones=observaciones))


@app.get("/api/v1/articulos/serie", response_model=m.Serie, operation_id="serieDeArticulo",
         tags=["Análisis"], **_con_rol("ANALISTA"))
def serie_de_articulo(datos: Datos, producto: Producto, presentacion: Producto,
                      entidad: str | None = None, desde: Quincena = None,
                      hasta: Quincena = None):
    articulo = _articulo(producto, presentacion)
    nombre = None
    if entidad is not None:
        nombre, _ = _entidad(datos, entidad)
    filas = ([] if entidad is not None and nombre is None else
             datos.serie(articulo.producto, articulo.presentacion, nombre, desde, hasta))
    if not filas:
        raise SinDatos("No hay observaciones de ese artículo en esa entidad y periodo.")
    # Cada punto dice su población: su quincena, su entidad y sus observaciones.
    return m.Serie(articulo=articulo, puntos=[
        m.PuntoDeSerie(quincena=q, entidad=e, mediana=m.Dinero.de(me), p25=m.Dinero.de(p25),
                       p75=m.Dinero.de(p75), minimo=m.Dinero.de(mn), maximo=m.Dinero.de(mx),
                       observaciones=n)
        for q, e, me, p25, p75, mn, mx, n in filas])


# ── La consola, sobre el esquema de operación (T069) ───────────────────────────

@app.get("/api/v1/operacion/estado", response_model=m.EstadoDeLaPlataforma,
         response_model_exclude_none=True, operation_id="estadoDeLaPlataforma",
         tags=["Operación"], **_con_rol("OPERADOR"))
def estado_de_la_plataforma(datos: Datos):
    estado = datos.estado()
    if estado is None:           # CU-05 · 2b: se dice, en lugar de cifras en cero
        raise SinDatos("Todavía no hay ninguna corrida registrada.")
    i, ultima = estado
    return m.EstadoDeLaPlataforma(
        ultimo_dato=i["ultimo_dato"],
        # Sin fecha que medir, la frescura no aplica (CU-05 · 2a).
        frescura=m.FrescuraDelDato(estado=i["frescura_estado"] or "NO_APLICA",
                                   dias=i["frescura_dias"]),
        ultima_corrida=m.Corrida.de(ultima), filas_procesadas=i["filas_procesadas"],
        cuarentena=m.VolumenEnCuarentena(filas=i["cuarentena_filas"],
                                         porcentaje=float(i["cuarentena_porcentaje"] or 0),
                                         poblacion=i["cuarentena_poblacion"]),
        avisos_de_esquema=i["avisos_de_esquema"], incidentes_abiertos=i["incidentes_abiertos"])


@app.get("/api/v1/operacion/corridas", response_model=m.Corridas,
         response_model_exclude_none=True, operation_id="listarCorridas", tags=["Operación"],
         **_con_rol("OPERADOR"))
def listar_corridas(datos: Datos, limit: Limit = 20, offset: Offset = 0):
    total, filas = datos.corridas(limit, offset)
    return m.Corridas(corridas=[m.Corrida.de(f) for f in filas], total=total)


@app.get("/api/v1/operacion/corridas/{lote}", response_model=m.Linaje,
         response_model_exclude_none=True, operation_id="linajeDeLote", tags=["Operación"],
         **_con_rol("OPERADOR"))
def linaje_de_lote(datos: Datos, lote: str):
    filas = datos.linaje(lote)
    if not filas:
        raise SinDatos("No hay corridas de ese lote.")
    return m.Linaje(lote=lote, corridas=[m.Corrida.de(f) for f in filas])


@app.get("/api/v1/operacion/cuarentena", response_model=m.Cuarentena,
         operation_id="listarCuarentena", tags=["Operación"], **_con_rol("OPERADOR"))
def listar_cuarentena(datos: Datos, lote: str | None = None,
                      motivo: m.MotivoDeCuarentena | None = None, limit: Limit = 20,
                      offset: Offset = 0):
    total, filas = datos.cuarentena(lote, motivo, limit, offset)
    return m.Cuarentena(total=total, filas=[
        m.FilaEnCuarentena(lote=lo, motivo=mo, compuerta=c, fila=f) for lo, mo, c, f in filas])


@app.get("/api/v1/operacion/incidentes", response_model=m.Incidentes,
         operation_id="listarIncidentes", tags=["Operación"], **_con_rol("OPERADOR"))
def listar_incidentes(datos: Datos, estado: Literal["ABIERTO", "CERRADO"] | None = None,
                      severidad: m.Severidad | None = None, limit: Limit = 20,
                      offset: Offset = 0):
    total, filas = datos.incidentes(estado, severidad, limit, offset)
    return m.Incidentes(incidentes=[m.Incidente.de(f) for f in filas], total=total)


@app.post("/api/v1/operacion/incidentes/{incidenteId}/cierre", response_model=m.Incidente,
          operation_id="cerrarIncidente", tags=["Operación"],
          openapi_extra={"x-rol": "OPERADOR"}, responses=SIN_SESION)
def cerrar_incidente(datos: Datos, cierre: m.Cierre,
                     incidente_id: Annotated[str, Path(alias="incidenteId")],
                     sesion: Annotated[dict, Depends(requiere_rol("OPERADOR"))],
                     token: Annotated[str, Depends(token_de_la_sesion)],
                     cuentas: Annotated[Dominio, Depends(dominio)]):
    """La única escritura de la interfaz (P-08). Guarda la causa, la decisión, la
    fecha y el correo de quien cerró (D-11, RNF-22), y nada más de la persona."""
    # Un id que no es un bigint no es de ningún incidente.
    numero = int(incidente_id) if incidente_id.isascii() and incidente_id.isdigit() else None
    actual = datos.incidente(numero) if numero is not None and numero < 2**63 else None
    if actual is None:
        raise SinDatos("No hay un incidente con ese id.")
    incidente = m.Incidente.de(actual)
    if incidente.severidad == "AVISO":
        raise NoSeCierra("Es un aviso: los avisos informan y no se cierran (RF-13).")
    if incidente.estado != "ABIERTO":
        raise NoSeCierra("El incidente ya estaba cerrado.")
    # Antes de escribir: sin saber quién cierra no se cierra nada.
    correo = cuentas.correo(token, sesion["sub"])
    cerrado = datos.cerrar_incidente(numero, cierre.causa, cierre.decision,
                                     cierre.reprocesar_lote, correo)
    if cerrado is None:          # alguien lo cerró entre la lectura y la escritura
        raise NoSeCierra("El incidente ya estaba cerrado.")
    return m.Incidente.de(cerrado)
