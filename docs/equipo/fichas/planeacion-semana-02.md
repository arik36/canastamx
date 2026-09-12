# Semana 2 · lunes 14 a miércoles 16 de septiembre

**Tres días.** El jueves 17 y el viernes 18 no llevan desarrollo nuevo: son la
consolidación y la **entrega del 18**. Lo que no cierre el miércoles 16 por la
noche, no entra.

**Lo que cambió desde el viernes:** las cuatro decisiones que bloqueaban el
trabajo ya están tomadas, y están en `docs/adr/001-fuente-de-datos.md` y
`docs/adr/002-identidad-del-articulo.md`.

**La tarea nueva de cada quien sigue siendo la del cronograma**, sin cambios.
Lo que se agrega encima son dos cosas, y conviene no fingir que no pesan:

- **Los pendientes de la semana 1**, que están en
  `docs/equipo/correcciones-por-integrante.md`.
- **Tres cosas que salieron al escribir los ADR** y no estaban en el
  cronograma: dos mediciones que A tiene que correr, un ADR corto que C1 tiene
  que escribir, y una comprobación de infraestructura que hace B con A. Suman
  poco, pero suman.

**Tres decisiones quedaron abiertas** y se cierran en la reunión del miércoles
16: la enmienda del descarte silencioso, la clave de fila del contrato y el
recorte de productos. Están al final, con su agenda.

> **Una de ellas tiene un problema de orden:** A escribe el contrato el lunes y
> la clave de fila no se ratifica hasta el miércoles. **No hay que esperar al
> miércoles.** A publica el lunes en el chat el número medido y la clave que
> propone; si nadie objeta en el día, se da por buena y el miércoles sólo se
> registra. Bloquear una semana de trabajo por una ratificación de dos minutos
> sería el error caro.

---

## Lo primero, el lunes temprano: cerrar lo que quedó abierto

Tres pendientes de la semana 1 **bloquean a otras personas** y por eso van
antes que la tarea de la semana. Están explicados uno por uno en
`docs/equipo/correcciones-por-integrante.md`.

| Quién | Qué | A quién bloquea |
|---|---|---|
| **C1** | Deshacer la carpeta anidada `services/domain-service/domain-service/` | A todos. Mientras esté así, la canalización dice «verde» sin compilar nada |
| **B** | Arreglar el guardián de la canalización para que distinga «no existe el pom» de «existe pero en otro lado» | A todos, por lo mismo |
| **C2** | Subir el proyecto de Expo a `clients/mobile/` | A sí mismo: la tarea de esta semana se construye encima |

**Lo demás de `correcciones-por-integrante.md`** —el healthcheck de MinIO, el
comentario de Traefik, las tablas del modelo de dominio, el enlace de Figma— no
bloquea a nadie, pero tiene que estar cerrado el miércoles.

---

## A · Ariadne — contrato de datos

**Tarea del cronograma:** contrato de datos versión uno para QQP en YAML —
columnas, tipos, obligatoriedad, rangos y umbral de frescura. Queda en
`contracts/`.

**Lunes, antes de escribir una línea del contrato: correr las dos mediciones.**
Los dos guiones ya están escritos y probados.

```bash
python docs/datos/perfilado/medir-decisiones.py
python docs/datos/perfilado/h3-entre-cadenas.py
```

Del primero salen cinco números que el contrato necesita y hoy no existen:

1. **Cuántas filas tiene el recorte de siete entidades.** Es lo que corrige el
   compromiso del protocolo de «dos a cuatro millones».
2. **Si cabe en Supabase.** Se descartó por los 21 millones, pero nadie ha
   pesado las siete entidades. Si no cabe, hay que decidir a qué se migra, y eso
   es otro ADR.
3. **Qué clave de fila deja menos duplicados.** El ADR 002 propone
   `producto` + `presentacion` + `marca` + `nombre_comercial` + `direccion` +
   `fecha_registro`. El guión dice cuántas filas legítimas rechazaría cada
   candidata. **Ninguna va a dar cero** —la fuente trae 301 duplicados exactos
   de captura—, así que la pregunta es cuál deja menos y si ese resto se maneja
   como rechazo o como deduplicación en la ingesta.
4. **Cuántos artículos hay en `producto` + `presentacion`.** Corrige el «~6,000»
   mal puesto en `perfilado.md` §3: no puede haber más artículos con dos
   columnas que con tres.
