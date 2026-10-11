# Fichas · semana 6 del tablero · lunes 12 al domingo 18 de octubre

> **Numeración.** Ésta es la **semana 6 del tablero** y la **semana 7 del
> cronograma**: el cronograma cuenta la entrega del 18 de septiembre como semana
> propia y el tablero no. La equivalencia está en `docs/equipo/cronograma.md`. **En
> los mensajes usamos fechas, no números de semana.**
>
> **Mismo formato que la semana 4,** porque funcionó. Cada ficha trae, en este
> orden: el nombre de tu rama, de qué depende, los términos raros explicados, el
> paso a paso, cómo se ve terminado y **cómo lo compruebas tú mismo** sin
> preguntarle a nadie.
>
> **Las tarjetas del tablero salen de `docs/equipo/semanas/semana-06.json`**, con
> `infra/scripts/sembrar-semana.py`. Los identificadores siguen la serie: T041 y
> T042 fueron la semana de la entrega, y las cinco de esta semana son **T043 a
> T047**.
>
> Si algo no se entiende, di **cuál sección** de cuál ficha.

## Arranca la construcción

Hasta el viernes 9 el proyecto produjo documentos. **Desde el lunes 12 produce
código, y el documento de análisis pasa a ser el contrato contra el que se
construye.** Eso cambia una cosa en la forma de trabajar: cuando el código y el
documento no coincidan, **no elijas en silencio**. Dilo, y se corrige el que esté
mal, con su solicitud de cambios.

## Lo que cambió antes de empezar

- **Las decisiones del 7 de octubre ya están propagadas** a los documentos:
  requerimientos, modelo entidad-relación, modelo de dominio, los dos contratos
  OpenAPI, el inventario de vistas y la navegación. El rastro completo, con archivo
  y línea, está en `docs/equipo/propagacion-decisiones-07-oct.md`.
- **La cuenta no tiene nombre (P-13)** y **la sesión lleva el rol (P-07)**. Eso toca
  a C1 en el código, a C2 en la pantalla de acceso y a D en la barra de la web.
- **Entraron cuatro ADR:** 016 Dagster (con fecha de salida el 25 de octubre), 017
  FastAPI, 018 Pandera y 019, que **pospone dbt** y mueve su revisión al 2 de
  noviembre. La fila del 19 al 25 de octubre del cronograma ya dice eso.
- **La integración continua tiene ruff anclado en 0.17.0.** El día que salió esa
  versión, una regla nueva puso en rojo tres líneas que llevaban ocho días sin
  tocarse. Si vuelve a pasar con otra herramienta, es lo mismo: se ancla la versión,
  no se parchea la prisa.
- **Las capturas del prototipo que se entregaron son las de antes de la
  corrección.** Al asesor se le explicó qué cambia. Las corregidas entran en la
  entrega del 4 de noviembre.

## La semana de un vistazo

| | mié 14 | vie 16 | dom 18 |
|---|---|---|---|
| **A** · Ariadne | Dagster: un activo particionado que corre | Pandera generado desde el contrato | Ingesta de punta a punta hasta la capa cruda |
| **B** · Ari Adair | Las tres suites corriendo en la CI | `redocly lint` en la CI | Guion de carga de datos semilla |
| **C1** · Liss | **Cuenta sin nombre, con rol, y el token** | Registro e inicio de sesión reales | Rutas de canasta |
| **C2** · Oscar | Las cuatro pestañas | Pantalla de acceso maquetada | Acceso conectado al dominio de C1 |
| **D** · Karen | Estructura de la web y rutas | Acceso y navegación | Barra lateral con correo y rol |

**La fecha límite oficial es el domingo 18 para todas.** Los días de la tabla están
puestos para que lo que desbloquea a otro salga primero:

- **Lo de C1 el miércoles 14**, porque la pantalla de acceso de C2 y la barra de D
  consumen ese token.
- **Las tres suites de B antes del viernes**, porque a partir de ahí cada solicitud
  de cambios se mide con ellas.

---

## Antes de empezar: tres votos que vencen el lunes

