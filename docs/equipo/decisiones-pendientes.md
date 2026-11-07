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

No queda ninguna abierta: D-09 a D-12 ya se votaron y están abajo, en «Decididas».
Por qué estaban aquí y no resueltas en silencio:
`docs/equipo/propagacion-decisiones-07-oct.md` §5 · M-2.

Lo demás que sigue abierto se mide o se escribe: ver «Por medir» y «Por escribir».

---

## Decididas el 2 de noviembre de 2026

D-12 se votó el 2 de noviembre, después del plazo del 29 de octubre. Ganó B, que no
cambia código: T062 (4 de noviembre) no esperaba nada de ella. Lo que obliga a
escribir está en «Lo que dejan las decisiones».

| # | Decisión | Resultado | Quién | Dónde quedó |
|---|---|---|---|---|
| D-12 | ¿Qué desafío lleva el 401 de `POST /api/v1/sesiones`? | **B · 401 sin `WWW-Authenticate`, como hoy, y se declara la excepción.** El inicio de sesión recibe el correo y la contraseña en el cuerpo, y `Bearer` es el esquema de las rutas con sesión: anunciarlo aquí nombraría un mecanismo que esta ruta no acepta. Así ningún cliente cambia: la web distingue las credenciales incorrectas por el 401 | C1, C2 y D; los tres votaron B | Falta: declarar la excepción en `dominio.yaml` y en CU-08 (ver «Lo que dejan las decisiones») |

## Decididas, registradas el 27 de octubre de 2026

D-09 y D-11 ya se votaron, cada una por quienes la boleta nombraba; la fecha del voto
no quedó en el repositorio: ésta es la fecha en que se anotan. Lo que cada una obliga
a cambiar está en «Lo que dejan las decisiones».

| # | Decisión | Resultado | Quién | Dónde quedó |
|---|---|---|---|---|
| D-09 | ¿Cómo se entregan los avisos de precio? | **B · sólo el aviso dentro de la app** (Inicio y «Precios que bajaron»). La alerta deja de servir con la app cerrada | C1 y B; los dos votaron B | Falta: el ADR nuevo, y quitar el correo de los documentos que todavía lo prometen (ver «Lo que dejan las decisiones») |
| D-11 | ¿Con qué se registra quién cerró un incidente o resolvió una variante? | **C · el correo, y se declara:** un RNF dice que el esquema de operación guarda el correo del operador como autor de la acción, y nada más de la persona | A, con B; los dos votaron C | Falta: el RNF en `requerimientos.md` y su cita en `esquema-de-operacion.md` |

## Decididas, registradas el 23 de octubre de 2026

D-10 ya se votó, pero la fecha del voto no quedó en el repositorio: ésta es la fecha
en que se anota.

| # | Decisión | Resultado | Quién | Dónde quedó |
|---|---|---|---|---|
| D-10 | ¿Cómo sabe el cliente el correo de la cuenta después de iniciar sesión? | **A · `GET /api/v1/cuentas/yo`,** que devuelve `Cuenta`. El teléfono no guarda el correo y la ruta funciona con la sesión restaurada; sirve igual a la app y a la web | C1 publica, C2 y D consumen | `dominio.yaml` 0.2.1 · CU-08 (T045) |

## Decididas el 7 de octubre de 2026

