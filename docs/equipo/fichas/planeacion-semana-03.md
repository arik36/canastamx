# Fichas · semana 3 · lunes 21 al domingo 27 de septiembre

> **Esta semana las fichas son más largas a propósito.** En la semana 2 varios
> dijeron que les faltó claridad en el paso a paso :'c . Así que cada ficha trae, en
> este orden: **el nombre de tu rama**, de qué depende, qué revisar antes, los
> términos raros explicados, el paso a paso, cómo se ve terminado y **cómo lo
> compruebas tú mismo** sin preguntarle a nadie. claro que si la duda te carcome, puedes 
> venir a preguntarme a mi (A)
>
> Si algo sigue sin entenderse, di **cuál sección** de cuál ficha. Eso se
> resuelve en dos minutos; «no le entiendo» no.

## La semana de un vistazo

| | mié 23 | vie 25 | sáb 26 | dom 27 |
|---|---|---|---|---|
| **A** · Ariadne | T095 · plantilla de casos de uso | T020 · guión de ingesta | | T031 · modelo dimensional |
| **B** · Ari Adair | | | T021 · entornos y secretos | T032 · ramas y plantillas |
| **C1** · Liseth | | | | T033 · CU-08 a CU-11 |
| **C2** · Oscar | | T034 · CU-12 | | |
| **D** · Karen | | | | T035 · CU-13 y CU-14 |

**La fecha límite oficial del cronograma es el domingo 27 para todas.** Los días
de esta tabla son sugeridos, y están puestos para que las que desbloquean a
alguien más salgan primero.

**Cuatro de las siete tareas son escribir casos de uso.** Es documentación para
la entrega de análisis del 9 de octubre, se hace en paralelo y nadie bloquea a
nadie. Después de la semana 2, se agradece.

---

## La deuda de la semana 2 · antes que lo nuevo

Esto no es reclamo, es orden: **si arrastras algo, va primero.** Una tarea a
medias bloquea a otro; una tarea nueva todavía no bloquea a nadie.

| Quién | Qué falta | Por qué urge |
|---|---|---|
| **C1** | T022 · `Canasta`, `LineaDeCanasta`, `CorreoElectronico` y las pruebas | Sin eso no hay T027, el diagrama de clases |
| **B** | T026 · guía de arranque | Ya se desbloqueó: el parche de MinIO está decidido |
| **C2** | T028 · prototipo móvil | Arranca en cuanto D suba los valores |
| **D** | T029 · prototipo navegable | Los ocho puntos del documento que ya tienes |


> **C2: los valores del sistema de diseño ya existen y no tienes que
> inventarlos.** Están en el registro de Figma: turquesa `#23BBB7`, crema
> `#F0EADF`, tinta `#2F2F2F`, verde éxito `#00A859`, tipografía Inter, y la regla
> semántica de que el **rojo es sólo para incidentes del sistema** y el
> **naranja para anomalías de mercado**. Cópialos a
> `docs/analisis/sistema-de-diseno.md` con los radios y la escala de espaciado.
> Son quince minutos y destraban a otra persona.

---

## Cómo se llama tu rama, y por qué importa

**Convención:** `tipo/iniciales-descripcion-corta`, todo en minúsculas y con
guiones. El `tipo` es uno de tres:

| Tipo | Cuándo |
|---|---|
| `feat` | Código o funcionalidad nueva |
| `docs` | Documentación: casos de uso, modelos, ADR |
| `chore` | Configuración, plantillas, herramientas |

Las ramas de esta semana ya están decididas, cada una en su ficha. **Créala
antes de tocar nada**, siempre desde `main` actualizado:

```bash
git switch main
git pull
git switch -c <tu-rama>
```

> Si tus iniciales no coinciden con las que puse, ajústalas. Lo que importa es
> que sean siempre las mismas.

---

# T095 · A · Plantilla de casos de uso

**Rama:** `docs/alm-plantilla-casos-de-uso` · **1 hora** ·
**Desbloquea a C1, C2 y D**

### Por qué existe esta tarea, que no estaba en el cronograma

