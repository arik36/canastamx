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

Las tres se votan **antes del 11 de octubre**: la fase 3 arranca el 12 y las tres
tocan contratos que se construyen esa semana. Por qué están aquí y no resueltas en
silencio: `docs/equipo/propagacion-decisiones-07-oct.md` §5 · M-2.

### D-09 · ¿Cómo se entregan los avisos de precio?

Viene de CU-11 y RF-21. Ya aparece como «por decidir» en el diseño arquitectónico
(`docs/arquitectura/README.md`, contexto, contenedores y despliegue), y hasta hoy no
estaba en la boleta.

| | Opción | Consecuencia |
|---|---|---|
| **A** | Un contenedor que atrapa los correos en desarrollo y un SMTP de proveedor en producción | Dos configuraciones y un secreto más en el `.env`. El experimento no depende de un proveedor externo: los avisos se pueden contar sin enviar nada a nadie |
| **B** | Sólo el aviso dentro de la app (Inicio y «Precios que bajaron») | Hay que cambiar RF-21, CU-11 y las tres vistas de arquitectura, que hoy dicen «por correo». La alerta deja de servir con la app cerrada |
| **C** | SMTP de proveedor también en desarrollo | Correos de prueba a direcciones reales, y una cuota que se agota en el experimento |

**Quién:** C1 y B. **Dónde quedará:** ADR nuevo · `arquitectura/` · CU-11.

### D-10 · ¿Cómo sabe el cliente el correo de la cuenta después de iniciar sesión?

La abrió P-13. La vista 8 debe mostrar el correo (`inventario-vistas.md`) y la barra
de la web, el correo y el rol (`diseno.md` §7 · 13). Hoy `dominio.yaml` sólo tiene
`POST /cuentas` y `POST /sesiones`, y `Sesion` trae token, expiración y rol: al
reabrir la app con la sesión guardada, el cliente **no tiene el correo**.

| | Opción | Consecuencia |
|---|---|---|
| **A** | `GET /api/v1/cuentas/yo`, que devuelve `Cuenta` | Una ruta nueva en `dominio.yaml` 0.2.1 y C1 la implementa. El teléfono no guarda el correo y funciona con la sesión restaurada. Sirve igual a la app y a la web |
| **B** | `Sesion` también trae el `correo` | Ninguna ruta nueva, pero la app tiene que guardar el correo en el teléfono para mostrarlo al reabrir: una copia del único dato personal fuera del servidor |
| **C** | El token lleva el correo como atributo y el cliente lo lee del JWT | El correo viaja en cada petición y queda en cualquier registro que guarde el encabezado. Hoy el contrato dice que el token «lleva el rol» |

**Quién:** C1 publica, C2 y D consumen. **Dónde quedará:** `dominio.yaml` · CU-08.

### D-11 · ¿Con qué se registra quién cerró un incidente o resolvió una variante?

La abrió P-08 junto con P-13. Hoy se guarda el **correo del operador** en el esquema
de operación (`analitica.yaml` §`Incidente` y §`Variante`, `cerradoPor` y
`resueltaPor`; `esquema-de-operacion.md` §3): una copia del único dato personal del
sistema, en una base distinta a la del dominio.

| | Opción | Consecuencia |
|---|---|---|
| **A** | El correo, como hoy, sin decir nada más | Queda un dato personal en una capa de la que el proyecto dice que no tiene datos personales, y nadie lo declaró |
| **B** | El `id` de la cuenta | La consola no puede mostrar quién cerró sin preguntarle al dominio, y P-09 sólo permite que el dominio consulte a la analítica, no al revés |
| **C** | El correo, y se declara: un RNF que diga que el esquema de operación guarda el correo del operador como autor de la acción, y nada más de la persona | La consola sigue sirviendo y el documento lo dice en voz alta, que es lo que el asesor va a preguntar |

**Quién:** A, con B. **Dónde quedará:** `requerimientos.md` (RNF) ·
`esquema-de-operacion.md`.

Lo demás que sigue abierto se mide o se escribe: ver «Por medir» y «Por escribir».

---

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

## Lo que dejan las decisiones

| Qué | Quién | Antes de |
|---|---|---|
| Explicar en el documento de la entrega 2 los dos cambios frente a la propuesta E1: las consolas son de escritorio (D-08), y el dominio sí consulta a la analítica (P-09) | A | 9 de octubre |
| Modelo ER, modelo de dominio, CU-09 a CU-11 y el BPMN de alertas, con P-07, P-13, P-14 y D-05 | C1 | 9 de octubre |
| Cuenta con el correo en lugar del nombre; la barra del analista con correo y rol; las métricas de la cola con su población (`diseno.md` §7, puntos 12 a 14) | D y C2 | 9 de octubre |
