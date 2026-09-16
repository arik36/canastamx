# Perfilado de la fuente QQP

<!-- Llenan T003, T004 y T005 (A) · lunes 7, martes 8 y miércoles 9.
     Regla: números, no adjetivos. "Hay bastantes nulos" no sirve;
     "88 nulos, 0.02%" sí. -->

**Archivos perfilados:** QQP_2025 + QQP_2026 (38 archivos, ene 2025 – jul 2026) ·
**Filas totales:** 21,357,873 · **Última medición:** 11/SEP/2026

---

## 0 · Objetivo del perfilado de datos

El perfilado de datos consiste en inspeccionar una fuente para saber:

- qué estructura tiene (estructurada, semiestructurada o no estructurada),
- qué tipos de datos contiene,
- cuántos valores nulos existen,
- qué tan variados son los valores,
- qué valores parecen imposibles,
- cuáles son posibles anomalías,
- qué registros parecen duplicados,
- y qué características pueden convertirse después en reglas de calidad de datos.

**Guiones que produjeron este documento**, todos en `docs/datos/perfilado/`:
`perfilado_nivel1.py` (sección 1) · `perfilado_nivel2.py` (sección 2) ·
`perfilado_nivel3.py` (sección 3) · `mojibake.py` y `centinelas.py` (hallazgos
que atraviesan las tres) · `revisar-candidatos.py`. El recorrido completo,
explicado bloque por bloque, está en `recapitulado-perfilado.md`.

---

## 1 · Estructura <!-- T003, lunes 7 -->

**Volumen:** 21,357,873 filas. **El número de columnas no es uno solo:**
36 archivos traen 15 columnas y 2 traen 18. Ver «Deriva de esquema» abajo.

**Rango de fechas:** 2025/01/02 a 2026/07/31 · fechas ilegibles: 0
**Entidades federativas:** 37 literales distintos que son **30 entidades reales**.
**Faltan Colima y Nayarit por completo** — 30 de 32, el 93.8% del territorio.

| Columna | Tipo declarado | % ausente | % vacío | Valores distintos | Ejemplo |
|---|---|---:|---:|---:|---|
| producto | Carácter (65) | 0% | 0% | 896 | Acelga |
| presentacion | Carácter (180) | 0% | 0% | 5,961 | Manojo |
| marca | Carácter (65) | 0% | 0% | 1,439 | S/m |
| categoria | Carácter (65) | 0% | 0% | 59 | Hortalizas Frescas |
| catalogo | Carácter (65) | 0% | 0% | 16 | Frutas y Legumbres |
| precio | Número (18,2) | 0% | 0% | 71,332 | 19.0 |
| fecha_registro | Datetime (8) | 0% | 0% | 434 | 2025/01/02 |
| cadena_comercial | Carácter (65) | 0% | 0% | 247 | Central de Abastos |
| giro | Carácter (65) | 0% | 0% | 21 | Central de Abasto |
| nombre_comercial | Carácter (120) | 0% | 0% | 2,961 | Central de Abasto |
| direccion | Carácter (255) | 0% | 0% | 3,641 | Av. Mahatma Gandhi S/n… |
| estado | Carácter (120) | 0% | 0% | 37 (30 reales) | Aguascalientes |
| municipio | Carácter (120) | 0% | 0% | 93 | Aguascalientes |
| latitud | Número (18,6) | 0% | 0.0086% | 2,111 | 21.832072 |
| longitud | Número (18,6) | 0% | 0.0086% | 2,113 | -102.292976 |
| **folio** | *(no está en el diccionario)* | **94.12%** | 0% | 1,853 | 20160 |
| **cv_producto** | *(no está en el diccionario)* | **94.12%** | 0% | 812 | 869 |
| **cv_marca** | *(no está en el diccionario)* | **94.12%** | 0% | 486 | 5 |

**«Ausente» y «vacío» no son lo mismo, y por eso van en columnas separadas.**
«Ausente» quiere decir que el archivo **no trae esa columna**: es una estructura
distinta, no un descuido del capturista. «Vacío» quiere decir que la columna
existe y la celda está en blanco. El contrato de datos tiene que reaccionar
distinto a cada caso.

**El 94.12% de `folio` está medido, no estimado.** Son 20,102,835 filas de
21,357,873 que pertenecen a archivos sin esa columna; sólo 1,255,038 filas
(las dos quincenas de junio de 2026) la traen.

> Versiones anteriores de este documento anotaron 94.7% y 94.12% para el mismo
> dato. La cifra correcta, medida con `count(folio)` sobre los 38 parquet, es
> **94.12%**.

### Marcadores textuales

Ninguna columna tiene celdas vacías salvo `latitud`/`longitud`. Pero eso no
significa que el dato esté completo: **`marca` trae `S/m` o `S/M` en 7,350,628
filas, el 34.4% del corpus.** Son registros que declaran «sin marca». No son
nulos y no son marcas: son una tercera cosa, y el contrato tiene que decidir
explícitamente qué hacer con ellos (ver sección 3, decisiones para la reunión).

### Deriva de esquema