No son tareas de la semana, son requisitos para que las tareas no se hagan dos
veces. Están en `docs/equipo/decisiones-pendientes.md` §«Para decidir», cada una con
sus opciones y lo que implica cada opción.

| | Qué se vota | Quién | Por qué antes del lunes |
|---|---|---|---|
| **D-09** | Cómo se entregan los avisos de precio | C1 y B | El notificador de CU-11 se construye una vez |
| **D-10** | Cómo lee el cliente el correo de la cuenta después de iniciar sesión | C1, con C2 y D | C1 publica `dominio.yaml` esta semana; una ruta nueva después es romper el contrato |
| **D-11** | Con qué se registra quién cerró un incidente | A y B | El esquema de operación se crea en la base en esta fase |

## La deuda del fin de semana · antes que lo nuevo

Si arrastras algo, va primero: una tarea a medias bloquea a otro; una nueva todavía
no.

| Quién | Qué falta | Dónde |
|---|---|---|
| **C2** | ADR 007 reescrito con las cuatro pestañas; 006 y 011 ratificados | `docs/adr/` |
| **B** | ADR 008: la población de su cifra de peso, y ratificarlo | `docs/adr/008-donde-vive-la-base.md` |
| **D** | Las capturas corregidas del prototipo | Figma · `docs/entregas/diseno.md` §7 |
| **C1** | Visto bueno al parche de CU-08 | `docs/analisis/casos-uso/CU-08-registrar-cuenta.md` |

Los dos avisos que da el auditor hoy son los ADR en propuesta y la cifra del ADR
008. Los dos se cierran con la deuda de arriba.

## Cómo se llama tu rama

`tipo/iniciales-descripcion`. Tipos: `feat`, `fix`, `docs`, `test`, `chore`,
`refactor`. Iniciales: `alm`, `aas`, `lyl`, `orf`, `kah`. Un commit por idea, con
`tipo(ámbito): descripción`.

---

# T043 · A · Ingesta de punta a punta y Pandera contra el contrato

**Rama:** `feat/alm-ingesta-dagster-pandera` · **10 horas**

### De qué depende, y qué revisar antes

- [ ] **ADR 016** · Dagster, su forma mínima y su fecha de salida del 25 de octubre.
- [ ] **ADR 018** · Pandera por lote, con el esquema generado desde el YAML.
- [ ] **`contracts/qqp-v1.yaml` 1.3.4** · las 15 columnas con tipo, largo y
      obligatoriedad, y los motivos de cuarentena.
- [ ] **`services/data-platform/ingestion/ingesta.py`** · lo que ya hace: lee los
      CSV desde el ZIP, detecta controles C1, `?` en los filtros y filas de otra
      quincena, y escribe particionado al bucket.

### Los términos

**Activo (asset).** En Dagster, una cosa que existe después de correr: una tabla,
un archivo en el bucket. Se declara qué produce y de qué depende, y Dagster deduce
el orden. No es «la tarea de ingerir», es «la capa cruda de la quincena 2026-07-Q2».

**Partición.** Una rebanada de un activo que se puede materializar sola. **Aquí la
partición es la quincena**, que es exactamente un lote. Reprocesar un lote (RF-25)
es re-materializar su partición.

**Sensor.** Código que Dagster corre cada pocos segundos y que, si ve algo nuevo
—un archivo en el bucket—, dispara la corrida. Ese disparo es el instante desde el
que H2 cuenta sus 15 minutos.

### Paso a paso

1. Crea la rama.
2. **Dagster mínimo:** un activo particionado por quincena que envuelva lo que
   `ingesta.py` ya hace. No reescribas la ingesta: envuélvela.
3. **Un segundo activo** que dependa del primero: la capa cruda validada.
4. **El esquema de Pandera se genera leyendo el contrato**, no se escribe a mano.
   Una función que abre `contracts/qqp-v1.yaml` y devuelve el esquema con las 15
   columnas, su tipo, su largo máximo y su obligatoriedad.
5. **Las filas que Pandera rechaza se escriben a cuarentena con su motivo**, una
   fila por fila rechazada. El motivo sale del nombre de la regla que falló.
