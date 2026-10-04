# CU-05 · Consultar el estado de la plataforma de datos

- **Actor primario:** operador de datos
- **Interesados:**
  - **Analista** — si la última corrida fue buena, puede confiar en lo que ve.
  - **Responsable de infraestructura (B)** — un servicio caído se nota primero
    aquí.
  - **Asesor y jurado** — la consola es donde se demuestra que la calidad se vigila.
- **Precondiciones:**
  1. Existe al menos una corrida registrada.
  2. El operador tiene una sesión con rol de operador en la consola web.
- **Disparador:** el operador abre la consola de observabilidad.

## Flujo principal

1. El operador abre la consola.
2. El sistema muestra seis indicadores:
   - la fecha del dato más reciente y su frescura;
   - la última corrida y su resultado;
   - las filas procesadas;
   - el volumen en cuarentena del alcance, con su porcentaje;
   - los avisos de esquema;
   - los incidentes abiertos.
3. El operador confirma que la última corrida fue correcta y que no hay incidentes
   abiertos.
4. El operador elige un lote para ver su detalle.
5. El sistema muestra el linaje del lote: de qué archivo vino, qué compuertas pasó
   y cuántas filas quedaron en cada capa.

## Flujos alternos

**2a · El corpus está congelado**
1. El sistema muestra la frescura como «no aplica: la fuente no publica desde
   2026-07-Q2», sin alarma.
2. Continúa en el paso 3.

**2b · No hay corridas registradas**
1. El sistema lo dice con un mensaje, en lugar de mostrar cifras en cero.
2. El caso de uso termina.

**3a · Hay incidentes abiertos**
1. El operador abre uno.
2. Continúa en CU-04.

**5a · El lote se reprocesó**
1. El sistema muestra todas sus corridas en orden, con la última como vigente.
2. Continúa en el paso 5.

## Postcondiciones

- **De éxito:** el operador conoce el estado de cada capa y del último lote. Los
  datos no cambiaron, porque es una consulta.
- **De fallo:** la consola no responde y el operador no puede confirmar el estado;
  lo reporta a infraestructura. Los datos no cambiaron.

## Requisito no funcional asociado

- El estado se confirma **en menos de 3 segundos** al abrir la consola (inventario
  de vistas, vista 4).
- Los indicadores se calculan sobre los registros de las corridas, no sobre los
  datos.

## Notas

- Es la vista 4 del inventario (consola de observabilidad, cliente web de D).
- Toda cifra va con su población. Hoy la cuarentena del alcance es **como máximo
  de 5,992 filas, el 0.23%** (T031).