| | archivos | columnas |
|---|---:|---|
| 2025 completo, y 2026 salvo junio | 36 | 15 |
| `06-2026_Q1`, `06-2026_Q2` | 2 | 18 (`+folio`, `+cv_producto`, `+cv_marca`) |

Las tres columnas extra **no aparecen en el diccionario oficial** de PROFECO
(`datos.profeco.gob.mx/diccionarioDatosQQP.php`, que describe 15). No es un
cambio permanente: **julio de 2026 vuelve a 15 columnas.**

### Discrepancias entre lo declarado y lo real

- **`fecha_registro`** está declarada `Datetime (8)` pero llega como texto en
  **dos formatos distintos según el archivo**: `YYYY/MM/DD` en 36 archivos y
  `DD/MM/YYYY` en las dos quincenas de mayo de 2026. Leer todo con un solo
  formato intercambiaría día y mes en 1,007,082 filas.
- **Codificación mixta.** 36 archivos son UTF-8 con BOM; `05-2026_Q1.csv` y
  `05-2026_Q2.csv` son ISO-8859-1 sin BOM. Comprobado a nivel de bytes el
  10/09/2026: esos dos archivos **no contienen bytes 0x80–0x9F**, que es lo que
  tendrían si fueran página de códigos de DOS. `latin-1` es la lectura correcta.
- **Nombres de columna.** El diccionario los declara en mayúsculas y pegados
  (`FECHAREGISTRO`, `CADENACOMERCIAL`, `NOMBRECOMERCIAL`); el archivo los trae
  en minúsculas con guión bajo. El contrato debe usar los literales del CSV.
- **`estado`** trae 37 literales por acentos inconsistentes: `Michoacan` y
  `Michoacán` conviven. Siete pares de ésos son la misma entidad. En 2026 la
  fuente empezó a acentuar `estado` y `catalogo`, y en cambio perdió acentos en
  `giro` y `categoria`, convertidos en `?`.
- **`folio`** parece una llave de registro, pero **no está documentada** y no se
  puede asumir única. Duda abierta para C2 (T013, punto 8).

### Corrupción de codificación (`?`)

Afecta **770,273 filas, el 3.61% del corpus**, repartidas en **36 de los 38
archivos**. No es un fenómeno, son dos con el mismo síntoma:

| | filas con `?` | qué es |
|---|---:|---|
| 2025, 24 archivos | 3,181 (0.024% de 2025) | ruido crónico, unos cientos por quincena |
| 2026 ene–abr, 8 archivos | 76 | prácticamente nada |
| 2026 mayo, 2 archivos | 13,962 | empieza a crecer |
| **2026 junio, 2 archivos** | **753,054** | **el 97.76% del problema** |
| **2026 julio, 2 archivos** | **0** | **limpio** |

Toca 8 de las 11 columnas de texto. **No toca `catalogo`, `estado` ni
`cadena_comercial`, y no toca `precio` ni `fecha_registro`.**

| columna | filas con `?` | valores distintos |
|---|---:|---:|
| municipio | 401,781 | 21 |
| presentacion | 236,062 | 636 |
| producto | 163,837 | 75 |
| direccion | 147,379 | 289 |
| marca | 66,526 | 99 |
| nombre_comercial | 61,577 | 612 |
| giro | 46,336 | 5 |
| categoria | 496 | 1 |

**No es irrecuperable.** Cuando el `?` sustituyó exactamente un carácter, el
valor correcto casi siempre sigue en la misma columna (`Art?culos` junto a
`Artículos`). Buscando para cada valor roto un gemelo de idéntica longitud que
coincida en todo salvo donde está el `?`:

| clase | valores distintos | apariciones | % de lo corrupto |
|---|---:|---:|---:|
| **reparable** (un gemelo único) | 1,650 | 1,088,196 | **96.82%** |
| ambiguo (más de un gemelo) | 63 | 31,703 | 2.82% |
| sin gemelo | 25 | 4,095 | 0.36% |

Los 25 «sin gemelo», revisados uno a uno, son en su mayoría **signos de
interrogación legítimos** (`Adivina Quién?`, `néctar de Miel?`) o cadenas únicas
de especificaciones de teléfono, no daño nuevo.

**Ambos hallazgos —las tres columnas extra y el `?`— coinciden en junio de 2026,
pero son independientes:** el `?` existe desde enero de 2025 en pequeña escala,
mucho antes de que aparecieran `folio`, `cv_producto` y `cv_marca`.

---

## 2 · Rangos y anomalías <!-- T004, martes 8 -->

**Precios en cero: 0 (0.0000%) · negativos: 0 · nulos: 0 (0.0000%)**

**Duplicados exactos** (coinciden en todo salvo `folio`/`cv_producto`/`cv_marca`):
**301 filas (0.0014%)**. Medido además por origen: **los 301 están dentro de un
mismo archivo; cero entre archivos distintos.** Eso importa para el contrato: es
captura duplicada en la fuente, no solape entre quincenas, así que se resuelve
al validar y no al ingerir.

**Clave de unicidad candidata — NO aguanta.** Se propuso
(`producto`, `nombre_comercial`, `direccion`, `fecha_registro`) y se midió:

