"""Lo que la interfaz lee de `postgres-analytics`: la capa intermedia de T048.

Sólo lee (P-08). La estrella de T053 todavía no existe, así que el artículo se
identifica por las columnas `clave_producto` y `clave_presentacion` de la capa, que
están en la forma canónica del contrato. Lo que llega en una petición se compara
en esa misma forma. La normalización se hace aquí, en Python, con la misma
definición que `contracts/qqp-v1.yaml`, porque PostgreSQL no trae `strip_accents`.

Los precios salen como `numeric` y se quedan en `Decimal`: nunca pasan por punto
flotante (P-02). Por eso el precio típico es `percentile_disc`, un precio que sí se
observó, y no `percentile_cont`, que devuelve `double precision`.
"""

import os
import re
import unicodedata

TABLA = "intermedia.observacion"


def _sin_acentos(texto):
    return "".join(c for c in unicodedata.normalize("NFKD", texto)
                   if not unicodedata.combining(c))


def canonica(texto):
    """`normalizacion.canonica` del contrato."""
    sin_signos = re.sub(r"[^a-z0-9 ]", " ", _sin_acentos(texto).lower())
    return re.sub(r"\s+", " ", sin_signos).strip()


def mayusculas_sin_acentos(texto):
    """`normalizacion.mayusculas_sin_acentos` del contrato."""
    return _sin_acentos(texto.strip()).upper()


class Almacen:
    """Las consultas. Una conexión por petición: la interfaz sólo lee, y poco.

    Se conecta con las mismas `ANALYTICS_*` del `.env` que usa la plataforma de
    datos. `ANALYTICS_HOST` es opcional; por omisión, `localhost`.
    """

    def consulta(self, sql, parametros=None):
        import psycopg

        # La contraseña va por PGPASSWORD, que libpq lee al conectarse, y no como
        # argumento. Como argumento, psycopg la mete en la cadena de conexión, y
        # pytest imprime esa cadena entre los argumentos de cada función del
        # traceback: así salió en la primera corrida contra la base real.
        os.environ["PGPASSWORD"] = os.environ["ANALYTICS_PASSWORD"]
        host = os.environ.get("ANALYTICS_HOST", "localhost")
        puerto = os.environ["ANALYTICS_PORT"]
        try:
            con = psycopg.connect(host=host, port=puerto, dbname=os.environ["ANALYTICS_DB"],
                                  user=os.environ["ANALYTICS_USER"])
        except psycopg.OperationalError as e:
            # `from None`: el traceback de psycopg no se muestra, sólo este mensaje.
            raise RuntimeError(f"no se pudo conectar a postgres-analytics "
                               f"({host}:{puerto}): {e}") from None
        with con:
            return con.execute(sql, parametros).fetchall()

    def entidades(self):
        """[(entidad, su quincena más reciente)]."""
        return self.consulta(f"SELECT entidad, max(quincena) FROM {TABLA} "
                           "GROUP BY entidad ORDER BY entidad")

    def buscar(self, palabras, entidad, catalogo, limit, offset):
        """(quincena, total, [(producto, presentacion, nombre, catalogo, precio, obs)]).

        En la quincena más reciente de la entidad. Cada palabra tiene que aparecer en
        el producto o en la presentación canónicos.
        """
        quincena = self.consulta(f"SELECT max(quincena) FROM {TABLA} WHERE entidad = %s",
                               (entidad,))[0][0]
        p = {"entidad": entidad, "quincena": quincena, "catalogo": catalogo,
             "patrones": [f"%{w}%" for w in palabras], "limit": limit, "offset": offset}
        articulos = f"""
            SELECT clave_producto, clave_presentacion,
                   mode() WITHIN GROUP (ORDER BY producto) AS nombre,
                   mode() WITHIN GROUP (ORDER BY catalogo_normalizado) AS catalogo,
                   percentile_disc(0.5) WITHIN GROUP (ORDER BY precio) AS precio_tipico,
                   count(*) AS observaciones
            FROM {TABLA}
            WHERE entidad = %(entidad)s AND quincena = %(quincena)s
              AND clave_producto || ' ' || clave_presentacion LIKE ALL (%(patrones)s)
              AND (%(catalogo)s::text IS NULL OR catalogo_normalizado = %(catalogo)s)
            GROUP BY clave_producto, clave_presentacion"""
        total = self.consulta(f"SELECT count(*) FROM ({articulos}) a", p)[0][0]
        filas = self.consulta(f"{articulos} ORDER BY observaciones DESC, nombre "
                            "LIMIT %(limit)s OFFSET %(offset)s", p)
        return quincena, total, filas

    def precios(self, producto, presentacion, entidad):
        """(quincena, [(nombre, direccion, municipio, cadena, marca, precio, fecha)]).

        La quincena más reciente del artículo en la entidad, y en ella la observación
        más reciente de cada establecimiento y marca. `S/M` va al final (ADR 002).
        """
        p = {"producto": producto, "presentacion": presentacion, "entidad": entidad}
        donde = ("clave_producto = %(producto)s AND clave_presentacion = %(presentacion)s "
                 "AND entidad = %(entidad)s")
        quincena = self.consulta(f"SELECT max(quincena) FROM {TABLA} WHERE {donde}", p)[0][0]
        if quincena is None:
            return None, []
        filas = self.consulta(f"""
            SELECT nombre, direccion, municipio, cadena, marca, precio, fecha_registro
            FROM (SELECT DISTINCT ON (nombre_comercial, direccion, marca)
                         coalesce(nombre_comercial, '') AS nombre, direccion, municipio,
                         coalesce(cadena_comercial, '') AS cadena,
                         coalesce(marca, '') AS marca, precio, fecha_registro
                  FROM {TABLA}
                  WHERE {donde} AND quincena = %(quincena)s
                  ORDER BY nombre_comercial, direccion, marca, fecha_registro DESC, precio
                 ) u
            ORDER BY upper(marca) = 'S/M', precio, nombre""", {**p, "quincena": quincena})
        return quincena, filas

    def desglose(self, producto, presentacion, entidad, desde, hasta):
        """[(nombre, cadena, maximo, minimo, promedio, obs, primera, ultima)]."""
        p = {"producto": producto, "presentacion": presentacion, "entidad": entidad,
             "desde": desde, "hasta": hasta}
        return self.consulta(f"""
            SELECT coalesce(nombre_comercial, ''), coalesce(cadena_comercial, ''),
                   max(precio), min(precio), avg(precio), count(*),
                   min(quincena), max(quincena)
            FROM {TABLA}
            WHERE clave_producto = %(producto)s AND clave_presentacion = %(presentacion)s
              AND entidad = %(entidad)s
              AND (%(desde)s::text IS NULL OR quincena >= %(desde)s)
              AND (%(hasta)s::text IS NULL OR quincena <= %(hasta)s)
            GROUP BY 1, 2 ORDER BY 1, 2""", p)
