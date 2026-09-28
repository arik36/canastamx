# CU-13 · Analizar la evolución de precios y detectar una anomalía

- **Actor primario:** analista
- **Interesados:** 
  - **Analista** — necesita identificar tendencias atípicas en el mercado para reportarlas.
  - **Operador de datos** — necesita que los hallazgos se basen en datos que ya pasaron por la limpieza, no en errores de sistema.
- **Precondiciones:** 
  1. El sistema cuenta con los datos de la quincena procesados y publicados en la capa de consumo.
  2. Los datos del Índice Nacional de Precios al Consumidor (INPC) están actualizados en el sistema.
- **Disparador:** El analista requiere investigar el comportamiento macroeconómico de una quincena específica.

## Flujo principal

1. El analista filtra la información por fecha, catálogo y entidad federativa.
2. El sistema presenta la comparativa del índice de la canasta propia contra el INPC.
3. El analista identifica un artículo con comportamiento anómalo en el reporte de variaciones.
4. El analista solicita visualizar el detalle específico del artículo anómalo.
5. El sistema despliega la serie histórica y el desglose de precios máximos, mínimos y promedios por establecimiento.
6. El analista solicita la exportación de la muestra de datos del artículo.
7. El sistema genera y descarga un archivo estructurado con los registros del artículo.

## Flujos alternos

**1a · El filtro no devuelve datos**
1. El sistema notifica que no existen registros para la combinación de fecha y catálogo seleccionada.
2. Vuelve al paso 1.

**1b · La entidad elegida no tiene cobertura**
1. El sistema advierte que la fuente original no cuenta con datos recolectados para esa entidad federativa específica.
2. Vuelve al paso 1.

**6a · La exportación falla**
1. El sistema registra un error interno y notifica al usuario que no se pudo construir el archivo.
2. Vuelve al paso 5 · o · el caso de uso termina sin éxito.

## Postcondiciones

- **De éxito:** El analista obtiene la vista detallada de la anomalía de mercado y un archivo exportado con la evidencia.
- **De fallo:** El analista no logra visualizar los datos filtrados o no obtiene el archivo exportado, dejando el análisis incompleto.

## Requisito no funcional asociado

- El tablero analítico debe pintar los resultados iniciales del filtrado en menos de 3 segundos.

## Notas

- Una anomalía de mercado significa que el dato almacenado es correcto pero el precio es atípico (ej. el huevo subió 27% en Jalisco). Esto es distinto a un incidente de sistema.