5. **Los 16 valores de `catalogo`, con su precio mediano.** Es la lista con la
   que se decide el recorte de productos el miércoles.

**Lo que el ADR 002 obliga a poner en el contrato y no estaba previsto:**

- La **clave de fila lleva `marca`**, aunque la identidad del artículo no. Son
  dos claves distintas y hacen dos trabajos distintos. Si el contrato usa la de
  artículo, la compuerta de calidad manda a cuarentena millones de filas buenas
  el día de la primera ingesta.
- **Regla de normalización de `marca`:** `S/m` y `S/M` colapsan a un solo
  literal. Hay que decidir cuál y escribirlo. Sin esa regla, la categoría
  «genérico» son dos categorías.
- **Las 15 columnas del diccionario, y sólo ésas.** `folio`, `cv_producto` y
  `cv_marca` no entran.
- **`precio`** sin regla de centinela: se buscaron con tres detectores y no hay.
  Sí van las reglas de «no nulo», «mayor que cero» y el rango medido.

**Lo demás de A —corregir el protocolo, cerrar el informe v1, escribir el
ADR 004 de H3— es de la semana 3**, jueves 17 y viernes 18. No cabe esta semana
y no hace falta que quepa.

---

## B · Ari Adair — estabilizar, que es su tarea

**El cronograma no le da tarea nueva, y es deliberado:** B es quien tiene que
dejar la canalización estable y el `README.md` verificable para la entrega del
18, y eso se hace revisando lo que ya existe, no agregando.

Su semana es entonces exactamente esto:

1. **El guardián de la canalización** (corrección B-1). Lo urgente del lunes.
2. **El healthcheck de MinIO y el comentario de Traefik** (B-2, B-3).
3. **La guía de arranque verificada**: otro integrante clona en máquina limpia y
   levanta sin preguntar nada. Es tarea de la semana 3, pero se prepara ahora.
4. **Con A: comprobar si Supabase aguanta las siete entidades.** Sale del guión
   de A; la decisión de infraestructura es de B.

**Lo de la protección de `main` es de A, no de B** —el cronograma se la asigna a
ella el lunes 7, junto con la estructura del repositorio—, y además
`docs/equipo/tablero-github.md` dice que **hoy no se puede**: GitHub no cobra
por proteger ramas en repositorios públicos, pero sí en los privados de cuenta
personal. **No se pone como casilla a cerrar el miércoles.** Lo que sí cabe esta
semana es que A decida entre las tres salidas —hacer el repositorio público,
esperar al GitHub Student Pack que B ya solicitó, o sostenerlo por acuerdo y
auditoría— y lo deje escrito. · **A · miércoles 16**.

**Y un acuerdo de proceso que hay que cerrar esta semana.** En la auditoría de
`main` aparecieron commits que parecían haber entrado sin solicitud, y no fue
así: la solicitud #55 existió, pero se cerró con el botón *«Create a merge
commit»* en lugar de *«Squash and merge»*. El comando de auditoría busca
mensajes que terminan en `(#número)`, que es la firma que deja el squash; un
merge normal escribe `Merge pull request #N from rama` y no coincide, así que
sale marcado aunque todo se haya hecho bien.

> **Acuerdo:** de aquí en adelante, **todas las solicitudes se cierran con
> «Squash and merge»**. No es cosmético: es lo que mantiene la auditoría
> confiable, y la auditoría es evidencia para la entrega.

**Y lo que sí hay que revisar de verdad:** si la solicitud #55 fue aprobada por
alguien distinto de quien la escribió. Eso el `git log` no lo dice.

```bash
gh pr view 55 --json author,mergedBy,reviews
```

Si nadie la revisó, el problema no es el botón: es que se saltó la revisión
cruzada. · **B · lunes**.

---

## C1 · Liseth — cerrar el modelo de dominio

**Tarea del cronograma:** cerrar el modelo de dominio —atributos de cada entidad
y reglas de negocio dentro del agregado—, estructurar el servicio en capas e
implementar **Usuario** y **Canasta** con sus reglas.

**Antes de eso, el lunes:** deshacer la carpeta anidada. Los comandos exactos
están en `correcciones-por-integrante.md`, sección C1-1.

**Lo que el ADR 002 cambia en el modelo, y conviene mirar antes de implementar:**

