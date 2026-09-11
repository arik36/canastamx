# Recapitulado del perfilado, explicado desde cero

Este documento es para leerse sin saber pandas. Explica el flujo completo de la
semana, qué hace cada guión bloque por bloque, qué estaba mal en las primeras
versiones y por qué, y qué devuelve cada archivo que se genera.

Complementa `perfilado.md`, que trae los resultados; aquí está el **cómo** y el
**por qué**. Las demostraciones ejecutables están en `demos-explicativas.py`.

---

# Parte 0 · Lo que hay que entender antes de leer una línea de código

## Por qué esto no se siente como SQL

Tu intuición viene de SQL: una tabla existe en algún lado, escribes una consulta,
te devuelve filas. Aquí hay dos herramientas y sólo una se parece a eso.

**pandas** es una biblioteca de Python que mete una tabla **dentro de la memoria
de tu programa**. Esa tabla se llama **DataFrame** y una columna suya se llama
**Series**. No hay servidor, no hay `SELECT`: manipulas la tabla con métodos de
Python (`df["precio"].max()`). Es cómodo para archivos chicos y para tareas que
no son consultas —leer un CSV, convertir tipos, escribir un parquet—. Su límite
es que **todo tiene que caber en RAM**.

**DuckDB** es una base de datos que corre dentro de tu programa, sin instalar
servidor, y que **sí habla SQL**. Lee archivos directamente del disco, trabaja por
partes y no necesita que todo quepa en memoria.

En este proyecto se usan las dos, cada una para lo suyo:

```
CSV (texto, 6.3 GB)  --pandas-->  parquet (columnar)  --DuckDB (SQL)-->  respuestas
      ^                                  ^                                    ^
   38 archivos               un archivo por CSV                   todo lo demás
```

**Casi todo el trabajo pesado es SQL.** pandas sólo aparece en la conversión de
CSV a parquet, y para imprimir tablas bonitas. Si el SQL te resulta más natural,
buena noticia: es la mayor parte.

## Por qué parquet y no seguir con los CSV

Un CSV es texto plano. Para saber el precio de la fila cinco millones hay que
leer y descomponer los cinco millones anteriores, porque no hay forma de saber
dónde empieza cada fila sin contar los saltos de línea.

Un **parquet** guarda cada columna por separado, ya con su tipo y comprimida.
`max(precio)` lee sólo la columna de precios y ni toca las otras catorce. Además
guarda un resumen por bloque, así que a veces ni lee: mira el resumen y descarta.

Por eso `perfilado_nivel2.py` convierte una vez y **todo lo demás trabaja sobre
los parquet**. La conversión tarda; las 40 consultas siguientes no.

## Qué es una vista

Varios guiones hacen esto:

```python
con.sql("CREATE VIEW q AS SELECT ... FROM read_parquet(...)")
```

Una **vista** es una consulta guardada con nombre. **No copia datos.** Cuando
después escribes `FROM q`, DuckDB ejecuta la consulta de la vista al vuelo. Sirve
para no repetir veinte veces la misma normalización de texto.

## Las tres palabras que más se repiten

| palabra | qué es |
|---|---|
| **normalizar** | reducir un texto a una forma canónica para poder comparar: minúsculas, sin acentos, sin puntuación. *(En el nombre `perfilado_nivel2.normalizar()` significa otra cosa: convertir CSV a parquet. Mala elección de nombre, heredada.)* |
| **mojibake** | texto roto por una conversión de codificación. Aquí aparece como `?` donde iba una letra acentuada: `Jab?n`, `Ma?z`. |
| **centinela** | un valor inventado pero válido en formato que alguien usa para decir «aquí no hay dato». Por ejemplo 999 en un campo de precio. |

---

# Parte 1 · El flujo de la semana

## Las cinco preguntas, en orden

El perfilado no es un guión: son cinco preguntas que sólo tienen sentido en ese
orden, porque cada una necesita la respuesta de la anterior.

| # | pregunta | guión | tarea |
|---|---|---|---|
| 1 | ¿De dónde salen los datos y qué forma tienen? | *(a mano)* | T002 |
| 2 | ¿Qué columnas hay, de qué tipo, y qué falta? | `perfilado_nivel1.py` | T003 |
| 3 | ¿Los valores son posibles? ¿Hay duplicados? | `perfilado_nivel2.py` | T004 |
| 4 | ¿De cuántas formas está escrita la misma cosa? | `perfilado_nivel3.py` | T005 |
| 5 | ¿Qué de todo esto se vuelve regla del contrato? | *(la reunión)* | T018 |

`mojibake.py` y `centinelas.py` nacieron **después**, cuando los pasos 2 y 3
dejaron preguntas que sus guiones no podían contestar.

## Por qué ese orden y no otro

**El nivel 1 va primero porque sin saber qué columnas hay no se puede preguntar
nada más.** Y encontró algo que cambió todo lo demás: no hay un esquema, hay dos
(15 columnas en 36 archivos, 18 en dos), y no hay una codificación, hay dos.

**El nivel 2 va después porque necesita esos hallazgos para leer bien.** Si no
supieras que mayo de 2026 viene en `latin-1` y con fecha `DD/MM/YYYY`, el parquet
de mayo saldría con los acentos rotos y con el día y el mes intercambiados.

**El nivel 3 va al final porque mide texto, y el texto había que entenderlo
primero.** Contar «de cuántas formas se escribe Aguacate» sin saber que hay un
`?` metido en medio da una cifra inflada con artículos que no existen.

## El orden de ejecución hoy

```bash
python docs/datos/perfilado/mojibake.py          # 1
python docs/datos/perfilado/perfilado_nivel2.py  # 2 · usa lo que dejó el 1
python docs/datos/perfilado/centinelas.py        # 3 · usa lo que dejó el 1
python docs/datos/perfilado/revisar-candidatos.py # 4 · usa lo que dejó el 3
python docs/datos/perfilado/perfilado_nivel3.py  # 5 · independiente
python docs/datos/perfilado/perfilado_nivel1.py  # 6 · independiente, el más lento
```

