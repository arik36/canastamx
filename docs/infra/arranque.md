# Levantar CanastaMX en tu máquina

> **Para quién es.** Para quien nunca ha usado Docker. Cada paso dice qué
> escribir, qué tienes que ver y qué hacer si ves otra cosa. Si algo no coincide,
> no improvises: busca el texto del error en [Problemas](#problemas).
>
> **La regla de esta guía:** la única cosa tuya que cambias es tu `.env`. Nunca
> `docker-compose.yml` ni `.env.example`.

**En corto**, para quien ya lo hizo una vez:

```bash
docker compose version                  # Docker responde
git switch main && git pull             # repositorio al día
cp .env.example .env                    # sólo la primera vez; luego llénalo
docker compose config --quiet && echo "✓ compose válido"
docker compose up -d                    # levanta todo
docker compose ps -a                    # 5 «Up» y minio-init en «Exited (0)»
```

---

## Qué vas a levantar

Seis contenedores que viven en una red privada llamada `canastamx`. Dentro de
esa red se llaman entre sí por su **nombre de servicio**; desde tu navegador
entras por **localhost** y el puerto que diga tu `.env`.

| Contenedor | Qué es | Qué hace | Quién lo usa | Puerto en tu máquina |
|---|---|---|---|---|
| `cmx-postgres-oltp` | PostgreSQL 16 | La base **transaccional**: usuarios, canastas y alertas | C1, desde el servicio de dominio | `OLTP_PORT` · 5432 |
| `cmx-postgres-analytics` | PostgreSQL 16 | El **almacén analítico**: capas intermedia y de consumo, cuarentena y esquema estrella | A, y la API analítica que consumen C2 y D | `ANALYTICS_PORT` · 5433 |
| `cmx-minio` | Almacenamiento de objetos compatible con S3 | Guarda la **capa cruda** (bronze): los archivos Parquet tal como llegan | A, desde la ingesta | `S3_PORT` · 9000 (API) y `S3_CONSOLE_PORT` · 9001 (consola web) |
| `cmx-minio-init` | El cliente `mc` de MinIO | Espera a que MinIO esté sano, **crea el bucket `canastamx-bronze` y se apaga** | Nadie lo usa directo | ninguno |
| `cmx-adminer` | Cliente web de bases de datos | Te deja asomarte a las dos bases sin instalar nada | Todos | `ADMINER_PORT` · 8080 |
| `cmx-traefik` | Puerta de enlace | Da nombres a los servicios (`minio.canastamx.localhost`, `db.canastamx.localhost`) y, más adelante, a la aplicación | Todos | `TRAEFIK_WEB_PORT` · 80 y `TRAEFIK_DASHBOARD_PORT` · 8090 |

Los datos viven en tres **volúmenes** (`oltp-data`, `analytics-data` y
`minio-data`). Un volumen sobrevive aunque apagues o borres los contenedores:
sólo `docker compose down -v` lo borra.

> **Cada quien tiene su propia copia de todo.** Lo que levantas vive en **tu**
> máquina y está vacío. Los datos que A ingiere están en el MinIO de A, no en el
> tuyo, y nada de lo que hagas aquí le llega a otro integrante.

---

## Paso 1 · Elige tu camino

Todos los comandos de esta guía son de **bash**, y funcionan igual en las tres
terminales de abajo. **No uses CMD ni PowerShell** para seguir esta guía: ahí no
existen `cp`, `grep` ni `awk`.

| Clave | Sistema | Terminal | Tu repositorio (según `docs/equipo/entorno/`) |
|---|---|---|---|
| A | Windows + WSL | Ubuntu, en Windows Terminal | `~/projects/canastamx` |
| B | Fedora | la terminal de Linux | `~/Projects/canastamx` |
| C1 | Windows 11 | **Git Bash**, en VS Code | `/d/projects/canastamx` |
| C2 | Windows 11 | **Git Bash**, en VS Code | `"/c/Users/renat/Documents/Universidad/9no Semestre/Liss/Proyecto integrador/Proyecto/canastamx"` |
| D | Windows 11 | **Git Bash** | `/c/Users/PC/ProjectsGIT/canastamx` |

> **¿Tengo que volver a clonar el repositorio dentro de Linux? No.** Sigue usando
> el clon que ya tienes, con la terminal que ya usas:
>
> - Docker Desktop funciona desde Git Bash. Ubuntu sólo hace falta si ya
>   trabajas ahí, como A.
> - Tus herramientas —Java y Maven, Node— están instaladas en Windows. Un clon
>   dentro de Linux no las ve.
> - El repositorio fuerza saltos de línea de Linux en todos los archivos de
>   texto (`.gitattributes`), así que los guiones `.sh` corren bien aunque lo
>   hayas clonado en Windows.
> - **Dos clones es peor que uno.** Los dos se llaman `canastamx`, así que Docker
>   los trata como el mismo proyecto y comparten las bases. Pero cada clon tiene
>   su propio `.env`: con dos contraseñas distintas, una de las dos deja de
>   entrar.
>
> Si ya trabajas en WSL y tu repositorio está en `/mnt/c`, puedes correr Docker
> desde ahí. Haz tus commits desde Windows, porque Git desde WSL sobre `/mnt/c`
> va muy lento.

**Cómo abrir la terminal en la carpeta del repositorio**

- **Git Bash en VS Code:** abre la carpeta del proyecto, luego *Terminal → New
  Terminal*. En la flecha ⌄ junto al `+`, elige **Git Bash**.
- **WSL:** abre *Ubuntu* desde el menú Inicio y escribe `cd ~/projects/canastamx`.

Para saber si estás en el lugar correcto, escribe `ls`. Tienes que ver
`docker-compose.yml` y `README.md` en la lista. Si no aparecen, no sigas: estás
en otra carpeta.

---

## Paso 2 · Instala Docker

### Windows (A, C1, C2 y D)

1. Descarga **Docker Desktop for Windows** desde docker.com. Casi todas las
   laptops usan la versión **AMD64**; la ARM64 es sólo para equipos con
   procesador Snapdragon.
2. Instálalo con la opción **«Use WSL 2»** marcada, que viene por omisión.
   Reinicia si te lo pide.
3. Ábrelo. Acepta el acuerdo de servicio: es gratis para uso educativo.
4. **No inicies sesión.** En la pantalla de bienvenida elige saltar el paso. No
   hace falta cuenta para descargar imágenes públicas.
5. Espera a que abajo a la izquierda diga **«Engine running»**.

Si al abrirlo te dice que hay que actualizar WSL, abre **PowerShell como
administrador**, escribe `wsl --update` y reinicia.

**Sólo si usas WSL (A):** en Docker Desktop entra a *Settings → Resources → WSL
integration*, activa tu **Ubuntu** y dale **Apply & restart**. Después **cierra y
vuelve a abrir** la terminal de Ubuntu. Sin esto, `docker` va a decir *command
not found* dentro de Ubuntu aunque Docker Desktop esté corriendo. Es el tropiezo
clásico.

**Sólo si usas Git Bash (C1, C2 y D):** cierra **por completo** VS Code y Git
Bash, y vuelve a abrirlos. La terminal que ya estaba abierta no sabe que Docker
existe.

### Linux (B)

Docker Engine con el complemento `compose`. Agrega tu usuario al grupo `docker`
(`sudo usermod -aG docker $USER`) y vuelve a iniciar sesión, para no usar `sudo`
en cada comando.

---

## Paso 3 · Comprueba que Docker responde

```bash
docker --version
docker compose version
docker info --format '{{.ServerVersion}} · {{.OSType}}/{{.Architecture}}'
```

Cada línea tiene que responder con una versión. La tercera tiene que decir
**`linux`** en medio, por ejemplo `28.4.0 · linux/x86_64`. El número de versión
no importa.

| Si ves | Qué pasa | Qué haces |
|---|---|---|
| `command not found` en Git Bash | La terminal se abrió antes de instalar Docker | Cierra VS Code por completo y vuelve a abrirlo |
| `command not found` en Ubuntu | Falta la integración con WSL | *Settings → Resources → WSL integration* (Paso 2) |
| `Cannot connect to the Docker daemon` o `error during connect` | Docker Desktop está cerrado o todavía está arrancando | Ábrelo y espera a que diga *Engine running* |
| La tercera dice `windows/…` | Docker está en modo de contenedores de Windows | Clic derecho en la ballena → *Switch to Linux containers* |

---

## Paso 4 · Pon tu repositorio al día

Desde la carpeta del repositorio:

```bash
git switch main
git pull
```

Esto importa aquí porque trae la versión vigente de `docker-compose.yml` y de
`.env.example`.

Opcional, pero útil. Cambia `C1` por tu clave:

```bash
bash infra/scripts/verificar-base.sh C1
```

Tiene que terminar en verde con **«PUEDES CREAR TU RAMA.»** Este guión revisa tu
clon y las herramientas de tu frente. **No revisa Docker**, salvo para A y B.

---

## Paso 5 · Crea y llena tu `.env`

El `.env` le dice a Docker con qué contraseñas crear **tus** bases y tu MinIO, y
en qué puertos de tu máquina publicarlos. Es sólo tuyo: **nunca se sube al
repositorio**, y el gancho de `pre-commit` y la integración continua lo impiden.

```bash
cp .env.example .env
```

Ábrelo con **VS Code** (`code .env`) o con **nano** (`nano .env`). En nano se
guarda con `Ctrl+O` y `Enter`, y se sale con `Ctrl+X`.

> **Si usas el Bloc de notas**, el riesgo no es cómo se ve el archivo: es que lo
> guarde como `.env.txt`. Mejor VS Code.

### Los cuatro valores que tú inventas

| Variable | Qué poner | Por qué |
|---|---|---|
| `OLTP_PASSWORD` | mínimo 8 caracteres | Contraseña de tu base transaccional |
| `ANALYTICS_PASSWORD` | mínimo 8 caracteres, **distinta** de la anterior | Contraseña de tu base analítica |
| `S3_ACCESS_KEY` | mínimo 3 caracteres, por ejemplo `canastamx` | Es el **usuario** de MinIO |
| `S3_SECRET_KEY` | **mínimo 8 caracteres** | Es la contraseña de MinIO. Con menos, MinIO no arranca |

**Usa sólo letras, números, `-` y `_`.** Nada de espacios, comillas, `#`, `$` ni
`=`. Docker lee el `$` como el inicio de una variable, así que una contraseña con
`$` llega cortada sin avisar.

**Decide tus contraseñas ahora.** Postgres guarda la contraseña de la primera vez
que levantas. Si después la cambias en el `.env`, la base no se entera y te va a
decir *password authentication failed*. Cómo arreglarlo está en
[Problemas](#problemas).

**No compartas tu `.env`**: ni por WhatsApp, ni en capturas, ni en un *issue*.
Esas contraseñas sólo abren servicios de tu máquina, pero tu máquina publica esos
puertos en la red donde estés conectado. En el Wi-Fi de la escuela, una
contraseña débil es una base abierta. Si Windows te pregunta si Docker puede usar
la red, permite **sólo redes privadas**.

### Comprueba tus contraseñas

Copia y pega esto completo:

```bash
awk -F= '
  $1 ~ /^(OLTP_PASSWORD|ANALYTICS_PASSWORD|S3_SECRET_KEY)$/ {min=8}
  $1 == "S3_ACCESS_KEY" {min=3}
  $1 ~ /^(OLTP_PASSWORD|ANALYTICS_PASSWORD|S3_ACCESS_KEY|S3_SECRET_KEY)$/ {
    v=$0; sub(/^[^=]*=/, "", v); crlf=sub(/\r$/, "", v); n=length(v)
    if (crlf)                      r="✗ saltos de línea de Windows (CRLF)"
    else if (n < min)              r="✗ mínimo " min
    else if (v ~ /[^A-Za-z0-9_-]/) r="✗ sólo letras, números, - y _"
    else                           r="✓"
    printf "  %-20s %3d caracteres  %s\n", $1, n, r
  }' .env
```

Tienen que salir **cuatro renglones con ✓**. Si alguno dice ✗, corrígelo en el
`.env`, guarda y vuelve a correrlo.

Si sale *saltos de línea de Windows*, en VS Code haz clic donde dice **CRLF**,
abajo a la derecha, cámbialo a **LF** y guarda.

### Si un puerto ya está ocupado, cambias tu `.env` y nada más

Todos los puertos que Docker publica en tu máquina salen del `.env`. Si otro
programa ya usa uno, cambia **sólo el número** en tu `.env`:

| Síntoma | Qué cambias en tu `.env` |
|---|---|
| Tienes XAMPP, IIS u otro servidor web usando el 80 | `TRAEFIK_WEB_PORT=8880` |
| Tienes PostgreSQL instalado en Windows | `OLTP_PORT=5442` |
| Otro programa usa el 8080 | `ADMINER_PORT=8088` |
| Otro programa usa el 9000 | `S3_PORT=9010` **y también** `S3_ENDPOINT=http://localhost:9010` |

La última fila es la única con trampa: `S3_ENDPOINT` repite el puerto de
`S3_PORT`, así que se cambian juntos.

> **El 8081, no.** Es el puerto del servicio de dominio
> (`services/domain-service/src/main/resources/application.properties`). Hasta el
> 5 de octubre esta guía lo sugería por error. Si lo pusiste, cámbialo a `8880` y
> corre `docker compose up -d traefik`.

Cambiar un puerto también cambia la dirección que abres en el navegador. Por eso
el Paso 8 te imprime **tus** direcciones, leídas de tu `.env`.

---

## Paso 6 · Tres comprobaciones antes de levantar

```bash
# 1 · No modificaste los archivos del equipo. No debe imprimir nada.
git status --short docker-compose.yml .env.example

# 2 · Tu .env tiene todas las variables del ejemplo
faltan=$(grep -oE '^[A-Z0-9_]+=' .env.example | grep -vxFf <(grep -oE '^[A-Z0-9_]+=' .env))
[ -z "$faltan" ] && echo "✓ tu .env tiene todas las variables" || echo "✗ le faltan: $(echo $faltan | tr -d '=')"

# 3 · El compose se puede leer con tu .env
docker compose config --quiet && echo "✓ compose válido"
```

Qué hacer con cada resultado:

- **Si la 1 imprime algo**, cambiaste un archivo que no es tuyo. Déjalo como
  estaba con `git restore docker-compose.yml .env.example`.
- **Si la 2 dice que faltan variables**, alguien agregó una nueva. Cópiala de
  `.env.example` a tu `.env` y llénala.
- **La 3 valida el archivo y avisa si falta una variable.** No avisa si una
  contraseña está vacía: eso lo revisó el Paso 5.

Repite este paso **cada vez que hagas `git pull`**.

---

## Paso 7 · Levanta los servicios

```bash
docker compose up -d
```

La primera vez descarga cinco imágenes: `postgres`, `canastamx/minio`,
`canastamx/mc`, `adminer` y `traefik`. Postgres se usa dos veces. Puede tardar
unos minutos según tu internet. Deja al menos **5 GB libres** en disco.

Ahora mira el estado. **Con `-a`**, porque sin él no aparecen los contenedores
que ya terminaron:

```bash
docker compose ps -a
```

En la columna **STATUS** tiene que decir:

| Contenedor | STATUS esperado |
|---|---|
| `cmx-postgres-oltp` | `Up … (healthy)` |
| `cmx-postgres-analytics` | `Up … (healthy)` |
| `cmx-minio` | `Up … (healthy)` |
| `cmx-minio-init` | **`Exited (0)`** |
| `cmx-adminer` | `Up …` |
| `cmx-traefik` | `Up …` |

**Si ves `(health: starting)`, espera.** Los tres `healthy` tardan entre diez y
treinta segundos. Vuelve a correr `docker compose ps -a`.

**`cmx-minio-init` apagado es lo correcto.** Su único trabajo es crear el bucket y
terminar:

- `Exited (0)` quiere decir que lo hizo.
- `Exited (1)` quiere decir que no.

Para verlo en sus propias palabras:

```bash
docker compose logs minio-init
```

La última línea tiene que decir **`Bucket canastamx-bronze listo.`**

---

## Paso 8 · Comprueba que sirven, no sólo que arrancaron

`Up` sólo prueba que el contenedor arrancó. Este paso prueba que responde y que
tus contraseñas entran.

Primero imprime **tus** direcciones. Salen de tu `.env`, así que ya traen tus
puertos:

```bash
v() { grep -E "^$1=" .env | cut -d= -f2- | tr -d '\r'; }
w=$(v TRAEFIK_WEB_PORT); [ "$w" = 80 ] && w="" || w=":$w"
echo "MinIO · consola        http://localhost:$(v S3_CONSOLE_PORT)"
echo "Adminer                http://localhost:$(v ADMINER_PORT)"
echo "Traefik · panel        http://localhost:$(v TRAEFIK_DASHBOARD_PORT)"
echo "MinIO · por nombre     http://minio.canastamx.localhost$w"
echo "Adminer · por nombre   http://db.canastamx.localhost$w"
```

Abre cada dirección en tu navegador, en este orden.

### 8.1 · El almacenamiento

Abre **MinIO · consola** y entra con:

| Campo | Valor |
|---|---|
| Username | tu `S3_ACCESS_KEY` |
| Password | tu `S3_SECRET_KEY` |

**Tiene que aparecer el bucket `canastamx-bronze`, vacío.** Que esté vacío es lo
correcto: es tu MinIO y nadie le ha subido nada. Lo que compruebas es que existe,
y **nadie lo creó a mano**: lo creó `cmx-minio-init`. Si está ahí, la cadena
completa funcionó.

> **Para A:** si ya corriste la ingesta (T020) en tu máquina, verás adentro la
> carpeta `qqp/`. Es la capa cruda real del alcance, no pruebas. Los demás no la
> van a ver, porque cada MinIO es de su máquina.

### 8.2 · Las dos bases de datos

Abre **Adminer** y entra a la primera:

| Campo | Base transaccional |
|---|---|
| Sistema | PostgreSQL |
| Servidor | `postgres-oltp` |
| Usuario | `canastamx` |
| Contraseña | tu `OLTP_PASSWORD` |
| Base de datos | `canastamx_oltp` |

Para la segunda, abre **otra pestaña** con la misma dirección de Adminer. Adminer
recuerda una sesión por servidor, así que las dos quedan abiertas a la vez:

| Campo | Base analítica |
|---|---|
| Sistema | PostgreSQL |
| Servidor | `postgres-analytics` |
| Usuario | `canastamx` |
| Contraseña | tu `ANALYTICS_PASSWORD`, la otra |
| Base de datos | `canastamx_analytics` |

> **Por qué `postgres-oltp` y no `localhost`.** Adminer corre *dentro* de la red
> de Docker. Desde ahí, `localhost` es el propio Adminer, no tu máquina. Dentro de
> la red, cada contenedor se llama por su nombre de servicio y usa el puerto
> **5432**, aunque en tu `.env` hayas cambiado `OLTP_PORT`.

**«No existen tablas» es lo correcto.** Las bases están creadas y vacías porque
todavía nadie crea tablas. Lo que compruebas es que la base existe, acepta tu
contraseña y responde.

### 8.3 · Los nombres de Traefik

Abre **MinIO · por nombre** y **Adminer · por nombre**. Tienen que mostrar lo
mismo que los dos pasos anteriores.

- **Si cambiaste `TRAEFIK_WEB_PORT`**, la dirección lleva el puerto, por ejemplo
  `http://db.canastamx.localhost:8880`. Sin el puerto no llegas a Traefik.
- **Si te lleva a otra página** (la bienvenida de XAMPP o de IIS), otro programa
  ya ocupa el 80. Ve a la tabla del Paso 5.

**Traefik · panel** es opcional. Si abre y lista los routers `adminer` y
`minio-console`, Traefik está bien.

---

## El día a día

| Situación | Qué haces |
|---|---|
| Vas a trabajar | Abre Docker Desktop (en Windows) y luego `docker compose up -d` |
| Reiniciaste la computadora | Lo mismo: los contenedores **no** arrancan solos |
| Quieres ver cómo están | `docker compose ps -a` |
| Terminaste por hoy | `docker compose down`. Apaga y **conserva** los datos |
| Hiciste `git pull` | Repite el [Paso 6](#paso-6--tres-comprobaciones-antes-de-levantar) y luego `docker compose up -d` |
| Quieres empezar de cero | `docker compose down -v` y luego `docker compose up -d` |

> **`down -v` borra los datos** de las dos bases y del bucket. Hoy están vacíos y
> no pasa nada, pero cuando tengan datos no hay vuelta atrás. En el día a día es
> `down` a secas. Se usa `-v` sólo para empezar de cero, por ejemplo después de
> cambiar una contraseña de Postgres.

---

## Problemas

| Lo que ves | Qué pasa | Qué haces |
|---|---|---|
| Docker Desktop dice que hay que actualizar WSL | Falta el componente de WSL 2 | PowerShell como administrador: `wsl --update`, y reinicia |
| *Virtualization support not detected* | La virtualización está apagada en el BIOS | Enciéndela (Intel VT-x o AMD SVM). Si no sabes cómo, pide ayuda en el grupo |
| `docker: command not found` | Ver la tabla del [Paso 3](#paso-3--comprueba-que-docker-responde) | |
| `port is already allocated`, o `Ports are not available … forbidden by its access permissions` | Otro programa, o Windows, ya tiene ese puerto | Cambia el puerto en tu `.env` (Paso 5) y `docker compose up -d` |
| `http://db.canastamx.localhost` abre XAMPP, IIS u otra cosa | El 80 está ocupado **y Docker no da error** | `TRAEFIK_WEB_PORT=8880`, `docker compose up -d`, y usa `:8880` en la dirección |
| Traefik responde *404 page not found* | Llegaste a Traefik sin un nombre que conozca | Usa las direcciones con nombre que imprime el Paso 8 |
| Adminer: *password authentication failed* | La contraseña no coincide, o la cambiaste **después** de la primera vez | Vuelve a poner la anterior, o `docker compose down -v` y `docker compose up -d` |
| Adminer: *could not translate host name* o *connection refused* | Escribiste `localhost` como servidor | Usa `postgres-oltp` o `postgres-analytics` |
| `cmx-minio` no llega a `healthy` | `S3_SECRET_KEY` con menos de 8 caracteres, o `S3_ACCESS_KEY` con menos de 3 | `docker compose logs minio` lo dice. Corrige el `.env` y `docker compose up -d`. Si sigue, `down -v` y otra vez `up -d` |
| `cmx-minio-init` en `Exited (1)` con *Bucket name cannot be empty* | Tu `.env` es viejo: trae `MINIO_*` en vez de `S3_*` | Vuelve a copiar `.env.example` y llénalo |
| `cmx-minio-init` en `Exited (1)` quejándose de credenciales | Caracteres especiales en las llaves | Sólo letras, números, `-` y `_` |
| `WARN … variable is not set` | Falta una variable nueva en tu `.env` | Comprobación 2 del Paso 6 |
| `toomanyrequests` al descargar | Docker Hub limita las descargas sin sesión por dirección IP, y en la escuela muchos comparten la misma | Espera un rato, o entra con una cuenta gratuita (`docker login`) |
| `pull access denied` o `manifest unknown` | El espejo de imágenes no responde | Ver [Si Docker Hub falla](#si-docker-hub-falla) |
| Una contraseña funciona un día y al otro no | Tienes dos clones con dos `.env` distintos | Trabaja con un solo clon (Paso 1) |

Para ver por qué se cayó algo:

```bash
docker compose logs minio          # o el servicio que falló
docker compose logs --tail 50      # lo último de todos
```

---

## Si Docker Hub falla

Las imágenes de MinIO salen de un espejo nuestro, `canastamx/minio` y
`canastamx/mc`, porque el registro original las retiró. Está contado en el
[ADR 012](../adr/012-de-donde-salen-las-imagenes.md). No hace falta cuenta para
descargarlas: son públicas.

Si el espejo tampoco responde, las dos imágenes están guardadas como archivo en
el Drive del equipo. **Pide el enlace en el grupo**; no se publica aquí porque
este repositorio es público.

```bash
docker load -i minio-RELEASE.2025-09-07T16-13-09Z-amd64.tar
docker load -i mc-RELEASE.2025-08-13T08-35-41Z-amd64.tar
docker compose up -d
```

En equipos ARM64, los archivos terminan en `-arm64.tar`. `docker load` mete la
imagen en tu Docker sin descargar nada, y el compose la encuentra solo.

Los `.tar` no van en el repositorio porque pesan más de 10 MB y la integración
continua los rechaza.

---

## Qué no levanta esto todavía

Sólo la infraestructura: las dos bases, el almacenamiento y la puerta de enlace.
Los servicios de la aplicación todavía no están en el `docker-compose.yml`: la
plataforma de datos, la interfaz analítica, el servicio de dominio y los dos
clientes. Se van agregando conforme cada frente los tenga. Si no ves «la
aplicación» por ningún lado, está bien: todavía no existe.

---

## Registro de verificación

Esta guía se verifica con una regla: **alguien que no la escribió la sigue en su
máquina, sin preguntar.** Si tiene que preguntar algo, se arregla el documento,
no se le explica a esa persona.

| Quién | Sistema y terminal | Fecha | ¿Llegó al final sin preguntar? | Qué se atoró |
|---|---|---|---|---|
| A | Windows + WSL · Ubuntu | 27-09-2026 | No | Docker no instalado; nombres del `.env` distintos a los de la guía; `minio-init` fallaba; `ps` sin `-a`; las rutas de Traefik iban a XAMPP |
| C2 (Oscar) | Windows 11 · Git Bash | 02-10-2026 | No | Docker instalado pero con el motor detenido; contraseñas vacías en `.env` y duda al abrir el archivo; los nombres de Traefik abrían XAMPP en el puerto 80. Se completaron las credenciales locales, se cambió `TRAEFIK_WEB_PORT` a `8081` y se aplicó con `docker compose up -d traefik`. Se verificaron las dos bases desde Adminer, el bucket `canastamx-bronze` en MinIO y los dos accesos por nombre con `:8081`. |

**La columna «qué se atoró» es la más útil.** Cada cosa anotada ahí es una línea
que le faltaba a la guía.
