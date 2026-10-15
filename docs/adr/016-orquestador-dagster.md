# ADR 016 · El orquestador: Dagster y no Airflow

- **Fecha:** 11 de octubre de 2026
- **Estado:** aceptada el 11 de octubre de 2026. Documenta una decisión ya tomada, registrada en `docs/equipo/decisiones-pendientes.md` §«Por escribir», y le pone fecha de salida
- **Participantes:** A, dueña del frente de datos. B firma la parte de infraestructura (consumo del contenedor, en el ADR 008)

## Contexto

La ingesta de hoy es un guion de Python con DuckDB que se corre a mano
(`services/data-platform/ingestion/ingesta.py`). Eso alcanzó para medir el corpus,
y no alcanza para lo que se construye a partir del 12 de octubre:

- **RF-12** pide el **linaje de cada lote** en la consola: de qué archivo salió cada
  fila y en qué corrida entró.
- **RF-13** pide que cada corrida que falle **levante un incidente** con su lote, su
  compuerta, su motivo y sus filas.
- **SLA-D-05, que es H2,** pide **menos de 15 minutos** entre el inicio de la ingesta
  de un lote defectuoso y el incidente. Eso exige que algo dispare la corrida y
  observe su resultado: un guion que alguien corre a mano no tiene «inicio» medible.
- **RF-25** pide poder **reprocesar cualquier lote** desde la capa cruda y obtener el
  mismo resultado.

El README y R-07 ya comprometen Dagster, y la guía de las presentaciones
(`docs/equipo/entregas/2026-12-presentaciones.md`) da por hecho que este ADR existe.
No existía. Este documento lo corrige.

## Decisión

**Se usa Dagster**, en su forma mínima, dentro del contenedor de la plataforma de
datos:

1. **Activos particionados por lote.** La partición es la quincena
   (`2026-07-Q2`), que es exactamente el grano de un lote. Re-materializar una
   partición *es* reprocesar un lote (RF-25).
2. **Un sensor** que dispara la corrida al aparecer un archivo nuevo en el bucket.
   Ese disparo es el instante cero que mide H2.
3. **El linaje que Dagster ya da** —qué activo produjo qué, con qué corrida— se
   expone en la consola en lugar de construirlo a mano (RF-12).
4. **Las transformaciones son SQL dentro de los activos**, no un marco aparte
   (ADR 019).

**Con fecha de salida: si el 25 de octubre no corren tres activos particionados con
un sensor, se cambia a guion más `cron`** y se escribe el ADR que reemplaza a éste.
La fecha está puesta para que la decisión no se defienda sola por inercia.

### Qué corre al 14 de octubre de 2026

`services/data-platform/orquestacion/definiciones.py` (T043). `dagster dev` levanta
y muestra **tres activos, los tres particionados en las 38 quincenas** —`capa_cruda`,
`filas_revisadas` y `lote_promovido`— más el sensor `archivo_nuevo`, que revisa cada
30 segundos y deja la marca de tiempo del disparo en las etiquetas de la corrida. Las
38 particiones no están escritas: salen de `alcance.ventana` del contrato.

**Lo que falta para que la fecha de salida quede contestada del todo:** una corrida
contra MinIO. Lo probado es de punta a punta en **simulación** (`--simular`), que
ejercita los tres activos, el linaje y el reproceso, pero no la escritura al bucket.
Eso es de B y del ADR 008.

Y una consecuencia de haberlo construido, que vale para el 25 de octubre: la
orquestación quedó **delgada a propósito**. Ninguna regla del contrato vive en
`orquestacion/`; están en `ingestion/compuerta.py` y `ingestion/lote.py`, que no
mencionan Dagster. Hay dos pruebas que lo vigilan
(`test_la_orquestacion_no_tiene_ninguna_regla_del_contrato` y
`test_las_compuertas_no_importan_dagster`). Si el 25 se decide volver a guion más
`cron`, se borra una carpeta y las compuertas siguen corriendo: eso es lo que hace
que la fecha de salida sea una decisión real y no una amenaza.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| **Airflow** | Su unidad es la tarea, no el dato: el linaje y el reproceso por lote hay que construirlos encima. Además pide planificador, servidor web, trabajador y su propia base, sobre los 12 GB que el ADR 008 reparte entre dos PostgreSQL, MinIO, Traefik, el dominio y la web |
| **Prefect** | Resuelve lo mismo que Dagster con menos adopción y sin particiones ni linaje de primera clase, que son justo las dos cosas que se necesitan |
| **Guion más `cron`** | Es la alternativa de respaldo, no la primera opción: no da linaje, ni reintento por partición, ni un instante de inicio observable, sin escribir las tres cosas a mano. Queda escrita aquí para poder volver a ella el 25 de octubre sin volver a discutirla |
| **No orquestar nada** | Deja H2 sin forma de medirse y RF-12 sin linaje |

## Consecuencias

- **Las particiones de Dagster son los lotes.** Eso amarra RF-25, el reproceso, a
  una operación de una línea, y hace que «reprocesar `07-2026_Q2`» signifique lo
  mismo para la consola, para el experimento y para el código.
- **El sensor es lo que vuelve medible H2.** Sin él, los 15 minutos no tienen
  desde cuándo contarse.
- **Sube el consumo del contenedor de la plataforma.** B lo confirma en el ADR 008,
  que todavía tiene que declarar la población de su cifra de peso.
- **Si el 25 de octubre la fecha de salida se cumple, este ADR se reemplaza.** No se
  reescribe: se escribe el 0XX que lo sustituye, con la medición que lo justificó.
- **La guía de las presentaciones deja de mentir:** la pregunta «¿por qué Dagster y
  no Airflow?» ya tiene dónde responderse.