Las fichas dicen que los casos de uso se escriben «con el formato de CU-02». Pero
**CU-02 vive en el protocolo, no en el repositorio**: `docs/analisis/casos-uso/`
está vacía, sólo tiene un `.gitkeep`. Tres personas iban a empezar el domingo sin
saber qué formato usar, y cada una iba a inventar el suyo.

### Depende de

Nada. Es lo primero de la semana.

### Qué entregas

- `docs/analisis/casos-uso/PLANTILLA.md`

### Cómo se ve terminado

El archivo tiene las nueve secciones del formato Cockburn explicadas, la
plantilla en blanco para copiar, **un ejemplo completo lleno** y una tabla de
errores frecuentes.

### Cómo lo compruebas

Mándaselo a C2 —que tiene el caso de uso más chico— y pregúntale si con eso puede
empezar sin hacerte ninguna pregunta. Si te pregunta algo, esa respuesta le falta
al archivo.

---

# T020 · A · Primer guión de ingesta

**Rama:** `feat/alm-guion-de-ingesta` · **4 a 5 horas**

### De qué depende, y qué revisar antes

- [ ] **El ADR 009 ya está decidido**: seguimos con MinIO apuntando a Quay.io.
      Sin eso, este guión se escribiría contra algo que puede cambiar.
- [ ] **B ya aplicó el parche** y `docker compose up -d` levanta MinIO sin error.
      Si truena, no empieces: avísale.
- [ ] **Tienes a la mano `contracts/qqp-v1.yaml`.** El guión no inventa reglas,
      las lee de ahí.

### Los términos, antes del paso a paso

**Capa cruda, o *bronze*.** Donde se deposita el dato **tal como llegó**, sin
limpiar ni corregir. Suena contraintuitivo guardar basura a propósito, pero es lo
que permite volver atrás: si mañana descubres que tu limpieza estaba mal,
reprocesas desde la cruda en vez de volver a bajar todo. **Este guión sólo llega
hasta ahí.** No limpia, no valida, no normaliza — eso es de la semana 6.

**Parquet particionado.** Parquet guarda por columnas en vez de por filas, así
que leer sólo `precio` no obliga a leer las otras catorce. *Particionar* es
partirlo en carpetas por el valor de una columna:

```
canastamx-bronze/
  qqp/
    estado=guanajuato/quincena=2026-07-Q2/parte-0.parquet
    estado=jalisco/quincena=2026-07-Q2/parte-0.parquet
```

Con eso, una consulta de Guanajuato ni abre los archivos de Jalisco. **Parte por
`estado` y por `quincena`**, que son las dos columnas por las que siempre se va a
filtrar.

**Objeto y bucket.** En almacenamiento de objetos no hay carpetas de verdad: hay
un *bucket* —el nuestro es `canastamx-bronze`— y dentro, *objetos* cuyo nombre
lleva diagonales que **parecen** carpetas. Por eso la estructura de arriba es en
realidad una convención de nombres, y por eso importa que sea consistente.

**Idempotente.** Que correrlo dos veces con la misma entrada deje el sistema
igual que si lo hubieras corrido una. Es la propiedad más importante de un
proceso de ingesta: si se cae a la mitad, lo vuelves a correr sin miedo. Un guión
que **agrega** en vez de **reemplazar** no es idempotente y te duplica los datos
en silencio.

### Sobre el corpus, para que no te agobie

**No vamos a estar recibiendo datos nuevos.** La decisión 9 del ADR 010 congeló
el corpus en la última quincena que publica la fuente, **2026-07-Q2**. Este guión
toma un archivo que ya tienes en disco; no descarga nada de internet en cada
corrida.

### Paso a paso

1. Crea la rama.
2. Crea `services/data-platform/ingestion/ingesta.py`.
3. **Parámetros, ninguno inventado:** ruta del archivo de entrada, y el endpoint,
   la llave y el bucket de S3 **leídos del entorno** — `S3_ENDPOINT`,
   `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET`. Nunca escritos en el código.
4. Lee el archivo con DuckDB y quédate con las **15 columnas del contrato**, en
   el orden que el contrato declara.