Las dependencias reales son **1 → 2**, **1 → 3** (Parte 5) y **3 → 4**:
`revisar-candidatos.py` lee la lista corta que deja `centinelas.py`.

---

# Parte 2 · `perfilado_nivel1.py`, bloque por bloque

## Qué contesta

«¿Qué columnas hay, de qué tipo son, y qué falta?» Es el único guión que lee los
**CSV crudos** para medir. No genera parquet.

## Cómo estaba la v1

### Bloque 1 · dónde están los archivos

```python
CARPETAS = [
    Path.home() / "canastamx-datos" / "crudo" / "QQP_2025",
    Path.home() / "canastamx-datos" / "crudo" / "QQP_2026",
]
ATIPICOS_MAYO_2026 = {"05-2026_Q1.csv", "05-2026_Q2.csv"}
```

`Path.home()` es tu carpeta personal (`/home/mlizz`). El operador `/` sobre un
`Path` **no divide**: pega pedazos de ruta. Es la forma de armar rutas que
funciona igual en Linux y en Windows.

`ATIPICOS_MAYO_2026` es un **conjunto** (`set`): una lista sin orden donde
preguntar «¿está esto adentro?» es instantáneo. Guarda los dos archivos que
rompen el patrón general.

### Bloque 2 · los acumuladores

```python
total_filas = 0
nulos = {}
distintos = {}
```

Un **diccionario** (`{}`) es una tabla de dos columnas: clave y valor. Aquí la
clave es el nombre de la columna y el valor, lo que se lleva contado. Se
inicializan vacíos y se van llenando archivo por archivo, porque los 38 no caben
juntos en memoria.

### Bloque 3 · el bucle que lee

```python
for carpeta in CARPETAS:
    for path in sorted(carpeta.glob("*.csv")):
        es_atipico = path.name in ATIPICOS_MAYO_2026
        encoding = "latin-1" if es_atipico else "utf-8-sig"
        df = pd.read_csv(path, encoding=encoding, low_memory=False)
        total_filas += len(df)
```

`glob("*.csv")` lista los archivos que terminan en `.csv`. `sorted()` los pone en
orden para que dos corridas den lo mismo.

`"latin-1" if es_atipico else "utf-8-sig"` se lee como una frase: «latin-1 si es
atípico, si no utf-8-sig».

`pd.read_csv(...)` devuelve un **DataFrame**: el archivo entero en memoria.
`len(df)` son sus filas. **Aquí está el primer error.**

### Bloque 4 · el conteo por columna

```python
for col in df.columns:
    nulos[col] = nulos.get(col, 0) + int(df[col].isna().sum())
    distintos.setdefault(col, set()).update(df[col].dropna().unique())
```

`df[col]` es una columna (una Series). `.isna()` devuelve una columna de
verdadero/falso: verdadero donde hay nulo. `.sum()` sobre verdadero/falso los
cuenta, porque verdadero vale 1.

`nulos.get(col, 0)` es «dame lo que llevo de esa columna, y si nunca la he visto,
dame 0». `.setdefault(col, set())` es lo mismo para conjuntos.

`.unique()` da los valores distintos, `.dropna()` quita los nulos antes.
**Aquí está el segundo error, y el tercero.**

## Los cuatro errores, con ejemplo

### Error 1 · pandas convertía textos a nulo sin avisar

`pd.read_csv` por omisión mira cada celda y, si el texto está en una lista suya,
lo convierte a nulo. La lista tiene diecinueve entradas: `NA`, `N/A`, `n/a`,
`NULL`, `null`, `NaN`, `nan`, `-NaN`, `-nan`, `None`, `<NA>`, `#NA`, `#N/A`,
`#N/A N/A`, la cadena vacía y cuatro formas de infinito de Excel.

Con este CSV de seis filas, donde **sólo una celda está vacía**:

```
marca,precio
S/m,19
NULL,20
NA,21
nan,22
-,23
,24
```

la lectura vieja devuelve:

```
  marca  precio
0   S/m      19
1   NaN      20     ← era 'NULL'
2   NaN      21     ← era 'NA'
3   NaN      22     ← era 'nan'
4     -      23     ← '-' sobrevive, no está en la lista
5   NaN      24     ← ésta sí estaba vacía

marca.isna().sum() = 4     ← dice 4 nulos donde hay 1 celda vacía
```

**Por qué importa.** Una celda vacía es «el capturista no escribió nada». Una
celda con la palabra `NULL` es «el capturista escribió NULL», que llegó a
propósito y es un dato sobre el sistema de origen. Después de `read_csv` las dos
son lo mismo y ya no se pueden separar.

Y hay una consecuencia concreta para el proyecto: **C2 midió su diccionario con
`keep_default_na=False`** justamente para no mezclarlas. Tu «0 nulos» y su «0
vacíos» decían el mismo número por motivos distintos, y ninguno de los dos lo
sabía.

### Error 2 · `.dropna()` escondía valores de la lista de distintos

Es consecuencia del error 1. Si pandas convirtió `NULL` a nulo, `.dropna()` lo
tira y ese valor tampoco aparece en la lista de valores distintos:

```
valores distintos, lectura vieja: ['-', 'S/m']
valores distintos, lectura nueva: ['', '-', 'NA', 'NULL', 'S/m', 'nan']
```

Cuatro de los seis valores de la columna eran invisibles. Si mañana la fuente
empieza a mandar `NULL` en `producto`, el perfilado no se entera.

### Error 3 · una columna que no existe no sumaba nulos

```python
for col in df.columns:          # ← sólo las que EXISTEN en este archivo
```

El bucle recorre las columnas **del archivo actual**. En los 36 archivos que no
traen `folio`, la columna no está en `df.columns`, el bucle ni pasa por ahí, y
`folio` no suma nada. Al final se divide entre el total de filas y sale 0%.

Con dos archivos de juguete, uno con `folio` y otro sin:

```
filas totales: 4
nulos contados con el bucle de la v1: {'producto': 0, 'folio': 0}
  -> folio: 0/4 = 0% de nulos
  pero 2 de las 4 filas NO TIENEN la columna folio.

con el conteo nuevo: ausente = 2/4 = 50%
```

