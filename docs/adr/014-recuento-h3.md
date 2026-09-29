# ADR 014 · Recuento de la muestra de H3 · la rama vuelve a la primera

- **Fecha:** 28 de septiembre de 2026
- **Estado:** **propuesta** · la ratifica el equipo. El asesor tiene que
  enterarse antes de la entrega del 9 de octubre
- **Autora del recuento:** **Karen (C2)** · segunda lectura independiente
- **Redacta:** Ariadne (A), que es quien se equivocó
- **Retira:** el [ADR 013](./013-h3-resultado-y-h5.md), que nunca se ratificó
- **Restituye:** la decisión original del [ADR 004](./004-h3-como-se-mide.md),
  sin cambiarle una coma

> **En cuatro líneas.** El ADR 013 declaró que H3 no era contrastable sobre esta
> fuente, apoyado en un conteo de 18 «sí» contra un umbral de 20. Una segunda
> lectura independiente de la muestra, hecha por quien no la había calificado
> antes, encontró **12 «sí» más**. El conteo queda en **30** y la regla del
> ADR 004 se activa en su primera rama: **H3 se mide como está enunciada.** Eso
> es exactamente lo que el ADR 004 había decidido el 17 de septiembre, así que
> lo que se retira es un desvío de once días, no una decisión del equipo.

---

## 1 · La regla, y el hecho de que ella misma previó este recuento

El [ADR 004](./004-h3-como-se-mide.md) §4 fijó la regla **antes** de contar un
solo «sí»:

| si la mitad por parecido da… | entonces |
|---|---|
| **≥ 20 «sí»** | la hipótesis tiene material real. **Se mide como está enunciada**, 85% de cobertura y 90% de precisión |
| **< 20 «sí»** | la normalización ya cubre casi todo y la meta no puede fallar. Se reenuncia H3 |

Su primera calificación dio **20**, exactamente en el umbral. Y el ADR 004 no lo
escondió: dedicó un bloque de aviso a decir que el margen era cero, y dejó
escrito qué hacer si el conteo se movía:

> *«Si para entonces la calificación se revisa por cualquier motivo, **el conteo
> se recalcula y la rama se vuelve a evaluar**, con la misma regla y dejando
> constancia del cambio. No se congela un resultado de frontera.»*

**Este ADR es esa cláusula ejecutándose.** No es una decisión nueva ni una
excepción: es el procedimiento que el propio ADR 004 escribió para este caso,
usado por primera vez. Conviene subrayarlo porque el reflejo natural, al ver que
un resultado se vuelve a mover, es sospechar que se está negociando el número
hasta que salga el que conviene. Lo que impide eso es que **la regla y el umbral
no se han tocado**: siguen siendo los del 17 de septiembre, y el 20 nunca se
movió.

---

## 2 · Qué hizo Karen, y por qué su lectura pesa más que las dos anteriores

El ADR 004 dejó anotada, con todas sus letras, la debilidad de su propia
calificación:

> *«No fue una calificación a ciegas ni una doble calificación independiente: la
> propuesta se generó primero y se revisó par por par. Se anota así porque cambia
> lo que el número significa.»*

Y dio la medida del problema: acuerdo del 90.5% entre propuesta y revisión,
**kappa de Cohen 0.578**, con 17 de 19 correcciones en la misma dirección. Un
kappa de 0.58 sobre un criterio declarado es acuerdo moderado, no bueno.

**Lo que faltaba era una segunda lectura independiente, y ésta es la primera.**
Karen calificó **32 pares** de la mitad por parecido:

- todos ellos venían marcados «no» **sin una sola palabra de justificación** —73
  de los 82 «no» estaban así—;
- se eligieron **mecánicamente**, sin juzgar el par: los «no» sin razón escrita
  en los que la palabra que cambia es un **color** o en los que un lado
  simplemente trae una **palabra de más**. Son las dos formas que la regla P3
  puede mandar al lado del «sí»;
