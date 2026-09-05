#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
llenar-tablero.py — CanastaMX

Llena los campos «Semana», «Frente» y «Fecha límite» de las 30 tarjetas del
tablero, leyéndolos del título y del cuerpo de cada issue. No inventa nada:
el título trae [S1][Datos] y el cuerpo trae «Fecha límite: 7 sep de 2026».

USO
    python3 llenar-tablero.py --simular    # no escribe nada, solo enseña qué haría
    python3 llenar-tablero.py              # escribe de verdad

ANTES DE CORRERLO, una sola vez:
    gh auth refresh -s project -h github.com

    (el permiso «project» no viene por defecto; sin él, gh puede crear issues
    pero no puede tocar los campos de un tablero)

Se puede volver a correr sin miedo: escribe el mismo valor encima. No duplica
nada, a diferencia del guión de siembra.
"""

import json
import re
import subprocess
import sys

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURA ESTO
# El número del proyecto sale de su dirección: .../users/arik36/projects/1
# ─────────────────────────────────────────────────────────────────────────────
DUENO   = "arik36"
NUMERO  = 1

# Nombres exactos de los campos que creaste en Settings → Fields
CAMPO_SEMANA = "Semana"
CAMPO_FRENTE = "Frente"
CAMPO_FECHA  = "Fecha límite"
# ─────────────────────────────────────────────────────────────────────────────

SIMULAR = "--simular" in sys.argv

MESES = {"ene": "01", "feb": "02", "mar": "03", "abr": "04",
         "may": "05", "jun": "06", "jul": "07", "ago": "08",
         "sep": "09", "oct": "10", "nov": "11", "dic": "12"}


def gql(consulta):
    r = subprocess.run(["gh", "api", "graphql", "-f", "query=" + consulta],
                       capture_output=True, text=True)
    if r.returncode != 0:
        salida = (r.stderr or r.stdout).strip()
        print("\n✗ gh falló:\n" + salida, file=sys.stderr)
        if "INSUFFICIENT_SCOPES" in salida or "project" in salida.lower():
            print("\n  Probablemente falta el permiso. Corre esto y vuelve a intentar:"
                  "\n      gh auth refresh -s project -h github.com", file=sys.stderr)
        sys.exit(1)
    d = json.loads(r.stdout)
    if "errors" in d:
        print("\n✗ La consulta devolvió errores:", file=sys.stderr)
        print(json.dumps(d["errors"], indent=2, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
    return d["data"]


CONSULTA = """
query {
  %s(login: "%s") {
    projectV2(number: %d) {
      id
      title
      fields(first: 50) {
        nodes {
          ... on ProjectV2Field            { id name }
          ... on ProjectV2IterationField    { id name }
          ... on ProjectV2SingleSelectField { id name options { id name } }
        }
      }
      items(first: 100) {
        nodes {
          id
          content { ... on Issue { number title body } }
        }
      }
    }
  }
}
"""

MUTACION = """
mutation {
  updateProjectV2ItemFieldValue(input: {
    projectId: "%s", itemId: "%s", fieldId: "%s", value: { %s }
  }) { projectV2Item { id } }
}
"""


def traer_proyecto():
    """Prueba como usuario; si no, como organización."""
    for tipo in ("user", "organization"):
        datos = gql(CONSULTA % (tipo, DUENO, NUMERO))
        raiz = datos.get(tipo)
        if raiz and raiz.get("projectV2"):
            return raiz["projectV2"]
    print(f"✗ No encontré el proyecto número {NUMERO} de {DUENO}.", file=sys.stderr)
    sys.exit(1)


def main():
    proy = traer_proyecto()
    print(f"Proyecto: {proy['title']}")
    print(f"Modo:     {'SIMULACIÓN — no se escribe nada' if SIMULAR else 'ESCRITURA'}\n")

    campos = {n["name"]: n for n in proy["fields"]["nodes"] if n.get("name")}

    faltan = [c for c in (CAMPO_SEMANA, CAMPO_FRENTE, CAMPO_FECHA) if c not in campos]
    if faltan:
        print("✗ Faltan campos en el proyecto: " + ", ".join(faltan), file=sys.stderr)
        print("  Están en Settings → Fields. Los nombres tienen que coincidir exactamente,"
              "\n  acentos incluidos. Los que sí encontré:", file=sys.stderr)
        for n in sorted(campos):
            print("    · " + n, file=sys.stderr)
        sys.exit(1)

    f_semana = campos[CAMPO_SEMANA]
    f_frente = campos[CAMPO_FRENTE]
    f_fecha  = campos[CAMPO_FECHA]

    if "options" not in f_frente:
        print(f"✗ «{CAMPO_FRENTE}» no es de tipo Single select.", file=sys.stderr)
        sys.exit(1)
    opciones = {o["name"]: o["id"] for o in f_frente["options"]}

    escritos, saltados, errores = 0, 0, []

    for it in proy["items"]["nodes"]:
        c = it.get("content") or {}
        titulo = c.get("title")
        if not titulo:
            saltados += 1
            continue

        m = re.match(r"^\[S(\d+)\]\[([^\]]+)\]", titulo)
        if not m:
            errores.append(f"#{c.get('number')} título sin [S#][Frente]: {titulo}")
            continue
        semana, frente = int(m.group(1)), m.group(2)

        if frente not in opciones:
            errores.append(f"#{c.get('number')} el frente «{frente}» no es una opción del campo "
                           f"«{CAMPO_FRENTE}» (hay: {', '.join(sorted(opciones))})")
            continue

        fecha = None
        fm = re.search(r"Fecha l[ií]mite:\s*(\d{1,2})\s+(\w{3})\w*\s+de\s+(\d{4})",
                       c.get("body") or "")
        if fm and fm.group(2).lower() in MESES:
            fecha = f"{fm.group(3)}-{MESES[fm.group(2).lower()]}-{int(fm.group(1)):02d}"

        print(f"  #{c['number']:<3} S{semana} · {frente:<8} · {fecha or '(sin fecha)':<11} "
              f"{titulo[:52]}")

        if SIMULAR:
            escritos += 1
            continue

        valores = [(f_semana["id"], f"number: {semana}"),
                   (f_frente["id"], f'singleSelectOptionId: "{opciones[frente]}"')]
        if fecha:
            valores.append((f_fecha["id"], f'date: "{fecha}"'))

        for id_campo, valor in valores:
            gql(MUTACION % (proy["id"], it["id"], id_campo, valor))
        escritos += 1

    print()
    print(f"{'Simuladas' if SIMULAR else 'Actualizadas'}: {escritos} tarjetas"
          + (f" · sin contenido: {saltados}" if saltados else ""))
    if errores:
        print(f"\n✗ {len(errores)} con problema:")
        for e in errores:
            print("   " + e)
        sys.exit(1)
    if SIMULAR:
        print("\nSi la lista se ve bien, vuelve a correrlo sin --simular.")


if __name__ == "__main__":
    main()