5. Escribe a MinIO en Parquet, **particionado por `estado` y `quincena`**, con
   modo de sobrescritura de partición para que sea idempotente.
6. Escribe un registro de la corrida en
   `services/data-platform/ingestion/corridas/<fecha>-<lote>.json`: qué archivo
   entró, cuántas filas leyó, cuántas escribió, cuánto tardó, y el hash del
   archivo de entrada.
7. Documenta en el encabezado del archivo qué hace y qué **no** hace.

### Cómo se ve terminado, exactamente

- Corres el guión y termina sin error, imprimiendo cuántas filas escribió.
- En la consola de MinIO ves el bucket `canastamx-bronze` con la estructura
  `estado=…/quincena=…`.
- Existe un archivo de corrida con las cinco cifras.
- **Corres el guión otra vez y el resultado es idéntico**: mismo número de
  objetos, mismo tamaño total.

### Cómo lo compruebas tú mismo

```bash
# 1 · Cuántos objetos quedaron, y cuánto pesan
mc ls --recursive local/canastamx-bronze | wc -l
mc du local/canastamx-bronze

# 2 · La prueba de idempotencia: corre otra vez y compara
python services/data-platform/ingestion/ingesta.py <archivo>
mc ls --recursive local/canastamx-bronze | wc -l     # tiene que dar lo mismo

# 3 · Lee de vuelta lo que escribiste y cuenta filas
python -c "
import duckdb
n = duckdb.sql(\"SELECT count(*) FROM read_parquet('s3://canastamx-bronze/qqp/**/*.parquet')\").fetchone()[0]
print('filas en la capa cruda:', n)
"
```

**La cifra del punto 3 tiene que coincidir con las filas del archivo de entrada.**
Si no coincide, algo se quedó en el camino y hay que encontrarlo antes de seguir.

### Errores frecuentes

| Qué pasa | Por qué | Qué hacer |
|---|---|---|
| La segunda corrida duplica todo | El guión agrega en vez de reemplazar | Usa sobrescritura por partición |
| `Access Denied` contra MinIO | Las variables del `.env` no coinciden | Revisa que sean las nuevas `S3_*`, no las viejas `MINIO_*` |
| Escribiste `minio:9000` en el código | Se siente más rápido | Sácalo a `S3_ENDPOINT`. El día que cambiemos de proveedor es una línea |
| Aprovechaste para limpiar los datos | Es tentador | La capa cruda guarda lo que llegó. Limpiar es semana 6 |

---

# T031 · A · Modelo dimensional completo

**Rama:** `docs/alm-modelo-dimensional` · **4 horas**

### De qué depende

- [ ] El contrato `contracts/qqp-v1.yaml` en su versión 1.2.1.
- [ ] El ADR 005, para saber qué catálogos entran.
- [ ] Idealmente T020 hecha, para saber qué forma tiene el dato en la capa cruda.

### Los términos

**Esquema estrella.** Una tabla grande en el centro con los **números** —la de
hechos— y varias chicas alrededor con el **contexto** —las dimensiones—. Se llama
estrella porque el diagrama parece una.

**Grano.** *Qué representa exactamente una fila de la tabla de hechos.* Es la
declaración más importante de todo el modelo y la que más se olvida. El nuestro
sería algo como: **«un precio observado de un artículo en un establecimiento en
una fecha»**. Si el grano no está escrito en una frase, el modelo está mal
aunque las tablas se vean bonitas.

**Dimensión.** Una tabla de contexto: artículo, establecimiento, fecha, cadena.
Guarda el texto una sola vez y la tabla de hechos la apunta con un número.

**Llave subrogada.** Un entero sin significado —1, 2, 3— que identifica una fila
de dimensión. Se usa en vez del texto porque indexar un entero de 4 bytes no es
lo mismo que indexar 88 bytes de dirección.

### El número que justifica todo esto

Medido el 19 de septiembre con `medir-el-peso.py`:

| | bytes por fila | total estimado |
|---|---:|---:|
| Como una sola tabla plana | 336 | **~1,929 MB** |
| Como tabla de hechos con llaves | 56 | **~350 MB** |

