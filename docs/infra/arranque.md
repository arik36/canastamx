# Levantar CanastaMX en tu máquina

**Antes de esto** tienes que haber preparado tu máquina:
[`instalar/README.md`](../equipo/instalar/README.md). Ahí se instalan Git y Docker. Aquí
se levanta el sistema, que es lo siguiente.

## Indíce

1. [Instalación y Configuración del entorno](#instalación-y-configuración-del-entorno)
2. [Ejecución y Paro](#ejecución-y-paro)
3. [Comprobación](#comprobación)
4. [Troubleshooting](#troubleshooting)

---

<br><br>

# Instalación y Configuración del entorno

## Instalación

Una vez cumplidos los requerimientos básicos (veáse Readme.md), el primer paso es clonar el repositorio (generar una copia del proyecto CanastaMX). Para ello se deben ejecutar los siguientes comandos en una terminal:

```bash
git clone https://github.com/arik36/canastamx.git
cd canastamx
```

## Configuración del entorno

**El siguiente paso es generar el archivo `.env`, necesario para levantar los servicios requeridos por el proyecto a través de Docker.** 

Antes de continuar, debe crear el archivo `.env` a partir de la plantilla proporcionada junto al proyecto `.env.example`. Este archivo se encuentra en la raíz del proyecto.

```bash
cp .env.example .env
```

Abra el archivo .env con un editor de texto.

El archivo trae unas variables con valor y otras vacías. Las vacías las inventas tú: son contraseñas de tu copia local, no tienen que coincidir con las de nadie.

Las que sí importa no dejar en blanco para arrancar:

| Variable | Qué poner |
|---|---|
| `OLTP_PASSWORD` | lo que quieras, sin espacios |
| `ANALYTICS_PASSWORD` | lo que quieras, sin espacios |
| `S3_ACCESS_KEY` | mínimo 3 caracteres |
| `S3_SECRET_KEY` | **mínimo 8 caracteres** — con menos, MinIO no arranca y el error no lo dice claro |

> **Si ya tenías el proyecto de antes**, tu `.env` viejo tiene variables
> `MINIO_*` que ya no existen. Cambiaron de nombre a `S3_*` por el
> [ADR 009](../adr/009-almacenamiento-de-objetos.md). Lo más rápido es borrar
> tu `.env`, volver a copiar el ejemplo y rellenarlo.

<br><br>

# Ejecución y Paro

En está sección se describirán los pasos para ejecutar y parar el proyecto.

## Primera ejecución

> **Durante la primera ejecución es necesario contar con una conexión estable a internet**

> **Es necesario haber realizado la configuración del entorno para ejecutar el proyecto.**

Para ejecutar el proyecto, se requiere tener una terminal con el directorio de trabajo establecido en la ruta de la raíz del proyecto (/canastamx).

En esa terminal, ejecute el siguiente comando

```bash
docker compose up -d
```

Al ejecutarse, se descargarán las imagenes necesarias y se creará un contenedor de docker. La terminal mostrará el progreso de estás acciones, e informará si se encuentra algún error. 

Al finalizar con éxito, el contenedor permanecerá activo. Si se requiere, puede verificar el estado de los servicios mediante el siguiente comando:

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

> Los tres `healthy` tardan entre diez y treinta segundos en aparecer. Si corres
`docker compose ps` de inmediato vas a ver `starting`; espera y vuelve a correrlo.

## Ejecución

Para cualquier ejecución subsecuente a la primera ejecución, simplemente ejecutar el siguiente comando desde la raíz del proyecto en una terminal:

```bash
docker compose up -d
```

## Paro

```bash
docker compose down        # apaga, conserva los datos
docker compose down -v     # apaga y BORRA los datos (bases y bucket)
```

`down -v` es el que deja la máquina como recién clonada. Es el que se usa para
probar esta guía; en el día a día, `down` a secas.

---

<br><br>

# Comprobación

En está sección se describe cómo se puede comprobar las funcionalidades del sistema.

> Que los contenedores digan `running` sólo prueba que arrancaron, no que sirvan.

## Comprobación almacenamiento

Abre **http://localhost:9001** y entra con el `S3_ACCESS_KEY` y el
`S3_SECRET_KEY` que pusiste en tu `.env`.

**Tiene que existir un bucket llamado `canastamx-bronze`.** Nadie lo creó a
mano: lo creó `cmx-minio-init` al arrancar. Si está ahí, la cadena completa
funcionó — el servidor levantó, el cliente lo alcanzó por la red interna y las
credenciales del `.env` sirvieron.

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

> **Por qué `postgres-oltp` y no `localhost`:** Adminer corre *dentro* de la red
> de Docker. Desde ahí, `localhost` es el propio contenedor de Adminer, no tu
> máquina. Los contenedores se llaman entre sí por el nombre del servicio. Desde
> **tu** máquina, en cambio, sí es `localhost:5432` — por ejemplo si conectas
> DBeaver. Son dos direcciones distintas para la misma base según desde dónde
> preguntes, y confundirlas es el error de red más común del proyecto.

## Tabla de direcciones

| Qué | Desde tu máquina | Desde otro contenedor |
|---|---|---|
| MinIO · consola web | http://localhost:9001 | — |
| MinIO · API de objetos | http://localhost:9000 | `http://minio:9000` |
| PostgreSQL transaccional | `localhost:5432` | `postgres-oltp:5432` |
| PostgreSQL analítico | `localhost:5433` | `postgres-analytics:5432` |
| Adminer | http://localhost:8080 | — |
| Panel de Traefik | http://localhost:8090 | — |

**Esa columna de la derecha es la que va en el `.env` del guión de ingesta.** Si
lo corres desde tu máquina, `S3_ENDPOINT=http://localhost:9000`. Si algún día
corre dentro de un contenedor, `http://minio:9000`.

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
`canastamx/mc`— precisamente porque el registro original las borró dos veces en
once días. Está contado en
[ADR 011](../adr/011-de-donde-salen-las-imagenes.md), con la comprobación de que
los binarios que traen son los que publicó MinIO.

Si algún día el espejo tampoco responde, las dos imágenes están guardadas como
archivo en el Drive del equipo:

```bash
docker load -i minio.tar
docker load -i mc.tar
docker compose up -d
```

`docker load` mete la imagen en tu Docker sin descargar nada, y a partir de ahí el compose la encuentra sola.

> Los `.tar` no están en el repositorio a propósito: pesan más de 10 MB y la
verificación de higiene de la integración continua rechaza archivos de ese
tamaño.
> Puedes encontrar las imagenes en la siguiente carpeta de Google Drive: [CanastaMX en Google Drive](https://drive.google.com/drive/folders/1vgHQ__Cq_aq2-Uqg2rrgpQELRfq9CnIR?usp=sharing)

---