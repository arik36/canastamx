#!/usr/bin/env python3
"""CanastaMX · T053 (#206) · H3 medida sobre los 200 pares (ADR 004 §1, recuento del ADR 014).

QUÉ MIDE
--------
La hipótesis, como la dejó el ADR 014 §5: *«la reconciliación de nombres de artículo
entre cadenas alcanza una cobertura ≥ 85% con precisión ≥ 90%»*, sobre la muestra
calificada `docs/datos/perfilado/h3-muestra-para-calificar.txt`. Cada par son dos
artículos que la normalización dejó en claves distintas, y la calificación dice si
son el mismo artículo. Se cuenta como dice el ADR 004 §1:

  · COBERTURA, en la mitad por parecido (pares 001 a 100): de los «sí», cuántos unió.
  · PRECISIÓN, en la mitad al azar (101 a 200): de los pares que unió, cuántos son
    «sí». Su población son los pares unidos, y se dice cuántos son. Se da también
    sobre los 200, porque la mitad por parecido trae los «no» más difíciles.
  · Aparte, los pares que sólo difieren en `marca` (ADR 004 §2), que no entran en la
    cobertura. En esta muestra son cero por construcción, y se cuentan igual.

Si la meta no se alcanza, se reporta la cifra que salió (criterio de #206). Las dos
mitades son las de `h3-muestra-para-calificar.py`: primero los 100 más parecidos y
después los 100 al azar.

DOS CIFRAS: LA MUESTRA Y LA PLATAFORMA NO TIENEN LA MISMA POBLACIÓN
------------------------------------------------------------------
`h3-muestra-para-calificar.py` armó los pares con el corpus completo y el recorte de
catálogos; no aplica el de entidades ni el de la ventana. La plataforma ingiere sólo
el alcance del contrato, así que algunos artículos de la muestra nunca llegan a
`dim_articulo`. Por eso el informe da dos cifras, cada una con su población:

  1. SOBRE LOS 200 PARES, la de H3 (ADR 004 §1 y criterio de #206). La reconciliación
     implementada —estas reglas y este código— se aplica a los artículos de la
     muestra junto con el catálogo cargado, y un par está unido si sus dos artículos
     quedan en el mismo grupo.
  2. DENTRO DEL ALCANCE DE LA PLATAFORMA: sólo los pares con sus dos artículos en
     `dim_articulo`, y unido quiere decir el mismo `articulo_canonico_key` en la
     estrella cargada. Es lo que ve el producto.

LO QUE LAS CIFRAS NO DICEN
--------------------------
La lista de palabras y el umbral difuso se calibraron contra esta misma muestra,
como pidió el ADR 004: las dos cifras son DENTRO de la muestra. Dicen que las reglas
reproducen la calificación, no cuánto cubren fuera de ella. Por eso el informe trae,
además, todas las uniones que la reconciliación hizo en el catálogo real, para
revisarlas a mano.

USO
---
    # contra postgres-analytics: lo que cargó la plataforma (las ANALYTICS_* del .env)
    python services/data-platform/ingestion/h3.py
    # contra el DuckDB de la simulación
    python services/data-platform/ingestion/h3.py --simular
    # y deja el informe en docs/datos/perfilado/h3-medicion.txt
    python services/data-platform/ingestion/h3.py --escribir
"""

import argparse
import dataclasses
import datetime as dt
import itertools
import re
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))

import estrella
import intermedia
import reconciliacion
from ingesta import CONTRATO, leer_contrato, sha256_de
from salida_segura import preparar_salida

RAIZ = CONTRATO.parent.parent
MUESTRA = RAIZ / "docs" / "datos" / "perfilado" / "h3-muestra-para-calificar.txt"
INFORME = RAIZ / "docs" / "datos" / "perfilado" / "h3-medicion.txt"
PARES, POR_MITAD = 200, 100
# H3 tal como la dejó el ADR 014 §5.1. Moverlas es otro ADR, no otra corrida.
META = {"cobertura": 0.85, "precision": 0.90}
MITADES = ("parecido", "azar")
NOMBRE = {"parecido": "mitad por parecido", "azar": "mitad al azar"}

_BLOQUE = re.compile(r"^par (\d{3}) · parecido ([0-9.]+)$", re.MULTILINE)
_CLAVES = re.compile(r"ya normalizados.*?\n\s+A: (.+?)\n\s+B: (.+?)\n", re.DOTALL)
_CASILLAS = re.compile(r"¿son el MISMO artículo\?\s+\[(.?)\] sí\s+\[(.?)\] no")