| | valor |
|---|---:|
| combinaciones distintas | 9,062,477 |
| combinaciones que se repiten | 3,675,363 |
| filas de más | 12,295,396 |
| peor caso (una sola combinación) | 95 filas |

Más de la mitad del corpus viola esa clave. Tiene sentido: **el mismo
establecimiento cotiza el mismo producto en varias presentaciones y marcas el
mismo día.** La clave necesita al menos `presentacion` y `marca`. Queda como
regla pendiente de definir en el contrato de la semana 2.

**Cardinalidades:** cadenas comerciales **247** · municipios **93** ·
entidades **37 literales → 30 reales** · establecimientos distintos
(`nombre_comercial` + `direccion`, proxy — confirmar con C2) **4,334**.

### Distribución de precio por categoría

45 categorías, después de reparar el `?` con el diccionario medido y normalizar
acentos. (Los 59 literales del diccionario de C2 colapsan a 45 categorías reales.)

<!-- `productos de temporada (navidenos)` pierde la ñ porque strip_accents la
     convierte en n. Es la clave de agrupación, no el nombre a mostrar. -->

| Categoría (normalizada) | mín | p25 | mediana | p75 | p95 | p99 | máx |
|---|---:|---:|---:|---:|---:|---:|---:|
| accesorios domesticos | 19.00 | 125.00 | 173.00 | 189.00 | 200.00 | 218.00 | 230.00 |
| aceites y grasas veg. comestibles | 2.00 | 31.00 | 39.00 | 52.00 | 84.50 | 130.00 | 151.00 |
| alimentos cocinados f/casa | 69.00 | 125.00 | 135.00 | 139.00 | 159.00 | 178.00 | 179.00 |
| aparatos electricos | 181.30 | 999.00 | 2799.00 | 10199.00 | 16999.00 | 25599.36 | 99999.00 |
| aparatos electronicos | 439.00 | 3199.00 | 5999.00 | 9499.00 | 17499.00 | 27599.00 | 107691.00 |
| arroz y cereales preparados | 5.00 | 22.00 | 43.00 | 74.00 | 96.00 | 113.00 | 132.00 |
| articulos deportivos | 599.00 | 1999.00 | 1999.00 | 2999.00 | 2999.00 | 3999.00 | 4000.00 |
| arts. de esparcimiento (juguetes) | 84.01 | 449.00 | 799.00 | 6990.00 | 12990.00 | 14899.00 | 20699.00 |
| arts. de papel p/higiene personal | 6.50 | 32.90 | 45.90 | 100.00 | 339.00 | 435.00 | 545.99 |
| arts. para el cuidado personal | 3.50 | 41.00 | 75.00 | 115.00 | 687.00 | 1239.00 | 1999.00 |
| azucar | 17.00 | 25.90 | 30.00 | 53.90 | 186.50 | 271.90 | 319.00 |
| botanas y bebidas | 5.00 | 30.00 | 44.90 | 59.90 | 76.00 | 110.00 | 118.00 |
| cafe | 6.60 | 90.50 | 115.00 | 149.00 | 176.00 | 263.00 | 295.00 |
| carne de ave | 16.61 | 39.90 | 64.90 | 104.90 | 174.00 | 198.00 | 232.00 |
| carne y visceras de cerdo | 13.01 | 80.00 | 116.00 | 135.00 | 149.99 | 160.00 | 180.00 |
| carne y visceras de res | 25.00 | 138.00 | 199.00 | 239.00 | 269.99 | 544.00 | 759.90 |
| carnes frias secas y embutidos | 14.00 | 62.90 | 128.50 | 211.90 | 352.90 | 438.00 | 785.00 |
| cerveza | 20.50 | 90.00 | 137.00 | 191.00 | 244.00 | 264.00 | 353.00 |
| chocolates y golosinas | 2.70 | 16.50 | 48.00 | 61.00 | 116.00 | 161.00 | 415.00 |
| cigarrillos | 15.00 | 25.00 | 27.00 | 27.90 | 28.90 | 29.50 | 30.50 |
| condimentos | 4.00 | 21.90 | 33.00 | 51.00 | 101.00 | 280.00 | 629.99 |
| derivados de leche | 3.50 | 25.00 | 50.00 | 96.90 | 260.00 | 328.00 | 428.00 |
| detergentes y productos similares | 6.50 | 27.50 | 41.00 | 80.00 | 164.00 | 209.90 | 265.00 |
| enseres menores | 7.00 | 23.00 | 30.00 | 115.00 | 659.50 | 999.00 | 999.00 |
| frutas frescas | 5.75 | 30.00 | 39.99 | 57.90 | 99.00 | 129.00 | 298.00 |
| frutas y legumbres procesadas | 5.50 | 16.90 | 28.00 | 42.00 | 72.00 | 80.00 | 98.90 |
| galletas | 32.90 | 52.00 | 55.00 | 63.60 | 64.90 | 66.90 | 71.90 |
| galletas pastas y harinas de trigo | 2.50 | 12.00 | 20.00 | 38.00 | 68.00 | 90.90 | 168.00 |
| grasas animales comestibles | 32.00 | 46.90 | 56.95 | 78.00 | 84.90 | 97.90 | 129.00 |
| hortalizas frescas | 3.00 | 16.50 | 26.90 | 43.99 | 108.50 | 174.00 | 340.00 |
| huevo | 18.50 | 42.50 | 49.90 | 60.00 | 91.90 | 98.00 | 114.00 |
| leche fresca | 20.99 | 28.50 | 30.00 | 32.00 | 36.90 | 84.50 | 94.50 |
| leche procesada | 7.00 | 26.25 | 34.00 | 39.90 | 210.00 | 288.00 | 320.00 |
| legumbres secas | 2.00 | 30.00 | 40.00 | 57.00 | 100.00 | 240.00 | 650.00 |
| material escolar | 1.15 | 30.00 | 58.90 | 108.00 | 250.00 | 426.00 | 1999.50 |
| medicamentos | 5.00 | 68.90 | 259.00 | 769.00 | 1807.00 | 2731.00 | 5924.86 |
| pan | 1.20 | 20.50 | 32.00 | 50.00 | 62.00 | 93.00 | 585.00 |
| pescados y mariscos | 10.30 | 96.00 | 139.00 | 260.00 | 428.90 | 650.00 | 2100.00 |
| pescados y mariscos en conserva | 8.00 | 17.90 | 20.50 | 35.00 | 48.00 | 279.90 | 674.00 |
| productos de temporada (navidenos) | 6.90 | 36.50 | 72.50 | 180.00 | 299.00 | 460.00 | 978.00 |
| refrescos envasados | 5.50 | 19.00 | 24.00 | 33.00 | 51.50 | 82.00 | 144.00 |
| te | 13.50 | 20.50 | 23.00 | 25.00 | 27.00 | 28.00 | 33.00 |
| tortillas y derivados del maiz | 5.00 | 15.50 | 24.00 | 39.50 | 57.00 | 64.50 | 85.00 |
| utensilios domesticos | 21.00 | 40.90 | 1329.00 | 1699.00 | 1999.00 | 3599.00 | 3999.00 |
| vinos y licores | 74.00 | 249.00 | 329.00 | 439.00 | 525.00 | 592.00 | 1089.00 |

