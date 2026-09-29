"""
sembrar-semana.py — CanastaMX

Siembra en el tablero las tarjetas de UNA semana, leídas de un archivo JSON
(por ejemplo semana-04.json), y las deja listas: issue creado con su etiqueta,
hito y responsable; agregado al proyecto; y con Semana, Frente, Fecha límite y
Status = «Esta semana» ya llenos.

A diferencia de sembrar-tablero.sh, SE PUEDE VOLVER A CORRER: si ya existe un
issue con el mismo título exacto, no crea otro; sólo se asegura de que esté en
el proyecto y con los campos bien.

USO, desde la raíz del repositorio:
    python3 infra/scripts/sembrar-semana.py docs/equipo/semanas/semana-04.json --simular
    python3 infra/scripts/sembrar-semana.py docs/equipo/semanas/semana-04.json

ANTES, una sola vez:
    gh auth refresh -s project -h github.com
"""

import json
import re
import shutil
import subprocess
import sys
from datetime import date

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN · la misma de sembrar-tablero.sh y llenar-tablero.py
# ─────────────────────────────────────────────────────────────────────────────
REPO = "arik36/canastamx"
DUENO = "arik36"
NUMERO = 1                      # .../users/arik36/projects/1
USUARIOS = {"A": "arik36", "B": "Wolff06", "C1": "lisslar",
            "C2": "Renato-Rios", "D": "alesitaK"}
CAMPO_SEMANA, CAMPO_FRENTE, CAMPO_FECHA, CAMPO_STATUS = (
    "Semana", "Frente", "Fecha límite", "Status")
COLUMNA = "Esta semana"
FRENTES = {"Datos", "Infra", "Dominio", "Móvil", "Web", "Equipo"}
MESES = ["ene", "feb", "mar", "abr", "may", "jun",
         "jul", "ago", "sep", "oct", "nov", "dic"]
# ─────────────────────────────────────────────────────────────────────────────

SIMULAR = "--simular" in sys.argv
ERRORES = []


def gh(*args, como_json=False):
    """Corre gh sin shell. Devuelve el texto (o el JSON) o None si falló."""
    r = subprocess.run(["gh", *args], capture_output=True, text=True, check=False)
    if r.returncode != 0:
        ERRORES.append(f"gh {' '.join(args[:3])} … → {(r.stderr or r.stdout).strip()[:300]}")
        return None
    salida = r.stdout.strip()
    return json.loads(salida) if como_json else salida


def validar(sem):
    malos = []
    for t in sem["tareas"]:
        m = re.match(r"^\[S(\d+)\]\[([^\]]+)\] \S", t["titulo"])
        if not m:
            malos.append(f"{t['id']}: el título no empieza con [S#][Frente]")
        elif int(m.group(1)) != sem["semana"] or m.group(2) != t["frente"]:
            malos.append(f"{t['id']}: el título dice S{m.group(1)}/{m.group(2)} y la tarea "
                         f"S{sem['semana']}/{t['frente']}")
        if t["frente"] not in FRENTES:
            malos.append(f"{t['id']}: frente «{t['frente']}» no es opción del tablero")
        if t["clave"] not in USUARIOS:
            malos.append(f"{t['id']}: clave «{t['clave']}» desconocida")
        date.fromisoformat(t["fecha"])
        for d in t.get("depende", []):
            if d not in [x["id"] for x in sem["tareas"]] and not re.fullmatch(r"#\d+", d):
                malos.append(f"{t['id']}: depende de «{d}», que no está en el archivo")
    if malos:
        print("✗ El archivo tiene problemas:\n  " + "\n  ".join(malos), file=sys.stderr)
        sys.exit(1)


def fecha_larga(iso):
    d = date.fromisoformat(iso)
    return f"{d.day} {MESES[d.month - 1]} de {d.year}"


def cuerpo(t, semana, numeros):
    deps = []
    for d in t.get("depende", []):
        if d.startswith("#"):
            deps.append(d)
        elif d in numeros:
            deps.append(f"#{numeros[d]} ({d})")
        else:
            deps.append(f"{d} (su número se conoce al crearla)")
    depende = ", ".join(deps) if deps else "Nada."
    if t.get("nota_dependencia"):
        depende += "\n\n" + t["nota_dependencia"]
    donde = t["donde"] if " " in t["donde"] else f"`{t['donde']}`"
    return (f"## Qué hay que hacer\n\n{t['que']}\n\n"
            f"## Cómo saber que quedó\n\n{t['criterio']}\n\n"
            f"## Dónde queda\n\n{donde}\n\n"
            f"## Depende de\n\n{depende}\n\n---\n\n"
            f"Semana {semana} · Frente: {t['frente']} · Responsable: {t['clave']} · "
            f"Fecha límite: {fecha_larga(t['fecha'])} · Tarea: {t['id']}\n\n"
            f"<sub>Sembrado con `infra/scripts/sembrar-semana.py`. Si el criterio de cierre "
            f"no es verificable, corrígelo aquí antes de empezar.</sub>\n")


