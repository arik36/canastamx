# ADR 002 · Qué cuenta como «el mismo artículo»

- **Fecha:** 11 de septiembre de 2026
- **Estado:** aceptada
- **Participantes:** Ariadne (A), Ari Adair (B), Liseth (C1), Oscar (C2), Karen (D)

## Contexto

Esta es la decisión de la que cuelgan casi todas las demás: el modelo de
dominio de C1, la pantalla de búsqueda de C2, el tablero de D, la clave del
contrato de datos de A y la forma de medir H3. Hasta tomarla, ninguna de las
cinco se puede cerrar.

El perfilado la volvió urgente con tres hallazgos.

**La variación de escritura resultó ser casi nula.** 1.29 formas de escribir el
mismo artículo, mediana 1, cero agrupamientos incorrectos en la revisión manual
de 15 grupos, y los cinco casos con más variantes difieren **sólo en mayúsculas
o acentos** (`Acido Fólico` / `Ácido Fólico`). O sea: el problema que
esperábamos —que cada cadena escribiera distinto— no existe.

**Pero hay otra variación, mucho más grande, que no es de escritura.**
`Carne Res` tiene **57 presentaciones** distintas; `Toalla Femenina`, 55;
`Leche Ultrapasteurizada`, 13 presentaciones y 30 marcas. Los 20 productos de
mayor volumen —el 21.8% del corpus— promedian **29.1 presentaciones y 16.1
marcas** cada uno. Eso no lo junta ninguna normalización, ni debe: un kilo de
carne no es lo mismo que 200 gramos.

**La clave de unicidad que el protocolo había propuesto no aguanta.**
(`producto`, `nombre_comercial`, `direccion`, `fecha_registro`) deja
**12,295,396 filas de más**: más de la mitad del corpus. Tiene sentido —el
mismo establecimiento cotiza el mismo producto en varias presentaciones el mismo
día— y apunta exactamente a esta decisión.

Y un cuarto hecho que condiciona todo lo anterior: **7,350,628 filas (el 34.4%)
no declaran marca.** Dicen `S/m` o `S/M`. No son celdas vacías y no son marcas:
son una tercera cosa.

## Decisión

### 1 · El artículo se identifica por `producto` + `presentacion`

Dos filas hablan del mismo artículo cuando coinciden el producto y la
presentación. `Leche Ultrapasteurizada · 1 L` es un artículo;
`Leche Ultrapasteurizada · 500 Ml` es otro.

**Razón:** la presentación es lo que hace comparable un precio con otro —un
litro contra un litro—. Comparar sólo por `producto` mete en la misma bolsa
cosas que no se parecen, y ya se vio el daño que hace: en el perfilado, un
termómetro a $999 parecía 10.4 veces más caro que «su producto», y resultó que
la etiqueta `termometro` cubría uno de mercurio de $30 y uno infrarrojo que
llega a $1,300 —el precio de $999 es la mediana de su propia presentación—. No
había dato malo: había una frontera mal puesta.

### 2 · `marca` se guarda y se muestra, pero no identifica

La marca **no forma parte de la identidad del artículo**. Se conserva en cada
registro y sirve para que el usuario, **después** de recibir los resultados de
lo que buscó, pueda ordenarlos y filtrarlos: por marca, y por precio de menor a
mayor o al revés.

**Razón:** la marca es preferencia, no unidad de comparación. Y hacerla parte de
la identidad dejaría al 34.4% del corpus sin identidad completa, porque no la
declara.

### 3 · `S/m` es una categoría propia

`S/m` **no es nulo y no es una marca más.** Es «producto genérico», una
categoría en sí misma.

**Sobre el orden**, la reunión lo dijo con esa palabra: *«preferentemente que al
buscar un producto sean los últimos que se muestren»*. Se recoge como
preferencia, no como regla dura: es el **orden por omisión**, y el usuario puede
cambiarlo.

> **Derivado, no votado en la reunión. Se ratifica el 16 de septiembre.**
> La fuente escribe `S/m` y `S/M`. **Si se dejan las dos formas, «genérico» no
> va a ser una categoría: van a ser dos**, y el orden de arriba fallaría en la
> mitad de los casos. El contrato tiene que normalizarlas a un solo literal, y
> hay que elegir cuál.

### 4 · La clave de fila del contrato **no es** la misma clave

> **Derivado, no votado en la reunión. Se ratifica el 16 de septiembre.**
> Se anota aquí porque A escribe el contrato de datos el lunes 14 y sin esto
> sale mal.

Son **dos claves distintas y hacen dos trabajos distintos**:

| | Para qué sirve | Qué la compone |
|---|---|---|
| **Identidad del artículo** | Lo que el usuario compara. Lo que agrupa la aplicación y el tablero. Lo que mide H3. | `producto` + `presentacion` |
| **Clave de fila del contrato** | Lo que la compuerta de calidad usa para saber si una fila es un duplicado | `producto` + `presentacion` + **`marca`** + `nombre_comercial` + `direccion` + `fecha_registro` |

