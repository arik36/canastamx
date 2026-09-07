# Perfilado de la fuente QQP

<!-- Llenan T003, T004 y T005 (A) · lunes 7, martes 8 y miércoles 9.
     Regla: números, no adjetivos. "Hay bastantes nulos" no sirve;
     "88 nulos, 0.02%" sí. -->

**Archivos perfilado:** QQP_2025 + QQP_2026 (38 archivos, ene 2025–jul 2026)· **Filas totales:** 21,357,873 filas · **Fecha:** 07/SEP/2026

---

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

- `folio` parece ser mas una llave de registro única.

- `fecha_registro` (declarado `Datetime`, viene como `str` en dos formatos). 

- `precio` sale `float64`, razonablemente cerca de lo declarado (`Número (18,2)`) — sin discrepancia grave aquí, a diferencia de lo que yo misma había anticipado antes de correr el script.

- El script en `docs/perfilado/perfilado_nivel1.py` devuelve 37 entidades pero 7 de ellas se repiten (no aparece Colima ni Nayarit en ningún lado de la lista).
---

## 2 · Rangos y anomalías  <!-- T004, martes 8 -->

Precios en cero: ______ ( ___% ) · negativos: ______ · nulos: ______ ( ___% )
Duplicados exactos: ______ ( ___% )
Establecimientos distintos: ______ · cadenas: ______ · municipios: ______

<!-- Los percentiles van POR CATEGORÍA. Un umbral global marca como anómalo
     todo lo caro y deja pasar todo lo barato mal capturado. -->

| Categoría | mín | p25 | mediana | p75 | p95 | p99 | máx | sospechosos |
|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |

**Reglas de contrato que se derivan de esto:**

<!-- Cada anomalía medida se convierte en una regla del contrato de la semana 2. -->

- `precio > 0`
- 
- **Clave de unicidad:** ( ______ , ______ , ______ )

---

## 3 · Variantes de escritura  <!-- T005, miércoles 9 · decide H3 -->

Variantes promedio por producto: ______ · mediana: ______ · máximo: ______
Productos con más de 10 variantes: ______ de ______ ( ___% )

| Producto (normalizado) | Variantes | Cadenas | Ejemplos |
|---|---|---|---|
|  |  |  |  |

<!-- Veinte productos comunes. Revisa diez grupos a mano antes de confiar en
     la cifra: si la normalización juntó productos distintos, está inflada. -->

**Verificación manual:** revisé ______ grupos. Agrupamientos incorrectos: ______

### Qué implica para H3

<!-- Guía de lectura:
     1 a 3 variantes  → la fuente ya viene normalizada. 85% es cómodo
     4 a 8 variantes  → normal. 85% alcanzable con comparación difusa
     más de 10        → hay que bajar la meta o acotar el recorte, y decirlo el lunes -->
