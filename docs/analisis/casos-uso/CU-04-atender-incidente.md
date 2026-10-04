# CU-04 · Atender un incidente de calidad de datos

- **Actor primario:** operador de datos
- **Interesados:**
  - **Analista** — necesita saber si lo que ve está afectado, y que no se publique
    nada dudoso mientras se resuelve.
  - **Responsable del contrato** — si la causa es una regla equivocada, necesita
    que se cambie por la vía escrita, no en silencio.
  - **Equipo del experimento** — cada incidente cerrado con su causa es evidencia
    para H1 y H2.
- **Precondiciones:**
  1. Hay un incidente abierto con su lote, la compuerta que lo detectó, el motivo
     y el número de filas.
  2. La cuarentena guarda las filas afectadas con su motivo.
- **Disparador:** la consola muestra un incidente nuevo.

## Flujo principal

1. El operador abre el incidente desde la consola.
2. El sistema muestra el lote, la compuerta, el motivo, cuántas filas afecta y un
   ejemplo de cada motivo.
3. El operador revisa las filas en cuarentena y las compara con el archivo
   original.
4. El operador determina que la causa está en el archivo de la fuente.
5. El operador deja el lote marcado para reprocesarse cuando la fuente lo corrija,
   y cierra el incidente con su causa.
6. El sistema registra quién lo cerró, cuándo y por qué.

## Flujos alternos

**3a · No se puede determinar la causa**
1. El operador deja el incidente abierto, con lo que ya se sabe.
2. El incidente se revisa en la reunión semanal.
3. El caso de uso termina sin éxito.

**4a · La causa es una regla del contrato**
1. El operador propone el cambio del contrato, con su porqué, en un PR que tiene
   que aprobar otra persona. Si cambia una decisión, va con ADR.
2. Cuando el cambio entra, el sistema reprocesa el lote con la regla nueva.
3. Continúa en el paso 6, con la causa «regla del contrato».

**4b · El dato es real aunque parezca raro**
1. El operador acepta el dato con un aviso y escribe por qué.
2. Las filas salen de la cuarentena con esa decisión registrada.
3. Continúa en el paso 6.

**4c · La causa es de infraestructura**
1. El operador asigna el incidente al responsable de infraestructura (B).
2. El incidente queda abierto y asignado.
3. El caso de uso termina sin éxito para el operador.

## Postcondiciones

- **De éxito:** el incidente quedó cerrado con su causa, su decisión y la fecha;
  si se reprocesó el lote, la corrida nueva está registrada.
- **De fallo:** el incidente sigue abierto, con lo que se sabe y un responsable;
  el lote en duda no llega a la capa de consumo.

## Requisito no funcional asociado

- El incidente aparece en la consola en **menos de 15 minutos** desde que el lote
  entró a la capa cruda. *(Es la hipótesis H2.)*
- **El 100% de los incidentes cerrados** tiene su causa escrita.

## Notas

- El proceso completo está en el BPMN de incidentes (`docs/analisis/bpmn/incidentes.bpmn`).
- Los motivos son los que declara el contrato: `deriva_de_esquema`,
  `codificacion_irrecuperable`, `colision_precio_alta`, de frescura y de valor.
- En la consola, el rojo es sólo para incidentes; los avisos tienen su propio color
  (sistema de diseño).
