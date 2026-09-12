# ADR 001 · Fuente de datos y recorte

- **Fecha:** 11 de septiembre de 2026
- **Estado:** aceptada
- **Participantes:** Ariadne (A), Ari Adair (B), Liseth (C1), Oscar (C2), Karen (D)

## Contexto

Se perfiló la fuente QQP de PROFECO del 7 al 10 de septiembre: 38 archivos
quincenales, **21,357,873 filas**, de enero de 2025 a julio de 2026. Los
hallazgos completos están en `docs/datos/informe-perfilado-v0.md` y el detalle
técnico en `docs/datos/perfilado.md`.

Tres cifras pesaron en la decisión:

**El precio llegó íntegro.** Cero nulos, cero en cero, cero negativos y ningún
valor centinela, buscados con tres detectores distintos. El precio es la
variable del proyecto, y es la que está limpia.

**La suciedad es de texto y está acotada.** 770,273 filas (3.61%) traen
caracteres corrompidos. De las 1,123,994 **apariciones** de texto roto, el
96.82% se repara de forma determinista. El 97.76% de ese daño viene de una sola
falla masiva en junio de 2026; julio vuelve a estar limpio.

**El recorte del protocolo no coincide con lo que hay.** La sección 8 del
protocolo compromete, literalmente: *«Recorte geográfico a **Guanajuato y tres
entidades vecinas**, con ventana temporal de 2024 a 2026, correspondiente a un
volumen estimado entre dos y cuatro millones de registros»*. La fuente entrega
cobertura nacional de 30 entidades, ventana de enero de 2025 a julio de 2026, y
21.4 millones de registros. Y **faltan Colima y Nayarit por completo**: no
aparecen en ninguno de los 38 archivos.

Conviene decirlo sin rodeos, porque el asesor lo va a notar: **el protocolo
compromete cuatro entidades y este ADR decide siete.** No es sólo nombrarlas: es
una ampliación, y como tal hay que justificarla y corregir el protocolo.

Un cuarto hecho, menor en volumen pero no en consecuencias: **dos de los 38
archivos traen tres columnas que los otros 36 no traen** —`folio`,
`cv_producto` y `cv_marca`, las dos quincenas de junio de 2026— y ninguna de las
tres está en el diccionario oficial de PROFECO. El 94.12% de las filas no las
tiene. Julio vuelve a 15 columnas.

Y un quinto que salió al revisar este ADR contra el protocolo, y que **no se
trató en la reunión**: la misma sección 8 compromete también un *«recorte de
productos a la canasta básica, conforme a la clasificación de productos de
consumo generalizado de la fuente»*. Nadie decidió nada sobre productos. Queda
como punto pendiente al final.

## Decisión

### Sobre la fuente

- [x] **Se continúa con el conjunto QQP de PROFECO**
- [ ] Se activa el plan alternativo: base 2025 más recolección propia acotada

**Razón:** el precio, que es la variable del proyecto, llegó íntegro. La
suciedad está medida, acotada y es reparable en un 96.82%. Que la fuente esté
sucia no la descalifica: **que esté sucia es la premisa del proyecto.** Lo que
la descalificaría sería que el precio no fuera recuperable, y sí lo es.

### Sobre el recorte territorial — se separa en dos niveles

El recorte deja de ser uno solo. **La base de trabajo y el producto desplegado
cubren territorios distintos, a propósito.**

**Nivel 1 · laboratorio.** La base de datos se trabaja **a nivel nacional, de
forma local, en la máquina de A**, preparada para los 21.4 millones completos
pero **cargándose también por etapas, empezando por una o dos entidades**. Se
descartó Supabase para este nivel porque no acepta ese volumen.

> El laboratorio nacional **no es cobertura nacional del producto**. El
> protocolo declara expresamente que el proyecto *«no pretende cobertura
> nacional»*, y eso se respeta: lo nacional es material de trabajo, no alcance
> comprometido.

**Nivel 2 · producto desplegado.** La página web y la aplicación móvil cubren
**siete entidades de centro-occidente**:

| | Entidad |
|---|---|
| 1 | Aguascalientes |
| 2 | Guanajuato |
| 3 | Jalisco |
| 4 | Michoacán |
| 5 | Querétaro |
| 6 | San Luis Potosí |
| 7 | Zacatecas |

**Colima y Nayarit quedan fuera del alcance declarado** porque no existen en la
fuente. No es una omisión: es un hecho medido que el producto tiene que decir.

**El despliegue es por etapas.** Arranca con **Guanajuato solo**, para ver cómo
responden el frente y el servicio con datos reales de una entidad. Conforme se
verifique el funcionamiento, se agregan las demás hasta llegar a las siete.

### Sobre la ventana temporal

- [x] **Se trabaja con 2025 y 2026.**

**Razón:** es lo que la fuente descargada entrega. El protocolo comprometió
2024–2026 antes de mirar los archivos.

> **Medido:** el filtro de años no quita ni una fila del corpus actual. Todo lo
> descargado ya está dentro de la ventana. **La reducción de volumen viene
> entera del recorte territorial, no de la ventana.** Conviene decirlo así en el
> protocolo, para no dar a entender que se descartaron datos que nunca hubo.