- Karen **no había visto la calificación anterior** de esos pares, ni el conteo,
  ni el ADR 013;
- **escribió la razón de cada uno**, que es lo que los 73 no tenían.

El único criterio prohibido —decidir por número de filas, que el ADR 004 rechazó
por escrito y que es el error que se corrigió en los pares 026 y 029— **no
aparece en ninguna de sus 32 justificaciones.**

---

## 3 · El recuento

**12 «sí» nuevos:** 015, 020, 025, 027, 028, 031, 041, 046, 050, 053, 064, 089.

| escenario | conteo | ¿cruza el umbral de 20? |
|---|---:|---|
| **A · la lectura de Karen tal como la entregó** | 18 + 12 = **30** | **sí** |
| **B · aplicando además las reglas ya escritas del ADR 004** (ver abajo) | 18 + 15 = **33** | **sí** |
| **C · descartando TODO lo discutible**, y quedándose sólo con los cuatro que nadie puede discutir | 18 + 4 = **22** | **sí** |

**El escenario C es el que decide**, porque es el que no depende de ningún juicio
contestable. Los cuatro son colores de envoltura y de envase:

| par | A | B |
|---|---|---|
| 027 | `jabon de pasta · barra 400 gr con envoltura` | `… con envoltura rosa` |
| 028 | `jabon de pasta · barra 400 gr con envoltura` | `… con envoltura azul` |
| 046 | `jabon de pasta · barra 400 gr con envoltura azul` | `… con envoltura rosa` |
| 089 | `talco para bebe · botella 200 gr azul` | `… botella 200 gr rosa` |

La regla P3 manda **«color de empaque → sí»**. En `con envoltura rosa` el color
califica literalmente la envoltura. Y Karen dio para el talco el argumento más
corto y más difícil de rebatir de toda la lectura: *«jamás he visto polvo de
talco de color»*.

**Karen tendría que haberse equivocado en nueve de sus doce pares para que el
umbral no se cruzara.**

### 3 bis · Lo que suma el escenario B, y de dónde sale

No de un criterio nuevo. De aplicar lo que el ADR 004 ya tenía escrito y que
nadie aplicó:

**El par 078 · `crema solida · frasco 200 gr` contra `frasco 200 ml`.** Está
calificado «no». Pero la pregunta **P1** del ADR 004 manda a «sí» las diferencias
de **unidad (`gr`/`ml`)** sin pasar por P3 — y el propio ADR 004, en la sección
«Lo que la calificación deja ver», **cita `200 gr` / `200 ml` como uno de sus 23
«sí»**. El ADR y el archivo calificado se contradicen en un par concreto. Bajo la
regla escrita, es «sí».

**Los pares 063 y 090 · el desempate que el ADR 004 ya tenía.** Karen escribió,
en los dos, que la palabra podía ser de cualquiera de las dos clases:

> 063 · `aqua` — *«puede referirse a una variante, aroma o línea específica»*
> 090 · `naranja` — *«podría ser tanto el color del empaque como el sabor»*

Y calificó «no» las dos. Pero el ADR 004 cierra su regla con esta línea:

> *«Default cuando P3 no alcanza a decidir: **sí**. Asumir que se escapó uno es
> la postura que no favorece al propio sistema.»*

**Bajo la regla escrita, esos dos son «sí».** No porque convenga: porque el
default se escribió el 17 de septiembre precisamente para que la duda no se
resolviera en favor del sistema, y aquí la duda está escrita de puño y letra por
la calificadora.

> **Esto no se lo apuntamos como error a Karen.** El formato que se le entregó
> le dio la regla P3 pero **no le dio el default**, porque quien lo escribió
> —yo— había afirmado unas horas antes que el default no existía. El hueco es
> del formato, no de la lectora.

---

## 4 · Por qué el ADR 013 se retira y no se enmienda

Porque no falla su conteo: **fallan sus dos argumentos**, y los dos son errores
de quien lo firmó.

### 4.1 · «El fenómeno que nombra casi no está: 1.29 formas por artículo»