Tú detectaste el síntoma sola y lo anotaste al pie de la tabla. Éste es el
mecanismo. Y el número real, ya medido, es **94.12%**.

### Error 4 · el tipo se infería en vez de comprobarse

```python
dtypes_vistos.setdefault(col, set()).add(str(df[col].dtype))
```

Esto anota lo que pandas **adivinó**. «`precio` es float64» no es un hallazgo: es
una opinión de pandas sobre ese archivo. Si un archivo trajera un precio con
letras, pandas dejaría la columna como texto y el guión lo anotaría sin decir
cuántas celdas fallaron.

El diccionario declara `Número (18,2)`. Lo que el contrato necesita saber es
**cuántas filas no cumplen esa declaración**.

## Cómo quedó la v2

### Bloque nuevo 1 · leer sin que nada se convierta solo

```python
for trozo in pd.read_csv(path, encoding=encoding, dtype=str,
                         keep_default_na=False, na_filter=False,
                         chunksize=TROZO):
```

- `dtype=str` — trae todo como texto. Nada se interpreta.
- `keep_default_na=False` — apaga la lista de diecinueve textos.
- `na_filter=False` — apaga la detección de nulos entera.
- `chunksize=200_000` — **en vez de un DataFrame, devuelve un generador**: el
  `for` va recibiendo pedazos de 200 mil filas. Como ahora todo es texto y el
  texto ocupa más que los números, se lee por partes para no llenar la RAM.

### Bloque nuevo 2 · contar cuatro cosas distintas

```python
vc = s.value_counts()
idx = vc.index

presentes[col] += int(vc.sum())
distintos[col].update(idx)
vacios[col]    += int(vc.get("", 0))
```

`value_counts()` devuelve **cuántas filas tiene cada valor distinto**, ordenado.
De ahí sale todo de una sola pasada: `vc.index` son los valores distintos,
`vc.sum()` son las filas, `vc.get("", 0)` son las que valen cadena vacía.

Es la misma idea de un `GROUP BY valor` en SQL, pero sobre una columna en memoria.

```python
solo_esp = idx.to_series().str.strip().eq("") & idx.to_series().ne("")
espacios[col] += int(vc[solo_esp.values].sum())
```

`.str.strip()` quita espacios de las orillas. `.eq("")` pregunta si quedó vacío.
`& ...ne("")` excluye las que ya estaban vacías, para no contarlas dos veces.
`vc[condicion].sum()` suma las filas de los valores que cumplen.

Y al final, **lo que antes era «nulos» ahora son cuatro cosas separadas**:

| categoría | qué significa |
|---|---|
| `ausente` | la columna no existe en ese archivo |
| `vacía` | existe y vale `""` |
| `sólo espacios` | existe y vale `"   "` |
| `marcador` | existe y vale `NA`, `NULL`, `S/m`… |

**El guión no decide cuál es un nulo.** Eso lo decide el contrato, y el contrato
lo deciden ustedes en la reunión. El guión sólo mide.

### Bloque nuevo 3 · comprobar el tipo en vez de inferirlo

```python
n = pd.to_numeric(s, errors="coerce")
no_numerico[col] += int((n.isna() & s.str.strip().ne("")).sum())
```

`pd.to_numeric(..., errors="coerce")` intenta convertir a número y **lo que no
puede, lo deja en nulo**. Entonces: «es nulo después de convertir» **y** «no
estaba vacío antes» = era texto que no es número. Eso sí es una violación del
tipo declarado, y sí es una regla de contrato.

### Bloque nuevo 4 · arreglar el sesgo de `folio`

```python
presentes[col] += int(vc.sum())      # filas donde la columna EXISTE
...
ausente = filas_totales - presentes[col]
```

Se cuenta al revés: en vez de sumar nulos donde la columna está, se suma
presencia y se resta del total. Lo que no se contó es lo ausente.

---

# Parte 3 · `perfilado_nivel2.py`, bloque por bloque

## Qué contesta

«¿Los valores son posibles? ¿Hay duplicados? ¿Cuántos establecimientos hay?»
Y además **es el que fabrica los parquet** que usan todos los demás.

## Bloque 1 · `normalizar()` — de CSV a parquet

```python
def normalizar(rehacer=()):
    for carpeta in CARPETAS:
        for path in sorted(carpeta.glob("*.csv")):
            destino = PARQUETS / f"{path.stem}.parquet"
            if destino.exists():
                continue
```

`path.stem` es el nombre sin extensión: de `01-2025_01.csv` saca `01-2025_01`.
`if destino.exists(): continue` es «si ya lo convertí, sáltatelo». Por eso la
segunda corrida es instantánea.

```python
            df = pd.read_csv(path, encoding=encoding, dtype=str,
                             keep_default_na=False, na_filter=False)
            for col in ("precio", "latitud", "longitud"):
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            df["fecha_registro"] = pd.to_datetime(
                df["fecha_registro"], format=formato_fecha, errors="coerce")
            df.to_parquet(destino, index=False)
```

Se lee como texto y **los tipos se aplican a mano, a propósito**. El orden
importa: primero texto crudo, luego conversión explícita. Así un `NULL` de texto
llega al parquet como el texto que es.

`index=False` evita que pandas guarde su numeración de filas como una columna
extra, que no significa nada.

> ### El error que tenía la v1 aquí
>
> ```python
> if not any(PARQUETS.glob("*.parquet")):
>     normalizar()
> ```
>
> Léelo literal: «si no existe **ningún** parquet, genera». Con 36 parquet
> presentes y 2 borrados, la condición es falsa y **no se genera nada**. Sin
> error y sin aviso.
>
> Y `normalizar()` ya tenía adentro la comprobación correcta
> (`if destino.exists(): continue`). **El guardián de afuera anulaba la lógica
> buena de adentro.** Ahora `normalizar()` se llama siempre y la comprobación de
> adentro hace el trabajo.

## Bloque 2 · `conectar()` — la vista

```python
con = duckdb.connect()
con.sql("SET memory_limit='4GB'")
tmp = RAIZ / "tmp-duckdb"
con.sql(f"SET temp_directory='{tmp}'")
```

