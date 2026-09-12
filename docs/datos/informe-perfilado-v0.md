# Informe de perfilado · fuente QQP · versión 0

<!-- Lo escribe A en T006 · jueves 10 de septiembre.
     Esto NO es un resumen: es una RECOMENDACIÓN. La diferencia está en el
     último párrafo. Un resumen termina en "estos son los hallazgos"; una
     recomendación termina en "por lo tanto propongo esto, y estos números
     lo sostienen". -->

**Fecha:** 11 de septiembre de 2026 · **Autora:** Macías Campos Ariadne Lizett
**Archivos analizados:** 38 CSV quincenales (QQP_2025 y QQP_2026, enero 2025 – julio 2026)
**Volumen total:** 21,357,873 filas

**Estado:** es el insumo de la reunión de decisión del 11 de septiembre.
Las decisiones que salieron de él están en
[`docs/adr/001-fuente-de-datos.md`](../adr/001-fuente-de-datos.md) y
[`docs/adr/002-identidad-del-articulo.md`](../adr/002-identidad-del-articulo.md).
**La versión 1 se cierra el 17 y 18 de septiembre** con las cuatro mediciones
pendientes que se listan al final.

---

## Resumen para quien no va a leer el resto

**La fuente sirve y hay que quedarse con ella.** El precio —que es la variable
del proyecto— llegó íntegro: ni un nulo, ni un cero, ni un negativo, y **ningún
valor centinela**, buscados con tres detectores distintos. La suciedad está en el
texto: 3.61% de las filas traen caracteres corrompidos, y **el 96.82% de las
apariciones de texto roto se repara de forma determinista**.

**Pero el recorte que comprometimos en el protocolo no coincide con lo que
hay**, en las tres dimensiones a la vez, y eso es lo que se decidió en la
reunión del viernes 11.

---

## 1 · Estructura

**No hay un esquema: hay dos.** 36 archivos traen 15 columnas y 2 traen 18 — las
dos quincenas de junio de 2026 agregan `folio`, `cv_producto` y `cv_marca`, que
**no están en el diccionario oficial de PROFECO**. Julio vuelve a 15.

**No hay una codificación: hay dos.** 36 archivos son UTF-8 con BOM; los dos de
mayo de 2026 son ISO-8859-1 sin BOM. Y esos mismos dos traen la fecha en
`DD/MM/YYYY` mientras el resto usa `YYYY/MM/DD`. Leer todo con un solo formato
intercambiaría día y mes en 1,007,082 filas.

| | valor medido |
|---|---|
| Filas | 21,357,873 |
| Rango de fechas | 2025/01/02 a 2026/07/31 · **fechas ilegibles: 0** |
| Entidades federativas | 37 literales que son **30 entidades reales** |
| Productos distintos | 896 |
| Cadenas comerciales | 247 |
| Establecimientos (proxy) | 4,334 |
| Nulos en `precio` | **0** |
| Celdas vacías en `latitud` / `longitud` | **0.0086%** en cada una · son las únicas columnas con vacíos |
| `folio`, `cv_producto`, `cv_marca` ausentes | **94.12%** de las filas |

**Faltan Colima y Nayarit por completo.** No aparecen en ninguno de los 38
archivos. La cobertura real es de 30 de las 32 entidades.

**Un tercio del corpus no declara marca.** `marca` no tiene celdas vacías, pero
7,350,628 filas (**34.4%**) dicen `S/m` o `S/M`. No son nulos y no son marcas:
son una tercera cosa que el contrato tiene que decidir cómo tratar.

*Detalle completo y tabla por columna en `docs/datos/perfilado.md`, sección 1.*

## 2 · Rangos y anomalías

**El precio está limpio.** Cero en cero, cero negativos, cero nulos. Se buscaron
valores centinela —esos 999 o 9999 que un capturista teclea cuando no sabe el
precio— con tres detectores, y **no hay**. Los 168 precios redondos que se
repiten mucho resultaron ser precios reales: puntos de precio del comercio (160)
o presentaciones caras dentro de una etiqueta de producto demasiado amplia (8).

> El caso que cierra ese análisis: el termómetro a $999 parecía **10.4 veces**
> más caro que la mediana de su producto. Al mirar su presentación resultó ser el
> modelo que normalmente cuesta **$996**. No había comodín: había un termómetro
> de mercurio y uno infrarrojo compartiendo la etiqueta `termometro`.

