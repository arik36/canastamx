# Preparar tu máquina · Windows con WSL

**Para A (Ariadne).** Windows por fuera, Ubuntu por dentro.

WSL es un Linux completo corriendo dentro de Windows. Todo lo de esta guía se teclea **en la terminal de Ubuntu**, no en el símbolo del sistema.

> **Si no tienes WSL, no lo instales para este proyecto.** La guía de [Windows](./windows.md) alcanza de sobra. Esta existe porque A ya trabajaba así.

---

## 1 · Git

```bash
sudo apt update && sudo apt install -y git
git --version

git config --global user.name "Tu Nombre Completo"
git config --global user.email "el-correo-de-tu-cuenta-de-github@ejemplo.com"
git config --global --list | grep user
```

## 2 · GitHub CLI

```bash
sudo apt install -y gh
gh auth login
```

**GitHub.com** → **HTTPS** → **Login with a web browser**.

> **Si el navegador no se abre solo** y ves `exec: "xdg-open,x-www-browser,wslview": executable file not found`, es que a WSL le falta el puente hacia Windows:
>
> ```bash
> sudo apt install -y wslu
> ```
>
> Mientras tanto, puedes copiar la dirección que imprime y pegarla a mano en el navegador. Funciona igual.

## 3 · Dónde clonar · el punto que importa en WSL

**Nunca en `/mnt/c/...`.** Eso es el disco de Windows visto desde Linux, y ahí Git corre entre **cinco y veinte veces más lento**, porque cada operación cruza la frontera entre los dos sistemas. Además se llena de archivos `:Zone.Identifier`, que son metadatos que Windows le pega a todo lo que se descarga de internet.

**Clona en el disco de Linux**, que es `~`:

```bash
mkdir -p ~/projects && cd ~/projects
git clone https://github.com/arik36/canastamx.git
cd canastamx
pwd        # /home/tu-usuario/projects/canastamx  ← correcto
```

Si algún día te aparecen archivos `:Zone.Identifier` —pasa cuando descomprimes un zip desde el lado de Windows— se limpian así:

```bash
find . -name '*:Zone.Identifier' -delete
```

Git ya los ignora, pero ensucian los listados.

## 4 · Los ganchos

```bash
bash infra/scripts/instalar-hooks.sh
git config core.hooksPath        # debe responder .githooks
```

## 5 · Python · lo tuyo

Tu frente es datos, y el perfilado de la semana 1 se hace con pandas.

**Ubuntu 24.04 no deja instalar bibliotecas de Python sobre el sistema.** Si intentas `pip install pandas`, te rechaza con:

```
error: externally-managed-environment
```

No está roto. Ubuntu protege su Python para que no lo destruyas instalándole cosas encima —el sistema operativo mismo depende de él—. La salida correcta es un **entorno virtual**: una carpeta con su propio Python y sus propias bibliotecas, aislada del sistema. Uno por proyecto, y así el tuyo no puede romper nada más.

```bash
cd ~/projects/canastamx
sudo apt install -y python3-venv
python3 -m venv .venv
source .venv/bin/activate
pip install pandas openpyxl pyarrow jupyter
python -c "import pandas; print('pandas', pandas.__version__)"
```

Después del `activate` verás **`(.venv)`** al inicio del renglón. Eso significa que estás dentro. Para salir, `deactivate`.

> **Hay que activarlo cada vez que abras una terminal nueva.** Es el tropiezo más común: abres la terminal al día siguiente, corres tu cuaderno, y `import pandas` falla. No se desinstaló — se te olvidó el `source .venv/bin/activate`.

Comprueba que no se va a colar al repositorio:

```bash
git check-ignore -v .venv     # debe citar la línea del .gitignore
git status --short            # no debe aparecer nada
```

Si `.venv/` apareciera en `git status`, **no hagas commit**: avísalo antes.

### Nota sobre `pip` y `pip3`

En algunas máquinas existe `pip` y no `pip3`; en otras, al revés. Son el mismo programa. **No instales nada para "arreglarlo"**: anota en tu ficha de entorno cuál te funciona, para que quien siga tus pasos no crea que le falta algo.

## 6 · La verificación final

```bash
bash infra/scripts/verificar-base.sh A
```

Revisa Python, pandas, Docker —que puede quedar pendiente hasta la semana 7—, tu identidad en Git, la línea base y la higiene de tu carpeta.

---

## Errores frecuentes de WSL

| Qué ves | Qué pasó | Salida |
|---|---|---|
| Git lentísimo | Clonaste en `/mnt/c/...` | Vuelve a clonar en `~/projects` |
| Archivos `:Zone.Identifier` por todos lados | Descomprimiste un zip del lado de Windows | `find . -name '*:Zone.Identifier' -delete` |
| `xdg-open ... not found` al hacer `gh auth login` | Falta el puente a Windows | `sudo apt install wslu` |
| `error: externally-managed-environment` | Ubuntu protege su Python | Entorno virtual, paso 5 |
| `ModuleNotFoundError: pandas` en una terminal nueva | Se te olvidó activar el entorno | `source .venv/bin/activate` |
| Te pide la frase de paso en cada `push` | Usas SSH | Normal. Con `ssh-agent` se pide una vez por sesión |