### Sobre las columnas que aparecen y desaparecen

- [x] **Las tres columnas extra de junio de 2026 —`folio`, `cv_producto` y
      `cv_marca`— no se ingieren.** El modelo de datos son las 15 columnas
      documentadas en el diccionario de PROFECO. El equipo acordó descartarlas
      **sin señalamiento**.

**Razón:** no están en el diccionario oficial, no hay documentación de qué
significan, y el 94.12% de las filas no las trae. Construir sobre una columna
que aparece en 2 de 38 archivos es construir sobre algo que puede desaparecer.

> **Punto abierto, a ratificar el 16 de septiembre.** La segunda mitad de esta
> decisión —descartarlas *en silencio*— quedó anotada tal como se dijo, pero
> tiene una tensión con el objeto de investigación del proyecto. Está
> desarrollada en Consecuencias, al final.

### Sobre la hipótesis H3

- [ ] Se sostiene la meta de 85% de cobertura y 90% de precisión
- [ ] Se ajusta la cobertura a ___%
- [x] **Queda abierta.** No se alcanzó a tratar en la reunión del 11.

El perfilado encontró que la fuente ya viene casi normalizada —1.29 formas de
escribir el mismo artículo, cero agrupamientos incorrectos en la revisión
manual— y que toda la variación es mecánica: mayúsculas y acentos. Eso abre la
sospecha de que **H3 mide la solución a un problema que esta fuente no tiene**,
porque PROFECO captura con su propio catálogo y no deja que cada tienda escriba
el nombre: hay sólo 896 nombres de producto para 247 cadenas.

Falta el dato que lo confirma o lo desmiente: cuántos pares *mismo artículo, dos
cadenas, escritura distinta* se pueden formar. H3 pide 200. Lo mide
`docs/datos/perfilado/h3-entre-cadenas.py`, **que hay que correr sobre los datos
reales antes de decidir**. Se resuelve en **ADR 004**, antes del 18 de
septiembre.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| **Recolección propia desde cero** | No hace falta: el precio de QQP llegó íntegro. Y costaría las catorce semanas del semestre construir lo que ya está publicado. |
| **Usar sólo la base de 2025** | Tirar siete meses de 2026 sin ninguna razón medida. La serie continua de 19 meses es lo que permite ver tendencia, que es la mitad del producto. |
| **Confirmar el recorte del protocolo tal cual (centro-occidente, 2024–2026)** | No se puede: Colima y Nayarit no existen en la fuente, y 2024 tampoco. Confirmarlo sería comprometerse por escrito con datos que no hay. |
| **Ampliar también el producto a cobertura nacional** | Era la recomendación del informe de perfilado, y el equipo la descartó: 21.4 millones de filas en el producto desplegado obligan a una infraestructura que no cabe en el semestre, y el valor para el usuario no crece por mostrarle entidades donde no vive. Se conserva el alcance nacional donde sí sale gratis —el laboratorio— y se acota donde cuesta. |
| **Acotar también el laboratorio a las siete entidades** | Descartaría datos que ya están descargados, ya están perfilados y no cuestan nada procesar: DuckDB agrega los 21 millones en segundos. Y dejaría sin material la comparación entre regiones, que es evidencia barata para el reporte final. |
| **Supabase con los 21 millones** | No acepta ese volumen. Es lo que obligó a partir el recorte en dos niveles. |
| **Ingerir las tres columnas extra por si acaso** | Serían nulas en el 94.12% de las filas y nadie sabe qué significan. Una columna sin definición en el diccionario no se puede validar, y lo que no se puede validar no entra al contrato. |

## Consecuencias

### Correcciones al protocolo — **antes del 18 de septiembre** · responsable: A

Son cinco, no tres, y **dos son ampliaciones**: hay que justificarlas, no sólo
anotarlas.

| Qué dice el protocolo (sección 8) | Qué tiene que decir | Tipo |
|---|---|---|
| «Guanajuato y **tres entidades vecinas**» | **Siete entidades**, nombradas, sin Colima ni Nayarit | **ampliación de 4 a 7** |
| «Ventana temporal de **2024 a 2026**» | **2025 – 2026**, porque es lo que la fuente publica | reducción |
| «Entre **dos y cuatro millones** de registros» | La cifra medida del recorte | por medir |
| «**Recorte de productos a la canasta básica**» | Sin decidir — ver el punto abierto al final | **pendiente** |
| Objetivo 4: reconciliación «mediante vocabulario canónico, diccionario de equivalencias **y comparación difusa**» | La comparación difusa se descarta: toda la variación medida es mecánica y una normalización determinista la resuelve entera (ADR 002) | corrección a declarar |

**Por qué se amplía de 4 a 7, y no es capricho:** las siete son las entidades de
centro-occidente que la fuente sí trae. Guanajuato más tres vecinas habría sido
una elección arbitraria entre las mismas siete, y excluir a la mitad de la
región no reduce el trabajo —el flujo es el mismo— mientras que sí reduce el
valor del índice por entidad, que es un entregable comprometido. Colima y
Nayarit, que completarían la región, quedan fuera porque no existen en la
fuente.

