# ADR 013 · H3 no resultó contrastable sobre esta fuente; entra H5

> # ⚠ RETIRADA · 28 de septiembre de 2026
>
> **Este ADR no se sostiene y no se aplica. Lo retira el
> [ADR 014](./014-recuento-h3.md).** Se conserva sin editar, igual que el
> `informe-perfilado-v0.md`, porque borrarlo dejaría once días sin explicar en un
> expediente cuyo valor es la trazabilidad.
>
> **Qué pasó.** Una segunda lectura independiente de la muestra, hecha por Karen
> (D) el mismo día y sin conocer el conteo, encontró **12 «sí» más** entre los 82
> «no» de la mitad por parecido —73 de los cuales no llevaban una sola palabra de
> justificación—. El conteo pasó de **18 a 30**, con el umbral del ADR 004 en 20,
> así que la regla se activa en su **primera** rama: **H3 se mide como está
> enunciada.** Que era, exactamente, lo que el ADR 004 había decidido el 17 de
> septiembre.
>
> **Y no falla sólo el conteo: fallan los dos argumentos del §5.2**, los dos por
> error de quien firma este documento.
>
> 1. **«El fenómeno casi no está: 1.29 formas por artículo».** Ese 1.29 sale de
>    la medición que `perfilado.md` §3 y el informe v1 declaran **circular**. Se
>    usó como prueba el número que el propio proyecto había descalificado, en el
>    mismo documento donde lo descalificó.
> 2. **«Su métrica de cobertura no puede fallar».** Era una objeción a cómo
>    `h3-entre-cadenas.py` armaba los pares, no a H3.
>    `h3-muestra-para-calificar.py` se construyó para corregir eso, y sobre esa
>    muestra la cobertura **sí** puede fallar: acaba de fallar 30 veces de 100.
>
> **Lo que sigue siendo válido de aquí:** el §5.1, donde se corrigen los pares
> 026 y 029 por haberse justificado con un criterio que el ADR 004 rechazaba —esa
> corrección estaba bien hecha y sigue en pie—, y el §5.4, que se negó a fijar
> umbrales sin un piloto. Todo lo demás lo reemplaza el ADR 014.
>
> **Lo que NO hay que sacar de aquí:** que reportar un resultado incómodo estuvo
> mal. Estuvo bien. Lo que estuvo mal fue el resultado.

- **Fecha:** 28 de septiembre de 2026
- **Estado:** **RETIRADA** el 28 de septiembre de 2026 por el
  [ADR 014](./014-recuento-h3.md). Nunca se ratificó, así que no hubo votación
  que revocar
- **Autora:** Ariadne (A)
- **Corrige:** la **aplicación** del ADR 004, no su contenido. El ADR 004 no se
  edita: su regla era correcta y es la que manda este documento
- **Toca también:** el protocolo de investigación, en tres lugares

> **Este ADR existe porque una regla escrita de antemano se activó en contra del
> resultado que queríamos, y se sigue.** Ésa es toda la decisión. Lo demás es
> dejar constancia de cómo se llegó ahí, incluido un error de quien firma.
>
> **H3 no se modifica.** Se reporta con sus criterios intactos y con el
> resultado de haber intentado contrastarla. La reconciliación de presentaciones
> entra como **hipótesis nueva, H5**, con sus propios criterios fijados antes de
> medir. La sección 11 del protocolo promete *«sin ajuste retrospectivo de los
> criterios»*, y ésta es la única forma de cumplirlo al pie de la letra.

---

## 1 · Qué decía la regla

El [ADR 004](./004-h3-como-se-mide.md), escrito el **17 de septiembre**, fijó
cómo se calificaría la muestra de 200 pares **antes de calificar un solo par**:

- **100 pares elegidos por parecido** — los casos difíciles
- **100 pares elegidos al azar** — la frecuencia del problema en general

Y dejó escrita la regla de decisión:

> **Si en la mitad por parecido hay 20 «sí» o más**, el problema de
> reconciliación existe en esta fuente y H3 se mide como está enunciada
> (cobertura ≥ 85%, precisión ≥ 90%).
> **Si hay menos de 20**, casi no hay nada que reconciliar por escritura y **H3
> se reenuncia** sobre presentaciones dentro de un producto.

