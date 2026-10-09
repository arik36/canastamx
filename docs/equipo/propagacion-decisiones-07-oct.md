# Propagación de las decisiones del 7 de octubre

> **Qué es.** Cada decisión del 7 de octubre cambió algo que ya estaba escrito en
> otra parte. Este documento dice **qué cambió**, **por qué**, dónde ya aterrizó y
> dónde falta, con archivo y línea.
>
> **Verificado contra `main` en `ebc9de1`, el 9 de octubre de 2026.** El auditor de
> datos da 21 ✓ y 2 ⚠ sobre ese mismo estado. Lo que aquí dice «falta» se comprobó
> abriendo el archivo, no recordándolo.

---

## 1 · Por qué existe este documento

Una decisión no termina cuando se vota: termina cuando **todo lo que dependía de la
respuesta vieja dice la nueva**. El 7 de octubre se votaron catorce cosas en una
tarde (D-08 y P-01 a P-15) y tres de ellas tocan la identidad de la cuenta. Cada una
viajó a algunos archivos y se quedó corta en otros, y las que se quedan cortas no
avisan: el repositorio compila igual, el validador de contratos sigue dando 0
errores y el documento de la entrega 2 se genera igual.

Por eso el equipo necesita una sola lista. Y por eso la regla nueva del §5: **toda
decisión se cierra con la lista de los archivos que la siguen, escrita el mismo
día.**

**Una advertencia honesta sobre el «por qué».** El resultado de cada decisión está
escrito (`docs/analisis/openapi/README.md` §«Decidido en la revisión del 7 de
octubre» y `docs/equipo/decisiones-pendientes.md`), pero **el motivo no**. Lo que
sigue reconstruye el motivo a partir de los artefactos. En diciembre el asesor va a
preguntar *por qué* y nadie se va a acordar; que quede aquí es el objetivo.

---

## 2 · Las tres decisiones que tocan la integridad del proyecto

### P-13 · La cuenta no tiene nombre

**Qué cambió.** `USUARIO` pierde la columna `nombre`. La cuenta se identifica con su
correo, y donde antes se mostraba un nombre, se muestra el correo.

**Por qué.**

1. **Ningún caso de uso lo usa.** Los catorce casos de uso se revisaron: nadie
   saluda a la persona por su nombre, nadie busca una cuenta por nombre, nadie lo
   edita. Un dato que no aparece en ningún flujo es un dato que se guarda «por si
   acaso».
2. **El correo ya identifica.** `correo_electronico` es `UNIQUE NOT NULL`
   (`docs/analisis/modelo-er.md` §USUARIO). Con una llave natural que ya existe, el
   nombre no identifica nada: sería un segundo rótulo del mismo registro.
3. **Es el único dato personal que queda, y eso se puede defender.** El proyecto
   promete que *«el prototipo no cobra nada y no recopila datos de pago ni
   domicilios»*. Guardar un nombre que nada usa debilita esa promesa a cambio de
   cero funcionalidad. Sin nombre, la respuesta ante el asesor es de una línea: *el
   sistema guarda un correo y un hash de contraseña, nada más*.
4. **Un nombre cuesta.** Validarlo, mostrarlo, permitir cambiarlo (otra ruta),
   decidir si es obligatorio. El prototipo ya se había inventado uno —«Karen
   Alejandra»— y ahí se vio el costo: cada pantalla nueva inventa un dato que el
   modelo no tiene.

**Lo que P-13 obliga a decidir y todavía no se decide:** si la cuenta se muestra por
su correo, la app y la web necesitan **leerlo**, y hoy no hay por dónde. Es la nueva
**D-10** de la boleta. Ver §3.

### P-07 · La sesión lleva el rol, y la emite el dominio

**Qué cambió.** `USUARIO` gana `rol` (`CONSUMIDOR`, `ANALISTA` u `OPERADOR`), el
token lo lleva, y la web decide con él si abre el tablero o la consola. La app sólo
crea consumidores.

**Por qué.** Hay tres perfiles y dos consolas; sin rol en la sesión, la única forma
de separarlos es que cada cliente decida por su cuenta qué muestra, que es decir que
no hay control de acceso. El rol lo emite el dominio porque es el único servicio que
escribe en la base transaccional (`dominio.yaml`, `info.description`): si lo emitiera
la analítica, habría dos fuentes de verdad sobre quién es quién. Y la app no crea
analistas ni operadores porque entonces cualquiera con el APK se haría operador.