| # | Decisión | Resultado | Quién | Dónde quedó |
|---|---|---|---|---|
| D-08 | ¿La web es responsiva en tres puntos de quiebre? | **B · las consolas son sólo de escritorio,** con aviso de ancho mínimo; el acceso web se adapta a los tres anchos. El cambio frente a la propuesta E1 se explica al asesor en la entrega 2 | D, con A y C1 | `puntos-de-quiebre.md` (#125) · `diseno.md` §4 |
| P-01 a P-10 | Convenciones y arquitectura de los contratos | Todas en **A**: `camelCase`, dinero como texto, `problem+json`, `/api/v1`, `limit` y `offset`, cobertura como respuesta normal, sesión con rol, esquema de operación, el dominio consulta a la analítica, y la analítica calcula el costo de la canasta | Todo el equipo | `docs/analisis/openapi/README.md` |
| P-13 | ¿El usuario tiene nombre? | **B · no:** se identifica con su correo | C1 | Modelo ER · `dominio.yaml` |
| P-14 | ¿De qué entidad es el precio de una alerta? | **A · la alerta guarda su entidad** | C1 | Modelo ER · CU-10 · `dominio.yaml` |
| P-15 | ¿Qué es un artículo «anómalo»? | **A · variación quincenal mayor al 20%.** Se calibra con el volumen real | A y D | `analitica.yaml` |

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
| Cuántos artículos marca como anómalos el 20%, y con qué mínimo de observaciones | Calibrar P-15 | A y D | Antes de construir el tablero |

## Por escribir

Son decisiones que ya se tomaron, pero sin ADR.

| ADR que falta | Dónde aparece la decisión | Quién |
|---|---|---|
| Cliente web en Next.js | README | D |

Las tres de A quedaron escritas el 11 de octubre: **ADR 016** (Dagster y no Airflow,
con fecha de salida el 25 de octubre), **ADR 017** (FastAPI) y **ADR 018** (Pandera
por lote). Se agregó el **ADR 019**, que pospone dbt y fija su revisión para el 2 de
noviembre.

## Por ratificar

| ADR | Estado | Quién |
|---|---|---|
| 008 · dónde vive la base | En propuesta: su peso no dice de qué población es, y le falta el presupuesto de memoria de los 12 GB que le dejó el ADR 010 (§3). Va en T044 (#158) | B |
| 020 · el token de sesión | En propuesta: HS256, `JWT_SECRET` como Base64 de 32 bytes y los claims `sub`, `rol`, `iat` y `exp`. El dominio ya lo aplica. Ratificarlo no cierra la verificación cruzada con la analítica: ésa es criterio de T058 (4 de noviembre) | A, con C1 |

Los ADR 006, 007 y 011 ya se ratificaron en #173.

## Lo que dejan las decisiones

| Qué | Quién | Antes de |
|---|---|---|
| D-09: el ADR nuevo del aviso dentro de la app, que diga también qué queda de los estados de envío (`PENDIENTE`, `ENVIADA` y `FALLIDA`) de `Notificacion` en `dominio.yaml` y en el modelo ER. Y quitar el correo de donde todavía se promete: RF-21, CU-11 (paso 6, alterno 6a y la poscondición), `navegacion.md` §3.2 y §3.3, `inventario-vistas.md` §8, el BPMN de alertas (`alertas.bpmn` y `alertas.svg`), las vistas `01-contexto`, `02-contenedores` y `04-componentes-dominio` de `arquitectura/` con sus `.png` y su `README.md`, y la fila de C1 en `entregas/2026-11-18-version-desplegada.md` | C1 y B | Antes de T066, la tarea de las alertas (C1, vence el 15 de noviembre) |
| D-11: el RNF nuevo en `requerimientos.md`: el esquema de operación guarda el correo del operador como autor de la acción, y nada más de la persona. Se cita desde `docs/datos/esquema-de-operacion.md` (el diagrama de §1 y la tabla de §2) | A, con B | Antes de T069 y T073 (A y D, vencen el 13 de noviembre), que cierran la consola y la cola |
| D-12: declarar la excepción en `dominio.yaml` —la descripción de `CredencialesInvalidas` y la nota de la versión 0.2.2, que hoy la dan por abierta— y en CU-08, alterno 7a. También el Javadoc de `SinSesionHandler`, que dice «la decisión D-12, todavía abierta» | C1 | Antes de la entrega del 18 de noviembre |

Las tres que vencían el 9 de octubre ya están hechas: la explicación de D-08 y P-09 en
la entrega 2 (`docs/entregas/2026-10-09/README.md`); el modelo ER, el modelo de
dominio, CU-09 a CU-11 y el BPMN de alertas con P-07, P-13, P-14 y D-05 (el BPMN, en
#149); y los puntos 12 a 14 de `diseno.md` §7, resueltos en Figma el 11 de octubre.
Las capturas corregidas del prototipo entran en la entrega del 4 de noviembre.