El artículo se identifica por **`producto` + `presentacion`**. La **marca no
forma parte de la identidad**: es un atributo del registro de precio, no del
artículo.

> Concretamente: `Leche Ultrapasteurizada · 1 L` es **un** artículo. Que la haya
> de Lala a $25 y de Alpura a $27 en la misma tienda el mismo día no son dos
> artículos: son **dos precios del mismo artículo**, y la marca es lo que
> distingue un precio del otro.

Si el modelo ya estaba escrito con la marca dentro de la identidad, hay que
corregirlo **antes** de implementar Usuario y Canasta. Después cuesta el triple,
porque ya hay código encima.

**Y el ADR de Spring Boot** (corrección C1-4): `docs/adr/003-version-de-spring-boot.md`.
Media cuartilla. Vale igual si la conclusión es «se tomó lo que venía por
omisión y lo confirmamos».

**Las tablas del modelo de dominio** (C1-2) y los tres detalles chicos (C1-3)
también cierran esta semana.

---

## C2 · Oscar — navegación de la app

**Tarea del cronograma:** navegación completa con las cuatro pantallas vacías —
búsqueda, detalle, mi canasta, alertas. Queda en `clients/mobile/`.

**El lunes primero:** subir el proyecto de Expo. Hoy no está en el repositorio y
la tarea de esta semana se construye encima (corrección C2-2). Si algo se
atoró, decirlo el lunes por la mañana en el chat, no el miércoles.

**Lo que conviene tener en la cabeza al armar las pantallas**, aunque se
implemente hasta las semanas 7 a 9:

- La pantalla de **búsqueda** devuelve **artículos**, que son `producto` +
  `presentacion`. No productos sueltos.
- Sobre esos resultados el usuario **ordena y filtra por marca y por precio**,
  de menor a mayor y al revés.
- Los **genéricos (`S/m`) van al final** en el orden por omisión.

No hay que construirlo esta semana. Sí conviene que los nombres de las pantallas
y de los componentes digan «artículo» donde el ADR dice artículo, para no tener
que renombrar todo en octubre.

---

## D · Karen — las ocho vistas

**Tarea del cronograma:** sistema de diseño mínimo en Figma —paleta, tipografía
y componentes base— aplicado a los wireframes existentes, más los wireframes de
las ocho vistas.

**Hay que decirlo con claridad: esta tarea viene encima de la semana 1, que
quedó en blanco.** El inventario de vistas es una plantilla vacía y el enlace de
Figma no está en el README. Dos semanas de trabajo en tres días no salen.

**Lo que sigue es una propuesta de orden, no una decisión.** El cronograma dice
que *«no se recorta ninguna función del proyecto»*, así que **degradar una parte
de esta tarea a opcional no lo decide este documento: lo decide el equipo el
miércoles 16**, o antes si Karen lo plantea en el chat. Se escribe aquí para que
llegue planteado y no se descubra el miércoles.

**El orden propuesto:**

1. **El inventario de las ocho vistas** (`docs/analisis/inventario-vistas.md`).
   Una línea de contenido por vista. Son veinte minutos y es el guion de todo lo
   demás: sin él, los wireframes se hacen a ciegas.
2. **Los ocho wireframes.** Es el grueso, y es lo que la semana 3 necesita para
   armar el prototipo navegable, que es lo que se presenta el 18.
3. **El sistema de diseño** —paleta, tipografía, espaciados— **aplicado sólo si
   sobra tiempo.** Un prototipo navegable con wireframes grises se presenta; uno
   con paleta bonita y tres pantallas no.
4. **El enlace de Figma en el README** (corrección D-2). Dos minutos, y sin él
   nadie puede ver nada de lo anterior.

**Por dónde empezar el inventario, si cuesta arrancar:** por la **consola de
observabilidad**. Es la única vista para la que ya hay contenido real medido
—tres incidentes concretos del perfilado: la corrupción masiva de junio de 2026,
la deriva de esquema de las tres columnas, y la tabla de cuarentena— y es más
fácil inventar una vista cuando ya sabes qué va adentro.

**Y si algo está atorado, decirlo el lunes.** No es un problema; que se sepa el
miércoles sí lo es.

---

## Miércoles 16 · reunión de cierre, 45 minutos

Es la reunión semanal, que esta semana cae el miércoles porque es el último día
hábil antes de la consolidación. Cinco puntos, y todos vienen preparados:

