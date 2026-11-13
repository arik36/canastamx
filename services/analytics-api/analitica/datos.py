"""Lo que la interfaz lee de `postgres-analytics`, y su única escritura.

- **La capa intermedia de T048** (`intermedia.observacion`), para las cuatro rutas de
  T058: el artículo se identifica por `clave_producto` y `clave_presentacion`, que
  están en la forma canónica del contrato.
- **La estrella de T053** (esquema `consumo`), para las tres de los clientes (T069):
  los agregados de `docs/datos/modelo-dimensional.md` §4, siempre por
  `articulo_canonico_key`. El artículo entra y sale por su par canónico, nunca por
  su llave (R-02).
- **El esquema de operación de T064** (esquema `operacion`), para las seis de la
  consola (T069). Aquí está la única escritura de toda la interfaz: el cierre de un
  incidente (P-08). En la capa de consumo no escribe nada.

Lo que llega en una petición se compara en la forma canónica. La normalización se
hace aquí, en Python, con la misma definición que `contracts/qqp-v1.yaml`, porque
PostgreSQL no trae `strip_accents`.

Los precios salen como `numeric` y se quedan en `Decimal`: nunca pasan por punto
flotante (P-02). Por eso el precio típico es `percentile_disc`, un precio que sí se
observó, y no `percentile_cont`, que devuelve `double precision`.
"""

import os
import re
import unicodedata

