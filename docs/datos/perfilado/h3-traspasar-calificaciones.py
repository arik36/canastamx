"""
H3 · traspasa las calificaciones hechas a mano al archivo regenerado

Para qué
--------
El guión `h3-muestra-para-calificar.py` construía los candidatos con una clave
que incluía `marca`, y el ADR 002 §1-2 dice que el artículo es
`producto` + `presentacion` y que **`marca` no identifica**. Corregido el
guión, la muestra hay que regenerarla — y sin esto se perderían las
calificaciones que ya se hicieron a mano.

Este guión las rescata. Empareja por la **clave de artículo** (los dos primeros
segmentos de la clave vieja, que son producto y presentación), así que:

  · un par viejo que sólo difería en `marca` no aparece en el archivo nuevo
    —por el ADR 002 es UN artículo— y su calificación se descarta, con aviso;
  · un par viejo que difería en presentación Y marca sí aparece, porque su
    diferencia de presentación sobrevive, y su calificación se traspasa;
  · si dos pares viejos caen sobre el mismo par nuevo y se calificaron
    distinto, se deja en blanco y se reporta: es una contradicción que tiene
    que resolver quien califica, no el guión.

Uso
---
    python docs/datos/perfilado/h3-traspasar-calificaciones.py \
        --viejo  docs/datos/perfilado/h3-muestra-para-calificar.ANTERIOR.txt \
        --nuevo  docs/datos/perfilado/h3-muestra-para-calificar.txt

Reescribe el archivo NUEVO en su lugar, con las casillas ya marcadas y una
marca `←  traspasado del archivo anterior` en cada par rescatado.
"""
import argparse
import re
from collections import defaultdict
from pathlib import Path

BLOQUE = re.compile(r"(?=^par \d{3} )", re.M)
CLAVES = re.compile(r"^      A: (.*)\n      B: (.*)$", re.M)
CASILLA = re.compile(r"(¿son el MISMO artículo\?\s+)\[\s*([xX]?)\s*\] sí\s+\[\s*([xX]?)\s*\] no")


def clave_de_articulo(linea):
    """Los dos primeros segmentos: producto y presentación. El tercero, si
    existe, es `marca` — y por el ADR 002 no forma parte de la identidad."""
    partes = linea.split(" · ")
    return tuple(partes[:2])


def leer(texto):
    """[(par_de_claves_de_articulo, respuesta|None, bloque_crudo)]"""
    fuera = []
    for b in BLOQUE.split(texto)[1:]:
        c = CLAVES.search(b)
        if not c:
            continue
        a, z = clave_de_articulo(c.group(1)), clave_de_articulo(c.group(2))
        m = CASILLA.search(b)
        resp = None
        if m:
            resp = "si" if m.group(2) else ("no" if m.group(3) else None)
        fuera.append((frozenset({a, z}), resp, b))
    return fuera


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--viejo", required=True, type=Path)
    ap.add_argument("--nuevo", required=True, type=Path)
    a = ap.parse_args()

    viejos = leer(a.viejo.read_text(encoding="utf-8"))
    texto_nuevo = a.nuevo.read_text(encoding="utf-8")
    nuevos = leer(texto_nuevo)

    # Respuestas del archivo viejo, agrupadas por par de artículos.
    por_par = defaultdict(set)
    degenerados = 0
    for k, resp, _ in viejos:
        if len(k) < 2:            # A y B son el MISMO artículo: sólo cambiaba la marca
            if resp:
                degenerados += 1
            continue
        if resp:
            por_par[k].add(resp)

    traspasados = conflictos = sin_dato = 0
    partes = BLOQUE.split(texto_nuevo)
    salida = [partes[0]]
    for b in partes[1:]:
        c = CLAVES.search(b)
        if c:
            k = frozenset({clave_de_articulo(c.group(1)), clave_de_articulo(c.group(2))})
            respuestas = por_par.get(k, set())
            if len(respuestas) == 1:
                r = next(iter(respuestas))
                marca_si, marca_no = ("x", " ") if r == "si" else (" ", "x")
                b = CASILLA.sub(
                    lambda m: f"{m.group(1)}[{marca_si}] sí   [{marca_no}] no"
                              "     ←  traspasado del archivo anterior", b, count=1)
                traspasados += 1
            elif len(respuestas) > 1:
                b = CASILLA.sub(
                    lambda m: f"{m.group(1)}[ ] sí   [ ] no"
                              "     ←  ¡CONTRADICCIÓN! antes se calificó de las dos"
                              " maneras, decídelo de nuevo", b, count=1)
                conflictos += 1
            else:
                sin_dato += 1
        salida.append(b)

    a.nuevo.write_text("".join(salida), encoding="utf-8")

    print(f"pares en el archivo nuevo      : {len(nuevos)}")
    print(f"  traspasados                  : {traspasados}")
    print(f"  con contradicción, en blanco : {conflictos}")
    print(f"  sin calificación previa      : {sin_dato}")
    print(f"\ncalificaciones descartadas       : {degenerados}")
    print("  eran pares que sólo diferían en `marca`. Por el ADR 002 §1-2 son UN")
    print("  artículo, no un par, y no vuelven a aparecer.")


if __name__ == "__main__":
    main()