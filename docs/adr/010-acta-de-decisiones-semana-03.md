# ADR 010 · Acta de la boleta de decisiones · semana 3

- **Fecha:** 23 de septiembre de 2026
- **Estado:** aceptada
- **Participantes:** votaron los cinco — Ariadne (A), Ari Adair (B), Liseth (C1),
  Oscar (C2), Karen (D)
- **Cómo se decidió:** boleta escrita, `docs/equipo/decisiones-pendientes.md`,
  con las opciones y sus consecuencias redactadas antes de votar

## Por qué este ADR existe y no son doce

La convención del proyecto es un ADR por decisión, y se respeta: **seis de estas
doce se van a un ADR que ya existe.** Este documento es el **acta** —el registro
de quién votó qué y con qué margen— y cada ADR de destino lo cita en vez de
repetir la votación.

Un ADR dice *qué se decidió y por qué*. El acta dice *quiénes lo decidieron*. Son
cosas distintas y las dos hacen falta para que la decisión se pueda auditar
después, que es lo que este proyecto le exige a sus datos y tiene que exigirse a
sí mismo.

## Resultados

| # | Decisión | A | B | C1 | C2 | D | **Resultado** | Margen |
|---|---|:-:|:-:|:-:|:-:|:-:|---|---|
| 1 | Horario fijo de reunión | C | C | B | C | D | **C · viernes 6:00 pm** | 3 – 1 – 1 |
| 2 | Almacenamiento de objetos | A | A | A | A | A | **A · MinIO vía Quay.io** | unánime |
| 3 | La base desplegada | A | A | A | A | A | **A · en contenedor** | unánime |
| 4 | Comparación difusa | A | A | A | A | A | **A · entra al alcance** | unánime |
| 5a | Largo de contraseña | B | C | C | C | A | **C · 8 + mayúscula + número** | 3 – 1 – 1 |
| 5b | Validez del umbral | B | B | B | B | B | **B · dentro del rango histórico** | unánime |
| 5c | La alerta dispara con | B | B | B | B | B | **B · menor o igual (`<=`)** | unánime |
| 6 | Fotos de los artículos | A | A | A | A | A,B | **A · ícono genérico** | 4 claros ⚠ |
| 7 | Qué se oculta | ABC | ABC | ABC | ABC | A,E | **A+B+C · alcohol y tabaco** | 4 – 1 ⚠ |
| 8 | Enunciado de H3 | A | A | A | A | C | **A · la regla tal como está** | 4 – 1 |
| 9 | Compuerta de frescura | C | C | C | C | B | **C · avisar y bloquear** | 4 – 1 |
| 10 | Nombre del archivo del ADR 005 | B | B | B | B | B | **B · corregir el issue** | unánime |

> **Nadie llenó los comentarios.** Eso significa que de las cinco decisiones que
> no fueron unánimes, **no quedó registrado por qué votó distinto quien votó
> distinto.** Es información que se pierde: si en noviembre alguien pregunta «¿y
> por qué no hicimos lo otro?», la respuesta es «nadie escribió». Para la próxima
> boleta, que el voto en minoría lleve una línea — es lo que más vale del
> ejercicio.

## Dos votos que hay que aclarar antes de ejecutar

**Decisión 6 · D marcó «A, B».** Las opciones eran excluyentes: A es ícono
genérico, B es banco de imágenes externo. La lectura razonable es «ícono genérico
ahora, banco de imágenes si sobra tiempo», y así se va a ejecutar salvo que Karen
diga otra cosa. **El resultado no cambia**: A gana con cuatro votos limpios.

**Decisión 7 · D marcó «A, E».** A es *ocultar cerveza* y E es *no ocultar nada*:
son contradictorias. **El resultado tampoco cambia** —cuatro votos idénticos por
A+B+C—, pero conviene saber si Karen quiso decir «sólo cerveza» o «nada», porque
es la persona que implementa el filtro junto con C2.

Ninguna de las dos bloquea nada esta semana.

---

## 1 · Horario fijo · **viernes 6:00 pm**

Queda en `docs/equipo/como-trabajamos.md`. Con el mínimo que no se votó: 45
minutos, cámara encendida, y quien no pueda avisa antes, no el mismo día.

**Un riesgo que hay que anotar, porque es el que motivó la decisión.** La opción
C se eligió sabiendo que decidir el día de entrega es lo que ya falló una vez. De
las cinco entregas del semestre, **sólo una cae en viernes: la E2 del 9 de
octubre**. Las otras cuatro son miércoles.

**Acuerdo derivado, para que no se repita lo de la semana 2:** en la semana de la
E2, la reunión se mueve al **miércoles 7 de octubre**. No se cancela, se adelanta.