@dataclasses.dataclass(frozen=True)
class Par:
    n: int
    mitad: str
    producto_a: str
    presentacion_a: str
    producto_b: str
    presentacion_b: str
    si: bool

    @property
    def a(self):
        return (self.producto_a, self.presentacion_a)

    @property
    def b(self):
        return (self.producto_b, self.presentacion_b)


def leer_muestra(ruta=MUESTRA):
    """Los 200 pares calificados, con sus claves ya normalizadas y su veredicto.

    Se lee lo que el archivo dice debajo de «ya normalizados»: es lo que se
    calificó (ADR 004 §1), y es la forma de `producto_c` y `presentacion_c`. Si un
    par no trae sus claves, o no tiene exactamente una casilla marcada, no se mide
    nada: una muestra a medias da una cifra que parece buena y no es de nadie."""
    texto = Path(ruta).read_text(encoding="utf-8")
    inicios = [m.start() for m in _BLOQUE.finditer(texto)] + [len(texto)]
    pares = []
    for ini, fin in itertools.pairwise(inicios):
        bloque = texto[ini:fin]
        n = int(_BLOQUE.match(bloque).group(1))
        claves, casillas = _CLAVES.search(bloque), _CASILLAS.search(bloque)
        if not claves or not casillas:
            raise ValueError(f"el par {n:03d} no trae sus claves normalizadas o su casilla")
        si, no = (c.strip().lower() == "x" for c in casillas.groups())
        if si == no:
            raise ValueError(f"el par {n:03d} tiene que estar marcado «sí» o «no», y sólo uno")
        (pa, ra), (pb, rb) = (c.strip().split(" · ", 1) for c in claves.groups())
        pares.append(Par(n, "parecido" if n <= POR_MITAD else "azar", pa, ra, pb, rb, si))
    if [p.n for p in pares] != list(range(1, PARES + 1)):
        raise ValueError(f"la muestra tiene que traer los pares 001 a {PARES:03d}, en orden; "
                         f"trae {len(pares)}")
    return pares


def _tasa(numerador, denominador):
    return {"numerador": numerador, "denominador": denominador,
            "valor": numerador / denominador if denominador else None}


def medir(pares, canonico):
    """`canonico` es {(producto_c, presentacion_c): articulo_canonico_key}, el de la
    estrella cargada. Devuelve las cuentas por mitad, las tasas y cada par."""
    cuentas = {m: dict.fromkeys(("pares", "si", "no", "tp", "fn", "fp", "tn",
                                 "sin_medir", "solo_marca"), 0) for m in MITADES}
    detalle = []
    for p in pares:
        c = cuentas[p.mitad]
        c["pares"] += 1
        c["si" if p.si else "no"] += 1
        if p.a == p.b:
            resultado = "solo_marca"
        elif p.a not in canonico or p.b not in canonico:
            resultado = "sin_medir"
        else:
            unido = canonico[p.a] == canonico[p.b]
            resultado = ("tp" if unido else "fn") if p.si else ("fp" if unido else "tn")
        c[resultado] += 1
        detalle.append((p, resultado))
    total = {k: sum(cuentas[m][k] for m in MITADES) for k in cuentas["parecido"]}
    par, azar = cuentas["parecido"], cuentas["azar"]
    r = {"cuentas": cuentas, "total": total, "pares": detalle,
         "cobertura": _tasa(par["tp"], par["tp"] + par["fn"]),
         "precision": _tasa(azar["tp"], azar["tp"] + azar["fp"]),
         "precision_200": _tasa(total["tp"], total["tp"] + total["fp"]),
         "no_separados": {m: _tasa(cuentas[m]["tn"], cuentas[m]["tn"] + cuentas[m]["fp"])
                          for m in MITADES}}
    r["cumple"] = {k: r[k]["valor"] is not None and r[k]["valor"] >= META[k] for k in META}
    return r


def _pct(tasa):
    if tasa["valor"] is None:
        return f"{tasa['numerador']} / {tasa['denominador']} = sin población"
    return (f"{tasa['numerador']} / {tasa['denominador']} = "
            f"{100 * tasa['valor']:.1f} %")