### P-14 · La alerta guarda su entidad

**Qué cambió.** `ALERTA` gana `entidad`: la que la persona tenía elegida al crearla.

**Por qué.** El precio de un artículo no existe «en general»; existe por entidad
(el precio típico es la mediana de las tiendas **de una entidad**, T031). Una alerta
sin entidad no se puede evaluar: habría que elegir una al revisarla, y la elegida
hoy no es la de ayer. Guardarla en la alerta hace la revisión determinista y deja el
rango histórico del umbral bien definido (RF-20). Para vigilar el mismo artículo en
otra entidad se crea otra alerta.

---

## 3 · Lo que P-13 abrió: por dónde viaja el correo

Con P-13, el correo deja de ser un dato de contacto y pasa a ser **la identidad de
la cuenta y el único dato personal del sistema**. Conviene saber exactamente por
dónde pasa. Esto es el estado verificado hoy:

| Tramo | Cómo viaja hoy | Archivo |
|---|---|---|
| App o web → dominio, al registrarse | En el **cuerpo** de `POST /api/v1/cuentas` (`Registro`) | `dominio.yaml` §`Registro` |
| App o web → dominio, al iniciar sesión | En el **cuerpo** de `POST /api/v1/sesiones` (`Credenciales`) | `dominio.yaml` §`Credenciales` |
| Dominio → base transaccional | `usuario.correo_electronico`, `UNIQUE NOT NULL`. Es el único lugar donde se guarda | `modelo-er.md` §USUARIO |
| Dominio → cliente, al registrarse | En la respuesta `201` (`Cuenta`: `id`, `correo`, `rol`, `fechaDeRegistro`) | `dominio.yaml` §`Cuenta` |
| Dominio → cliente, al iniciar sesión | **No viaja.** `Sesion` trae `token`, `expiraEn` y `rol` | `dominio.yaml` §`Sesion` |
| En el token | **No viaja.** El token «lleva el rol de la cuenta (P-07)» | `dominio.yaml`, esquema de seguridad `sesion` |
| Dominio → servicio de correo | El aviso de precio de CU-11 (RF-21). El servicio **está por decidir** | `arquitectura/01-contexto.dot` · `02-contenedores.dot` |
| Analítica y esquema de operación | El correo **del operador** queda en `cerrado_por` y `resuelta_por` | `analitica.yaml` §`Incidente`, §`Variante` · `esquema-de-operacion.md` §3 |

**Tres cosas buenas, que conviene no perder:** el correo nunca viaja en una ruta ni
en un parámetro de consulta —siempre en el cuerpo de un `POST`—, así que no queda en
los registros de la puerta de enlace; el token no lo lleva; y el teléfono no tiene
por qué guardarlo.

**Dos huecos:**

1. **Nadie puede leer su propia cuenta.** El inventario de vistas pide que la vista 8
   muestre *«el perfil, con el **correo** de la cuenta (no tiene nombre, P-13)»*
   (`inventario-vistas.md` §vista 8) y `diseno.md` §7 · 13 pide *«el correo y el rol
   de la sesión»* en la barra de la web. Pero el contrato del dominio no tiene una
   ruta que devuelva la cuenta: sólo `POST /cuentas` y `POST /sesiones`. Al reabrir
   la app con una sesión guardada, el cliente tiene token y rol, y **no tiene
   correo**. → **D-10**.
2. **El correo del operador vive fuera del dominio.** El esquema de operación guarda
   quién cerró un incidente como un correo. Es una copia del único dato personal en
   una base distinta, escrita por la analítica (P-08), en una capa de la que el
   proyecto dice que no tiene datos personales. → **D-11**.

Las dos salen a la boleta en lugar de resolverse en silencio: tocan el contrato que
C1 va a construir la semana que entra.

---

## 4 · Integridad · lo que hay y lo que debe haber

Verificado el 9 de octubre sobre `ebc9de1`.