### La regla del «10x el p99» y por qué no sirvió

La primera regla automática que se probó fue: *sospechoso si el precio supera
10 veces el p99 de su categoría*. Devolvió **0**, y hay que decir con precisión
por qué, porque el motivo es más interesante que el resultado.

**No es que no hubiera precios raros: es que la regla no podía disparar nunca.**
En una distribución de precios el p99 ya está pegado al máximo. Medido sobre
estas mismas 45 categorías, la razón máx/p99 más alta de todo el corpus es
**6.29x (pan)**. La regla pedía más de 10x. **Cero de 45 categorías podían
dispararla**, aunque los datos hubieran estado perfectos.

| categoría | p99 | máx | razón |
|---|---:|---:|---:|
| pan | 93.00 | 585.00 | **6.29x** ← la más alta del corpus |
| material escolar | 426.00 | 1,999.50 | 4.69x |
| aparatos electricos | 25,599.36 | 99,999.00 | 3.91x |
| aparatos electronicos | 27,599.00 | 107,691.00 | 3.90x |
| pescados y mariscos | 650.00 | 2,100.00 | 3.23x |

Y hay un segundo problema, de fondo: **`categoria` es una unidad demasiado
gruesa.** Dentro de «material escolar» conviven un lápiz de $1.15 y un juego de
tenis de $1,999.50 — un rango de **1,738x en un solo grupo**:

| producto (dentro de material escolar) | n | mediana | mín | máx |
|---|---:|---:|---:|---:|
| tenis | 2,185 | 489.00 | 118.00 | 1,999.50 |
| calculadoras | 12,531 | 335.00 | 26.40 | 860.00 |
| sueter escuela oficial | 1,643 | 260.00 | 105.00 | 759.00 |
| bata escuela oficial | 4,132 | 199.90 | 98.90 | 529.00 |

Un p99 calculado sobre esa mezcla no describe a ningún producto. **La unidad
correcta es `producto`** (896 valores), no `categoria` (45).

### Precios redondos: punto de precio contra centinela

Un **valor centinela** es un dato ficticio pero válido en formato (999, 9999)
que un capturista usa como comodín para decir «no había precio».

**Pero no todo número redondo repetido es un centinela, y confundirlos costaría
tirar precios buenos.** El comercio mexicano pone precios redondos a propósito:
el yoghurt a $9.00 exacto aparece 7,562 veces porque **ése es su precio**, no
porque nadie supiera cuánto costaba. Una primera versión de la detección marcó
157,412 filas como «centinelas confirmados» y la mayoría eran precios reales de
$9 y $99.

Lo que separa a los dos no es cuánto se repiten, sino **dónde caen dentro del
rango de su propio producto**:

- un **punto de precio** está en medio del rango normal (el yoghurt a $9 con
  mediana $20 está por debajo de la mediana, es simplemente barato);
- un **centinela** está en el extremo, porque su función es ser reconociblemente
  imposible para ese producto.