**Cinco veces menos**, y los índices se abaratan solos porque indexar `int4` no
es indexar texto. **Esto le importa a B**: su máquina tiene 12 GB, y dimensionar
contra 1,929 MB en vez de 350 MB cambia su presupuesto. Cuando termines, pásale
la cifra.

### Qué entregas

- `docs/datos/modelo-dimensional.md`

Con estas seis partes:

1. **Declaración de grano**, en una frase, arriba de todo.
2. **Tabla de hechos**: columnas, tipos, llaves foráneas, medidas.
3. **Cuatro dimensiones**: artículo, establecimiento, fecha, cadena comercial.
   Cada una con sus atributos y su llave subrogada.
4. **Agregados**: qué se precalcula y por qué.
5. **Diccionario**: qué significa cada columna, en una línea.
6. **Requisitos no funcionales de datos**, con número: frescura —avisa a los 20
   días, bloquea a los 45, según la decisión 9—, completitud y latencia.

### Cómo lo compruebas

**La prueba del grano.** Escribe estas tres preguntas como consultas usando sólo
tu modelo:

1. ¿Cuánto costó el huevo blanco de 30 piezas en Guanajuato en julio?
2. ¿Qué cadena tuvo el precio promedio más bajo de la canasta en junio?
3. ¿Cuántos artículos distintos se observaron en Michoacán la última quincena?

**Si alguna no se puede responder, al modelo le falta algo.** Anota las tres
consultas al final del documento: son la prueba de que el modelo sirve, y además
le ahorran a quien lo implemente tener que adivinar.

### Errores frecuentes

| Qué pasa | Por qué | Qué hacer |
|---|---|---|
| No hay frase de grano | Se dio por obvio | Escríbela literal. Es la primera línea del documento |
| `marca` quedó como dimensión propia | Parece una entidad | La marca es atributo del artículo. El artículo es producto + presentación (ADR 002) |
| La tabla de hechos guarda `nombre_comercial` | Se copió de la tabla plana | Eso va en la dimensión de establecimiento. En hechos van llaves y medidas |
| «frescura: reciente» | No es medible | 20 y 45 días. Los decidió la boleta |

---

# T021 · B · Entornos, secretos y `pytest` en la integración continua

**Rama:** `feat/aas-entornos-y-secretos` · **4 horas**

### De qué depende, y qué revisar antes

- [ ] El parche de MinIO ya aplicado y `docker compose up -d` levantando los
      cinco servicios.
- [ ] La integración continua de T009 corriendo en verde.

### Los términos

**Entorno.** Una copia completa del sistema con su propia configuración y sus
propios datos. **Desarrollo** es donde trabajas y donde se rompe todo;
**pruebas** es una copia limpia donde corre el experimento, aislada, para que
nadie inyecte fallas en los datos con los que otro está trabajando. Si comparten
base de datos, no son dos entornos: son uno con dos nombres.

**Secreto.** Cualquier valor que da acceso: contraseñas, llaves de S3, tokens.
**Nunca entran al repositorio** —es la regla 7 del tablero— porque el repositorio
se hace público al final del semestre y el historial de git no olvida.

**Variable de entorno.** Un valor que el programa lee del sistema en vez de
tenerlo escrito. Vive en `.env`, que está en `.gitignore`. Lo que sí se sube es
`.env.example`, con los nombres y **sin los valores**.

**`pytest`.** El corredor de pruebas de Python. Busca archivos `test_*.py`, corre
las funciones `test_*` y reporta cuáles fallaron.

### Paso a paso

1. Crea la rama.
2. Separa la configuración en `infra/envs/dev/` e `infra/envs/test/`, cada uno
   con su archivo de variables y **puertos distintos**, para que puedan estar
   arriba los dos a la vez.
3. Actualiza `.env.example` con **todos** los nombres y ningún valor. Aprovecha y
   renombra `MINIO_*` a `S3_*`, más el `S3_ENDPOINT` nuevo — lo pide el ADR 009.
4. Verifica que `.env` esté en `.gitignore` y que **nunca haya estado en el
   historial**.
