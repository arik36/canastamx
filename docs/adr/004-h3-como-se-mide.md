# ADR 004 · H3 · cómo se enuncia y cómo se mide

- **Fecha:** 17 de septiembre de 2026
- **Estado:** propuesta · se ratifica en la primera reunión de la semana 3
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
> y las cifras equivalentes son **596 pares distintos de escritura, 191
> sobrevivientes**. ⚠ **CONFIRMAR** contra la salida de esa corrida antes de
> aceptar el ADR: son de la corrida, no de una remedición.

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

### Resultado de la calificación

⚠ **PENDIENTE — se llena al terminar de marcar `h3-muestra-para-calificar.txt`.**
Es lo único de este documento que depende de la calificación; todo lo anterior
ya está decidido.

| | sí (mismo artículo) | no (distintos) | sólo difieren en `marca` |
|---|---:|---:|---:|
| Mitad por parecido (100) | | | |
| Mitad al azar (100) | | | |
| **Total** | | | |

- Cobertura observada: ___ %  ·  Precisión observada: ___ %
- Rama de la tabla del punto 4 que aplica: ___
- Enunciado final de H3: ___

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

**La calificación misma.** Mientras la tabla de resultados esté vacía, este ADR
está en estado **propuesta**: fija el método y la corrección al 002, pero no
puede cerrar el enunciado de H3.

**La ratificación del equipo.** La corrección al ADR 002 toca una decisión que
se tomó en reunión con los cinco. Se lleva a la primera reunión de la semana 3
para ratificarla, aunque el método de medición sea del frente de datos.

## Referencias

- `docs/adr/001-fuente-de-datos.md` § «Sobre la hipótesis H3» — el punto abierto
  que este ADR cierra
- `docs/adr/002-identidad-del-articulo.md` § «Alternativas descartadas» — la
  línea que este ADR corrige
- `docs/datos/perfilado/h3-muestra-para-calificar.py` — construye la muestra
- `docs/datos/perfilado/h3-muestra-para-calificar.txt` — la muestra calificada
- `docs/datos/perfilado.md` §3 — la medición y la nota de corrección
- `docs/datos/informe-perfilado-v1.md` §3 — el relato de la corrección
- `contracts/qqp-v1.yaml` → `normalizacion.reparar_interrogantes` — la
  reparación del `?` como mecanismo de reconciliación
