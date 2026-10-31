"""Un ayudante de las pruebas: una copia del contrato con su propia tabla de ambiguos.

La tabla real (`contracts/mojibake-ambiguos.csv`) sale del corpus y cambia si el
corpus cambia. Las pruebas de la regla por frecuencia necesitan saber exactamente
qué gemelos hay y cuántas filas tiene cada uno, así que escriben la suya en una
carpeta temporal y una COPIA del contrato apunta a ella. El contrato real no se
toca.
"""

import copy
import csv
from pathlib import Path

# Dos ambiguos de prueba: uno que la frecuencia resuelve (5,000 contra 120, más de
# diez a uno) y uno parejo (300 contra 200). Ninguno está en el diccionario real.
CANDIDATOS = [
    ("marca", "Kellogg?s", "Kellogg's", 5000),
    ("marca", "Kellogg?s", "Kellogg´s", 120),
    ("marca", "Nestl?", "Nestlé", 300),
    ("marca", "Nestl?", "Nestle", 200),
]


def escribir_candidatos(ruta, filas):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["columna", "valor_roto", "candidato", "filas"])
        w.writerows(filas)
    return ruta


def con_candidatos(contrato, carpeta, filas=CANDIDATOS, **ambiguo):
    """Una copia del contrato cuyos candidatos son `filas`, con `ambiguo` cambiado."""
    otro = copy.deepcopy(contrato)
    am = otro["normalizacion"]["reparar_interrogantes"]["ambiguo"]
    am["candidatos"] = str(escribir_candidatos(Path(carpeta) / "candidatos.csv", filas))
    am.update(ambiguo)
    return otro