`centinelas.py` mide las dos cosas y las separa con dos criterios: la
**posición** del precio frente a las demás cotizaciones del mismo producto, y la
**razón contra su mediana**.

Medido sobre los 21,357,873 registros:

| | pares (producto, precio) | filas | % del corpus |
|---|---:|---:|---:|
| precios redondos con ≥30 repeticiones | 250 | — | — |
| de ésos, con salto ≥20x sobre sus vecinos | 168 | 157,412 | 0.7370% |
| **· punto de precio** (dentro del rango normal) | **160** | **153,166** | **0.7171%** |
| **· posible centinela** (en el extremo) | **8** | **4,246** | **0.0199%** |

**El 97% de lo que la primera versión llamaba «centinela» son precios reales.**
Los diez más grandes de esa clase, para que se vea por qué:

| producto | precio | veces | posición | mediana | razón |
|---|---:|---:|---:|---:|---:|
| yoghurt | 9.00 | 7,562 | 0.129 | 20.00 | 0.45x |
| shampoo | 99.00 | 5,387 | 0.606 | 92.00 | 1.08x |
| lavadoras | 9,999.00 | 5,378 | 0.397 | 10,499.00 | 0.95x |
| leche en polvo | 99.00 | 5,272 | 0.540 | 98.90 | 1.00x |
| papel higienico | 9.00 | 4,735 | 0.043 | 41.90 | 0.22x |
| pantallas | 9,999.00 | 4,051 | 0.584 | 9,490.00 | 1.05x |
| leche ultrapasteurizada | 9.00 | 3,498 | 0.004 | 34.00 | 0.27x |

«Posición» es qué fracción de las demás cotizaciones de ese producto es más
barata. **La lavadora a $9,999 está por debajo de su propia mediana ($10,499) y
es más cara que sólo el 40% de las lavadoras.** No es un comodín: es el precio
redondo clásico del electrodoméstico mexicano. El yoghurt a $9 es más caro que
apenas el 13% de los yoghurts.

### Los 8 candidatos, y la revisión que falta

| producto | precio | veces | posición | mediana | razón |
|---|---:|---:|---:|---:|---:|
| yoghurt | 99.00 | 1,191 | 0.962 | 20.00 | 4.95x |
| celulares | 9,999.00 | 996 | 0.998 | 4,299.00 | 2.33x |
| huevo | 99.00 | 897 | 0.997 | 49.90 | 1.98x |
| termometro | 999.00 | 604 | 0.959 | 96.00 | **10.41x** |
| ibuprofeno | 99.00 | 217 | 0.993 | 50.00 | 1.98x |
| tostadores de pan | 999.00 | 159 | 0.991 | 628.00 | 1.59x |
| barra de sonido | 9,999.00 | 105 | 0.997 | 3,499.00 | 2.86x |
| tabcin 500 | 99.00 | 77 | 0.998 | 61.00 | 1.62x |

**Ninguno está confirmado todavía, y hay una razón concreta para dudar de casi
todos.** Seis de los ocho tienen una razón contra su mediana de entre 1.6x y
2.9x — eso no es «imposible», es «la presentación grande». Un celular a $9,999
es un celular de gama media; un tostador a $999 es un tostador.

**La comprobación que lo decide es bajar de `producto` a `presentacion`**, y es
el mismo problema que rompió la regla del p99 una planta más abajo: `producto` es
una etiqueta gruesa. «yoghurt» cubre un vasito de 150 g y un bote de un kilo;
«termometro» cubre uno de mercurio de $30 y uno infrarrojo de $1,300 —lo confirma
D3, donde `termometro` va de $10 a $1,354—. Si el precio alto corresponde
siempre a la presentación grande, **no es un comodín: es otro producto con la
misma etiqueta.**

`revisar-candidatos.py` hace exactamente esa comparación: para cada candidato
mira qué presentaciones aparecen a ese precio y cuánto cuestan esas mismas
presentaciones en el resto de sus filas.

### Veredicto: QQP no usa valores centinela

Corrido `revisar-candidatos.py`, los ocho se explican. Cuatro quedan
descartados de inmediato porque el precio es **normal para su presentación**:

| producto | precio | razón vs producto | razón vs **su presentación** | qué era |
|---|---:|---:|---:|---|
| yoghurt | 99.00 | 4.95x | **1.09x** | 9 presentaciones grandes, medianas ~$90 |
| celulares | 9,999.00 | 2.33x | **1.33x** | 14 modelos de gama media, mediana $7,499 |
| huevo | 99.00 | 1.98x | **1.09x** | la presentación de mayor tamaño, mediana $91 |
| **termometro** | 999.00 | **10.41x** | **1.00x** | el modelo que cuesta $996 |

**El caso del termómetro es el que cierra la discusión.** Era el candidato más
fuerte —10.4 veces la mediana de su producto— y al bajar a la presentación
resulta que ese $999 corresponde a un modelo cuya mediana es **$996**. No había
comodín: había un termómetro caro y un termómetro barato compartiendo la etiqueta
`termometro`. Exactamente el mismo error que rompió la regla del p99, una planta
más abajo.

Los otros cuatro pasaron el umbral automático (1.5x) por poco, y revisados uno
por uno también se explican:

