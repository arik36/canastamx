# ADR 004 · H3 · cómo se enuncia y cómo se mide
 
- **Fecha:** 17 de septiembre de 2026 · **resultados añadidos el 24 de septiembre**
- **Estado:** **aceptada.** El método y la corrección al ADR 002 los ratificó el
  equipo en la boleta de la semana 3 (ADR 010, decisiones 4 y 8). La tabla de
  resultados quedó llena el 24 de septiembre
- **Autor:** Ariadne (A) · frente de datos
- **Corrige:** el ADR 002, en una línea de «Alternativas descartadas»
- **Cierra:** el punto abierto «Sobre la hipótesis H3» del ADR 001
> **Por qué este ADR existe si ya están `perfilado.md` y el informe v1.** Los tres
> documentos hacen trabajos distintos y ninguno sustituye a otro. `perfilado.md`
> es la bitácora: qué se midió, con qué guión y sobre qué población; cambia cada
> vez que se vuelve a medir. `informe-perfilado-v1.md` es el relato para quien
> no estuvo: cuenta la exploración y a qué llevó, y se congela por versión. Este
> ADR es **la decisión**: qué se comprometió el equipo a hacer, quién lo decidió,
> qué se descartó y qué le cuesta a cada frente. Los dos primeros, de hecho,
> dicen literalmente «la corrección formal va en el ADR 004»: se lo saltan a
> propósito, porque un documento que describe no puede comprometer a nadie.
>
> La prueba está en la pregunta que va a hacer el asesor en noviembre: *«¿contra
> qué se mide esta hipótesis?»*. Sin este archivo, la respuesta está repartida en
> tres documentos que se citan entre sí y en ninguno es vinculante.
 
## Contexto
 
El protocolo enuncia H3 así: *«la reconciliación de nombres de producto entre
cadenas alcanza una cobertura ≥ 85% con precisión ≥ 90%, sobre una muestra
aleatoria de 200 pares»*. Esa es la hipótesis que sostiene el frente de datos
entero y la que se mide en la semana 9 (T058).
 
El ADR 001 dejó el punto abierto —marcado así, con la casilla sin llenar— por
una razón concreta: **la primera medición no podía fallar**, y una hipótesis que
no puede fallar no es una hipótesis.
 
`h3-entre-cadenas.py` armó 1,730 pares de escrituras distintas del mismo
artículo, y el 100% resultaron diferencias mecánicas: mayúsculas, acentos,
puntuación. No era una propiedad de los datos sino del método. Los pares se
armaban **uniendo literales que ya compartían clave normalizada**, y dos
literales que comparten clave normalizada sólo pueden diferir en lo que la
normalización quita. Se estaba midiendo la cobertura sobre el conjunto de casos
que la normalización resuelve por definición.
 
Los casos donde la normalización **falla** —dos escrituras del mismo artículo
que caen en claves distintas— eran invisibles ahí, porque si cayeron en claves
distintas el cruce nunca las junta.
 
De ahí salió `h3-muestra-para-calificar.py`: construye pares entre claves
**distintas**, que son los únicos donde el sistema puede equivocarse, y los
deja para calificar a mano. Esa muestra es la que este ADR usa.
 
> **Sobre la población.** Las cifras de arriba (1,730 pares, 687 sobrevivientes
> a la normalización de `marca`) están medidas sobre el corpus. Con el recorte
> de catálogos del ADR 005 aplicado, la muestra se regeneró el 14 de septiembre
> y las cifras equivalentes son **596 pares, 191 sobrevivientes (32.0%)**. El
> recorte cambia la escala, no la conclusión: los que sobreviven siguen
> compartiendo clave normalizada, así que siguen siendo, sin excepción,
> diferencias mecánicas. La comparación está en el ADR 005, § «Consecuencia
> sobre H3».
 
## Decisión
 
### 1 · H3 se mide sobre pares que la normalización NO unió
 
