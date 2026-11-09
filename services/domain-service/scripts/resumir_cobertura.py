"""Resume jacoco.csv y los informes Surefire sin dependencias externas (T055)."""

import csv
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

PAQUETE = "mx.tecnm.canastamx.domain_service.domain"
SERVICIO = Path(__file__).resolve().parents[1]


def contador(fila, tipo):
    cubiertos = int(fila[f"{tipo}_COVERED"])
    return cubiertos, cubiertos + int(fila[f"{tipo}_MISSED"])


def cobertura(archivo):
    clases = []
    with archivo.open(encoding="utf-8", newline="") as entrada:
        for fila in csv.DictReader(entrada):
            paquete = fila["PACKAGE"]
            if paquete == PAQUETE or paquete.startswith(PAQUETE + "."):
                clases.append((f"{paquete}.{fila['CLASS']}",
                               contador(fila, "LINE"), contador(fila, "BRANCH")))
    if not clases or sum(lineas[1] for _, lineas, _ in clases) == 0:
        raise ValueError("El informe no contiene líneas del paquete domain.")
    return sorted(clases)


def pruebas(carpeta):
    archivos = sorted(carpeta.glob("TEST-*.xml"))
    if not archivos:
        raise ValueError("No hay informes Surefire de esta ejecución.")
    totales = dict.fromkeys(("tests", "failures", "errors", "skipped"), 0)
    for archivo in archivos:
        suite = ET.parse(archivo).getroot()
        for campo in totales:
            totales[campo] += int(suite.attrib.get(campo, 0))
    if totales["tests"] - totales["skipped"] <= 0:
        raise ValueError("No se ejecutó ninguna prueba; no se publica cobertura.")
    if totales["failures"] or totales["errors"]:
        raise ValueError("Hay pruebas fallidas; no se publica una medición en verde.")
    return totales


def proporcion(conteo):
    cubiertos, total = conteo
    if total == 0:
        return "N/A (sin ramas)"
    return f"{cubiertos}/{total} ({100 * cubiertos / total:.2f}%)"


def resumen(clases, totales, commit, modificado):
    lineas = tuple(sum(c[1][i] for c in clases) for i in (0, 1))
    ramas = tuple(sum(c[2][i] for c in clases) for i in (0, 1))
    sin_cubrir = [nombre for nombre, linea, _ in clases if linea[0] == 0 and linea[1] > 0]
    texto = [
        "## Cobertura del dominio (T055, #202)", "",
        f"Commit de checkout: `{commit}`.",
        "Estado: **cambios locales sin commit**; la cifra incluye esos cambios."
        if modificado else "Estado: árbol de trabajo limpio.", "",
        ("Herramienta: JaCoCo 0.8.16. Población: todas las clases compiladas de "
        f"`{PAQUETE}` y sus subpaquetes, incluidas clases internas."),
        "Se excluyen controladores, servicios de aplicación, persistencia y seguridad.",
        "Se mide lo ejercitado por toda la suite Java, tanto unitarias como integración.", "",
        (f"Tests run: {totales['tests']}, Failures: {totales['failures']}, "
        f"Errors: {totales['errors']}, Skipped: {totales['skipped']}."), "",
        f"Clases incluidas: {len(clases)}.",
        f"Líneas: **{proporcion(lineas)}**.",
        f"Ramas: **{proporcion(ramas)}**.", "",
        "| Clase | Líneas cubiertas/total | Ramas cubiertas/total |",
        "|---|---|---|",
    ]
    texto.extend(f"| `{nombre}` | {proporcion(linea)} | {proporcion(rama)} |"
                 for nombre, linea, rama in clases)
    texto.extend(["", "Clases sin líneas ejecutadas: "
                  + (", ".join(f"`{nombre}`" for nombre in sin_cubrir) if sin_cubrir else "ninguna.")])
    texto.extend(["", ("Los porcentajes totales suman los contadores; no promedian porcentajes "
                  "por clase. N/A significa que la clase no tiene ramas, no cobertura del 100%."),
                  ("Esta medición no impone un umbral mínimo ni cubre funcionalidades "
                  "retiradas por el recorte del 5 de noviembre."), ""])
    return "\n".join(texto)


def main():
    try:
        target = SERVICIO / "target"
        clases = cobertura(target / "site/jacoco/jacoco.csv")
        totales = pruebas(target / "surefire-reports")
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=SERVICIO, text=True).strip()
        modificado = bool(subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=SERVICIO, text=True).strip())
        texto = resumen(clases, totales, commit, modificado)
        (target / "cobertura-dominio.md").write_text(texto, encoding="utf-8")
        print(texto)
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as salida:
                salida.write(texto)
    except (OSError, ValueError, KeyError, ET.ParseError, subprocess.CalledProcessError) as error:
        print(f"No se pudo medir la cobertura: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
