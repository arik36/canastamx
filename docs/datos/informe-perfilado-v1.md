# Informe de perfilado · fuente QQP · versión 1

**Fecha:** 18 de septiembre de 2026 · **Autora:** Macías Campos Ariadne Lizett
**Archivos analizados:** 38 CSV quincenales (QQP_2025 y QQP_2026, enero 2025 – julio 2026)
**Volumen total:** 21,357,873 filas

**Estado:** cierra la fase de exploración de la fuente. Sustituye a
`informe-perfilado-v0.md`, que se conserva sin editar porque documenta lo que se
sabía el 11 de septiembre y qué se recomendó con esa información.

> **Este documento sigue fechado el 18 de septiembre y su cuerpo no se reescribe.**
> Después de esa fecha pasaron tres cosas que lo afectan: se calificó la muestra
> de H3 y **H3 no resultó contrastable** (ADR 013), el contrato subió a 1.3.0, y
> se descubrió que dos casillas de la conclusión 2 afirmaban una corrección del
> protocolo que **nunca se aplicó**. Lo falso se corrige en el lugar donde
> estaba; lo nuevo se agrega fechado. El recuento completo está al final, en
> [**Qué cambió después del 18 de septiembre**](#qué-cambió-después-del-18-de-septiembre).

Las decisiones en firme viven en los ADR: [001 · fuente y
recorte](../adr/001-fuente-de-datos.md), [002 · identidad del
artículo](../adr/002-identidad-del-articulo.md), [005 · recorte de
catálogos](../adr/005-recorte-de-catalogos.md), y **004 · cómo se mide H3**.
El contrato de datos está en [`contracts/qqp-v1.yaml`](../../contracts/qqp-v1.yaml).

---

## Qué cambió de la versión 0

La v0 terminó con cinco pendientes y una recomendación que resultó estar mal
razonada. Las dos cosas están resueltas, y **conviene que se lea así**: un
informe que encuentra su propio error y lo corrige con datos vale más que uno
que nunca se equivocó.

| | v0 decía | v1 dice |
|---|---|---|
| Volumen del recorte | por medir | **4,384,962** territorial · **2,658,906** con el recorte de catálogos |
| ¿Hay que corregir el volumen del protocolo? | sí, excede por 384,962 | **no**: con el recorte de productos cae dentro del rango |
| Recorte de productos | sin decidir | cinco catálogos · ADR 005 |
| Artículos del catálogo | «~6,000», estimado a ojo | **1,597** en el alcance del producto · 5,015 en el corpus |
| Comparación difusa | se descarta | **se necesita** · el argumento anterior era circular |
| El `?` | 3.61% del corpus, riesgo acotado | **se repara antes de validar** · confirmado dentro del alcance |

---

## Las tres poblaciones, y por qué se dicen antes que nada

Este informe cita cifras de tres conjuntos distintos, y confundirlos **ya costó
tres campos mal puestos en el contrato**. Cada cifra de aquí en adelante dice de
cuál sale.

| población | filas | qué la define |
|---|---:|---|
| **corpus** | 21,357,873 | los 38 archivos completos |
| **recorte territorial** | 4,384,962 | 7 entidades ∩ 2025-2026 |
| **alcance del producto** | 2,658,906 | lo anterior ∩ los 5 catálogos del ADR 005 |

Una cifra medida sobre una población no vale para otra aunque las dos se llamen
«el recorte». Es una lección barata de escribir y cara de aprender.

---

## 1 · Estructura

**No hay un esquema: hay dos.** 36 archivos traen 15 columnas y 2 traen 18 — las
dos quincenas de junio de 2026 agregan `folio`, `cv_producto` y `cv_marca`, que
**no están en el diccionario oficial de PROFECO**. Julio vuelve a 15.

**No hay una codificación: hay dos.** 36 archivos son UTF-8 con BOM; los dos de
mayo de 2026 son ISO-8859-1 sin BOM. Y esos mismos dos traen la fecha en
`DD/MM/YYYY` mientras el resto usa `YYYY/MM/DD`. **Leer todo con un solo formato
intercambiaría día y mes en 1,007,082 filas.**

| | valor medido · corpus |
|---|---|
| Filas | 21,357,873 |
| Rango de fechas | 2025/01/02 a 2026/07/31 · **fechas ilegibles: 0** |
| Entidades federativas | 37 literales que son **30 entidades reales** |
| Productos distintos | 896 literales · **816** claves normalizadas |
| Cadenas comerciales | 247 |
| Establecimientos (proxy) | 4,334 |
| Nulos en `precio` | **0** |
| Celdas vacías en `latitud` / `longitud` | **0.0086%** en cada una · son las únicas columnas con vacíos |
| `folio`, `cv_producto`, `cv_marca` ausentes | **94.12%** de las filas |

**Faltan Colima y Nayarit por completo.** No aparecen en ninguno de los 38
archivos. La cobertura real es de 30 de las 32 entidades.

**Un tercio del corpus no declara marca.** 7,350,628 filas (**34.4%**) dicen
`S/m` o `S/M`. No son nulos y no son marcas: son una tercera cosa. *Dentro del
alcance del producto son el **20.02%**, no el 34.4%: el resto vivía sobre todo
en Medicamentos, que quedó fuera.*

*Detalle completo y tabla por columna en `perfilado.md`, sección 1.*

## 2 · Rangos y anomalías

**El precio está limpio.** Cero en cero, cero negativos, cero nulos, y **ningún
valor centinela** — buscados con tres detectores distintos. Los 168 precios
redondos que se repiten mucho resultaron ser precios reales: puntos de precio
del comercio (160) o presentaciones caras dentro de una etiqueta de producto
demasiado amplia (8).

> El caso que cierra ese análisis: el termómetro a $999 parecía **10.4 veces**
> más caro que la mediana de su producto. Al mirar su presentación resultó ser
> el modelo que normalmente cuesta **$996**. No había comodín: había un
> termómetro de mercurio y uno infrarrojo compartiendo la etiqueta
> `termometro`.
>
> **De ahí salió la regla más útil del contrato:** cualquier regla sobre
> `precio` se evalúa sobre `producto` + `presentacion`, nunca sobre `producto`
> solo.

**301 duplicados exactos** (0.0014%), todos dentro de un mismo archivo. Es
captura repetida en la fuente, no solape entre quincenas.

**La clave de unicidad del protocolo no aguantaba, y ya está sustituida.**
(`producto`, `nombre_comercial`, `direccion`, `fecha_registro`) dejaba
**12,295,396 filas de más** — más de la mitad del corpus. La que quedó lleva seis
columnas, y la medición de por qué es concluyente: **agregar `marca` salva
286,483 filas legítimas** sólo en el recorte territorial.

Sobre el alcance del producto quedan **74,992 filas (2.82%)** que ni la clave de
seis separa, y el contrato dice qué hace con cada una:

| diferencia de precio dentro del grupo | grupos | filas | qué se hace |
|---|---:|---:|---|
| menos de $1 (máx. $0.95) | 72,629 | 72,631 | captura doble · se deduplica |
| de $1 a $50 (prom. $17.68) | 2,089 | 2,105 | dos observaciones legítimas · se aceptan |
| más de $50 (máx. $200) | 256 | 256 | cuarentena · `colision_precio_alta` |

**La corrupción de texto es el único daño real, y se repara.** 770,273 filas
(3.61% del corpus), en 36 de los 38 archivos. No es un fenómeno, son dos: ruido
crónico de unos cientos de filas por quincena durante todo 2025, y **una falla
masiva en junio de 2026 que por sí sola explica el 97.76%**. Julio vuelve a
estar limpio.

Medido **dentro del alcance del producto**, que es lo que le importa al
contrato:

| | valores distintos | reparación por filas |
|---|---:|---:|
| con gemelo único · se reparan solos | 455 (91.92%) | **96.63%** |
| ambiguos · se resuelven por frecuencia 10:1 | 38 | — |
| sin gemelo · a cuarentena | **2** | 0.04% |

**Dos valores irrecuperables en todo el alcance.** El costo real de la
cuarentena por codificación es, en la práctica, cero — muy lejos del 3.61% que
habría costado la regla ingenua de «rechazar cualquier fila con `?`».

## 3 · Variantes de escritura

**La fuente ya viene normalizada**, en el eje de la escritura: 1.29 formas
distintas de escribir el mismo artículo, mediana 1, máximo 4. Tres de cada
cuatro artículos ya venían escritos de una sola manera.

**Verificación manual: 15 grupos revisados, 0 agrupamientos incorrectos.** Los
cinco grupos con más variantes difieren **únicamente en mayúsculas o acentos**
(`Acido Fólico` / `Ácido Fólico`, `Sistema Gb.` / `Sistema GB.`).

> ### La corrección más importante de esta versión
>
> **La v0 concluyó de aquí que «una normalización determinista resuelve la
> variación entera, sin comparación difusa». Eso no se sostiene, y el error es
> de método, no de medición.**
>
> Las variantes se contaron agrupando literales que caen en la **misma clave
> normalizada**. Pero dos literales que comparten clave normalizada **sólo
> pueden diferir en mayúsculas, acentos y puntuación** — es exactamente lo que
> la normalización quita. Se midió la variación usando nada más los casos que la
> normalización resuelve *por definición*, y de ahí se concluyó que la
> normalización bastaba. **El razonamiento es circular**: mide aciertos
> garantizados y no puede decir nada sobre los fallos.
>
> Cuando se construyó la muestra correcta —pares que **no** comparten clave
> normalizada, con `h3-muestra-para-calificar.py`— aparecieron los casos que
> ninguna regla determinista une: `Mazatán` contra `Mazatún`, `Whirlpool` contra
> `Whirpool`, `1 L` contra `1 Lt`, `Mh 1536 Gir.` contra `Mh1536 Gir.`. Y el
> diccionario de reparación del `?` es, en los hechos, otro mecanismo de
> reconciliación: une `Camar?n` con `Camarón`, cosa que ninguna normalización de
> mayúsculas hace.
>
> **Conclusión corregida: la comparación difusa sí hace falta**, tal como el
> protocolo la comprometió desde el principio —*«una comparación difusa que
> tolere diferencias menores de escritura, abreviaturas y unidades»*—. La
> corrección formal va en el **ADR 004**; el ADR 002 no se edita porque está
> aceptado, y lleva una nota de estado que apunta ahí.
>
> **No hay que corregir el protocolo en este punto.** Al revés: el protocolo
> tenía razón y el análisis intermedio se equivocó. Eso también hay que
> decirlo.

**Y hay otra variación, mucho más grande, que no es de escritura.** `Carne Res`
tiene 57 presentaciones distintas; `Toalla Femenina`, 55. Los 20 productos de
mayor volumen —el 21.8% del corpus— promedian **29.1 presentaciones y 16.1
marcas** cada uno. Ésa no se arregla normalizando: es decidir **qué cuenta como
«el mismo artículo»**, y lo decidió el ADR 002.

### Cuántos artículos hay · la cifra que la v0 dejó mal puesta

La v0 traía «~6,000», una estimación a ojo que se coló como si fuera medición y
que no podía ser cierta: agregar una columna a una clave nunca reduce el número
de claves distintas. Medido, y en las dos poblaciones que importan:

| unidad de emparejamiento | corpus sin `?` | **alcance del producto** |
|---|---:|---:|
| `producto` | 816 | **303** |
| `producto` + `presentacion` ← **decidido** | 5,015 | **1,597** |
| `producto` + `presentacion` + `marca` | 5,750 | **1,992** |

**El catálogo que el producto va a exponer son 1,597 artículos sobre 303
productos** — una media de 5.3 presentaciones por producto. Es mucho más chico
de lo que cualquiera suponía, y la razón es el ADR 005: dejó fuera
`Medicamentos`, que son 401 productos cada uno con su presentación única. **El
recorte de catálogos no sólo quitó filas: quitó la parte del catálogo que más
artículos distintos aportaba por producto.**

Y sin reparar el `?`, ese mismo alcance daría **1,988** artículos. Son **391
fantasmas (24.5%)**: el mismo artículo contado dos veces porque una de sus
escrituras trae `?` —`Camarón` y `Camar?n`, confirmado dentro de `Basicos`—.

---

## Conclusión · las tres preguntas que este informe llevó a la mesa

> **La v0 fue el insumo de la reunión del 11 de septiembre, no su resultado.**
> En dos de las tres preguntas el equipo decidió algo distinto de lo que el
> informe recomendaba, y esta versión conserva las dos posturas a la vista a
> propósito: un informe reescrito para que parezca que siempre estuvo de acuerdo
> con la decisión pierde justo lo que lo hacía útil.

### 1 · ¿La fuente sirve?

- [x] **Sí sirve.** · *ADR 001, aceptado sin cambios*

El precio llegó íntegro, que es la condición que de verdad importaba porque el
precio es la variable del proyecto. Hay 19 meses continuos de serie, 21.4
millones de registros, 30 entidades y 247 cadenas. La suciedad es de texto, está
medida y es reparable.

**Que la fuente esté sucia no la descalifica. Que esté sucia es la premisa del
proyecto.** Lo que la descalificaría sería que el precio no fuera recuperable, y
sí lo es.

### 2 · ¿El recorte comprometido se sostiene?

**No se sostenía, y fallaba en las tres dimensiones a la vez.** Así quedó:

| | El protocolo comprometió | Lo que hay | Cómo se resolvió |
|---|---|---|---|
| Territorio | Guanajuato + 3 vecinas (4 entidades) | 30 entidades, sin Colima ni Nayarit | **7 entidades** de centro-occidente · ADR 001 · **decidido; pendiente de aplicar al protocolo** |
| Ventana | 2024 – 2026 | enero 2025 – julio 2026 | **2025 – 2026** · ADR 001 · **decidido; pendiente de aplicar al protocolo** |
| Volumen | 2 a 4 millones | 21,357,873 | **2,658,906** tras los dos recortes · **no hace falta corregir** |
| Productos | «canasta básica según la fuente» | sin decidir | **5 catálogos** · ADR 005 |

**El punto de volumen cambió de signo respecto de la v0, y el orden en que se
decidió importa.** La v0 midió el recorte territorial en 4,384,962 filas, un
9.6% por encima del máximo comprometido, y concluyó que había que corregir el
protocolo. Pero el protocolo compromete **tres** recortes y sólo se habían
aplicado dos. Al decidir el tercero —el de productos, ADR 005— el recorte baja a
**2,658,906**, que cae dentro de «entre dos y cuatro millones».

**No hay nada que corregir en esa cifra.** Y la lección de método es que
conviene aplicar todas las decisiones antes de declarar que un compromiso se
rompió: por poco corregimos un número que estaba bien.

> **La ampliación de cuatro a siete entidades sí hubo que justificarla**, porque
> es una ampliación y no un recorte. La justificación está en el ADR 001, junto
> con la mención de que Colima y Nayarit quedan fuera por no existir en la
> fuente.
>
> **Corrección del 28 de septiembre:** esta versión decía *«y ya se aplicó al
> protocolo»*, y la tabla de arriba decía *«corregido en el protocolo»* en
> territorio y en ventana. **No era cierto: la decisión se tomó, el documento
> del protocolo nunca se editó.** El texto entregado sigue diciendo «Guanajuato
> y tres entidades vecinas» y «2024 a 2026». Las dos correcciones están en el
> [pliego de correcciones](../entregas/pliego-correcciones-protocolo.md), que se
> aplica en una sola pasada antes del 9 de octubre. Era lo único que este
> informe afirmaba en falso.

### 3 · ¿H3 al 85% de cobertura es realista?

- [x] **Se mide con la muestra construida el 14 de septiembre.** → **ADR 004**

La v0 sospechaba que **los 200 pares podían no existir**, porque PROFECO captura
con su propio catálogo y no deja que cada tienda escriba el nombre. Se midió, y
la respuesta tiene dos partes.

**Existen pares, pero los primeros que se contaron no servían.**
`h3-entre-cadenas.py` encontró **1,730 formas distintas de escritura** en el
corpus (596 dentro del alcance del ADR 005) — más que los 200 que H3 pide. Pero
esos pares se arman uniendo literales que **comparten clave normalizada**, así
que por construcción sólo difieren en mayúsculas, acentos y puntuación.
**Medida así, la cobertura de H3 sale 100% siempre, sin importar qué tan buena
sea la normalización. Una hipótesis que no puede fallar no es una hipótesis.**

**La muestra que sí sirve son los pares que la normalización NO unió**, que son
los únicos donde puede equivocarse. `h3-muestra-para-calificar.py` los construyó
sobre el alcance del ADR 005: **8,654 candidatos**, de los que se tomaron 200
—100 de los más parecidos y 100 al azar del resto, para poder medir cobertura y
precisión—. Esa muestra se calificó a mano el 17 de septiembre y **el ADR 004 la
resuelve**.

> **Tres cosas que el ADR 004 tiene que dejar escritas**, y salieron de
> construir la muestra:
>
> **El número define el artículo; las letras son las que se escriben distinto.**
> La primera versión del muestreo ordenaba por parecido de texto y sus diez
> mejores candidatos eran pares como `400 000 Ui` contra `800 000 Ui` — se
> parecen en 60 de 61 caracteres y son dosis distintas. El guión ahora exige que
> los dígitos coincidan y mide el parecido sólo sobre las letras.
>
> **La cobertura se cuenta sobre los pares que difieren en `producto` o
> `presentacion`.** El muestreo arma pares sobre la clave de tres columnas, pero
> el ADR 002 define el artículo con dos, así que hay pares que difieren sólo en
> `marca` y son el mismo artículo *por definición del contrato*. Si se mezclan,
> la cobertura sale inflada con pares que ninguna reconciliación tuvo que
> resolver.
>
> **La comparación difusa entra**, por lo dicho en la sección 3.

**Y hay una candidata para reenunciar H3 si la muestra confirma que el eje de la
escritura es fácil:** reconciliar **presentaciones** dentro de un mismo producto.
`Carne Res` tiene 57. Eso ninguna normalización lo resuelve, y sí es
investigación.

**Ajustar o reenunciar una hipótesis en septiembre, con datos, es método.
Hacerlo en noviembre porque no salió es otra cosa.**

> ### Resultado · 28 de septiembre de 2026
>
> **Los dos párrafos de arriba se conservan palabra por palabra, y ésa es la
> razón por la que importan.** Fueron escritos el 18 de septiembre, antes de
> calificar un solo par, y dejaron apuntada la alternativa con nombre. Lo que
> sigue es lo que pasó después, y no cambia una coma de lo anterior.
>
> **La muestra se calificó y la regla del ADR 004 se activó en contra del
> resultado que convenía: 18 «sí» en la mitad por parecido, con el umbral en
> 20.** Dos calificaciones propias —los pares 026 y 029— estaban mal hechas y se
> corrigieron a «no»; se habían justificado por frecuencia de filas, que es
> exactamente el criterio que el ADR 004 había rechazado por escrito. La muestra
> no se regeneró y ningún otro par se tocó.
>
> **H3 no resultó contrastable sobre esta fuente**, por dos razones medidas e
> independientes: el fenómeno que nombra casi no está (1.29 formas por artículo,
> mediana 1), y su métrica de cobertura no puede fallar —lo dice este mismo
> informe, en esta misma sección, desde el 18 de septiembre—.
>
> **H3 no se reenuncia: se reporta con sus criterios de 85% y 90% intactos**, y
> la reconciliación entra como **hipótesis nueva, H5 · reconciliación de
> presentaciones**, con sus umbrales pendientes de un ADR de piloto que se
> escribe *antes* de medir. Se numera H5 y no H3′ a propósito: renumerarla
> borraría el rastro de que se planteó, se intentó contrastar y se encontró
> algo.
>
> Todo lo anterior, con la evidencia y la cadena de fechas, en el
> [**ADR 013**](../adr/013-h3-resultado-y-h5.md).

---

## Lo que la v0 dejó pendiente · estado al 18 de septiembre

| # | pendiente | estado |
|---|---|---|
| 1 | Volumen del recorte de siete entidades | **cerrado** · 4,384,962 |
| 2 | El recorte de productos | **cerrado** · ADR 005 · 2,658,906 |
| 3 | El «~6,000» mal puesto | **cerrado** · 5,015 corpus · 1,597 alcance |
| 4 | Los pares de H3 | **cerrado** · muestra construida y calificada → ADR 004 · *resultado el 28-sep → ADR 013* |
| 5 | Si PROFECO publica 2024 | **por confirmar** · consulta al portal |

---

## Tres hallazgos que la versión 0 no tenía

### La fuente lleva 48 días sin dato nuevo

El registro más reciente del corpus es **2026-07-31**. Al 18 de septiembre son
48 días, y la compuerta de frescura del contrato dispara a los 20 —QQP publica
por quincena, así que 20 días sin dato nuevo es incidente de fuente, no dato
viejo—.

O PROFECO publicó agosto y septiembre y no se han descargado, o dejó de
publicar. **Las dos son incidentes reales que el sistema detecta el día uno, sin
simular nada**, y por eso conviene que la compuerta se quede como está en vez de
aflojarla para que no moleste.

### `catalogo` y `categoria` no están anidadas

Son dos clasificaciones **independientes** de la fuente, y eso matiza el ADR
005: se excluyó el catálogo `Medicamentos` y aun así entran **8,212 filas de
`categoria = medicamentos`** por la puerta de `Basicos`.

**No es un defecto, y el detalle es lo interesante:** los que entran son 3
productos con mediana de $30 y máximo de $134 —analgésico de mostrador—, contra
los 401 productos con mediana de $245 y máximo de $5,891 del catálogo que quedó
fuera. **El recorte por catálogo se quedó con el medicamento básico de una
despensa y dejó fuera el de receta**, sin que nadie lo planeara así.

### `Basicos` es más ancho que «la despensa»

Su categoría más grande es `arts. para el cuidado personal` con **290,136
filas — el 10.9% de todo el alcance**. Y contiene `cerveza` (35,000),
`vinos y licores` (26,197) y `cigarrillos` (3,794).

El contrato **los ingiere igual**: el protocolo compromete la clasificación *de
la fuente*, y sacar artículos porque nos parecen poco básicos sería sustituirla
por un criterio propio que habría que defender caso por caso. Lo que se resuelve
es el mensaje: la vista por omisión de «canasta básica» oculta esas tres
categorías —**64,991 filas, el 2.44%**—, reversible por el usuario y escrita en
el contrato. **Sirve además para H4**: la canasta básica alimentaria de CONEVAL
no incluye bebidas alcohólicas, así que el índice se puede reportar con y sin
ellas y decir cuál es cuál.

---

## Observación de fondo

**La fuente se degradó y se recuperó sola dentro del periodo observado.** En
2026 `estado` y `catalogo` ganaron los acentos que les faltaban en 2025,
mientras `giro` y `categoria` los perdieron convertidos en `?`. Junio reventó,
con 18 columnas y 753 mil filas rotas. Julio volvió a la normalidad en las dos
cosas a la vez.

**Un sistema que ingiera esto sin compuertas publica junio como si nada.** Eso
es exactamente lo que este proyecto dice que va a detectar, y ahora está medido
con números propios en lugar de argumentado en abstracto.

Y hay una segunda observación, sobre el trabajo y no sobre la fuente. **Este
perfilado no sólo describió los datos: encontró cuatro compromisos del protocolo
que no se sostenían y corrigió dos errores propios**, todo con evidencia medida
y todo en septiembre, que es cuando cambiar de opinión todavía no cuesta nada.

- Dos entidades que el protocolo daba por cubiertas y que no existen en la fuente.
- Una ventana temporal que no era la que se creía.
- Una clave de unicidad que habría mandado a cuarentena 12 millones de filas buenas el día de la primera ingesta.
- Una hipótesis que, como estaba escrita y medida, no podía fallar.
- Un «~6,000» estimado a ojo que se había colado como medición.
- Y una conclusión propia —que la comparación difusa no hacía falta— que resultó apoyarse en un razonamiento circular.

Los dos últimos son errores de este informe, y están corregidos aquí con su
explicación. **Ésa es la diferencia entre un sistema que se vigila a sí mismo y
uno que se cree lo que le llega**, que es justamente el objeto de investigación
del proyecto.

---

## Qué cambió después del 18 de septiembre

**El cuerpo de este informe se dejó como estaba.** Un informe reescrito para que
coincida con lo que se supo después deja de ser un informe y pasa a ser un
resumen. Lo que se corrigió son las dos afirmaciones que eran **falsas** —no
incompletas: falsas— y lo que se agregó va fechado y marcado.

| # | qué | dónde quedó en este documento | fuente |
|---|---|---|---|
| 1 | **H3 no resultó contrastable.** 18 «sí» de 20 en la mitad por parecido; la regla del ADR 004 se activó y se siguió | bloque «Resultado · 28 de septiembre» al cierre de la pregunta 3, sin borrar lo anterior | [ADR 013](../adr/013-h3-resultado-y-h5.md) |
| 2 | **Entra H5 · reconciliación de presentaciones**, con umbrales pendientes de un ADR de piloto | mismo bloque | [ADR 013](../adr/013-h3-resultado-y-h5.md) §5.3 |
| 3 | **Dos calificaciones propias estaban mal hechas** (pares 026 y 029, justificadas por frecuencia de filas, criterio que el ADR 004 rechazaba) | mismo bloque | `perfilado/h3-muestra-para-calificar.txt`, líneas `CORREGIDO` |
| 4 | **«Corregido en el protocolo» era falso** en territorio y ventana: se decidió, no se aplicó | tabla de la conclusión 2 y el blockquote que sigue | [pliego de correcciones](../entregas/pliego-correcciones-protocolo.md) |
| 5 | **El contrato subió a 1.3.0.** La ventana se cierra en `2025-01-01 … 2026-07-31`, la frescura gana bloqueo a 45 días y se suspende mientras el corpus esté congelado, y `reparar_interrogantes` gana `catalogo` y `estado` | no se toca el cuerpo · ver la nota de abajo | [`contracts/qqp-v1.yaml`](../../contracts/qqp-v1.yaml) |

**Sobre la compuerta de frescura**, que este informe recomendó *«que se quede
como está en vez de aflojarla para que no moleste»*: el umbral de aviso **sigue
en 20 días** y la recomendación se respetó. Lo que cambió es otra cosa y conviene
no confundirla con aflojarla. El ADR 010, decisión 9, **congeló el corpus** en la
segunda quincena de julio de 2026 para que el experimento corra sobre un conjunto
estable. Con el corpus congelado la compuerta dispara todos los días por diseño,
y una alarma que suena siempre no informa nada: deja de leerse. Por eso 1.3.0
añade `no_aplica_mientras: corpus_congelado` y separa **avisar** (20 días) de
**bloquear la publicación** (45 días). La compuerta no se relajó: se le quitó el
ruido que ella misma generaba por una decisión ajena, y se dejó escrito de qué
depende que vuelva a aplicar.

**Lo que este informe midió no cambió.** Ninguna de las cifras de las secciones 1
a 3 se movió: los 21,357,873 del corpus, los 2,658,906 del alcance, los 1,597
artículos, el 3.61% de mojibake y los dos valores irrecuperables siguen siendo
los mismos números, medidos sobre las mismas poblaciones. Lo que cambió es una
hipótesis y una afirmación sobre el protocolo, y las dos están arriba con su
fecha.