| producto | precio | presentación dominante | su mediana | razón |
|---|---:|---|---:|---:|
| ibuprofeno | 99.00 | Frasco 120 Ml. Suspensión | 51.00 | 1.94x |
| tostadores de pan | 999.00 | Tt1a18mx | 549.00 | 1.82x |
| barra de sonido | 9,999.00 | Ht-s20r | 4,799.00 | 2.08x |
| tabcin 500 | 99.00 | Caja 12 Tabletas Efervescente | 61.00 | 1.62x |

**Entre 1.6 y 2.1 veces no es un comodín: es dispersión de precio entre
establecimientos**, que es precisamente el fenómeno que este proyecto existe para
medir. Un Tabcin a $99 en una farmacia cuando la mediana es $61 es una farmacia
cara, no un dato inventado. Para contraste, en la prueba controlada un centinela
real da **8.5x contra su propia presentación**; ninguno de estos se acerca.

> **Conclusión para el informe.** No se encontró evidencia de valores centinela
> en `precio`. Los 168 precios redondos anormalmente repetidos se explican como
> **puntos de precio del comercio** (160) y **presentaciones caras dentro de una
> etiqueta de producto gruesa** (8). Las tablas de «validación de centinelas» de
> versiones anteriores de este documento —lavadoras a $9,999 repetidas 4,515
> veces— describían precios reales, no comodines.
>
> **Esto no debilita el proyecto: lo afina.** Significa que la compuerta de
> calidad no necesita una regla de centinelas para `precio`, y que el esfuerzo va
> a donde sí hay daño medido: la corrupción de codificación (3.61% del corpus) y
> la deriva de esquema de junio de 2026.

**Y deja un hallazgo estructural que sí importa:** `producto` es una etiqueta
demasiado gruesa para juzgar precios, igual que lo era `categoria`. Cualquier
regla de calidad sobre `precio` tiene que evaluarse sobre
`producto` + `presentacion`, nunca sobre `producto` solo. Eso se conecta
directamente con la decisión de la sección 3.

<!-- Un detalle que salió en la revisión y vale anotarlo: en `ibuprofeno` la
     misma presentación aparece dos veces, como «Suspensión» y «Suspensi?n».
     Es el mojibake partiendo una presentación en dos, visto en vivo. -->

**Nota sobre el umbral.** `revisar-candidatos.py` descarta automáticamente con
razón menor a 1.5x, a propósito holgado: la idea es descartar con confianza, no
acusar. Los cuatro que quedaron arriba de 1.5x pasaron a revisión humana y la
revisión los descartó. El umbral funcionó como debía — filtrar, no decidir.

### Atípicos por dispersión robusta

Aparte de los números redondos se midió qué tan lejos está cada precio del centro
de **su propio producto**, con mediana y MAD sobre el logaritmo del precio
(logaritmo porque los precios son multiplicativos; mediana y MAD porque ni la
media ni la desviación estándar sobreviven a los propios atípicos).

**568,362 filas marcadas (2.6611%)** en 595 productos. Pero una parte importante
son productos con rango ancho de verdad, no errores:

| producto | filas atípicas | precio mín | precio máx |
|---|---:|---:|---:|
| leche ultrapasteurizada | 42,294 | 7.00 | 21.90 |
| papas fritas y similares | 39,883 | 15.90 | 119.00 |
| azucar | 20,170 | 51.50 | 121.00 |
| termometro | 13,266 | 10.00 | 1,354.00 |
| atun | 12,045 | 8.00 | 420.00 |

**Esta cifra no se puede cerrar hasta que la reunión decida qué es «el mismo
artículo»** (sección 3). Si la unidad pasa a ser `producto` + `presentacion`, la
mayoría de estos 568 mil dejan de ser atípicos: son presentaciones distintas
midiéndose juntas.

**28 productos tienen MAD = 0** — más de la mitad de sus filas comparten el mismo
precio exacto (`semilla de girasol` $50, `playera oficial` $1,999, `jurel` $69.90).
El detector no los evalúa, porque no se puede dividir entre cero, y por eso se
reportan aparte en vez de desaparecer en silencio.

### Reglas de contrato que se derivan de la sección 2

<!-- Cada anomalía medida se convierte en una regla del contrato de la semana 2. -->

1. **`precio > 0`.** Cero violaciones hoy. Se escribe igual: el contrato
   describe lo que se acepta, no lo que pasó.
2. **NO se escribe regla de centinelas para `precio`.** Se buscaron y no hay:
   los 168 precios redondos anormalmente repetidos son puntos de precio del
   comercio (160) o presentaciones caras dentro de una etiqueta gruesa (8).
   Un `precio NOT IN (999, 9999)` habría tirado 157,412 filas buenas.
   **La ausencia de la regla es el resultado, y está medida.**
3. **Cualquier regla sobre `precio` se evalúa sobre `producto` + `presentacion`,
   nunca sobre `producto` solo.** Medido: el termómetro a $999 parece 10.4x
   anómalo contra su producto y 1.00x contra su presentación.
4. **Duplicados exactos:** rechazar, con motivo `duplicado_exacto`. Son 301 y
   todos dentro de un mismo archivo.
