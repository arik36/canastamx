-- Ampliación visual de la semilla T056. Sólo para cmx-t056-oltp/t056_analytics.
-- Datos enteramente sintéticos; nunca se ejecuta sobre el despliegue público.
WITH muestra(id, producto, nombre, presentacion, catalogo, precio) AS (VALUES
 (101, 'pechuga de pollo', 'Pechuga de pollo', '1 kg', 'BASICOS', 89.90),
 (102, 'huevo blanco', 'Huevo blanco', '18 piezas', 'BASICOS', 52.90),
 (103, 'atun en agua', 'Atún en agua', '140 g', 'PACIC', 18.50),
 (104, 'arroz super extra', 'Arroz súper extra', '1 kg', 'PACIC', 24.50),
 (105, 'aceite vegetal', 'Aceite vegetal', '1 litro', 'BASICOS', 43.20),
 (106, 'jitomate saladette', 'Jitomate saladette', '1 kg', 'FRUTAS Y LEGUMBRES', 28.00),
 (107, 'chile serrano', 'Chile serrano', '1 kg', 'FRUTAS Y LEGUMBRES', 34.50),
 (108, 'sardina en tomate', 'Sardina en tomate', '425 g', 'PESCADOS Y MARISCOS', 22.00)
), articulos AS (
 INSERT INTO consumo.dim_articulo SELECT id, producto, presentacion FROM muestra ON CONFLICT DO NOTHING
), costos AS (
 INSERT INTO consumo.agg_articulo_cadena_entidad_quincena
 SELECT id, 1, 'Guanajuato', '2026-07-Q2', precio FROM muestra ON CONFLICT DO NOTHING
)
INSERT INTO intermedia.observacion
SELECT producto, presentacion, nombre, catalogo, 'Guanajuato', '2026-07-Q2',
 'Tienda de prueba Centro', 'Dirección ficticia 1', 'León', 'Cadena de prueba A', 'Marca de prueba', precio, '2026-07-24'::date FROM muestra
ON CONFLICT DO NOTHING;
