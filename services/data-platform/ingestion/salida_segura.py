"""La salida de las líneas de comandos no truena por la codificación.

En Windows, cuando la salida de Python va a un archivo o a una tubería
(`> archivo`, `subprocess`, Dagster), se escribe con la página de códigos del
sistema —cp1252 en español—, y un `print("→")` truena con UnicodeEncodeError a la
mitad del lote. En una consola de Windows, en Linux, en WSL y en la CI no pasa,
porque ahí la salida es UTF-8. Las líneas de comandos de esta carpeta imprimen
→ ✓ ⚠ ✗ y ─ a propósito: son su forma de decir qué pasó.

Dos medidas, una a cada lado de la tubería:

1. `preparar_salida()`, al empezar cada línea de comandos: lo que la codificación
   de la salida no tiene se escribe como `\\u2192` en lugar de tronar. No cambia la
   codificación, no toca un texto que sí cabe y no esconde nada: el carácter queda
   escrito con su código.
2. `entorno_utf8()` y `CODIFICACION_DE_LOS_HIJOS`, para quien corre una de estas
   líneas de comandos como proceso hijo y lee lo que escribe (la orquestación): el
   hijo escribe UTF-8 y el padre lee UTF-8, así que no se pierde ningún carácter.
"""

import os
import sys

CODIFICACION_DE_LOS_HIJOS = "utf-8"


def preparar_salida():
    """Que stdout y stderr escriban `\\uXXXX` lo que su codificación no tiene."""
    for flujo in (sys.stdout, sys.stderr):
        reconfigurar = getattr(flujo, "reconfigure", None)
        if reconfigurar is not None:
            reconfigurar(errors="backslashreplace")


def entorno_utf8(base=None):
    """El entorno de un proceso hijo de Python que escriba su salida en UTF-8."""
    entorno = dict(os.environ if base is None else base)
    entorno["PYTHONIOENCODING"] = CODIFICACION_DE_LOS_HIJOS
    return entorno
