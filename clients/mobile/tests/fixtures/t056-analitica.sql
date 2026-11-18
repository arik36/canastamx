-- Semilla sintética mínima de aceptación del cliente, sólo en una base aislada.
-- Las rutas y consultas SQL son las de analytics-api; esto no acredita la ingesta.
CREATE SCHEMA IF NOT EXISTS intermedia;
CREATE SCHEMA IF NOT EXISTS consumo;
CREATE TABLE IF NOT EXISTS intermedia.observacion (
  clave_producto text, clave_presentacion text, producto text, catalogo_normalizado text,
  entidad text, quincena text, nombre_comercial text, direccion text, municipio text,
  cadena_comercial text, marca text, precio numeric(12,2), fecha_registro date,
  PRIMARY KEY (clave_producto, clave_presentacion, nombre_comercial)
);
INSERT INTO intermedia.observacion VALUES
 ('leche entera','envase de 1 litro','Leche entera','BASICOS','Guanajuato','2026-07-Q2','Tienda de prueba Centro','Dirección ficticia 1','León','Cadena de prueba A','Marca de prueba',28.50,'2026-07-24'),
 ('leche entera','envase de 1 litro','Leche entera','BASICOS','Guanajuato','2026-07-Q2','Tienda de prueba Norte','Dirección ficticia 2','León','Cadena de prueba B','Marca de prueba',30.00,'2026-07-25'),
 ('leche descremada','envase de 1 litro','Leche descremada','BASICOS','Guanajuato','2026-07-Q2','Tienda de prueba Centro','Dirección ficticia 1','León','Cadena de prueba A','Marca de prueba',32.40,'2026-07-24')
 ON CONFLICT DO NOTHING;
CREATE TABLE IF NOT EXISTS consumo.dim_articulo (articulo_canonico_key integer PRIMARY KEY, producto_c text, presentacion_c text);
CREATE TABLE IF NOT EXISTS consumo.dim_cadena (cadena_key integer PRIMARY KEY, cadena_comercial text);
CREATE TABLE IF NOT EXISTS consumo.agg_articulo_cadena_entidad_quincena (
  articulo_canonico_key integer, cadena_key integer, entidad text, quincena text, mediana numeric(12,2),
  PRIMARY KEY (articulo_canonico_key,cadena_key,entidad,quincena)
);
INSERT INTO consumo.dim_articulo VALUES (1,'leche entera','envase de 1 litro'),(2,'leche descremada','envase de 1 litro') ON CONFLICT DO NOTHING;
INSERT INTO consumo.dim_cadena VALUES (1,'Cadena de prueba A'),(2,'Cadena de prueba B') ON CONFLICT DO NOTHING;
INSERT INTO consumo.agg_articulo_cadena_entidad_quincena VALUES
 (1,1,'Guanajuato','2026-07-Q2',28.50),(1,2,'Guanajuato','2026-07-Q2',30.00),
 (2,1,'Guanajuato','2026-07-Q2',32.40) ON CONFLICT DO NOTHING;
