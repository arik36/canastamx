# Plantilla de caso de uso · formato Cockburn

> **Para qué es esto.** Los catorce casos de uso del proyecto se escriben todos
> con el mismo formato. La ficha de entrega dice que CU-02 sirve de plantilla,
> pero **CU-02 vive en el protocolo, no en el repositorio, bravo administración**, así que 
> aquí está el formato desempacado más un ejemplo completo para copiar.
>
> Copia este archivo, renómbralo `CU-XX-nombre-corto.md` y llénalo.

---

## Antes de escribir: qué es y qué no es un caso de uso

Un caso de uso describe **una conversación entre alguien y el sistema para
lograr un objetivo**. Se escribe en prosa numerada, en lenguaje de negocio, y se
lee de corrido.

| **Sí** es un caso de uso | **No** lo es |
|---|---|
| «Configurar una alerta de precio» | «Pantalla de alertas» — eso es una vista |
| «Validar un lote contra el contrato» | «Método `validar()`» — eso es código |
| Tiene un actor con un objetivo | Una lista de campos de un formulario |
| Termina en un resultado observable | «El sistema guarda en la base» |

**La prueba de que está bien escrito:** dáselo a alguien que no programa y pídele
que te cuente qué hace el sistema. Si puede, está bien. Si te pregunta «¿y esto
qué es?», falta lenguaje de negocio.

**Y la regla dura del proyecto:** *un caso de uso sin flujos alternos está
incompleto. Los flujos alternos son donde vive la ingeniería.*

---

## Las nueve secciones, explicadas

| Sección | Qué va ahí | Cómo se equivoca la gente |
|---|---|---|
| **1 · Identificador y nombre** | `CU-09 · Crear y editar una canasta`. Verbo en infinitivo | Ponerle nombre de pantalla en vez de objetivo |
| **2 · Actor primario** | Quién quiere el objetivo. Puede ser una persona o un proceso automático | Poner «el sistema» como actor primario. El sistema no quiere nada |
| **3 · Interesados** | Quién más le importa el resultado, y qué le importa | Dejarlo vacío. Es donde salen requisitos escondidos |
| **4 · Precondiciones** | Qué tiene que ser verdad **antes** de empezar. El sistema las garantiza | Confundirlas con el disparador |
| **5 · Disparador** | El evento concreto que arranca todo | «El usuario quiere…». Un deseo no es un evento |
| **6 · Flujo principal** | Los pasos numerados cuando **todo sale bien**. Alternan actor y sistema | Meter los errores aquí. Los errores van abajo |
| **7 · Flujos alternos** | Qué pasa cuando algo no sale bien, numerado contra el paso del que se desvía | Escribir uno solo, o ninguno |
| **8 · Postcondiciones** | Qué quedó cierto al final. **De éxito y de fallo, las dos** | Olvidar la de fallo: qué queda cuando falla |
| **9 · Requisito no funcional** | Tiempo, volumen o disponibilidad asociados, con número | Poner «debe ser rápido». Rápido no es un número |

**Cómo se numeran los flujos alternos.** Si el paso 3 del flujo principal puede
fallar, sus alternos son `3a`, `3b`, `3c`. Así quien lee sabe exactamente de
dónde se desvía cada uno.

---

## La plantilla en blanco

```markdown
# CU-XX · <verbo en infinitivo + objeto>

- **Actor primario:** 
- **Interesados:** 
  - <quién> — <qué le importa>
- **Precondiciones:** 
  1. 
- **Disparador:** 

## Flujo principal

1. El <actor> …
2. El sistema …
3. …

## Flujos alternos

**3a · <qué sale mal>**
1. El sistema …
2. Vuelve al paso 2 · o · el caso de uso termina sin éxito.

**3b · <otra cosa que sale mal>**
1. …

## Postcondiciones

- **De éxito:** 
- **De fallo:** 

## Requisito no funcional asociado

- 

## Notas

- <decisiones de ADR que aplican, dependencias con otros frentes>
```

---

## Ejemplo completo · para ver cómo se ve terminado

> Éste es el caso de uso del subsistema de datos que el protocolo usa como
> referencia. Está reconstruido a partir de `contracts/qqp-v1.yaml`, así que
> **cuando A escriba CU-01 a CU-07 formalmente tendrá que cotejarlo con el
> protocolo.** Aquí sirve para ver el formato lleno, no como versión final.

# CU-02 · Validar un lote contra el contrato de datos