def particiones(filas):
    """{articulo_key: frozenset del grupo}: la forma de comparar dos reconciliaciones
    sin que importe qué artículo quedó de canónico."""
    grupos = {}
    for articulo, canonico in filas:
        grupos.setdefault(canonico, set()).add(articulo)
    return {a: frozenset(g) for g in grupos.values() for a in g}


def con_la_muestra(pares, articulos, reglas, con):
    """La reconciliación implementada sobre el catálogo cargado MÁS los artículos de la
    muestra que no están en él (los que la plataforma no ingiere: ver el encabezado).

    Devuelve {(producto_c, presentacion_c): grupo} para todos, y los artículos de la
    muestra que faltaban en el catálogo. Es la cifra de H3: «la reconciliación ya
    implementada, contra esta muestra» (ADR 004)."""
    en_el_catalogo = {(p, r) for _, p, r, _ in articulos}
    faltan = sorted({x for p in pares for x in (p.a, p.b)} - en_el_catalogo)
    filas = [(k, p, r, 0) for k, p, r, _ in articulos]
    # Llaves negativas: las de dim_articulo empiezan en 1 y no chocan.
    filas += [(-i, p, r, 0) for i, (p, r) in enumerate(faltan, start=1)]
    grupos = reconciliacion.agrupar(filas, reglas, con)
    nombre = {k: (p, r) for k, p, r, _ in filas}
    return {nombre[k]: canonico for k, (canonico, _, _) in grupos.items()}, faltan


def _tabla(resultado, ultima=None):
    """Las tres filas de cuentas y la de `marca`. `ultima` es (título, llave) de una
    columna más, para los pares que no se midieron."""
    c, t = resultado["cuentas"], resultado["total"]
    extra = f"{ultima[0]:>11}" if ultima else ""
    lineas = [f"{'':<26}{'pares':>6}{'sí':>5}{'no':>5}{'sí unidos':>11}{'no unidos':>11}" + extra]
    for nombre, x in ((NOMBRE["parecido"], c["parecido"]), (NOMBRE["azar"], c["azar"]),
                      ("los 200", t)):
        lineas.append(f"{nombre:<26}{x['pares']:>6}{x['si']:>5}{x['no']:>5}{x['tp']:>11}"
                      f"{x['fp']:>11}" + (f"{x[ultima[1]]:>11}" if ultima else ""))
    lineas.append(f"{'sólo difieren en marca':<26}{t['solo_marca']:>6}"
                  "   · no entran en la cobertura (ADR 004 §2); cero por construcción")
    return lineas


def _tasas(resultado, poblacion_de_la_cobertura):
    def cumple(k):
        return "se cumple" if resultado["cumple"][k] else "NO se cumple"
    return [
        f"COBERTURA · {NOMBRE['parecido']} · {_pct(resultado['cobertura'])}",
        (f"    población: {poblacion_de_la_cobertura} · meta ≥ "
         f"{100 * META['cobertura']:.0f} % · {cumple('cobertura')}"),
        f"PRECISIÓN · {NOMBRE['azar']} · {_pct(resultado['precision'])}",
        (f"    población: los pares de esa mitad que la reconciliación unió · meta ≥ "
         f"{100 * META['precision']:.0f} % · {cumple('precision')}"),
        f"precisión sobre los 200 · {_pct(resultado['precision_200'])}",
        (f"«no» que siguen separados · {NOMBRE['parecido']} "
         f"{_pct(resultado['no_separados']['parecido'])} · {NOMBRE['azar']} "
         f"{_pct(resultado['no_separados']['azar'])}"),
    ]


def _veredicto(resultado):
    return "SE CUMPLE" if all(resultado["cumple"].values()) else "NO SE CUMPLE"


