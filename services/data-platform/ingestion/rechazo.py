#!/usr/bin/env python3
"""
rechazo.py — CanastaMX · la cifra de D-07

QUÉ HACE
--------
Mide, lote por lote, qué proporción de las filas del alcance va a cuarentena y si
el lote se detiene por el umbral de D-07 (5%, `promocion_del_lote.rechazo_maximo`
del contrato). Es la medición que CU-02 (alterno 5b) y RF-24 pedían para
confirmar el umbral con los 38 lotes.

Usa las mismas funciones y en el mismo orden que el activo `lote_promovido` de
`orquestacion/definiciones.py`: la compuerta de fila (`compuerta.revisar_lote`),
el `?` que no se puede reparar (`reparacion.apartar_irreparables`) y las reglas de
grupo (`lote.revisar_grupos`), con las tres cuarentenas juntas y la decisión de
`compuerta.decidir_promocion`. La cifra es la que la plataforma aplica, no una
estimación aparte, y `test_rechazo_mide_lo_mismo_que_lote_promovido` lo comprueba.

No importa Dagster y no escribe nada en `corridas/`: sólo lee los lotes.

USO
---
    # la cifra de D-07 sobre los lotes del alcance
    python services/data-platform/ingestion/rechazo.py --medir LOTES/*.parquet
    # y escribirla en CU-02, entre sus marcas
    python services/data-platform/ingestion/rechazo.py --medir LOTES/*.parquet \\
        --escribir docs/analisis/casos-uso/CU-02-validar-lote-contrato.md

Sale con 1 si algún lote pasa del umbral o se detiene.
"""

import datetime as dt
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import compuerta
import lote as reglas_de_lote
import reparacion
from ingesta import leer_contrato
from salida_segura import preparar_salida

MARCA_INICIO, MARCA_FIN = "<!-- cifra-d07:inicio -->", "<!-- cifra-d07:fin -->"


def medir_lote(ruta, contrato):
    """Lo que `lote_promovido` decide para un lote, sin escribir nada."""
    ruta = Path(ruta)
    df = compuerta.leer_alcance(ruta, contrato)
    limpias, _, por_fila = compuerta.revisar_lote(df, contrato, ruta.name)
    if limpias is None:
        # Le falta una columna al archivo entero: se detiene sin revisar filas.
        return {"lote": ruta.stem, "alcance": len(df), "fila": 0, "reparacion": 0,
                "grupo": 0, "cuarentena": 0, "proporcion": None, "umbral": None,
                "resultado": por_fila["resultado"], "motivo_lote": por_fila["motivo_lote"],
                "por_motivo": {}}
    reparables, _, res_rep = reparacion.apartar_irreparables(limpias, contrato)
    _, _, res_grupo = reglas_de_lote.revisar_grupos(reparables, contrato)
    etapas = (por_fila, res_rep, res_grupo)
    resumen = compuerta.decidir_promocion({
        "filas_entrada": por_fila["filas_entrada"],
        "filas_en_cuarentena": sum(e["filas_en_cuarentena"] for e in etapas),
        "filas_salida": res_grupo["filas_salida"],
    }, contrato)
    return {"lote": ruta.stem, "alcance": por_fila["filas_entrada"],
            "fila": por_fila["filas_en_cuarentena"],
            "reparacion": res_rep["filas_en_cuarentena"],
            "grupo": res_grupo["filas_en_cuarentena"],
            "cuarentena": resumen["filas_en_cuarentena"],
            "proporcion": resumen["proporcion_en_cuarentena"], "umbral": resumen["umbral"],
            "resultado": resumen["resultado"], "motivo_lote": resumen.get("motivo_lote"),
            "por_motivo": {**por_fila["por_motivo"], **res_rep["por_motivo"],
                           **res_grupo["por_motivo"]}}


def medir(rutas, contrato=None):
    contrato = contrato or leer_contrato()
    filas = [medir_lote(r, contrato) for r in sorted(Path(p) for p in rutas)]
    total = {"alcance": sum(f["alcance"] for f in filas),
             "cuarentena": sum(f["cuarentena"] for f in filas),
             "fila": sum(f["fila"] for f in filas),
             "reparacion": sum(f["reparacion"] for f in filas),
             "grupo": sum(f["grupo"] for f in filas),
             "por_motivo": {}}
    for f in filas:
        for m, n in f["por_motivo"].items():
            total["por_motivo"][m] = total["por_motivo"].get(m, 0) + n
    return filas, total


def detenidos(filas):
    return [f for f in filas if f["resultado"] == "DETENIDO"]