6. **Lo que necesita el lote completo se queda en DuckDB:** colisión de precio alta,
   frescura y el umbral de rechazo del 5% por lote (D-07).
7. **El sensor** que dispara al aparecer un archivo nuevo.
8. Corre un lote real de punta a punta y guarda la salida completa de la terminal.

### Cómo se ve terminado, exactamente

- `dagster dev` levanta y muestra **tres activos**, uno de ellos particionado por
  quincena.
- Materializar la partición `2026-07-Q2` escribe la capa cruda y deja su linaje.
- Un lote con filas defectuosas **no promueve esas filas**: quedan en cuarentena,
  cada una con su motivo.
- El esquema de Pandera **no tiene ninguna regla escrita a mano**: todas salen del
  YAML.

### Cómo lo compruebas tú misma

```bash
# 1 · Que el esquema sale del contrato y no de tu memoria
#     Cambia largo_maximo de una columna en el YAML, corre, y mira que la compuerta
#     cambie sin que toques código. Luego regrésalo.

# 2 · Que la cuarentena guarda motivo por fila, no un conteo
#     Inyecta tres filas malas de tres tipos distintos y revisa que haya tres
#     motivos distintos, no "3 filas rechazadas".

# 3 · Que reprocesar da lo mismo (RF-25)
#     Materializa la partición dos veces y compara la huella del resultado.

# 4 · Que el estático pasa, con la versión anclada
pip install ruff==0.17.0 && ruff check services/
```

### Errores frecuentes

- **Escribir el esquema de Pandera a mano «por ahora».** Ese «por ahora» es la
  segunda copia de las reglas, que es exactamente lo que el proyecto investiga.
- **Meter en Pandera lo que necesita ver el lote entero.** Una proporción del lote
  no es una regla de fila.
- **Dejar que Dagster crezca.** El ADR 016 dice mínimo y con fecha de salida: tres
  activos y un sensor. Si para el 25 de octubre no corren, se cambia a guion y
  `cron`, y eso es un resultado del experimento, no un fracaso.

---

# T044 · B · Las tres suites en la integración continua y los datos semilla

**Rama:** `feat/aas-ci-suites-y-semilla` · **8 horas**

### De qué depende, y qué revisar antes

- [ ] **Que C1 ya haya quitado el campo `nombre` de `Usuario.java`.** Esto es lo más
      importante de tu semana y es una dependencia, no una sugerencia: ver abajo.
- [ ] **`.github/workflows/ci.yml`** · el paso «Pruebas» del trabajo Dominio está
      comentado, en las líneas 64 a 67.
- [ ] **Tu deuda:** el ADR 008 sigue sin decir de qué población es su cifra de peso.

### El orden importa, y no es un detalle

`Usuario.java` todavía tiene el campo `nombre` que el equipo quitó el 7 de octubre
(P-13), y `UsuarioTest.java` le pasa un nombre en su línea 32. **Si activas las
pruebas del dominio antes de que C1 lo corrija, la integración continua se pone
verde certificando un modelo que ya cambiamos.** Una compuerta que aprueba lo
incorrecto es peor que no tener compuerta: da confianza falsa. Espera a que C1
suba su cambio, y entonces activa el paso.

### Paso a paso

1. Crea la rama.
2. **Cierra tu deuda primero:** el ADR 008 con la población de la cifra y su estado
   en «aceptada». Es uno de los dos avisos del auditor.
3. **Espera el cambio de C1.** Mientras, haz los puntos 4 y 5.
4. **`redocly lint` en la integración continua**, sobre
   `docs/analisis/openapi/*.yaml`. Hoy el validador da 0 errores y 5 avisos
   esperados: deja que esos cinco no rompan el trabajo, y que un sexto sí.
5. **Guion de carga de datos semilla:** lo mínimo para que el dominio y la web
   tengan con qué arrancar, en `infra/scripts/`. Sin datos reales de PROFECO en el
   repositorio.
6. **Cuando C1 suba su cambio,** descomenta el paso «Pruebas» del trabajo Dominio y
   comprueba que corre en verde **por haber corrido**, no por haberse saltado.