La muestra de 200 pares **no** se toma al azar del conjunto de artículos. Se
construye así, y esto queda fijado:
 
| | |
|---|---|
| Universo | pares de artículos con **claves normalizadas distintas**, dentro del alcance del contrato |
| Filtro de candidatos | los **números tienen que coincidir** entre las dos escrituras |
| Mitad 1 · 100 pares | los de mayor parecido de texto **sobre las letras solamente** |
| Mitad 2 · 100 pares | tomados **al azar** del resto |
| Se califica | a mano, comparando **las claves ya normalizadas**, no los literales |
 
**Por qué los números tienen que coincidir.** La primera versión ordenaba por
parecido de texto a secas y los diez primeros candidatos fueron
`Bencilpenicilina · Inyectable 400 000 Ui` contra `800 000 Ui`: 60 de 61
caracteres iguales y **dosis distintas**. En esta fuente el número es lo que
define el artículo —la dosis, el gramaje, el conteo de piezas, el modelo— y las
letras son lo que se escribe de maneras distintas. Con esta regla `1 L` contra
`1 Lt` entra y `400 000` contra `800 000` no.
 
**Por qué dos mitades y no una.** Miden cosas distintas y se reportan por
separado:
 
- La mitad **por parecido** mide **cobertura**: cuántos de los que sí son el
  mismo artículo se nos escaparon. Los «sí» de esta mitad son el denominador
  que a la medición anterior le faltaba.
- La mitad **al azar** mide **precisión**: sin pares verdaderamente distintos
  no hay con qué medirla. Ahí los «no» cuentan a favor.
**La polaridad está al revés que en `variantes-para-revisar.txt`**, y conviene
dejarlo escrito porque ya confundió a alguien: allá «sí» confirmaba que el guión
acertó al juntar dos escrituras; aquí el sistema **no** los juntó, así que un
«sí» significa que se escapó uno. Es un fallo de cobertura y cuenta en contra.
 
### 2 · Los pares que sólo difieren en `marca` no son fallos de cobertura
 
Consecuencia directa del ADR 002: el artículo es `producto` + `presentacion`, y
`marca` **no** identifica. Entonces `Frijol Bayo · 1 Kg · Verde Valle` y
`Frijol Bayo · 1 Kg · La Merced` **ya son el mismo artículo** por definición del
contrato, y que aparezcan como dos filas no es un fallo de la reconciliación:
es el comportamiento correcto.
 
**Esos pares se reportan aparte y no entran en el cálculo de cobertura.** Si
entraran, la cobertura saldría artificialmente baja por una decisión de diseño
que ya se tomó a propósito.
 
> **Corrección del 23 de septiembre.** La primera versión de
> `h3-muestra-para-calificar.py` construía los candidatos con una clave que
> incluía `marca` —exactamente la alternativa que el ADR 002 descartó— y por eso
> **80 de los 200 pares (40%) sólo difieren en la marca**: `Nutri` contra
> `Tamariz`, `Borden` contra `León`. Calificarlos obligaba a contradecir el ADR
> 002 si se marcaban «no», o a anotar como fallo de cobertura algo que la
> reconciliación nunca tuvo que resolver si se marcaban «sí». El guión se
> corrigió para separar las dos claves del ADR 002 §4 —`clave` con marca para el
> diagnóstico de escritura, `clave_articulo` sin marca para los candidatos— y la
> muestra se regeneró. **En la muestra vigente esa columna es cero por
> construcción**, y las 62 calificaciones de pares de sólo-marca se descartaron.
> Se conserva el hallazgo lateral: 6 de esos 80 eran la **misma marca escrita de
> dos formas** (`Mazatán`/`Mazatún`, `El Duende Frijolín`/`Frijolón`). No afectan
> la identidad del artículo, pero sí rompen el filtro por marca que el ADR 002 §2
> promete, y son evidencia adicional a favor de la comparación difusa.
 
### 3 · La comparación difusa entra al alcance — corrección al ADR 002
 
