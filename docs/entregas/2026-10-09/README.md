# Entrega 2 · Documento de análisis

| | |
|---|---|
| **Materia** | Proyecto Integrador · TecNM campus León · periodo 2026-2 |
| **Fecha** | 9 de octubre de 2026 |
| **Qué se entregó** | «CanastaMX · Análisis y diseño», en Word: 113 páginas, 92 tablas, 24 figuras e índices automáticos |
| **De qué commit sale** | `ebc9de1` · 8 de octubre de 2026 |
| **Dónde está** | PENDIENTE · pegar aquí el enlace del documento en Drive y el de la carpeta, como en la entrega 1 |
| **Cómo se entregó** | PENDIENTE · decir si se envió al asesor, se subió a la plataforma o las dos |

## Qué contiene

1. **Introducción y qué cambió desde la entrega 1.**
2. **Administración del proyecto:** equipo, cronograma, tablero y herramientas.
3. **Requerimientos:** RF-01 a 25, RNF-01 a 21 y SLA-D-01 a 10, con su correspondencia al protocolo.
4. **Los 14 casos de uso.**
5. **Modelo de dominio y modelo entidad-relación.**
6. **Diseño de los servicios:** arquitectura en cinco vistas, los dos contratos OpenAPI, el contrato de datos 1.3.4, el modelo dimensional y el esquema de operación.
7. **Procesos:** BPMN de ingesta, de incidentes y de alertas.
8. **Maquetación de las vistas:** inventario, navegación, puntos de quiebre y sistema de diseño.
9. **Lo que sigue:** la boleta de decisiones.

## Lo que cambió frente a la propuesta de la entrega 1

Se explica en el documento, en «Qué cambió desde la entrega 1»:

- las consolas del analista y del operador son de escritorio (D-08);
- el dominio sí consulta a la interfaz analítica, sólo para leer (P-09);
- la interfaz analítica tiene 19 rutas, no cuatro (P-08);
- son dos contratos OpenAPI, no tres (R-01).

## Cómo se regenera

El documento sale del repositorio con el generador (`generador-word-entrega2.zip`):
las figuras 1 a 12 y 21 a 24 se dibujan solas, y las figuras 13 a 20 son las
capturas del prototipo de Figma, que se pegan a mano.

## Nota

Se archiva tal como se entregó. Lo que cambió después va en la entrega 3, del 4 de
noviembre: cuatro suites de pruebas demostradas. Las decisiones que quedaron
abiertas al entregar están en `docs/equipo/decisiones-pendientes.md` §«Para decidir»
(D-09, D-10 y D-11) y su rastro, en
`docs/equipo/propagacion-decisiones-07-oct.md`.
