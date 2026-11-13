"""Los esquemas de analitica.yaml 0.2.1 que usan las rutas (ADR 017): las cuatro de
T058, las seis de la consola y las tres de los clientes (T069).

`camelCase` sale del alias, y el dinero sale siempre de `Dinero.de()`, que redondea
un `Decimal` a centavos: así P-02 no depende de acordarse en cada ruta.
"""

import datetime as dt
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

QUINCENA = r"^\d{4}-(0[1-9]|1[0-2])-Q[12]$"
Catalogo = Literal["BASICOS", "PACIC", "FRUTAS Y LEGUMBRES", "MERCADOS",
                   "PESCADOS Y MARISCOS"]


class Modelo(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class Salud(Modelo):
    status: Literal["UP"] = "UP"
    service: str
    time: dt.datetime


class Dinero(Modelo):
    monto: str = Field(pattern=r"^\d+\.\d{2}$")
    moneda: Literal["MXN"] = "MXN"

    @classmethod
    def de(cls, valor):
        return cls(monto=str(Decimal(valor).quantize(Decimal("0.01"), ROUND_HALF_UP)))


class Articulo(Modelo):
    producto: str
    presentacion: str


class Poblacion(Modelo):
    entidades: list[str]
    desde: str = Field(pattern=QUINCENA)
    hasta: str = Field(pattern=QUINCENA)
    observaciones: int = Field(ge=0)


class EntidadConDatos(Modelo):
    entidad: str
    ultima_quincena: str = Field(pattern=QUINCENA)


class Entidades(Modelo):
    entidades: list[EntidadConDatos]


class Encontrado(Modelo):
    articulo: Articulo
    nombre: str
    catalogo: Catalogo
    precio_tipico: Dinero
    observaciones: int = Field(ge=1)


class ResultadoDeBusqueda(Modelo):
    cobertura: bool
    entidad: str
    entidades_cubiertas: list[str] | None = None
    quincena: str | None = Field(default=None, pattern=QUINCENA)
    total: int | None = Field(default=None, ge=0)
    resultados: list[Encontrado] | None = None


class PrecioEnEstablecimiento(Modelo):
    nombre: str
    direccion: str | None = None
    municipio: str | None = None
    cadena: str
    marca: str
    precio: Dinero
    fecha_registro: dt.date


class ComparacionDePrecios(Modelo):
    articulo: Articulo
    entidad: str
    quincena: str = Field(pattern=QUINCENA)
    establecimientos: list[PrecioEnEstablecimiento]


class DesgloseDeEstablecimiento(Modelo):
    nombre: str
    cadena: str
    maximo: Dinero
    minimo: Dinero
    promedio: Dinero
    observaciones: int = Field(ge=1)


class Desglose(Modelo):
    establecimientos: list[DesgloseDeEstablecimiento]
    poblacion: Poblacion


# ── Los clientes: la canasta, las anomalías y la serie (T069) ───────────────

class LineaDePedido(Modelo):
    articulo: Articulo
    cantidad: int = Field(ge=1)


class PedidoDeCosto(Modelo):
    entidad: str
    lineas: list[LineaDePedido] = Field(max_length=200)


class LineaConPrecio(Modelo):
    articulo: Articulo
    cantidad: int
    precio: Dinero | None      # null es «sin precio»: nunca un monto (R-09)


class CostoDeCadena(Modelo):
    cadena: str
    total: Dinero
    faltan: int = Field(ge=0)
    lineas: list[LineaConPrecio]


class CostoPorCadena(Modelo):
    entidad: str
    quincena: str = Field(pattern=QUINCENA)
    cadenas: list[CostoDeCadena]


class ArticuloAnomalo(Modelo):
    articulo: Articulo
    entidad: str
    quincena: str = Field(pattern=QUINCENA)
    variacion: float
    observaciones: int


class Anomalos(Modelo):
    articulos: list[ArticuloAnomalo]
    poblacion: Poblacion


class PuntoDeSerie(Modelo):
    quincena: str = Field(pattern=QUINCENA)
    entidad: str
    mediana: Dinero
    p25: Dinero
    p75: Dinero
    minimo: Dinero
    maximo: Dinero
    observaciones: int = Field(ge=1)


class Serie(Modelo):
    articulo: Articulo
    puntos: list[PuntoDeSerie]


# ── La consola: el esquema de operación (T069) ──────────────────────────────

Resultado = Literal["CORRECTA", "CON_AVISOS", "RECHAZADA", "FALLIDA"]
Frescura = Literal["OK", "AVISA", "BLOQUEA", "NO_APLICA"]
Severidad = Literal["AVISO", "INCIDENTE"]
Causa = Literal["ARCHIVO_DE_LA_FUENTE", "REGLA_DEL_CONTRATO", "DATO_REAL_ATIPICO",
                "INFRAESTRUCTURA"]
# Los ocho motivos de nivel FILA de `operacion.motivo`. `test_rutas.py` comprueba
# que sean los del `enum` del contrato.
MotivoDeCuarentena = Literal[
    "codificacion_irrecuperable", "revision_humana", "fecha_fuera_de_ventana",
    "precio_fuera_de_rango", "colision_precio_alta", "valor_requerido_vacio",
    "largo_excedido", "tipo_invalido"]


class Corrida(Modelo):
    lote: str
    fecha: dt.datetime                     # cuándo empezó: `corrida.iniciada_en`
    resultado: Resultado
    filas_leidas: int
    filas_aceptadas: int
    filas_en_cuarentena: int
    duracion_segundos: float | None = None

    @classmethod
    def de(cls, fila):
        """De (lote, iniciada_en, resultado, leídas, aceptadas, en cuarentena, segundos)."""
        lote, fecha, resultado, leidas, aceptadas, apartadas, segundos = fila
        return cls(lote=lote, fecha=fecha, resultado=resultado, filas_leidas=leidas or 0,
                   filas_aceptadas=aceptadas or 0, filas_en_cuarentena=apartadas or 0,
                   duracion_segundos=None if segundos is None else float(segundos))


class Corridas(Modelo):
    corridas: list[Corrida]
    total: int


class Linaje(Modelo):
    lote: str
    corridas: list[Corrida]


class FrescuraDelDato(Modelo):
    estado: Frescura
    dias: int | None = None


class VolumenEnCuarentena(Modelo):
    filas: int
    porcentaje: float
    poblacion: str


class EstadoDeLaPlataforma(Modelo):
    # Sólo falta si ningún lote ha pasado todavía: no hay dato del que decir la fecha.
    ultimo_dato: str | None = Field(default=None, pattern=QUINCENA)
    frescura: FrescuraDelDato
    ultima_corrida: Corrida
    filas_procesadas: int
    cuarentena: VolumenEnCuarentena
    avisos_de_esquema: int
    incidentes_abiertos: int


class FilaEnCuarentena(Modelo):
    lote: str
    motivo: MotivoDeCuarentena
    compuerta: str
    fila: dict


class Cuarentena(Modelo):
    filas: list[FilaEnCuarentena]
    total: int


class Incidente(Modelo):
    id: str
    severidad: Severidad
    lote: str
    compuerta: str
    motivo: str
    filas: int
    estado: Literal["ABIERTO", "CERRADO", "INFORMATIVO"]
    abierto_en: dt.datetime
    cerrado_en: dt.datetime | None = None
    cerrado_por: str | None = None
    causa: str | None = None
    decision: str | None = None
    reprocesar_lote: bool = False

    @classmethod
    def de(cls, fila):
        """De las columnas de `Almacen.INCIDENTE`, en su orden."""
        campos = ("id", "severidad", "lote", "compuerta", "motivo", "filas", "estado",
                  "abierto_en", "cerrado_en", "cerrado_por", "causa", "decision",
                  "reprocesar_lote")
        return cls(**{**dict(zip(campos, fila, strict=True)), "id": str(fila[0])})


class Incidentes(Modelo):
    incidentes: list[Incidente]
    total: int


class Cierre(Modelo):
    """El cuerpo de `cerrarIncidente`. Quién cierra y cuándo no vienen aquí: el
    correo sale de la cuenta de la sesión (D-11) y la fecha la pone la base."""
    causa: Causa
    decision: str
    reprocesar_lote: bool = False

    @field_validator("decision")
    @classmethod
    def _con_texto(cls, valor):
        # SLA-D-09: el 100% de los incidentes cerrados tiene escrito qué se hizo.
        if not valor.strip():
            raise ValueError("la decisión no puede ir vacía")
        return valor.strip()
