# ADR 005 · Recorte de productos por catálogo

- **Fecha:** 14 de septiembre de 2026
- **Estado:** propuesta — A la lleva a la reunión del **miércoles 16** para
  ratificarla o enmendarla con el equipo. No se marca «aceptada» hasta entonces.
- **Participantes:** Ariadne (A) — autora de la propuesta. Ari Adair (B),
  Liseth (C1), Oscar (C2), Karen (D) — deciden el miércoles 16.

## Contexto

El ADR 001 dejó abierto el tercer recorte que compromete el protocolo —el de
productos— con esta nota: *«la decisión está casi tomada por la fuente: el
protocolo dice "conforme a la clasificación de productos de consumo
generalizado de la fuente", y esa clasificación es la columna `catalogo`»*.

No es un tecnicismo. El corpus, sin recorte de productos, trae 896 productos
que incluyen celulares, lavadoras, tenis y pantallas de televisión junto con el
kilo de tortilla. El proyecto se llama *plataforma de inteligencia de precios
de **canasta básica*** — hoy, sin este recorte, «canasta básica» no significa
nada en el dato.

**La columna trae 16 literales que son en realidad 12 catálogos**, porque la
fuente escribe cuatro de ellos de dos maneras (`Basicos`/`Básicos`,
`Electrodomesticos`/`Electrodomésticos`, `Utiles Escolares`/`Útiles
Escolares`, `Pacic`/`PACIC`). Medido sobre el recorte de siete entidades
(`medir-decisiones.py`, 12 de septiembre):

| catálogo | filas | precio mediano | precio máximo |
|---|---:|---:|---:|
| Basicos | 2,105,019 | $45 | $770 |
| Medicamentos | 1,241,581 | $245 | $5,891 |
| Electrodomesticos | 288,757 | $4,699 | $83,997 |
| Frutas y Legumbres | 237,440 | $38 | $498 |
| Pacic | 169,083 | $27 | $299 |
| Utiles Escolares | 139,830 | $60 | $19,999 |
| Mercados | 104,409 | $50 | $850 |
| Pescados y Mariscos | 42,955 | $153 | $1,775 |
| Juguetes | 35,512 | $599 | $16,299 |
| Especial | 14,465 | $47 | $3,999 |
| Navideños | 5,557 | $167 | $995 |
| Tenis | 354 | $1,124 | $1,349 |

Dos catálogos no se deciden solo con esta tabla. **Especial** tiene mediana de
canasta básica ($47) pero máximo de casi $4,000 — el nombre no dice qué agrupa
y hace falta mirar contenido, no solo el número. Y **Pacic**, aunque el nombre
sugiere un programa agropecuario, había que verificarlo antes de recomendarlo:
se inspeccionó el 14 de septiembre y **son alimentos básicos** — pasta para
sopa, atún, pollo, leche, res, huevo, arroz, aceite, cebolla, cerdo, tortilla,
manzana, sardina, mojarra —, consistentes con ser la canasta oficial
antiinflación del gobierno. Ver la muestra completa en
`docs/datos/perfilado/salidas/` (consulta reproducible al final de este ADR).

**Especial no se alcanzó a inspeccionar de la misma manera.** Queda anotado
como pendiente antes de ratificar el miércoles — ver Consecuencias.

## Decisión

### Catálogos que entran a la canasta básica del producto

- [x] **Basicos**
- [x] **Pacic** — verificado por contenido, no solo por nombre: es la canasta
      básica antiinflación oficial.
- [x] **Frutas y Legumbres**
- [x] **Mercados**
- [x] **Pescados y Mariscos**

**Razón, catálogo por catálogo:**

`Basicos` es el núcleo por definición del propio literal de la fuente.
`Frutas y Legumbres`, `Mercados` y `Pescados y Mariscos` son alimentos de
consumo directo con precio mediano de canasta básica ($38–$153) y sin las
colas largas de los catálogos excluidos. `Pacic` entra por lo mismo que
`Basicos` — es alimento básico — con el argumento adicional de que es
programa gubernamental antiinflación, que es exactamente el tipo de dato que
un índice de canasta básica debería poder comparar contra el propio INPC
(hipótesis H4).

### Catálogos que quedan fuera

- [ ] Medicamentos
- [ ] Electrodomesticos
- [ ] Utiles Escolares
- [ ] Juguetes
- [ ] Navideños
- [ ] Tenis
- [ ] Especial — **excluido por ahora, sujeto a revisión antes del miércoles**

**Medicamentos es el más discutible de los seis y merece decirlo así.** Es
consumo genuinamente básico para muchos hogares, pero su mediana ($245) es 5.4
veces la de `Basicos` y su máximo ($5,891) distorsiona cualquier promedio o
mediana del índice si se mezcla con el resto. Incluirlo complicaría además la
comparación con el INPC de H4, que separa alimentos de salud en categorías
distintas. **No se descarta para siempre** — es candidato natural para una
fase 2 del producto, como catálogo aparte con su propio índice. Para v1, fuera.

`Electrodomesticos`, `Utiles Escolares`, `Juguetes`, `Navideños` y `Tenis`
salen por lo mismo entre todos: medianas y máximos de bienes durables o
estacionales, ajenos al consumo diario de despensa que el proyecto declara
como su objeto.

`Especial` sale **provisionalmente**: su mediana no lo descarta, pero nadie
del equipo ha mirado qué contiene y el nombre no lo dice. Se decide con
contenido, no con la etiqueta — el mismo criterio que ya sirvió para
confirmar `Pacic` y que evitó incluir un catálogo mal entendido solo por su
nombre.