**Por qué se escribió antes.** Porque una regla decidida después de ver el
número siempre encuentra la justificación del número que conviene. Escribirla
antes es lo que hace que decidan los datos. Es la misma disciplina que el
proyecto le exige a la ingesta: la compuerta se pone antes de que pase el dato,
no después de ver qué pasó.

---

## 2 · Qué salió, y qué se descubrió después

### El conteo original

| Mitad | «sí» | «no» |
|---|---:|---:|
| Por parecido (001–100) | **20** | 80 |
| Al azar (101–200) | 3 | 97 |

**Exactamente 20.** El mínimo justo. El ADR 004 ya lo marcó con un aviso: *«el
resultado cayó exactamente en el umbral»*, sin margen.

### Los cinco «sí» que necesitaron excepción

De los 20, cinco no se resolvían con las preguntas P1 o P2 y se anotó una
excepción sobre la P3. La P3, tal como está escrita en el encabezado del archivo
de la muestra, dice:

> **P3 · Una escritura tiene una palabra de más. Se clasifica LA PALABRA:**
> · estado, tamaño, corte, tipo, variedad, **grado**, **origen**, sabor,
>   ingrediente, propiedad nutricional o envase → **NO**
> · nombre de línea comercial, color de empaque, o algo que la norma o la
>   costumbre ya dan por hecho → **SÍ**

Tres de las cinco excepciones **citan la P3 y la aplican**:

| Par | Palabra de más | Clasificación |
|---|---|---|
| 024 | «rinde» | nombre de línea → SÍ |
| 030 | «clásica» | nombre de línea → SÍ |
| 039 | «agua» | la gelatina de limón siempre es de agua → no restringe → SÍ |

**Dos no citan ninguna regla.** Citan una razón de filas:

| Par | Los dos literales | Justificación escrita |
|---|---|---|
| **026** | Jitomate… **Primera** vs Jitomate… **Primera Nacional** | *«"nacional" aparece en 1 de cada 142 filas: anotación esporádica, no línea»* |
| **029** | Jitomate… vs Jitomate… **Primera** | *«"primera" aparece en 283 filas contra 45,076: anotación, no grado del producto»* |

### Por qué eso invalida esas dos calificaciones

**Primero, y esto no necesita interpretar ninguna regla: la muestra se
contradice a sí misma.** El mismo archivo, el mismo producto y la misma palabra,
calificados al revés:

```
par 016   Jitomate · 1 Kg. Granel. Saladette/huaje … Primera     [x] no
          vs  … Tercera
          CORREGIDO · P2 · «primera» y «tercera» son dos grados, los dos explícitos

par 029   Jitomate · 1 Kg. Granel. Saladette/huaje               [x] sí
          vs  … Primera
          EXCEPCIÓN · «primera» aparece en 283 filas contra 45,076: anotación, no grado
```

Es **el mismo literal** —incluso las mismas 283 filas— y en el par 016 «primera»
es un **grado** y en el 029 es una **anotación**. Las dos calificaciones no
pueden ser correctas a la vez. Y la del 016 lleva su propia marca `CORREGIDO`:
ya se había revisado una vez y se había resuelto como grado.

**Segundo: la P3 los clasifica, y los manda al otro lado.** «Nacional» es
**origen**. «Primera» es **grado** — el propio ADR 004 la llama así cuando
describe la P2 con el ejemplo *«primera/tercera»*, que es exactamente el par 016.
Los dos están en la lista que va a **NO**.

**Tercero, y es peor: el criterio que se usó en su lugar ya estaba descartado
por escrito, en este mismo proyecto y por la misma persona.** El ADR 004
documenta, en su apartado de cómo se calificó, que la heurística por conteo de
filas se probó como criterio general y **se rechazó porque no separa**:
reproducía cuatro ejemplos elegidos a mano y fallaba al aplicarse a los 51
casos.

O sea: se escribió la razón por la que ese criterio no sirve, y dos pares
después se decidió con él.

**Cuarto: movió el resultado exactamente al umbral.** Sin esas dos, la mitad da
18; con ellas, 20. El mínimo era 20. **No hay peor lugar para doblar una regla
que justo encima de la línea que esa regla traza.**