`memory_limit` es cuánta RAM puede usar DuckDB. Cuando una operación no cabe
—ordenar 21 millones de filas para sacar una mediana— **derrama a disco**:
escribe pedazos temporales, trabaja por partes y los junta.

`temp_directory` es dónde escribe esos pedazos. **Por omisión es `.tmp`,
relativo a la carpeta desde la que corres el guión** — o sea, dentro del
repositorio. Con 21 millones de filas eso son gigabytes apareciendo en tu
carpeta de git. Por eso se apunta junto a los parquet.

```python
con.sql(f"""
    CREATE VIEW qqp AS
    SELECT f.* EXCLUDE (categoria),
           {categoria_limpia}                        AS categoria,
           lower(strip_accents({categoria_limpia}))  AS categoria_norm
    FROM {fuente} f
    {join}
""")
```

- `f.* EXCLUDE (categoria)` — todas las columnas menos ésa. Se quita para
  volverla a poner ya reparada.
- `categoria_norm` es la **clave de agrupación**: minúsculas y sin acentos.
- `{join}` mete el `LEFT JOIN` con el diccionario de mojibake. Parte 5.

`read_parquet('.../*.parquet', union_by_name=true)` lee los 38 como si fueran uno
solo. **`union_by_name=true` es lo que hace que funcione** con dos esquemas
distintos: junta por nombre de columna, no por posición, y donde una columna no
existe pone nulo. Sin eso, los 36 archivos de 15 columnas y los 2 de 18 no se
podrían leer juntos.

## Bloque 3 · las mediciones

```python
def distribucion_por_categoria(con):
    return con.sql("""
        SELECT categoria_norm,
               min(precio) AS min,
               quantile_cont(precio, 0.25) AS p25,
               quantile_cont(precio, 0.5)  AS mediana,
               ...
        FROM qqp GROUP BY categoria_norm ORDER BY categoria_norm
    """).df()
```

`quantile_cont(precio, 0.25)` es el percentil 25: el precio por debajo del cual
está la cuarta parte de las filas. `.df()` al final convierte el resultado de
DuckDB en un DataFrame de pandas, sólo para imprimirlo bonito — son 45 filas, no
21 millones.

```python
def duplicados_exactos(con):
    return con.sql("""
        WITH grupos AS (
            SELECT * EXCLUDE (folio, cv_producto, cv_marca, categoria_norm),
                   count(*) AS n
            FROM qqp GROUP BY ALL
        )
        SELECT coalesce(sum(n - 1), 0) FROM grupos WHERE n > 1
    """).fetchone()[0]
```

`GROUP BY ALL` agrupa por **todas las columnas que no son agregados** — aquí, las
15. Entonces `n` es cuántas filas idénticas hay. `n - 1` son las sobrantes (una
es la original). `coalesce(x, 0)` es «x, y si es nulo, 0» — por si no hay ningún
duplicado y la suma sale nula.

`.fetchone()[0]` toma el primer valor de la primera fila, porque el resultado es
un solo número.

## Los cinco errores de la v2, con ejemplo

### Error 1 · el guardián de `normalizar()`

Explicado arriba, en el recuadro del bloque 1.

### Error 2 · los cinco `replace()` encadenados

```sql
lower(replace(replace(replace(replace(replace(
   categoria,'á','a'),'é','e'),'í','i'),'ó','o'),'ú','u'))
```

Dos problemas. Sólo cubre las cinco vocales acentuadas **en minúscula**; y **el
`lower()` está por fuera**, así que los `replace()` corren sobre el texto todavía
con mayúsculas. En `CAFÉ`, la `É` no coincide con `'é'` y sobrevive; después
`lower()` la convierte en `é`, pero ya es tarde.

```
 original cadena_de_replace strip_accents
     Café              cafe          cafe
     CAFÉ              café          cafe     ← ¡grupos distintos!
   Azúcar            azucar        azucar
   AZÚCAR            azúcar        azucar     ← ¡grupos distintos!
Navideños         navideños     navidenos
 Pingüino          pingüino      pinguino

grupos con la cadena de replace : 6
grupos con strip_accents        : 4
```

Con tus datos no te mordió porque QQP escribe en tipo título y los acentos caen
en minúsculas. **Eso es suerte, no diseño.**

`strip_accents()` descompone cada letra acentuada en «letra + marca» y tira la
marca. Cubre todo el alfabeto latino.

> **Un cuidado:** `strip_accents` convierte `ñ` en `n`. Por eso en tu tabla
> aparece `productos de temporada (navidenos)`. Está bien como **clave de
> agrupación** y está mal como **texto para mostrarle al usuario**. La vista
> guarda las dos: `categoria` con su escritura original y `categoria_norm` sólo
> para agrupar.

### Error 3 · `sospechosos()` devolvía un cero sin significado

La función contaba filas con `precio > p99_de_su_categoria * 10`. Devolvía 0, y
**no podía devolver otra cosa**: la razón máx/p99 más alta de las 45 categorías
es 6.29x (pan) y la regla pedía 10x.

Un `0` que sólo puede ser `0` no es una medición: es un adorno, y es peligroso
porque parece decir «no hay precios malos». Ahora la función se llama
`por_que_el_p99_no_sirve()` e imprime el cero **y la razón**.

### Error 4 · `||` con un NULL borraba la fila del conteo

```sql
count(DISTINCT nombre_comercial || '§' || direccion)
```

En SQL, `NULL` no es un valor: es «no sé». Y «no sé» pegado a cualquier cosa
sigue siendo «no sé». Si `direccion` es nulo, la concatenación entera es `NULL`,
y `count(DISTINCT ...)` **no cuenta nulos**. El establecimiento desaparece:

```
 nombre    direccion           con_barras           con_concat
Soriana Av. Juarez 1 Soriana§Av. Juarez 1 Soriana§Av. Juarez 1
Walmart Av. Juarez 2 Walmart§Av. Juarez 2 Walmart§Av. Juarez 2
 Bodega          NaN                  NaN            Bodega§     ← || se lo comió

 establecimientos_barras  establecimientos_concat
                       2                        3
```

