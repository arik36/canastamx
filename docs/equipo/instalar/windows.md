# Preparar tu máquina · Windows

**Para C1 (Liseth), C2 (Oscar) y D (Karen).** Windows directo, sin WSL.

Unos 30 minutos, casi todos de esperas de instalación. **Hazlo antes del lunes**, no el lunes: si los cinco instalamos al mismo tiempo en la reunión, la reunión se convierte en soporte técnico.

---

## 1 · Instalar Git

Descarga de **git-scm.com/download/win**. Se baja solo el instalador que te toca.

Durante la instalación, **acepta todo lo que viene marcado salvo una cosa**: en la pantalla *«Choosing the default editor used by Git»* viene **Vim** seleccionado. Cámbialo por **Notepad**, o por **Visual Studio Code** si ya lo tienes.

> Vim es un editor de terminal en el que, si entras sin saber, ni siquiera puedes salir. Algún día Git te va a abrir el editor solo —al resolver un conflicto, por ejemplo— y ese día lo vas a agradecer.

**Comprueba.** Abre el símbolo del sistema: tecla Windows → escribe `cmd` → Enter.

```
git --version
```

Debe responder algo como `git version 2.47.0.windows.1`.

> Si dice que no reconoce el comando, **cierra esa ventana y abre una nueva**. El instalador no actualiza las terminales que ya estaban abiertas. Es el tropiezo más común de este paso.

## 2 · Decirle a Git quién eres

```
git config --global user.name "Tu Nombre Completo"
git config --global user.email "el-correo-de-tu-cuenta-de-github@ejemplo.com"
```

Verifica:

```
git config --global user.name
git config --global user.email
```

> **El correo tiene que ser el de tu cuenta de GitHub.** Es lo único que ata un commit a una persona. Si no coincide, tus commits aparecen como de un desconocido y **tu trabajo no cuenta como contribución tuya ante el asesor**. Se arregla ahora en diez segundos; en noviembre, reescribiendo el historial.

## 3 · Elegir dónde va a vivir el repositorio

**Dos lugares que NO sirven:**

- **Escritorio, Documentos o Imágenes.** En casi todas las computadoras están sincronizadas con OneDrive, y OneDrive sube archivos a medio escribir. Corrompe el repositorio, y el daño no se nota hasta que ya no se puede deshacer.
- **Cualquier carpeta dentro de OneDrive, Drive o Dropbox**, aunque no lleve ese nombre.

**Usa una de estas:**

```
C:\Users\TU_USUARIO\projects
```

o, si tienes disco `D:`

```
D:\projects
```

Créala:

```
cd C:\Users\%USERNAME%
mkdir projects
cd projects
```

## 4 · Clonar el repositorio

**Con la dirección HTTPS. No la de SSH.**

```
git clone https://github.com/arik36/canastamx.git
cd canastamx
```

Se te abre el navegador pidiéndote iniciar sesión en GitHub. Eso lo hace el *Git Credential Manager*, que vino con Git: guarda la credencial y ya no te vuelve a preguntar.

> **Fíjate con qué cuenta entras.** Tiene que ser la tuya, la que aceptó la invitación de colaborador. Si tu navegador está con otra cuenta, te va a decir que el repositorio **no existe** — no es un error tuyo: el repositorio es privado y esa otra cuenta no lo puede ver. Sal de sesión y entra con la correcta.

Comprueba:

```
dir
```

Tienes que ver `docs`, `infra`, `services`, `clients`, `README.md`, `docker-compose.yml`.

### Si ves `Permission denied (publickey)`

Usaste la dirección de SSH (`git@github.com:...`). SSH necesita una llave criptográfica que no tienes y que no te hace falta.

```
cd ..
rmdir /s /q canastamx
```

Y vuelve a clonar con la dirección `https://` de arriba.

## 5 · Cambiar a Git Bash

**A partir de aquí, cierra el símbolo del sistema y abre Git Bash.** Los guiones del proyecto están escritos en bash, y el símbolo del sistema de Windows no los entiende.

Git Bash ya se instaló junto con Git. Ábrelo así:

- Tecla Windows → escribe `Git Bash` → Enter, **o**
- Entra a la carpeta `canastamx` en el explorador, clic derecho en un espacio vacío → **Open Git Bash here**
  *(en Windows 11 puede estar dentro de «Mostrar más opciones»)*

**Las rutas se escriben distinto ahí.** Es la misma carpeta:

| Símbolo del sistema | Git Bash |
|---|---|
| `C:\Users\liseth\projects\canastamx` | `/c/Users/liseth/projects/canastamx` |
| `D:\projects\canastamx` | `/d/projects/canastamx` |

