# Perfilado de la fuente QQP

<!-- Llenan T003, T004 y T005 (A) · lunes 7, martes 8 y miércoles 9.
     Regla: números, no adjetivos. "Hay bastantes nulos" no sirve;
     "88 nulos, 0.02%" sí. -->

**Archivos perfilado:** QQP_2025 + QQP_2026 (38 archivos, ene 2025–jul 2026)· **Filas totales:** 21,357,873 filas · **Fecha:** 07/SEP/2026

---
## 0 · Objetivo del perfilado de datos

El perfilado de datos consiste en inspeccionar una fuente para saber:

    qué estructura tiene (Estructurada, Semiestructurada o No estructurada),
    qué tipos de datos contiene,
    cuántos valores nulos existen,
    qué tan variados son los valores,
    qué valores parecen imposibles,
    cuáles son posibles anomalías,
    qué registros parecen duplicados,
    y qué características pueden convertirse posteriormente en reglas de calidad de datos.

## 1 · Estructura  <!-- T003, lunes 7 -->

**Volumen:** 21,357,873 filas × 18 columnas
**Rango de fechas:** de 2025/01 a 2026/07 · fechas ilegibles: 0
**Entidades federativas presentes:** 30 Entidades

| Columna | Tipo declarado | Tipo real | % nulos | Valores distintos | Ejemplo |
|---|---|---|---|---|---|
| producto | Carácter (65) | str | 0% | 896 | Acelga |
| presentacion | Carácter (180) | str | 0% | 5,961 | Manojo |
| marca | Carácter (65) | str | 0% | 1,439 | S/m |
| categoria | Carácter (65) | str | 0% | 59 | Hortalizas Frescas |
| catalogo | Carácter (65) | str | 0% | 16 | Frutas y Legumbres |
| precio | Número (18,2) | float64 | 0% | 71,332 | 19.0 |
| fecha_registro | Datetime (8) | str | 0% | 434 | 2025/01/02 |
| cadena_comercial | Carácter (65) | str | 0% | 247 | Central de Abastos |
| giro | Carácter (65) | str | 0% | 21 | Central de Abasto |
| nombre_comercial | Carácter (120) | str | 0% | 2,961 | Central de Abasto |
| direccion | Carácter (255) | str | 0% | 3,641 | Av. Mahatma Gandhi S/n... |
| estado | Carácter (120) | str | 0% | 37 (30 reales) | Aguascalientes |
| municipio | Carácter (120) | str | 0% | 93 | Aguascalientes |
| latitud | Número (18,6) | float64 | 0.0086% | 2,111 | 21.832072 |
| longitud | Número (18,6) | float64 | 0.0086% | 2,113 | -102.292976 |
| folio | *(no está en el diccionario)* | int64 | 0% | 1,853 | 20160 |
| cv_producto | *(no está en el diccionario)* | int64 | 0% | 812 | 869 |
| cv_marca | *(no está en el diccionario)* | int64 | 0% | 486 | 5 |

- - el porcentaje de nulos en folio, cv_productos y cv_marcas es de 0% si solo tomamos en cuenta los .csv que contienen esas 3 columnas (2026_Q1.csv y 06-2026_Q2.csv) pero si contamos todos los archivos realmente es 94.12%

<!-- El "tipo declarado" sale del diccionario de C2. Si difiere del tipo real,
     ese es un hallazgo y una regla del contrato de datos. -->

### PseudoCodigo de perfilado_nivel1.py 
<!--Logica detras de datos/perfilado/perfilado_nivel1.py: script usado para comparar el estado real de las columas en los .csv-->
```bash
para cada carpeta en [QQP_2025, QQP_2026]:
    para cada archivo .csv en la carpeta:
        si el archivo es una de las 2 excepciones de mayo 2026:
            codificación = latin-1, formato_fecha = DD/MM/YYYY
        si no:
            codificación = utf-8-sig, formato_fecha = YYYY/MM/DD

        leer el archivo con esa codificación
        sumar filas al total
        sumar nulos por columna al acumulador
        registrar tipo real por columna (la primera vez que se ve)
        convertir fecha_registro con el formato correcto → actualizar mín/máx global
        agregar los valores de estado al conjunto de entidades vistas

al terminar:
    calcular % de nulos = nulos acumulados / filas totales
    reportar: filas, columnas, tipos, % nulos, rango de fechas, entidades
```

