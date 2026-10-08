-- ════════════════════════════════════════════════════════════════════════════
-- Esquema de operación · CanastaMX
-- Vive en postgres-analytics, aparte de la capa de consumo (P-08).
-- Documento: docs/datos/esquema-de-operacion.md
--
-- Quién escribe:
--   · la plataforma de datos CREA: corridas, pasos, cuarentena, incidentes,
--     avisos, variantes y equivalencias;
--   · la interfaz analítica sólo CIERRA incidentes y RESUELVE variantes
--     (las columnas marcadas «interfaz analítica»).
-- Nadie más escribe aquí, y esta interfaz no escribe en la capa de consumo.
--
-- Probarlo con el compose:
--   docker exec -i cmx-postgres-analytics psql -U canastamx -d canastamx_analytics \
--     < docs/datos/esquema-de-operacion.sql
-- ════════════════════════════════════════════════════════════════════════════

CREATE SCHEMA IF NOT EXISTS operacion;
SET search_path = operacion;

-- ── 1 · Catálogo de motivos ─────────────────────────────────────────────────
-- Un motivo por regla del contrato que aparta filas, detiene un lote o avisa.
-- `en_contrato = false` es un nombre propuesto que el contrato todavía no
-- declara (pendiente antes de construir la compuerta, semana del 9 de noviembre).
CREATE TABLE motivo (
  codigo       text PRIMARY KEY,
  nivel        text NOT NULL CHECK (nivel IN ('FILA', 'LOTE', 'CORRIDA')),
  efecto       text NOT NULL CHECK (efecto IN ('CUARENTENA', 'LOTE_DETENIDO', 'AVISO', 'PUBLICACION_DETENIDA')),
  regla        text NOT NULL,
  en_contrato  boolean NOT NULL,
  descripcion  text NOT NULL,
  UNIQUE (codigo, nivel)
);

INSERT INTO motivo (codigo, nivel, efecto, regla, en_contrato, descripcion) VALUES
  ('codificacion_irrecuperable', 'FILA', 'CUARENTENA', 'normalizacion.reparar_interrogantes.sin_gemelo', true,  'Un ? sin gemelo único en el diccionario'),
  ('revision_humana',            'FILA', 'CUARENTENA', 'normalizacion.reparar_interrogantes.ambiguo.empate', true, 'Un ? ambiguo con empate en la frecuencia'),
  ('fecha_fuera_de_ventana',     'FILA', 'CUARENTENA', 'columnas.fecha_registro.al_estar_fuera_de_rango', true, 'Fecha fuera de la ventana del alcance'),
  ('precio_fuera_de_rango',      'FILA', 'CUARENTENA', 'columnas.precio.al_exceder', true, 'Precio por encima del techo de su catálogo'),
  ('colision_precio_alta',       'FILA', 'CUARENTENA', 'clave_de_fila.colision_precio_alta', true, 'Grupo de la misma clave de fila con más de $50 de diferencia: va el grupo completo'),
  ('valor_requerido_vacio',      'FILA', 'CUARENTENA', 'columnas.*.valor_requerido', false, 'Vacío en una de las 13 columnas con valor requerido'),
  ('largo_excedido',             'FILA', 'CUARENTENA', 'columnas.*.largo_maximo', false, 'Texto más largo que el máximo de su columna'),
  ('tipo_invalido',              'FILA', 'CUARENTENA', 'columnas.*.tipo', false, 'Valor que no es del tipo de su columna'),
  ('archivo_ilegible',           'LOTE', 'LOTE_DETENIDO', 'archivo.codificacion.al_fallar', true, 'El archivo no se puede leer con la codificación declarada'),
  ('controles_c1',               'LOTE', 'LOTE_DETENIDO', 'archivo.codificacion.compuerta_extra', true, 'Caracteres de control C1 en el archivo'),
  ('fecha_ilegible',             'LOTE', 'LOTE_DETENIDO', 'archivo.formato_de_fecha.al_no_parsear', true, 'El formato de fecha del archivo no es el declarado'),
  ('columna_requerida_faltante', 'LOTE', 'LOTE_DETENIDO', 'columnas.*.columna_requerida', true, 'Al lote le falta una de las 15 columnas (CU-02 · 2b)'),
  ('interrogante_en_filtro',     'LOTE', 'LOTE_DETENIDO', 'CU-01 · 4a', true, 'Un ? en estado o catalogo: no se puede recortar el alcance'),
  ('filas_de_otra_quincena',     'LOTE', 'LOTE_DETENIDO', 'CU-01 · 6a', true, 'Filas que no son de la quincena del lote'),
  ('rechazo_mayor_al_umbral',    'LOTE', 'LOTE_DETENIDO', 'promocion_del_lote.rechazo_maximo', true, 'Más del 5% de las filas del lote en cuarentena (D-07)'),
  ('columnas_extra',             'LOTE', 'AVISO', 'columnas_extra.politica', true, 'Columnas que el contrato no declara: no se ingieren y el lote entra'),
  ('frescura_avisa',             'CORRIDA', 'AVISO', 'frescura.avisa_dias', true, 'El dato más reciente tiene 20 días o más'),
  ('frescura_bloquea',           'CORRIDA', 'PUBLICACION_DETENIDA', 'frescura.bloquea_dias', true, 'El dato más reciente tiene 45 días o más: la capa de consumo deja de publicarse vigente');