Ese 1.29 se obtiene contando cuántos literales crudos caen en la **misma clave
normalizada**. Es exactamente la medición que `perfilado.md` §3 y el informe v1
declaran **circular**, con estas palabras:

> *«se midió la variación usando únicamente los casos que la normalización
> resuelve por definición. El razonamiento es circular y no puede concluir nada
> sobre lo que la normalización NO une.»*

**El ADR 013 usó como prueba el número que el propio proyecto ya había
descalificado**, en el mismo documento donde lo descalificó. No es un dato mal
copiado: es una medición inválida reciclada como evidencia once días después de
haberla declarado inválida.

### 4.2 · «Su métrica de cobertura no puede fallar»

Esto era una objeción a **cómo `h3-entre-cadenas.py` armaba los pares** —uniendo
literales que ya compartían clave normalizada, de donde la cobertura sale 100%
siempre—. El ADR 004 lo dice en su lista de alternativas descartadas, y por eso
descartó ese método y construyó otro.

`h3-muestra-para-calificar.py` arma pares entre claves **distintas**, que son
los únicos donde el sistema puede equivocarse. **Sobre esa muestra la cobertura
sí puede fallar**, y acaba de fallar 30 veces de 100.

**El ADR 013 convirtió una crítica a un método ya descartado en una crítica a la
hipótesis.** Las dos «razones independientes» de su §5.2 eran, entonces, la
misma pieza mal usada dos veces: una medición circular y una objeción huérfana.

### 4.3 · Y un tercer error, de esta semana

Al preparar la segunda lectura afirmé que **el ADR 004 no tenía desempate** para
una palabra que puede ser de dos clases, y propuse escribir uno. Sí lo tiene:
está en la línea siguiente a la tabla P3 y dice «default: sí». **Proponer
escribir una regla que ya existía es el mismo defecto que este proyecto estudia
—no leer lo que el propio sistema ya declaró— aplicado a la documentación.**

> **El ADR 013 no se borra.** Se queda en el repositorio con su estado cambiado
> a **retirada**, y este ADR como razón. Borrarlo dejaría el expediente con una
> decisión del 17 de septiembre, otra del 28, y nada que explique los once días
> de por medio. Nunca se ratificó, así que no hay que revocar ninguna votación:
> hay que dejar constancia de un desvío.

---

## 5 · Decisión

**1 · La rama que aplica es la primera del ADR 004 §4.** Con 30 «sí» en la mitad
por parecido contra un umbral de 20, **el problema de reconciliación existe en
esta fuente y H3 se mide como está enunciada:**

> **H3 · la reconciliación de nombres de artículo entre cadenas alcanza una
> cobertura ≥ 85% con precisión ≥ 90%**, sobre la muestra construida según el
> ADR 004 §1.

**2 · El umbral no se mueve.** Sigue en 20, como desde el 17 de septiembre. Lo
que se movió fue el conteo, y por una segunda lectura, no por una
reinterpretación.

**3 · H5 queda SIN EFECTO. No se aplaza: no existe.** Y conviene que la
respuesta sea así de tajante, porque es la pregunta que va a hacer todo el mundo.

H5 no era una hipótesis que alguien hubiera propuesto por sus méritos: era **el
instrumento de la rama 2**. El ADR 004 §4 ya la traía nombrada como «el eje de
reenunciación, ya identificado», y la reenunciación **sólo ocurre si la mitad por
parecido da menos de 20 «sí»**. Dio 30. La rama 2 no aplicó, así que la
reenunciación no ocurre, y lo que existía únicamente para ejecutarla se queda sin
razón de ser.

**El problema que H5 nombraba sigue siendo real** —`Carne Res` tiene 57
presentaciones y ninguna normalización las junta— y sigue escrito donde siempre
estuvo: en el ADR 004 §4, como el eje que se habría usado. Si algún día el equipo
la quiere como hipótesis, **va en un ADR propio con su propia justificación**, no
heredada de un documento retirado. Cuatro hipótesis y dos semanas para la entrega
no es el momento de estrenar una quinta que ninguna medición pidió.