Hoy no te afecta porque `direccion` no tiene nulos. Pero tu cifra de 4,334
establecimientos va al informe, y el día que llegue una dirección vacía baja sola
y nadie se entera. `concat()` trata el nulo como cadena vacía.

### Error 5 · `temp_directory` sin configurar

Explicado en el bloque 2.

## Mediciones nuevas que se agregaron

```python
def clave_candidata(con):
    return con.sql("""
        WITH g AS (
            SELECT producto, nombre_comercial, direccion, fecha_registro,
                   count(*) AS n
            FROM qqp GROUP BY ALL
        )
        SELECT count(*) AS combinaciones,
               count(*) FILTER (WHERE n > 1) AS repetidas,
               coalesce(sum(n - 1) FILTER (WHERE n > 1), 0) AS filas_de_mas,
               max(n) AS peor_caso
        FROM g
    """).fetchone()
```

`FILTER (WHERE ...)` es «cuenta/suma sólo las filas que cumplen». Es más limpio
que envolver todo en un `CASE WHEN`.

Esto probó que la clave candidata **no aguanta**: 12.3 millones de filas de más.
Tiene sentido — el mismo establecimiento cotiza el mismo producto en varias
presentaciones el mismo día.

---

# Parte 4 · `perfilado_nivel3.py`, bloque por bloque

## Qué contesta

«¿De cuántas formas distintas está escrita la misma cosa?» De eso depende H3.

## El problema, con peras y manzanas

Nadie te dice que `Acido Fólico` y `Ácido Fólico` son el mismo producto. Hay que
deducirlo. **La idea es de una línea:** si dos textos distintos se reducen al
mismo texto después de quitarles todo lo que no importa, entonces eran el mismo.

Ese texto reducido se llama **clave**. El número de textos originales que caen en
una misma clave es el número de **variantes**.

## Bloque 1 · las dos normalizaciones

```python
SUAVE  = "trim(regexp_replace(lower(strip_accents({0})), '\\s+', ' ', 'g'))"
FUERTE = ("trim(regexp_replace(regexp_replace(lower(strip_accents({0})), "
          "'[^a-z0-9 ]', ' ', 'g'), '\\s+', ' ', 'g'))")
```

De dentro hacia afuera, sobre `'1 Kg.  GRANEL. Hass '`:

| paso | qué hace | resultado |
|---|---|---|
| `strip_accents` | quita acentos | `1 Kg.  GRANEL. Hass ` |
| `lower` | todo a minúsculas | `1 kg.  granel. hass ` |
| `[^a-z0-9 ] → ' '` *(sólo fuerte)* | lo que no sea letra, número o espacio, a espacio | `1 kg   granel  hass ` |
| `\s+ → ' '` | varios espacios seguidos, a uno | `1 kg granel hass ` |
| `trim` | quita espacios de las orillas | `1 kg granel hass` |

`\s+` es «uno o más espacios». La `'g'` del final es «hazlo en todas las
apariciones, no sólo la primera». El `{0}` es un hueco de Python: se rellena con
el nombre de la columna cuando se arma la consulta.

La diferencia entre las dos normalizaciones es **la puntuación**:

```
                literal crudo          clave suave            clave fuerte
           1 Kg. Granel. Hass   1 kg. granel. hass       1 kg granel hass
             1 kg granel hass     1 kg granel hass       1 kg granel hass
          1 Kg. Granel. Hass.  1 kg. granel. hass.       1 kg granel hass
                 Acido Fólico         acido folico           acido folico
                 Ácido Fólico         acido folico           acido folico

literales crudos : 8
claves suaves    : 5
claves fuertes   : 3
```

**Por qué se calculan las dos.** Si sólo diera la fuerte, tendrías que creerte
que quitar la puntuación es la decisión correcta. Dando las dos, la distancia
entre ellas te dice cuánto de tu resultado depende de esa decisión. Es una forma
de no esconder una elección dentro de un número.

## Bloque 2 · la vista

```python
con.sql(f"""
    CREATE VIEW q AS
    SELECT producto, presentacion, marca, categoria, precio,
           (producto LIKE '%?%' OR presentacion LIKE '%?%'
            OR marca LIKE '%?%')                       AS roto,
           {SUAVE.format('producto')}     AS prod_s,
           {FUERTE.format('producto')}    AS prod_f,
           ...
    FROM {fuente}
""")
```

Agrega seis columnas calculadas (dos normalizaciones por cada uno de los tres
campos) y una bandera `roto`. **No copia nada**: es una vista.

`LIKE '%?%'` es «contiene un signo de interrogación». En SQL los comodines de
`LIKE` son `%` y `_`; el `?` es literal.

## Bloque 3 · contar las variantes

Sobre una tabla de juguete de 9 filas. Primero cada fila se reduce a su clave:

```
    producto       presentacion    marca                                  clave
    Aguacate 1 Kg. Granel. Hass      S/m          aguacate§1 kg granel hass§s m
    Aguacate   1 kg granel hass      S/m          aguacate§1 kg granel hass§s m  ← misma
    Aguacate 1 Kg. Granel. Hass      S/m          aguacate§1 kg granel hass§s m
    Aguacate              Pieza      S/m                     aguacate§pieza§s m
Acido Fólico   Caja 30 Tabletas Genérico acido folico§caja 30 tabletas§generico
Ácido Fólico   Caja 30 Tabletas Genérico acido folico§caja 30 tabletas§generico  ← misma
```

El `§` sólo separa: es un carácter que no aparece en los datos, para que `a§bc` y
`ab§c` no se confundan.

Después se agrupa por clave y se cuentan los **literales crudos distintos**:

```sql
SELECT clave, count(*) AS filas,
       count(DISTINCT producto||'§'||presentacion||'§'||marca) AS variantes
FROM qn GROUP BY clave
```

```
                                 clave  filas  variantes
acido folico§caja 30 tabletas§generico      2          2
         aguacate§1 kg granel hass§s m      3          2
                    aguacate§pieza§s m      1          1
```

**Fíjate en la diferencia entre `filas` y `variantes`.** El aguacate tiene 3
filas pero 2 variantes, porque dos de esas filas están escritas idénticas. Lo que
se mide es **de cuántas maneras se escribió**, no cuántas veces apareció.