> **Esto es un error de quien firma este documento**, y no es un error de
> cálculo: es de método, que es precisamente el objeto de esta investigación.
> Queda escrito aquí con nombre y apellido porque borrarlo costaría más que
> admitirlo.

### El conteo corregido

| Mitad | Antes | Después |
|---|---:|---:|
| Por parecido (001–100) | 20 sí · 80 no | **18 sí · 82 no** |
| Al azar (101–200) | 3 sí · 97 no | 3 sí · 97 no |
| **Total** | 23 | **21** |

**La regla evalúa la mitad por parecido: 18 < 20.**

---

## 3 · La alternativa que se consideró, y por qué no

**Se podría argumentar que la P3 está mal**, y que «primera» en el jitomate es
una anotación del capturista y no una calidad del producto. El argumento no es
tonto: 283 filas contra 45,076 es un patrón de captura irregular, no de un
producto distinto.

**Y aun así no se toma.** Por tres razones:

| | |
|---|---|
| **Se cambiaría la regla después de ver el resultado** | Que es exactamente lo que la regla escrita de antemano existe para impedir |
| **El cambio favorece al propio sistema** | Reclasificar «primera» como anotación sube el conteo. Toda enmienda que empuja el resultado hacia donde conviene tiene que sospecharse primero |
| **No hay evidencia, hay intuición** | Nadie midió si «primera» se usa como grado en esta fuente. Se supuso a partir de que sale poco |

**Si el equipo quiere de verdad esa enmienda**, el camino existe y es otro: se
mide si «primera» funciona como grado —por ejemplo, viendo si los precios de las
filas con «primera» difieren sistemáticamente de las que no la traen—, se
escribe un ADR que corrija la P3 **con esa evidencia**, y **la muestra se vuelve
a calificar entera** con la regla nueva. No dos pares: los 200.

Eso cuesta días y no cambia el fondo, porque el hallazgo del perfilado sigue en
pie. Por eso la recomendación es aplicar la regla literal.

---

## 4 · Lo que el perfilado ya había encontrado, y que sostiene lo que sigue

Reenunciar H3 **no es no haber llegado al número**. Es que el problema que el
protocolo describe **no se presenta en esta fuente como la literatura lo
describe**, y eso está medido desde hace dos semanas.

**La variación de escritura entre cadenas es casi nula.**

| | |
|---|---|
| Formas de escribir el mismo artículo | **1.29** · mediana **1** |
| Agrupamientos incorrectos en revisión manual de 15 grupos | **0** |
| Los cinco casos con más variantes | difieren **sólo en mayúsculas o acentos** (`Acido Fólico` / `Ácido Fólico`) |

El protocolo, en su §3.3, ilustra el problema con
`"LECHE LALA ENTERA 1 L"` · `"Leche Lala Ent. 1LT"` · `"LALA LECHE ENTERA 1000 ML"`.
**Ese fenómeno prácticamente no ocurre aquí.**

**Pero hay otra variación, mucho más grande, que no es de escritura.**

| | |
|---|---|
| `Carne Res` | **57 presentaciones** |
| `Toalla Femenina` | **55 presentaciones** |
| Los 20 productos de mayor volumen | **29.1 presentaciones** y 16.1 marcas cada uno |
| El catálogo del alcance | **1,597 artículos** sobre **303 productos** · media **5.3** |

Eso no lo junta ninguna normalización de texto, **ni debe**: un kilo de carne no
es un paquete de 200 gramos. Lo que hace falta ahí no es unir escrituras, es
**extraer la unidad comparable** para poder comparar un litro contra un litro.

**Y la calificación de la muestra dejó la prueba de que el parecido textual no
sirve para eso:**

| Par | Parecido | ¿El mismo artículo? |
|---|---:|---|
| `congelado` / `descongelado` | **0.962** | **NO** |
| `letra` / `letras` | **0.994** | **SÍ** |

Dos pares casi idénticos para una medida de parecido, y en lados opuestos.
**La similitud textual no separa lo que hay que separar en esta fuente.** Ése es
el hallazgo, y es más interesante que el 85%.

---

## 5 · Decisión

### 5.1 · Se aplica la regla del ADR 004

Las calificaciones de los pares **026** y **029** se corrigen a «no», con su
línea `CORREGIDO` y la razón, en `h3-muestra-para-calificar.txt`. **La muestra no
se regenera y ningún otro par se toca.**