**Discrepancias entre tipo declarado y tipo real:**

- datos.profeco.gob.mx/diccionarioDatosQQP.php no documento todo: el diccionario solo marca 15 columnas del diccionario oficial. El script docs/datos/perfilado/perfilado_nivel1.py encontró 18. Las tres de más — folio, cv_producto, cv_marca — no aparecen en el sitio oficial. 

- - `verificación de perfilado2`: dichas tres columnas sobrantes existen únicamente en `06-2026_Q1` y `06-2026_Q2` (2 de 38 archivos). No es un cambio permanente de esquema: julio ya vuelve a 15 columnas. % de nulos real en esas 3 columnas ≈ 94.7% del total (36 de 38 archivos no las tienen), no 0% como se había anotado.

- - `verificación de perfilado2`: Corrupción de codificación (? reemplazando caracteres): Presente en los 38 archivos al evaluar las 11 columnas de texto. Existe como ruido constante en todo el histórico debido a fallos de acentuación aislados (ej. en municipio o direccion), con una falla sistémica masiva concentrada en junio de 2026.

- - `verificación de perfilado2`: Ambos hallazgos son independientes ya que aunque las 3 columnas extras solo apaerezcan en `06-2026_Q1` y `06-2026_Q2` los errores con ? aparecen en todos los archivos

- `folio` parece ser mas una llave de registro única.

- `fecha_registro` declarado `Datetime`, viene como `str` en dos formatos distintos según el archivo (YYYY/MM/DD y DD/MM/YYYY en mayo 2026).

- `precio` sale `float64`, razonablemente cerca de lo declarado (`Número (18,2)`) — sin discrepancia grave aquí, a diferencia de lo que yo misma había anticipado antes de correr el script.

- - El script en `docs/perfilado/perfilado_nivel1.py` devuelve 37 entidades pero 7 de ellas se repiten y se tomaban como diferente por inconcistencia de acentos (no aparece Colima ni Nayarit en ningún lado de la lista).


**Numero de columnas de cada archivo**
36 archivo(s) con 15 columnas:
 ['01-2025_01.parquet', '01-2025_02.parquet', '01-2026_Q1.parquet', '01-2026_Q2.parquet', '02-2025_01.parquet', '02-2025_02.parquet', '02-2026_Q1.parquet', '02-2026_Q2.parquet', '03-2025_01.parquet', '03-2025_02.parquet', '03-2026_Q1.parquet', '03-2026_Q2.parquet', '04-2025_01.parquet', '04-2025_02.parquet', '04-2026_Q1.parquet', '04-2026_Q2.parquet', '05-2025_01.parquet', '05-2025_02.parquet', '05-2026_Q1.parquet', '05-2026_Q2.parquet', '06-2025_01.parquet', '06-2025_02.parquet', '07-2025_01.parquet', '07-2025_02.parquet', '07-2026_Q1.parquet', '07-2026_Q2.parquet', '08-2025_01.parquet', '08-2025_02.parquet', '09-2025_01.parquet', '09-2025_02.parquet', '10-2025_01.parquet', '10-2025_02.parquet', '11-2025_01.parquet', '11-2025_02.parquet', '12-2025_01.parquet', '12-2025_02.parquet']

2 archivo(s) con 18 columnas: 
['06-2026_Q1.parquet', '06-2026_Q2.parquet']

---

## 2 · Rangos y anomalías  <!-- T004, martes 8 -->

Precios en cero: 0 ( 0.0000 % ) · negativos: 0 · nulos: 0 ( 0.0000% )
Duplicados exactos (excluyendo folio/cv_producto/cv_marca): 301 (0.0014%)
<!-- es decir registros que coinciden en todos los campos menos folio, cv_producto y cv_marca. -->
Establecimientos distintos: (nombre_comercial + dirección, proxy — confirmar con C2): 4334 · cadenas: 243 · municipios: 93

<!-- Categoría normalizada sin acentos (lower + reemplazo de vocales). El '?' de mojibake NO se normalizó a propósito — es corrupción real, no un acento, ver discrepancias abajo. -->