5. **Clave de unicidad:** pendiente. La candidata de cuatro campos no aguanta
   (12.3 millones de filas de más); hay que probar la de seis con `presentacion`
   y `marca`.
6. **Deriva de esquema:** aceptar las 15 columnas obligatorias y **avisar** de
   las extra sin romperse ni descartarlas en silencio.
7. **Codificación por archivo, no por corpus**, más una compuerta que detecte
   caracteres de control C1 — que es la corrupción que no deja rastro visible.

---

## 3 · Variantes de escritura <!-- T005, miércoles 9 · decide H3 -->

**Qué se midió.** Una «variante de escritura» son dos textos distintos que se
refieren a lo mismo. Se detecta normalizando —minúsculas, sin acentos, sin
puntuación, espacios colapsados— y contando cuántos literales crudos caen en la
misma clave. Se midió sobre el trío `producto` + `presentacion` + `marca`, que
es lo que identifica un artículo concreto en un anaquel.

**Las cifras van sobre las 20,934,197 filas sin `?`** (el 98.0% del corpus). Se
excluyen las 423,676 filas con corrupción de codificación porque el `?` no se
normaliza a la letra que se comió: `Art?culos` y `Artículos` quedarían como dos
artículos distintos. Contaminaban **1,215 de 6,962 claves (17.5%)** — artículos
fantasma, no variantes de escritura.

| | por `producto` | por `presentacion` | por `marca` | **por artículo (el trío)** |
|---|---:|---:|---:|---:|
| literales crudos | 821 | 5,320 | 1,340 | **7,389** |
| claves tras normalizar | 816 | 4,771 | 1,286 | **5,750** |
| variantes por clave, media | 1.01 | 1.12 | 1.04 | **1.29** |
| variantes por clave, mediana | 1 | 1 | 1 | **1** |
| variantes por clave, máximo | 2 | 4 | 4 | **4** |

**Variantes promedio por artículo: 1.29 · mediana: 1 · máximo: 4**
**Artículos con más de 10 variantes: 0 de 5,750 (0.0%)**
**Artículos con más de 1 variante: 1,551 de 5,750 (27.0%)**

La normalización sólo colapsa 1,639 literales de 7,389 — el 22.2%. Dicho de otro
modo: **tres de cada cuatro artículos ya venían escritos de una sola manera en
la fuente.**

### Verificación manual

**Revisados 15 grupos. Agrupamientos incorrectos: 0.**

Los cinco grupos con más variantes —donde estaría el error si lo hubiera— son:

| clave normalizada | literales encontrados | filas | ¿es lo mismo? |
|---|---|---:|---|
| `pasa uva pasa` | `Pasa (uva Pasa)` / `Pasa (Uva Pasa)` | 4,093 / 295 | sí · mayúscula |
| `vagitrol v` | `Vagitrol -v` / `Vagitrol -V` | 11,389 / 626 | sí · mayúscula |
| `acido folico` | `Acido Fólico` / `Ácido Fólico` | 7,559 / 373 | sí · acento |
| `minibocinas portatiles bluetooth` | `Minibocinas…` / `MiniBocinas…` | 9,443 / 597 | sí · mayúscula |
| `sistema gb solucion alopecia` | `Sistema Gb.` / `Sistema GB.` | 9,677 / 990 | sí · mayúscula |

**El hallazgo no es el cero: es el patrón.** Los cinco casos difieren
**únicamente en mayúsculas o en acentos**. Ninguno es una variante semántica
—no hay «Coca Cola» contra «Refresco de Cola»—, ni un error de dedo, ni una
abreviatura distinta. La variación de escritura de esta fuente es **mecánica**,
y una normalización determinista la resuelve entera. No hace falta comparación
difusa para esto.

En los diez grupos de control tomados al azar aparecen dos casos de mojibake
—`Coctel de Frutas en Alm?bar`, `Ma?z Pozolero`— que confirman lo dicho arriba:
el `?` crea claves separadas, y por eso se mide sin ellas.

### Presentaciones por producto — otra cosa, y más grande

Esto ya no es variación de escritura: son productos que de verdad se venden de
formas distintas. Ninguna normalización los junta, ni debe.

| | valor |
|---|---:|
| productos distintos | 891 |
| presentaciones por producto, media | 6.8 |
| presentaciones por producto, mediana | **2** |
| presentaciones por producto, máximo | **248** |
| productos con más de 10 presentaciones | 137 de 891 (15.4%) |
| marcas por producto, media | 3.9 |

**La mediana de 2 es un espejismo.** La fijan los productos raros: los
medicamentos de marca —`Bactrim F`, `Uniclar`, `Pantozol`, `Celebrex`— aparecen
con una sola presentación cada uno y son cientos. Los productos que alguien
pondría en una despensa están en el otro extremo:

| producto | filas | presentaciones | marcas |
|---|---:|---:|---:|
| Refresco | 465,710 | 23 | 24 |
| Yoghurt | 308,147 | 39 | 11 |
| Jamón | 282,553 | 38 | 25 |
| Toalla Femenina | 271,252 | 55 | 7 |
| Carne Res | 240,318 | 57 | 5 |
| Atún | 230,303 | 41 | 22 |
| Shampoo | 235,592 | 42 | 18 |