El resultado queda en **18 «sí» en la mitad por parecido**, por debajo del
umbral de 20. La regla se activa.

### 5.1 bis · La alternativa no se inventa hoy: estaba pre-registrada

Esto importa tanto como la regla. **La alternativa estaba escrita, con nombre,
antes de calificar un solo par.** El informe de perfilado v1, del **18 de
septiembre**, dice:

> *«Y hay una candidata para reenunciar H3 si la muestra confirma que el eje de
> la escritura es fácil: reconciliar **presentaciones** dentro de un mismo
> producto. `Carne Res` tiene 57. Eso ninguna normalización lo resuelve, y sí es
> investigación.»*

Y cierra esa sección con la frase que este documento no podría decir mejor:

> *«Ajustar o reenunciar una hipótesis en septiembre, con datos, es método.
> Hacerlo en noviembre porque no salió es otra cosa.»*

**Hoy es 28 de septiembre.** No se está sustituyendo una hipótesis que falló por
otra que convenga: se está ejecutando la alternativa que el propio proyecto
había dejado apuntada, en la fecha en que dijo que se podía hacer.

Y no es lo único que ya estaba dicho. **El ADR 001, del 11 de septiembre, dejó
H3 formalmente abierta**, con esta casilla sin marcar:

> *«- [ ] Se sostiene la meta de 85% de cobertura y 90% de precisión
>   - [x] **Queda abierta.** No se alcanzó a tratar en la reunión del 11.»*

y con la sospecha ya escrita: *«H3 mide la solución a un problema que esta
fuente no tiene»*.

**Lo que este ADR hace, entonces, no es abrir una discusión: es cerrar una que
lleva abierta desde el 11 de septiembre**, con el dato que faltaba.

> **Y ejecuta un voto, no lo contradice.** El [ADR 010](./010-acta-de-decisiones-semana-03.md),
> decisión 8, el equipo votó **4 a 1** por *«la regla tal como está»*. Aplicarla
> es obedecer esa votación.

---

### 5.2 · H3 se reporta, no se ajusta

**H3 queda tal como está escrita, con sus criterios de 85% y 90% intactos**, y
se le agrega el resultado de haber intentado contrastarla:

> **H3 no resultó contrastable sobre esta fuente.** Por dos razones medidas, y
> son independientes entre sí:
>
> **1 · El fenómeno que nombra casi no está.** «Variación de escritura de
> nombres de producto entre cadenas»: **1.29 formas por artículo, mediana 1**,
> cero agrupamientos incorrectos en la revisión manual de 15 grupos, y los cinco
> casos con más variantes difieren **sólo en mayúsculas o acentos**. PROFECO
> captura con su propio catálogo: hay 896 nombres de producto para 247 cadenas.
>
> **2 · Su métrica de cobertura no puede fallar.** Está medido y escrito desde
> el 18 de septiembre, en el informe de perfilado v1: los pares se arman uniendo
> literales que comparten clave normalizada, así que por construcción sólo
> difieren en lo que la normalización quita. *«Medida así, la cobertura de H3
> sale 100% siempre, sin importar qué tan buena sea la normalización. **Una
> hipótesis que no puede fallar no es una hipótesis.**»*

**Esto es un resultado, no un ajuste.** Y es el resultado más incómodo de
reportar y el más útil de los cuatro: dice algo sobre la fuente que la
literatura no anticipaba.

> **Por qué importa la diferencia entre «reportar» y «reenunciar».** Reenunciar
> H3 —cambiarle el objeto y conservarle el nombre— haría desaparecer del
> expediente que se planteó, que se intentó contrastar y qué se encontró. Visto
> desde fuera sería indistinguible de bajar el listón. Reportarla deja el rastro
> completo, que es exactamente lo que la sección 11 del protocolo compromete.

### 5.3 · Entra H5 · reconciliación de presentaciones

La hipótesis que **sí** es contrastable sobre esta fuente, y que este proyecto
ya había identificado por escrito el 18 de septiembre:

> **H5 · Reconciliación de presentaciones.** Dado el campo libre `presentacion`,
> el sistema extrae una **unidad comparable** —cantidad y unidad de medida
> canónica— que permite comparar precios entre presentaciones equivalentes del
> mismo producto.