**4 · La tasa de omisión que se reporta cambia de 20 a 30 de cada 100.** El
ADR 004 cierra diciendo que lo único afirmable hoy es *«la tasa de omisión de la
normalización determinista vigente sobre el estrato difícil: **20 de cada 100**
pares de alta similitud que no unió eran en realidad el mismo artículo»*. Con el
recuento son **30 de cada 100**. La normalización vigente es **la mitad de peor**
de lo que el expediente decía, y ése es el número que va al informe.

**5 · El conteo vigente es 30, y el archivo calificado lo refleja par por par.**
Las 12 calificaciones de Karen entran con su razón escrita y con su nombre. Los
pares en disputa (§6) quedan marcados como tales y **no** se cuentan en el 30;
si se resuelven a «sí», el conteo sube.

---

## 5 bis · La consecuencia técnica, que es la más cara de todas

**Los «sí» dejaron de ser todos ortográficos, y eso rompe el diseño de T053 tal
como está escrito.**

El ADR 004 afirma, sobre sus 23 «sí»: *«son además de un solo tipo, todos
ortográficos»*, y lista cinco formas —plural, conector, abreviatura, unidad y
orden de palabras—. De ahí saca la receta de T053: *«un conjunto de reglas
dirigidas a esas cinco formas… y la comparación difusa encima de eso»*.

**Los 12 «sí» de Karen no son ninguna de las cinco.** Son de dos clases nuevas:

| clase | ejemplos | ¿lo resuelve normalizar plural/unidad/orden? | ¿lo resuelve comparación difusa? |
|---|---|---|---|
| **color de empaque** | `con envoltura` / `con envoltura rosa` · `talco 200 gr azul` / `rosa` | no | **no** · difieren en una palabra entera |
| **nombre de línea comercial** | `liquido limon` / `liquido pure lemon` | no | **no** · por lo mismo |

Esto es lo que hay que ver y no es cómodo: **la comparación difusa tampoco los
une.** `jabon de pasta barra 400 gr con envoltura` contra
`…con envoltura rosa` difieren en una palabra completa; cualquier métrica de
distancia de cadenas los separa, y bajar el umbral hasta que los junte uniría
también `congelado` con `descongelado`, que es el caso de prueba que el propio
ADR 004 dejó para detectar un umbral demasiado flojo.

**Hace falta un sexto mecanismo que el expediente no tiene:** una **lista de
palabras que no identifican al artículo** —colores de empaque, nombres de línea
comercial— que se quitan antes de comparar, igual que el diccionario del `?`
repara antes de normalizar. No es comparación difusa: es una decisión de
vocabulario, revisable, versionada, y con el mismo problema que todo lo demás de
este proyecto —quién la aprueba y cómo se audita—.

> **Y trae su propia trampa, que hay que escribir antes de implementarla.** La
> misma palabra identifica o no según el producto: `azul` no identifica un jabón
> pero **sí** identifica `agave azul` en el tequila y `pan blanco` contra
> `integral`. La lista no puede ser global: tiene que ser **por producto o por
> categoría**, y eso es más trabajo del que T053 tenía presupuestado.

**Lo mete al alcance este ADR y le pone dueño: es de A, en T053, semana 8.** El
umbral difuso se sigue calibrando como decía el ADR 004 —unir los «sí» sin unir
los «no»— pero ahora con 30 «sí» en el numerador y con dos clases que el difuso
no puede atender sola.

---

## 6 · Lo que queda en disputa, y por qué no cambia nada

Cinco de los 32 tienen problemas que hay que resolver antes de cerrar el
archivo. **Ninguno mueve la rama**, porque el escenario C ya la decide sin ellos.

