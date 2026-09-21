-- pesar-en-postgres.sql · generado por medir-el-peso.py
--
-- Carga la muestra en una tabla temporal, le pone los mismos índices que va a
-- llevar el esquema estrella y reporta cuánto ocupa cada cosa. Es la única
-- medición que se puede defender: lo demás son estimaciones.
--
-- Cómo correrlo, desde la raíz del repositorio y con los contenedores arriba:
--
--   docker compose cp docs/datos/perfilado/salidas/muestra-para-pesar.csv \
--     postgres-analytics:/tmp/muestra.csv
--   docker compose cp docs/datos/perfilado/salidas/pesar-en-postgres.sql \
--     postgres-analytics:/tmp/pesar.sql
--   docker compose exec postgres-analytics \
--     psql -U $POSTGRES_USER -d $POSTGRES_DB -f /tmp/pesar.sql

DROP TABLE IF EXISTS peso_muestra;

CREATE TABLE peso_muestra (
  producto          text,
  presentacion      text,
  marca             text,
  categoria         text,
  cadena_comercial  text,
  giro              text,
  nombre_comercial  text,
  direccion         text,
  estado            text,
  municipio         text,
  catalogo          text,
  fecha_registro    date,
  latitud           double precision,
  longitud          double precision,
  precio            numeric(12,2)
);

COPY peso_muestra FROM '/tmp/muestra.csv' WITH (FORMAT csv, HEADER true);

-- Sin índices todavía: cuánto pesa el puro montón.
SELECT 'solo la tabla'                             AS que,
       count(*)                                    AS filas,
       pg_size_pretty(pg_relation_size('peso_muestra'))       AS tamano,
       pg_relation_size('peso_muestra')::float / count(*)     AS bytes_por_fila
  FROM peso_muestra;

-- Los índices que el modelo sí va a necesitar.
CREATE INDEX ix_peso_clave_de_fila ON peso_muestra
  (producto, presentacion, marca, nombre_comercial, direccion, fecha_registro);
CREATE INDEX ix_peso_articulo ON peso_muestra (producto, presentacion);
CREATE INDEX ix_peso_fecha    ON peso_muestra (fecha_registro);
ANALYZE peso_muestra;

SELECT 'tabla + indices'                                       AS que,
       pg_size_pretty(pg_relation_size('peso_muestra'))         AS solo_tabla,
       pg_size_pretty(pg_indexes_size('peso_muestra'))          AS solo_indices,
       pg_size_pretty(pg_total_relation_size('peso_muestra'))   AS total;

-- Cada índice por separado: el de la clave de fila suele ser el caro.
SELECT indexrelname                                AS indice,
       pg_size_pretty(pg_relation_size(indexrelid)) AS tamano
  FROM pg_stat_user_indexes
 WHERE relname = 'peso_muestra'
 ORDER BY pg_relation_size(indexrelid) DESC;

-- Multiplica el total por  (FILAS_DEL_ALCANCE / filas_de_la_muestra)  y ése es
-- el número que va al ADR 006. Postgres crece casi lineal con las filas, así
-- que extrapolar aquí es honesto.
