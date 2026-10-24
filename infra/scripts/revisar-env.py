"""revisar-env.py — CanastaMX

Revisa que un .env lo lean igual Docker Compose y Spring Boot.

El .env de la raíz lo leen los dos: Compose, para levantar las bases, y el servicio
de dominio, que lo importa como .properties (application.properties). No lo
interpretan igual. Compose quita las comillas, acepta «export» y corta un
comentario al final de la línea; Spring conserva las comillas, toma «export X»
como otra clave, deja el comentario dentro del valor y trata «\\» como escape. Un
valor que uno de los dos lea distinto acaba en una contraseña o una clave distinta
en cada lado, sin avisar.

Nunca imprime valores: sólo nombres de variable y números de línea.

Uso, desde la raíz del repositorio:
    python3 infra/scripts/revisar-env.py                 # el .env de la raíz
    python3 infra/scripts/revisar-env.py otro/.env ...   # los archivos que se den
    python3 infra/scripts/revisar-env.py --entorno       # además: qué variables de
                                                         # la terminal le ganan al .env

Sale con 1 si encontró algo.
"""

import base64
import binascii
import os
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
NOMBRE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
BYTES_DE_JWT_SECRET = 32   # ADR 020


def revisar(texto):
    """Los problemas del texto de un .env, sin valores, y las variables que define."""
    problemas = []
    variables = {}
    donde = {}
    for numero, linea in enumerate(texto.splitlines(), start=1):
        if numero == 1 and linea.startswith("﻿"):
            problemas.append("línea 1: empieza con BOM; guárdalo como UTF-8 sin BOM")
            linea = linea[1:]
        limpia = linea.strip()
        if not limpia or limpia.startswith("#"):
            continue
        if limpia.startswith(("export ", "export\t")):
            problemas.append(f"línea {numero}: «export»: Spring lo lee como otra clave")
            continue
        if "=" not in linea:
            problemas.append(f"línea {numero}: no tiene la forma CLAVE=valor")
            continue

        clave, valor = linea.split("=", 1)
        if not NOMBRE.fullmatch(clave):
            # No se muestra lo que hay antes del «=»: podría ser un valor mal puesto.
            problemas.append(f"línea {numero}: antes del «=» no hay un nombre de "
                             "variable válido, o hay espacios alrededor del «=»")
            continue
        if clave in donde:
            problemas.append(f"línea {numero}: {clave} ya estaba en la línea {donde[clave]}")
        donde[clave] = numero
        variables[clave] = valor
        problemas += [f"línea {numero}: {clave}: {p}" for p in _problemas_del_valor(clave, valor)]
    return problemas, variables


def _problemas_del_valor(clave, valor):
    if valor != valor.strip():
        yield "espacios al principio o al final del valor"
    if valor[:1] in ("'", '"'):
        yield "comillas: Compose las quita y Spring las conserva"
    if re.search(r"\s#", valor):
        yield "comentario al final de la línea: Spring lo deja dentro del valor"
    if "\\" in valor:
        yield "barra invertida: Spring la toma como escape"
    if "$" in valor:
        yield "«$»: Compose y Spring lo leen como una variable, y no igual"
    if not valor.isascii():
        yield "caracteres que no son ASCII: Spring lee el archivo como ISO-8859-1"
    if clave == "JWT_SECRET" and valor.strip() and not _es_base64_de(valor.strip()):
        yield (f"no es Base64 de {BYTES_DE_JWT_SECRET} bytes (ADR 020); "
               "genérala con: openssl rand -base64 32")


def _es_base64_de(valor, bytes_esperados=BYTES_DE_JWT_SECRET):
    try:
        return len(base64.b64decode(valor, validate=True)) == bytes_esperados
    except (binascii.Error, ValueError):
        return False


def tapadas(variables, entorno):
    """Las variables con valor en el archivo que el entorno trae con OTRO valor.

    Docker Compose y Spring dejan ganar al entorno, así que con éstas no se usa el
    archivo. Una vacía en el archivo no cuenta: ahí el entorno es la única fuente.
    """
    return sorted(clave for clave, valor in variables.items()
                  if valor and clave in entorno and entorno[clave] != valor)


def main(argumentos):
    con_entorno = "--entorno" in argumentos
    rutas = [Path(a) for a in argumentos if a != "--entorno"] or [RAIZ / ".env"]
    hubo_problemas = False
    for ruta in rutas:
        if not ruta.is_file():
            print(f"{ruta}: no existe")
            hubo_problemas = True
            continue
        try:
            texto = ruta.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            print(f"{ruta}: no es UTF-8")
            hubo_problemas = True
            continue
        problemas, variables = revisar(texto)
        if con_entorno:
            problemas += [f"{clave}: el entorno la trae con otro valor y le gana al archivo"
                          for clave in tapadas(variables, os.environ)]
        for problema in problemas:
            print(f"{ruta}: {problema}")
        if not problemas:
            print(f"{ruta}: sin problemas")
        hubo_problemas = hubo_problemas or bool(problemas)
    return 1 if hubo_problemas else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
