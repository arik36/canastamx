# ADR 005 · Recorte de productos por catálogo

- **Fecha:** 14 de septiembre de 2026 · **actualizado el 17 de septiembre**
- **Estado:** **aceptada** en la reunión del miércoles 16 — ⚠ **CONFIRMAR ANTES
  DE ENTREGAR**: si la reunión se movió o la lista cambió, este encabezado y
  todas las cifras medidas sobre los cinco catálogos se vuelven a tocar.
- **Participantes:** Ariadne (A) — autora de la propuesta. Ari Adair (B),
  Liseth (C1), Oscar (C2), Karen (D).

> **Nota de archivo.** El issue sembrado en el tablero cita la ruta
> `docs/adr/005-recorte-de-productos.md` y el archivo vive en
> `docs/adr/005-recorte-de-catalogos.md`. Iguala una de las dos antes de
> entregar; da lo mismo cuál, pero que no queden dos.

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

**`Especial` también se inspeccionó** (`revisar-catalogo-especial.py`,
17 de septiembre) y el resultado cambia la razón de su exclusión, no la
exclusión. Está en «Qué es `Especial`», más abajo.

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
- [ ] Especial — **excluido**, inspeccionado el 17 de septiembre: es el catálogo
      de campaña del Mundial 2026, no una categoría de producto

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

`Especial` sale, y la razón **no es la que esta propuesta traía al escribirse**.
Se inspeccionó su contenido y resultó ser un catálogo de campaña, no una
categoría de producto. La justificación completa está en el apartado que sigue.

### Qué es `Especial`, y por qué eso decide su exclusión

**Su mediana no lo distingue de los catálogos que sí entran, y ése era el
criterio con el que se le había excluido.** Ordenados por precio mediano,
`especial` ($46.90) cae **entre `basicos` ($44.90) y `mercados` ($50.00)**, los
dos dentro del ADR 005. Con el criterio de mediana, `Especial` tendría que
entrar. Hacía falta otra razón, y mirar el contenido la dio.

**`Especial` es el catálogo del Mundial 2026.** Sus 25 productos son tres cosas:

| qué es | filas | % del catálogo | ejemplos |
|---|---:|---:|---|
| comida y bebida de fiesta | **13,850** | **95.7%** | papas fritas, refresco, cerveza, chocolate, galletas saladas, queso crema, dip, cacahuates, agua con gas |
| mercancía deportiva | 456 | 3.2% | Balón Oficial Adidas Trionda FIFA World Cup ($3,999), Playera Oficial de México, Argentina, Alemania y España ($2,999), réplicas, mochila, gorra |
| servicio de mesa | 159 | 1.1% | vajilla, cubiertos, platos, tazas, baterías de cocina |

Las quince filas más caras son **todas de Liverpool, todas marca Adidas, todas
entre marzo y junio de 2026**: el balón oficial y las playeras de selección. No
es un precio raro de un artículo básico —el caso del Centro de Lavado— sino un
artículo que nunca debió estar en un catálogo de precios básicos.

**Tres razones para dejarlo fuera, en orden de peso:**

**1 · Es temporal por construcción.** Un catálogo que existe por un evento
desaparece con el evento. Incluirlo mete en la serie un quiebre estructural en
agosto de 2026 que no tiene nada que ver con inflación, y para H4 —la
correlación contra el INPC— eso es ruido que habría que explicar cada vez.

**2 · Su comida ya está cubierta.** De sus 25 productos, **7 ya aparecen en los
cinco catálogos decididos**: agua con gas, cacahuates, cerveza, chocolate,
galletas saladas, papas fritas y refresco. Son 11,132 de sus 13,850 filas de
comida. **Excluir `Especial` cuesta 2,718 filas de alimento que no está en otro
lado —Dip y Queso Crema—, el 0.10% del alcance del contrato.** El catálogo
entero es el 0.54%.

**3 · Un producto en dos catálogos rompe lo que está indexado por catálogo.**

> **Precisión importante, porque el guión lo dice de una manera que confunde.**
> Su salida advierte que ingerir `Especial` sería «contar el mismo artículo dos
> veces», y **eso no es exacto**: la clave de artículo es
> `producto` + `presentacion` y **no incluye `catalogo`**, así que un `Refresco`
> capturado bajo `Especial` y otro bajo `Basicos` colapsan en el mismo artículo
> y suman observaciones, que es el comportamiento correcto. El conteo de
> artículos no se infla.
>
> Lo que sí se rompe es todo lo que está **indexado por catálogo**. En concreto,
> `precio.maximo_por_catalogo` del contrato: si el mismo `Refresco` puede venir
> etiquetado de dos maneras, deja de estar claro qué techo le aplica. Y la clave
> de fila tampoco lleva `catalogo`, así que un precio capturado una vez y
> archivado en dos catálogos aparece como colisión de $0 y se deduplica — lo
> cual está bien, pero conviene saber que pasa.
>
> El costo real, entonces, no es duplicación: es **ambigüedad de catálogo en el
> 0.54% de las filas a cambio de 0.10% de dato nuevo.** No sale.

**Lo que NO es razón para excluirlo, y conviene decirlo para que nadie lo
repita:** que tenga artículos caros. Mandar el balón de $3,999 a cuarentena por
techo de precio sería llenar la cuarentena de algo que no es un defecto —el
precio es correcto—, que es exactamente el error que el perfilado ya corrigió
con el `?` y con los centinelas. Un artículo fuera de alcance se deja fuera en
el filtro de ingesta, no se rechaza en la compuerta.