5. Agrega un trabajo de `pytest` a `.github/workflows/ci.yml`, que corra sobre
   `services/data-platform/`.
6. Escribe una prueba mínima que sí pase, para que el trabajo tenga algo que
   correr.
7. Documenta en `infra/envs/README.md` cómo se levanta cada entorno.

### Cómo se ve terminado

- `docker compose -f infra/envs/dev/... up -d` y el de `test` levantan **los dos
  a la vez**, sin pelearse por puertos.
- `.env.example` tiene todos los nombres y ningún valor.
- Al abrir una solicitud de cambios aparece un trabajo **Datos (Python)** en
  verde, además de los que ya había.

### Cómo lo compruebas tú mismo

```bash
# 1 · Los dos entornos arriba al mismo tiempo
docker compose -f infra/envs/dev/docker-compose.yml up -d
docker compose -f infra/envs/test/docker-compose.yml up -d
docker ps --format '{{.Names}}\t{{.Ports}}'      # ninguno repetido

# 2 · Que no haya secretos en el repositorio, ni ahora ni antes
git grep -nE "(PASSWORD|SECRET|ACCESS_KEY)\s*=\s*.+" -- . ':!*.example'
git log --all --oneline -- .env                   # las dos vacías

# 3 · La CI: abre una rama de prueba y mira el resultado
git commit --allow-empty -m "ci: probar pytest"
git push -u origin HEAD
gh pr create --fill
gh pr checks
```

**Las dos búsquedas del punto 2 tienen que salir vacías.** Si `git log` devuelve
algo, un `.env` estuvo en el historial y hay que rotar esas credenciales, no sólo
borrar el archivo.

### Errores frecuentes

| Qué pasa | Por qué | Qué hacer |
|---|---|---|
| Los dos entornos chocan de puertos | Copiaste el compose sin cambiarlos | Pon los puertos en variables y dale a cada entorno los suyos |
| `pytest` falla con «no tests ran» | No hay ninguna prueba | El paso 6 existe para eso |
| Pusiste valores reales en `.env.example` | Se copió del `.env` | Déjalo con los nombres y el `=` vacío |
| Los dos entornos comparten volumen | Se heredó del compose original | Volúmenes distintos, si no el experimento contamina desarrollo |

---

# T032 · B · Estrategia de ramas y plantillas

**Rama:** `chore/aas-ramas-y-plantillas` · **2 horas**

### De qué depende

Nada técnico. Se puede hacer en cualquier momento de la semana.

### Los términos

**Plantilla de solicitud de cambios.** Un archivo que GitHub carga
automáticamente cuando alguien abre un PR, para que la descripción no dependa de
que a esa persona se le ocurra qué poner. Va en
`.github/pull_request_template.md`.

**Vista por iteración.** Una forma de ver el tablero agrupado por semana en vez
de por estado. Sirve para contestar «¿qué toca esta semana?» de un vistazo.

### Paso a paso

1. Crea la rama.
2. Escribe `docs/equipo/estrategia-de-ramas.md` con lo que **ya estamos
   haciendo**: `tipo/iniciales-descripcion`, los tres tipos, que se ramifica
   desde `main` actualizado, que se integra con solicitud y una aprobación, y que
   la rama se borra al integrarse. **No inventes un convenio nuevo**: documenta
   el que existe, que es lo que hace que se cumpla.
3. Revisa `.github/pull_request_template.md`. Que pida: qué cambia, qué tarea
   cierra, cómo lo probó quien lo escribió, y qué tiene que revisar quien
   aprueba.
4. Configura la vista por iteración en el tablero, con las semanas del
   cronograma.
5. Documenta en dos líneas dónde está esa vista, porque si nadie sabe que existe
   no sirve.

### Cómo se ve terminado

Abres una solicitud de prueba y **la plantilla aparece sola**, con sus secciones
vacías. En el tablero hay una vista que agrupa por semana.

### Cómo lo compruebas

```bash
git switch -c chore/aas-prueba-plantilla
git commit --allow-empty -m "chore: probar la plantilla"
git push -u origin HEAD
gh pr create --web        # mira si el cuerpo viene pre-llenado
```

