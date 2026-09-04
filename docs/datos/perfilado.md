# Perfilado de la fuente QQP

<!-- Llenan T003, T004 y T005 (A) · jueves 3 y viernes 4.
     Regla: números, no adjetivos. "Hay bastantes nulos" no sirve;
     "88 nulos, 0.02%" sí. -->

**Archivo perfilado:** _______ · **Filas totales:** _______ · **Fecha:** _______

---

## 1 · Estructura  <!-- T003, jueves 3 -->

**Volumen:** ______ filas × ______ columnas
**Rango de fechas:** de ______ a ______ · fechas ilegibles: ______
**Entidades federativas presentes:** ______

| Columna | Tipo declarado | Tipo real | % nulos | Valores distintos | Ejemplo |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

<!-- El "tipo declarado" sale del diccionario de C2. Si difiere del tipo real,
     ese es un hallazgo y una regla del contrato de datos. -->

**Discrepancias entre tipo declarado y tipo real:**

- 

---

## 2 · Rangos y anomalías  <!-- T004, viernes 4 -->

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

## 3 · Variantes de escritura  <!-- T005, viernes 4 · decide H3 -->

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

