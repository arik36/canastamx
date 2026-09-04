# Fusión del paquete con el repositorio que ya existe

**Pregunta:** ¿borro el repositorio y subo el paquete, o solo cambio algunas cosas?

**Respuesta corta: no borres nada.** Se agregan 28 archivos, se fusionan 3, y no se pierde ninguno.

---

## Qué encontró la comparación

Comparé el paquete contra lo que produce tu `bootstrap.sh`, ejecutándolo en un directorio limpio.

| | Cuántos | Qué hacer |
|---|---|---|
| **Archivos que el paquete agrega** | 28 | Se copian tal cual. No pisan nada |
| **Archivos en los dos, con contenido distinto** | 3 | `README.md`, `.env.example`, `.gitignore`. Se fusionan, no se reemplazan a ciegas |
| **Archivos solo tuyos** | 1 | `.gitattributes`. **Se queda como está.** El paquete no lo trae |
| **Archivos que perderías** | 0 | — |
| **Carpetas nuevas** | 6 | `docs/equipo/` y sus dos subcarpetas, `.github/ISSUE_TEMPLATE/`, `infra/envs/dev` y `infra/envs/test` |

Tu bootstrap creó **19 carpetas**; el paquete usa **26**. Las 19 tuyas se conservan idénticas.

---

## Los tres archivos en conflicto

### 1 · `.env.example` — **aquí estaba el problema real**

Tu bootstrap definió las variables así, y mi `docker-compose.yml` esperaba otras. **Solo 2 de 8 coincidían.**

| Lo que tu `.env.example` define | Lo que mi compose esperaba |
|---|---|
| `OLTP_USER`, `OLTP_PASSWORD`, `OLTP_DB`, `OLTP_PORT` | `POSTGRES_OLTP_USER`, `POSTGRES_OLTP_PASSWORD`, `POSTGRES_OLTP_DB` |
| `ANALYTICS_USER`, `ANALYTICS_PASSWORD`, `ANALYTICS_DB`, `ANALYTICS_PORT` | `POSTGRES_ANALYTICS_USER`, `POSTGRES_ANALYTICS_PASSWORD`, `POSTGRES_ANALYTICS_DB` |
| `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD` ✓ | `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD` ✓ |

Si hubieran quedado los dos como estaban, `docker compose up` habría levantado Postgres **con usuario y contraseña vacíos**, sin error visible hasta que alguien intentara conectarse.

**Ganan tus nombres**, por tres razones: son más cortos, parametrizan los puertos —cosa que los míos no hacían— y solo dejan vacíos los secretos, con los nombres y puertos ya llenos. Eso último es mejor práctica: quien copia el archivo tiene menos decisiones que tomar.

**El `docker-compose.yml` del paquete ya está reescrito con tus nombres.** El `.env.example` del paquete es el tuyo más cinco líneas:

```diff
+ MINIO_PORT=9000
+ MINIO_CONSOLE_PORT=9001
+ ADMINER_PORT=8080          # el 8080 choca seguido, conviene poder moverlo
+ PROFECO_QQP_URL=           # lo llena A en la semana 2
```

Todo lo demás queda literal como lo escribiste, incluido `INEGI_API_TOKEN`, que yo no tenía.

### 2 · `README.md`

El tuyo está bien estructurado y ya vive en el repositorio, así que se conservó su forma: la tabla de arquitectura con columna de ruta —mejor que la mía—, la sección de cómo levantarlo con su nota de verificación, y las convenciones.

Se cambiaron tres cosas:

- **La tabla del equipo.** Decía «(por definir)» en B, C y D. Ahora tiene los cinco nombres, con C partido en C1 y C2, y las iniciales de rama de cada quien.
- **Los enlaces al manual**, que antes no existía.
- **Una sección nueva:** «Antes de crear tu primera rama», con el comando de verificación.

Una nota sobre acentos: tu bootstrap escribió el README sin ellos, probablemente por seguridad con la codificación dentro del heredoc de bash. En un archivo `.md` que se sube directo no hace falta: GitHub lo lee como UTF-8 sin problema, y el resto del paquete usa acentos. Si prefieres mantenerlo sin acentos, es cosmético y no rompe nada.

### 3 · `.gitignore`

**Este no lo pude comparar**, porque tu bootstrap lo toma de un archivo que colocaste aparte y no lo tengo. Córrelo tú:

```bash
cd ~/projects/canastamx
bash ~/paquete-canastamx/entrega/infra/scripts/comparar-paquete.sh ~/paquete-canastamx/entrega
```

El del paquete tiene 62 líneas y cubre Python, dbt, Java, Node, Expo, Docker, datos y editores, con una excepción explícita para que sí suban los archivos de prueba:

```gitignore
*.csv
!services/data-platform/tests/fixtures/*.csv
!docs/experimento/bitacora.csv
```

Si el tuyo ya cubre `node_modules/`, `.venv/`, `target/`, `__pycache__/` y `.env`, quédate con el tuyo y agrégale solo las líneas de datos. Si no los cubre, usa el del paquete.

---

## Lo que NO se toca

- **`.gitattributes`** — es tuyo y el paquete no lo trae. Con un equipo repartido entre Windows con WSL, Mac y Linux, es lo que evita que medio repositorio cambie de finales de línea en un commit y todo aparezca como modificado. Fue buena decisión ponerlo desde el bootstrap.
- **`git config core.autocrlf false`** — igual. Que cada quien lo corra en su máquina.
- **Las 19 carpetas y sus `.gitkeep`** — quedan idénticas.
- **El historial.** Nada de lo que sigue reescribe commits.

---

## Dónde poner el paquete

**Fuera del repositorio.** Si lo descomprimes adentro, el `git add .` del final se lo lleva al commit.

El paquete es solo una carpeta de la que se copia; puede vivir donde sea. Lo cómodo es dejarlo al lado del repositorio, no adentro:

```
/home/mlizz/
├─ projects/
│  └─ canastamx/          ← tu repositorio
└─ paquete-canastamx/     ← aquí descomprimes el zip
   └─ entrega/            ← esta es la carpeta que le pasas al script
```

### Si trabajas en WSL, que es lo normal en este equipo

El zip se descarga del lado de Windows, y el repositorio vive del lado de Linux. Hay que cruzarlo. Desde la terminal de WSL:

```bash
# 1. Averigua tu usuario de Windows
ls /mnt/c/Users/

# 2. Trae el zip desde Descargas de Windows
mkdir -p ~/paquete-canastamx
cp /mnt/c/Users/TU_USUARIO_WINDOWS/Downloads/CanastaMX_paquete_equipo.zip ~/paquete-canastamx/

# 3. Descomprime
cd ~/paquete-canastamx
unzip CanastaMX_paquete_equipo.zip      # si falta: sudo apt install unzip
ls entrega/                             # debe listar docs, infra, README.md...
```

Si `unzip` no está y no quieres instalarlo:

```bash
python3 -m zipfile -e CanastaMX_paquete_equipo.zip .
```

> **Por qué no dejar el repositorio en `/mnt/c/`.** Git sobre el sistema de archivos de Windows visto desde WSL es varias veces más lento, y los permisos se comportan raro. Tenerlo en `/home/mlizz/projects/` es lo correcto. El zip sí puede venir de `/mnt/c/`, porque solo se lee una vez.

---

## Dos trampas que ya nos pasaron

### 1 · Pararse en el repositorio equivocado

`comparar-paquete.sh` mira el directorio en el que estás. Si te paras en otro repositorio tuyo, compara contra ese, y el `cp -r` del paso siguiente le vuelca 53 archivos de CanastaMX encima.

Se detecta por la sección 3 del reporte: si «SOLO TUYOS» lista archivos que no reconoces del proyecto —notas, apuntes, prácticas— estás en el repositorio equivocado.

El script ya lo comprueba solo: si ni la carpeta ni el remoto mencionan `canastamx`, se detiene con un aviso en rojo y no continúa. Para saltárselo a propósito hay que repetirlo con `--forzar`.

**Verifica siempre antes de copiar:**

```bash
pwd                        # debe terminar en /canastamx
git remote get-url origin  # debe decir arik36/canastamx
```

### 2 · Los archivos `:Zone.Identifier`

Windows le pega una marca invisible a todo lo que se descarga de internet, para saber que viene de fuera. Si descomprimes el zip **del lado de Windows** y luego copias la carpeta a WSL, esa marca aparece como un archivo suelto por cada archivo del paquete: `cronograma.md:Zone.Identifier`, `ci.yml:Zone.Identifier`, y así.

No rompen nada, pero si copias el paquete tal cual se van al commit y ensucian el repositorio.

**Se borran en un comando:**

```bash
find ~/paquete-canastamx/entrega -name '*:Zone.Identifier' -delete
```

**O se evitan de raíz** descomprimiendo dentro de WSL en vez de en Windows: copia el `.zip` a WSL primero y corre `unzip` ahí. Es lo que hace la sección anterior.

El script los omite del reporte y avisa cuántos encontró. Y el `.gitignore` del paquete ya los ignora, por si alguno se cuela.

---

## Cómo se hace

Hay dos caminos. El primero es el recomendado.

### Camino A · con el guión de fusión

