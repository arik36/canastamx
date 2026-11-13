"""Compara una respuesta con su esquema en analitica.yaml 0.2.1 (ADR 017: el contrato
publicado manda). Cubre lo que usan las rutas: objetos, listas, `$ref`, `required`,
`enum`, `pattern`, `minimum`, y desde T069 los números, `oneOf` y los tipos que
admiten `null` (`type: [string, "null"]`). Un campo que el esquema no declara también
es un error: así un `snake_case` que se cuele no pasa."""

import re
from pathlib import Path

import yaml

RUTA = Path(__file__).resolve().parents[3] / "docs" / "analisis" / "openapi" / "analitica.yaml"
CONTRATO = yaml.safe_load(RUTA.read_text(encoding="utf-8"))


def _resuelto(nodo):
    while "$ref" in nodo:
        destino = CONTRATO
        for parte in nodo["$ref"].removeprefix("#/").split("/"):
            destino = destino[parte]
        nodo = destino
    return nodo


def operaciones():
    """[(ruta, método, operación)] de todo el contrato."""
    return [(ruta, metodo, o) for ruta, metodos in CONTRATO["paths"].items()
            for metodo, o in metodos.items()]


def esquema(ruta, metodo, estado, medio="application/json"):
    respuesta = _resuelto(CONTRATO["paths"][ruta][metodo]["responses"][str(estado)])
    return respuesta["content"][medio]["schema"]


def errores(valor, nodo, donde="$"):
    e = _resuelto(nodo)
    if "oneOf" in e:
        cumplen = [o for o in e["oneOf"] if not errores(valor, o, donde)]
        if len(cumplen) == 1:
            return []
        return [f"{donde}: cumple {len(cumplen)} de las {len(e['oneOf'])} opciones de oneOf"]
    if "enum" in e and valor not in e["enum"]:
        return [f"{donde}: {valor!r} no está en {e['enum']}"]
    tipo = e.get("type")
    if isinstance(tipo, list):                  # [string, "null"]: uno de los dos
        if valor is None:
            return [] if "null" in tipo else [f"{donde}: no admite null"]
        tipo = next(t for t in tipo if t != "null")
    elif valor is None:
        return [] if tipo in (None, "null") else [f"{donde}: no admite null"]
    if tipo == "null":
        return [f"{donde}: tiene que ser null"]
    if tipo == "object":
        if not isinstance(valor, dict):
            return [f"{donde}: no es objeto"]
        props = e.get("properties", {})
        out = [f"{donde}.{k}: falta" for k in e.get("required", []) if k not in valor]
        out += [f"{donde}.{k}: no está en el contrato" for k in valor if props and k not in props]
        for k, sub in props.items():
            if k in valor:
                out += errores(valor[k], sub, f"{donde}.{k}")
        return out
    if tipo == "array":
        if not isinstance(valor, list):
            return [f"{donde}: no es lista"]
        return [x for i, v in enumerate(valor) for x in errores(v, e.get("items", {}), f"{donde}[{i}]")]
    if tipo == "string":
        if not isinstance(valor, str):
            return [f"{donde}: no es texto"]
        if "pattern" in e and not re.search(e["pattern"], valor):
            return [f"{donde}: {valor!r} no cumple {e['pattern']}"]
        return []
    if tipo == "integer":
        if not isinstance(valor, int) or isinstance(valor, bool):
            return [f"{donde}: no es entero"]
        return [f"{donde}: menor que {e['minimum']}"] if valor < e.get("minimum", valor) else []
    if tipo == "number":
        if not isinstance(valor, int | float) or isinstance(valor, bool):
            return [f"{donde}: no es número"]
        return [f"{donde}: menor que {e['minimum']}"] if valor < e.get("minimum", valor) else []
    if tipo == "boolean" and not isinstance(valor, bool):
        return [f"{donde}: no es booleano"]
    return []