**301 duplicados exactos** (0.0014%), todos dentro de un mismo archivo. Es
captura repetida en la fuente, no solape entre quincenas.

**La clave de unicidad que habíamos propuesto no aguanta.**
(`producto`, `nombre_comercial`, `direccion`, `fecha_registro`) deja **12,295,396
filas de más**: más de la mitad del corpus. Tiene sentido —el mismo
establecimiento cotiza el mismo producto en varias presentaciones el mismo día—
y apunta a la misma decisión que la sección 3.

**La corrupción de texto es el único daño real.** 770,273 filas (3.61%), en 36 de
los 38 archivos. No es un fenómeno, son dos: ruido crónico de unos cientos de
filas por quincena durante todo 2025, y **una falla masiva en junio de 2026 que
por sí sola explica el 97.76%**. Julio vuelve a estar limpio.

| clase | valores | apariciones | % |
|---|---:|---:|---:|
| **reparable** de forma determinista | 1,650 | 1,088,196 | **96.82%** |
| ambiguo (más de un candidato) | 63 | 31,703 | 2.82% |
| irrecuperable | 25 | 4,095 | **0.36%** |

*Detalle en `docs/datos/perfilado.md`, sección 2.*

## 3 · Variantes de escritura

**La fuente ya viene normalizada.** 1.29 formas distintas de escribir el mismo
artículo, mediana 1, máximo 4. Ningún artículo pasa de 10 variantes. Tres de cada
cuatro ya venían escritos de una sola manera.

**Verificación manual: 15 grupos revisados, 0 agrupamientos incorrectos.** Y el
hallazgo no es el cero, es el patrón: los cinco grupos con más variantes difieren
**únicamente en mayúsculas o acentos** (`Acido Fólico` / `Ácido Fólico`,
`Sistema Gb.` / `Sistema GB.`). Ninguna variante semántica, ningún error de dedo.
La variación de esta fuente es mecánica, y eso significa que una normalización
determinista la resuelve entera, sin comparación difusa.

**Pero hay otra variación, mucho más grande, que no es de escritura.**
`Carne Res` tiene 57 presentaciones distintas. `Toalla Femenina`, 55.
`Leche Ultrapasteurizada`, 13 presentaciones y 30 marcas. Los 20 productos de
mayor volumen —el 21.8% del corpus— promedian **29 presentaciones y 16 marcas**
cada uno. La mediana general de 2 presentaciones por producto es un espejismo: la
fijan los medicamentos de marca, que aparecen con una sola.

Ésa no se arregla normalizando. Es decidir **qué cuenta como «el mismo
artículo»**, y de eso depende H3.

*Detalle en `docs/datos/perfilado.md`, sección 3.*

---

## Conclusión

> **Este informe fue el insumo de la reunión del 11 de septiembre, no su
> resultado.** Las secciones 1 a 3 son lo que se midió, y no cambian: los datos
> son los mismos antes y después de la reunión.
>
> Lo que sigue son las tres preguntas que el informe llevó a la mesa, cada una
> con **lo que el informe recomendaba** y **lo que el equipo decidió**. En dos de
> las tres no fue lo mismo, y se dejan las dos versiones a la vista a propósito:
> un informe que se reescribe para que parezca que siempre estuvo de acuerdo con
> la decisión pierde justo lo que lo hacía útil.
>
> Las decisiones en firme viven en `docs/adr/001-fuente-de-datos.md` y
> `docs/adr/002-identidad-del-articulo.md`.

### 1 · ¿La fuente sirve?

- [x] **Sí sirve.**
- [ ] **No sirve.** → se activa el plan alternativo

**Razón:** el precio llegó íntegro —cero nulos, cero en cero, cero negativos y
ningún valor centinela—, que es la condición que de verdad importaba, porque el
precio es la variable del proyecto. Hay 19 meses continuos de serie, 21.4
millones de registros, 30 entidades y 247 cadenas. La suciedad es de texto, está
medida (3.61%) y es reparable en un 96.82%.

**Y conviene decirlo explícitamente:** que la fuente esté sucia no la
descalifica. **Que esté sucia es la premisa del proyecto.** Lo que la
descalificaría sería que el precio no fuera recuperable, y sí lo es.