def informe(pares, articulos, reglas, con, fuente, muestra=MUESTRA, hoy=None):
    """El texto de `h3-medicion.txt`. `articulos` son las filas de `dim_articulo`:
    (articulo_key, producto_c, presentacion_c, articulo_canonico_key)."""
    hoy = hoy or dt.date.today().isoformat()
    sin_clasificar = {s[2]: s for s in reglas.sin_clasificar}
    canonico = {(p, r): c for _, p, r, c in articulos}
    grupo, faltan = con_la_muestra(pares, articulos, reglas, con)
    todos, alcance = medir(pares, grupo), medir(pares, canonico)
    fuera = [p for p in pares if p.a not in canonico or p.b not in canonico]

    # ¿La estrella se cargó con estas reglas? Se reconcilia otra vez el catálogo, aquí,
    # y se comparan los grupos: si no son los mismos, la cifra 2 es de otras reglas.
    solo = reconciliacion.agrupar([(k, p, r, 0) for k, p, r, _ in articulos], reglas, con)
    cargados = particiones((k, c) for k, _, _, c in articulos)
    calculados = particiones((k, g[0]) for k, g in solo.items())
    distintos = sum(cargados[k] != calculados[k] for k in cargados)
    # Y que sumar los artículos de fuera no le cambie el grupo a ninguno del catálogo.
    con_fuera = particiones((k, grupo[(p, r)]) for k, p, r, _ in articulos)
    se_mueven = sum(calculados[k] != con_fuera[k] for k in calculados)

    lineas = [
        "H3 · LA RECONCILIACIÓN DE PRODUCTOS CONTRA LOS 200 PARES CALIFICADOS",
        "",
        f"medido el {hoy} · {fuente}",
        f"reglas: {Path(reglas.ruta).name} {reglas.version}",
        f"muestra: {Path(muestra).name} · sha256 {sha256_de(Path(muestra))[:16]}",
        (f"dim_articulo: {len(articulos):,} artículos · "
         f"{len({c for *_, c in articulos}):,} canónicos"),
        ("✓ la estrella cargada tiene los grupos que dan estas reglas"
         if distintos == 0 else
         f"✗ {distintos:,} artículos están en otro grupo que el que dan estas reglas: la "
         "estrella se cargó con otras. Vuelve a cargarla (estrella.py --cargar) y mide de "
         "nuevo; la cifra 2 de abajo es de las reglas con que se cargó"),
    ]
    if faltan:
        lineas += [
            (f"{len(faltan):,} artículos de la muestra no están en dim_articulo, y {len(fuera)} "
             "pares"),
            "tienen alguno: la muestra salió del corpus con el recorte de catálogos, sin el de",
            "entidades ni el de la ventana (h3-muestra-para-calificar.py), y la plataforma",
            "ingiere sólo el alcance del contrato. La cifra 1 los mide con la misma",
            "reconciliación; la 2 los deja fuera.",
        ]
    if se_mueven:
        lineas.append(f"✗ sumar esos artículos cambia de grupo a {se_mueven:,} del catálogo: "
                      "unen grupos que la plataforma deja separados")

    lineas += [
        "",
        "Cobertura en la mitad por parecido y precisión en la mitad al azar (ADR 004 §1).",
        "",
        "1 · SOBRE LOS 200 PARES · la cifra de H3 (ADR 004 §1, criterio de #206)",
        "Un par está UNIDO si la reconciliación, aplicada a los artículos de la muestra",
        "junto con el catálogo cargado, deja sus dos artículos en el mismo grupo.",
        "",
        *_tabla(todos),
        "",
        *_tasas(todos, "los «sí» de esa mitad"),
        "",
        f"H3 {_veredicto(todos)} sobre los 200 pares.",
        "",
        (f"2 · DENTRO DEL ALCANCE DE LA PLATAFORMA · los {len(pares) - len(fuera)} pares con "
         "sus dos artículos en dim_articulo"),
        "Un par está UNIDO si sus dos artículos tienen el mismo articulo_canonico_key en la",
        "estrella cargada. Es lo que ve el producto.",
        "",
        *_tabla(alcance, ("fuera", "sin_medir")),
        "",
        *_tasas(alcance, "los «sí» de esa mitad dentro del alcance"),
        "",
        f"DENTRO DEL ALCANCE: {_veredicto(alcance)}.",
        "",
        "LAS DOS SON DENTRO DE LA MUESTRA: la lista de palabras y el umbral se calibraron",
        "contra estos mismos 200 pares (ADR 004). Dicen que las reglas reproducen la",
        "calificación; no cuánto cubren fuera de ella. Las uniones del catálogo entero",
        "están al final, para revisarlas a mano.",
    ]

    sin_medir = {p.n for p in fuera}
    lineas += ["", "─" * 78, "LOS «SÍ», UNO POR UNO · con la cifra 1", ""]
    for p, res in todos["pares"]:
        if not p.si:
            continue
        marca = {"tp": "unido   ", "fn": "SEPARADO", "solo_marca": "marca   "}[res]
        lineas.append(f"{p.n:03d} {marca}  {p.producto_a} · {p.presentacion_a}  ||  "
                      f"{p.presentacion_b}" + ("  · fuera del alcance" if p.n in sin_medir else ""))
        if res in ("tp", "fn"):
            lineas.append("       " + reconciliacion.explicar(
                p.producto_a, p.presentacion_a, p.presentacion_b, reglas, con))
        if res == "fn" and f"{p.n:03d}" in sin_clasificar:
            lineas.append(f"       sin clasificar, a propósito: {sin_clasificar[f'{p.n:03d}'][3]}")

    unidos = sorted({p.n for r in (todos, alcance) for p, res in r["pares"] if res == "fp"})
    lineas += ["", "─" * 78, f"LOS «NO» UNIDOS · {len(unidos)} de {todos['total']['no']}", ""]
    for p in pares:
        if p.n in unidos:
            lineas.append(f"{p.n:03d} UNIDO  {p.producto_a} · {p.presentacion_a}  ||  "
                          f"{p.presentacion_b}")
            lineas.append("       " + reconciliacion.explicar(
                p.producto_a, p.presentacion_a, p.presentacion_b, reglas, con))
    if not unidos:
        lineas.append("ninguno")

    if faltan:
        numeros = [f"{p.n:03d}" for p in fuera]
        lineas += ["", "─" * 78,
                   f"FUERA DEL ALCANCE · {len(fuera)} pares, {len(faltan)} artículos", ""]
        lineas += ["pares: " + " ".join(numeros[i:i + 15]) for i in range(0, len(numeros), 15)]
        lineas += [""] + [f"  {producto} · {presentacion}" for producto, presentacion in faltan]

    por_canonico = {}
    for k, _, presentacion, c in articulos:
        por_canonico.setdefault(c, []).append((k, presentacion))
    nombre = {k: (producto, presentacion) for k, producto, presentacion, _ in articulos}
    grupos = sorted(((nombre[c], c, g) for c, g in por_canonico.items() if len(g) > 1))
    lineas += ["", "─" * 78,
               (f"TODAS LAS UNIONES DEL CATÁLOGO · {len(grupos):,} grupos, "
                f"{sum(len(g) - 1 for *_, g in grupos):,} variantes"),
               "Cada grupo con su canónico (=) y por qué se le une cada variante (+).",
               "Una palabra que no identifica en la muestra puede identificar en otra",
               "presentación del mismo producto: aquí es donde se ve.", ""]
    for (producto, presentacion), c, g in grupos:
        lineas.append(f"= {producto} · {presentacion}")
        for k, variante in sorted(g, key=lambda x: x[1]):
            if k != c:
                lineas.append(f"  + {variante}  ·  "
                              + reconciliacion.explicar(producto, presentacion, variante,
                                                        reglas, con))
    return "\n".join(lineas)