## 2 · Almacenamiento de objetos · **seguimos con MinIO, vía Quay.io**

Unánime. Va al **ADR 009**, que pasa de propuesta a aceptada con esta fecha.

Lo que arranca de inmediato, y no se vota porque es higiene:

- Fijar la imagen con versión y digest. `latest` fue exactamente lo que tronó.
- Renombrar `MINIO_*` a `S3_*` y agregar `S3_ENDPOINT`.
- **Guardar una copia de las imágenes** con `docker save`, una por arquitectura
  —`amd64` para las laptops, `arm64` para la máquina de Oracle—, al Drive del
  equipo. Si Quay también las quita, se recuperan con `docker load`.
- **MinIO no se expone a internet.** Ni puertos publicados hacia afuera ni regla
  de Traefik en el punto de entrada público. Si hace falta la consola en la
  máquina desplegada, túnel SSH. Esto aplica con imagen congelada o sin ella.

## 3 · La base desplegada · **PostgreSQL en contenedor**

Unánime. Va al **ADR 008**, que tiene que resolver su contradicción interna: el
documento citaba el protocolo para descartar Supabase y luego proponía instalación
nativa. Con esta decisión el ADR queda coherente consigo mismo.

**Presupuesto de memoria para los 12 GB**, que es lo que al ADR 008 le faltaba:

| Servicio | Memoria |
|---|---|
| Sistema operativo + Docker | ~1.0 GB |
| `postgres-analytics` · `shared_buffers` 2 GB | ~3.0 GB |
| `postgres-oltp` · `shared_buffers` 256 MB | ~0.7 GB |
| MinIO | ~0.5 GB |
| Servicio de dominio · JVM con `-Xmx512m` | ~0.8 GB |
| API analítica | ~0.5 GB |
| Traefik + web estática | ~0.2 GB |
| **Comprometido** | **~6.7 GB** |
| **Libre para caché de disco** | **~5.3 GB** |

Y cuatro cuidados que van en las consecuencias del ADR 008: **límite de memoria
por contenedor** —sin él, uno que se desboque mata a los demás—, **no dejar
`shared_buffers` por omisión ni al 25% en las dos bases**, **agregar swap** de 2
a 4 GB como red de seguridad, y **respaldos de `pg_dump` fuera de la máquina**.

## 4 · La comparación difusa entra al alcance

Unánime, y con los cinco sabiendo lo que le cuesta a cada quien. Va al **ADR
004**, y el **ADR 002** conserva su nota de estado apuntando ahí.

Lo que le aparece a cada uno, ya no como propuesta:

| Quién | Qué |
|---|---|
| **C1** | Una entidad nueva en el modelo: el par aprobado del diccionario, con su estado —propuesto, aprobado, rechazado— y quién lo resolvió |
| **D** | La pantalla «Revisión de Diccionario» deja de ser idea del wireframe y pasa a requisito |
| **A** | T053 lleva un paso de comparación difusa con umbral y tabla de diccionario. El filtro de «los números tienen que coincidir» va desde el principio |

## 5 · Las tres reglas del modelo de dominio

Van a `docs/analisis/modelo-dominio.md`, que con esto sale de «borrador».

**5a · Contraseña: mínimo 8 caracteres, con al menos una mayúscula y un número.**
Se eligió por 3 de 5. La objeción conocida queda anotada: reglas de composición
como ésta empujan a la gente hacia `Password1`, y lo que de verdad mueve la aguja
es rechazar las contraseñas más usadas. Eso no se descarta, se deja como mejora
posible; la regla votada es la que se implementa.

**5b · Un umbral es válido si cae dentro del rango histórico del artículo.**
Unánime. Implica que crear una alerta consulta el histórico: **C1 necesita ese
dato de la interfaz analítica**, o sea de A. Es una dependencia nueva entre
frentes y hay que anotarla en el mapa.

**5c · La alerta dispara con menor o igual.** Unánime. Quien escribe «avísame si
baja de $50» se entera también a los $50 exactos.

## 6 · Fotos · **ícono genérico por catálogo**

No se va a mantener un mapeo de 1,597 artículos a imágenes. Las fotos que hoy
tienen los wireframes salen, o se marcan explícitamente como ilustrativas en las
pantallas de la demostración.

**Consecuencia para D:** hay que definir cinco íconos, uno por catálogo, y
reemplazar las fotos de banco en las tarjetas de artículo.

## 7 · Se ocultan por omisión · **cerveza, vinos y licores, cigarrillos**

64,991 filas, el 2.44% del alcance. **Los productos navideños se quedan
visibles.**

