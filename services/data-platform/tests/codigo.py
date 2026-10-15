"""Un ayudante de las pruebas: el CÓDIGO de un archivo, sin comentarios ni textos.

Varias pruebas comprueban que ninguna cifra del contrato esté escrita en el
código. Buscar el número en el archivo entero no sirve: un comentario que dice
«hoy son 38» es documentación, no una regla, y el contrato mismo está lleno de
cifras explicadas en prosa. Lo que importa es si el número está en una posición
donde el programa lo obedece.

Se usa `tokenize` en lugar de una expresión regular porque es el analizador del
propio Python: distingue un `#` dentro de un texto de uno que abre comentario, y
no hay forma de que una regla se le escape por un salto de línea.

Los textos también se quitan, y eso sí deja un hueco: una cifra dentro de una
cadena no se vería. Vale la pena de todas formas, porque la alternativa —dejar
los textos— marca como falla cada mensaje de error que mencione un número.
"""

import io
import tokenize
from pathlib import Path


def codigo_sin_comentarios(ruta):
    """El archivo, con los comentarios y los textos sustituidos por un espacio."""
    fuente = Path(ruta).read_text(encoding="utf-8")
    piezas = []
    for tok in tokenize.generate_tokens(io.StringIO(fuente).readline):
        if tok.type in (tokenize.COMMENT, tokenize.STRING):
            piezas.append(" ")
        elif tok.type in (tokenize.NL, tokenize.NEWLINE):
            piezas.append("\n")
        else:
            piezas.append(tok.string)
            piezas.append(" ")
    return "".join(piezas)