Y por último se resume:

```
 articulos  literales  media  mediana  maximo  con_mas_de_1
         6          8   1.33      1.0       2             2
```

**9 filas → 6 artículos → media 1.33 variantes.** Ése es todo el cálculo. Con tus
datos es lo mismo con 21 millones: 5,750 artículos, 7,389 literales, media 1.29.

## Bloque 4 · lo otro que mide, que es distinto

```sql
SELECT prod_f,
       count(DISTINCT presentacion) AS crudas,
       count(DISTINCT pres_f)       AS normalizadas
FROM q GROUP BY prod_f
```

```
    producto  presentaciones_crudas  presentaciones_reales
    aguacate                      3                      2
```

El aguacate tiene **3 presentaciones escritas** pero **2 distintas de verdad**.
Esa diferencia —de 3 a 2— es escritura y se arregla normalizando. **Las 2 que
quedan** (`1 Kg. Granel. Hass` y `Pieza`) son productos distintos, y ninguna
normalización las va a juntar.

**Ésa es la distinción que decide H3**, y por eso el guión reporta las dos cosas
por separado. Tu 1.29 es la primera y está holgada. La segunda da media de 6.8
presentaciones por producto con un máximo de 248, y ésa es la que va a la reunión.

## Bloque 5 · con `?` y sin `?`

El guión mide dos veces. El `?` no se normaliza a la letra que se comió, así que
`art?culos` y `articulos` producen **claves distintas**. No inventan variantes de
más: inventan **artículos de más**. En tus datos, 1,215 claves de 6,962 (17.5%)
estaban contaminadas.

---

# Parte 5 · `mojibake.py`

## Qué resuelve

Tres preguntas que quedaron abiertas después del nivel 2 y `diagnostico.py`:

**1 · ¿El `?` está en los datos o lo mete el guión?**
Se responde sola: ninguna de las dos codificaciones puede **fabricar** un `?`.
`utf-8-sig` revienta con error ante un byte inválido —no sustituye en silencio— y
`latin-1` mapea los 256 bytes a un carácter cada uno. Un `?` es el byte `0x3F`:
sólo puede venir del archivo. El guión lo comprueba además leyendo los **bytes
crudos** del CSV, sin pasar por pandas ni por parquet.

**2 · ¿En cuántos archivos, de verdad?**
`diagnostico.py` usaba `GROUP BY`, y un `GROUP BY` **no devuelve renglón para los
grupos vacíos**. Su tabla traía 36 filas y se leyó como «36 archivos afectados».
Los dos que faltaban no habían fallado: **estaban limpios**. Julio de 2026 tiene
cero. `mojibake.py` lista los 38 explícitamente, con los ceros incluidos.

**3 · ¿Es irrecuperable?**
No. Cuando el `?` se comió exactamente una letra, el valor correcto suele seguir
en la misma columna. El guión busca, para cada valor roto, un **gemelo de la
misma longitud** que coincida en todo salvo donde está el `?`:

```python
patron = re.compile("^" + "".join("." if ch == "?" else re.escape(ch)
                                  for ch in v) + "$")
cand = [b for b in por_largo.get(len(v), ()) if patron.match(b)]
```

Cada `?` se convierte en un `.` de expresión regular, que significa «cualquier
carácter». `re.escape` protege lo demás para que un punto real no se vuelva
comodín. `por_largo` agrupa los valores sanos por longitud: como un `?`
sustituye exactamente un carácter, el gemelo mide lo mismo.

Y se clasifica según cuántos gemelos aparecen:

| gemelos encontrados | clase | qué se hace |
|---|---|---|
| exactamente 1 | `reparable` | sustitución determinista |
| 2 o más | `ambiguo` | decidir por frecuencia o a mano |
| 0 | `sin gemelo` | cuarentena |

Resultado en tus datos: **1,650 sustituciones recuperan el 96.82%** de lo
corrupto. Eso cambió la regla CU-03 de «cuarentena para el 3.61% del corpus» a
«reparar, y cuarentena para el 0.36%».

## Los dos CSV que deja, y en qué se diferencian

| archivo | qué trae | para qué sirve |
|---|---|---|
| `mojibake-clasificado.csv` | **todos** los valores rotos, con su clase, sus filas y sus candidatos | auditoría: para poder revisar por qué cada valor cayó donde cayó |
| `mojibake-diccionario.csv` | **sólo los `reparable`**: `columna`, `valor_roto`, `reparado`, `filas` | es el que se **aplica**: entra al pipeline y al contrato de la semana 2 |

El primero es para entender. El segundo es para ejecutar. Se separan porque uno
se lee con los ojos y el otro lo consume una consulta, y mezclar auditoría con
configuración es como acaban los sistemas que nadie entiende.

## Por qué el nivel 2 depende de mojibake, y por qué antes no

**Antes no dependía porque no se sabía qué era el `?`.** El comentario original
del guión lo decía: «el `?` queda sin tocar a propósito hasta ver qué dice
`diagnostico.py` — no adivinar». Era la decisión correcta con la información de
ese momento: reparar sin medir habría sido inventar.

**Ahora depende porque ya está medido.** `categoria` tiene exactamente un valor
roto (`Art?culos Deportivos`, 496 filas) y tiene un gemelo único
(`Artículos Deportivos`). Sin reparar, la tabla del informe sale con las dos
categorías separadas y cada una calcula su p99 con media muestra:

```
| art?culos deportivos | 649.00 | ... | 3999.00 |
| articulos deportivos | 599.00 | ... | 4000.00 |
```

Con el diccionario cargado son **una sola categoría** y las 46 quedan en 45.

El enganche técnico es un `LEFT JOIN`:

```sql
SELECT f.* EXCLUDE (categoria),
       coalesce(r.reparado, f.categoria) AS categoria
FROM fuente f
LEFT JOIN repara r ON r.columna = 'categoria' AND r.valor_roto = f.categoria
```