### Cómo se ve terminado, exactamente

- Los **tres trabajos** de la integración continua corren y los tres dicen qué
  hicieron: Dominio compila **y prueba**, Datos analiza y prueba, Higiene revisa.
- `redocly lint` corre en cada solicitud de cambios.
- El guion de semilla se corre dos veces seguidas sin romperse.

### Cómo lo compruebas tú mismo

```bash
# 1 · Que las pruebas del dominio CORRIERON, no que se saltaron
#     En el registro del trabajo tiene que aparecer el conteo de pruebas.
#     "0 tests" en verde es un falso positivo: la guarda se las saltó.

# 2 · Que el ancla de ruff sirve
pip install ruff==0.17.0 && ruff check services/

# 3 · Que el guion de semilla es idempotente
#     Córrelo dos veces. La segunda no debe duplicar filas ni reventar.
```

### Errores frecuentes

- **Activar las pruebas antes del cambio de C1.** Es el error de la semana.
- **Confundir «el trabajo salió verde» con «las pruebas pasaron».** La guarda
  `if: steps.existe.outputs.hay == 'si'` existe a propósito: lee el registro.
- **Meter datos crudos de PROFECO en el guion de semilla.** Nunca entran al
  repositorio.

---

# T045 · C1 · La cuenta con rol y sin nombre, y el inicio de sesión real

**Rama:** `feat/lyl-autenticacion-con-rol` · **10 horas**

### De qué depende, y qué revisar antes

- [ ] **D-10, votada.** Es tuya y vence el lunes: define si hay una ruta nueva para
      leer la cuenta. Si se vota la opción A, la implementas esta semana.
- [ ] **`docs/analisis/modelo-dominio.md`** · el diagrama de clases ya trae la clase
      `Usuario` correcta: con `Rol`, sin `nombre`. El código es el que está atrasado.
- [ ] **`docs/analisis/openapi/dominio.yaml`** · `Registro`, `Credenciales`, `Cuenta`
      y `Sesion` son el contrato que publicas. `Cuenta` es `id`, `correo`, `rol` y
      `fechaDeRegistro`. `Sesion` es `token`, `expiraEn` y `rol`.
- [ ] **CU-08**, con el parche que te pasé: el rol al crear la cuenta y el token con
      el rol al iniciar sesión.

### Lo que cambió en tu modelo, y por qué

| Antes | Ahora | Por qué |
|---|---|---|
| `Usuario` tiene `nombre` | **No tiene** | Ningún caso de uso lo usa, el correo ya identifica la cuenta y es el único dato personal que guardamos (P-13) |
| No hay rol | **`Rol`: `CONSUMIDOR`, `ANALISTA`, `OPERADOR`** | Hay tres perfiles y dos consolas; sin rol en la sesión, cada cliente decide solo qué muestra, y eso es no tener control de acceso (P-07) |
| La sesión era «entra o no entra» | **El token lleva el rol** | Con él la web decide si abre el tablero o la consola |

### Paso a paso

1. Crea la rama.
2. **`Rol`**, como enumeración: `CONSUMIDOR`, `ANALISTA`, `OPERADOR`.
3. **`Usuario`:** fuera `nombre`, fuera `renombrar()`, fuera el `nombre()`. Entra
   `Rol rol` en el constructor y su acceso.
4. **`UsuarioTest`:** quita el argumento del nombre, y **agrega una prueba que falle
   si `Usuario` vuelve a tener nombre.** Esa prueba es lo que convierte la decisión
   en algo verificable.
5. **Registro e inicio de sesión reales,** contra el contrato: `POST /api/v1/cuentas`
   devuelve `Cuenta`; `POST /api/v1/sesiones` devuelve `Sesion` con el token y el
   rol. Desde la app sólo se crean `CONSUMIDOR`.
6. **Si D-10 salió opción A:** `GET /api/v1/cuentas/yo` que devuelva `Cuenta`, y
   `dominio.yaml` sube a 0.2.1.
