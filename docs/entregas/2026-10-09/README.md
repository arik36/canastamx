# Entrega 2 · Documento de análisis

| | |
|---|---|
| **Materia** | Proyecto Integrador · TecNM campus León · periodo 2026-2 |
| **Fecha** | 9 de octubre de 2026 |
| **Qué se entregó** | «CanastaMX · Análisis y diseño», en Word: 113 páginas, 92 tablas, 24 figuras e índices automáticos |
| **De qué commit sale** | `ebc9de1` · 8 de octubre de 2026 |
| **Dónde está** | `FALTA EL ENLACE` · pegar el del documento en Drive y el de la carpeta, como en la entrega 1, y decir la fecha en que se revisó que cualquiera con el enlace puede verlo |
| **Cómo se entregó** | Se entregó al asesor el 9 de octubre de 2026, explicándole de viva voz qué cambia en las capturas del prototipo (ver «Una nota sobre las figuras 13 a 20») · `CONFIRMAR` si además se subió a la plataforma de la materia |

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

## Una nota sobre las figuras 13 a 20

**Las ocho capturas del prototipo son las de antes de la corrección.** Al entregar,
el prototipo todavía tenía los tres puntos que `docs/entregas/diseno.md` §7 registra
como pendientes y que las decisiones del 7 de octubre volvieron obligatorios:

| Punto | Qué se ve en la captura | Qué dirá la corregida | Decisión |
|---|---|---|---|
| 12 | La pestaña Cuenta con el nombre «Karen Alejandra» y una foto | El correo de la cuenta y un avatar con su inicial | P-13: la cuenta no tiene nombre |
| 13 | La barra lateral de la web con «Analista Ruiz» | El correo y el rol de la sesión | P-07 y P-13 |
| 14 | La cola con cobertura 81.4% y precisión 97.3% | «Se mide en T058», o la cifra real con su población | RNF-16 · esas dos cifras eran de ejemplo |

**Se le explicó al asesor en la entrega.** No es una inconsistencia oculta: el propio
documento declara los catorce puntos de `diseno.md` §7 como pendientes, y el modelo
entidad-relación y RF-17 ya dicen que la cuenta no guarda nombre.

**Las capturas corregidas entran en la entrega del 4 de noviembre.** Quien las
rehaga, que actualice también los puntos 12, 13 y 14 de `diseno.md` §7 a resueltos,
para que el pendiente y la evidencia se muevan juntos.

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
