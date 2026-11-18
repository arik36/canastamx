# T056 · Detalle y canasta · Evidencia del 18 de noviembre de 2026

## Entorno y alcance

BlueStacks 5 con Android 11 y Expo Go SDK 55. **No se acredita teléfono físico.**
Node 20.20.2. Rama `feat/orf-canasta`, actualizada hasta `4f1faa8` antes de la entrega.
Dominio Spring Boot y analítica FastAPI reales, contra PostgreSQL 16 en una base
temporal aislada. Direcciones de prueba por proceso; no se modificó el `.env` del
usuario. La semilla es `tests/fixtures/t056-analitica.sql`: dos artículos y tres
registros sintéticos, no un conjunto de precios de producción ni una prueba de ingesta.

Se inició sesión con un consumidor sintético creado para esta prueba. Los datos
del dominio persistieron en PostgreSQL; no se utilizó un simulador de canastas.
El costo y el detalle se consultaron a la interfaz analítica real. La depuración
temporal de Android se apagó al terminar, con autorización del usuario.

## Recorrido observado

1. Búsqueda «leche» en Guanajuato: dos resultados, con precio, presentación,
   quincena 2026-07-Q2 y observaciones.
2. Leche entera abrió el detalle con dos establecimientos: 28.50 y 30.00 MXN,
   fechas 2026-07-24 y 2026-07-25, entidad, quincena y población de dos registros.
   Leche descremada mostró un establecimiento y el aviso correspondiente.
3. Desde el detalle se creó «Canasta T056» y se agregó una unidad de cada artículo.
4. En Canasta, cero mostró validación e impidió guardar. Se fijó Leche entera en
   tres y el dominio devolvió **cantidad guardada: 3**.
5. Con ambos artículos, la cadena A mostró **117.90 MXN**, sin faltantes; B,
   **90.00 MXN**, total parcial con Leche descremada sin precio.
6. Se quitó Leche descremada: quedó sólo Leche entera en tres. El costo fue
   **85.50 MXN** para A y **90.00 MXN** para B, ambos completos.
7. Se cerraron las tarjetas de CanastaMX y de Expo Go en aplicaciones recientes.
   Se abrió Expo Go desde Android y se cargó otra vez el proyecto. Recuperó la
   cuenta sin pedir credenciales y, en Canasta, «Canasta T056» con una sola línea
   de Leche entera en tres y sus costos desde los servicios.
8. Se detuvo sólo la analítica temporal: apareció el error de conexión sin
   perder la canasta. Se reinició y, con **Actualizar costo**, se recuperaron
   los datos. No se sustituyeron por precios ficticios.

## Capturas nativas

Guardadas por BlueStacks, copiadas sin edición. Conservan las superposiciones de
depuración que estaban activas durante la prueba; no son elementos de CanastaMX.

| Estado | Archivo |
|---|---|
| Canasta recuperada al reabrir, cantidad guardada en tres | [Captura](01-canasta-recuperada.png) |
| Costo recuperado, entidad, quincena y población | [Captura](02-costo-recuperado.png) |
| Analítica detenida y mensaje de conexión | [Captura](03-sin-conexion.png) |

El detalle, la edición, el total parcial y la recuperación del error se observaron
durante el recorrido; las tres capturas no pretenden representar cada uno de esos pasos.

## Verificación automática

- `npm test`: **43 pruebas aprobadas**, cero fallidas, canceladas u omitidas.
- `npm run typecheck`: correcto.
- Exportación Android con Expo: correcta, 1,082 módulos; salida fuera del repositorio.
- `node tests/t056-real.cjs`, optativa contra HTTP real: búsqueda, comparación,
  las ocho operaciones de canasta, POST que suma, PUT que fija, PATCH que renombra,
  errores 401 y 404, recuperación con una sesión nueva y los dos costos esperados.
  La prueba borra únicamente la canasta que ella misma creó.

Las pruebas de proveedor también comprueban respuestas tardías de otra cuenta,
doble pulsación y bloqueo de reenvíos cuando una escritura pudo haberse guardado
pero su respuesta se perdió. Guía para reproducir:
[T056](../../t056-detalle-canasta.md).