7. **Las rutas de canasta**, si queda semana.
8. **Avísale a Ari Adair** en cuanto el cambio de `Usuario` esté incorporado: él
   activa las pruebas del dominio en la integración continua después, no antes.

### Cómo se ve terminado, exactamente

- `Usuario` **no compila** si alguien le pasa un nombre.
- Registrarse y entrar devuelve un token, y el token lleva el rol.
- La respuesta de la cuenta trae `id`, `correo`, `rol` y `fechaDeRegistro`, y **nada
  más**.
- Si D-10 fue A, `GET /api/v1/cuentas/yo` responde con la cuenta de quien tiene la
  sesión.

### Cómo lo compruebas tú misma

```bash
# 1 · Que el contrato y el código dicen lo mismo
npx @stoplight/prism-cli mock docs/analisis/openapi/dominio.yaml -p 4010
# y compara campo por campo contra lo que devuelve tu servicio

# 2 · Que la cuenta no guarda nombre
mvn -B test        # la prueba nueva falla si alguien lo repone

# 3 · Que el token lleva el rol
#     Decodifica el token en jwt.io y mira el rol. No publiques un token real.
```

### Errores frecuentes

- **Dejar `nombre` «por si acaso».** Es el campo que el equipo decidió no tener.
- **Crear cuentas de analista u operador desde la app.** Se crean por
  configuración: si no, cualquiera con el APK se hace operador.
- **Publicar `dominio.yaml` antes de que D-10 se vote.** Agregar una ruta después
  es romper el contrato con el que C2 y D ya construyeron.

---

# T046 · C2 · Las cuatro pestañas y la pantalla de acceso conectada

**Rama:** `feat/orf-acceso-conectado` · **8 horas** · (las pestañas van en su propia
rama, ver abajo)

### De qué depende, y qué revisar antes

- [ ] **Tu deuda:** el ADR 007 reescrito con las cuatro pestañas, y el 006 y el 011
      ratificados. Va antes que el código.
- [ ] **`docs/analisis/navegacion.md` §1** · el diagrama de la app: cuatro pestañas,
      el detalle como hoja sobre la pestaña, y «Mis alertas» detrás de la campana y
      de Cuenta.
- [ ] **El token de C1**, con su rol. Hasta el miércoles 14 no está.
- [ ] **D-10**, que define cómo obtienes el correo para mostrarlo en Cuenta.

### Paso a paso · primero las pestañas

Rama aparte, `feat/orf-cuatro-pestanas`, porque es un cambio de estructura y se
revisa solo:

1. `clients/mobile/app/(tabs)/_layout.tsx`: cuatro `Tabs.Screen` — `index`,
   `descubrir`, `canasta`, `cuenta`.
2. `index.tsx`: el título pasa de «Búsqueda de artículos» a **«Inicio»**.
3. `descubrir.tsx` y `cuenta.tsx`: nuevas, con `PantallaVacia`.
4. `alertas.tsx` **sale del grupo `(tabs)`** y se mueve a `app/alertas.tsx`. La ruta
   `/alertas` no cambia, porque `(tabs)` es un grupo: sólo deja de tener pestaña. Se
   llega por la campana y por Cuenta.
5. `app/_layout.tsx`: el `headerBackTitle` del detalle pasa a «Inicio».

### Paso a paso · la pantalla de acceso

1. Crea la rama `feat/orf-acceso-conectado`.
2. Maqueta el acceso con el sistema de diseño: correo, contraseña, «Explorar sin
   cuenta» y **«No somos PROFECO»** (RF-23).
3. **Conéctala al dominio real de C1:** `POST /api/v1/sesiones`, guarda el token, y
   con el rol decide a dónde entra.
4. **La cuenta no tiene nombre:** la pestaña Cuenta muestra **el correo** y un
   avatar con su inicial. De dónde sale el correo lo define D-10.
5. La canasta del invitado vive en el teléfono hasta que inicia sesión (D-04): no la
   subas antes.

### Cómo se ve terminado, exactamente

- La barra de abajo tiene **cuatro** pestañas y «Alertas» ya no es una de ellas.
- Con credenciales buenas entra; con malas dice que no son válidas y no revienta.
- La pestaña Cuenta muestra un correo, nunca un nombre.

