# El tablero: GitHub Projects e Issues

El tablero es la fuente de verdad del avance. La bitácora en Excel se genera **desde** aquí, no al revés.

Esta guía la ejecuta A una sola vez (montaje), y después la usan los cinco todos los días (operación).

---

# Parte 1 — Montaje

> **Quién:** A · **Cuándo:** antes del lunes 7 de septiembre · **Cuánto:** 40 minutos

## 1.1 Crea el proyecto

1. Entra a `github.com/arik36/canastamx`.
2. Pestaña **Projects** → botón verde **New project**.
3. Plantilla **Board** → **Create**.
4. Nombre: `CanastaMX — Semestre 2026-2`.

## 1.2 Configura las columnas

Por defecto trae tres. Necesitas cinco. Haz clic en el `+` a la derecha de la última columna para agregar, y en los tres puntos de cada una para renombrar.

| Columna | Qué contiene |
|---|---|
| **Backlog** | Todo lo que existe pero aún no toca |
| **Esta semana** | Lo comprometido para la semana en curso |
| **En curso** | Lo que alguien está haciendo *ahora*. Máximo dos tarjetas por persona |
| **En revisión** | Solicitud abierta esperando aprobación |
| **Hecho** | Incorporado a `main` |

El límite de **dos tarjetas en curso por persona** es lo único que impide que alguien tenga siete cosas empezadas y ninguna terminada.

## 1.3 Agrega los campos personalizados

Tres puntos arriba a la derecha → **Settings** → **Custom fields** → **New field**.

| Campo | Tipo | Valores |
|---|---|---|
| `Semana` | Number | 1 a 14 |
| `Frente` | Single select | `Datos`, `Infra`, `Dominio`, `Móvil`, `Web`, `Equipo` |
| `Estado` | Single select | `Sin empezar`, `En curso`, `Parcial`, `Aprobada`, `Retrasada` |
| `Fecha límite` | Date | — |
| `Evidencia` | Text | Enlace a la PR o al archivo |

Con `Semana` y `Frente` puedes filtrar el tablero por persona o por semana en un clic, que es lo que hace útil la reunión.

## 1.4 Crea las vistas

Abajo de las columnas hay una barra de pestañas con un `+`. Crea tres:

| Vista | Tipo | Filtro | Para qué |
|---|---|---|---|
| **Tablero** | Board | — | El día a día |
| **Por persona** | Table, agrupada por *Assignees* | — | La reunión semanal |
| **Esta semana** | Table | `Semana:<la actual>` | Saber qué toca |

## 1.5 Crea las etiquetas

En el repositorio: **Issues** → **Labels** → **New label**.

| Etiqueta | Color | Para |
|---|---|---|
| `datos` | azul | Frente A |
| `infra` | gris | Frente B |
| `dominio` | naranja | Frente C1 |
| `movil` | morado | Frente C2 |
| `web` | verde | Frente D |
| `docs` | amarillo | Documentación |
| `entrega` | rojo | Tareas atadas a una entrega institucional |
| `bloqueo` | rojo oscuro | Algo detenido esperando a otro |
| `experimento` | café | Semana 13 |

## 1.6 Crea los hitos

**Issues** → **Milestones** → **New milestone**. Cinco, con su fecha:

| Hito | Fecha |
|---|---|
| `E1 — Definición` | 18 de septiembre de 2026 |
| `E2 — Análisis` | 9 de octubre de 2026 |
| `E3 — Construcción` | 4 de noviembre de 2026 |
| `E4 — Versión desplegada` | 18 de noviembre de 2026 |
| `E5 — Presentación` | 9 de diciembre de 2026 |

Los hitos te dan una barra de progreso automática por entrega. Es lo primero que le enseñas al asesor.

## 1.7 Siembra las tareas

Hay dos caminos.

**Camino rápido (recomendado):** el script `infra/scripts/sembrar-tablero.sh` crea etiquetas, hitos y las tareas de las semanas 1 a 3 en un solo comando. Requiere `gh` instalado (`cli.github.com`) y `gh auth login`.

```bash
cd canastamx
bash infra/scripts/sembrar-tablero.sh
```

Léelo antes de correrlo. Al final imprime cuántos issues creó.