def leer_dim_articulo(con, contrato, simular=False):
    """Las filas de `dim_articulo` del destino, y de dónde salieron."""
    destino = intermedia.adjuntar_destino(con, contrato, simular)
    try:
        filas = con.execute(
            "SELECT articulo_key, producto_c, presentacion_c, articulo_canonico_key "
            f"FROM destino.{estrella.ESQUEMA}.dim_articulo ORDER BY articulo_key").fetchall()
    except duckdb.Error as e:
        raise RuntimeError(f"no se pudo leer {estrella.ESQUEMA}.dim_articulo en "
                           f"{destino['donde']}: ¿ya se cargó la estrella? "
                           f"(estrella.py --cargar). {e}") from None
    finally:
        con.execute("DETACH destino")
    return destino, filas


def main():
    preparar_salida()
    ap = argparse.ArgumentParser(description="H3 sobre los 200 pares calificados, contra la "
                                             "estrella cargada")
    ap.add_argument("--simular", action="store_true",
                    help="el DuckDB de la carpeta de corridas, no postgres-analytics")
    ap.add_argument("--escribir", action="store_true",
                    help=f"deja el informe en {INFORME.relative_to(RAIZ)}")
    a = ap.parse_args()

    contrato = leer_contrato()
    reglas = reconciliacion.leer_reglas(contrato)
    con = intermedia._con()
    destino, articulos = leer_dim_articulo(con, contrato, a.simular)
    texto = informe(leer_muestra(), articulos, reglas, con,
                    f"{destino['motor']} {destino['donde']} · esquema {estrella.ESQUEMA}")
    print(texto)
    if a.escribir:
        INFORME.write_text(texto + "\n", encoding="utf-8")
        print(f"\n✓ {INFORME.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