Hace lo mismo que el manual, pero sin que se te pase ningún paso: respalda todo archivo que vaya a ser pisado **antes** de tocarlo, une los dos `.gitignore` en vez de reemplazar el tuyo, omite la basura de Windows y te deja la lista de qué revisar. **No hace commit.**

```bash
cd ~/projects/canastamx
git switch main && git pull
git switch -c chore/alm-linea-base

bash ~/paquete-canastamx/entrega/infra/scripts/fusionar-paquete.sh ~/paquete-canastamx/entrega
```

Se niega a correr si estás en `main`, si el repositorio no es CanastaMX, o si tienes cambios sin confirmar que ensuciarían el `git diff` de después.

Al terminar imprime, con las rutas ya escritas, los `diff` que tienes que mirar. Tu versión original de cada archivo pisado queda completa en `../respaldo-canastamx-<fecha>/`, fuera del repositorio.

### Camino B · a mano

```bash
cd ~/projects/canastamx
git switch main && git pull
git switch -c chore/alm-linea-base

# 1. Respalda lo que va a ser pisado
mkdir -p ../respaldo-canastamx
cp README.md .env.example .gitignore ../respaldo-canastamx/

# 2. Míralos ANTES de copiar
diff -u .gitignore   ~/paquete-canastamx/entrega/.gitignore   | less
diff -u README.md    ~/paquete-canastamx/entrega/README.md    | less
diff -u .env.example ~/paquete-canastamx/entrega/.env.example | less

# 3. Copia. El "/." del final incluye los archivos ocultos.
cp -r ~/paquete-canastamx/entrega/. .
rm -f INSTALAR.md          # es para ti, no para el repositorio

# 4. Completa las carpetas que faltaban
bash infra/scripts/crear-estructura.sh

# 5. Revisa y sube
git status
git diff
git add .
git commit -m "chore(repo): línea base — manual, fichas y plantillas"
git push -u origin chore/alm-linea-base
```

---

## Qué hacer con cada uno de los tres

### `.env.example` — quédate con el del paquete

El del paquete es **el tuyo más cuatro líneas**. Ninguna de tus variables desaparece, incluido `INEGI_API_TOKEN`. Reemplazar es seguro.

### `.gitignore` — únelos, no elijas

Un `.gitignore` es aditivo: la unión de los dos casi siempre es la respuesta correcta. Tus reglas quedan arriba y las del paquete se agregan debajo, sin duplicar. El guión de fusión lo hace solo; a mano:

```bash
{ cat ../respaldo-canastamx/.gitignore
  echo
  echo "# --- agregado desde el paquete del equipo ---"
  grep -vE '^\s*(#|$)' ~/paquete-canastamx/entrega/.gitignore \
    | while read -r r; do grep -qxF "$r" ../respaldo-canastamx/.gitignore || echo "$r"; done
} > .gitignore
```

### `README.md` — este sí míralo

Es el único que editaste después del bootstrap, así que el diff importa. Si tu cambio no está en la versión del paquete, recupéralo del respaldo y vuelve a ponerlo antes de confirmar.

---

## Después de incorporar: marca la línea base

Cuando la solicitud esté en `main`, es el momento de la etiqueta que espera `verificar-base.sh`:

```bash
git switch main && git pull
git tag -a base-v0 -m "Línea base: estructura, gitignore, manual y plantillas"
git push origin base-v0
```

Sin esa etiqueta, el guión de verificación le dice a todos «todavía no ramifiques». Con ella, los cinco pueden arrancar.

---

## Por qué no borrar el repositorio

Aunque hoy tenga poco adentro, borrarlo cuesta más de lo que parece:

- Se pierde el historial, que es evidencia de trabajo ante el asesor. Un repositorio con commits desde agosto se ve distinto a uno creado el 3 de septiembre.
- Se pierden las invitaciones de colaborador ya aceptadas y hay que rehacerlas.
- Se pierde la configuración de la rama protegida, si ya la pusiste.
- La URL `github.com/arik36/canastamx` queda libre unos minutos y hay que recrearla con el mismo nombre exacto, o todos los enlaces del panel y del manual se rompen.

Y a cambio no se gana nada: la fusión son dos comandos y tres `git diff`.

---

## Una última cosa: el bootstrap ya cumplió

`bootstrap.sh` hizo su trabajo y no hay que volver a correrlo. De aquí en adelante, la estructura la mantiene `infra/scripts/crear-estructura.sh`, que es idempotente —se puede correr las veces que sea sin romper nada— y que además crea las seis carpetas que al bootstrap le faltaban.

Si quieres conservar el `bootstrap.sh` como registro de cómo nació el repositorio, guárdalo en `infra/scripts/` con un comentario arriba que diga que ya se ejecutó y no debe volver a correrse. Es historia del proyecto y al asesor le sirve verla.
