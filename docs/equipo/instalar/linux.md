# Preparar tu máquina · Linux

**Para B (Ari Adair), infraestructura.** Linux instalado directo en la máquina.

Los comandos son para **Ubuntu y Debian**. En Fedora cambia `apt` por `dnf`; en Arch, por `pacman`.

---

## 1 · Git

```bash
sudo apt update && sudo apt install -y git
git --version

git config --global user.name "Ari Adair Soto Garnica"
git config --global user.email "el-correo-de-tu-cuenta-de-github@ejemplo.com"
git config --global --list | grep user
```

> **El correo tiene que ser el de tu cuenta de GitHub.** Es lo único que ata un commit a una persona: si no coincide, tus commits aparecen como de un desconocido y no cuentan como contribución tuya ante el asesor.

## 2 · GitHub CLI, para no pelear con las credenciales

En Linux no existe el *Credential Manager* que Windows trae con Git, así que Git te pediría usuario y contraseña en **cada** `push`. La salida limpia es `gh`, que además vas a querer para otras cosas de tu frente:

```bash
sudo apt install -y gh
gh auth login
```

Responde: **GitHub.com** → **HTTPS** → **Login with a web browser**. Copia el código de un solo uso, pégalo en el navegador y listo. `gh` queda configurado como ayudante de credenciales de Git y no te vuelve a preguntar.

> Si `apt` no encuentra `gh`, agrega su repositorio siguiendo **cli.github.com** — o sáltate este paso y usa SSH, ver abajo.

> **Si prefieres SSH**, adelante: eres el de infraestructura. Solo usa `ssh-agent` para no teclear la frase de paso en cada `push`, que es exactamente la molestia que A tiene hoy y que estamos evitándole al resto del equipo.

## 3 · Clonar

```bash
mkdir -p ~/projects && cd ~/projects
git clone https://github.com/arik36/canastamx.git
cd canastamx
git status
```

Fuera de carpetas sincronizadas con la nube: sincronizan `.git` a medio commit y la corrompen.

## 4 · Instalar los ganchos

```bash
bash infra/scripts/instalar-hooks.sh
git config core.hooksPath        # debe responder .githooks
```

> **Por qué no vienen con el clon.** Los ganchos son ejecutables que Git corre en tu máquina antes de cada commit. Si vinieran activados de fábrica, clonar cualquier repositorio de internet ejecutaría código ajeno en tu computadora. Por eso Git obliga a activarlos a mano — **son cinco activaciones distintas, una por persona.**

Te van a frenar antes de subir un `.env`, una carpeta de dependencias o un archivo de más de 10 MB. Los tres son errores **que no se arreglan borrando el archivo después**: lo que entra al historial de Git ahí se queda.

## 5 · Docker · lo tuyo

**No instales `docker.io` de los repositorios de Ubuntu.** Viene sin el complemento `compose`, y el verificador te va a marcar rojo en `docker compose version`. Usa el repositorio oficial:

```bash
# 1 · llave y repositorio oficiales
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
| sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 2 · instalar
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 3 · poder usarlo sin sudo
sudo usermod -aG docker $USER
newgrp docker
```

**El paso 3 importa más de lo que parece.** Sin él, cada comando de Docker necesita `sudo`, y `docker compose up` con `sudo` crea archivos que después tu propio usuario no puede borrar. El `newgrp docker` aplica el cambio en esta terminal; para que valga en todas, cierra sesión y vuelve a entrar.

Comprueba, en este orden:

```bash
docker --version
docker compose version
docker run --rm hello-world
```

El tercero es la prueba de verdad: descarga una imagen y la ejecuta. Si sale «Hello from Docker!», el motor funciona.

## 6 · Python, si vas a tocar la plataforma de datos

No es tuyo esta semana, pero eres el suplente de A y en la semana 8 montas el entorno de pruebas. Cuando llegue el momento:

```bash
sudo apt install -y python3-venv
```

> **Ubuntu 24.04 no deja instalar bibliotecas de Python sobre el sistema.** Si intentas `pip install pandas` te va a rechazar con `error: externally-managed-environment`. No está roto: Ubuntu protege su Python para que no lo destruyas. La salida correcta es un **entorno virtual** — una carpeta con su propio Python aislado, uno por proyecto:
>
> ```bash
> python3 -m venv .venv
> source .venv/bin/activate      # verás (.venv) al inicio del renglón
> pip install pandas
> deactivate                     # para salir
> ```
>
> Hay que activarlo **cada vez que abras una terminal nueva**. `.venv/` ya está en el `.gitignore`, así que nunca se sube.

## 7 · La verificación final

```bash
bash infra/scripts/verificar-base.sh B
```

Revisa Docker, el complemento `compose`, `gh`, tu identidad en Git, la línea base del repositorio y la higiene de tu carpeta.

| Si dice | Qué haces |
|---|---|
| **PUEDES CREAR TU RAMA** | Listo |
| Falta algo **del repositorio** | Avisa en el chat; lo arregla su dueño |
| Falta algo **de tu máquina** | Instálalo. Ese sí es tuyo |

**Pega la parte final de la salida en el chat.** Y si algo sale en rojo, la pantalla completa antes de tocar nada.

---

## Errores frecuentes de Linux

| Qué ves | Qué pasó | Salida |
|---|---|---|
| `permission denied while trying to connect to the Docker daemon` | Falta el paso 3 de Docker | `sudo usermod -aG docker $USER` y vuelve a entrar a la sesión |
| `docker: command not found` tras instalar | La terminal es anterior a la instalación | Ábrela de nuevo |
| `docker compose: 'compose' is not a docker command` | Instalaste `docker.io` en vez del repositorio oficial | Desinstálalo y sigue el paso 5 |
| Git pide usuario y contraseña en cada `push` | No corriste `gh auth login` | Paso 2 |
| `error: externally-managed-environment` | Ubuntu protege su Python | Entorno virtual, paso 6 |
| `Permission denied (publickey)` | Clonaste por SSH sin llave | Clona por `https://`, o configura la llave |