**Los 20 productos de mayor volumen concentran 4,653,735 filas (el 21.8% del
corpus) y los 20 pasan de 10 presentaciones** —el mínimo del grupo es 11—, con
una media de **29.1 presentaciones y 16.1 marcas** cada uno. Es 4.3 veces la
media del corpus.

De cada 7.4 presentaciones escritas por producto, 6.8 son distintas de verdad.
Sólo 0.6 son cómo se escribió. **El problema no es de normalización: es de
modelo de datos.**

<!-- Para saber qué producto tiene las 248 presentaciones:
SELECT producto, count(DISTINCT presentacion) n
FROM read_parquet('~/canastamx-datos/procesado/por_archivo/*.parquet', union_by_name=true)
GROUP BY producto ORDER BY n DESC LIMIT 5; -->

### Qué implica para H3

<!-- Guía de lectura de la plantilla:
     1 a 3 variantes  → la fuente ya viene normalizada. 85% es cómodo
     4 a 8 variantes  → normal. 85% alcanzable con comparación difusa
     más de 10        → hay que bajar la meta o acotar el recorte -->

**1.29 variantes por artículo cae en la primera banda. En el eje de la
escritura, H3 está holgada y no hace falta comparación difusa.** La verificación
manual lo respalda: los cinco grupos revisados difieren sólo en mayúsculas y
acentos, que es exactamente lo que una normalización determinista resuelve al
100%. La meta del 85% no está en riesgo por este lado.

**Pero H3 tiene un segundo eje que estas cifras no cubren, y ahí sí hay decisión
que tomar.** Emparejar «leche» con un precio no es un problema de ortografía: es
que `Leche Ultrapasteurizada` tiene 13 presentaciones y 30 marcas, y `Carne Res`
tiene 57 presentaciones. La pregunta no es «¿se escribe igual?» sino **«¿qué
cuenta como el mismo artículo para quien arma su despensa?»**. De esa definición
depende el número de H3:

| unidad de emparejamiento | artículos | qué le responde al usuario | costo |
|---|---:|---|---|
| `producto` | 891 | «la leche cuesta entre $22 y $45» | trivial de alcanzar, respuesta vaga |
| `producto` + `presentacion` | 5,015 | «leche entera 1 L: $28 aquí, $31 allá» | el usuario elige entre 13 opciones |
| `producto` + `presentacion` + `marca` | 5,750 | el artículo exacto | preciso, pero pide mucho al usuario |

**Propuesta para la reunión:** emparejar en `producto` + `presentacion` y tratar
`marca` como filtro opcional, no como parte de la identidad. Razón: la
presentación es lo que hace comparable un precio con otro —un kilo contra un
kilo—, mientras que la marca es preferencia, y además el 34.4% del corpus dice
`S/m` y no la declara. Si la decisión es otra, hay que dejarla escrita hoy:
**H3 no se puede medir hasta que esté tomada.**

### Regla de cuarentena (CU-03), corregida

La versión anterior decía «mandar a cuarentena cualquier registro con `?`». Eso
costaría el 3.61% del corpus. La regla medida es:

1. Aplicar el diccionario de reparación **antes** de agrupar por categoría,
   municipio o producto (`mojibake-diccionario.csv`, 1,650 entradas).
2. Lo que quede sin gemelo único va a la tabla de rechazos con el motivo
   `codificacion_irrecuperable`. Coste real: **0.36% del corpus**, no 3.61%.
3. Los 63 ambiguos son casi todos el apóstrofo (`Kellogg's` contra `Kellogg´s`).
   Se resuelven por frecuencia: donde un gemelo domina diez a uno en los datos
   limpios, la fuente ya decidió. Sólo lo que quede parejo es decisión humana.

---

## 4 · Decisiones que le tocan a la reunión, no al guión

1. **Colima y Nayarit no existen en la fuente.** ¿El producto lo declara, o se
   acota el alcance a las 30 entidades presentes?
2. **El 34.4% del corpus no declara marca** (`S/m`). ¿Es un valor, un nulo, o
   una categoría propia? Cambia cómo se agrupa y cambia H3.
3. **Qué es «el mismo artículo»** (sección 3). De esto depende el número de H3 y
   no se puede medir hasta que esté decidido.
4. **Qué hacer con `folio`, `cv_producto` y `cv_marca`**, que existen en 2 de 38
   archivos y no están documentados. Duda 8 del diccionario de C2.

---

## 5 · Observación de fondo

**La fuente se degradó y se recuperó sola dentro del periodo observado.** En
2026 `estado` y `catalogo` ganaron los acentos que les faltaban en 2025,
mientras `giro` y `categoria` los perdieron convertidos en `?`. Junio reventó,
con 18 columnas y 753 mil filas rotas. Julio volvió a la normalidad en las dos
cosas a la vez.

Un sistema que ingiera esto sin compuertas publica junio como si nada. Eso es
exactamente lo que este proyecto dice que va a detectar, y ahora está medido con
números propios en lugar de argumentado en abstracto.
