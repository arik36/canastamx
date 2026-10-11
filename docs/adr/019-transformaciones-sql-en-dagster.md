# ADR 019 · Las transformaciones: se pospone dbt

- **Fecha:** 11 de octubre de 2026
- **Estado:** aceptada el 11 de octubre de 2026, con revisión fechada el 2 de noviembre de 2026
- **Participantes:** A, dueña del frente de datos

## Contexto

El cronograma pone **dbt del 19 al 25 de octubre**, para las transformaciones de capa
cruda a intermedia. Al llegar la fecha, tres cosas son ciertas y no lo eran cuando se
planeó:

1. **Los SQL de T031 ya existen y están probados** sobre PostgreSQL 16
   (`docs/datos/esquema-de-operacion.sql` y `probar-esquema-de-operacion.sql`). El
   modelo dimensional está medido sobre el alcance, no previsto.
2. **La carpeta `services/data-platform/dbt/` está vacía.** No hay nada que migrar:
   lo que se decida aquí es con qué se escribe lo que todavía no existe.
3. **El frente de datos es una persona**, y en la misma semana entra el entorno de
   pruebas aislado. Dagster, DuckDB y Pandera ya son tres marcos nuevos en dos
   semanas; dbt sería el cuarto.

La entrega del 4 de noviembre pide **cuatro suites de pruebas demostradas**, y una de
ellas es de datos. Esa es la razón real por la que dbt interesa: sus pruebas de datos,
no su motor de plantillas.

## Decisión

**Se pospone dbt.** Las transformaciones de capa cruda → intermedia → consumo se
escriben como **SQL dentro de activos de Dagster** (ADR 016), partiendo de los SQL
ya probados de T031.

**dbt se revisa el 2 de noviembre**, con el esquema estrella ya cargado. Si entra,
entra **por sus pruebas de datos**, que es lo que aportaría a la cuarta suite, y no
por reescribir transformaciones que para entonces ya funcionarán.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| **dbt desde el 19 de octubre**, como decía el cronograma | Un cuarto marco en la semana en la que además entra el entorno de pruebas, para reescribir SQL que ya está probado. El riesgo no es que dbt sea malo: es que la semana del 19 no tiene espacio para aprenderlo |
| **dbt nunca** | Cerraría la puerta a sus pruebas de datos, que son candidatas naturales a una de las cuatro suites del 4 de noviembre. No hay razón para decidir eso hoy |
| **Transformar con pandas en lugar de SQL** | Obliga a traer los datos a memoria y a reescribir lo de T031 en otro lenguaje. SQL sobre PostgreSQL ya está medido |

## Consecuencias

- **Cambia la fila del 19 al 25 de octubre del cronograma**, que decía
  «transformaciones en dbt». Se actualiza en este mismo cambio.
- **R-07 y el README nombran dbt** entre las tecnologías de la plataforma. Quedan
  como **previsto, en revisión el 2 de noviembre**. No se borra la mención: se
  fecha.
- **`services/data-platform/dbt/` se queda vacía y no se borra.** Borrarla sería
  decidir «dbt nunca», que es justo lo que este ADR no decide.
- **Si el 2 de noviembre dbt no entra**, se escribe el ADR que lo retira de R-07 y
  del README, y la cuarta suite de pruebas de datos se arma con Pandera y con
  pruebas de SQL.
- **La revisión del 2 de noviembre es parte de la entrega del 4**, así que cae en la
  semana con menos holgura del semestre. Si se quiere mover, se mueve **antes**, no
  ese día.
