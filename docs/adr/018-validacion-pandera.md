# ADR 018 · La validación del contrato de datos: Pandera por lote

- **Fecha:** 11 de octubre de 2026
- **Estado:** aceptada el 11 de octubre de 2026. Documenta una decisión ya tomada, registrada en `docs/equipo/decisiones-pendientes.md` §«Por escribir»
- **Participantes:** A, dueña del frente de datos

## Contexto

El contrato `contracts/qqp-v1.yaml` 1.3.4 declara, columna por columna, el tipo, el
largo máximo y si el valor es obligatorio, y nombra los motivos por los que una fila
va a cuarentena. **H1 exige contener al menos el 95%** de las filas defectuosas que
se inyecten: una fila mala que llega a consumo es la hipótesis reprobada.

El alcance son **2,658,906 filas en 38 lotes**: alrededor de **70 mil filas por
lote**. Un lote entero cabe en memoria sin esfuerzo.

La pregunta no es si se valida —eso ya lo decidió el contrato— sino **con qué**, y
sobre todo **cómo se evita que las reglas se escriban dos veces**: una en el YAML del
contrato y otra en el código. Dos copias de la misma regla es exactamente la falla
que este proyecto investiga.

## Decisión

**Se usa Pandera, por lote, con el esquema generado desde el YAML del contrato.**

1. **El esquema no se escribe a mano.** Se construye leyendo
   `contracts/qqp-v1.yaml`: las 15 columnas con su tipo, su largo y su
   obligatoriedad salen de ahí. Cambiar `largo_maximo` en el contrato cambia la
   compuerta sin tocar el código.
2. **Grano de validación: el lote.** Pandera revisa fila por fila y devuelve, por
   cada fila rechazada, **cuál regla falló** —que es justo lo que la tabla de
   cuarentena necesita guardar como motivo (SLA-D-09).
3. **Lo que necesita ver más que una fila se queda en DuckDB:** la colisión de
   precio alta (que compara grupos), la frecuencia del `?` ambiguo (que se cuenta
   sobre el corpus, D-03), la frescura y el umbral de rechazo del 5% por lote
   (D-07), que es una proporción del lote completo.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| **Great Expectations** | Su conjunto de expectativas se escribe y versiona **aparte** del contrato. Serían dos documentos que dicen lo mismo y que se separan en silencio: el error que el proyecto estudia, cometido por el proyecto |
| **Validar a mano con pandas** | Cada regla del contrato se escribiría una segunda vez, sin reporte por fila ni motivo estructurado. Es lo más barato hoy y lo más caro en noviembre |
| **Todo en DuckDB, sin Pandera** | SQL sí puede filtrar filas malas, pero no devuelve con naturalidad «esta fila, por esta regla». La cuarentena pide fila y motivo, no un conteo |
| **Validar el corpus completo de una vez** | 21 millones de filas no caben en memoria, y la compuerta tiene que correr **por lote** para que H2 pueda medir cuánto tarda en detectar uno defectuoso |

## Consecuencias

- **El contrato es la única fuente de las reglas de columna.** Esa es la parte de
  «contratos de datos» que el trabajo afirma y aquí queda implementada, no sólo
  enunciada.
- **Falta declarar tres motivos en el contrato** —`valor_requerido_vacio`,
  `largo_excedido` y `tipo_invalido`— **antes del 9 de noviembre.** Son exactamente
  los que Pandera produce, y hoy los nombra `docs/datos/esquema-de-operacion.md` §3
  y el `enum` de `analitica.yaml` como propuesta. Mientras no estén en el contrato,
  quien construya la cuarentena lee el contrato, no el `enum`.
- **Setenta mil filas por lote caben en memoria**, así que no hace falta trocear.
  Si la ventana se abriera con datos nuevos y un lote creciera, habría que revisarlo.
- **La compuerta fina de precio** (comparar cada precio contra su artículo usando
  `agg_articulo_entidad_quincena`) **no es de Pandera**: necesita el agregado, y vive
  en DuckDB. Sigue siendo pendiente del contrato.
