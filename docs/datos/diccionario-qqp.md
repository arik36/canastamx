# Diccionario de datos · QQP

<!-- C2 (Renato) · T013. Elaborado con el enlace proporcionado por A en T002 y los cuatro ZIP compartidos. -->

**Fuente del diccionario:** [Diccionario oficial de PROFECO](https://datos.profeco.gob.mx/diccionarioDatosQQP.php) · **Consultado el:** 8 de septiembre de 2026.
**Contrastado contra:** encabezado equivalente a `head -1` de `QQP_2025/01-2025_01.csv`, identificado por A, y de los otros 37 CSV de los cuatro ZIP compartidos, el 8 de septiembre de 2026.

**Hallazgo principal:** el diccionario oficial describe 15 columnas. Hay 36 CSV con esas 15 columnas y 2 con 18: las dos piezas de junio de 2026 agregan `folio`, `cv_producto` y `cv_marca`. Julio vuelve a tener 15 columnas. Los significados de los tres campos adicionales no aparecen en la fuente proporcionada y se marcan con `?`.

Encabezado literal de 2025, enero–mayo de 2026 y julio de 2026, después de retirar únicamente el BOM cuando existe:

```text
producto,presentacion,marca,categoria,catalogo,precio,fecha_registro,cadena_comercial,giro,nombre_comercial,direccion,estado,municipio,latitud,longitud
```

Encabezado literal de las dos quincenas de junio de 2026, después de retirar únicamente el BOM:

```text
producto,presentacion,marca,categoria,catalogo,precio,fecha_registro,cadena_comercial,giro,nombre_comercial,direccion,estado,municipio,latitud,longitud,folio,cv_producto,cv_marca
```

**Alcance comprobado:** 21,357,873 registros, sin contar encabezados. Se leyeron completos los 38 CSV desde los ZIP, sin extraer los datos al repositorio. Las primeras 15 columnas conservan el mismo nombre y orden en todos ellos.

| ZIP compartido | CSV | Registros |
|---|---:|---:|
| `QQP_2025-20260908T210451Z-1-001.zip` | 14 | 7,059,729 |
| `QQP_2025-20260908T210451Z-1-002.zip` | 10 | 6,210,795 |
| `QQP_2026-20260908T210501Z-1-001.zip` | 12 | 6,710,178 |
| `QQP_2026-20260908T210501Z-1-002.zip` | 2 | 1,377,171 |

| Conjunto | CSV | Registros | Fechas observadas |
|---|---:|---:|---|
| 2025 | 24 | 13,270,524 | 2025-01-02 a 2025-12-31 |
| 2026 | 14 | 8,087,349 | 2026-01-02 a 2026-07-31 |

---

## Columnas

Los tipos y tamaños entre paréntesis proceden del diccionario oficial. El CSV almacena representaciones de texto: esos tipos describen cómo interpretar cada campo, no un esquema ya aplicado al archivo.

**¿Nulos?** El diccionario consultado no declara su admisibilidad. Se cuentan por separado los campos vacíos (`""`) y los que contienen únicamente espacios en los 38 CSV. Cero casos observados no establece una regla `NOT NULL`. Los marcadores textuales no se convierten automáticamente en nulos.

Los ejemplos de las primeras 15 columnas proceden del primer registro de `QQP_2025/01-2025_01.csv`; los tres campos adicionales, del primer registro de `QQP_2026/06-2026_Q1.csv`. «Máx.» indica longitud máxima observada en caracteres. Para las columnas adicionales se evalúan solo los dos CSV que las contienen: ausencia de columna y celda vacía son situaciones distintas.

| Columna | Tipo | Significado | Ejemplo | ¿Nulos? | Notas |
|---|---|---|---|---|---|
| `producto` | Texto (65) | Qué producto se cotizó. | `Acelga` | No especificado; 0 vacíos y 0 solo espacios. | Oficial: `PRODUCTO`. Máx. observado: 44. `cv_producto` solo aparece en junio de 2026; falta confirmar su significado. |
| `presentacion` | Texto (180) | Cómo se presenta el producto. | `Manojo` | No especificado; 0 vacíos y 0 solo espacios. | Oficial: `PRESENTACIÓN`. Máx. observado: 140. Conservar el texto literal al comparar tamaños o cantidades. |
| `marca` | Texto (65) | Marca del producto. | `S/m` | No especificado; 0 vacíos y 0 solo espacios. | Oficial: `MARCA`. Máx. observado: 49. `S/m` y `S/M` se conservan como texto; A los interpreta como sin marca. Ver duda 3. |
| `categoria` | Texto (65) | Categoría del producto. | `Hortalizas Frescas` | No especificado; 0 vacíos y 0 solo espacios. | Oficial: `CATEGORÍA`. Máx. observado: 34. Valores observados en la sección siguiente. |
| `catalogo` | Texto (65) | Catálogo del producto. ? Falta precisar el criterio de agrupación. | `Frutas y Legumbres` | No especificado; 0 vacíos y 0 solo espacios. | Oficial: `CATÁLOGO`. Máx. observado: 19. Es una columna distinta de `categoria`; ver duda 1. |
| `precio` | Decimal (18,2) | Precio de venta al público. | `19` | No especificado; 0 vacíos y 0 solo espacios. | Oficial: `PRECIO`. Moneda, impuestos, descuentos y base de comparación: ver duda 4. |
| `fecha_registro` | Fecha; oficial: Datetime (8) | Fecha de captura del precio en el establecimiento. | `2025/01/02` | No especificado; 0 vacíos y 0 solo espacios. | Oficial: `FECHAREGISTRO`. Texto `YYYY/MM/DD`; en mayo de 2026, `DD/MM/YYYY`. No trae hora. |
| `cadena_comercial` | Texto (65) | Cadena que agrupa sucursales de una misma marca comercial. | `Central de Abastos` | No especificado; 0 vacíos y 0 solo espacios. | Oficial: `CADENACOMERCIAL`. Máx. observado: 39. No usar la cadena como identificador de una sucursal. |
| `giro` | Texto (65) | Actividad comercial del establecimiento. | `Central de Abasto` | No especificado; 0 vacíos y 0 solo espacios. | Oficial: `GIRO`. Máx. observado: 37. Corresponde a «tipos de establecimiento» en esta plantilla. |
| `nombre_comercial` | Texto (120) | Nombre comercial ligado a la razón social. ? Identificación de sucursal por aclarar. | `Central de Abasto` | No especificado; 0 vacíos y 0 solo espacios. | Oficial: `NOMBRECOMERCIAL`. Máx. observado: 64. No asumir unicidad; ver duda 2. |
| `direccion` | Texto (255) | Domicilio del establecimiento. | `Av. Mahatma Gandhi S/n. Salida a México. Col. Central de Abasto. Cp. 20280` | No especificado; 0 vacíos y 0 solo espacios. | Oficial: `DIRECCIÓN`. Máx. observado: 166. Conservar acentos y puntuación. No hay columna independiente de código postal. |
| `estado` | Texto (120) | Entidad donde está el establecimiento. | `Aguascalientes` | No especificado; 0 vacíos y 0 solo espacios. | Oficial: `ESTADO`. Máx. observado: 19. Conservar las grafías del CSV, por ejemplo `Ciudad de Mexico`. |
| `municipio` | Texto (120) | Municipio o demarcación del establecimiento. | `Aguascalientes` | No especificado; 0 vacíos y 0 solo espacios. | Oficial: `MUNICIPIO`. Máx. observado: 24. No hay clave territorial explícita en el encabezado. |
| `latitud` | Decimal (18,6) | Posición respecto al ecuador, en grados decimales. | `21.832072` | No especificado; 1,829 vacíos y 0 solo espacios. | Oficial: `LATITUD`. Sistema de referencia geográfica por confirmar; ver duda 6. |
| `longitud` | Decimal (18,6) | Posición respecto al meridiano cero, en grados decimales. | `-102.292976` | No especificado; 1,829 vacíos y 0 solo espacios. | Oficial: `LONGITUD`. Conservar el signo del número; ver duda 6. |
| `folio` | No especificado; conservar como texto hasta acordar el contrato. | ? No se define qué entidad identifica ni su alcance. | `20160` | No especificado; 0 vacíos y 0 solo espacios en los 2 CSV con el campo; ausente en 36 CSV. | No aparece en el diccionario. Máx. observado: 5. No asumir unicidad ni convertir en clave primaria. Ver duda 8. |
| `cv_producto` | No especificado; conservar como texto hasta acordar el contrato. | ? El nombre sugiere una clave de producto; falta definición oficial y alcance. | `869` | No especificado; 0 vacíos y 0 solo espacios en los 2 CSV con el campo; ausente en 36 CSV. | No aparece en el diccionario. Máx. observado: 4. No asumir unicidad ni convertir en clave primaria. Ver duda 8. |
| `cv_marca` | No especificado; conservar como texto hasta acordar el contrato. | ? El nombre sugiere una clave de marca; falta definición oficial y alcance. | `5` | No especificado; 0 vacíos y 0 solo espacios en los 2 CSV con el campo; ausente en 36 CSV. | No aparece en el diccionario. Máx. observado: 3. No asumir unicidad ni convertir en clave primaria. Ver duda 8. |

---

## Valores de las columnas categóricas

Listas de valores distintos calculadas con todos los registros de 2025 y enero–julio de 2026. Equivalen a la unión de `unique()` de cada CSV, ordenada para consulta. Se preservan mayúsculas, acentos, abreviaturas y espacios. Son valores observados en estos archivos; su uso como lista cerrada del contrato requiere acuerdo de A.

**Entidades federativas:** columna `estado` · 37 valores literales.

```text
Aguascalientes
Baja California
Baja California Sur
Campeche
Chiapas
Chihuahua
Ciudad de Mexico
Ciudad de México
Coahuila
Durango
Estado de Mexico
Estado de México
Guanajuato
Guerrero
Hidalgo
Jalisco
Michoacan
Michoacán
Morelos
Nuevo Leon
Nuevo León
Oaxaca
Puebla
Queretaro
Querétaro
Quintana Roo
San Luis Potosi
San Luis Potosí
Sinaloa
Sonora
Tabasco
Tamaulipas
Tlaxcala
Veracruz
Yucatan
Yucatán
Zacatecas
```

**Categorías de producto:** columna `categoria` · 59 valores literales.

```text
Accesorios Domesticos
Accesorios Domésticos
Aceites y Grasas Veg. Comestibles
Alimentos Cocinados F/casa
Aparatos Electricos
Aparatos Electronicos
Aparatos Electrónicos
Aparatos Eléctricos
Arroz y Cereales Preparados
Art?culos Deportivos
Arts. de Esparcimiento (Juguetes)
Arts. de Esparcimiento (juguetes)
Arts. de Papel P/higiene Personal
Arts. para el Cuidado Personal
Artículos Deportivos
Azucar
Azúcar
Botanas y Bebidas
Cafe
Café
Carne de Ave
Carne y Visceras de Cerdo
Carne y Visceras de Res
Carne y Vísceras de Cerdo
Carne y Vísceras de Res
Carnes Frias Secas y Embutidos
Carnes Frías Secas y Embutidos
Cerveza
Chocolates y Golosinas
Cigarrillos
Condimentos
Derivados de Leche
Detergentes y Productos Similares
Enseres Menores
Frutas Frescas
Frutas y Legumbres Procesadas
Galletas
Galletas Pastas y Harinas de Trigo
Grasas Animales Comestibles
Hortalizas Frescas
Huevo
Leche Fresca
Leche Procesada
Legumbres Secas
Material Escolar
Medicamentos
Pan
Pescados y Mariscos
Pescados y Mariscos en Conserva
Productos de Temporada (Navideños)
Productos de Temporada (navideños)
Refrescos Envasados
Te
Tortillas y Derivados del Maiz
Tortillas y Derivados del Maíz
Té
Utensilios Domesticos
Utensilios Domésticos
Vinos y Licores
```

**Tipos de establecimiento:** columna `giro` · 21 valores literales.

```text
Central de Abasto
Farmacias
Jugueter?as
Jugueterías
Mercados
Panader?as
Panaderías
Papeler?as
Papelerías
Pescader?as
Pescaderías
Supermercado / Tienda de Autoservicio
Tienda Departamentales
Tienda de Conveniencia
Tienda de Electrodomésticos
Tiendas Departamentales
Tortiller?as
Tortillerías
Uniformes
Vinaterías
Zapaterías
```

**Catálogos de producto:** columna `catalogo` · 16 valores literales.

```text
Basicos
Básicos
Electrodomesticos
Electrodomésticos
Especial
Frutas y Legumbres
Juguetes
Medicamentos
Mercados
Navideños
PACIC
Pacic
Pescados y Mariscos
Tenis
Utiles Escolares
Útiles Escolares
```

**Cuidado con las variantes:** `Ciudad de Mexico` y `Ciudad de México` son valores literales distintos. El número de valores de `estado` no equivale al número de entidades geográficas. También se conservan `Tienda Departamentales` y `Tiendas Departamentales` en `giro`; su unificación corresponde a la normalización que acuerde A.

**Signos `?` dentro de los valores:** `Art?culos Deportivos`, `Jugueter?as`, `Panader?as`, `Papeler?as`, `Pescader?as` y `Tortiller?as` aparecen así en los datos. Esos signos son contenido literal del CSV; las marcas `?` en la columna «Significado» señalan dudas de este documento. No se sustituyeron automáticamente por letras acentuadas.

**Variaciones entre años:**

| Columna | Solo en los archivos de 2025 | Solo en los archivos de 2026 |
|---|---|---|
| `estado` | `Ciudad de Mexico`, `Estado de Mexico`, `Michoacan`, `Nuevo Leon`, `Queretaro`, `San Luis Potosi`, `Yucatan` | Ninguno |
| `categoria` | `Enseres Menores` | `Art?culos Deportivos`, `Arts. de Esparcimiento (Juguetes)`, `Artículos Deportivos`, `Botanas y Bebidas`, `Productos de Temporada (Navideños)` |
| `giro` | `Vinaterías` | `Jugueter?as`, `Panader?as`, `Papeler?as`, `Pescader?as`, `Tortiller?as` |
| `catalogo` | Ninguno | `Básicos`, `Electrodomésticos`, `PACIC`, `Útiles Escolares` |

---

## Discrepancias entre el diccionario y el archivo real

| Qué dice el diccionario | Qué trae el archivo | Impacto |
|---|---|---|
| Describe 15 columnas. | 36 CSV contienen las 15 equivalentes; `06-2026_Q1.csv` y `06-2026_Q2.csv` agregan `folio`, `cv_producto` y `cv_marca`, para un total de 18. Las dos piezas de julio regresan a 15. | El encabezado de enero que se muestra en T002 no representa todos los archivos. El contrato debe acordar cómo manejar ambas estructuras; no descartar ni interpretar los tres campos sin confirmar su significado. |
| Nombres en mayúsculas; algunos con acentos o palabras unidas. | Nombres en minúsculas, sin acentos y con guiones bajos en `fecha_registro`, `cadena_comercial` y `nombre_comercial`. La equivalencia completa está en las notas de cada fila. | El contrato debe usar los nombres literales del CSV. Convertir solo a minúsculas no resuelve todas las diferencias. |
| No especifica codificación ni BOM. | 36 CSV tienen BOM y se leen como UTF-8 con `utf-8-sig`. Las dos piezas de mayo de 2026 se leen con `latin-1`, según T002, y no tienen BOM. | Leer el conjunto con una única codificación puede fallar o alterar acentos. El BOM es una marca de codificación, no un espacio ni parte del nombre `producto`. |
| Declara `Datetime (8)` sin patrón de serialización. | Fechas de 10 caracteres y sin hora: `YYYY/MM/DD` en 36 CSV y `DD/MM/YYYY` en las dos piezas de mayo de 2026. | Definir el formato por archivo evita intercambiar día y mes; el `(8)` oficial no debe interpretarse como longitud de la cadena del CSV. |
| No enumera valores permitidos ni establece reglas de nulos. | Las listas anteriores y los conteos de vacíos se obtuvieron del archivo. Hay variantes textuales entre años. | Separar observación de regla: A debe acordar normalización, tratamiento de faltantes y futuras categorías. |
| Describe campos de texto sin reglas para caracteres alterados. | En `05-2026_Q2.csv` y las dos piezas de junio aparecen valores categóricos con `?` literal, como `Papeler?as`; en junio también aparece `Art?culos Deportivos`. | Una lectura con la codificación seleccionada conserva esos signos. Registrar la anomalía y acordar su tratamiento antes de agrupar categorías. |
| Establece tamaños para los campos de texto. | Ninguna longitud máxima observada supera el tamaño oficial de su campo. | No se detectó discrepancia de longitud en las columnas de texto del conjunto revisado. |

**Detalle comprobado de la excepción de mayo de 2026:**

| Archivo | Registros | Formato de fecha en todos sus registros | Lectura |
|---|---:|---|---|
| `QQP_2026/05-2026_Q1.csv` | 479,993 | `DD/MM/YYYY` | `latin-1`, sin BOM |
| `QQP_2026/05-2026_Q2.csv` | 527,089 | `DD/MM/YYYY` | `latin-1`, sin BOM |

**Marcas textuales:**

- `marca`: `S/M` en 3,056,111 registros; `S/m` en 4,294,517 registros.

Se buscaron literalmente `NULL`, `null`, `NA`, `N/A`, `NaN`, `nan`, `S/m` y `S/M`. Esta comprobación no determina el significado de cada marcador ni agota otras maneras de representar faltantes.

**Método de contraste:** lectura completa por bloques con separador coma, tratamiento CSV de comillas, codificación explícita y conversión automática de nulos desactivada (`dtype=str`, `keep_default_na=False`, `na_filter=False`). Se compararon encabezados, contaron registros, vacíos y espacios, midieron longitudes y reunieron valores distintos. Se comprobaron las fechas con el patrón correspondiente y la conversión numérica de `precio`, `latitud` y `longitud`. Las listas conservan los valores originales; no se normalizaron ni corrigieron los datos.

**Archivos con campos vacíos o solo espacios:**

| Archivo | Columna | Vacíos | Solo espacios |
|---|---|---:|---:|
| `QQP_2026/04-2026_Q2.csv` | `latitud` | 163 | 0 |
| `QQP_2026/04-2026_Q2.csv` | `longitud` | 163 | 0 |
| `QQP_2026/05-2026_Q1.csv` | `latitud` | 323 | 0 |
| `QQP_2026/05-2026_Q1.csv` | `longitud` | 323 | 0 |
| `QQP_2026/05-2026_Q2.csv` | `latitud` | 305 | 0 |
| `QQP_2026/05-2026_Q2.csv` | `longitud` | 305 | 0 |
| `QQP_2026/06-2026_Q1.csv` | `latitud` | 325 | 0 |
| `QQP_2026/06-2026_Q1.csv` | `longitud` | 325 | 0 |
| `QQP_2026/06-2026_Q2.csv` | `latitud` | 320 | 0 |
| `QQP_2026/06-2026_Q2.csv` | `longitud` | 320 | 0 |
| `QQP_2026/07-2026_Q1.csv` | `latitud` | 235 | 0 |
| `QQP_2026/07-2026_Q1.csv` | `longitud` | 235 | 0 |
| `QQP_2026/07-2026_Q2.csv` | `latitud` | 158 | 0 |
| `QQP_2026/07-2026_Q2.csv` | `longitud` | 158 | 0 |

---

## Dudas para la reunión del lunes

Seguimiento previsto en T018: viernes 11 de septiembre de 2026. Se conserva el encabezado de la plantilla.

1. **`catalogo` (?) y `categoria`:** ¿qué criterio distingue las dos agrupaciones y existe una relación oficial entre ellas? ¿Cómo se interpretan los catálogos `Pacic` y `Basicos`?
2. **`nombre_comercial` (?):** ¿permite distinguir una sucursal? Si no, ¿qué combinación de cadena, nombre, dirección y coordenadas usará A para identificar establecimientos? ¿Tiene relación con `folio`, disponible solo en junio de 2026?
3. **`marca`:** ¿A confirma que `S/m` y `S/M` representan «sin marca»? ¿Se conservarán, unificarán o tratarán como faltantes? La equivalencia se señala en T002, pero el diccionario no la define.
4. **`precio`:** ¿en qué moneda se expresa, incluye impuestos y promociones, y corresponde siempre a la presentación descrita? ¿Qué regla permite comparar presentaciones distintas?
5. **Nulos y categorías:** ¿qué campos serán obligatorios y qué ocurrirá con valores nuevos o variantes ortográficas? Los valores y conteos observados aquí no bastan para definir por sí solos esas reglas.
6. **Coordenadas:** ¿cuál es el sistema de referencia geográfica y cómo se tratarán coordenadas ausentes, fuera de rango o que no correspondan al establecimiento?
7. **Fechas:** la fuente sí establece que `fecha_registro` es la fecha de captura. ¿Qué vigencia se mostrará al usuario y cómo se distinguirá esa fecha de la publicación o descarga del lote?
8. **`folio`, `cv_producto` y `cv_marca` (?):** ¿A puede proporcionar la documentación oficial de estos campos? ¿Qué identifican, en qué ámbito son únicos y son estables entre quincenas? ¿Por qué aparecen en junio y no en julio? ¿Qué estructura admitirá el contrato para los 36 CSV que no los incluyen?
