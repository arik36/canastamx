# Levantar CanastaMX en tu máquina

> **Guía verificada.** El 27 de septiembre alguien que no la escribió intentó
> seguirla en una máquina limpia. Todo lo que aparece aquí está probado; lo que
> se atoró está en la sección de [Problemas](#problemas), con el texto literal
> del error. El registro de esa prueba está en
> [`verificacion-arranque-2026-09-27.md`](../equipo/verificacion-arranque-2026-09-27.md).

## Índice

1. [Requisitos](#requisitos)
2. [Configuración del entorno](#configuración-del-entorno)
3. [Ejecución y paro](#ejecución-y-paro)
4. [Comprobación](#comprobación)
5. [Problemas](#problemas)
6. [Si Docker Hub falla](#si-docker-hub-falla)

---

# Requisitos

**Antes de esto** tienes que haber preparado tu máquina siguiendo
[`instalar/README.md`](../equipo/instalar/README.md): Git configurado y el repositorio
clonado.

Además, **para esta guía hacen falta dos cosas que la guía de instalación no
te pidió**, porque hasta ahora no las necesitabas:

| | |
|---|---|
| **Docker Desktop instalado** | Descárgalo de [docker.com](https://www.docker.com/products/docker-desktop/) |
| **Docker Desktop abierto** | No basta con instalarlo. Si el programa está cerrado, nada de esto funciona |

> **Al abrirlo por primera vez te va a pedir iniciar sesión.** No hace falta
> cuenta: hay un **`Skip`** en azul, arriba a la derecha del recuadro. Es pequeño
> y la pantalla está hecha para que parezca obligatorio.

**Si trabajas en WSL**, falta un paso más y sin él `docker` no existe dentro de
Ubuntu aunque Docker Desktop esté corriendo en Windows:

> Docker Desktop → **Settings** (el engrane) → **Resources** → **WSL
> Integration** → activa el interruptor de tu Ubuntu → **Apply & Restart**.

## Comprobar que quedó

En la terminal donde vas a trabajar:

```bash
docker --version
docker compose version
docker info --format '{{.ServerVersion}}'
```

Los tres tienen que responder con un número de versión.

| Lo que ves | Qué significa |
|---|---|
| `Command 'docker' not found` | No está instalado, o falta la integración con WSL |
| `Cannot connect to the Docker daemon` | Está instalado pero **Docker Desktop está cerrado**. Ábrelo |

**Cómo clonaste no importa aquí.** Por HTTPS o por SSH, da igual: Docker no sabe
ni le interesa de dónde salió la carpeta.

---

# Configuración del entorno

## Si es tu primera vez

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

**Sólo letras y números.** Nada de espacios, comillas, `#` ni `$`:

- un `#` inicia un comentario y te corta la contraseña a la mitad
- un `$` se interpreta como el nombre de otra variable

**Son tuyas y son locales.** No tienen que coincidir con las de nadie, y no se
suben a ningún lado: el `.env` está en `.gitignore`.

`JWT_SECRET`, `INEGI_API_TOKEN` y `PROFECO_QQP_URL` se quedan vacías: ningún
servicio las usa todavía.

### Comprobar que quedó, sin enseñar tus contraseñas

```bash
awk -F= '/^(OLTP_PASSWORD|ANALYTICS_PASSWORD|S3_ACCESS_KEY|S3_SECRET_KEY)=/ \
  {printf "%-20s %d caracteres\n", $1, length($2)}' .env
```

Las cuatro tienen que dar más de cero, y `S3_SECRET_KEY` ocho o más.

## Si ya tenías el proyecto de antes · **importante**

**Tu `.env` viejo tiene nombres que ya no existen.** El
[ADR 009](../adr/009-almacenamiento-de-objetos.md) renombró las variables de
MinIO y agregó `S3_ENDPOINT`.

Y esto **no se arregla solo con `git pull`**: el `.env` está en `.gitignore`, así
que lo que se actualiza es la plantilla, no tu archivo. El tuyo se queda como
estaba, con los nombres viejos, y MinIO te va a decir `Access Denied` sin
explicar por qué.

Pega esto en la raíz del proyecto. Conserva tus contraseñas —sólo cambia el
nombre a la izquierda del `=`— y se puede correr dos veces sin hacer daño:

```bash
python3 - <<'PY'
import pathlib
CAB = "# --- Almacenamiento de objetos · capa bronze (A) ---"
FIN = ("S3_CONSOLE_PORT=9001\n"
       "\n"
       "# El guion de ingesta corre en TU maquina, no dentro de compose.\n"
       "# Dentro de la red de compose el nombre seria http://minio:9000\n"
       "S3_ENDPOINT=http://localhost:9000")

for nombre in (".env.example", ".env"):
    p = pathlib.Path(nombre)
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8")
    t = t.replace("# --- MinIO (capa bronze · A) ---", CAB)
    t = t.replace("MINIO_ROOT_USER=",     "S3_ACCESS_KEY=")
    t = t.replace("MINIO_ROOT_PASSWORD=", "S3_SECRET_KEY=")
    t = t.replace("S3_ROOT_USER=",        "S3_ACCESS_KEY=")
    t = t.replace("S3_ROOT_PASSWORD=",    "S3_SECRET_KEY=")
    t = t.replace("MINIO_BUCKET=",        "S3_BUCKET=")
    t = t.replace("MINIO_PORT=",          "S3_PORT=")
    t = t.replace("MINIO_CONSOLE_PORT=",  "S3_CONSOLE_PORT=")
    if "S3_ENDPOINT" not in t:
        t = t.replace("S3_CONSOLE_PORT=9001", FIN)
    p.write_text(t, encoding="utf-8")
    print(nombre, "corregido")
PY
```

Y comprueba que quedaron las seis:

```bash
grep -nE "^S3_" .env | sed 's/=.*/=…/'
```

Tienen que salir `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET`, `S3_PORT`,
`S3_CONSOLE_PORT` y `S3_ENDPOINT`. El `sed` del final les corta el valor, así que
puedes pegar esa salida en el chat sin pensarlo.

Si prefieres empezar de cero: borra tu `.env`, vuelve a copiar `.env.example` y
rellénalo a mano. Es igual de válido.

---

# Ejecución y paro

## Primera ejecución

Desde la raíz del proyecto, con Docker Desktop abierto:

```bash
docker compose up -d
```

**La primera vez tarda alrededor de 35 segundos**, porque descarga seis
imágenes. Las siguientes, unos 17. Hay un tramo al final en que la pantalla no
se mueve: es la espera a que MinIO se reporte sano antes de arrancar el
contenedor que crea el bucket. **No lo canceles.**

## Ejecuciones siguientes

El mismo comando. Ya no descarga nada.

```bash
docker compose up -d
```

## Paro

```bash
docker compose down        # apaga y CONSERVA los datos
docker compose down -v     # apaga y BORRA los datos (bases y bucket)
```

`down -v` deja la máquina como recién clonada. Es el que se usa para probar esta
guía; en el día a día, `down` a secas.

---

# Comprobación

Que los contenedores digan `running` sólo prueba que arrancaron, no que sirvan.
Esto es lo que lo prueba.

## 1 · Los seis contenedores

```bash
docker compose ps -a
```

> **La `-a` no es opcional.** Sin ella, `docker compose ps` sólo enseña los que
> están corriendo, y uno de los seis termina a propósito. Vas a contar cinco y
> a buscar el sexto sin encontrarlo nunca.

| Contenedor | Estado esperado |
|---|---|
| `cmx-postgres-oltp` | `Up (healthy)` |
| `cmx-postgres-analytics` | `Up (healthy)` |
| `cmx-minio` | `Up (healthy)` |
| `cmx-minio-init` | **`Exited (0)`** |
| `cmx-adminer` | `Up` |
| `cmx-traefik` | `Up` |

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

| Campo | Valor |
|---|---|
| Motor | PostgreSQL |
| Servidor | `postgres-analytics` |
| Usuario | `canastamx` |
| Contraseña | tu **`ANALYTICS_PASSWORD`** — la otra, no la de arriba |
| Base de datos | `canastamx_analytics` |

> **«No existen tablas» es lo correcto.** Las dos bases están creadas y vacías
> porque nadie ha creado ninguna todavía: el servicio de dominio es de la semana
> 7. Lo que compruebas es que la base existe, acepta tus credenciales y
> responde.

> **Por qué `postgres-oltp` y no `localhost`.** Adminer corre *dentro* de la red
> de Docker. Desde ahí, `localhost` es el propio contenedor de Adminer, no tu
> máquina. Los contenedores se llaman entre sí por el nombre del servicio. Desde
> **tu** máquina, en cambio, sí es `localhost:5432` — por ejemplo si conectas
> DBeaver. Son dos direcciones distintas para la misma base según desde dónde
> preguntes, y confundirlas es el error de red más común del proyecto.

## 4 · La tabla de direcciones

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

## 5 · Las rutas por nombre · opcional

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
docker load -i <archivo-de-minio>.tar
docker load -i <archivo-de-mc>.tar
docker compose up -d
```

`docker load` mete la imagen en tu Docker sin descargar nada, y a partir de ahí
el compose la encuentra sola.

> Los nombres exactos de los dos archivos están en la carpeta del Drive, junto a
> ellos. Llevan la versión y la arquitectura en el nombre a propósito: `docker
> save` guarda sólo la arquitectura de la máquina donde se corrió, así que el
> archivo `amd64` no sirve en la máquina virtual y al revés.
>
> Carpeta: [CanastaMX en Google Drive](https://drive.google.com/drive/folders/1vgHQ__Cq_aq2-Uqg2rrgpQELRfq9CnIR?usp=sharing)

Los `.tar` no están en el repositorio a propósito: pesan más de 10 MB y la
verificación de higiene de la integración continua rechaza archivos de ese
tamaño.

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