El ADR 002 descartó la comparación difusa con este argumento:
 
> *«toda la variación medida es mecánica y una normalización determinista la
> resuelve al 100%»*
 
**Ese argumento era circular**, por lo explicado en el contexto: se apoyaba en
pares que ya compartían clave normalizada. La conclusión que sale de él no es
válida, y esta es la corrección formal.
 
La muestra construida sobre claves **distintas** sí trae casos que ninguna regla
determinista une:
 
| par | qué los separa | ¿lo une una regla de mayúsculas/acentos? |
|---|---|---|
| `Mazatán` / `Mazatún` | una letra en medio de la palabra | no |
| `Whirlpool` / `Whirpool` | una letra faltante | no |
| `1 L` / `1 Lt` | abreviatura de unidad | no |
| `Mh1536` / `Mh 1536` | espacio dentro de un código | no |
 
Y hay un segundo mecanismo que tampoco es normalización: la **reparación del
`?`**. Recuperar `Camar?n` como `Camarón` buscando un gemelo de la misma
longitud entre los valores limpios de la columna es reconciliación, no limpieza
de mayúsculas. Esa regla ya vive en `contracts/qqp-v1.yaml`
(`normalizacion.reparar_interrogantes`) y en `perfilado.md` §3.
 
**Decisión: la comparación difusa sí hace falta y entra al alcance**, como el
protocolo la había comprometido desde el principio —*«una comparación difusa
que tolere diferencias menores de escritura, abreviaturas y unidades»*—.
 
Hay evidencia de diseño que ya lo asumía: el wireframe de la consola de D
incluye una pantalla **«Revisión de Diccionario y Comparación Difusa»**, con
cola de revisión manual y botones de aprobar, rechazar y asignar.
 
> **El ADR 002 no se edita.** Está aceptado, y por convención del proyecto un ADR
> aceptado se corrige desde el que viene. Sus cuatro decisiones siguen vigentes
> sin cambio: el artículo es `producto` + `presentacion`, `marca` no identifica,
> `S/m` es categoría propia y las dos claves son distintas. Lo único que cae es
> la línea de «Alternativas descartadas» sobre comparación difusa.
 
### 4 · La regla de reenunciación, fijada antes de ver los resultados
 
Esto se escribe **antes** de contar los «sí» a propósito: si la regla se elige
después de ver los números, se elige la que conviene.
 
| si la mitad por parecido da… | entonces |
|---|---|
| **≥ 20 «sí»** | la hipótesis tiene material real. Se mide como está enunciada, con la meta de 85% de cobertura y 90% de precisión |
| **< 20 «sí»** | la normalización determinista ya cubre casi todo y la meta no puede fallar. **Se reenuncia H3** sobre el eje que sí es difícil |
 
**El eje de reenunciación, ya identificado:** reconciliar **presentaciones**
dentro de un mismo producto. `Carne Res` tiene 57 presentaciones distintas. Eso
ninguna normalización lo resuelve, y sí es investigación.
 
### Cómo se calificó
 
**Quién y cuándo.** Ariadne Lizett Macías Campos (frente A), el 24 de
septiembre de 2026, **revisando y corrigiendo una propuesta asistida**. No fue
una calificación a ciegas ni una doble calificación independiente: la propuesta
se generó primero y se revisó par por par. Se anota así porque cambia lo que el
número significa y porque el orden se eligió a sabiendas.
 
De los 200, la revisión cambió el veredicto propuesto en **19 pares** —acuerdo
del 90.5%, kappa de Cohen 0.578— y en **17 de esos 19** la corrección fue en la
misma dirección: la propuesta decía «distintos» y la revisión dijo «el mismo».
La propuesta aplicaba una regla mecánica («más específico = distinto») que no
distingue un grado de calidad de un nombre de línea comercial. La revisión sí.
 
**La regla de calificación, declarada antes de cerrar el conteo.** Tres
preguntas, en orden; se detiene en la primera que aplique:
 
