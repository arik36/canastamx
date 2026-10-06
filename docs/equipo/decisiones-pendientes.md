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

### D-01 · Las pestañas de la app · antes del 9 de octubre

**Deciden:** C2 y D · **Queda en:** ADR 007 · **Por qué urge:** el prototipo es parte de la entrega del 9.

| Opción | Qué es | Consecuencia |
|---|---|---|
| **A** | Tres pestañas: Búsqueda, Mi canasta y Alertas | Es lo que dicen el ADR 007 y la app. Cambia el prototipo |
| **B** | Cuatro pestañas: Inicio, Descubrir, Canasta y Cuenta | Es lo que tiene el prototipo. Se reescribe el ADR 007 y cambia la navegación de la app |

### D-02 · La canasta del índice (H4) · antes del 25 de octubre

**Decide:** A, con el equipo · **Queda en:** un ADR nuevo · **Afecta:** CU-07, RF-11.

| Opción | Qué es | Consecuencia |
|---|---|---|
| **A** | Los artículos con precio en las 38 quincenas y las 7 entidades, sin alcohol ni tabaco, con el mismo peso y base 100 en 2025-01-Q1 | Fácil de calcular y de explicar. Sus pesos no se parecen a los del INPC |
| **B** | Los mismos artículos, ponderados con los pesos del INPC por categoría | Más comparable con INEGI. Hay que relacionar las categorías de PROFECO con las del INPC |

*Recomendación de A: la opción A, que es la propuesta de CU-07.*

### D-03 · Dónde se cuenta la frecuencia del `?` ambiguo · antes del 25 de octubre (T048)

**Decide:** A · **Queda en:** el contrato · **Afecta:** CU-03, RF-05.

| Opción | Qué es | Consecuencia |
|---|---|---|
| **A** | En el corpus completo | La misma población de la que salió el diccionario, y con más datos |
| **B** | Sólo en el alcance | La población que se publica, aunque con menos datos |

*Recomendación de A: la opción A.*

### D-04 · La canasta del invitado

**Deciden:** C1 y C2 · **Queda en:** CU-09 · **Afecta:** RF-22.

| Opción | Qué es | Consecuencia |
|---|---|---|
| **A** | Vive en el teléfono hasta que la persona inicia sesión, y entonces se sube | El dominio no cambia: la canasta sigue siendo de un solo usuario |
| **B** | Una sesión anónima en el servidor | Contradice el modelo de dominio, en el que toda canasta tiene dueño |

### D-05 · Qué pasa con una alerta después de dispararse

**Decide:** C1 · **Queda en:** CU-11 · **Afecta:** RF-21.

*Avance (#137): CU-11 ya dice que la alerta **permanece activa** después de
notificar. Falta decir si vuelve a avisar en cada revisión mientras el precio siga
por debajo del umbral, o sólo cuando vuelva a cruzarlo.*

| Opción | Qué es | Consecuencia |
|---|---|---|
| **A** | Se dispara una vez y queda «disparada»; la persona la vuelve a armar | Un aviso por alerta, y nada más |
| **B** | Se vuelve a armar sola cuando el precio sube otra vez por encima del umbral | Avisa en cada bajada, sin repetir mientras el precio siga bajo |

*Si no se decide, una alerta que sigue activa avisa cada quincena mientras el precio siga bajo.*

### D-06 · Los colores del sistema de diseño

**Decide:** D, y C2 copia los valores · **Queda en:** `docs/entregas/diseno.md` y `clients/mobile/theme/design-system.ts`.

Faltan el código de color del rojo y del naranja, que hoy sólo tienen nombre, y un
color para «aviso», porque el contrato tiene tres niveles: ok, avisa y bloquea.

---

### D-07 · El umbral de rechazo por lote · antes del 1 de noviembre

**Decide:** A · **Queda en:** el contrato · **Afecta:** RF-D07 del protocolo y el
alterno 5b de CU-02.

Si la proporción de filas en cuarentena de un lote pasa de este umbral, el lote
entero no se promueve. El protocolo lo pide («el umbral acordado») y ningún
documento le pone número todavía.

| Opción | Qué es | Consecuencia |
|---|---|---|
| **A** | Un umbral fijo, por ejemplo el 5% de las filas del lote | Simple de explicar. Hay que medir antes cuánto rechaza un lote sano: hoy la cuarentena del alcance es como máximo del 0.225% (T031) |
| **B** | Un umbral relativo a la historia, por ejemplo tres veces la mediana de rechazo de los lotes anteriores | Se adapta a cada fuente, pero tarda en tener historia y cuesta más explicarlo |

---

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
| 006, 007 y 011 · móvil | En propuesta, aunque ya se siguen. El 007 depende de D-01 | C2 |
| 008 · dónde vive la base | En propuesta; su título dice «ADR 006» y su peso no dice de qué población es | B |

## Decididas hace poco

| Decisión | Resultado | Dónde quedó |
|---|---|---|
| Colisión de precio de más de $50 | Va a cuarentena el grupo completo. Unanimidad | Contrato 1.3.3 (#124) |
| H3 | Se mide como está enunciada, con 30 «sí» | ADR 014 (#135) |
| Precio de una cadena en Mi canasta | Mediana de sus tiendas en la entidad | Modelo dimensional (T031) |
| Revisión de los PR | Se pide siempre y no bloquea | `estrategia-de-ramas.md` §5 (#134) |
| Iniciales de D en las ramas | `kah` | `estrategia-de-ramas.md` (#134) |