### Cómo lo compruebas tú mismo

```bash
# 1 · Que las rutas siguen funcionando después de mover alertas
npx expo start
# navega: Inicio -> detalle -> atrás; campana -> Mis alertas; Cuenta -> Mis alertas

# 2 · Que hablas con el dominio real y no con un simulador
#     Apaga el servicio de C1 y vuelve a intentar: tiene que fallar con un mensaje,
#     no quedarse cargando para siempre.
```

### Errores frecuentes

- **Escribir el código antes que el ADR.** El 007 dice tres pestañas; si subes
  cuatro sin reescribirlo, el repositorio se contradice a sí mismo.
- **Mostrar un nombre en Cuenta.** No existe.
- **Guardar la contraseña en el teléfono.** Se guarda el token, nunca la
  contraseña.

---

# T047 · D · La estructura de la web, con acceso y navegación

**Rama:** `feat/kah-web-acceso-y-navegacion` · **8 horas**

### De qué depende, y qué revisar antes

- [ ] **Tu deuda:** las capturas corregidas del prototipo, y marcar los puntos 12,
      13 y 14 de `diseno.md` §7 como resueltos.
- [ ] **El ADR del cliente web** (Next.js o el Vite que exporta Figma) sigue sin
      escribirse, y es tuyo. Va antes del código, por la misma razón que el 007 de
      Oscar.
- [ ] **`docs/analisis/inventario-vistas.md`** · las ocho vistas y qué contiene cada
      una.
- [ ] **`docs/analisis/puntos-de-quiebre.md`** · D-08: las consolas son de
      escritorio desde 1025 px y avisan del ancho mínimo; el acceso web sí se adapta
      a los tres anchos.
- [ ] **El token de C1**, con su rol, a partir del miércoles 14.

### Lo que cambió en tu barra lateral, y por qué

Donde el prototipo dice «Analista Ruiz» va **el correo y el rol de la sesión**. La
cuenta no tiene nombre (P-13), y el rol es lo que decide si se abre el tablero o la
consola (P-07). No es un detalle de maquetación: es lo único que distingue al
analista del operador en la pantalla.

### Paso a paso

1. **Escribe el ADR del cliente web** y súbelo. Media cuartilla: qué se usa, qué se
   descartó y qué cuesta.
2. Crea la rama.
3. **La estructura del proyecto** y las rutas de las cinco vistas web: acceso,
   tablero, detalle, consola y cola.
4. **El acceso**, contra `POST /api/v1/sesiones` de C1, y con el rol decide a dónde
   manda: tablero al analista, consola al operador.
5. **La barra lateral con el correo y el rol** de la sesión.
6. **El aviso de ancho mínimo** en las consolas por debajo de 1025 px (D-08).

### Cómo se ve terminado, exactamente

- Las cinco rutas existen y se navega entre ellas.
- Entrar como analista abre el tablero; como operador, la consola.
- La barra lateral muestra un correo y un rol, nunca un nombre.
- Por debajo de 1025 px la consola avisa del ancho mínimo en lugar de deformarse.

### Cómo lo compruebas tú misma

```bash
# 1 · Que el rol manda, y no la URL
#     Entra como analista y escribe a mano la ruta de la consola: no debe abrirla.

# 2 · Que el aviso de ancho aparece donde dice D-08
#     Achica la ventana a 1024 px. A 1025 no aparece; a 1024 sí.

# 3 · Que las cifras llevan su población (RNF-16)
#     Cualquier número en pantalla dice de qué población sale y de qué fecha.
```

### Errores frecuentes

- **Inventar datos en la pantalla.** Fue lo que pasó con la cobertura del 81.4%: una
  cifra inventada que además reprueba nuestra propia hipótesis. Si no hay dato, dice
  «se mide en T058».
- **Esconder la consola con CSS en lugar de avisar.** D-08 pide un aviso de ancho
  mínimo, no una consola deformada.
- **Construir antes del ADR.** Es la misma deuda que tiene Oscar con el 007.