Si el cuerpo viene vacío, la plantilla no está en la ruta correcta. Ciérrala sin
integrar y borra la rama.

---

# T033 · C1 · Casos de uso CU-08 a CU-11

**Rama:** `docs/lyl-casos-de-uso-08-11` · **4 a 5 horas**

### De qué depende, y qué revisar antes

- [ ] **`docs/analisis/casos-uso/PLANTILLA.md` existe** (T095, de A). Ábrelo
      antes de escribir una sola línea: trae el formato, un ejemplo completo y
      los errores frecuentes.
- [ ] **Tu propio `modelo-dominio.md`**, porque las reglas que escribiste ahí son
      las que aquí se vuelven pasos.
- [ ] **Las tres reglas que la boleta acaba de cerrar** y que tienes que
      reflejar: contraseña de mínimo 8 con mayúscula y número; el umbral de una
      alerta es válido si cae dentro del rango histórico del artículo; la alerta
      dispara con **menor o igual**.

### Cuáles son tus cuatro

| | Caso de uso | Actor primario |
|---|---|---|
| CU-08 | Registrar cuenta e iniciar sesión | persona consumidora |
| CU-09 | Crear y editar una canasta | persona consumidora |
| CU-10 | Configurar una alerta de precio | persona consumidora |
| CU-11 | Notificar cuando la alerta se dispara | el proceso de alertas (actor automático) |

> **CU-11 es el que más se equivoca**, porque su actor primario **no es una
> persona**: es el proceso que revisa las alertas contra los precios nuevos. La
> persona es *interesada*, no actora. Si lo escribes como «el usuario recibe una
> notificación», el caso de uso empieza donde ya terminó.

### Los términos

**Formato Cockburn.** Nueve secciones fijas: identificador, actor primario,
interesados, precondiciones, disparador, flujo principal numerado, flujos
alternos, postcondiciones de éxito y de fallo, y requisito no funcional. Están
todas explicadas en la plantilla.

**Flujo alterno.** Qué pasa cuando algo no sale bien, numerado contra el paso del
que se desvía: si el paso 3 puede fallar, sus alternos son `3a`, `3b`. **La regla
del proyecto es que un caso de uso sin flujos alternos está incompleto**, porque
los alternos son donde vive la ingeniería.

**Postcondición de fallo.** Qué queda cierto cuando el caso **no** logra su
objetivo. Es la que siempre se olvida y la que más importa: si la alerta no se
pudo enviar, ¿queda marcada como pendiente o se pierde?

### Paso a paso

1. Crea la rama.
2. Copia la plantilla cuatro veces:
   `CU-08-registrar-cuenta.md`, `CU-09-crear-canasta.md`,
   `CU-10-configurar-alerta.md`, `CU-11-notificar-alerta.md`.
3. Llena primero **CU-09**, que es el que mejor conoces porque acabas de
   modelar `Canasta`. Te sirve de calentamiento.
4. Por cada paso del flujo principal, pregúntate **«¿qué pasa si esto falla?»** y
   escribe el alterno. Mínimo dos por caso de uso.
5. En CU-08, que las reglas de contraseña sean las votadas, y que el flujo diga
   **explícitamente** que el sistema nunca guarda la contraseña en texto plano.
6. En CU-10, el flujo alterno del umbral fuera del rango histórico.
7. En CU-11, la postcondición de fallo: qué pasa si el correo no sale.

### Cómo se ve terminado, exactamente

Cuatro archivos, cada uno con **las nueve secciones**, **mínimo dos flujos
alternos**, **las dos postcondiciones** y un requisito no funcional **con
número**.

### Cómo lo compruebas tú misma

**La prueba de la persona que no programa.** Dale CU-09 a alguien de tu familia y
pídele que te cuente qué hace el sistema. Si puede, está bien escrito. Si te
pregunta «¿y esto qué es?», ahí falta lenguaje de negocio.

**La prueba de completitud**, sobre los cuatro archivos:

