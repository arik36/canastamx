# Levantar CanastaMX en tu máquina

> **Guía verificada.** El 27 de septiembre alguien que no la escribió intentó
> seguirla en una máquina limpia. Todo lo que aparece aquí está probado; lo que
> se atoró está en la sección de [Problemas](#problemas), con el texto literal
> del error. El registro de esa prueba está en
> [`verificacion-arranque-2026-09-27.md`](../equipo/verificacion-arranque-2026-09-27.md).

> **RECOMENDACIÓN**
> ---
> Antes de iniciar con la guía, consulta el siguiente README y leélo con atención:
> [`instalar/README.md`](../equipo/instalar/README.md)

> **IMPORTANTE**  
> ---
> Para la ejecución de está guía es necesario satisfacer los siguientes requerimientos:
> - Conexión estable a internet (Si eres usuario de Windows: WSL debe tener acceso a internet)
> - Acceso a un entorno de Linux (WSL o una distribución de Linux)
> - Docker, y sus dependencias, instalado y configurado (Consulte documentación de Docker)
> - Contar con una instalación funcional en el entorno de Linux de los siguientes programas:
>   - git
>   - curl

<br><br>

# Indíce

1. [Requisitos](#requisitos)
2. [Configuración del entorno](#configuración-del-entorno)
3. [Ejecución y paro](#ejecución-y-paro)
4. [Comprobación](#comprobación)
5. [Problemas](#problemas)
6. [Si Docker Hub falla](#si-docker-hub-falla)

---

# Requisitos

# PREPARACIÓN DEL ENTORNO

## Primeros pasos

> **RECORDATORIO**
> ---
> Si ere usuario de Windows, la ejecución de todo comando debe hacerse **dentro del entorno de Linux**, NO en el CMD (Línea de comando de Windows)

El primer paso es verificar que se cuente con los requerimientos necesarios.  
Ejecute los siguientes comandos uno por uno en la terminal:

```bash
docker --version
docker compose version
git --version
```

Cada comando debe resultar en una impresión de la versión del programa respectivo y no en un error del siguiente tipo: 

`bash: <programa>: command not found...`

> **IMPORTANTE**
> ---
> Si el shell le índica que no encontró el comando, pero puede instalarlo, rechace la operación y consulte nuevamente el [`README.md`](../equipo/instalar/README.md). 

## Clonar el repositorio

_Clonar un repositorio significa hacer una copia local de todo el conjunto de archivos que componen el proyecto._

> **IMPORTANTE**
> ---
> Para realizar el siguiente paso es necesario contar con una conexión a internet

Para clonar el repositorio ejecute los siguientes comandos:

```bash
docker --version
docker compose version
docker info --format '{{.ServerVersion}}'
```

Como resultado, la terminal debe imprimir un estado de descarga, y después cambiar el directorio de trabajo a `canastamx`, que se le conocerá como **raíz del proyecto**.

## Actualizar el proyecto

> **IMPORTANTE**
> ---
> - Es necesario contar con internet para este paso

> **RECOMENDACIÓN**
> ---
> - Consulte regularmente si existen actualizaciones al proyecto

Si existe una versión actualizada del proyecto, y usted tiene un proyecto desactualizado, ejecute el siguiente comando para implementar los cambios en su copia del proyecto:

```bash
git pull
```

Como resultado, su copia ahora estará a la par que el proyecto de GitHub.

## Configuración del entorno

_Un archivo `.env` permite definir variables globales dentro del alcance del proyecto, esto nos ayudará a definir valores fijos que podemos consultar dentro del proyecto sin tener que repetirlos manualmente en cada configuración._

> **IMPORTANTE**
> ---
> Si es la primera vez que ejecuta estos pasos, y existe un archivo `.env`, elíminelo o muevalo de directorio. **NO eliminar el archivo `.env.example`**  
>
> **Si ya tenías el proyecto de antes**, tu `.env` viejo tiene variables
> `MINIO_*` que ya no existen. Cambiaron de nombre a `S3_*` por el
> [ADR 009](../adr/009-almacenamiento-de-objetos.md). Lo más rápido es borrar
> tu `.env`, volver a copiar el ejemplo y rellenarlo.

El siguiente paso es generar el archivo `.env`, necesario para levantar los servicios requeridos por el proyecto a través de Docker.

Para crear el archivo `.env` debemos usar la plantilla proporcionada junto al proyecto, está plantilla se encuentra en el archivo `.env.example` en la **raíz del proyecto**. 

Ejecute el siguiente comando en la terminal:

```bash
cd canastamx
cp .env.example .env
```

Ahora **abre el `.env` y llena los valores vacíos.** Este paso es el que la gente
se salta y es el que rompe todo.

> **Con qué editor.** En WSL o Linux, `nano .env` (se guarda con `Ctrl+O`,
> `Enter`, y se sale con `Ctrl+X`). En Windows, **no uses el Bloc de notas**: el
> archivo usa saltos de línea de Unix y te lo va a mostrar todo en un solo
> renglón. Usa VS Code o Notepad++.

Son cuatro valores. Los demás se quedan como están.

| Variable | Qué poner | Por qué |
|---|---|---|
| `OLTP_PASSWORD` | 8 a 16 caracteres | Contraseña de la base transaccional |
| `ANALYTICS_PASSWORD` | 8 a 16 caracteres | Contraseña de la base analítica |
| `S3_ACCESS_KEY` | mínimo 3 caracteres, p. ej. `canastamx` | Es el *usuario* de MinIO |
| `S3_SECRET_KEY` | **mínimo 8 caracteres** | Con menos, MinIO no arranca y el error no lo dice claro |

<br><br>

# Ejecución y Desactivación

> **IMPORTANTE**
> ---
> - Es absolutamente necesario que haya realizado la configuración del `.env` correctamente. En algunos casos, Docker no avisará explicitamente que existe un error, pero los servicios podrían fallar internamente.  
> 
> Si se encuentra con algún problema, consulte la sección de [Problemas](#problemas).

## Primera ejecución

> IMPORTANTE
> ---
> - El directorio de trabajo de la terminal debe estar posicionado en la **carpeta raíz** del proyecto.  
> - Durante la primera ejecución es necesario contar con una conexión estable a internet  
> - Asegurese de tener por lo menos **5 Gb** de espacio en disco disponible.

En la terminal, ejecute el siguiente comando para iniciar los servicios de Docker

```bash
docker compose up -d
```

Se descargarán las imagenes necesarias y se creará un contenedor de docker. La terminal mostrará el progreso de descarga y el proceso de creación de los contenedores. 

Al finalizar con éxito, los contenedores permanecerán activos. Verifique el estado de los servicios mediante el siguiente comando:

```bash
docker compose ps -a
```

`docker compose ps -a` tiene que mostrar seis contenedores:

| Contenedor | Estado esperado |
|---|---|
| `cmx-postgres-oltp` | `running (healthy)` |
| `cmx-postgres-analytics` | `running (healthy)` |
| `cmx-minio` | `running (healthy)` |
| `cmx-minio-init` | **`exited (0)`** |
| `cmx-adminer` | `running` |
| `cmx-traefik` | `running` |

**`cmx-minio-init` sale apagado y así tiene que ser.** No está roto. Su único
trabajo es crear el bucket `canastamx-bronze` y terminar. Si dice `exited (0)`,
hizo su trabajo. Si dice `exited (1)`, no lo hizo — ve a la sección de [Troubleshooting](#troubleshooting).

> **NOTA**
> ---
> Los tres `healthy` tardan entre diez y treinta segundos en aparecer. Si corres
`docker compose ps` de inmediato vas a ver `starting`; espera y vuelve a correrlo.

## Ejecuciones posteriores

> IMPORTANTE
> ---
> - Si ha eliminado las imagenes o contenedores de Docker, vea [Primera ejecución](#primera-ejecución)
> - Si ha ocurrido algún cambio respecto a las imagenes de Docker, y ya ha ejecutado el proyecto, es necesarios removerlas y actualizar el proyecto. 

Para cualquier ejecución subsecuente a la primera ejecución, simplemente ejecutar el siguiente comando desde la raíz del proyecto en una terminal:

```bash
docker compose up -d
```

## Detener CanastaMX

> **IMPORTANTE**
> ---
> - Verifique bien el comando que ingrese. **Cada ejecución es final**, significando que una vez ejecutado, **NO hay vuelta atrás**.

Para detener los servicios debe ejecutar **UNO** de los siguientes comandos, dependiendo de su intención.

```bash
docker compose down        # apaga y CONSERVA los datos
docker compose down -v     # apaga y BORRA los datos (bases y bucket)
```

`down -v` deja la máquina como recién clonada. Es el que se usa para probar esta
guía; en el día a día, `down` a secas.

---

<br><br>

# Comprobar los servicios

> **NOTA**
> ---
> Que los contenedores digan `running` sólo prueba que arrancaron, no que sirvan.

> **IMPORTANTE**
> ---
> - Evite modificaciones accidentales al archivo `.env` al consultarlo, si se modifica y se guardan los cambios, puede generar errores de autorización, y por ende, de funcionalidad. 

## Comprobación almacenamiento

Abra **http://localhost:9001** y entra con el `S3_ACCESS_KEY` y el
`S3_SECRET_KEY` que pusiste en tu `.env`.

| Contenedor | Estado esperado |
|---|---|
| `cmx-postgres-oltp` | `Up (healthy)` |
| `cmx-postgres-analytics` | `Up (healthy)` |
| `cmx-minio` | `Up (healthy)` |
| `cmx-minio-init` | **`Exited (0)`** |
| `cmx-adminer` | `Up` |
| `cmx-traefik` | `Up` |

<br>

## Comprobación de bases de datos

**`cmx-minio-init` sale apagado y así tiene que ser.** No está roto. Su único
trabajo es crear el bucket y terminar. `Exited (0)` quiere decir que lo hizo.
`Exited (1)` quiere decir que no: ve a [Problemas](#problemas).

Para verlo con sus palabras:

```bash
docker compose logs minio-init
```

Tiene que decir:

```
Added `local` successfully.
Bucket created successfully `local/canastamx-bronze`.
Bucket canastamx-bronze listo.
```

Los tres `healthy` tardan entre diez y treinta segundos en aparecer. Si corres
`ps -a` de inmediato vas a ver `starting`; espera y vuelve a correrlo.

## 2 · El almacenamiento

Abre **http://localhost:9001** y entra con:

| Campo | Valor |
|---|---|
| Username | tu `S3_ACCESS_KEY` |
| Password | tu `S3_SECRET_KEY` |

**Tiene que aparecer un bucket llamado `canastamx-bronze`, vacío.**

> **El bucket vacío es lo correcto.** Dice *«This location is empty»* y así tiene
> que ser: todavía nadie ha subido nada. Lo que estás comprobando es que exista,
> porque **nadie lo creó a mano** — lo creó `cmx-minio-init` al arrancar. Si está
> ahí, la cadena completa funcionó: el servidor levantó, el cliente lo alcanzó
> por la red interna y tus credenciales sirvieron.

## 3 · Las dos bases de datos

Abre **http://localhost:8080**, que es Adminer. Son **dos entradas distintas** y
Adminer sólo mantiene una sesión a la vez: para la segunda hay que darle a
**«Cerrar sesión»** arriba a la derecha y volver a entrar.

### Base transaccional

| Campo | Valor |
|---|---|
| Motor | PostgreSQL |
| Servidor | `postgres-oltp` |
| Usuario | `canastamx` |
| Contraseña | tu **`OLTP_PASSWORD`** |
| Base de datos | `canastamx_oltp` |

### Base analítica

> **NOTA**
> ---
> **Por qué `postgres-oltp` y no `localhost`:** Adminer corre *dentro* de la red de Docker. Desde ahí, `localhost` es el propio contenedor de Adminer, no tu máquina. Los contenedores se llaman entre sí por el nombre del servicio Desde **tu** máquina, en cambio, sí es `localhost:5432` — por ejemplo si conectas DBeaver. Son dos direcciones distintas para la misma base según desde dónde preguntes, y confundirlas es el error de red más común del proyecto.

| Campo | Valor |
|---|---|
| Motor | PostgreSQL |
| Servidor | `postgres-analytics` |
| Usuario | `canastamx` |
| Contraseña | tu **`ANALYTICS_PASSWORD`** — la otra, no la de arriba |
| Base de datos | `canastamx_analytics` |

> **NOTA**
> ---
> **No existen tablas» es lo correcto.** Las dos bases están creadas y vacías
> porque nadie ha creado ninguna todavía: el servicio de dominio es de la semana
> 7. Lo que compruebas es que la base existe, acepta tus credenciales y
> responde.

### Tabla de direcciones

| Qué | Desde tu máquina | Desde otro contenedor |
|---|---|---|
| MinIO · consola web | http://localhost:9001 | — |
| MinIO · API de objetos | http://localhost:9000 | `http://minio:9000` |
| PostgreSQL transaccional | `localhost:5432` | `postgres-oltp:5432` |
| PostgreSQL analítico | `localhost:5433` | `postgres-analytics:5432` |
| Adminer | http://localhost:8080 | — |
| Traefik · panel | http://localhost:8090 | — |

**Esa columna de la derecha es la que confunde al escribir el `.env`.** El guión
de ingesta se corre desde tu máquina, así que ahí va
`S3_ENDPOINT=http://localhost:9000`. El nombre `minio` sólo existe dentro de la
red de compose.

### Las rutas por nombre - opcional

El sistema también publica dos rutas a través de Traefik:

- http://minio.canastamx.localhost
- http://db.canastamx.localhost

**Si te llevan a otra página** —la bienvenida de XAMPP, una pantalla de IIS, el
panel de tu módem— no están rotas: hay otro programa ocupando el puerto 80 en tu
máquina. Ve a [Problemas](#problemas); son opcionales y los puertos directos de
la tabla de arriba funcionan siempre.

---

# Problemas

| Lo que ves | Qué pasa | Qué hacer |
|---|---|---|
| `Command 'docker' not found` | No está instalado, o en WSL falta la integración | Ver [Requisitos](#requisitos) |
| `Cannot connect to the Docker daemon` | Docker Desktop está cerrado | Ábrelo y espera a que la ballena deje de moverse |
| `port is already allocated` | Otro programa usa ese puerto | Cambia el puerto en tu `.env`: `OLTP_PORT`, `ANALYTICS_PORT`, `S3_PORT`, `ADMINER_PORT`, `TRAEFIK_WEB_PORT` |
| El 5432 ocupado | Tienes PostgreSQL instalado en tu máquina | `OLTP_PORT=5442`. No hace falta desinstalar nada |
| **Las rutas `*.canastamx.localhost` llevan a otra página** | Otro programa escucha en el puerto 80 —**XAMPP es el culpable habitual**— y **Docker no da ningún error** | `TRAEFIK_WEB_PORT=8081` en tu `.env`, `docker compose up -d`, y usa `http://minio.canastamx.localhost:8081` |
| `cmx-minio` reinicia en bucle | Tu `S3_SECRET_KEY` tiene menos de 8 caracteres | Alárgala, `docker compose down -v` y vuelve a subir |
| `cmx-minio-init` sale con `Exited (1)` y dice **`Bucket name cannot be empty`** | El contenedor no recibió `S3_BUCKET` | Tu `.env` tiene los nombres viejos. Corre el guión de [Si ya tenías el proyecto de antes](#si-ya-tenías-el-proyecto-de-antes) |
| `cmx-minio-init` sale con `Exited (1)` y se queja de credenciales | `S3_ACCESS_KEY` o `S3_SECRET_KEY` traen espacios, comillas, `#` o `$` | Déjalas sólo con letras y números |
| `Access Denied` desde el guión de ingesta | Tu `.env` tiene las variables viejas | El mismo guión de migración |
| `variable is not set` al subir | Falta una variable en tu `.env` | Alguien agregó una nueva. Vuelve a copiar `.env.example` y rellénalo |
| `no such host: minio` | Usaste el nombre interno desde tu máquina | Desde tu máquina es `localhost`. Ver la [tabla de direcciones](#4--la-tabla-de-direcciones) |
| Todo en una sola línea al abrir el `.env` | Lo abriste con el Bloc de notas | VS Code, Notepad++ o `nano` |
| `pull access denied` · `manifest unknown` | Docker Hub no responde, o el repositorio quedó privado | Ver [Si Docker Hub falla](#si-docker-hub-falla) |

**El de las rutas `.localhost` merece una nota**, porque es el único que falla en
silencio: `docker compose ps -a` te va a decir que Traefik está `Up` y con el
puerto 80 publicado. Todo verde, sirviendo el contenido equivocado. Si quieres
confirmarlo, abre el panel de Traefik en http://localhost:8090 — si carga y no
marca errores, Traefik está bien y el problema es sólo quién llegó primero al
puerto.

Para ver por qué se cayó algo:

```bash
docker compose logs minio          # o el servicio que falló
docker compose logs --tail 50      # lo último de todos
```

Y para empezar de cero sin dudas:

```bash
docker compose down -v
docker compose up -d
docker compose ps -a
```

---

# Si Docker Hub falla

Las imágenes de MinIO salen de un espejo **nuestro** —`canastamx/minio` y
`canastamx/mc`— precisamente porque el registro original las borró dos veces en
once días. Está contado en el
[ADR 012](../adr/012-de-donde-salen-las-imagenes.md), junto con la comprobación
de que los binarios que traen son exactamente los que publicó MinIO.

**No hace falta cuenta de Docker Hub para descargarlas.** Los dos repositorios
son públicos; está comprobado bajando las seis imágenes sin haber iniciado
sesión.

Si algún día el espejo tampoco responde, las dos imágenes están guardadas como
archivo en el Drive del equipo:

```bash
docker load -i <minio>.tar
docker load -i <mc>.tar
docker compose up -d
```

> **NOTA**
> ---
> Sustituya <minio> o <mc> por los nombres correspondientes a la imagén que desee cargar, por ejemplo, `minio-RELEASE.2025-09-07T16-13-09Z-amd64.tar` o `mc-RELEASE.2025-08-13T08-35-41Z-amd64`.

`docker load` mete la imagen en tu Docker sin descargar nada, y a partir de ahí el compose la encuentra sola.

> **NOTA**
> ---
> - Los `.tar` no están en el repositorio a propósito: pesan más de 10 MB y la
verificación de higiene de la integración continua rechaza archivos de ese
tamaño.  
> - Puedes encontrar las imagenes en la siguiente carpeta de Google Drive: [CanastaMX en Google Drive](https://drive.google.com/drive/folders/1vgHQ__Cq_aq2-Uqg2rrgpQELRfq9CnIR?usp=sharing). Las images están nombradas con su versión y arquitectura.

---

# Qué **no** levanta esto todavía

Sólo la infraestructura: las dos bases, el almacenamiento y la puerta de enlace.
Los servicios de la aplicación —la plataforma de datos, la interfaz analítica, el
servicio de dominio y los dos clientes— todavía no están en el `docker-compose`.
Se van agregando conforme cada frente los tenga.

Así que si levantas esto y no ves «la aplicación» por ningún lado, está bien: no
existe aún. Lo que existe es el suelo donde se va a parar.

---

# Registro de verificación

Esta guía se verifica con una regla: **alguien que no la escribió la sigue en su
máquina, sin preguntar.** Si tiene que preguntar algo, se arregla el documento,
no se le explica a esa persona.

| Quién | Sistema | Fecha | ¿Llegó al final sin preguntar? | Qué se atoró |
|---|---|---|---|---|
| Ariadne (A) | Windows + WSL 2 · Edge | 27-09-2026 | No | Docker no instalado; nombres del `.env` distintos a los de la guía; `minio-init` fallaba; `ps` sin `-a`; las rutas de Traefik iban a XAMPP |
| *(por definir)* | Windows nativo | | | |

**La columna «qué se atoró» es la más útil de la tabla.** Cada cosa anotada ahí
es una línea que le faltaba a la guía, y es lo que hace que la siguiente persona
no se atore igual.
