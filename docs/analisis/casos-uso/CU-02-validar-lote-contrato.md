# CU-02 · Validar un lote contra el contrato de datos

- **Actor primario:** el proceso de validación (actor automático)
- **Interesados:**
  - **Operador de datos** — necesita enterarse de cualquier lote defectuoso sin
    tener que revisarlo a mano.
  - **Analista** — necesita que lo que llega a la capa de consumo esté validado,
    porque sus gráficas se construyen sobre eso.
  - **Consumidor de la app** — no sabe que esto existe, y precisamente por eso no
    puede ver un precio inventado.
  - **Equipo del experimento** — necesita que las compuertas atrapen las fallas
    que se inyectan (H1).
- **Precondiciones:**
  1. Existe `contracts/qqp-v1.yaml` en su versión vigente (1.3.3).
  2. La tabla de cuarentena (`quarantine_registro`) existe y acepta escrituras.
  3. El lote está en la capa cruda: CU-01 terminó con éxito.
- **Disparador:** CU-01 termina con éxito y el orquestador dispara la validación.

## Flujo principal

1. El proceso lee el contrato vigente y carga sus reglas.
2. El proceso compara las columnas del lote contra las 15 declaradas.
3. El proceso valida cada fila: tipos, las 13 columnas con valor requerido, el
   rango de precio y el techo de precio por catálogo.
4. El proceso repara los valores con `?` y normaliza los textos (CU-03).
5. El proceso agrupa las filas por la clave de fila (producto, presentación,
   marca, nombre comercial, dirección y fecha, ya reparados y normalizados) y
   resuelve cada grupo según su diferencia de precio. Si difieren en menos de $1,
   es la misma captura dos veces y se queda una. De $1 a $50, se quedan todas.
6. El proceso deposita las filas válidas en la capa intermedia.
7. El proceso mide la frescura: los días entre la fecha de registro más reciente y
   la fecha de referencia de la corrida.
8. El proceso registra la corrida: lote, filas leídas, filas aceptadas, filas en
   cuarentena por motivo y duración.
9. La consola de observabilidad muestra la corrida como correcta (CU-05).

## Flujos alternos

**2a · El lote trae columnas que el contrato no declara**
1. El proceso **no ingiere** las columnas extra.
2. El proceso levanta un aviso de tipo `deriva_de_esquema`, con la lista de
   columnas inesperadas. Pasó con los archivos de junio de 2026: 18 columnas
   contra 15.
3. Continúa en el paso 3. *Es un aviso, no un incidente: la política del contrato
   es `no_ingerir_con_aviso`.*

**2b · Al lote le falta una columna requerida**
1. El proceso rechaza el lote completo.
2. El proceso levanta un incidente de severidad alta (CU-04).
3. El caso de uso termina sin éxito.

**3a · Una fila viola una regla de valor**
1. El proceso escribe la fila en cuarentena con su motivo.
2. Continúa en el paso 3 con la siguiente fila.

**4a · Un texto no se puede reparar**
1. El proceso escribe la fila en cuarentena con motivo `codificacion_irrecuperable`
   (el detalle está en CU-03).
2. Continúa en el paso 4.

**5a · Las filas de un grupo difieren en más de $50**
1. El proceso escribe **el grupo completo** en cuarentena con motivo
   `colision_precio_alta`: con esa diferencia no se sabe cuál precio es el bueno.
2. Continúa en el paso 5. *En el alcance fueron 512 filas, 256 pares (medido en
   T031).*

**5b · La proporción de filas en cuarentena del lote supera el umbral**
1. El proceso no promueve el lote: la capa intermedia no recibe ninguna de sus filas.
2. El proceso levanta un incidente (CU-04).
3. El caso de uso termina sin éxito. *El umbral todavía no está decidido (RF-D07 del
   protocolo; `docs/equipo/decisiones-pendientes.md`, D-07).*

**6a · La capa intermedia no acepta la escritura**
1. El proceso marca la corrida como fallida y no deja filas a medias.
2. El proceso levanta un incidente (CU-04).
3. El caso de uso termina sin éxito.

**7a · El dato más reciente es viejo**
1. Si pasan más de 20 días, el proceso levanta un aviso de frescura.
2. Si pasan más de 45, la capa de consumo deja de publicarse como vigente.
3. *Mientras el corpus esté congelado la regla no aplica: hoy el dato más reciente
   es de 2026-07-Q2. En el experimento la fecha de referencia se fija, para
   inyectar datos viejos a propósito.*

## Postcondiciones

- **De éxito:** la capa intermedia contiene las filas válidas del lote; las
  inválidas están en cuarentena con su motivo; la corrida quedó registrada y
  visible en la consola.
- **De fallo:** la capa intermedia **no cambió**; el lote quedó marcado como
  rechazado con su causa; hay un incidente abierto en la consola.

## Requisito no funcional asociado

- El incidente queda señalado en la consola en **menos de 15 minutos** desde el **inicio de la ingesta** del lote. *(Es la hipótesis H2, como la mide el protocolo en RNF-D02.)*
- **Al menos el 95%** de las filas defectuosas queda contenido y no llega a la capa
  de consumo. *(Es la hipótesis H1.)*

## Notas

- Las 15 columnas y sus reglas son las de `contracts/qqp-v1.yaml`.
- El orden de reparar el `?` **antes** de normalizar no es cosmético: al revés,
  `camar n` y `camaron` siguen siendo dos claves distintas.
- Esta versión sustituye al ejemplo de la plantilla en dos puntos, los dos del
  contrato 1.3.3: en 5a va a cuarentena el grupo completo, y en 7a, a los 45 días,
  se deja de publicar la capa de consumo en lugar de rechazar el lote.
- Los umbrales de frescura vienen de la decisión 9 del ADR 010.