```bash
cd docs/analisis/casos-uso
for f in CU-08*.md CU-09*.md CU-10*.md CU-11*.md; do
  echo "── $f"
  grep -c "^\*\*[0-9]" "$f"      | sed 's/^/   flujos alternos: /'
  grep -c "De fallo"   "$f"      | sed 's/^/   postcondición de fallo: /'
done
```

**Si algún «flujos alternos» sale en 0 o 1, ese caso de uso está incompleto.**

### Errores frecuentes

| Qué pasa | Por qué | Qué hacer |
|---|---|---|
| El flujo principal tiene «si… entonces…» | Metiste el error en el camino feliz | Sácalo a un alterno numerado |
| El actor de CU-11 es «el usuario» | Parece lo natural | Es el proceso. La persona es interesada |
| El RNF dice «rápido» | No es medible | Ponle número y unidad |
| Se lee como una pantalla | Describiste la interfaz | Escríbelo sin mencionar botones. Si no se puede, no era caso de uso |

---

# T034 · C2 · Caso de uso CU-12

**Rama:** `docs/of-caso-de-uso-12` · **1.5 horas**

### De qué depende

- [ ] **`docs/analisis/casos-uso/PLANTILLA.md`** (T095, de A). Léelo completo
      primero; trae un ejemplo lleno.
- [ ] Los wireframes de D, para saber qué se busca y qué se compara.

> **Tienes la tarea más ligera de la semana y la menos bloqueada.** Si terminas
> el viernes, lo mejor que puedes hacer con el resto del tiempo es avanzar T028,
> que es tu deuda de la semana 2.

### Cuál es el tuyo

**CU-12 · Buscar un artículo y comparar su precio entre establecimientos.**
Actor primario: la persona consumidora.

### Los términos

Los mismos de la plantilla. Y dos que son de este caso en particular:

**Artículo, no producto.** El ADR 002 lo fijó: un artículo es `producto` +
`presentacion`. «Leche» no tiene precio comparable; «Leche Ultrapasteurizada ·
1 L» sí. En todo el caso de uso di **artículo**.

**Cobertura declarada.** La app sólo tiene datos de **siete entidades**. Si
alguien busca algo de un estado que no cubrimos, eso **no es un error del
sistema**: es un flujo alterno donde el sistema dice qué cubre. Ese alterno
tiene que estar.

### Paso a paso

1. Crea la rama.
2. Copia la plantilla a `CU-12-buscar-y-comparar.md`.
3. Flujo principal: la persona busca, el sistema devuelve artículos del catálogo
   acotado a su entidad, la persona elige uno, el sistema muestra el precio por
   establecimiento ordenado.
4. Flujos alternos, **mínimo estos tres**:
   - `2a` La búsqueda no devuelve nada.
   - `2b` La persona está en una entidad que no cubrimos.
   - `4a` El artículo sólo tiene un establecimiento con dato: no hay qué comparar.
5. Postcondición de fallo: qué queda cuando no hay resultados.
6. Requisito no funcional: tiempo máximo de respuesta de la búsqueda, con número.

### Cómo se ve terminado

Un archivo con las nueve secciones, tres flujos alternos, las dos
postcondiciones y un RNF con número.

### Cómo lo compruebas

Léelo en voz alta. Si en algún punto dices «y entonces le pica al botón», está
describiendo la pantalla y no el objetivo — reescribe esa línea sin mencionar la
interfaz.

---

# T035 · D · Casos de uso CU-13 y CU-14

**Rama:** `docs/kh-casos-de-uso-13-14` · **3 horas**

### Antes que nada: parte de tu tarea ya está hecha

El cronograma dice «CU-13 y CU-14. **Inicia la maquetación de alta fidelidad**».
**Esa segunda mitad ya la hiciste en T024**: entregaste alta fidelidad cuando se
te pedían wireframes. Así que de esta tarea sólo te quedan los dos casos de uso.

Lo que sí sigue pendiente de la semana 2, y va **antes** que esto:

1. **Documentar el sistema de diseño con valores.** Oscar está detenido. Quince
   minutos.
2. Los ocho puntos de T029.

### De qué depende

