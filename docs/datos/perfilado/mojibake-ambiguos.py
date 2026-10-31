"""
mojibake-ambiguos.py — T048 · los gemelos de cada `?` ambiguo y sus filas en el corpus

Genera `contracts/mojibake-ambiguos.csv`, la tabla que el contrato 1.3.6 declara en
`normalizacion.reparar_interrogantes.ambiguo.candidatos`. La regla por frecuencia
(D-03) compara cuántas filas tiene cada gemelo posible EN EL CORPUS, y el corpus no
entra a la plataforma: por eso la cuenta se hace aquí, una vez, y queda versionada.

La tabla trae CONTEOS y no decisiones. Quién gana lo decide
`services/data-platform/ingestion/reparacion.py` al leerla, con el `umbral` del
contrato: si el contrato lo cambia, la decisión cambia sin volver a correr esto.

ANTES DE ESCRIBIR, COMPRUEBA QUE ES LA MISMA POBLACIÓN Y EL MISMO MÉTODO
------------------------------------------------------------------------
Con el mismo corpus y la misma definición de gemelo (`reparacion.es_gemelo()`, la
de `mojibake.py`), los valores de gemelo único tienen que ser exactamente las 1,650
entradas de `contracts/mojibake-diccionario.csv`, con la misma reparación. Si no
coinciden, el corpus o el método cambiaron, y una tabla de ambiguos calculada así
no sería hermana del diccionario: el guion se niega a escribirla y dice dónde
difieren.

Uso, desde la raíz del repositorio:

    python docs/datos/perfilado/mojibake-ambiguos.py              # sólo cuenta
    python docs/datos/perfilado/mojibake-ambiguos.py --escribir   # y escribe la tabla
    CANASTAMX_DATOS=/otra/ruta python docs/datos/perfilado/mojibake-ambiguos.py
"""

import argparse
import csv
import glob
import os
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "services" / "data-platform" / "ingestion"))

import reparacion
from ingesta import leer_contrato

DATOS = Path(os.environ.get("CANASTAMX_DATOS", Path.home() / "canastamx-datos"))
PARQUETS = DATOS / "procesado" / "por_archivo"


def clasificar(con, fuente, columna):
    """Para cada valor roto de la columna: sus gemelos y las filas de cada uno."""
    valores = con.execute(
        f'SELECT CAST("{columna}" AS VARCHAR) AS v, count(*) AS filas FROM {fuente} '
        f'WHERE "{columna}" IS NOT NULL GROUP BY 1').fetchall()
    sanos = {v: n for v, n in valores if reparacion.INTERROGANTE not in v}
    por_largo = defaultdict(list)
    for v in sanos:
        por_largo[len(v)].append(v)
    for v, filas in valores:
        if reparacion.INTERROGANTE not in v:
            continue
        gemelos = [s for s in por_largo.get(len(v), ()) if reparacion.es_gemelo(v, s)]
        yield v, filas, sorted(((s, sanos[s]) for s in gemelos), key=lambda g: (-g[1], g[0]))


def main():
    ap = argparse.ArgumentParser(description="Gemelos de los `?` ambiguos, contados en el corpus")
    ap.add_argument("--origen", default=str(PARQUETS / "*.parquet"),
                    help="glob de los parquet del corpus completo")
    ap.add_argument("--escribir", action="store_true",
                    help="escribe la tabla que declara el contrato")
    a = ap.parse_args()

    import duckdb

    contrato = leer_contrato()
    r = reparacion.regla(contrato)
    if not glob.glob(a.origen):
        sys.exit(f"no hay parquet en {a.origen}. Es el corpus completo de perfilado_nivel2.py")
    con = duckdb.connect()
    fuente = f"read_parquet('{a.origen}', union_by_name=true)"

    diccionario = {}
    with (REPO / r["diccionario"]).open(encoding="utf-8", newline="") as f:
        for fila in csv.DictReader(f):
            diccionario[(fila["columna"], fila["valor_roto"])] = fila["reparado"]

    unicos, ambiguos, sin_gemelo = {}, [], []
    for columna in r["aplica_a"]:
        for v, filas, gemelos in clasificar(con, fuente, columna):
            if len(gemelos) == 1:
                unicos[(columna, v)] = gemelos[0][0]
            elif gemelos:
                ambiguos.append((columna, v, filas, gemelos))
            else:
                sin_gemelo.append((columna, v, filas))

    print(f"corpus: {a.origen}")
    print(f"  gemelo único : {len(unicos):>6,} valores · el diccionario trae {len(diccionario):,}")
    print(f"  ambiguos     : {len(ambiguos):>6,} valores · "
          f"{sum(len(g) for *_, g in ambiguos):,} gemelos posibles")
    print(f"  sin gemelo   : {len(sin_gemelo):>6,} valores")

    faltan = sorted(set(diccionario) - set(unicos))
    sobran = sorted(set(unicos) - set(diccionario))
    distintos = sorted(k for k in set(unicos) & set(diccionario) if unicos[k] != diccionario[k])
    if faltan or sobran or distintos:
        print("\n✗ no reproduce el diccionario: el corpus o el método no son los mismos.")
        for nombre, lista in (("en el diccionario y no aquí", faltan),
                              ("aquí y no en el diccionario", sobran),
                              ("con otra reparación", distintos)):
            if lista:
                print(f"  {len(lista):,} {nombre}; por ejemplo {lista[:3]}")
        print("  No se escribe la tabla.")
        return 1
    print("\n✓ reproduce el diccionario entrada por entrada: misma población, mismo método")

    umbral = r["umbral"]
    resueltos = sum(1 for *_, g in ambiguos if g[0][1] >= umbral * g[1][1])
    print(f"  con el umbral del contrato ({umbral}), la frecuencia resuelve {resueltos:,} "
          f"de los {len(ambiguos):,} ambiguos; los demás van a {r['motivo_empate']}")

    if a.escribir:
        destino = REPO / r["candidatos"]
        with destino.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["columna", "valor_roto", "candidato", "filas"])
            for columna, v, _, gemelos in sorted(ambiguos):
                for candidato, filas in gemelos:
                    w.writerow([columna, v, candidato, filas])
        print(f"\n✓ {destino.relative_to(REPO)} · {sum(len(g) for *_, g in ambiguos):,} renglones")
    return 0


if __name__ == "__main__":
    sys.exit(main())
