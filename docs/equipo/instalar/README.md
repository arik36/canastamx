# Preparar tu máquina

**De cero a poder trabajar en CanastaMX.** Una guía por sistema operativo, porque los comandos no son intercambiables y probarlo a ciegas cuesta la tarde.

## ¿Cuál me toca?

| Guía | Quién | Cómo saber si es la tuya |
|---|---|---|
| **[Windows](./windows.md)** | **C1** Liseth · **C2** Oscar · **D** Karen | Abres el símbolo del sistema y dice `C:\Users\tu-usuario>` |
| **[Linux](./linux.md)** | **B** Ari Adair | Ubuntu, Debian o similar instalado directo en la máquina |
| **[Windows con WSL](./windows-wsl.md)** | **A** Ariadne | Windows, pero trabajas dentro de una terminal de Ubuntu |

Si no sabes cuál es la tuya, es **Windows**. WSL no se instala solo.

## Lo que las tres tienen en común

Cambian los comandos, no el resultado. Al terminar, cualquiera de las tres deja:

1. **Git instalado y sabiendo quién eres** — con el correo de tu cuenta de GitHub, que es lo único que ata un commit a una persona.
2. **El repositorio clonado por HTTPS**, fuera de OneDrive y de cualquier carpeta que sincronice.
3. **Los ganchos de Git activados** — `git config core.hooksPath` responde `.githooks`.
4. **Las herramientas de tu frente** instaladas.
5. **`verificar-base.sh <tu clave>` en verde.**

## Tres reglas que valen para todos

**Clona por HTTPS, no por SSH.** La dirección es `https://github.com/arik36/canastamx.git`. Si usas la que empieza con `git@github.com:`, Git te va a pedir una llave criptográfica que no tienes y no necesitas, y va a fallar con `Permission denied (publickey)`.

**Nunca clones dentro de OneDrive, Drive o Dropbox.** Sincronizan la carpeta `.git` a medio commit y la corrompen. En Windows, «Documentos» y «Escritorio» suelen estar dentro de OneDrive sin que se note.

**Los ganchos no vienen con el clon.** Cada quien los activa a mano, una vez, con `instalar-hooks.sh`. Son cinco activaciones distintas. Git lo exige a propósito: si vinieran activados, clonar cualquier repositorio de internet ejecutaría código de un desconocido en tu computadora.

---

*Cuando termines, llena tu [ficha de entorno](../entorno/PLANTILLA.md). Es la primera tarea de la semana 1 y es lo que se consulta en noviembre, la primera vez que alguien diga «en mi máquina sí funciona».*