-- ── 2 · Corridas · CU-01, CU-02 paso 8, RF-08 ──────────────────────────────
-- Una fila por corrida. Un lote reprocesado tiene varias (CU-05 · 5a).
CREATE TABLE corrida (
  id                   bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  lote                 text NOT NULL CHECK (lote ~ '^(0[1-9]|1[0-2])-[0-9]{4}_Q[12]$'),
  quincena             text GENERATED ALWAYS AS (substr(lote, 4, 4) || '-' || substr(lote, 1, 2) || '-' || substr(lote, 9, 2)) STORED,
  archivo              text NOT NULL,
  sha256_entrada       char(64) NOT NULL,
  version_contrato     text NOT NULL,
  fecha_de_referencia  date NOT NULL,
  iniciada_en          timestamptz NOT NULL,
  terminada_en         timestamptz,
  filas_del_archivo    integer CHECK (filas_del_archivo >= 0),
  filas_leidas         integer CHECK (filas_leidas >= 0),
  filas_aceptadas      integer CHECK (filas_aceptadas >= 0),
  filas_en_cuarentena  integer CHECK (filas_en_cuarentena >= 0),
  resultado            text CHECK (resultado IN ('CORRECTA', 'CON_AVISOS', 'RECHAZADA', 'FALLIDA')),
  frescura_estado      text CHECK (frescura_estado IN ('OK', 'AVISA', 'BLOQUEA', 'NO_APLICA')),
  frescura_dias        integer,
  detalle              jsonb NOT NULL DEFAULT '{}'::jsonb,
  CHECK (terminada_en IS NULL OR terminada_en >= iniciada_en),
  CHECK (resultado IS NULL OR terminada_en IS NOT NULL),
  CHECK (filas_aceptadas + filas_en_cuarentena <= filas_leidas)
);
CREATE INDEX corrida_por_lote ON corrida (lote, iniciada_en DESC);

-- ── 3 · Pasos · el linaje de CU-05 paso 5 y RF-12 ──────────────────────────
CREATE TABLE paso (
  corrida_id           bigint NOT NULL REFERENCES corrida (id) ON DELETE CASCADE,
  orden                smallint NOT NULL CHECK (orden >= 1),
  capa                 text NOT NULL CHECK (capa IN ('ARCHIVO', 'CRUDA', 'COMPUERTA', 'INTERMEDIA', 'CONSUMO')),
  nombre               text NOT NULL,
  filas_entrada        integer CHECK (filas_entrada >= 0),
  filas_salida         integer CHECK (filas_salida >= 0),
  filas_en_cuarentena  integer NOT NULL DEFAULT 0 CHECK (filas_en_cuarentena >= 0),
  iniciado_en          timestamptz NOT NULL,
  terminado_en         timestamptz,
  resultado            text CHECK (resultado IN ('PASO', 'AVISO', 'DETENIDO', 'FALLO')),
  PRIMARY KEY (corrida_id, orden)
);