**1 · Ratificar el descarte de las columnas extra (5 min).** El viernes se
decidió no ingerir `folio`, `cv_producto` y `cv_marca`, y descartarlas **en
silencio**. La primera mitad no está en discusión. La segunda tiene una tensión
con el objeto de investigación del proyecto —contratos, compuertas y
**observabilidad**— porque una columna que aparece en junio y desaparece en
julio es justamente un incidente de deriva de esquema, y es el único ejemplo
real que tiene el proyecto. La enmienda propuesta está al final del ADR 001 y
cuesta un renglón: no ingerirlas **pero dejar aviso**. Se ratifica o se enmienda
ahí, y no se edita el ADR: si cambia, se anota como ADR 001-bis.

**2 · Ratificar la clave de fila del contrato (5 min).** El viernes se decidió
qué cuenta como el mismo artículo. La clave que usa la compuerta de calidad es
otra cosa y no se votó, pero A la necesita para escribir el contrato. Está en el
ADR 002, punto 4, con el número medido detrás.

**3 · Decidir el recorte de productos (15 min).** Es el punto nuevo, y el más
importante de los tres. El protocolo compromete un *«recorte de productos a la
canasta básica, conforme a la clasificación de productos de consumo generalizado
de la fuente»*, y **nadie decidió nada el viernes**. Hoy el corpus trae
celulares, lavadoras y pantallas de televisión junto al kilo de tortilla, y el
proyecto se llama *plataforma de precios de canasta básica*.

La clasificación de la fuente **es la columna `catalogo`**, con 16 valores. A
lleva la lista impresa con el volumen y el precio mediano de cada uno. La
decisión es: **cuáles de los 16 entran.** Un catálogo con mediana de cientos de
pesos no es canasta básica, se llame como se llame. → **ADR 005**.

**4 · Cómo queda la tarea de D (5 min).** Su semana 1 quedó en blanco y la tarea
de esta semana viene encima. Decidir en grupo qué se prioriza y qué se corre a
la semana 3, en lugar de que cada quien lo suponga.

**5 · Cargar la semana 3 al tablero (5 min)** y confirmar que el **horario fijo
de la reunión semanal** está en el calendario de los cinco. Se acordó en la
semana 1 y conviene comprobar que quedó.

Los minutos restantes: vuelta de mesa, dos por persona, qué queda abierto para
el 18.

---

## Numeración de ADR, para que no choquen

| | Tema | Quién | Estado |
|---|---|---|---|
| **001** | Fuente de datos y recorte | A | aceptada |
| **002** | Identidad del artículo | A | aceptada |
| **003** | Versión de Spring Boot | C1 | por escribir · semana 2 |
| **004** | H3 · cómo se enuncia y cómo se mide | A | por escribir · antes del 18 |
| **005** | Recorte de productos · qué catálogos son canasta básica | A | se decide el miércoles 16 |
| 006+ | libre | | |

---

## Lista de verificación · miércoles 16 por la noche

- [ ] La canalización compila de verdad el servicio de dominio, y falla si no encuentra el `pom.xml`
- [ ] `services/domain-service/` sin carpeta anidada
- [ ] El equipo cerrando solicitudes con **Squash and merge**
- [ ] Revisada la aprobación de la solicitud #55
- [ ] Decidido y escrito qué se hace con la protección de `main`, que hoy no se puede activar
- [ ] `contracts/` con el contrato de datos versión uno, con la clave de fila medida
- [ ] Corridos `medir-decisiones.py` y `h3-entre-cadenas.py`, con sus cifras anotadas
- [ ] Decidido el recorte de productos, y `docs/adr/005-recorte-de-productos.md` escrito
- [ ] Modelo de dominio cerrado, con **Artículo = producto + presentación** y marca como atributo
- [ ] Usuario y Canasta implementados
- [ ] `docs/adr/003-version-de-spring-boot.md` escrito
- [ ] Proyecto de Expo en el repositorio, con las cuatro pantallas y la navegación
- [ ] `docs/analisis/inventario-vistas.md` lleno
- [ ] Los ocho wireframes en Figma, con el enlace en el `README.md`
- [ ] Los puntos abiertos de los ADR 001 y 002 ratificados o enmendados
- [ ] Tablero con las tareas de la semana 3 y horario fijo de reunión confirmado