| | Pregunta | Veredicto |
|---|---|---|
| **P1** | ¿La diferencia es sólo de escritura? Plural, acento, conector (`a`/`ó`), abreviatura (`No.`, `c/u`), orden de palabras, preposición, unidad (`gr`/`ml`) | **sí** |
| **P2** | ¿Las dos escrituras nombran cosas distintas, y las dos lo dicen explícitamente? `congelado`/`descongelado`, `primera`/`tercera`, `con sal`/`sin sal`, `bolsa`/`bote` | **no** |
| **P3** | Una escritura tiene una palabra de más. Se clasifica **la palabra**: estado, tamaño, corte, tipo, variedad, grado, origen, sabor, ingrediente, propiedad nutricional o envase → **no**; nombre de línea comercial, color de empaque, o algo que la norma o la costumbre ya dan por hecho → **sí** | según la clase |
 
Default cuando P3 no alcanza a decidir: **sí**. Asumir que se escapó uno es la
postura que no favorece al propio sistema.
 
**Por qué P3 clasifica la palabra y no el par.** Es lo que la hace aplicable
igual 51 veces. El caso «una escritura omite un calificador» es **51 de los 200
pares**, más de la cuarta parte, y sin una regla de clase se decide por
intuición y deriva. Se probó antes una regla objetiva —la razón de filas entre
las dos escrituras, bajo la idea de que un calificador raro es una anotación del
capturista y no una línea de producto— y **se descartó porque no separa**: hay
«no» con razón 5,895× y «sí» con razón 1.0×. Reproducía cuatro ejemplos
escogidos y fallaba en el conjunto.
 
**Trazabilidad.** Al declarar la regla, 11 pares quedaron en contra de ella y se
ajustaron; cada uno lleva en el archivo una línea `CORREGIDO` con la pregunta
que lo decide. Otros 7 se quedaron en «sí» con una línea `EXCEPCIÓN` que dice
por qué la regla los admite —el jitomate cuyo grado «primera» aparece en 283
filas contra 45,076, la gelatina de limón que siempre es de agua, el camarón
donde `congelado o descongelado` cubre los dos estados y por tanto no
restringe—. El archivo calificado es auditable par por par.
 
### Resultado de la calificación
 
| | sí (mismo artículo) | no (distintos) | sólo difieren en `marca` |
|---|---:|---:|---:|
| Mitad por parecido (100) | **20** | 80 | 0 |
| Mitad al azar (100) | 3 | 97 | 0 |
| **Total** | **23** | **177** | **0** |
 
La columna de `marca` es cero **por construcción**: el guión corregido ya no
genera esos pares. Ver la nota del punto 2.
 
**Rama de la tabla del punto 4 que aplica: la primera.** La mitad por parecido
da 20 «sí», la regla pide ≥ 20, y la regla se fijó antes de contar.
 
**Enunciado final de H3 — se queda como está:** *la reconciliación de nombres de
artículo entre cadenas alcanza una cobertura ≥ 85% con precisión ≥ 90%.*
 
> ### ⚠ El resultado cayó exactamente en el umbral
>
> **20 contra 20. El margen es cero.** Un solo par que cambie de veredicto en la
> mitad por parecido tumba la decisión hacia la reenunciación. Conviene decirlo
> con todas sus letras en vez de esconderlo, por tres razones:
>
> 1. La regla se fijó **antes** de contar, y por eso se aplica tal cual. Ése era
>    todo el punto de fijarla por anticipado: si se negocia ahora que el número
>    incomoda, la precaución no sirvió de nada.
> 2. La calificación de la mitad por parecido **ya se movió una vez**: la primera
>    pasada daba 27 «sí» y bajó a 20 al declarar la regla y corregir los 7 pares
>    de esa mitad que quedaban contra ella. O sea que el 20 es el resultado
>    *después* de apretar el criterio, no antes.
> 3. En la semana 9 (T058) la medición se hace contra el sistema implementado.
>    **Si para entonces la calificación se revisa por cualquier motivo, el conteo
>    se recalcula y la rama se vuelve a evaluar**, con la misma regla y dejando
>    constancia del cambio. No se congela un resultado de frontera.
>
> Lo que **no** se va a hacer es mover el umbral. Está escrito desde el 17 de
> septiembre y se queda en 20.
 