| par | problema | quién lo resuelve |
|---|---|---|
| **064** | La casilla vino escrita `[]` en vez de `[ ]`, así que un lector automático no la cuenta. Y es **la misma estructura que el par 063**, que Karen calificó «no»: `jabon de tocador · barra 135 gr` contra `135 gr aqua` frente a `150 gr` contra `150 gr rosa`. Una de las dos está mal | Karen, con el default escrito a la vista |
| **031** | Respuesta correcta, clasificación equivocada. `agave azul` **no** es color de empaque: es la variedad botánica *Agave tequilana* Weber var. azul. Cae en «sí» por la otra puerta de P3 —todo el tequila es legalmente de agave azul, así que es *algo que la norma ya da por hecho*— | se corrige la razón, no el veredicto |
| **050 · 053** | `tortilla de maiz · 1 kg granel amarilla` contra `amarilla chica`. **«Chica» es tamaño**, y P3 manda tamaño a «no». El argumento de Karen —que los kilos son los mismos— no responde a que la tortilla es de otro tamaño | el equipo. Si son «no», el conteo baja a 28 |
| **022** | La razón escrita clasifica «light» pero declara que la palabra que cambia es «azul y light». Falta clasificar «azul» | Karen |

---

## 7 · Qué se mueve en cada documento

| documento | qué afirma hoy que dejó de ser cierto |
|---|---|
| **`docs/adr/013-*.md`** | todo · pasa a **retirada** con una nota de cabecera que apunta aquí |
| **`contracts/qqp-v1.yaml`** → 1.3.2 | cuatro líneas: el cierre de la cabecera 1.3.0 («H3 dejó de ser la hipótesis de la reconciliación»), la viñeta de los comentarios de H3, y dos menciones de H5 en `clave_de_articulo.por_que_se_fija_esto`. **Ninguna regla cambia; son comentarios** |
| **`docs/datos/informe-perfilado-v1.md`** | el bloque «Resultado · 28 de septiembre» entero, la nota de cabecera, el renglón 4 de la tabla de pendientes de la v0 y los renglones 1 a 3 de la tabla final |
| **`docs/datos/perfilado/h3-muestra-para-calificar.txt`** | 12 calificaciones y sus razones, más las cinco marcas de disputa |
| **`docs/adr/004-h3-como-se-mide.md`** | **no se edita** · lleva una nota de estado que apunta aquí. Lo que queda desactualizado en su cuerpo, y que este ADR sustituye: la tabla de resultados (20 → 30), la frase «los 23 «sí» son todos ortográficos», la tasa de omisión de 20 de cada 100, y la receta de T053 de las cinco formas. **Su regla, su umbral y su método siguen intactos y son los que manda este recuento** |
| **el panel** | la tarjeta de H3 y la de H5 |
| **`docs/entregas/pliego-correcciones-protocolo.md`** | lo que dijera sobre reenunciar H3 |

---

## 8 · Lo que esto vale para la investigación, y por qué conviene contarlo

El objeto de este trabajo es un sistema que detecta cuándo sus propios datos se
rompen. Lo que pasó entre el 17 y el 28 de septiembre es ese mismo mecanismo,
aplicado a las personas en vez de a las filas, funcionando **dos veces y en
contra de quien lo escribió**:

1. **Primera vez.** Una regla fijada por anticipado se activó contra el resultado
   que convenía a la coordinadora, y se siguió: dos calificaciones propias mal
   hechas bajaron el conteo de 20 a 18 y obligaron a abandonar H3.
2. **Segunda vez.** La misma regla, leída por otra persona que no había visto la
   primera calificación, subió el conteo a 30 y obligó a abandonar el abandono.

**Y hay una asimetría que importa más que las dos.** En el primer caso el error
se encontró solo, revisando el propio trabajo. En el segundo **hizo falta otra
lectora**: el conteo de 18 era autoconsistente, tenía un documento de 461 líneas
defendiéndolo, y nadie lo habría movido desde dentro. Setenta y tres de los
ochenta y dos «no» no llevaban una sola palabra de razón, y eso no se ve cuando
lo mira quien los marcó.