> **Esto no cambia qué se ingiere.** El contrato sigue ingiriendo todo `Basicos`,
> porque el protocolo compromete respetar la clasificación de la fuente. Es el
> filtro por omisión de la pantalla, y el usuario lo quita con un clic.

El criterio que sostiene la decisión es **externo y citable**: la canasta básica
alimentaria de CONEVAL no incluye bebidas alcohólicas, y el tabaco no es
alimento. Por eso la lista es corta: cada cosa que se le agregue por gusto propio
la debilita.

**Consecuencia para C2 y D:** el filtro va con un texto visible que diga por qué,
del tipo *«Se ocultan bebidas alcohólicas y tabaco, que la canasta básica de
CONEVAL no incluye. Mostrar todo»*. Sin ese texto es paternalismo; con él es
transparencia.

**Y un beneficio para H4:** con la lista escrita, el índice de canasta se puede
reportar con y sin alcohol al compararlo contra el INPC, y decir cuál es cuál.

## 8 · H3 se mide con la regla ya escrita

4 de 5. Se aplica tal cual está en el **ADR 004**: si la mitad por parecido da 20
o más «sí», H3 se mide como está enunciada —cobertura ≥85%, precisión ≥90%—; si
da menos, se reenuncia sobre reconciliar presentaciones dentro de un mismo
producto.

Lo que falta no es la decisión sino el dato: terminar de calificar los 200 pares.
Responsable A.

## 9 · Frescura · **avisa a los 20 días, bloquea a los 45**

4 de 5. Va al contrato, `contracts/qqp-v1.yaml` → `frescura`.

**Y con esta decisión se cierra otra que estaba implícita: el corpus se congela
en la última quincena disponible, 2026-07-Q2.** La verificación del 23 de
septiembre confirmó que eso es lo último que publica la fuente.

Eso quita una preocupación que valía la pena aclarar: **no vamos a estar
recibiendo datos nuevos ni repitiendo el perfilado.** El perfilado fue
exploración y ya terminó; produjo el contrato, y de ahí en adelante el contrato es
el que trabaja. La ingesta corre cuando se le dispara, no en un reloj.

**La compuerta se demuestra por inyección, no por espera.** El experimento de la
semana 12 ya inyecta cinco tipologías de falla a propósito; **la frescura es la
sexta**, y se mide igual: ¿la detectó? ¿en cuánto tiempo? ¿la contuvo?

> **Trampa técnica que hay que resolver al implementarla.** Si el corpus está
> congelado en julio y la compuerta compara contra la fecha de hoy, **rechazaría
> el corpus entero**. La frescura tiene que medirse contra una **fecha de
> referencia de la corrida**, que es un parámetro: en operación normal es la
> fecha actual; en reproducción histórica y en el experimento, se fija. Si esto
> no queda escrito así en el contrato, la compuerta es inutilizable.

## 10 · El archivo del ADR 005

Se corrige el issue del tablero para que cite `005-recorte-de-catalogos.md`. El
archivo no se renombra.

**Y dos acuerdos que no se votaron, sólo se confirman:**

- **Numeración de ADR.** 006 y 007 son de móvil. La base desplegada es el **008**,
  el almacenamiento de objetos el **009** y esta acta el **010**.
- **Acta del ADR 005.** Su encabezado dice «aceptada» sin decir dónde. Anotar cómo
  y cuándo se recogió esa aceptación.

---

## A dónde va cada decisión

| # | Se registra en |
|---|---|
| 1 | `docs/equipo/como-trabajamos.md` |
| 2 | `docs/adr/009-almacenamiento-de-objetos.md` → aceptada |
| 3 | `docs/adr/008-donde-vive-la-base.md` → aceptada, con el presupuesto de memoria |
| 4, 8 | `docs/adr/004-h3-como-se-mide.md` → aceptada |
| 5a, 5b, 5c | `docs/analisis/modelo-dominio.md` → sale de borrador |
| 6, 7 | este ADR, y `docs/analisis/inventario-vistas.md` |
| 9 | `contracts/qqp-v1.yaml` → `frescura` |
| 10 | el issue del tablero |

## Lo que esta votación deja abierto

- Aclarar los dos votos dobles de D, decisiones 6 y 7.
- Fijar los dos umbrales de la frescura —20 y 45 días— en el contrato, con la
  fecha de referencia como parámetro. · **A**
- Anotar la dependencia nueva de la 5b: C1 necesita el rango histórico del
  artículo, que lo da la interfaz analítica de A. Va al mapa de dependencias.
- Poner una línea de justificación en los votos de minoría de la próxima boleta.