### Consecuencia sobre el volumen comprometido en el protocolo

El ADR 001 midió el recorte de siete entidades en **4,384,962 filas**, un
9.6% por encima del «entre dos y cuatro millones» que compromete el
protocolo, y dejó dicho: *«si al decidir los catálogos se dejan fuera
Medicamentos, Electrodomésticos, Juguetes, Útiles Escolares, Tenis y
Navideños, el recorte baja a alrededor de 2.7 millones»*.

Medido con esta decisión:

| | filas | % del recorte de 7 entidades |
|---|---:|---:|
| Basicos + Pacic + Frutas y Legumbres + Mercados + Pescados y Mariscos | **2,658,906** | 60.6% |

**Cae dentro del rango comprometido.** No hace falta corregir la cifra de
volumen del protocolo — a diferencia de la ventana temporal y el recorte
geográfico, que sí se corrigieron, este número ya escrito sigue siendo
cierto una vez aplicado el recorte de productos.

### Consecuencia sobre H3

Se corrió `h3-muestra-para-calificar.py` ya acotado a los cinco catálogos de
esta decisión (14 de septiembre), para saber si el recorte de productos
cambia lo que ADR 001 ya había medido sobre H3. Resultado: **no cambia la
conclusión, solo la escala.**

| | sin recorte de catálogos (ADR 001) | con este recorte |
|---|---:|---:|
| Formas distintas de escribir (pares) | 1,730 | 596 |
| Sobreviven a la normalización de `marca` (ADR 002) | 687 (39.7%) | 191 (32.0%) |

Los que sobreviven siguen compartiendo clave normalizada, así que siguen
siendo, sin excepción, diferencias mecánicas de mayúscula, acento o
puntuación. **La conclusión del ADR 001 se sostiene con el catálogo acotado:
esos pares no sirven para calificar H3**, y la muestra de 200 pares que sí
sirve —candidatos donde la normalización pudo haber fallado— se construyó
sobre este mismo recorte y quedó lista para calificar en la semana 3. Se
resuelve en **ADR 004**.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| **No recortar por catálogo, dejar los 12** | Contradice el nombre y el objeto del proyecto: «canasta básica» tendría que incluir buscar una pantalla de televisión junto al kilo de tortilla. |
| **Decidir solo con la tabla de medianas, sin inspeccionar contenido** | Habría llevado a incluir `Pacic` por una mala lectura del nombre (parecía un programa agropecuario) o a excluirlo sin verificar. El criterio de este ADR es contenido, no etiqueta. |
| **Incluir Medicamentos** | Su mediana y máximo distorsionan el índice y complican la comparación con el INPC de H4. Queda anotado como candidato de fase 2, no descartado para siempre. |
| **Excluir Pacic por el nombre** | Habría sido exactamente el error que este ADR evita: decidir sin mirar el contenido. Verificado, es alimento básico y el mejor argumento de origen oficial que tiene la propuesta. |
| **Incluir Especial sin inspeccionarlo** | Su mediana no lo descarta pero nadie sabe qué agrupa. Se prefiere dejarlo fuera y revisarlo que arriesgar contaminar el índice con bienes que no son de despensa. |

## Consecuencias

### Antes de la reunión del miércoles 16 — responsable: A

**Inspeccionar `Especial`** con la misma consulta que ya sirvió para `Pacic`
(agrupar por `producto` dentro del catálogo, ver qué aparece). Si el
contenido es de despensa, se propone incluirlo el miércoles; si no, la
exclusión de este ADR se ratifica tal cual.

```bash
python3 -c "
import duckdb, pathlib
p = pathlib.Path.home()/'canastamx-datos/procesado/por_archivo'
duckdb.sql(f'''
  SELECT catalogo, producto, count(*) filas, round(median(precio),2) mediana, max(precio) maximo
  FROM read_parquet(\"{p}/*.parquet\", union_by_name=true)
  WHERE upper(strip_accents(catalogo)) = 'ESPECIAL'
  GROUP BY 1,2 ORDER BY filas DESC LIMIT 40''').show(max_width=120)
"
```

### Para el contrato de datos (T019, A, semana 2)

El contrato tiene que declarar la regla de aceptación por `catalogo` con la
lista de esta decisión, y tiene que **normalizarlo antes de comparar** —igual
que `marca`—, porque la fuente escribe cuatro de los doce catálogos de dos
maneras. Sin esa normalización, filas de `Básicos` (con acento) o `PACIC`
(mayúsculas) se rechazarían o se contarían aparte sin que nadie lo note,
exactamente el mismo riesgo que ya señaló el ADR 001 para esta columna.

### Para `medir-decisiones.py` y `h3-muestra-para-calificar.py`

Ambos guiones ya se corrieron con este recorte (`CATALOGOS = ["Basicos",
"Pacic", "Frutas y Legumbres", "Mercados", "Pescados y Mariscos"]`) para
producir las cifras de este ADR. Si el miércoles se agrega `Especial`, hay
que volver a correr los dos y actualizar las cifras aquí antes de marcar este
ADR como aceptado.

### Para el informe de perfilado y el protocolo

Ninguna corrección de cifra es necesaria por ahora: el volumen ya cae dentro
del rango comprometido (ver arriba). Si el miércoles se agrega `Especial`
(14,465 filas) el total sigue muy por debajo de 4 millones, así que tampoco
cambiaría esa conclusión.