> **La lección de método, y es la que va al informe:** revisar tu propio trabajo
> encuentra los errores de ejecución. **Los errores de criterio necesitan a otra
> persona.** Una compuerta de calidad de datos es precisamente eso —un segundo
> lector que no escribió la fila—, y el proyecto acaba de comprobar en su propia
> carne por qué no basta con que el autor revise dos veces.

Sin la segunda lectura de Karen, la entrega del 9 de octubre habría reportado que
una hipótesis no era contrastable, apoyándose en una medición que el mismo
expediente declaraba circular. **Eso es lo que este recuento evitó**, y es
material de resultados, no de disculpas.

---

## 9 · Alternativas descartadas

**Bajar el umbral de 20, o subirlo.** Es la tentación en las dos direcciones y
por eso se dice explícito: el 20 no se toca. Está escrito desde el 17 de
septiembre y ya sobrevivió a un resultado que no convenía.

**Enmendar el ADR 013 cambiándole el número de 18 a 30.** No alcanza. Sus dos
argumentos fallan independientemente del conteo, y dejarlos en pie con otro
número los vuelve a poner en circulación.

**Borrar el ADR 013 del repositorio.** Dejaría once días sin explicar en un
expediente cuyo valor es justamente la trazabilidad.

**Regenerar la muestra y calificarla de cero.** Habría sido lo más limpio en
abstracto y es lo peor en concreto: la muestra vigente tiene tres calificaciones
encima con su historia, y tirarla borra la evidencia de los dos errores. El
ADR 004 §4 ya había decidido esto: se recalcula el conteo, no se rehace la
muestra.

**Esperar a la semana 9 (T058) y resolverlo ahí.** La entrega del 9 de octubre
reportaría algo falso durante dos semanas, y el asesor lo leería antes.

---

## 10 · Qué falta

1. **Ratificación del equipo.** Es un cambio de hipótesis, que es lo que el
   ADR 010 §8 votó 4 a 1 mantener bajo regla. La regla se está siguiendo.
2. **Cerrar los cinco pares en disputa** (§6), con el default escrito a la vista.
3. **Un par donde el ADR 004 y el archivo se contradicen.** El ADR cita
   `200 gr` / `200 ml` como uno de sus 23 «sí» por la pregunta P1 (unidad), y el
   **par 078** —`crema solida · frasco 200 gr` contra `frasco 200 ml`— está
   calificado «no» en el archivo. Uno de los dos está mal y hay que decir cuál.
4. **Las 50 calificaciones «no» de la mitad por parecido que Karen no leyó** —las
   que no eran de color ni de omisión— siguen sin razón escrita. Bajo la regla
   deberían ir a «no», pero eso no está verificado y el precedente de esta semana
   dice que no conviene suponerlo. Es lectura de una hora y sube o baja el conteo,
   no la rama.
5. **La mitad al azar (100 pares, 3 «sí»)** nunca se ha releído. Mide precisión,
   no cobertura, así que no toca esta decisión — pero sí toca la meta del 90%.
6. **La lista de palabras que no identifican** (§5 bis), por producto o por
   categoría. Entra a T053 y no estaba presupuestada.
7. **Avisar al asesor**, con este documento, antes del 9 de octubre.

---

## 11 · Quién decidió qué

| | |
|---|---|
| Escribió la regla y el umbral, antes de los datos | Ariadne (A) · ADR 004, 17 de septiembre |
| Ratificó la regla «tal como está», 4 a 1 | el equipo · ADR 010 §8 |
| Calificó la muestra la primera vez, no a ciegas | Ariadne (A) · 24 de septiembre |
| Se equivocó en dos pares y lo corrigió | Ariadne (A) · 28 de septiembre |
| Escribió el ADR 013 con dos argumentos que no se sostienen | Ariadne (A) · 28 de septiembre |
| **Volvió a leer 32 pares sin conocer el conteo, y encontró 12 «sí»** | **Karen (C2) · 28 de septiembre** |
| Redacta este ADR | Ariadne (A) |
| Ratifica | el equipo, pendiente |