`LEFT JOIN` es «trae la reparación si existe, y si no, **deja la fila igual**»
(un `JOIN` normal borraría las filas sin pareja, que son 21 millones).
`coalesce(a, b)` es «usa `a`, salvo que sea nulo, y entonces usa `b`».

Y si el diccionario no está, el guión **avisa y sigue sin reparar**. Mejor una
tabla con un aviso que una reparación inventada.

---

# Parte 6 · `centinelas.py`

## Qué resuelve

La regla original de la sección 2 era: *sospechoso si el precio supera 10 veces
el p99 de su categoría*. Devolvió **0**, y el motivo es más interesante que el
resultado: **no podía devolver otra cosa.**

En una distribución de precios el p99 ya está pegado al máximo. La razón máx/p99
más alta de las 45 categorías es **6.29x (pan)**. La regla pedía 10x. Cero de 45
podían dispararla aunque los datos hubieran estado perfectos.

Y hay un segundo problema: **`categoria` es una unidad demasiado gruesa.** Dentro
de «material escolar» conviven un lápiz de $1.15 y unos tenis de $1,999.50 — un
rango de 1,738x en un solo grupo. Un p99 sobre esa mezcla no describe a ningún
producto. La unidad correcta es **`producto`**.

El guión trae tres detectores en lugar de un umbral:

**D1 · precios redondos anormalmente repetidos.** Un precio repdigit (9, 99, 999,
9999) que se repite muchísimo más que los precios vecinos del mismo producto.

**D2 · distribución contaminada.** Productos cuya mediana o cuyo precio más
frecuente ya *es* un número redondo. En ésos ninguna regla de percentil sirve,
porque el valor redondo ayudó a calcular el percentil.

**D3 · atípico por dispersión robusta**, en escala logarítmica y por producto:

```
|ln(p) − mediana(ln p)| / (1.4826 · MAD) > 3.5
```

Logaritmo porque los precios son multiplicativos (duplicarse importa más que
sumar 10 pesos). Mediana y MAD porque **ni la media ni la desviación estándar
sobreviven a los propios atípicos** — un precio de $99,999 arrastra la media
hacia arriba y después «no parece tan raro» comparado con ella. El 1.4826 es una
constante que hace que el MAD sea comparable con una desviación estándar. El 3.5
es el umbral clásico de esa técnica.

Y hay un cuarto resultado que no es un detector: **los productos con MAD = 0**.
MAD cero significa que **más de la mitad de las filas de ese producto tienen el
mismo precio exacto**. El detector no puede dividir entre cero, así que no los
evalúa — los manda a una lista aparte, en vez de callarse.

## Tu pregunta: ¿por qué salían precios con un solo 9?

**Tenías razón en sospechar, y el guión estaba mal.**

La expresión que detecta un número redondo es `^9+\.(00|99)$`, y `9+` significa
«uno o más nueves». Eso incluye `9.00` y `99.00`, no sólo `999.00` y `9999.00`.
Por eso en tu salida aparecían cosas como:

```
producto  precio  veces       n  razon_mediana
 yoghurt     9.0   7562  308147          0.450
 shampoo    99.0   5387  235592          1.076
```

Detectar el `9` y el `99` **no está mal por sí solo** — puede haber un centinela
de $99 en un producto barato. Lo que estaba mal era **llamarles «centinelas
confirmados» sin más**.

El problema de fondo: **repetirse mucho no basta para ser un comodín.** El
comercio mexicano pone precios redondos a propósito. Un yoghurt a $9.00 exacto
aparece 7,562 veces porque **ése es su precio**, no porque nadie supiera cuánto
costaba. Mira la columna `razon_mediana`: 0.450 quiere decir que $9 es menos de
la mitad de la mediana del yoghurt. Es **barato**, no imposible.

Lo que de verdad distingue a un centinela es **dónde cae dentro del rango de su
propio producto**:

- un **punto de precio** cae en medio del rango normal;
- un **centinela** cae en el extremo, porque su función es ser reconociblemente
  imposible para ese producto.

El guión corregido mide dos cosas nuevas:

- **`posicion`** — de las demás cotizaciones de ese producto, qué fracción es más
  barata. 0 = es lo más barato que hay; 1 = es más caro que todo lo demás.
- **`razon_mediana`** — cuántas veces la mediana de su producto.

Y separa la salida en dos clases. Un caso construido a propósito para probarlo:

```
producto  precio  veces  posicion  mediana  razon_mediana           clase
 yoghurt     9.0   1500      0.00    20.53          0.438 punto_de_precio
  nexium   999.0    300      1.00   122.98          8.123 posible_centinela
```

**El mismo patrón de repetición, dos cosas distintas.**

Detalle de implementación que importa: la `posicion` se calcula **excluyendo las
filas del propio valor** del denominador. Si no, un valor muy repetido nunca
podría llegar arriba: sus miles de filas ocupan el extremo y empujan su propio
percentil hacia abajo. Probado con datos hechos a mano: un comodín con el 7% de
las filas se quedaba en 0.93 y parecía «no tan extremo» cuando era más caro que
todo el resto.

## Qué hay que hacer con esto

1. **Vuelve a correr `centinelas.py`.** La corrida del 10/09 clasificaba 157,412
   filas como centinelas y la mayoría eran precios reales.
2. **Mira a mano `centinelas-confirmados.csv`.** Ahora trae sólo los candidatos.
   Un comodín se reconoce porque el precio es absurdo **para ese producto**, y
   eso lo decide una persona, no un percentil.
3. **La regla del contrato es el par (`producto`, `precio`) revisado**, nunca un
   `precio NOT IN (999, 9999)` a ciegas. En «aparatos electricos» el p25 es
   exactamente 999: hay licuadoras y planchas que de verdad cuestan eso.

Los dos archivos que deja:

| archivo | qué trae |
|---|---|
| `precios-redondos-clasificados.csv` | todos los precios redondos repetidos, con su clase |
| `centinelas-confirmados.csv` | sólo los candidatos a comodín — los que van a revisión |

---

# Parte 7 · `variantes-para-revisar.txt`

## De dónde nace

Lo escribe `perfilado_nivel3.py` al final:

```python
grandes = con.sql("""
    SELECT prod_f, count(DISTINCT producto) v FROM q
    GROUP BY prod_f HAVING count(DISTINCT producto) > 1
    ORDER BY v DESC LIMIT 10""").df()
azar = con.sql("""
    SELECT prod_f, count(DISTINCT producto) v FROM q
    GROUP BY prod_f ORDER BY random() LIMIT 10""").df()
```

Toma los grupos con **más variantes** —que es donde estaría el error si lo
hubiera— y unos cuantos **al azar** como control. Para cada uno vuelca todos los
literales crudos con sus filas.

## Qué problema arregla

El número 1.29 sale de **suponer** que la normalización agrupó bien. Si hubiera
juntado dos productos distintos —si `Pasa (uva Pasa)` y `Pasa (Uva Pasa)` fueran
en realidad dos cosas— el número saldría inflado y **no habría manera de saberlo
desde adentro del guión**. Ninguna consulta puede verificar su propia suposición.

La única forma de comprobarlo es que **una persona mire los grupos y diga si son
lo mismo**. Por eso el archivo trae casillas para marcar. No es burocracia: es el
único paso del perfilado que una máquina no puede hacer.

Y en tu caso dio algo mejor que un cero. Los cinco grupos con más variantes
difieren **sólo en mayúsculas o acentos**:

```
clave: acido folico   (2 literal/es)
         7,559  'Acido Fólico'
           373  'Ácido Fólico'
```

Ninguno es una variante semántica, ni un error de dedo, ni una abreviatura
distinta. **La variación de escritura de esta fuente es mecánica**, y eso es lo
que permite decir que una normalización determinista la resuelve entera — sin
comparación difusa y sin riesgo para H3.

---

# Parte 8 · Glosario de lo que aparece en el código

| qué ves | qué significa |
|---|---|
| `df` | un DataFrame: una tabla dentro de la memoria del programa |
| `df["precio"]` | una columna (Series) |
| `df[col].isna()` | columna de verdadero/falso: verdadero donde hay nulo |
| `.sum()` sobre booleanos | los cuenta, porque verdadero vale 1 |
| `.unique()` | los valores distintos de una columna |
| `.value_counts()` | cuántas filas tiene cada valor distinto |
| `pd.to_numeric(s, errors="coerce")` | convierte a número; lo que no puede, lo deja en nulo |
| `chunksize=200_000` | en vez de la tabla entera, devuelve pedazos de 200 mil filas |
| `Path.home() / "x" / "y"` | arma una ruta; el `/` pega pedazos, no divide |
| `path.stem` | el nombre del archivo sin extensión |
| `f"texto {variable}"` | texto con huecos que Python rellena |
| `{}` en Python | un diccionario: clave → valor |
| `set()` | un conjunto: sin orden, sin repetidos, búsqueda instantánea |
| `CREATE VIEW` | una consulta guardada con nombre; no copia datos |
| `read_parquet('*.parquet', union_by_name=true)` | lee muchos parquet como uno; junta por nombre de columna y pone nulo donde falte |
| `GROUP BY ALL` | agrupa por todas las columnas que no son agregados |
| `count(*) FILTER (WHERE ...)` | cuenta sólo las filas que cumplen |
| `coalesce(a, b)` | usa `a`, salvo que sea nulo, y entonces `b` |
| `LEFT JOIN` | trae la pareja si existe; si no, deja la fila igual |
| `strip_accents(x)` | quita acentos. Convierte `ñ` en `n` |
| `quantile_cont(x, 0.99)` | el percentil 99 |
| `SELECT * EXCLUDE (a, b)` | todas las columnas menos ésas |
| `.fetchone()[0]` | el primer valor de la primera fila del resultado |
| `.df()` | convierte un resultado de DuckDB en DataFrame, para imprimirlo |

---

---

# Parte 9 · Los cinco patrones que hay debajo de todo esto

Esto es lo que se repite, y lo que vale la pena llevarse a la siguiente fuente
de datos aunque no vuelvas a ver QQP nunca.

**1 · Una herramienta que «te ayuda» sin avisar es una herramienta que miente.**
`read_csv` convirtiendo `NULL` a nulo, `latin-1` aceptando cualquier byte, `||`
propagando el nulo. Ninguna da error. Las tres te dejan con datos distintos a los
que hay en el archivo. Cuando algo *nunca falla*, sospecha.

**2 · Ausente y vacío no son lo mismo.** Una columna que no existe, una celda
vacía, una celda con la palabra «NULL» y una celda con `S/m` son cuatro
incidentes distintos con cuatro causas distintas. Un guión que los cuenta juntos
te da un número que no sirve para ninguna regla.

**3 · Agregar por la unidad equivocada hace invisible cualquier cosa.** El p99
por `categoria` no encontró nada porque «aparatos electricos» mezcla una plancha
de $181 con un refrigerador de $99,999. Y el mismo error se repitió una planta
más abajo: el termómetro a $999 parecía 10.4 veces anómalo contra su `producto` y
resultó valer 1.00 veces la mediana de **su presentación**. Antes de preguntarte
qué umbral usar, pregúntate sobre qué grupo lo estás calculando.

**4 · `GROUP BY` no devuelve renglón para los grupos vacíos.** La tabla de
mojibake tenía 36 filas y se leyó como «36 archivos afectados». Los dos que
faltaban no habían fallado: estaban limpios. Cuando un resultado tiene menos
renglones de los que esperabas, **la ausencia es el dato**.

**5 · Medir, no inferir.** «pandas dice que es float64» no es un hallazgo.
«3 de 21 millones de celdas no convierten a número» sí lo es. La diferencia es
que lo segundo se puede convertir en una regla del contrato y lo primero no.

**Y un sexto, que salió al final:** *no encontrar nada también es un resultado,
si lo buscaste bien.* Se buscaron valores centinela en `precio` y no hay. Eso no
es una búsqueda fallida: es una compuerta que el contrato no necesita, y 157,412
filas buenas que no se van a tirar.

---

*Las demostraciones ejecutables de todo esto están en `demos-explicativas.py`.
Córrelo cuando algo no te cuadre: son tablas de cinco filas, no de veintiún
millones.*