- [ ] **`docs/analisis/casos-uso/PLANTILLA.md`** (T095, de A).
- [ ] Tu inventario de vistas, que ya dice qué hace cada pantalla.

### Cuáles son los tuyos

| | Caso de uso | Actor primario |
|---|---|---|
| CU-13 | Analizar la evolución de precios y detectar una anomalía | analista |
| CU-14 | Revisar y resolver una variante en la cola de reconciliación | operador de datos |

> **Estos dos títulos son propuesta.** El protocolo tiene la lista oficial de los
> catorce; cotéjalos antes de escribir y si no coinciden, gana el protocolo.
> Pregúntale a A si tienes duda.

### Los términos

Los de la plantilla, más dos que son de tus casos:

**Anomalía de mercado contra incidente del sistema.** No son lo mismo y en tu
propio diseño ya los separaste por color. Una **anomalía** es que el huevo subió
27% en Jalisco: el dato es correcto y el precio es raro. Un **incidente** es que
el archivo llegó con 18 columnas en vez de 15: el dato está mal. **CU-13 es de
anomalías; CU-14 no es de ninguno de los dos**, es de variantes de nombre.

**Variante de artículo.** Dos escrituras distintas del mismo artículo:
`Mazatán` y `Mazatún`, `1 L` y `1 Lt`. La cola de reconciliación es donde una
persona decide si son el mismo o no, cuando el comparador no está seguro.

### Paso a paso

1. Crea la rama.
2. Cotejo rápido de los títulos contra el protocolo.
3. Copia la plantilla dos veces.
4. **CU-13:** el analista filtra por fecha, catálogo y entidad; ve el índice
   contra el INPC; detecta un artículo anómalo; entra a su detalle; exporta.
   Alternos: el filtro no devuelve datos; la entidad elegida no tiene cobertura;
   la exportación falla.
5. **CU-14:** el operador abre la cola; ve una variante con su porcentaje de
   similitud; **aprueba, rechaza o asigna manualmente**. Los tres caminos van en
   el flujo, porque cada uno deja un resultado distinto.
6. Postcondiciones de CU-14: qué queda escrito en el diccionario en cada uno de
   los tres casos.
7. RNF de CU-13: cuánto puede tardar el tablero en pintar. De CU-14: cuántas
   variantes por hora debería poder resolver una persona.

### Cómo se ve terminado

Dos archivos con las nueve secciones, mínimo dos alternos cada uno, las dos
postcondiciones y un RNF con número.

### Cómo lo compruebas

**Contrasta CU-14 contra tu propia pantalla.** Si el caso de uso dice que hay
tres acciones y tu prototipo sólo distingue dos —porque «Manual» hace lo mismo
que «Aprobar»—, uno de los dos está mal. Ésa es justamente la corrección que
tienes pendiente en T029, y escribir el caso de uso primero te va a decir
exactamente cómo debe comportarse.

### Errores frecuentes

| Qué pasa | Por qué | Qué hacer |
|---|---|---|
| CU-13 y CU-14 se parecen mucho | Los dos empiezan con «entra a una pantalla» | Fíjate en el objetivo: uno es entender precios, el otro es resolver una duda de datos |
| El actor de CU-14 es «el sistema» | El sistema propone la coincidencia | El sistema propone; **la persona decide**. Por eso existe la cola |
| Describiste los botones | Tienes el diseño en la cabeza | Escribe qué logra la persona, no dónde pica |

---

## Lista de verificación · domingo 27 antes de cerrar

- [ ] Cada quien trabajó **en su rama**, con el nombre que dice su ficha
- [ ] Cada rama tiene su solicitud de cambios abierta, con una aprobación
- [ ] La deuda de la semana 2 está cerrada o tiene fecha comprometida
- [ ] `docs/analisis/casos-uso/` tiene **siete archivos**: la plantilla más
      CU-08 a CU-14
- [ ] Ningún caso de uso tiene cero o un solo flujo alterno
- [ ] El sistema de diseño está documentado con valores y C2 ya lo está usando
- [ ] La integración continua está en verde en `main`
- [ ] La reunión del **viernes 6:00 pm** ya ocurrió, y lo que se decidió quedó
      escrito