| Categoría (normalizada) | mín | p25 | mediana | p75 | p95 | p99 | máx | sospechosos |
|---|---|---|---|---|---|---|---|---|
| accesorios domesticos | 19.00 | 125.00 | 173.00 | 189.00 | 200.00 | 218.00 | 230.00 | |
| aceites y grasas veg. comestibles | 2.00 | 31.00 | 39.00 | 52.00 | 84.50 | 130.00 | 151.00 | |
| alimentos cocinados f/casa | 69.00 | 125.00 | 135.00 | 139.00 | 159.00 | 178.00 | 179.00 | |
| aparatos electricos | 181.30 | 999.00 | 2799.00 | 10199.00 | 16999.00 | 25599.36 | 99999.00 | ver nota |
| aparatos electronicos | 439.00 | 3199.00 | 5999.00 | 9499.00 | 17499.00 | 27599.00 | 107691.00 | ver nota |
| arroz y cereales preparados | 5.00 | 22.00 | 43.00 | 74.00 | 96.00 | 113.00 | 132.00 | |
| art?culos deportivos | 649.00 | 1999.00 | 1999.00 | 2999.00 | 2999.00 | 3999.00 | 3999.00 | mojibake, ver nota |
| articulos deportivos | 599.00 | 1999.00 | 1999.00 | 2999.00 | 2999.00 | 3999.00 | 4000.00 | mojibake, ver nota |
| arts. de esparcimiento (juguetes) | 84.01 | 449.00 | 799.00 | 6990.00 | 12990.00 | 14899.00 | 20699.00 | |
| arts. de papel p/higiene personal | 6.50 | 32.90 | 45.90 | 100.00 | 339.00 | 435.00 | 545.99 | |
| arts. para el cuidado personal | 3.50 | 41.00 | 75.00 | 115.00 | 687.00 | 1239.00 | 1999.00 | |
| azucar | 17.00 | 25.90 | 30.00 | 53.90 | 186.50 | 271.90 | 319.00 | |
| botanas y bebidas | 5.00 | 30.00 | 44.90 | 59.90 | 76.00 | 110.00 | 118.00 | |
| cafe | 6.60 | 90.50 | 115.00 | 149.00 | 176.00 | 263.00 | 295.00 | |
| carne de ave | 16.61 | 39.90 | 64.90 | 104.90 | 174.00 | 198.00 | 232.00 | |
| carne y visceras de cerdo | 13.01 | 80.00 | 116.00 | 135.00 | 149.99 | 160.00 | 180.00 | |
| carne y visceras de res | 25.00 | 138.00 | 199.00 | 239.00 | 269.99 | 544.00 | 759.90 | |
| carnes frias secas y embutidos | 14.00 | 62.90 | 128.50 | 211.90 | 352.90 | 438.00 | 785.00 | |
| cerveza | 20.50 | 90.00 | 137.00 | 191.00 | 244.00 | 264.00 | 353.00 | |
| chocolates y golosinas | 2.70 | 16.50 | 48.00 | 61.00 | 116.00 | 161.00 | 415.00 | |
| cigarrillos | 15.00 | 25.00 | 27.00 | 27.90 | 28.90 | 29.50 | 30.50 | |
| condimentos | 4.00 | 21.90 | 33.00 | 51.00 | 101.00 | 280.00 | 629.99 | |
| derivados de leche | 3.50 | 25.00 | 50.00 | 96.90 | 260.00 | 328.00 | 428.00 | |
| detergentes y productos similares | 6.50 | 27.50 | 41.00 | 80.00 | 164.00 | 209.90 | 265.00 | |
| enseres menores | 7.00 | 23.00 | 30.00 | 115.00 | 659.50 | 999.00 | 999.00 | |
| frutas frescas | 5.75 | 30.00 | 39.99 | 57.90 | 99.00 | 129.00 | 298.00 | |
| frutas y legumbres procesadas | 5.50 | 16.90 | 28.00 | 42.00 | 72.00 | 80.00 | 98.90 | |
| galletas | 32.90 | 52.00 | 55.00 | 63.60 | 64.90 | 66.90 | 71.90 | |
| galletas pastas y harinas de trigo | 2.50 | 12.00 | 20.00 | 38.00 | 68.00 | 90.90 | 168.00 | |
| grasas animales comestibles | 32.00 | 46.90 | 56.95 | 78.00 | 84.90 | 97.90 | 129.00 | |
| hortalizas frescas | 3.00 | 16.50 | 26.90 | 43.99 | 108.50 | 174.00 | 340.00 | |
| huevo | 18.50 | 42.50 | 49.90 | 60.00 | 91.90 | 98.00 | 114.00 | |
| leche fresca | 20.99 | 28.50 | 30.00 | 32.00 | 36.90 | 84.50 | 94.50 | |
| leche procesada | 7.00 | 26.25 | 34.00 | 39.90 | 210.00 | 288.00 | 320.00 | |
| legumbres secas | 2.00 | 30.00 | 40.00 | 57.00 | 100.00 | 240.00 | 650.00 | |
| material escolar | 1.15 | 30.00 | 58.90 | 108.00 | 250.00 | 426.00 | 1999.50 | |
| medicamentos | 5.00 | 68.90 | 259.00 | 769.00 | 1807.00 | 2731.00 | 5924.86 | |
| pan | 1.20 | 20.50 | 32.00 | 50.00 | 62.00 | 93.00 | 585.00 | |
| pescados y mariscos | 10.30 | 96.00 | 139.00 | 260.00 | 428.90 | 650.00 | 2100.00 | |
| pescados y mariscos en conserva | 8.00 | 17.90 | 20.50 | 35.00 | 48.00 | 279.90 | 674.00 | |
| productos de temporada (navideños) | 6.90 | 36.50 | 72.50 | 180.00 | 299.00 | 460.00 | 978.00 | |
| refrescos envasados | 5.50 | 19.00 | 24.00 | 33.00 | 51.50 | 82.00 | 144.00 | |
| te | 13.50 | 20.50 | 23.00 | 25.00 | 27.00 | 28.00 | 33.00 | |
| tortillas y derivados del maiz | 5.00 | 15.50 | 24.00 | 39.50 | 57.00 | 64.50 | 85.00 | |
| utensilios domesticos | 21.00 | 40.90 | 1329.00 | 1699.00 | 1999.00 | 3599.00 | 3999.00 | |
| vinos y licores | 74.00 | 249.00 | 329.00 | 439.00 | 525.00 | 592.00 | 1089.00 | |