-- ── 4 · Filas en cuarentena · CU-02 3a, 4a y 5a, SLA-D-09 ──────────────────
-- `nivel` fijo en FILA y la llave compuesta impiden guardar aquí un motivo de lote.
CREATE TABLE cuarentena (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  corrida_id    bigint NOT NULL REFERENCES corrida (id),
  motivo        text NOT NULL,
  nivel         text NOT NULL DEFAULT 'FILA' CHECK (nivel = 'FILA'),
  compuerta     text NOT NULL,
  huella_fila   char(64) NOT NULL,
  grupo         text,
  fila          jsonb NOT NULL,
  detectada_en  timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (motivo, nivel) REFERENCES motivo (codigo, nivel),
  UNIQUE (corrida_id, huella_fila, motivo),
  CHECK (motivo <> 'colision_precio_alta' OR grupo IS NOT NULL)
);
CREATE INDEX cuarentena_por_corrida ON cuarentena (corrida_id, motivo);

-- ── 5 · Incidentes y avisos · CU-04, RF-13, SLA-D-05 y SLA-D-09 ────────────
CREATE TABLE incidente (
  id               bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  severidad        text NOT NULL CHECK (severidad IN ('AVISO', 'INCIDENTE')),
  corrida_id       bigint NOT NULL REFERENCES corrida (id),
  compuerta        text NOT NULL,
  motivo           text NOT NULL REFERENCES motivo (codigo),
  filas_afectadas  integer NOT NULL CHECK (filas_afectadas >= 0),
  abierto_en       timestamptz NOT NULL DEFAULT now(),
  estado           text NOT NULL CHECK (estado IN ('ABIERTO', 'CERRADO', 'INFORMATIVO')),
  -- interfaz analítica: el cierre (CU-04 pasos 5 y 6)
  cerrado_en       timestamptz,
  cerrado_por      text,
  causa            text CHECK (causa IN ('ARCHIVO_DE_LA_FUENTE', 'REGLA_DEL_CONTRATO', 'DATO_REAL_ATIPICO', 'INFRAESTRUCTURA')),
  decision         text,
  reprocesar_lote  boolean NOT NULL DEFAULT false,
  CHECK ((severidad = 'AVISO') = (estado = 'INFORMATIVO')),
  CHECK (estado <> 'CERRADO' OR (cerrado_en IS NOT NULL AND cerrado_por IS NOT NULL
                                AND causa IS NOT NULL AND decision IS NOT NULL)),
  CHECK (estado = 'CERRADO' OR (cerrado_en IS NULL AND causa IS NULL AND decision IS NULL)),
  CHECK (cerrado_en IS NULL OR cerrado_en >= abierto_en)
);
CREATE INDEX incidente_abierto ON incidente (abierto_en) WHERE estado = 'ABIERTO';

-- ── 6 · La cola de variantes · CU-06 2b y CU-14 ─────────────────────────────
CREATE TABLE variante (
  id                     bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  original_producto      text NOT NULL,
  original_presentacion  text NOT NULL,
  sugerido_producto      text NOT NULL,
  sugerido_presentacion  text NOT NULL,
  parecido               numeric(4, 3) NOT NULL CHECK (parecido BETWEEN 0 AND 1),
  cadena                 text,
  corrida_id             bigint NOT NULL REFERENCES corrida (id),
  detectada_en           timestamptz NOT NULL DEFAULT now(),
  estado                 text NOT NULL DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE', 'APROBADA', 'RECHAZADA', 'ASIGNADA')),
  -- interfaz analítica: la resolución (CU-14 paso 4, alternos 4a y 4b)
  resuelta_en            timestamptz,
  resuelta_por           text,
  asignado_producto      text,
  asignado_presentacion  text,
  UNIQUE (original_producto, original_presentacion, sugerido_producto, sugerido_presentacion),
  CHECK (estado = 'PENDIENTE' OR (resuelta_en IS NOT NULL AND resuelta_por IS NOT NULL)),
  CHECK ((estado = 'ASIGNADA') = (asignado_producto IS NOT NULL AND asignado_presentacion IS NOT NULL))
);
CREATE INDEX variante_pendiente ON variante (parecido DESC) WHERE estado = 'PENDIENTE';

-- ── 7 · El diccionario de artículos · CU-06 pasos 3 y 3a, CU-14 paso 5, RF-D10
-- Lo escribe sólo la plataforma: en cada corrida pasa aquí las variantes ya
-- resueltas, y la decisión del operador gana sobre la automática (CU-06 · 3a).
CREATE TABLE equivalencia (
  original_producto      text NOT NULL,
  original_presentacion  text NOT NULL,
  canonico_producto      text NOT NULL,
  canonico_presentacion  text NOT NULL,
  origen                 text NOT NULL CHECK (origen IN ('AUTOMATICA', 'OPERADOR')),
  variante_id            bigint REFERENCES variante (id),
  vigente_desde          timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (original_producto, original_presentacion),
  CHECK ((origen = 'OPERADOR') = (variante_id IS NOT NULL))
);

