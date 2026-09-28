# Levantar CanastaMX en tu máquina

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

1. [Instalación y Configuración del entorno](#instalación-y-configuración-del-entorno)
2. [Ejecución y Paro](#ejecución-y-paro)
3. [Comprobación](#comprobación)
4. [Troubleshooting](#troubleshooting)

---

<br><br>

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
git clone https://github.com/arik36/canastamx.git
cd canastamx
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
cp .env.example .env
```

Abra el archivo `.env` con un editor de texto.

El archivo contiene unas variables con valor ya establecido y otras vacías. Es necesario completar los campos vacíos con valores que usted defina, a continuación se muestra una tabla con los campos **necesarios** de definir y qué valores debe asignar.

| Variable | Qué poner |
|---|---|
| `OLTP_PASSWORD` | lo que quieras, sin espacios |
| `ANALYTICS_PASSWORD` | lo que quieras, sin espacios |
| `S3_ACCESS_KEY` | mínimo 3 caracteres |
| `S3_SECRET_KEY` | **mínimo 8 caracteres** — con menos, MinIO no arranca y el error no lo dice claro |

<br><br>

# Ejecución y Desactivación

> **IMPORTANTE**
> ---
> - Es absolutamente necesario que haya realizado la configuración del `.env` correctamente. En algunos casos, Docker no avisará explicitamente que existe un error, pero los servicios podrían fallar internamente.  
> 
> Si se encuentra con algún problema, consulte la sección de [Troubleshooting](#troubleshooting).

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
docker compose ps
```

`docker compose ps` tiene que mostrar seis contenedores:

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
docker compose down        # apaga, conserva los datos
docker compose down -v     # apaga y BORRA los datos (bases y bucket)
```

`down -v` es el que deja la máquina como recién clonada. Es el que se usa para
probar esta guía; en el día a día, `down` a secas.

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

**Tiene que existir un bucket llamado `canastamx-bronze`.** Nadie lo creó a
mano: lo creó `cmx-minio-init` al arrancar. Si está ahí, la cadena completa
funcionó — el servidor levantó, el cliente lo alcanzó por la red interna y las
credenciales del `.env` sirvieron.

<br>

## Comprobación de bases de datos

Abre **http://localhost:8080**, que es Adminer, y entra con:

| Campo | Valor |
|---|---|
| Motor | PostgreSQL |
| Servidor | `postgres-oltp` *(el nombre del servicio, no `localhost`)* |
| Usuario | `canastamx` |
| Contraseña | tu `OLTP_PASSWORD` |
| Base de datos | `canastamx_oltp` |

Y lo mismo con `postgres-analytics` / `canastamx_analytics` para la otra.

> **NOTA**
> ---
> **Por qué `postgres-oltp` y no `localhost`:** Adminer corre *dentro* de la red de Docker. Desde ahí, `localhost` es el propio contenedor de Adminer, no tu máquina. Los contenedores se llaman entre sí por el nombre del servicio Desde **tu** máquina, en cambio, sí es `localhost:5432` — por ejemplo si conectas DBeaver. Son dos direcciones distintas para la misma base según desde dónde preguntes, y confundirlas es el error de red más común del proyecto.

<br>

## Tabla de direcciones

| Qué | Desde tu máquina | Desde otro contenedor |
|---|---|---|
| MinIO · consola web | http://localhost:9001 | — |
| MinIO · API de objetos | http://localhost:9000 | `http://minio:9000` |
| PostgreSQL transaccional | `localhost:5432` | `postgres-oltp:5432` |
| PostgreSQL analítico | `localhost:5433` | `postgres-analytics:5432` |
| Adminer | http://localhost:8080 | — |
| Panel de Traefik | http://localhost:8090 | — |

**Esa columna de la derecha es la que va en el `.env` del guión de ingesta.** Si lo corres desde tu máquina, `S3_ENDPOINT=http://localhost:9000`. Si algún día corre dentro de un contenedor, `http://minio:9000`.

---

<br><br>

# Troubleshooting

| Lo que ves | Qué pasa | Qué hacer |
|---|---|---|
| `port is already allocated` | otro programa ya usa ese puerto | cambia el puerto en tu `.env` (`OLTP_PORT`, `S3_PORT`, `ADMINER_PORT`, `TRAEFIK_WEB_PORT`) y vuelve a subir |
| El 5432 ocupado | tienes PostgreSQL instalado en tu máquina | pon `OLTP_PORT=5442` en el `.env`. No hace falta desinstalar nada |
| El 80 ocupado (Windows) | IIS o el servicio de publicación web | `TRAEFIK_WEB_PORT=8081` |
| `cmx-minio` reinicia en bucle | tu `S3_SECRET_KEY` tiene menos de 8 caracteres | alárgala, `down -v` y vuelve a subir |
| `cmx-minio-init` sale con `exited (1)` | las credenciales del `.env` no le sirvieron a MinIO | revisa que `S3_ACCESS_KEY` y `S3_SECRET_KEY` no tengan espacios ni comillas |
| `Access Denied` desde el guión de ingesta | tu `.env` tiene las variables viejas `MINIO_*` | renómbralas a `S3_*` y agrega `S3_ENDPOINT` |
| `no such host: minio` | usaste el nombre interno desde tu máquina | desde tu máquina es `localhost`, no `minio` — ver la tabla de la sección 3 |
| `variable is not set` al subir | falta una variable en tu `.env` | vuelve a copiar `.env.example` y rellénalo; alguien agregó una variable nueva |
| `pull access denied` / `manifest unknown` | Docker Hub no responde o el repositorio quedó privado | ve a la sección 6 |

Para ver por qué se cayó algo:

```bash
docker compose logs minio          # o el servicio que falló
docker compose logs --tail 50      # lo último de todos
```

## Docker Hub

Las imágenes de MinIO salen de un espejo **nuestro** —`canastamx/minio` y
`canastamx/mc`— precisamente porque el registro original las borró dos veces en once días. Está contado en [ADR 011](../adr/011-de-donde-salen-las-imagenes.md), con la comprobación de que los binarios que traen son los que publicó MinIO.

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