> **Decidido el 11 de septiembre · ADR 001.** El equipo aceptó la recomendación
> sin cambios.

### 2 · ¿El recorte comprometido se sostiene?

El protocolo declara en Alcances, literalmente: *«Recorte geográfico a
**Guanajuato y tres entidades vecinas**, con ventana temporal de 2024 a 2026,
correspondiente a un volumen estimado entre dos y cuatro millones de
registros»*.

**No se sostiene, y falla en las tres dimensiones a la vez:**

| | El protocolo comprometió | Lo que hay |
|---|---|---|
| Territorio | Guanajuato + 3 vecinas (**cuatro entidades**) | **30 entidades de todo el país**, y **sin Colima ni Nayarit**, que no existen en la fuente |
| Ventana | 2024 – 2026 | **enero 2025 – julio 2026** |
| Volumen | 2 a 4 millones | **21,357,873** |

**Lo que este informe recomendaba:** ampliar el alcance a cobertura nacional,
con el argumento de que acotar significaría descartar datos que ya tenemos, ya
están perfilados y no cuestan más de procesar —DuckDB agrega los 21 millones en
segundos.

**Lo que el equipo decidió · ADR 001:** partir el recorte en dos niveles.

| | Territorio | Dónde vive |
|---|---|---|
| **Laboratorio** | nacional, 30 entidades, 21.4 millones | base local en la máquina de A |
| **Producto desplegado** | **siete entidades de centro-occidente** | página web y aplicación móvil |

Las siete: **Aguascalientes, Guanajuato, Jalisco, Michoacán, Querétaro, San Luis
Potosí y Zacatecas.** Colima y Nayarit quedan fuera del alcance declarado porque
no existen en la fuente. El despliegue arranca **sólo con Guanajuato** y crece
conforme se verifique el funcionamiento.

**Ventana:** 2025 y 2026.

**Por qué la decisión es mejor que la recomendación del informe.** El informe
midió el costo de *procesar* —que es casi cero— y no miró el costo de
*desplegar*, que no lo es: 21.4 millones de filas en el producto obligan a una
infraestructura que no cabe en catorce semanas, y al usuario no le sirve ver
precios de entidades donde no vive. La decisión se queda con el alcance nacional
donde sale gratis y lo acota donde cuesta.

**Y evita una contradicción que la recomendación del informe sí tenía:** el
protocolo declara expresamente que el proyecto *«no pretende cobertura
nacional»*. Ampliar el producto a las 30 entidades habría chocado de frente con
esa frase. Como laboratorio no choca: lo nacional es material de trabajo, no
alcance comprometido.

> **Pero la decisión tampoco sale gratis en el protocolo.** Se pasa de **cuatro
> entidades a siete**, y eso es una ampliación que hay que justificar por
> escrito, no sólo anotar. La justificación está en el ADR 001.

> **Medido:** el filtro de años no quita ni una fila. Todo lo descargado ya está
> dentro de 2025–2026. **La reducción de volumen viene entera del territorio.**
>
> **Falta medir:** cuántas filas tiene el recorte de siete entidades. De ahí
> sale si el compromiso de «dos a cuatro millones» se sostiene o hay que
> corregirlo. Lo mide `docs/datos/perfilado/medir-decisiones.py`.

**Esto obliga a corregir el protocolo antes del 18 de septiembre**, y va anotado
con nombre y fecha en las consecuencias del ADR 001.

### 3 · ¿H3 al 85% de cobertura es realista?

H3 mide, sobre 200 pares, si el sistema reconoce que dos nombres escritos en
cadenas distintas son el mismo producto. Cobertura ≥85%, precisión ≥90%.

- [ ] **Se sostiene el 85%**
- [ ] **Se ajusta a ___%**
- [x] **Queda abierta.** No se alcanzó a tratar el 11 de septiembre. → **ADR 004**

**En el eje que H3 nombra —la escritura— la meta está holgada:** 1.29 variantes,
cero agrupamientos incorrectos en la revisión manual, y toda la variación es
mecánica.

**El problema es que H3 supone un problema que esta fuente puede no tener.** La
ficha de T005 lo plantea así: *«cuatro cadenas, cuatro escrituras, un
producto»*. Pero PROFECO **no deja que cada tienda escriba el nombre**: captura
con su propio catálogo. Por eso hay sólo **896 nombres de producto para 247
cadenas**. Si las cadenas no escriben distinto, los 200 pares que H3 pide pueden
no existir.

