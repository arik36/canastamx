-- ════════════════════════════════════════════════════════════════════════════
-- Recorrido de prueba del esquema de operación (docs/datos/esquema-de-operacion.md §5)
-- Inserta datos de ejemplo dentro de una transacción y al final la deshace:
-- no deja nada en la base. Las líneas «debe FALLAR» tienen que imprimir ERROR.
-- ════════════════════════════════════════════════════════════════════════════
\set ON_ERROR_STOP 0
\set ON_ERROR_ROLLBACK on
BEGIN;
\pset footer off
SET search_path = operacion;
\echo '── 1 · Una corrida correcta del lote 07-2026_Q2, con su linaje y su cuarentena'
INSERT INTO corrida (lote, archivo, sha256_entrada, version_contrato, fecha_de_referencia, iniciada_en, terminada_en,
  filas_del_archivo, filas_leidas, filas_aceptadas, filas_en_cuarentena, resultado, frescura_estado)
VALUES ('07-2026_Q2', 'QQP_07-2026_Q2.csv', repeat('a',64), '1.3.4', '2026-07-31',
  '2026-10-07 10:00+00', '2026-10-07 10:06+00', 312000, 70120, 69980, 140, 'CORRECTA', 'NO_APLICA');
\set primera '(SELECT id FROM corrida WHERE lote = ''07-2026_Q2'')'
INSERT INTO paso VALUES
  (:primera, 1, 'ARCHIVO',   'leer_con_codificacion_declarada', 312000, 312000, 0,   '2026-10-07 10:00+00', '2026-10-07 10:01+00', 'PASO'),
  (:primera, 2, 'COMPUERTA', 'detectar_controles_C1',            312000, 312000, 0,   '2026-10-07 10:01+00', '2026-10-07 10:01+00', 'PASO'),
  (:primera, 3, 'CRUDA',     'recortar_alcance',                 312000, 70120,  0,   '2026-10-07 10:01+00', '2026-10-07 10:02+00', 'PASO'),
  (:primera, 4, 'COMPUERTA', 'validar_contrato',                 70120,  69980,  140, '2026-10-07 10:02+00', '2026-10-07 10:05+00', 'PASO'),
  (:primera, 5, 'INTERMEDIA','promover',                         69980,  69980,  0,   '2026-10-07 10:05+00', '2026-10-07 10:06+00', 'PASO');
INSERT INTO cuarentena (corrida_id, motivo, compuerta, huella_fila, fila)
VALUES (:primera, 'precio_fuera_de_rango', 'validar_contrato', repeat('b',64), '{"producto":"HUEVO","precio":"6500.00"}');
\echo '── debe FALLAR · un motivo de lote no puede ir a la cuarentena de filas'
INSERT INTO cuarentena (corrida_id, motivo, compuerta, huella_fila, fila) VALUES (:primera, 'controles_c1', 'x', repeat('c',64), '{}');
\echo '── debe FALLAR · la colisión alta necesita su grupo'
INSERT INTO cuarentena (corrida_id, motivo, compuerta, huella_fila, fila) VALUES (:primera, 'colision_precio_alta', 'clave_de_fila', repeat('d',64), '{}');
\echo '── debe FALLAR · el lote inventado del prototipo no tiene el formato de la fuente'
INSERT INTO corrida (lote, archivo, sha256_entrada, version_contrato, fecha_de_referencia, iniciada_en) VALUES ('L-2026-Q18', 'x', repeat('e',64), '1.3.4', '2026-07-31', now());

\echo '── 2 · Una corrida rechazada del lote 06-2026_Q2: un aviso y un incidente'
INSERT INTO corrida (lote, archivo, sha256_entrada, version_contrato, fecha_de_referencia, iniciada_en, terminada_en,
  filas_leidas, filas_aceptadas, filas_en_cuarentena, resultado, frescura_estado)
VALUES ('06-2026_Q2', 'QQP_06-2026_Q2.csv', repeat('f',64), '1.3.4', '2026-07-31',
  '2026-10-07 11:00+00', '2026-10-07 11:04+00', 69000, 0, 4140, 'RECHAZADA', 'NO_APLICA');
\set rechazada '(SELECT id FROM corrida WHERE lote = ''06-2026_Q2'' AND resultado = ''RECHAZADA'')'
INSERT INTO incidente (severidad, corrida_id, compuerta, motivo, filas_afectadas, abierto_en, estado) VALUES
  ('AVISO',     :rechazada, 'deriva_de_esquema', 'columnas_extra',          0,    '2026-10-07 11:01+00', 'INFORMATIVO'),
  ('INCIDENTE', :rechazada, 'promover',          'rechazo_mayor_al_umbral', 4140, '2026-10-07 11:04+00', 'ABIERTO');
