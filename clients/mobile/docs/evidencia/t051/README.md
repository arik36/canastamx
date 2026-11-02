# T051 · Evidencia de búsqueda (#189)

- Fecha: 2 de noviembre de 2026.
- Entorno: BlueStacks, Android 11, Expo Go para SDK 55, Node 20.20.2.
- Origen: Prism 5.14.2 con ejemplos sintéticos del contrato analitica.yaml 0.2.1.
- Las capturas son nativas de BlueStacks (Ctrl+Shift+S), sin edición ni ratón.
- Se usó emulador por indicación de Renato; no se acredita prueba en teléfono físico.

| Archivo | Consulta y comprobación |
|---|---|
| [01-resultados.png](01-resultados.png) | leche + Guanajuato: dos artículos con precio en MXN, presentación, quincena y observaciones |
| [02-sin-coincidencias.png](02-sin-coincidencias.png) | inexistente + Guanajuato: estado vacío de CU-12, alterno 2a, conservando criterios |
| [03-sin-cobertura.png](03-sin-cobertura.png) | leche + Colima: aviso de cobertura y siete entidades, no un error técnico |
| [04-sin-conexion.png](04-sin-conexion.png) | simulador apagado: termina la carga, muestra el fallo y ofrece Reintentar |

En las cuatro imágenes permanece visible «Simulador · datos de prueba».
Se comprobó la búsqueda con el servicio apagado y se volvió a encender para la
recuperación. Los importes y conteos son ficticios y se etiquetan como tales.

Validación adicional:

- 29 pruebas aprobadas: 16 de sesión y 13 de analítica.
- Incluyen una instancia real de Prism que verifica resultados, vacío, cobertura
  y application/problem+json; la API conserva title, detail y status.
- TypeScript y exportación Android aprobados.
- El contrato compartido no se modificó. La analítica y el dominio tienen URLs
  independientes; las consultas de artículos no envían el token de sesión.

Los pasos para repetirlo están en [la guía de T051](../../t051-busqueda-analitica.md).