> **De paso, dos casos más del bug del `?`, los dos dentro de este catálogo:**
> `Balón Oficial` (5 filas) contra `Bal?n Oficial` (1), y `Réplica de Balón`
> (47) contra `Réplica de Bal?n` (16). El mismo artículo partido en dos. No
> cambia esta decisión —el catálogo queda fuera— pero suma evidencia a la regla
> de reparación del contrato.

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

### Lo que la medición posterior confirmó, y lo que destapó

Después de escribir esta propuesta se midió sobre el alcance que produce —siete
entidades ∩ 2025-2026 ∩ estos cinco catálogos, 2,658,906 filas—
(`medir-para-contrato.py`, 17 de septiembre). Tres hallazgos, y el segundo
cambia cómo hay que leer este ADR.

**1 · El catálogo del producto es mucho más chico de lo que nadie suponía.**

| unidad | corpus sin `?` | **este recorte** |
|---|---:|---:|
| productos | 816 | **303** |
| artículos (`producto` + `presentacion`) | 5,015 | **1,597** |

La caída no es proporcional a las filas —el recorte deja el 60.6% de las filas
pero sólo el 32% de los artículos— y la razón es `Medicamentos`: son 401
productos, cada uno con su propia presentación única. **Este recorte no sólo
quitó filas: quitó la parte del catálogo que más artículos distintos aportaba
por producto.** Que sean 1,597 y no 5,015 tiene consecuencias prácticas para
C1 y C2: el catálogo cabe entero en memoria y la búsqueda no necesita
paginación agresiva.

**2 · `catalogo` y `categoria` NO están anidadas — y eso matiza este ADR.**

Son dos clasificaciones **independientes** de la fuente. Dentro de `Basicos`
conviven 37 categorías, y varias pertenecen a catálogos que este ADR deja
fuera. El caso que hay que decir en voz alta: **este ADR excluye el catálogo
`Medicamentos`, y aun así entran 8,212 filas de `categoria = medicamentos`**
por la puerta de `Basicos`. Lo mismo con 16,723 de
`productos de temporada (navidenos)`, 2,217 de `pescados y mariscos`, 8,194 de
`accesorios domesticos` y 2,618 de `utensilios domesticos`.

**No es un defecto, y el detalle importa:** los medicamentos que entran por
`Basicos` son **3 productos con mediana de $30 y máximo de $134** —analgésico
de mostrador—, mientras que el catálogo `Medicamentos` que queda fuera son 401
productos con mediana de $245 y máximo de $5,891. **El recorte por catálogo
hizo exactamente lo correcto sin que nadie lo planeara**: se quedó con el
medicamento básico de una despensa y dejó fuera el de receta.

Lo único que faltaba era anotarlo, para que nadie lea este ADR como «no hay
medicamentos» y se sorprenda al ver una caja de aspirinas en el catálogo.

**3 · `Basicos` no es «la despensa»: es más ancho.** Su categoría más grande es
`arts. para el cuidado personal`, con **290,136 filas — el 10.9% de todo el
alcance**. Le siguen refrescos, derivados de leche, papel higiénico y
detergentes. También contiene `cerveza` (35,000), `vinos y licores` (26,197) y
`cigarrillos` (3,794).

Eso **no cambia la ingesta** —el protocolo compromete la clasificación *de la
fuente*, y sacar artículos porque nos parecen poco básicos sería sustituirla
por un criterio propio que habría que defender caso por caso—, pero sí obliga a
una decisión de mensaje que este ADR no había previsto. Está en el contrato
como `presentacion.ocultar_por_defecto_en_canasta_basica`: la vista por omisión
oculta esas tres categorías —**64,991 filas, el 2.44% del alcance**—, el dato
entra igual y el usuario puede verlo. **La decide el equipo con C2 y D, no el
frente de datos.**

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

### Inspección de `Especial` — hecha el 17 de septiembre

**Cerrado.** Lo midió `docs/datos/perfilado/revisar-catalogo-especial.py` y el
resultado está arriba, en «Qué es `Especial`». La exclusión se ratifica, pero
con una razón distinta de la que esta propuesta traía: no es por su precio
mediano —que no lo distingue de `Basicos` ni de `Mercados`— sino porque es un
catálogo de campaña del Mundial 2026, temporal por construcción, cuya comida ya
está cubierta en un 80% por los catálogos que sí entran.

La consulta original que quedó anotada aquí:

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

Ninguna corrección de cifra es necesaria: el volumen ya cae dentro del rango
comprometido (ver arriba). Si se agregara `Especial` (14,465 filas) el total
sigue muy por debajo de 4 millones, así que tampoco cambiaría esa conclusión.

**Lo que sí hay que corregir en el informe** es de signo contrario a lo que
decía: la versión 0 concluía que el recorte excedía el compromiso del protocolo
por 384,962 filas y que había que corregir el documento. **Con este recorte ya
no hay nada que corregir.** Va en `informe-perfilado-v1.md`.

### Lo que sigue abierto

**Si la lista cambia, se vuelve a medir todo.** Las cifras del contrato
—`medicion`, `clave_de_fila.colisiones_conocidas`, `precio.maximo_por_catalogo`,
el porcentaje de `S/M` y el conteo de artículos— están **atadas a estos cinco
catálogos**. No es una advertencia de forma: ya pasó tres veces que una cifra
medida sobre una población se copiara a otra. · **A**