TABLA = "intermedia.observacion"
CONSUMO = "consumo"
OPERACION = "operacion"


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
    """Las consultas. Una conexión por consulta: la interfaz lee poco, y sólo
    escribe el cierre de un incidente.

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

    # ── Los clientes, sobre la estrella (T069) ─────────────────────────────────

    def costo(self, entidad, articulos):
        """(quincena, [(cadena, producto, presentacion, mediana)]).

        La quincena más reciente de la entidad y, en ella, el precio de cada artículo
        pedido en cada cadena que lo tiene: la mediana de sus tiendas (R-09). Una
        cadena sin ninguno de los artículos no sale.
        """
        agregado = f"{CONSUMO}.agg_articulo_cadena_entidad_quincena"
        quincena = self.consulta(f"SELECT max(quincena) FROM {agregado} WHERE entidad = %s",
                                 (entidad,))[0][0]
        if quincena is None or not articulos:
            return quincena, []
        filas = self.consulta(f"""
            SELECT c.cadena_comercial, a.producto_c, a.presentacion_c, g.mediana
            FROM {agregado} g
            JOIN {CONSUMO}.dim_articulo a ON a.articulo_canonico_key = g.articulo_canonico_key
            JOIN {CONSUMO}.dim_cadena c ON c.cadena_key = g.cadena_key
            WHERE g.entidad = %(entidad)s AND g.quincena = %(quincena)s
              AND (a.producto_c, a.presentacion_c) IN (
                    SELECT * FROM unnest(%(productos)s::text[], %(presentaciones)s::text[]))
            ORDER BY 1, 2, 3""",
            {"entidad": entidad, "quincena": quincena,
             "productos": [a[0] for a in articulos],
             "presentaciones": [a[1] for a in articulos]})
        return quincena, filas

    def _pares(self):
        """El SQL de P-15: cada artículo en cada entidad y quincena del periodo,
        contra su quincena anterior.

        «Anterior» es la quincena de calendario anterior (`dim_fecha` las tiene
        todas), no la última con dato: si el artículo no se observó en ella, no hay
        con qué comparar. Por eso el periodo se recorta después de mirar hacia atrás:
        la primera quincena pedida se compara con la que está justo antes.
        """
        return f"""
            WITH orden AS (
                SELECT quincena, row_number() OVER (ORDER BY quincena) AS i
                FROM (SELECT DISTINCT quincena FROM {CONSUMO}.dim_fecha) q),
            universo AS (
                SELECT g.articulo_canonico_key AS articulo, g.entidad, g.quincena, g.n,
                       g.mediana, o.i
                FROM {CONSUMO}.agg_articulo_entidad_quincena g
                JOIN orden o ON o.quincena = g.quincena
                WHERE (%(entidad)s::text IS NULL OR g.entidad = %(entidad)s)
                  AND (%(catalogo)s::text IS NULL OR g.articulo_canonico_key IN (
                        SELECT articulo_key FROM {CONSUMO}.dim_articulo
                        WHERE catalogo_principal = %(catalogo)s))),
            con_la_anterior AS (
                SELECT u.*, lag(u.mediana) OVER w AS mediana_anterior,
                       lag(u.n) OVER w AS n_anterior, lag(u.i) OVER w AS i_anterior
                FROM universo u
                WINDOW w AS (PARTITION BY u.articulo, u.entidad ORDER BY u.i)),
            pares AS (
                SELECT articulo, entidad, quincena, mediana / mediana_anterior - 1 AS variacion,
                       least(n, n_anterior) AS observaciones
                FROM con_la_anterior
                WHERE i_anterior = i - 1 AND mediana_anterior > 0
                  AND least(n, n_anterior) >= %(minimo)s
                  AND (%(desde)s::text IS NULL OR quincena >= %(desde)s)
                  AND (%(hasta)s::text IS NULL OR quincena <= %(hasta)s))"""

    def anomalos(self, entidad, catalogo, desde, hasta, umbral, minimo, limit):
        """([(producto, presentacion, entidad, quincena, variacion, obs)], poblacion).

        P-15: la variación de la mediana de un artículo en una entidad contra la
        quincena anterior, cuando pasa del umbral en valor absoluto y las dos
        quincenas tienen al menos `minimo` observaciones. El catálogo es el
        principal del artículo.

        De la más reciente a la más antigua y, dentro de una quincena, la mayor
        variación primero. `limit` en None las trae todas.

        `poblacion` dice lo que se examinó: (entidades, desde, hasta, observaciones).
        Si con ese filtro no hay nada, las entidades salen vacías y el periodo es el
        pedido o, si no se pidió, la ventana de `dim_fecha`.
        """
        p = {"entidad": entidad, "catalogo": catalogo, "desde": desde, "hasta": hasta,
             "umbral": umbral, "minimo": minimo, "limit": limit}
        filas = self.consulta(f"""{self._pares()}
            SELECT a.producto_c, a.presentacion_c, x.entidad, x.quincena, x.variacion,
                   x.observaciones
            FROM (SELECT articulo, entidad, quincena, round(variacion, 4) AS variacion,
                         observaciones
                  FROM pares WHERE abs(variacion) > %(umbral)s
                  ORDER BY quincena DESC, abs(variacion) DESC, articulo, entidad
                  LIMIT %(limit)s) x
            JOIN {CONSUMO}.dim_articulo a ON a.articulo_key = x.articulo
            ORDER BY x.quincena DESC, abs(x.variacion) DESC, x.articulo, x.entidad""", p)
        poblacion = self.consulta(f"""
            WITH periodo AS (
                SELECT g.entidad, g.quincena, g.n
                FROM {CONSUMO}.agg_articulo_entidad_quincena g
                WHERE (%(entidad)s::text IS NULL OR g.entidad = %(entidad)s)
                  AND (%(catalogo)s::text IS NULL OR g.articulo_canonico_key IN (
                        SELECT articulo_key FROM {CONSUMO}.dim_articulo
                        WHERE catalogo_principal = %(catalogo)s))
                  AND (%(desde)s::text IS NULL OR g.quincena >= %(desde)s)
                  AND (%(hasta)s::text IS NULL OR g.quincena <= %(hasta)s))
            SELECT (SELECT coalesce(array_agg(DISTINCT entidad ORDER BY entidad), '{{}}')
                    FROM periodo),
                   coalesce((SELECT min(quincena) FROM periodo), %(desde)s,
                            (SELECT min(quincena) FROM {CONSUMO}.dim_fecha)),
                   coalesce((SELECT max(quincena) FROM periodo), %(hasta)s,
                            (SELECT max(quincena) FROM {CONSUMO}.dim_fecha)),
                   (SELECT coalesce(sum(n), 0) FROM periodo)""", p)[0]
        return filas, poblacion

    def comparaciones(self, minimo):
        """Cuántas parejas de quincenas seguidas cumplen el mínimo, en todo el alcance:
        el denominador para calibrar P-15. Ninguna ruta lo pide."""
        return self.consulta(f"{self._pares()} SELECT count(*) FROM pares",
                             {"entidad": None, "catalogo": None, "desde": None, "hasta": None,
                              "minimo": minimo})[0][0]

    def serie(self, producto, presentacion, entidad, desde, hasta):
        """[(quincena, entidad, mediana, p25, p75, minimo, maximo, n)], en orden."""
        return self.consulta(f"""
            SELECT g.quincena, g.entidad, g.mediana, g.p25, g.p75, g.minimo, g.maximo, g.n
            FROM {CONSUMO}.agg_articulo_entidad_quincena g
            JOIN {CONSUMO}.dim_articulo a ON a.articulo_canonico_key = g.articulo_canonico_key
            WHERE a.producto_c = %(producto)s AND a.presentacion_c = %(presentacion)s
              AND (%(entidad)s::text IS NULL OR g.entidad = %(entidad)s)
              AND (%(desde)s::text IS NULL OR g.quincena >= %(desde)s)
              AND (%(hasta)s::text IS NULL OR g.quincena <= %(hasta)s)
            ORDER BY g.quincena, g.entidad""",
            {"producto": producto, "presentacion": presentacion, "entidad": entidad,
             "desde": desde, "hasta": hasta})

    # ── La consola, sobre el esquema de operación (T069) ──────────────────────

    # Una corrida sin resultado todavía no termina, y el contrato no tiene cómo
    # decirla: sale en las listas cuando termina. La plataforma escribe la corrida
    # ya con su resultado, así que sólo pasa si alguien la insertó a mano.
    CORRIDA = ("lote, iniciada_en, resultado, filas_leidas, filas_aceptadas, "
               "filas_en_cuarentena, extract(epoch FROM terminada_en - iniciada_en)")
    INCIDENTE = ("i.id, i.severidad, c.lote, i.compuerta, i.motivo, i.filas_afectadas, "
                 "i.estado, i.abierto_en, i.cerrado_en, i.cerrado_por, i.causa, i.decision, "
                 "i.reprocesar_lote")

    def estado(self):
        """(indicadores, última corrida), o None si no hay ninguna corrida terminada.

        Los indicadores son las columnas de la vista `estado_de_la_plataforma`, por
        nombre: se calculan sobre los registros de las corridas, no sobre los datos
        (CU-05).
        """
        ultima = self.consulta(f"SELECT {self.CORRIDA} FROM {OPERACION}.corrida "
                               "WHERE resultado IS NOT NULL ORDER BY iniciada_en DESC, id DESC "
                               "LIMIT 1")
        if not ultima:
            return None
        columnas = ("ultimo_dato", "frescura_estado", "frescura_dias", "filas_procesadas",
                    "cuarentena_filas", "cuarentena_porcentaje", "cuarentena_poblacion",
                    "avisos_de_esquema", "incidentes_abiertos")
        vista = self.consulta(f"SELECT {', '.join(columnas)} "
                              f"FROM {OPERACION}.estado_de_la_plataforma")[0]
        return dict(zip(columnas, vista, strict=True)), ultima[0]

    def corridas(self, limit, offset):
        """(total, [corrida]): todas las corridas, de la más reciente a la más antigua."""
        tabla = f"{OPERACION}.corrida WHERE resultado IS NOT NULL"
        total = self.consulta(f"SELECT count(*) FROM {tabla}")[0][0]
        filas = self.consulta(f"SELECT {self.CORRIDA} FROM {tabla} "
                              "ORDER BY iniciada_en DESC, id DESC LIMIT %s OFFSET %s",
                              (limit, offset))
        return total, filas

    def linaje(self, lote):
        """Las corridas de un lote, en orden: la última es la vigente (CU-05 · 5a)."""
        return self.consulta(f"SELECT {self.CORRIDA} FROM {OPERACION}.corrida "
                             "WHERE lote = %s AND resultado IS NOT NULL "
                             "ORDER BY iniciada_en, id", (lote,))

    def cuarentena(self, lote, motivo, limit, offset):
        """(total, [(lote, motivo, compuerta, fila)]).

        Las filas que apartó la corrida vigente de cada lote: las mismas que cuenta
        el indicador de la consola. Las de una corrida que después se reprocesó ya no
        están apartadas.
        """
        p = {"lote": lote, "motivo": motivo, "limit": limit, "offset": offset}
        desde = f"""FROM {OPERACION}.cuarentena q
            JOIN {OPERACION}.corrida_vigente c ON c.id = q.corrida_id
            WHERE (%(lote)s::text IS NULL OR c.lote = %(lote)s)
              AND (%(motivo)s::text IS NULL OR q.motivo = %(motivo)s)"""
        total = self.consulta(f"SELECT count(*) {desde}", p)[0][0]
        filas = self.consulta(f"SELECT c.lote, q.motivo, q.compuerta, q.fila {desde} "
                              "ORDER BY c.quincena DESC, q.id "
                              "LIMIT %(limit)s OFFSET %(offset)s", p)
        return total, filas

    def incidentes(self, estado, severidad, limit, offset):
        """(total, [incidente]): incidentes y avisos, del más reciente al más antiguo."""
        p = {"estado": estado, "severidad": severidad, "limit": limit, "offset": offset}
        desde = f"""FROM {OPERACION}.incidente i
            JOIN {OPERACION}.corrida c ON c.id = i.corrida_id
            WHERE (%(estado)s::text IS NULL OR i.estado = %(estado)s)
              AND (%(severidad)s::text IS NULL OR i.severidad = %(severidad)s)"""
        total = self.consulta(f"SELECT count(*) {desde}", p)[0][0]
        filas = self.consulta(f"SELECT {self.INCIDENTE} {desde} "
                              "ORDER BY i.abierto_en DESC, i.id DESC "
                              "LIMIT %(limit)s OFFSET %(offset)s", p)
        return total, filas

    def incidente(self, incidente_id):
        """El incidente o el aviso con ese id, o None."""
        filas = self.consulta(f"SELECT {self.INCIDENTE} FROM {OPERACION}.incidente i "
                              f"JOIN {OPERACION}.corrida c ON c.id = i.corrida_id "
                              "WHERE i.id = %s", (incidente_id,))
        return filas[0] if filas else None

    def cerrar_incidente(self, incidente_id, causa, decision, reprocesar_lote, correo):
        """LA ESCRITURA de la interfaz (P-08): cierra un incidente abierto.

        Devuelve el incidente ya cerrado, o None si no estaba abierto: `estado =
        'ABIERTO'` va en el mismo UPDATE, así que de dos cierres a la vez gana uno y
        un aviso (`INFORMATIVO`) nunca se cierra. La fecha la pone la base.
        """
        filas = self.consulta(f"""
            WITH i AS (
                UPDATE {OPERACION}.incidente
                SET estado = 'CERRADO', cerrado_en = greatest(now(), abierto_en),
                    cerrado_por = %(correo)s, causa = %(causa)s, decision = %(decision)s,
                    reprocesar_lote = %(reprocesar_lote)s
                WHERE id = %(id)s AND estado = 'ABIERTO'
                RETURNING *)
            SELECT {self.INCIDENTE} FROM i JOIN {OPERACION}.corrida c ON c.id = i.corrida_id""",
            {"id": incidente_id, "causa": causa, "decision": decision,
             "reprocesar_lote": reprocesar_lote, "correo": correo})
        return filas[0] if filas else None