def buscar_issue(titulo):
    texto = re.sub(r"^\[S\d+\]\[[^\]]+\]\s*", "", titulo).replace('"', "")
    res = gh("issue", "list", "--repo", REPO, "--state", "all", "--limit", "50",
             "--search", f'in:title "{texto}"', "--json", "number,title,url", como_json=True)
    for i in res or []:
        if i["title"].strip() == titulo:
            return i
    return None


def main():
    if len(sys.argv) < 2 or sys.argv[1].startswith("--"):
        print(__doc__)
        sys.exit(2)
    with open(sys.argv[1], encoding="utf-8") as f:
        sem = json.load(f)
    validar(sem)
    semana, hito = sem["semana"], sem["hito"]
    print(f"Semana {semana} · del {sem['del']} al {sem['al']} · hito «{hito}» · "
          f"{len(sem['tareas'])} tareas")
    print(f"Modo: {'SIMULACIÓN · no se escribe nada' if SIMULAR else 'ESCRITURA'}\n")

    hay_gh = shutil.which("gh") is not None
    if not SIMULAR and not hay_gh:
        print("✗ No encuentro gh. Instálalo desde https://cli.github.com", file=sys.stderr)
        sys.exit(1)

    proyecto, campos = None, {}
    if hay_gh:
        proyecto = gh("project", "view", str(NUMERO), "--owner", DUENO,
                      "--format", "json", como_json=True)
        lista = gh("project", "field-list", str(NUMERO), "--owner", DUENO,
                   "--format", "json", "--limit", "50", como_json=True)
        if not proyecto or not lista:
            print("✗ No pude leer el proyecto. ¿Corriste «gh auth refresh -s project -h "
                  "github.com»?\n  " + "\n  ".join(ERRORES), file=sys.stderr)
            sys.exit(1)
        campos = {c["name"]: c for c in lista["fields"]}
        faltan = [c for c in (CAMPO_SEMANA, CAMPO_FRENTE, CAMPO_FECHA, CAMPO_STATUS)
                  if c not in campos]
        if faltan:
            print(f"✗ Faltan campos en el proyecto: {', '.join(faltan)}. Hay: "
                  f"{', '.join(sorted(campos))}", file=sys.stderr)
            sys.exit(1)
        print(f"Proyecto: {proyecto.get('title')}\n")

    def opcion(campo, nombre):
        for o in campos.get(campo, {}).get("options", []):
            if o["name"] == nombre:
                return o["id"]
        return None

    numeros, creados, reusados, editados = {}, 0, 0, 0
    for t in sem["tareas"]:
        print(f"── {t['id']} · {t['clave']} → @{USUARIOS[t['clave']]} · {t['titulo']}")
        existe = buscar_issue(t["titulo"]) if hay_gh else None
        if existe:
            numeros[t["id"]] = existe["number"]
            url = existe["url"]
            reusados += 1
            print(f"   ya existe: #{existe['number']} · no se crea otro")
        elif SIMULAR:
            print("   crearía el issue con este cuerpo:")
            print("   │ " + cuerpo(t, semana, numeros).replace("\n", "\n   │ "))
            continue
        else:
            url = gh("issue", "create", "--repo", REPO, "--title", t["titulo"],
                     "--body", cuerpo(t, semana, numeros), "--label", t["etiqueta"],
                     "--milestone", hito, "--assignee", USUARIOS[t["clave"]])
            if not url:
                print("   ✗ no se pudo crear")
                continue
            numeros[t["id"]] = int(url.rstrip("/").rsplit("/", 1)[-1])
            creados += 1
            print(f"   ✓ creado: {url}")

        valores = [
            (CAMPO_SEMANA, ["--number", str(semana)]),
            (CAMPO_FRENTE, ["--single-select-option-id", opcion(CAMPO_FRENTE, t["frente"])]),
            (CAMPO_FECHA, ["--date", t["fecha"]]),
            (CAMPO_STATUS, ["--single-select-option-id", opcion(CAMPO_STATUS, COLUMNA)]),
        ]
        if SIMULAR:
            print(f"   pondría: Semana {semana} · Frente {t['frente']} · Fecha límite "
                  f"{t['fecha']} · Status «{COLUMNA}»")
            continue
        item = gh("project", "item-add", str(NUMERO), "--owner", DUENO, "--url", url,
                  "--format", "json", como_json=True)
        if not item:
            print("   ✗ no se pudo agregar al proyecto")
            continue
        for campo, arg in valores:
            if arg[1] is None:
                ERRORES.append(f"{t['id']}: el campo «{campo}» no tiene la opción que busco")
                print(f"   ✗ {campo}: opción no encontrada")
                continue
            if gh("project", "item-edit", "--id", item["id"], "--project-id", proyecto["id"],
                  "--field-id", campos[campo]["id"], *arg) is not None:
                editados += 1
        print(f"   ✓ en el tablero: Semana {semana} · {t['frente']} · {t['fecha']} · «{COLUMNA}»")

    print(f"\n{'Simulado' if SIMULAR else 'Listo'}: {creados} creados · {reusados} ya existían · "
          f"{editados} campos escritos")
    if ERRORES:
        print(f"\n✗ {len(ERRORES)} problema(s):\n  " + "\n  ".join(ERRORES))
        sys.exit(1)
    if SIMULAR:
        print("\nSi se ve bien, vuelve a correrlo sin --simular.")


if __name__ == "__main__":
    main()