**Por qué la segunda sí lleva `marca`:** el mismo establecimiento, el mismo día,
cotiza `Leche Ultrapasteurizada · 1 L` de Lala a $25 y de Alpura a $27. Son dos
filas legítimas. Si el contrato declara única la combinación sin `marca`, la
compuerta de calidad va a mandar una de las dos a la tabla de rechazos **el día
de la primera ingesta**, y va a hacerlo con millones de filas.

Que el usuario no elija por marca no significa que la marca no distinga una
fila de otra. Lo mide `docs/datos/perfilado/medir-decisiones.py`, y la cifra
va al contrato.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| **Identificar por `producto` solo** | Da respuestas que no sirven: «la leche cuesta entre $22 y $45». Y junta artículos que no se parecen: el caso del termómetro de mercurio contra el infrarrojo bajo la misma etiqueta. |
| **Identificar por el trío, con `marca` dentro** | Es lo más preciso, pero le pide demasiado al usuario: para saber cuánto cuesta la leche tendría que elegir entre 30 marcas antes de ver un precio. Y deja al 34.4% del catálogo con identidad incompleta, porque dice `S/m`. |
| **Tratar `S/m` como nulo** | Un tercio del corpus se volvería inservible. Peor: un nulo en una columna obligatoria es motivo de rechazo en la compuerta, así que estaríamos mandando a cuarentena 7.35 millones de filas buenas. |
| **Tratar `S/m` como una marca más** | Aparecería mezclada entre Lala y Alpura como si fuera una marca comercial, y el usuario la leería como tal. |
| **Usar la misma clave para la identidad y para el contrato** | Es el error que este ADR existe para evitar. Descrito en el punto 4. |
| **Resolver la variación con comparación difusa** | No hace falta. Toda la variación medida es mecánica —mayúsculas y acentos— y una normalización determinista la resuelve al 100%. Meter comparación difusa aquí sería complejidad sin problema que la justifique. **Ojo: esto corrige el protocolo**, que compromete la reconciliación *«mediante vocabulario canónico, diccionario de equivalencias y comparación difusa»*. Va anotado en las correcciones del ADR 001. |

## Consecuencias

### Lo que cambia en el trabajo de cada quien

**A · contrato de datos, semana 2.** El contrato se escribe con la **clave de
fila**, no con la de artículo. La clave del protocolo queda derogada: dejaba
12,295,396 filas de más. Antes de escribirlo, correr
`medir-decisiones.py` para tener la cifra de cuántas filas rechazaría cada
clave candidata. · **el lunes 14, antes de escribir el contrato**.

**A · contrato de datos, semana 2.** Regla de normalización de `marca`: `S/m` y
`S/M` colapsan a un solo literal. Se decide cuál y se escribe en el contrato.
Sin esa regla, la categoría «genérico» son dos categorías.

**C1 · modelo de dominio, semana 2.** El agregado tiene que reflejar esto:
**Artículo** = producto + presentación, con marca como **atributo** del
registro de precio, no del artículo. Si el modelo ya estaba escrito con marca
dentro de la identidad, hay que corregirlo antes de implementar Usuario y
Canasta, porque después cuesta el triple. · `docs/analisis/modelo-dominio.md`.

**C2 y D · pantallas de búsqueda y listados.** El orden por defecto pone los
`S/m` al final. El usuario recibe resultados agrupados por artículo y los
ordena por marca o por precio, ascendente y descendente. · **semanas 7 a 9**.

**C1 y C2 · contrato OpenAPI.** El objeto que viaja entre el servicio de
dominio y la aplicación móvil tiene que distinguir artículo de registro de
precio. Es su punto de acuerdo y conviene cerrarlo con esto ya decidido. ·
**semana 5**.

### Lo que esta decisión desbloquea

**H3 ya se puede enunciar.** El «mismo artículo» del examen de 200 pares es
`producto` + `presentacion`. Sin esta decisión, H3 no tenía respuestas
correctas contra las cuales calificar.

**Pero todavía no se puede medir**, y por otra razón: falta saber si los 200
pares existen. Se resuelve en **ADR 004**, con el resultado de
`docs/datos/perfilado/h3-entre-cadenas.py` sobre datos reales. · **A · antes
del 18 de septiembre**.

### Una cifra que hay que corregir

La tabla «unidad de emparejamiento» de `docs/datos/perfilado.md` §3 trae
**«~6,000»** artículos para `producto` + `presentacion` y **«5,750»** para el
trío con `marca`. **No puede ser:** agregar una columna a una clave nunca reduce
el número de claves distintas, así que el nivel de en medio tiene que ser menor
o igual que 5,750. El ~6,000 era una estimación a ojo que se coló como si fuera
medición, y la tilde de «~» no alcanzó a avisarlo.

`medir-decisiones.py` mide los tres niveles de una sola pasada y con la
misma normalización. **El número que salga es el que va al ADR, al informe y a
`perfilado.md`.** · **A · el lunes 14, antes de escribir el contrato**.

No es un detalle cosmético: es el número de artículos del catálogo sobre el que
el equipo acaba de decidir construir.