> **Lo mide `docs/datos/perfilado/h3-entre-cadenas.py`**, que cuenta cuántos
> productos presentes en dos o más cadenas se escriben distinto y cuántos pares
> se pueden formar. **Hay que correrlo sobre los datos reales antes del 18.**

**Lo que sí es un problema medido, y grande, es otro:** la variación de
presentaciones dentro de un mismo producto (57 en `Carne Res`). Reconciliar
*eso* sí es difícil y sí es investigación. **La propuesta para el ADR 004 es
reenunciar H3 sobre ese eje.**

Ajustar o reenunciar una hipótesis **en septiembre, con datos**, es método.
Hacerlo en noviembre porque no salió es otra cosa.

---

## Qué más se decidió el 11 de septiembre

Dos preguntas que este informe dejó abiertas se resolvieron en la reunión y
viven en el **ADR 002**:

| Pregunta | Decisión |
|---|---|
| **¿Qué cuenta como «el mismo artículo»?** | `producto` + `presentacion`. `marca` se guarda y se muestra, pero no identifica: sirve para ordenar y filtrar los resultados. |
| **¿Qué es `S/m`?** | Una categoría propia: producto genérico. Ni nulo ni marca. Se normaliza a un solo literal y va al final en los listados. |

Y una tercera, en el **ADR 001**:

| Pregunta | Decisión |
|---|---|
| **¿Qué hace el contrato con las columnas que aparecen y desaparecen?** | `folio`, `cv_producto` y `cv_marca` **no se ingieren, y se descartan sin señalamiento**, tal como se acordó. *El ADR 001 propone enmendar sólo la segunda mitad —no ingerirlas pero dejar aviso— por su tensión con la observabilidad, que es el objeto de investigación. Se ratifica o se enmienda el 16 de septiembre.* |

---

## Lo que este informe deja pendiente para la versión 1

La versión 1 se cierra el **17 y 18 de septiembre** (semana 3, tarea de A) y
tiene que llegar con esto resuelto:

1. **El volumen del recorte de siete entidades.** Corre
   `docs/datos/perfilado/medir-decisiones.py`. Es el número que corrige el
   protocolo. · *lunes 14 a primera hora, porque el contrato de datos se escribe
   con él.*
2. **El recorte de productos, que no se decidió.** El protocolo compromete
   *«recorte de productos a la canasta básica, conforme a la clasificación de
   productos de consumo generalizado de la fuente»*, y esa clasificación es la
   columna `catalogo`, con 16 valores. Hoy el corpus trae celulares, lavadoras y
   pantallas de televisión junto al kilo de tortilla. El mismo guión imprime los
   16 con su volumen y su precio mediano. · *se decide en la reunión del
   miércoles 16 · queda como ADR 005.*
3. **Una cifra mal puesta en `perfilado.md` §3.** La tabla «unidad de
   emparejamiento» trae «~6,000» artículos para `producto` + `presentacion` y
   «5,750» para el trío con `marca`. **No puede ser:** agregar una columna a una
   clave nunca reduce el número de claves distintas. El ~6,000 era una
   estimación a ojo y la tilde no alcanzó a avisarlo. El mismo guión mide los
   tres niveles con la misma normalización. · *lunes 14.*
4. **Los pares de H3.** Corre `h3-entre-cadenas.py` sobre los datos reales. El
   número decide el ADR 004. · *antes del 18.*
5. **Si PROFECO publica 2024.** Ya **no bloquea** —el equipo decidió trabajar
   2025–2026 de todos modos—, pero cambia cómo se redacta la corrección al
   protocolo: no es lo mismo *«se acotó la ventana»* que *«la fuente no publica
   más atrás»*. Una consulta al portal. · *antes del 18.*

> **Y una corrección al protocolo que sale del ADR 002 y conviene no olvidar:**
> el objetivo específico de reconciliación compromete *«vocabulario canónico,
> diccionario de equivalencias **y comparación difusa**»*. La comparación difusa
> se descarta porque toda la variación medida es mecánica. Eso hay que
> declararlo, no dejarlo pasar en silencio.