Se mide con los dos indicadores de siempre, que se reportan juntos:

| Indicador | Qué cuenta |
|---|---|
| **Cobertura** | Proporción de los 1,597 artículos del catálogo a los que se les asigna una unidad comparable `(cantidad, unidad)` |
| **Precisión** | Proporción de esas asignaciones que resulta correcta al verificarse a mano sobre muestra aleatoria |

**Ejemplos de lo que tiene que resolver:** `1 L` y `1 Lt` a la misma unidad;
`500 Ml` a media unidad de litro; `620 Gr` y `1 Kg` a la misma escala de peso;
`30 Pzas` a conteo. Y **lo que tiene que reconocer que no puede resolver**:
`Granel`, `Paquete Grande`, `Pieza` — presentaciones sin cantidad declarada, que
no son un fallo de la extracción sino una propiedad de la fuente.

**Por qué ésta sí puede fallar**, que es lo que le faltaba a H3: la extracción
de cantidad y unidad **puede equivocarse de forma observable y contable**. Puede
no encontrar la cantidad donde la hay, puede leer `620 Gr` como 620 unidades, y
puede unir dos presentaciones que no son equivalentes. Se mide sobre los 1,597
artículos reales, no sobre pares elegidos por parecerse.

> **Se numera H5 y no H3′ a propósito.** H3 sigue existiendo en el expediente,
> con su resultado. Renumerarla borraría el rastro.

### 5.4 · Los umbrales de H5 NO se fijan en este documento

**Y ésa es una decisión, no un olvido.**

Los 85% y 90% de H3 se heredaron del protocolo sin una base escrita. Poner un
número sin base fue parte de cómo llegamos hasta aquí, y repetirlo sería no
haber aprendido nada.

**Los umbrales de H5 se fijan en un ADR aparte, antes de medir, sobre un piloto
de 30 artículos elegidos al azar.** El piloto existe para una sola cosa: saber
si el umbral que se propone es exigente. Un umbral que se cumple solo no prueba
nada —es el defecto que acaba de costarnos H3— y uno imposible tampoco.

| Si el piloto muestra que… | El umbral… |
|---|---|
| La extracción resuelve casi todo sin esfuerzo | sube, o el indicador se cambia por uno que sí discrimine |
| La extracción falla en la mayoría | baja, y se documenta por qué el problema era más duro de lo previsto |
| Queda en medio | se fija ahí, con el número del piloto como respaldo |

**El ADR del piloto se escribe y se acepta antes de correr la medición
completa.** No después. La secuencia importa tanto como el número.

---

## 6 · Qué cambia, y qué no

### Cambia

| Dónde | Qué |
|---|---|
| `docs/datos/perfilado/h3-muestra-para-calificar.txt` | Dos calificaciones corregidas, con su línea `CORREGIDO` |
| `docs/datos/informe-perfilado-v1.md` | Un apartado con el hallazgo: el problema de escritura casi no existe aquí; la variación está en las presentaciones |
| **Protocolo · §5** | La fila de H3 gana su resultado; entra una fila H5 |
| **Protocolo · §7** | El objetivo específico de reconciliación, que repite el mismo criterio de 85/90 |
| **Protocolo · §3.3** | La descripción del problema, hoy ilustrada con un fenómeno que esta fuente casi no presenta |
| **T053** · semana 8 | «Reconciliación de productos versión uno» pasa a ser de presentaciones |
| **T058** · semana 9 | Mide **H5**, no H3, con los umbrales del ADR del piloto |

> **Ya que se abre el protocolo**, hay otra cosa desfasada que no tiene que ver
> con H3: el **§8** dice *«recorte geográfico a Guanajuato y tres entidades
> vecinas, ventana temporal de 2024 a 2026»*, y el **ADR 001** decidió **siete
> entidades** con ventana desde **2025-01-01**. Conviene corregirlo en la misma
> pasada.

### No cambia

| | |
|---|---|
| **ADR 002** | El artículo sigue siendo `producto` + `presentacion`. `marca` sigue sin identificar |
| **ADR 004** | Su regla era correcta. **No se edita**: este documento la aplica |
| **El modelo de dominio** | Intacto |
| **El modelo dimensional** | Intacto. Ya dejaba la reconciliación para después, como tabla de equivalencias aparte |
| **El contrato de datos** | Intacto |
| **H1, H2 y H4** | Intactas |
| **El objetivo general** | Intacto |

