# ADR 023 · dbt no entra

- **Fecha:** 7 de noviembre de 2026
- **Estado:** aceptada el 7 de noviembre de 2026. Cierra la revisión que el ADR 019
  fechó para el 2 de noviembre.
- **Participantes:** A, dueña del frente de datos

## Contexto

El ADR 019 pospuso dbt y fijó su revisión para el 2 de noviembre, «con el esquema
estrella ya cargado». Si entraba, entraba por sus pruebas de datos; si no, había que
escribir el ADR que lo retira de R-07 y del README. La revisión no se hizo ese día.
Hoy tres cosas son ciertas:

1. **El esquema estrella ya se carga sin dbt** (T053, #200). El activo `capa_consumo`
   lo recalcula desde la capa intermedia con SQL de DuckDB, en
   `services/data-platform/ingestion/estrella.py`, igual que toda la plataforma desde
   la ingesta.
2. **Las pruebas de datos ya existen sin dbt.** La compuerta de Pandera (ADR 018)
   juzga cada lote contra el contrato, y las pruebas de `services/data-platform/tests/`
   corren en el trabajo «Datos (Python)» de la integración continua, la estrella
   incluida.
3. **El recorte del 5 de noviembre** dejó el núcleo para el 18 de noviembre, el día
   del congelamiento de funcionalidad (R-06). Un cuarto marco, con su dependencia
   nueva (`dbt-core` y un adaptador), entraría en las dos semanas con menos holgura
   del semestre.

## Decisión

**dbt no entra en esta versión.** Las transformaciones se quedan como SQL dentro de
activos de Dagster (ADR 016 y 019), ejecutado en DuckDB, y las pruebas de datos, en
Pandera y en pytest.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| **dbt sólo por sus pruebas de datos** | Repetiría en YAML lo que ya prueban Pandera y pytest, con una dependencia nueva que habría que instalar en la integración continua y en la máquina virtual |
| **Volver a posponer la revisión** | No queda fecha: desde el 18 no entra nada nuevo, y antes no hay holgura |
| **Reescribir las transformaciones en dbt** | Reescribiría SQL que ya funciona y está probado, que es justo lo que el ADR 019 quería evitar |

## Consecuencias

- **R-07 y el README dejan de nombrar dbt.** El README nombra DuckDB, que es donde
  corre el SQL.
- **Se borra `services/data-platform/dbt/`**, que estaba vacía. El ADR 019 la
  conservaba para no decidir «dbt nunca»; este ADR lo decide para esta versión.
- **El ADR 019 queda revisado:** su estado lo dice y apunta aquí.
- **dbt queda como línea de continuación** en el documento de traspaso (T083), por
  sus pruebas y su documentación del linaje, si el proyecto sigue después del 9 de
  diciembre.