**Camino manual:** abre `docs/equipo/cronograma.md` y crea un issue por cada fila de la semana en curso. Toma unos veinte minutos por semana y tiene la ventaja de que te obliga a leer lo que estás comprometiendo.

En cualquiera de los dos casos, **solo se siembran las semanas 1 a 3 por ahora**. Sembrar las catorce de golpe produce un tablero con 70 tarjetas que nadie mira. Las siguientes se cargan en la reunión semanal, que es cuando ya sabes qué se recorrió.

## 1.8 Protege `main`

**Settings** → **Branches** → **Add branch protection rule**.

- Branch name pattern: `main`
- ☑ Require a pull request before merging
- ☑ Require approvals: **1**
- ☑ Require status checks to pass before merging
- ☑ Do not allow bypassing the above settings

Sin esto, la regla de "nadie escribe en `main`" es un acuerdo verbal que alguien va a romper sin querer un martes a las once de la noche.

---

# Parte 2 — Operación diaria

## 2.1 Anatomía de un issue

Un issue mal escrito genera trabajo mal hecho. Este es el formato, y la plantilla `.github/ISSUE_TEMPLATE/tarea.yml` ya lo impone:

```markdown
Título: [S1][Datos] Perfilado nivel 2 de la fuente QQP

## Qué hay que hacer
Distribución de precios: mínimo, máximo, mediana y percentiles por categoría.
Contar precios en cero, negativos o absurdamente altos. Duplicados exactos.
Número de establecimientos y cadenas distintas.

## Cómo saber que quedó
La sección de rangos y anomalías del perfilado está escrita con números
concretos, no con adjetivos.

## Dónde queda
docs/datos/perfilado/

## Depende de
#3 (perfilado nivel 1)

Semana: 1 · Frente: Datos · Fecha límite: 8 de septiembre
```

**"Cómo saber que quedó" es la parte que no se puede omitir.** Es lo que permite que otra persona revise sin discutir, y lo que convierte "avancé bastante" en un hecho verificable.

## 2.2 El día a día

| Momento | Qué haces |
|---|---|
| Tomas una tarea | Te asignas en el issue y arrastras la tarjeta a **En curso** |
| Abres la solicitud | Escribes `Closes #14` en el cuerpo. La tarjeta se mueve sola a **En revisión** |
| Te incorporan | El issue se cierra solo y la tarjeta cae en **Hecho** |
| Te atoras | Etiqueta `bloqueo`, asignas a quien lo puede resolver, avisas en el chat |

Ese `Closes #14` es lo que hace que el tablero se mantenga solo. Sin él, alguien tiene que mover tarjetas a mano y se deja de hacer en la segunda semana.

## 2.3 En la reunión semanal

1. Abre la vista **Por persona**.
2. Recorre integrante por integrante. Para cada tarjeta que no esté en **Hecho**, se asigna `Estado`: `Parcial` o `Retrasada`, y se anota qué falta.
3. Lo `Parcial` recibe fecha nueva **dentro de la misma semana**.
4. Lo `Retrasado` se replantea en voz alta: ¿se recorta el alcance, se reasigna, o se descarta?
5. Se crean las tarjetas de la semana siguiente desde `cronograma.md`, con dueño y fecha.

## 2.4 Exportar para el asesor

Vista **Por persona** → tres puntos arriba a la derecha → **Export view as CSV**.

Ese CSV se pega en la hoja `Bitácora` del libro `CanastaMX_Bitacora.xlsx`, que ya trae el semáforo y el tablero de porcentajes armados. Se hace una vez por entrega institucional, no cada semana.

---

## Los cinco errores que matan un tablero

1. **Tarjetas sin criterio de aceptación.** Se discute para siempre si algo quedó.
2. **Tarjetas de dos semanas.** Nunca se mueven y el tablero deja de reflejar la realidad.
3. **Tarjetas sin dueño.** Nadie las hace y todos suponen que alguien más.
4. **Trabajar en algo que no está en el tablero.** Es trabajo invisible: no se evalúa y no se aprovecha.
5. **Sembrar las catorce semanas de golpe.** 70 tarjetas que nadie lee. Tres semanas a la vez.