\echo '── debe FALLAR · cerrar un incidente sin causa (SLA-D-09)'
UPDATE incidente SET estado='CERRADO', cerrado_en='2026-10-07 12:00+00', cerrado_por='operador@canastamx.mx' WHERE severidad='INCIDENTE';
\echo '── debe FALLAR · cerrar un aviso (RF-13: los avisos no se cierran)'
UPDATE incidente SET estado='CERRADO', cerrado_en='2026-10-07 12:00+00', cerrado_por='operador@canastamx.mx', causa='INFRAESTRUCTURA', decision='x' WHERE severidad='AVISO';

\echo '── 3 · H2 · el incidente se abrió 4 minutos después de iniciar la corrida'
SELECT incidente_id, lote, minutos, cumple_h2 FROM deteccion;
\echo '── el operador lo cierra bien (CU-04 · 5 y 6)'
UPDATE incidente SET estado='CERRADO', cerrado_en='2026-10-07 12:00+00', cerrado_por='operador@canastamx.mx',
  causa='ARCHIVO_DE_LA_FUENTE', decision='La fuente publicó precios con un cero de más; se reprocesa cuando corrija', reprocesar_lote=true WHERE severidad='INCIDENTE';
\echo '── y el lote se reprocesa: ahora es correcto'
INSERT INTO corrida (lote, archivo, sha256_entrada, version_contrato, fecha_de_referencia, iniciada_en, terminada_en,
  filas_leidas, filas_aceptadas, filas_en_cuarentena, resultado, frescura_estado)
VALUES ('06-2026_Q2', 'QQP_06-2026_Q2_corregido.csv', repeat('9',64), '1.3.4', '2026-07-31',
  '2026-10-08 09:00+00', '2026-10-08 09:05+00', 69000, 68900, 100, 'CORRECTA', 'NO_APLICA');
SELECT lote, quincena, resultado, iniciada_en::date FROM corrida_vigente ORDER BY lote;
\echo '── el historial del incidente quedó completo'
SELECT severidad, motivo, estado, causa, cerrado_por, reprocesar_lote FROM incidente ORDER BY id;

\echo '── 4 · La cola: tres variantes y su resolución'
INSERT INTO variante (original_producto, original_presentacion, sugerido_producto, sugerido_presentacion, parecido, cadena, corrida_id) VALUES
  ('JITOMATE SALADET', 'KG',  'JITOMATE SALADETTE', 'KG',  0.940, 'SORIANA', :primera),
  ('ACEITE VEGETAL',   '1 L', 'ACEITE VEGETAL',     '900 ML', 0.880, 'WALMART', :primera),
  ('CEBOLLA BLANCA',   'KG',  'CEBOLLA',            'KG',  0.810, 'CHEDRAUI', :primera),
  ('FRIJOL NEGRO',     '1 KG','FRIJOL NEGRO',       '900 G', 0.790, 'BODEGA AURRERA', :primera);
\echo '── debe FALLAR · asignar a mano sin decir a qué artículo'
UPDATE variante SET estado='ASIGNADA', resuelta_en=now(), resuelta_por='operador@canastamx.mx' WHERE id=3;
UPDATE variante SET estado='APROBADA',  resuelta_en=now(), resuelta_por='operador@canastamx.mx' WHERE id=1;
UPDATE variante SET estado='RECHAZADA', resuelta_en=now(), resuelta_por='operador@canastamx.mx' WHERE id=2;
UPDATE variante SET estado='ASIGNADA',  resuelta_en=now(), resuelta_por='operador@canastamx.mx',
  asignado_producto='CEBOLLA BLANCA', asignado_presentacion='KG' WHERE id=3;
INSERT INTO equivalencia (original_producto, original_presentacion, canonico_producto, canonico_presentacion, origen)
SELECT 'AUTO ' || g, 'KG', 'CANONICO ' || g, 'KG', 'AUTOMATICA' FROM generate_series(1, 8) g;
INSERT INTO equivalencia (original_producto, original_presentacion, canonico_producto, canonico_presentacion, origen, variante_id) VALUES
  ('JITOMATE SALADET', 'KG', 'JITOMATE SALADETTE', 'KG', 'OPERADOR', 1),
  ('CEBOLLA BLANCA',   'KG', 'CEBOLLA BLANCA',     'KG', 'OPERADOR', 3);
SELECT cobertura_numerador AS cub, cobertura_denominador AS det, cobertura_porcentaje AS "cobertura %",
       precision_numerador AS apr, precision_denominador AS rev, precision_porcentaje AS "precisión %", en_cola, poblacion FROM metricas_de_normalizacion;

\echo '── 5 · Los seis indicadores de la consola'
\x on
SELECT * FROM estado_de_la_plataforma;
\x off
ROLLBACK;
\echo '── Listo: la transacción se deshizo y la base quedó como estaba.'