| # | Archivo y línea | Qué hay | Qué debe haber | Dueño | Antes de |
|---|---|---|---|---|---|
| 1 | `services/.../domain/usuario/Usuario.java:11,14,30,47-54,64-66` | `private String nombre`, el constructor lo exige y `renombrar()` lo valida | Sin `nombre`. Con `Rol rol`, como el diagrama de clases de `modelo-dominio.md` | C1 | Semana 7 |
| 2 | `services/.../domain/UsuarioTest.java:32` | La prueba construye el usuario con `"Liseth"` como nombre | Sin ese argumento. Y una prueba que falle si `nombre` regresa | C1 | Semana 7 |
| 3 | `.github/workflows/ci.yml:64-67` | El paso «Pruebas» del trabajo Dominio está comentado | Activo. **Pero después del punto 1:** si se activa antes, la integración continua se pone verde certificando un modelo que el equipo ya cambió | B, con C1 | Semana 7 |
| 4 | `docs/analisis/casos-uso/CU-08-registrar-cuenta.md:14-21,50` | El flujo registra «correo + contraseña cifrada» y no menciona el rol | El rol `CONSUMIDOR` al crear la cuenta y el token con el rol al iniciar sesión (P-07). RF-17 y `dominio.yaml` ya lo exigen | C1 (parche listo) | 9 de octubre |
| 5 | `clients/mobile/app/(tabs)/_layout.tsx:41-46` | Tres pestañas: Búsqueda, Mi canasta y Alertas | Cuatro: Inicio, Descubrir, Canasta y Cuenta (D-01). «Mis alertas» pasa detrás de la campana y de Cuenta | C2 | Semana 7 |
| 6 | `docs/adr/007-navegacion-mobile.md:22` | «tres pestañas» en la decisión, con la nota de D-01 encima | Reescrito con las cuatro pestañas, y ratificado | C2 | 11 de octubre |
| 7 | `docs/adr/008-donde-vive-la-base.md` | El peso «~1,476 MB que pesa el recorte» sin decir qué recorte (⚠ del auditor) | La población de la cifra: corpus, recorte territorial o alcance del contrato | B | 11 de octubre |
| 8 | `docs/adr/{006,007,008,011}` | Cuatro ADR en «propuesta» (⚠ del auditor) | Ratificados o reescritos. Un ADR en propuesta que ya se sigue es una decisión sin acta | C2 (006, 007, 011) y B (008) | 11 de octubre |
| 9 | `docs/entregas/diseno.md:236-238` (§7 · 12, 13 y 14) | El prototipo muestra «Karen Alejandra», «Analista Ruiz» y cobertura 81.4% / precisión 97.3% inventadas | El correo con avatar de inicial; el correo y el rol; y «se mide en T058» o la cifra real con su población (RNF-16) | D y C2 | **Antes de capturar las figuras 13 a 20** |
| 10 | `docs/analisis/openapi/analitica.yaml` §`MotivoDeFila` | El `enum` declara ocho motivos; tres (`valor_requerido_vacio`, `largo_excedido`, `tipo_invalido`) no existen en el contrato de datos | O el contrato los declara, o el `enum` los marca como propuestos. Quien construya la cuarentena lee el contrato, no el `enum` | A | 9 de noviembre |
| 11 | `README.md:94` · `docs/equipo/README.md:101` · `cronograma.md:41` · `ciclo-de-trabajo.md:314` · `git-paso-a-paso.md:189` | «Liseth Yareth» | «Lisseth Yaret», como firma en Git | A (parche listo) | 11 de octubre |
| 12 | `docs/equipo/semanas/` y `docs/equipo/fichas/` | Sólo `semana-04`. Faltan las semanas 5 y 6 | La bitácora de las semanas 4 a 6, que es lo que pide el asesor | A o B | 9 de octubre |