### Lo que la calificación deja ver, y que vale más que el veredicto
 
Los dos extremos de la muestra, uno junto a otro:
 
| par | parecido | veredicto |
|---|---:|---|
| `congelado` / `descongelado` | **0.962** | artículos **distintos** |
| `letra` / `letras` | **0.994** | el **mismo** artículo |
 
**En esta fuente la similitud textual no separa lo que hay que separar.** La
información que distingue un artículo de otro —congelado o descongelado, con
hueso o sin hueso, primera o tercera, con sal o sin sal— viaja en palabras
cortas que casi no mueven la métrica. Y al revés: lo que sí son variantes de
escritura —plurales, conectores, abreviaturas, orden de palabras— tampoco la
mueven. Jaro-Winkler no distingue un caso del otro, y por eso el filtro de «los
números tienen que coincidir» del punto 1 resultó necesario pero no suficiente:
`Aa` contra `Aaa` en pilas y `Niña` contra `Niño` en pañales pasan el filtro de
números, se parecen en más de 0.99, y son artículos distintos.
 
Los 23 «sí» son además de un solo tipo, todos ortográficos: plural (`letra` /
`letras`), conector (`800 a 880 gr` / `800 ó 880 gr`), abreviatura (`fideo 2` /
`fideo no 2`, `355 ml` / `355 ml c/u`), unidad (`200 gr` / `200 ml`) y **orden
de palabras** (`de cerdo y pavo virginia` / `de pavo y cerdo virginia`, que
ninguna normalización une sin ordenar los tokens).
 
**Consecuencia para el diseño de T053:** el subsistema de reconciliación se
construye con un conjunto de reglas dirigidas a esas cinco formas —normalizar
plurales, conectores, abreviaturas y unidades, y ordenar tokens antes de
comparar— **y la comparación difusa encima de eso**, no en lugar de eso. El
umbral difuso se calibra contra esta muestra: tiene que unir los 23 «sí» sin
unir los 177 «no», y los pares `Aa`/`Aaa` y `Niña`/`Niño` son el caso de prueba
que dice si el umbral está demasiado flojo.
 
## Alternativas descartadas
 
**Medir H3 con los 1,730 pares de `h3-entre-cadenas.py`.** Es la medición que ya
existía y era la ruta cómoda. Se descarta porque por construcción sólo contiene
casos que la normalización resuelve: da 100% de cobertura siempre, sin importar
qué tan buena sea la reconciliación.
 
**Tomar los 200 pares al azar del catálogo completo, como dice el protocolo al
pie de la letra.** Con 1,597 artículos en el alcance, una muestra aleatoria de
pares trae casi puros pares obviamente distintos y prácticamente ningún caso
difícil: mide precisión bien y cobertura nada. La mitad por parecido existe
justamente para que el examen tenga casos donde fallar.
 
**Contar como fallo los pares que sólo difieren en `marca`.** Haría la cobertura
artificialmente baja por una decisión de diseño deliberada (ADR 002).
 
**Dejar la comparación difusa para la fase dos.** Era defendible mientras el
argumento del ADR 002 se creyera válido. Una vez visto que la muestra trae
`Mazatán`/`Mazatún`, dejarla fuera significa que esos casos nunca se
reconcilian y la cobertura tiene un techo que no depende del esfuerzo.
 
## Consecuencias
 
### Lo que cambia en el trabajo de cada quien
 
