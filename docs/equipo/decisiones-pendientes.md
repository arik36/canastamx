# Decisiones pendientes · la boleta vigente

> **Qué es.** La boleta del equipo: cada decisión con sus opciones y sus
> consecuencias, escritas antes de votar. Cuando una decisión se toma, sale de aquí
> y queda en su ADR, su contrato o su caso de uso, con la fecha.
>
> La boleta de la semana 3, la que cita el ADR 010, no quedó en el repositorio. Su
> resultado está en el propio ADR 010. Desde el 5 de octubre de 2026, éste es el
> archivo vigente.

---

## Para decidir

### D-08 · ¿La web es responsiva en tres puntos de quiebre? · antes del 9 de octubre

**Decide:** D, con A · **Queda en:** `docs/analisis/puntos-de-quiebre.md` y `docs/entregas/diseno.md`.

La propuesta entregada (E1) compromete una «aplicación web responsiva en tres
puntos de quiebre». `puntos-de-quiebre.md` dice que las consolas son sólo de
escritorio, con un aviso de ancho mínimo.

| Opción | Qué es | Consecuencia |
|---|---|---|
| **A** | Responsiva en los tres: tres columnas de tarjetas en escritorio, dos en tableta y una en teléfono; las tablas se desplazan de lado dentro de su tarjeta | Cumple lo entregado en E1. Es más trabajo de maquetación |
| **B** | Sólo escritorio, con aviso de ancho mínimo | Cambia lo entregado en E1, y hay que decírselo al asesor |

*Recomendación de A: la opción A, con la regla mínima de `diseno.md` §4.*

### Contratos OpenAPI

Las convenciones y preguntas de arquitectura de los contratos (P-01 a P-15) están
en el PR de T037, en `docs/analisis/openapi/README.md`.

---

## Decididas el 6 de octubre de 2026

| # | Decisión | Resultado | Quién | Dónde quedó |
|---|---|---|---|---|
| D-01 | Las pestañas de la app | **B · cuatro pestañas:** Inicio, Descubrir, Canasta y Cuenta | C2 y D | `navegacion.md` §1. El ADR 007 lleva una nota y C2 lo reescribe |
| D-02 | La canasta del índice (H4) | **A:** precio en las 38 quincenas y las 7 entidades, sin alcohol ni tabaco, mismo peso, base 100 en 2025-01-Q1 | A, con el equipo | ADR 015 |
| D-03 | Dónde se cuenta la frecuencia del `?` ambiguo | **A · en el corpus** | A | Contrato 1.3.4 |
| D-04 | La canasta del invitado | **A · en el teléfono** hasta que inicia sesión | C1, C2 y D | CU-09, alterno 1a · `navegacion.md` §4 |
| D-05 | Qué pasa con una alerta después de dispararse | **B, ajustada:** avisa cuando el precio cruza el umbral hacia abajo, no repite mientras siga abajo y se vuelve a armar cuando sube. Más la idea de Renato: aviso en Inicio y «Precios que bajaron» en Descubrir, con su tabla por quincena. Los dos botones de modo quedan como trabajo futuro | C1, C2 y D | CU-11 · `navegacion.md` §3 |
| D-06 | Los colores | Los tonos de Figma: rojo `#d32f2f`, naranja `#f2a900`. Aviso en azul `#89ccff`, con texto `#0b5394`. Más variantes oscuras para que el texto se lea | D | `diseno.md` §1 |
| D-07 | El umbral de rechazo por lote | **A · 5% de las filas del lote.** Se confirma midiendo los 38 lotes antes del 1 de noviembre | A | Contrato 1.3.4 · CU-02, alterno 5b |

## Decididas antes

| Decisión | Resultado | Dónde quedó |
|---|---|---|
| Colisión de precio de más de $50 | Va a cuarentena el grupo completo. Unanimidad | Contrato 1.3.3 (#124) |
| H3 | Se mide como está enunciada, con 30 «sí» | ADR 014 (#135) |
| Precio de una cadena en Mi canasta | Mediana de sus tiendas en la entidad | Modelo dimensional (T031) |
| Revisión de los PR | Se pide siempre y no bloquea | `estrategia-de-ramas.md` §5 (#134) |
| Iniciales de D en las ramas | `kah` | `estrategia-de-ramas.md` (#134) |

---

## Por medir

| Qué | Para qué | Quién | Antes de |
|---|---|---|---|
| El porcentaje de cuarentena de cada uno de los 38 lotes | Confirmar el 5% de D-07 | A | 1 de noviembre |
| Cuántos artículos cumplen la canasta del ADR 015 | Saber si la canasta representa algo | A | T069 |

## Por escribir

Son decisiones que ya se tomaron, pero sin ADR.

| ADR que falta | Dónde aparece la decisión | Quién |
|---|---|---|
| Orquestador: Dagster y no Airflow | README. La guía de las presentaciones dice que el ADR ya existe, y no existe | A |
| Interfaz analítica en FastAPI | README | A |
| Validación con Pandera | README | A |
| Cliente web en Next.js | README | D |

## Por ratificar

| ADR | Estado | Quién |
|---|---|---|
| 007 · navegación de la app | En propuesta, y con D-01 hay que reescribirlo: cuatro pestañas | C2 |
| 006 y 011 · entorno y diseño de la app | En propuesta, aunque ya se siguen | C2 |
| 008 · dónde vive la base | En propuesta; su título dice «ADR 006» y su peso no dice de qué población es | B |