-- ── Vistas que lee la interfaz analítica ─────────────────────────────────────

-- La corrida vigente de cada lote: la última (CU-05 · 5a)
CREATE VIEW corrida_vigente AS
SELECT DISTINCT ON (lote) *
FROM corrida
ORDER BY lote, iniciada_en DESC;

-- Los seis indicadores de la consola (CU-05 · GET /api/v1/operacion/estado)
CREATE VIEW estado_de_la_plataforma AS
WITH ultima AS (
  SELECT * FROM corrida ORDER BY iniciada_en DESC LIMIT 1
), vigentes AS (
  SELECT * FROM corrida_vigente
)
SELECT
  (SELECT max(quincena) FROM vigentes WHERE resultado IN ('CORRECTA', 'CON_AVISOS'))      AS ultimo_dato,
  (SELECT frescura_estado FROM ultima)                                                       AS frescura_estado,
  (SELECT frescura_dias FROM ultima)                                                         AS frescura_dias,
  (SELECT lote FROM ultima)                                                                  AS ultima_corrida_lote,
  (SELECT resultado FROM ultima)                                                             AS ultima_corrida_resultado,
  (SELECT coalesce(sum(filas_leidas), 0) FROM vigentes)                                      AS filas_procesadas,
  (SELECT coalesce(sum(filas_en_cuarentena), 0) FROM vigentes)                               AS cuarentena_filas,
  (SELECT round(100.0 * sum(filas_en_cuarentena) / nullif(sum(filas_leidas), 0), 3) FROM vigentes) AS cuarentena_porcentaje,
  'lotes vigentes del alcance'::text                                                         AS cuarentena_poblacion,
  (SELECT count(*) FROM incidente i JOIN vigentes v ON v.id = i.corrida_id
    WHERE i.severidad = 'AVISO' AND i.motivo = 'columnas_extra')                             AS avisos_de_esquema,
  (SELECT count(*) FROM incidente WHERE estado = 'ABIERTO')                                  AS incidentes_abiertos;

-- H2 · minutos entre el inicio de la corrida y el incidente (SLA-D-05: menos de 15)
CREATE VIEW deteccion AS
SELECT i.id AS incidente_id, c.lote, c.iniciada_en, i.abierto_en,
       round(extract(epoch FROM (i.abierto_en - c.iniciada_en)) / 60.0, 2) AS minutos,
       (i.abierto_en - c.iniciada_en) < interval '15 minutes'               AS cumple_h2
FROM incidente i
JOIN corrida c ON c.id = i.corrida_id
WHERE i.severidad = 'INCIDENTE';

-- Cobertura y precisión de la cola (RF-14 · GET /api/v1/reconciliacion/cola)
-- Cobertura: variantes con decisión (automática o del operador) entre las detectadas.
-- Precisión: sugerencias que el operador aprobó entre las que revisó.
CREATE VIEW metricas_de_normalizacion AS
WITH a AS (SELECT count(*) AS n FROM equivalencia WHERE origen = 'AUTOMATICA'),
     v AS (SELECT count(*)                                      AS detectadas,
                  count(*) FILTER (WHERE estado <> 'PENDIENTE') AS revisadas,
                  count(*) FILTER (WHERE estado = 'APROBADA')   AS aprobadas,
                  count(*) FILTER (WHERE estado = 'PENDIENTE')  AS en_cola
           FROM variante)
SELECT a.n + v.revisadas                                                       AS cobertura_numerador,
       a.n + v.detectadas                                                      AS cobertura_denominador,
       round(100.0 * (a.n + v.revisadas) / nullif(a.n + v.detectadas, 0), 1)  AS cobertura_porcentaje,
       v.aprobadas                                                             AS precision_numerador,
       v.revisadas                                                             AS precision_denominador,
       round(100.0 * v.aprobadas / nullif(v.revisadas, 0), 1)                 AS precision_porcentaje,
       v.en_cola,
       'variantes detectadas en todas las corridas'::text                     AS poblacion
FROM a, v;