**Lo que estas comprobaciones prueban y lo que no.** Probé que los archivos del
repositorio dicen lo que dicen y que el auditor pasa sobre `ebc9de1`. **No** probé
el prototipo de Figma: el punto 9 sale de `diseno.md` §7, que es la lista que el
equipo escribió el 7 de octubre, no de abrir Figma. Tampoco puedo ver si un PR está
abierto o cerrado: lo que sí vi es que **en el remoto sólo existe `main`**, así que
la rama `feat/orf-primera-llamada` de T039 (#120) **no está subida** y los `pr/83` y
`pr/84` tienen commits que no entraron a `main`. Para saber si están abiertos,
mándame `gh pr list --state open --json number,title,author`.

---

## 5 · Las medidas

Cinco, y las tres primeras cuestan minutos.

**M-1 · Toda decisión se cierra con su lista de archivos, el mismo día.** El acta de
la decisión no dice sólo el resultado: dice qué archivos lo tienen que decir y quién
los toca. La sección «Lo que estos contratos piden a otros documentos» de
`docs/analisis/openapi/README.md` ya se hizo así, y es la razón por la que la mayor
parte del 7 de octubre sí aterrizó. Se vuelve obligatoria.

**M-2 · Una decisión que abre otra no se cierra: la abre.** P-13 quitó el nombre y
dejó sin resolver cómo se lee el correo. P-08 mandó las acciones del operador a otra
base y dejó un correo ahí. Cuando una decisión deja una pregunta nueva, la pregunta
entra a la boleta ese día, con sus opciones y sus consecuencias. Hoy entran D-09,
D-10 y D-11.

**M-3 · El código no se queda atrás en silencio: la prueba lo delata.** Cada
decisión que toca el modelo se cierra con una prueba que falla si la decisión se
revierte. Para P-13: una prueba que falle si `Usuario` vuelve a tener `nombre`. Es
lo que convierte una decisión en algo verificable, y es justo lo que la hipótesis H1
hace con los datos. La integración continua se activa **después** de que el código
siga la decisión, nunca antes.

**M-4 · El prototipo es un artefacto con dueño, no un dibujo.** Las pantallas
inventan datos que el modelo no tiene: un nombre, una foto, una cobertura de 81.4%.
Mientras el prototipo sea la evidencia que se entrega, cada punto de `diseno.md` §7
es una tarea del tablero, y se revisa antes de capturar.

**M-5 · El auditor se corre antes de cada entrega y de cada cierre de fase.**
`python auditar_datos.py <carpeta>` sobre el commit que se entrega, y el resultado
se pega en la ficha de la semana. Hoy: 21 ✓ y 2 ⚠, y los dos ⚠ están en esta tabla
(puntos 7 y 8).

---

## 6 · Antes de que cierre la semana 6 · el 11 de octubre

La fase 3 arranca el 12 de octubre y la regla es que no se construye sobre una
decisión sin acta.

| Quién | Qué | Por qué ahora |
|---|---|---|
| **D y C2** | Puntos 12, 13 y 14 de `diseno.md` §7 en Figma, y luego las 8 capturas (figuras 13 a 20 del Word están vacías) | Se entrega hoy, y la figura 20 es la pantalla de Cuenta |
| **A** | Portada, campos e índices del Word; subirlo a Drive; `docs/entregas/2026-10-09/`; bitácora de las semanas 4 a 6 | Es la entrega 2 |
| **C1 y B** | Votar **D-09** (servicio de correo) | Sin eso, el notificador de CU-11 se construye dos veces |
| **C1, con C2 y D** | Votar **D-10** (cómo se lee el correo de la cuenta) | C1 publica `dominio.yaml` la semana que entra; una ruta nueva después es romper el contrato |
| **A y B** | Votar **D-11** (con qué se registra quién cerró un incidente) | El esquema de operación se crea en la base en la fase 3 |
| **C2** | Reescribir el ADR 007 con las cuatro pestañas; ratificar 006 y 011 | Tres de los cuatro ⚠ del auditor son suyos, y la app se construye sobre ellos |
| **B** | Población del peso del ADR 008 y ratificarlo | Es el cuarto ⚠ |
| **A** | ADR 016 a 019 (Dagster, FastAPI, Pandera, dbt) | La fase 3 empieza con esas cuatro herramientas y ninguna tiene acta |

---

## 7 · De dónde sale cada cosa

| Qué | Dónde |
|---|---|
| El resultado de cada decisión | `docs/analisis/openapi/README.md` · `docs/equipo/decisiones-pendientes.md` |
| Las decisiones por votar | `docs/equipo/decisiones-pendientes.md` §«Para decidir» |
| El estado de los datos | `auditar_datos.py`, 23 comprobaciones, sobre el commit que se entrega |
| Lo que el prototipo todavía no cumple | `docs/entregas/diseno.md` §7 |