- **Actor primario:** el proceso de ingesta (actor automático)
- **Interesados:**
  - **Operador de datos** — necesita enterarse de cualquier lote defectuoso sin
    tener que revisarlo a mano.
  - **Analista** — necesita que lo que llega a la capa de consumo esté validado,
    porque sus gráficas se construyen sobre eso.
  - **Consumidor de la app** — no sabe que esto existe, y precisamente por eso
    no puede ver un precio inventado.
- **Precondiciones:**
  1. Existe `contracts/qqp-v1.yaml` en su versión vigente.
  2. La tabla `quarantine_registro` existe y acepta escrituras.
  3. El lote está depositado en la capa cruda y es legible.
- **Disparador:** termina la descarga de un lote y el proceso de ingesta lo
  deposita en la capa cruda.

## Flujo principal

1. El proceso de ingesta lee el contrato vigente y carga sus reglas.
2. El proceso compara las columnas del lote contra las 15 declaradas.
3. El proceso valida cada fila: tipos, rangos, valores requeridos y el techo de
   precio por catálogo.
4. El proceso repara los valores con `?` usando el gemelo de la misma longitud
   de la columna, antes de normalizar.
5. El proceso detecta filas que comparten la clave de fila y resuelve la
   colisión según su diferencia de precio.
6. El proceso deposita las filas válidas en la capa intermedia.
7. El proceso registra la corrida: lote, filas leídas, filas aceptadas, filas
   retenidas, duración.
8. La consola de observabilidad muestra la corrida como correcta.

## Flujos alternos

**2a · El lote trae columnas que el contrato no declara**
1. El proceso **no ingiere** las columnas extra.
2. El proceso levanta un incidente de tipo `deriva_de_esquema`, con la lista de
   columnas inesperadas.
3. Continúa en el paso 3. *El aviso no detiene la ingesta: la política es
   `no_ingerir_con_aviso`.*

**2b · Al lote le falta una columna requerida**
1. El proceso rechaza el lote completo.
2. El proceso levanta un incidente de severidad alta.
3. El caso de uso termina sin éxito.

**3a · Una fila viola una regla de valor**
1. El proceso escribe la fila en `quarantine_registro` con su motivo.
2. Continúa en el paso 3 con la siguiente fila.

**4a · Un valor con `?` no tiene gemelo de la misma longitud**
1. El proceso escribe la fila en cuarentena con motivo
   `codificacion_irrecuperable`.
2. Continúa en el paso 4 con el siguiente valor.

**5a · Dos filas comparten clave y su precio difiere en más de $50**
1. El proceso escribe las dos en cuarentena con motivo `colision_precio_alta`.
2. Continúa en el paso 5.

**7a · La quincena del lote es anterior al umbral de frescura**
1. Si el retraso pasa de 20 días, el proceso levanta un aviso de frescura.
2. Si pasa de 45 días, el proceso rechaza el lote y el caso de uso termina sin
   éxito.

## Postcondiciones

- **De éxito:** la capa intermedia contiene las filas válidas del lote; las
  inválidas están en `quarantine_registro` con su motivo; la corrida quedó
  registrada y visible en la consola.
- **De fallo:** la capa intermedia **no cambió**; el lote quedó marcado como
  rechazado con su causa; hay un incidente abierto en la consola.

## Requisito no funcional asociado

- El incidente queda señalado en la consola en **menos de 15 minutos** desde que
  el lote entró a la capa cruda. *(Es la hipótesis H2.)*
- **Al menos el 95%** de las filas defectuosas queda contenido y no llega a la
  capa de consumo. *(Es la hipótesis H1.)*

## Notas

- Las 15 columnas y sus reglas son las de `contracts/qqp-v1.yaml`.
- El orden de reparar el `?` **antes** de normalizar no es cosmético: al revés,
  `camar n` y `camaron` siguen siendo dos claves distintas.
- Los umbrales de frescura vienen de la decisión 9 del ADR 010.

---

## Errores frecuentes al escribir el tuyo

| Qué pasa | Por qué | Qué hacer |
|---|---|---|
| El flujo principal tiene `if` y `else` | Metiste los errores en el camino feliz | Los errores van en flujos alternos, numerados contra su paso |
| Sólo hay un flujo alterno | Pensaste nada más en el error obvio | Por cada paso del flujo principal pregúntate: ¿qué pasa si esto falla? |
| Dice «el sistema valida los datos» | Es demasiado vago para implementarlo | Di **qué** valida y **contra qué**. El contrato tiene nombre y ruta |
| El RNF dice «rápido» o «eficiente» | No es medible | Ponle número y unidad. Si no lo sabes, dilo: «pendiente de medir en la semana 9» |
| Se parece a una pantalla | Describiste la interfaz en vez del objetivo | Escríbelo sin mencionar botones ni campos. Si no se puede, no era un caso de uso |