Ubícate y comprueba:

```bash
cd /c/Users/TU_USUARIO/projects/canastamx
pwd
git status
```

`git status` debe decir `On branch main` y `nothing to commit, working tree clean`.

## 6 · Instalar los ganchos

```bash
bash infra/scripts/instalar-hooks.sh
git config core.hooksPath
```

El segundo comando debe responder `.githooks`.

> **Por qué esto no viene con el clon.** Los ganchos son programas que Git ejecuta en tu máquina antes de cada commit. Si vinieran activados de fábrica, clonar cualquier repositorio de internet ejecutaría código de un desconocido en tu computadora. Por eso Git obliga a activarlos a mano. **Son cinco activaciones distintas, una por persona**: si te lo saltas, no tienes ninguna de estas protecciones y nadie se entera hasta que rompes algo.

Lo que te van a evitar: subir un `.env` con contraseñas, subir carpetas de dependencias (`node_modules`, `target`), y subir archivos de más de 10 MB. Los tres son errores **que no se arreglan borrando el archivo después**: una vez que algo entra al historial de Git, ahí se queda aunque lo borres en el commit siguiente.

## 7 · Las herramientas de tu frente

Solo las tuyas. Lo más rápido en Windows 10 y 11 es **winget**, que ya viene instalado — pruébalo con `winget --version` en el símbolo del sistema.

### C1 · Liseth · servicio de dominio

```
winget install EclipseAdoptium.Temurin.21.JDK
winget install Apache.Maven
```

**Cierra y vuelve a abrir la terminal**, y comprueba:

```
java -version
mvn -v
```

`java -version` tiene que decir **21**. Si dice 17, 23 o cualquier otro, el proyecto no va a compilar igual que en las demás máquinas.

Sin winget: **adoptium.net** para el JDK 21, y **maven.apache.org/download.cgi** para Maven (hay que agregarlo al `PATH` a mano).

### C2 · Oscar · cliente móvil

```
winget install OpenJS.NodeJS.LTS
```

O el instalador de **nodejs.org**, versión **LTS**. Después:

```
node --version
npm --version
npx --version
```

### D · Karen · cliente web

```
winget install OpenJS.NodeJS.LTS
```

Y una cuenta en **figma.com**, que se usa desde el navegador — no hay nada que instalar para eso.

## 8 · La verificación final

De vuelta en **Git Bash**, dentro de la carpeta del proyecto, **con tu clave**:

```bash
bash infra/scripts/verificar-base.sh C1
```

Las claves: **C1** Liseth · **C2** Oscar · **D** Karen.

Revisa siete cosas: que estés en un clon de verdad, que tu `main` esté al día, la etiqueta de línea base, los archivos que no pueden faltar, la higiene de tu carpeta, tu identidad en Git y las herramientas de tu frente.

| Si dice | Qué haces |
|---|---|
| **PUEDES CREAR TU RAMA** | Listo. Ya puedes trabajar |
| Falta algo **del repositorio** | **No lo subas por tu cuenta.** Avisa en el chat; lo arregla su dueño |
| Falta algo **de tu máquina** | Instálalo. Ese sí es tuyo |

**Cuando termines, pega en el chat la parte final de la salida.** Si algo salió en rojo, manda la pantalla completa **antes de tocar nada**: es más rápido resolverlo entre todos que a solas.

---

## Lo que NO necesitas instalar

| | Por qué |
|---|---|
| **GitHub CLI (`gh`)** | Solo lo usa A, para los guiones del tablero |
| **WSL ni Ubuntu** | A trabaja así porque ya lo tenía. Con Git Bash tienes todo lo que hace falta |
| **Llaves SSH** | Con HTTPS y el inicio de sesión del navegador es suficiente |
| **Docker** | Es del frente de B. Tú lo necesitarías hasta que el sistema completo se levante, y para eso avisamos |

## Errores frecuentes de Windows

| Qué ves | Qué pasó | Salida |
|---|---|---|
| `'git' no se reconoce como un comando` | La terminal es anterior a la instalación | Ciérrala y abre una nueva |
| `Permission denied (publickey)` | Clonaste por SSH | Borra la carpeta y clona por `https://` |
| `Repository not found` | El navegador está con otra cuenta de GitHub | Sal de sesión y entra con la tuya |
| `bash: infra/scripts/...: No such file` | No estás dentro de la carpeta del proyecto | `pwd` y `cd` a la ruta correcta |
| El guión no hace nada en CMD | Los guiones son de bash | Usa **Git Bash**, no el símbolo del sistema |
| `java -version` dice otra versión | Tienes varios JDK instalados | Desinstala los otros, o ajusta `JAVA_HOME` |