---

## 7 · Consecuencias por frente

**A · datos.** Ejecuta todo lo anterior. Corrige la muestra, recuenta, escribe
el apartado del informe, prepara la corrección del protocolo y escribe el ADR
del piloto antes de T058.

**B · infraestructura.** Aviso, sin trabajo ahora. El protocolo compromete
*«mínimo cinco tipologías de falla, treinta ejecuciones y contraste formal de las
hipótesis planteadas»*. Si cambia una hipótesis, cambia qué se contrasta. Le
llega en **T049** (semana 7) y en el experimento de la semana 13.

**C1 · dominio. Ninguna consecuencia.** Se dice explícito porque es lo primero
que se va a temer: **el ADR 002 no se toca.**

**C2 · móvil.** Nada esta semana. Le llega en **T051**, cuando conecte la
búsqueda con datos reales. Lo que debe saber desde ya: **el parecido textual no
separa** —`congelado` y `descongelado` a 0.962— así que la búsqueda no puede
apoyarse en él para decidir qué es el mismo artículo.

**D · web. Ninguna consecuencia.** Comprobado contra el protocolo: los seis
indicadores de la consola son última ejecución, frescura, resultado de
validaciones, linaje, historial de incidentes y volumen en cuarentena. **Ninguno
mide reconciliación.**

---

## 8 · Cómo se le presenta esto al asesor

**No como un ajuste de metas.** Como un resultado.

1. **Declaramos una regla de decisión el 17 de septiembre**, antes de calificar
   la muestra, y quedó escrita en el ADR 004.
2. **Al revisar las calificaciones encontramos que dos de las veinte se habían
   resuelto con un criterio distinto del declarado** —y además con uno que el
   propio ADR 004 había descartado por escrito—.
3. **Corregidas, el resultado queda en 18 y la regla se activa.**
4. **Se sigue.** H3 se reporta como no contrastable, con sus criterios
   intactos, y entra **H5** sobre lo que el perfilado ya había mostrado que es
   el problema real de esta fuente.

El punto 2 es el que hay que decir en voz alta y no esconder. Un proyecto que
encuentra su propio error de método y lo corrige contra su interés es más
creíble que uno que llega con los cuatro números en verde.

**Y hay una lectura que conviene ofrecerle**, porque es verdad: este episodio es
el mismo fenómeno que el proyecto investiga, ocurrido en el propio equipo. El
sistema detecta cuando los datos se rompen porque la regla está escrita antes y
se aplica aunque duela. Aquí la regla estaba escrita antes, casi no se aplica, y
lo que la salvó fue una revisión independiente. **Eso es material para las
conclusiones, no un tropiezo que ocultar.**

---

## 9 · Lo que esta decisión deja abierto

**Los umbrales.** Los fija el ADR del piloto, antes de medir. Está en el
apartado 5.3.

**Si «primera» es grado o anotación.** No se midió. Si alguien lo mide y resulta
que es anotación, la P3 se corrige **con esa evidencia** y **la muestra se
recalifica entera**, no dos pares.

**El acuerdo entre calificadores.** El ADR 004 reporta 90.5% de acuerdo y kappa
0.578 sobre la muestra original. Con dos calificaciones corregidas esas cifras
cambian ligeramente y hay que recalcularlas antes de citarlas otra vez.

**La numeración de los ADR.** Este documento tomó el 013 después de comprobar
que el 011 y el 012 están ocupados. La colisión del 011 ocurrió porque el número
se elige al escribir y no se aparta en ningún lado. **Propuesta para T032: el
número de ADR se reserva en el tablero antes de empezar a escribirlo.**

## Referencias

- [ADR 002](./002-identidad-del-articulo.md) — la identidad del artículo, que no cambia
- [ADR 004](./004-h3-como-se-mide.md) — la regla que este documento aplica
- `docs/datos/perfilado/h3-muestra-para-calificar.txt` — la muestra y sus 200 calificaciones
- `docs/datos/informe-perfilado-v1.md` — las cifras de variación de escritura y de presentaciones
- `CanastaMX_Protocolo_Investigacion.docx` — §3.3, §5, §7 y §8