Sospechosos totales (regla automática, >10x el p99 de su categoría): **0**. La columna "sospechosos" por categoría queda vacía porque el script solo calculó el total agregado, no tomarse como "cero en cada categoría", solo como "cero en total con esa regla".

## validacion de centinelas

Un valor centinela es un dato ficticio pero válido en formato (como 999 o 9999) que los capturistas o sistemas usan como comodín para indicar que un precio no estaba disponible, se ignoraba o no se quiso ingresar.

La consulta en DuckDB contó cuántas veces se repiten exactamente esos precios "redondos" por producto y categoría:

- - No son errores aleatorios: Una lavadora a $9,999.00 aparece 4,515 veces; las pantallas a ese mismo precio aparecen  3,669 veces; y las batidoras a $999.00 se repiten 2,044 veces.

```text
┌─────────────────────────┬───────────────────────────────────────┬────────┬───────┐
│        categoria        │               producto                │ precio │ veces │
│         varchar         │                varchar                │ double │ int64 │
├─────────────────────────┼───────────────────────────────────────┼────────┼───────┤
│ Aparatos Electricos     │ Lavadoras                             │ 9999.0 │  4515 │
│ Aparatos Electronicos   │ Pantallas                             │ 9999.0 │  3669 │
│ Aparatos Electricos     │ Estufas                               │ 9999.0 │  2541 │
│ Aparatos Electricos     │ Batidoras                             │  999.0 │  2044 │
│ Aparatos Electricos     │ Licuadoras                            │  999.0 │  1724 │
│ Aparatos Electricos     │ Planchas                              │  999.0 │  1664 │
│ Aparatos Electricos     │ Extractores de Jugos y Exprimidores   │  999.0 │  1233 │
│ Aparatos Electronicos   │ Bocinas Portátiles                    │ 9999.0 │  1164 │
│ Aparatos Electricos     │ Refrigeradores                        │ 9999.0 │  1132 │
│ Medicamentos            │ Pulmonarom                            │  999.0 │   901 │
│            .            │                   .                   │      . │     . │
│            .            │                   .                   │      . │     . │
│            .            │                   .                   │      . │     . │
│ Aparatos Electrónicos   │ Tablet                                │  999.0 │     1 │
│ Medicamentos            │ Seloken Zok                           │  999.0 │     1 │
│ Medicamentos            │ Tafirol Flex                          │  999.0 │     1 │
│ Aparatos Electricos     │ Lavadoras                             │99999.0 │     1 │
│ Medicamentos            │ Competact                             │  999.0 │     1 │
│ Medicamentos            │ Vasculflow                            │  999.0 │     1 │
│ Aparatos Electronicos   │ C?maras Digitales                     │ 9999.0 │     1 │
│ Medicamentos            │ Sermion                               │  999.0 │     1 │
│ Medicamentos            │ Travatan                              │  999.0 │     1 │
│ Medicamentos            │ Nexium                                │  999.0 │     1 │
└─────────────────────────┴───────────────────────────────────────┴────────┴───────┘
135 rows (20 shown)                                                      4 columns
```
- - ¿porque entonces tenemos 0 errores en precio?
Por qué la regla del 10x p99 es una fórmula estadística que busca "raros aislados" (como un frijol de $800). Al haber miles de lavadoras y pantallas registradas a $9,999.00, el valor infló la distribución o se integró en ella. Como el percentil 99 quedó altísimo, pedir que un valor superara 10 veces ese percentil volvió la regla inalcanzable.

