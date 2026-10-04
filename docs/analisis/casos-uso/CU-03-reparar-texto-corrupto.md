# CU-03 · Reparar el texto corrupto o mandarlo a cuarentena

- **Actor primario:** el proceso de transformación de la capa intermedia (actor
  automático)
- **Interesados:**
  - **Analista** — sin reparar, «Camar?n» y «Camarón» serían dos artículos, y la
    serie de precios del camarón quedaría partida en dos.
  - **Consumidor de la app** — busca «camarón» y tiene que encontrarlo.
  - **Operador de datos** — necesita saber qué se reparó, qué no y por qué.
- **Precondiciones:**
  1. El diccionario de reparaciones está versionado en
     `contracts/mojibake-diccionario.csv` (1,650 entradas).
  2. El lote pasó la revisión de columnas y de valores (CU-02, pasos 1 a 3).
- **Disparador:** CU-02 llega a su paso 4 con un lote que trae valores con `?`.

## Flujo principal

1. El proceso busca los valores con `?` en las columnas de texto.
2. El proceso busca cada valor en el diccionario del contrato y lo reemplaza por
   su reparación.
3. El proceso normaliza los textos reparados: sin acentos, sin signos y en
   minúsculas. Es la forma canónica, la misma que usa la clave de artículo.
4. El proceso registra cuántos valores reparó en cada columna.
5. Continúa CU-02 en su paso 5.

## Flujos alternos

**2a · El valor no está en el diccionario y tiene varios candidatos**
1. Si un candidato aparece al menos 10 veces más que el siguiente, el proceso
   repara con él.
2. Si no, la fila va a cuarentena con motivo `revision_humana`.
3. Continúa en el paso 2 con el siguiente valor.

**2b · El valor no tiene ningún candidato**
1. La fila va a cuarentena con motivo `codificacion_irrecuperable`.
2. Continúa en el paso 2 con el siguiente valor.

**2c · El diccionario no se puede leer**
1. El lote no avanza y la capa intermedia no cambia.
2. El proceso levanta un incidente (CU-04).
3. El caso de uso termina sin éxito.

## Postcondiciones

- **De éxito:** todo valor con `?` quedó reparado o en cuarentena con su motivo;
  ningún `?` llega a la capa de consumo.
- **De fallo:** el lote no avanzó; la capa intermedia no cambió; hay un incidente
  abierto.

## Requisito no funcional asociado

- El diccionario repara **el 96.63% de las filas afectadas por `?`** en el alcance
  (contrato, medido sobre 162,079 apariciones).
- **0 filas con `?` llegan a la capa de consumo.**
- Con sólo el diccionario quedan sin reparar **como máximo 5,480 filas** del
  alcance (medido en T031). La regla por frecuencia del alterno 2a las reduce; la
  cifra exacta sale en T048.

## Notas

- La regla es `reparar_interrogantes` del contrato: el diccionario para los
  valores con un solo candidato, la frecuencia para los ambiguos y la cuarentena
  para los que no tienen candidato.
- **Falta decidir en el contrato** si la frecuencia se cuenta en el corpus o en el
  alcance. Se recomienda el corpus, porque de ahí salió el diccionario.
- Se implementa en la capa intermedia de dbt (T048, 25 de octubre).
