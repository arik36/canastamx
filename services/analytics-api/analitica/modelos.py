"""Los esquemas de analitica.yaml 0.2.1 que usan las cuatro rutas (ADR 017).

`camelCase` sale del alias, y el dinero sale siempre de `Dinero.de()`, que redondea
un `Decimal` a centavos: así P-02 no depende de acordarse en cada ruta.
"""

import datetime as dt
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
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