**A · plataforma de datos, semana 8 (T053).** «Reconciliación de productos
versión uno» ya no es sólo normalización determinista: lleva un paso de
comparación difusa con umbral y una tabla de diccionario con los pares
aprobados. El filtro de «los números tienen que coincidir» es la primera regla
de ese subsistema y va desde el principio.
 
**A · interfaz analítica, semana 9 (T058).** La medición de H3 se hace con el
procedimiento del punto 1 de este ADR, no con `h3-entre-cadenas.py`. Los pares
que sólo difieren en `marca` se reportan en una fila aparte de la tabla de
resultados.
 
**D · consola de observabilidad, semana 10 (T073).** La pantalla «Revisión de
Diccionario y Comparación Difusa» deja de ser una idea del wireframe y pasa a
ser requisito: es la cola donde un humano aprueba o rechaza los pares que el
umbral no resuelve solo.
 
**C1 · modelo de dominio.** Aparece una entidad que antes no estaba: el
**par aprobado** del diccionario de reconciliación, con su estado (propuesto,
aprobado, rechazado) y quién lo resolvió.
 
**Nadie toca el ADR 002.** Queda como está, con su nota de estado apuntando
aquí.
 
### Lo que este ADR deja abierto
 
**El umbral de la comparación difusa no está fijado.** Este documento decide que
la comparación difusa existe; con qué distancia y sobre qué campos se decidirá
con los datos de la calificación, en la semana 8, cuando se implemente. No se
fija a ciegas.
 
**El resultado de frontera.** La mitad por parecido dio exactamente 20 «sí»
contra un umbral de 20. La rama aplicada es la primera y el enunciado de H3 se
queda como está, pero el margen es cero: **si la calificación se revisa antes de
la semana 9, el conteo se recalcula y la rama se vuelve a evaluar.** Queda
abierto en ese sentido, no en el de estar sin decidir.
 
**Cómo se mide la cobertura y la precisión finales.** Esta calificación fija el
**patrón de referencia**, no el resultado. Los 23 «sí» son los pares que el
sistema debió unir y no unió; con eso queda el denominador que a la primera
medición le faltaba. Las cifras de cobertura y precisión se producen en la
semana 9 (T058) corriendo la reconciliación ya implementada (T053) contra esta
muestra. Lo único que se puede afirmar hoy es la tasa de omisión de la
**normalización determinista vigente** sobre el estrato difícil: **20 de cada
100** pares de alta similitud que no unió eran en realidad el mismo artículo.
 
**Un dato del estrato aleatorio que conviene tener presente.** Ahí sólo 3 de 100
resultaron el mismo artículo. Confirma que las dos mitades miden cosas distintas
y que fue correcto separarlas: sin la mitad por parecido no habría material para
medir cobertura, y sin la mitad al azar no habría con qué medir precisión.
 
## Referencias
 
- `docs/adr/001-fuente-de-datos.md` § «Sobre la hipótesis H3» — el punto abierto
  que este ADR cierra
- `docs/adr/002-identidad-del-articulo.md` § «Alternativas descartadas» — la
  línea que este ADR corrige
- `docs/datos/perfilado/h3-muestra-para-calificar.py` — construye la muestra.
  Corregido el 23 de septiembre para separar `clave` de `clave_articulo`
- `docs/datos/perfilado/h3-muestra-para-calificar.txt` — los 200 pares
  calificados, con la regla en el encabezado y las líneas `CORREGIDO` y
  `EXCEPCIÓN` por par
- `docs/datos/perfilado/h3-traspasar-calificaciones.py` — traspasa las
  calificaciones entre versiones de la muestra emparejando por clave de artículo
- `docs/adr/010-acta-de-decisiones-semana-03.md` decisiones 4 y 8 — la
  ratificación del equipo
- `docs/datos/perfilado.md` §3 — la medición y la nota de corrección
- `docs/datos/informe-perfilado-v1.md` §3 — el relato de la corrección
- `contracts/qqp-v1.yaml` → `normalizacion.reparar_interrogantes` — la
  reparación del `?` como mecanismo de reconciliación
 