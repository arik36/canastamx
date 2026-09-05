# Entorno de trabajo · A · Ariadne Lizett Macías Campos

## Máquina

- **Sistema operativo:** Windows + WSL2 · Ubuntu 24.04.3 LTS
- **Terminal que uso:** Windows Terminal, perfil Ubuntu
- **Dónde vive el repositorio:** `/home/mlizz/projects/canastamx`

## Herramientas

| Herramienta | Versión | Cómo la comprobé |
|---|---|---|
| git | 2.43.0 | `git --version` |
| gh | 2.45.0 | `gh --version` |
| Python | 3.12.3 | `python3 --version` |
| pip | **pendiente** | `pip3 --version` → *command not found*. **Lo necesito esta misma semana** para el perfilado (T003–T005): pandas no se puede instalar sin él. Se resuelve con `sudo apt install python3-pip` |
| Docker | **pendiente** | `docker --version` → *command not found*. Lo necesito en la semana 7, cuando la ingesta escriba en MinIO |

## Notas

- Trabajo en **WSL2, no en Linux nativo**. Si reproduces un problema mío, considera que mi Git corre sobre el sistema de archivos de Linux (`/home/mlizz`), no sobre el de Windows.
- El repositorio **nunca** va en `/mnt/c`: ahí Git va mucho más lento y se ensucia con archivos `:Zone.Identifier`.
- Mi sesión de `gh` usa **SSH** con frase de paso, por eso me la pide en cada `push`. El equipo usa HTTPS, que no la pide.