**Reglas de contrato que se derivan de esto:**

<!-- Cada anomalía medida se convierte en una regla del contrato de la semana 2. -->

- `precio > 0`

- Excluir precios centinela precio NOT IN (999, 9999, 99999). La validación confirmó que estos valores se repiten miles de veces como comodines de los capturistas (ej. en Aparatos Eléctricos/Electrónicos), no son precios reales del mercado y deben filtrarse para no romper los promedios estadísticos

- **Clave de unicidad (candidata, sin confirmar):** (`producto`, `nombre_comercial`, `direccion`, `fecha_registro`)

---

## 3 · Variantes de escritura  <!-- T005, miércoles 9 · decide H3 -->

Variantes promedio por producto: ______ · mediana: ______ · máximo: ______
Productos con más de 10 variantes: ______ de ______ ( ___% )

- `folio`, `cv_producto`, `cv_marca` y la corrupción de codificación (ver abajo) coinciden en las mismas dos quincenas — **junio 2026 es un evento acotado**, no un problema del año completo.

- El criterio de limpieza para precios: Los precios anómalos o de control se filtrarán explícitamente mediante reglas deterministas (por ejemplo, excluyendo los centinelas exactos que DuckDB ya permitió medir) en lugar de depender de un umbral de percentiles dinámicos.
  
- El `?` es corrupción de codificación irrecuperable confirmada en las 11 columnas de texto libres (incluyendo direccion, municipio, estado, presentacion) a través de todos los archivos. (no es acento, es un carácter perdido en el origen — ej. `Jab?n`, `Kellogg?s`). Afecta `producto`, `marca`, `nombre_comercial`, `categoria`, etc. 
No afecta `precio` ni `fecha_registro`. 

- Lista de registros afectados por '?' segun columna (aplicado a los 38 archivos)
    producto: 163,837 filas con '?' (75 valores distintos)
    presentacion: 236,062 filas con '?' (636 valores distintos)
    marca: 66,526 filas con '?' (99 valores distintos)
    categoria: 496 filas con '?' (1 valores distintos)
    giro: 46,336 filas con '?' (5 valores distintos)
    nombre_comercial: 61,577 filas con '?' (612 valores distintos)
    direccion: 147,379 filas con '?' (289 valores distintos)
    municipio: 401,781 filas con '?' (21 valores distintos)

- `categoria` tiene el mismo problema de acentos inconsistentes que `estado` (Sección 1): `Aparatos Electricos`/`Eléctricos` y `Electronicos`/`Electrónicos` eran 4 filas antes de normalizar, ahora 2. `art?culos deportivos`/`articulos deportivos` siguen separadas porque el `?` no es un acento — es el mismo problema de junio, no otro nuevo.

- Candidato fuerte para la regla de cuarentena (CU-03): Enviar a cuarentena cualquier registro que contenga ? en columnas analíticas clave (como producto o municipio), sin importar a qué mes pertenezca, para evitar que la agrupación falle


<!-- Veinte productos comunes. Revisa diez grupos a mano antes de confiar en
     la cifra: si la normalización juntó productos distintos, está inflada. -->

**Verificación manual:** revisé ______ grupos. Agrupamientos incorrectos: ______

### Qué implica para H3

<!-- Guía de lectura:
     1 a 3 variantes  → la fuente ya viene normalizada. 85% es cómodo
     4 a 8 variantes  → normal. 85% alcanzable con comparación difusa
     más de 10        → hay que bajar la meta o acotar el recorte, y decirlo el lunes -->