### Cifras que faltan y quién las consigue

**El volumen del recorte todavía no está medido.** Lo mide
`docs/datos/perfilado/medir-decisiones.py`, que ya está escrito y probado. Sale
de ahí si el compromiso de «dos a cuatro millones» se sostiene o hay que
corregirlo también. · **A · el lunes 14 a primera hora**, porque el contrato de
datos de la semana 2 se escribe con ese número.

**Nadie ha comprobado que Supabase aguante las siete entidades.** Se descartó
por los 21 millones, pero el recorte no se ha pesado. El mismo guión da la
estimación. Si no cabe, el despliegue por etapas deja de ser una preferencia y
pasa a ser la única forma, y hay que decidir a qué se migra al crecer —eso sería
un ADR aparte. · **A y B · antes del miércoles 16**.

### Riesgos que deja abiertos esta decisión

**La base nacional vive en una sola máquina.** Si la máquina de A falla, no hay
base. Y hay una dependencia concreta: **B tiene que correr las treinta corridas
del experimento en la semana 13** sobre un entorno aislado, y hoy los datos
están donde B no los alcanza. Hay que decidir cómo se le entrega a B un
subconjunto reproducible. · **A y B · se decide antes del 25 de octubre**, que
es cuando B monta el entorno de pruebas aislado (semana 8 del cronograma).

**El producto tiene que declarar su cobertura.** Un usuario de Colima que abra
la aplicación no puede quedarse sin entender por qué no aparece su estado. Va en
la interfaz, no en la documentación. · **C2 y D · cuando se maqueten las
pantallas de búsqueda, semanas 8 y 9**, y anotado desde ahora en el inventario
de vistas para que no se olvide.

**Los datos semilla de B y las pruebas de C2 se hacen con Guanajuato**, no con
el corpus completo ni con datos inventados. Es el tamaño del primer despliegue.
· **B · semana 7**.

### El punto abierto del recorte de productos

**Este ADR decidió el recorte de territorio y el de tiempo, pero no el de
productos, y el protocolo compromete los tres.** La lista de verificación de la
semana 1 del cronograma también lo pide con esas palabras: *«recorte geográfico
**y de productos** definido con base en datos reales»*.

No es un tecnicismo. El corpus trae 896 productos que incluyen celulares,
lavadoras, barras de sonido y pantallas de televisión. Hoy, si alguien busca
«despensa» en el producto, le puede salir una pantalla junto al kilo de
tortilla. Y el proyecto se llama *plataforma de inteligencia de precios de
**canasta básica***.

**La buena noticia es que la decisión está casi tomada por la fuente.** El
protocolo dice *«conforme a la clasificación de productos de consumo
generalizado de la fuente»*, y esa clasificación **es la columna `catalogo`**,
que trae **16 valores** —`Frutas y Legumbres` es uno—, sin nulos ni vacíos. La
decisión se reduce a: **cuáles de los 16 entran.**

`docs/datos/perfilado/medir-decisiones.py` imprime los 16 con su volumen, su
precio mediano y su precio máximo. Un catálogo con mediana de cientos de pesos
no es canasta básica, se llame como se llame.

· **A lleva la lista · se decide en la reunión del miércoles 16 · queda como
ADR 005.**

### El punto abierto del descarte silencioso

Descartar las tres columnas **es correcto**, y esa parte no está en discusión.
Lo que conviene mirar una vez más, cinco minutos el miércoles 16, es la palabra
**«en silencio»**.

El objeto de investigación de este proyecto, escrito en el protocolo, son los
**contratos de datos, las compuertas de calidad y la observabilidad**. La frase
que lo define dice que cuando llega información defectuosa el sistema *no la
deja pasar: la bloquea, la aísla y señala el incidente en un tablero de
control*. Una columna que aparece en junio y desaparece en julio es exactamente
eso: **deriva de esquema**, uno de los tres tipos de incidente que el proyecto
existe para detectar.

Y hay un detalle práctico: **la consola de observabilidad de D necesita seis
indicadores con datos reales detrás, y todavía no están definidos.** La deriva
de junio de 2026 es el único episodio real de deriva de esquema que tiene el
proyecto entero. Si se descarta en silencio, ese indicador se queda sin nada que
mostrar y habría que simularlo.

La enmienda cuesta casi nada y no cambia el fondo de la decisión:

> Las columnas **no se ingieren** —igual que se decidió— **pero el hecho se
> registra como un aviso**, no como un rechazo: *«el archivo de la primera
> quincena de junio de 2026 trae 18 columnas; se ignoraron folio, cv_producto y
> cv_marca»*. El lote entra completo, nadie se bloquea, y queda el rastro.

Sin la enmienda: si en marzo aparece una columna que sí importa, nadie se
entera. Con ella: aparece un renglón en la consola.

· **Lo lleva A a la reunión del 16 · se ratifica o se enmienda ahí, y si se
enmienda, se anota como ADR 001-bis y no se edita este documento.**