def bloque_para_cu02(filas, total, contrato):
    hoy = dt.datetime.now(dt.UTC).date().isoformat()
    umbral = contrato["promocion_del_lote"]["rechazo_maximo"]
    medidos = [f["proporcion"] for f in filas if f["proporcion"] is not None]
    fuera = detenidos(filas)
    if fuera:
        lista = ", ".join(f"`{f['lote']}` ({f['proporcion']:.2%})" if f["proporcion"] is not None
                          else f"`{f['lote']}` ({f['motivo_lote']})" for f in fuera)
        veredicto = (f"- **{len(fuera)} de {len(filas)} lotes se detienen** con el umbral de "
                     f"{umbral:.0%}: {lista}.")
    else:
        veredicto = (f"- **Ningún lote pasa del {umbral:.0%}**: los {len(filas)} se promueven, "
                     "y el umbral de D-07 se confirma.")
    rango = (f"- La proporción en cuarentena va de **{min(medidos):.4%}** a "
             f"**{max(medidos):.4%}** por lote (mediana {statistics.median(medidos):.4%})."
             if medidos else "")
    motivos = ", ".join(f"`{m}` {n:,}" for m, n in sorted(total["por_motivo"].items())) or "ninguno"
    return (f"{MARCA_INICIO}\n"
            f"> Medido el {hoy} con `services/data-platform/ingestion/rechazo.py --medir`, "
            f"contrato {contrato['version']}, sobre {len(filas)} lotes y {total['alcance']:,} "
            f"filas del alcance (el contrato dice {contrato['medicion']['filas']:,}). No se "
            "escribe a mano: si algo cambia, se vuelve a correr.\n\n"
            f"{veredicto}\n"
            + (f"{rango}\n" if rango else "")
            + f"- Filas en cuarentena: **{total['cuarentena']:,}** "
            f"({total['cuarentena'] / max(total['alcance'], 1):.4%} del alcance): "
            f"{total['fila']:,} de fila, {total['reparacion']:,} por el `?` y "
            f"{total['grupo']:,} de grupo. Registros por motivo: {motivos}.\n"
            f"{MARCA_FIN}")


def main():
    preparar_salida()
    import argparse

    ap = argparse.ArgumentParser(description="La cifra de D-07: qué proporción de cada "
                                             "lote va a cuarentena y qué lotes se detienen")
    ap.add_argument("--medir", nargs="+", metavar="LOTE",
                    help="los archivos de los lotes (.parquet o .csv)")
    ap.add_argument("--escribir", help="el documento donde dejar la cifra, entre "
                                       f"las marcas {MARCA_INICIO} y {MARCA_FIN}")
    a = ap.parse_args()
    if not a.medir:
        ap.error("falta --medir con los archivos de los lotes")

    contrato = leer_contrato()
    filas, total = medir(a.medir, contrato)
    print(f"contrato {contrato['version']} · {len(filas)} lotes · población: ALCANCE · "
          f"umbral {contrato['promocion_del_lote']['rechazo_maximo']:.0%}\n")
    print(f"  {'lote':<14}{'alcance':>11}{'de fila':>9}{'por ?':>7}{'grupo':>7}"
          f"{'total':>8}{'%':>9}   resultado")
    for f in filas:
        pct = f"{f['proporcion']:.3%}" if f["proporcion"] is not None else "—"
        print(f"  {f['lote']:<14}{f['alcance']:>11,}{f['fila']:>9,}{f['reparacion']:>7,}"
              f"{f['grupo']:>7,}{f['cuarentena']:>8,}{pct:>9}   {f['resultado']}"
              + (f" · {f['motivo_lote']}" if f["motivo_lote"] else ""))
    print(f"  {'total':<14}{total['alcance']:>11,}{total['fila']:>9,}{total['reparacion']:>7,}"
          f"{total['grupo']:>7,}{total['cuarentena']:>8,}")
    fuera = detenidos(filas)
    print(f"\n{'✗' if fuera else '✓'} {len(fuera)} de {len(filas)} lotes se detienen con el umbral")
    if a.escribir:
        doc = Path(a.escribir)
        texto = doc.read_text(encoding="utf-8")
        if texto.count(MARCA_INICIO) != 1 or texto.count(MARCA_FIN) != 1:
            print(f"✗ {doc} no trae una sola vez las marcas {MARCA_INICIO} y {MARCA_FIN}",
                  file=sys.stderr)
            return 1
        ini, fin = texto.index(MARCA_INICIO), texto.index(MARCA_FIN) + len(MARCA_FIN)
        doc.write_text(texto[:ini] + bloque_para_cu02(filas, total, contrato) + texto[fin:],
                       encoding="utf-8")
        print(f"✓ cifra escrita en {doc}")
    return 1 if fuera else 0


if __name__ == "__main__":
    sys.exit(main())
