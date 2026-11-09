#!/usr/bin/env python3
"""CanastaMX · T048 · reparar el `?` o apartarlo, antes del 5% de D-07 (CU-03).

QUÉ HACE
--------
La fuente escribe `?` donde su codificación no pudo escribir una letra
(`Camar?n`). Este módulo decide, valor por valor, qué se hace con cada uno:

    1. está en el diccionario del contrato  → se repara con su gemelo único
    2. tiene varios gemelos y uno domina     → se repara con ése (regla por frecuencia)
    3. tiene varios gemelos y ninguno domina → cuarentena · `revision_humana`
    4. no tiene gemelo conocido              → cuarentena · `codificacion_irrecuperable`

y aparta las filas de 3 y 4 con su motivo. Es la regla
`normalizacion.reparar_interrogantes` del contrato y el CU-03, con sus alternos
2a, 2b y 2c.

POR QUÉ ANTES DEL 5% Y NO EN LA CAPA INTERMEDIA
-----------------------------------------------
Una fila que no se puede reparar va a cuarentena, y la cuarentena cuenta para el
umbral de D-07. Si se apartara después de decidir la promoción, un lote lleno de
texto irreparable pasaría por debajo del 5% y se promovería. Por eso
`lote_promovido` llama a `apartar_irreparables()` antes de las reglas de grupo, y
la capa intermedia (`intermedia.py`) sólo APLICA lo que aquí se decidió.

LA FRECUENCIA SE CUENTA EN EL CORPUS (D-03), Y EL CORPUS NO ESTÁ AQUÍ
--------------------------------------------------------------------
La regla por frecuencia compara cuántas filas tiene cada gemelo posible en el
corpus completo, la misma población del diccionario. El corpus no entra al
repositorio ni a la plataforma: la capa cruda guarda sólo el alcance. Por eso esas
filas viven en una tabla versionada, `ambiguo.candidatos` del contrato
(`contracts/mojibake-ambiguos.csv`), que sale del corpus con
`docs/datos/perfilado/mojibake-ambiguos.py`. La tabla trae los conteos y no la
decisión: el umbral se aplica aquí, leído del contrato, así que si el contrato
cambia el umbral cambia la decisión sin regenerar nada.

QUÉ SE LEE DEL CONTRATO, Y NADA DE ESTO SE ESCRIBE AQUÍ
-------------------------------------------------------
| Del contrato | Para qué |
|---|---|
| `reparar_interrogantes.aplica_a` | las once columnas donde se busca el `?` |
| `reparar_interrogantes.metodo` | qué es un gemelo (`es_gemelo()`) |
| `reparar_interrogantes.diccionario` | las 1,650 reparaciones de gemelo único |
| `ambiguo.candidatos` | los gemelos de cada ambiguo y sus filas en el corpus |
| `ambiguo.umbral` · `ambiguo.empate` | cuándo gana un gemelo y el motivo si no |
| `sin_gemelo.motivo` | el motivo de lo que no tiene gemelo |
| `motivos_de_fila` | que los dos motivos estén declarados, con su regla |

No importa Dagster: si la orquestación se va (fecha de salida del ADR 016), esto
sigue corriendo igual.

USO
---
    # la cifra de CU-03: filas con `?` que van a cuarentena en el alcance
    python services/data-platform/ingestion/reparacion.py --medir LOTES/*.parquet
    # y escribirla en el caso de uso, entre sus marcas
    python services/data-platform/ingestion/reparacion.py --medir LOTES/*.parquet \\
        --escribir docs/analisis/casos-uso/CU-03-reparar-texto-corrupto.md
"""

import csv
import datetime as dt
import numbers
import sys
from collections import namedtuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ingesta import CONTRATO, columnas_del_contrato, leer_contrato
from salida_segura import preparar_salida

NOMBRE_COMPUERTA = "reparar_interrogantes"

# El carácter que la fuente deja en lugar de la letra que no pudo escribir. No es
# una cifra ni una frontera del contrato: es el objeto de la regla.
INTERROGANTE = "?"

# Las dos rutas del contrato de las que salen los dos motivos que este módulo
# emite. `motivos_de_fila` tiene que nombrar cada motivo con esta misma regla.
REGLAS_DE_LOS_MOTIVOS = {
    "sin_gemelo": "normalizacion.reparar_interrogantes.sin_gemelo",
    "empate": "normalizacion.reparar_interrogantes.ambiguo.empate",
}

MARCA_INICIO, MARCA_FIN = "<!-- cifra-cu03:inicio -->", "<!-- cifra-cu03:fin -->"

Tablas = namedtuple("Tablas", "diccionario candidatos")
Decision = namedtuple("Decision", "reparado motivo via candidatos")


# ── La regla, leída del contrato ───────────────────────────────────────────

def regla(contrato):
    """La regla `reparar_interrogantes` del contrato, comprobada.

    Si el contrato cambia algo que este módulo no sabe hacer —otro método, otra
    población, otra acción para lo que no tiene gemelo—, se niega y dice qué
    cambió, en lugar de seguir con lo que creía.
    """
    rep = contrato["normalizacion"]["reparar_interrogantes"]
    amb, sin = rep.get("ambiguo") or {}, rep.get("sin_gemelo") or {}
    esperado = {
        "metodo": (rep.get("metodo"), "gemelo_unico_de_igual_longitud"),
        "ambiguo.regla": (amb.get("regla"), "por_frecuencia"),
        "ambiguo.poblacion": (amb.get("poblacion"), "corpus"),
        "sin_gemelo.accion": (sin.get("accion"), "cuarentena"),
    }
    for campo, (dice, sabe) in esperado.items():
        if dice != sabe:
            raise ValueError(
                f"`reparar_interrogantes.{campo}` dice «{dice}»; este módulo sólo "
                f"sabe aplicar «{sabe}»")
    umbral = amb.get("umbral")
    if not isinstance(umbral, numbers.Real) or isinstance(umbral, bool) or umbral <= 1:
        raise ValueError(
            f"`ambiguo.umbral` dice «{umbral}»: tiene que ser un número mayor que 1 "
            "para que un gemelo pueda dominar a otro")
    if not amb.get("candidatos"):
        raise ValueError(
            "el contrato no declara `reparar_interrogantes.ambiguo.candidatos`: sin "
            "las filas de cada gemelo en el corpus, la regla por frecuencia no se "
            "puede aplicar (D-03)")

    motivos = {"sin_gemelo": sin.get("motivo"), "empate": amb.get("empate")}
    declarados = contrato.get("motivos_de_fila") or {}
    for clave, motivo in motivos.items():
        if declarados.get(motivo) != REGLAS_DE_LOS_MOTIVOS[clave]:
            raise ValueError(
                f"el motivo «{motivo}» no está en `motivos_de_fila` con la regla "
                f"{REGLAS_DE_LOS_MOTIVOS[clave]}")
    return {
        "aplica_a": list(rep["aplica_a"]),
        "diccionario": rep["diccionario"],
        "candidatos": amb["candidatos"],
        "umbral": umbral,
        "motivo_empate": motivos["empate"],
        "motivo_sin_gemelo": motivos["sin_gemelo"],
    }


def es_gemelo(roto, sano):
    """`gemelo_unico_de_igual_longitud`, con la definición exacta del contrato 1.3.1:
    mide lo mismo y coincide en toda posición donde el roto no lleva `?`.

    Es la misma comparación que `docs/datos/perfilado/mojibake.py` hizo con una
    expresión regular al construir el diccionario: cada `?` se volvía `.`, que
    acepta cualquier carácter menos el salto de línea, y los candidatos salían de
    los valores sin `?`.
    """
    if len(roto) != len(sano) or INTERROGANTE in sano:
        return False
    return all(a == b or (a == INTERROGANTE and b != "\n") for a, b in zip(roto, sano))


# ── Las dos tablas ─────────────────────────────────────────────────────────

def _abrir(relativa, que):
    ruta = CONTRATO.parent.parent / relativa
    if not ruta.exists():
        # CU-03 · 2c: sin la tabla el lote no avanza. No se sigue con la mitad.
        raise FileNotFoundError(
            f"el contrato declara {que} en {relativa} y el archivo no existe "
            f"({ruta}). Sin él no se puede reparar el `?`, y el lote no avanza "
            "(CU-03 · 2c)")
    return ruta


def _leer_csv(ruta, columnas):
    with ruta.open(encoding="utf-8", newline="") as f:
        lector = csv.DictReader(f)
        faltan = [c for c in columnas if c not in (lector.fieldnames or [])]
        if faltan:
            raise ValueError(f"{ruta.name} no trae las columnas {', '.join(faltan)}")
        return list(lector)


def leer_tablas(contrato):
    """El diccionario y los candidatos de los ambiguos, comprobados al leerlos.

    Se comprueba lo que el contrato afirma de las dos tablas, porque una tabla
    que no cumple su propia definición repara mal sin dar error: cada entrada
    tiene `?`, su reparación es un gemelo según `es_gemelo()`, la columna es de
    `aplica_a`, ninguna llave se repite, cada ambiguo tiene al menos dos gemelos y
    ningún valor está en las dos tablas.
    """
    r = regla(contrato)
    aplica = set(r["aplica_a"])

    diccionario = {}
    ruta = _abrir(r["diccionario"], "el diccionario del `?`")
    for n, fila in enumerate(_leer_csv(ruta, ("columna", "valor_roto", "reparado")), 2):
        llave = (fila["columna"], fila["valor_roto"])
        _comprobar_entrada(ruta, n, llave, fila["reparado"], aplica)
        if llave in diccionario:
            raise ValueError(f"{ruta.name}, renglón {n}: {llave} está repetido")
        diccionario[llave] = fila["reparado"]

    candidatos = {}
    ruta = _abrir(r["candidatos"], "los candidatos de los ambiguos")
    vistos = set()
    for n, fila in enumerate(_leer_csv(ruta, ("columna", "valor_roto", "candidato", "filas")), 2):
        llave = (fila["columna"], fila["valor_roto"])
        _comprobar_entrada(ruta, n, llave, fila["candidato"], aplica)
        try:
            filas = int(fila["filas"])
        except ValueError:
            filas = 0
        if filas <= 0:
            raise ValueError(f"{ruta.name}, renglón {n}: `filas` tiene que ser un entero "
                             f"positivo y dice {fila['filas']!r}")
        if (*llave, fila["candidato"]) in vistos:
            raise ValueError(f"{ruta.name}, renglón {n}: el candidato está repetido")
        if llave in diccionario:
            raise ValueError(f"{ruta.name}, renglón {n}: {llave} también está en el "
                             "diccionario; un valor es de gemelo único o es ambiguo")
        vistos.add((*llave, fila["candidato"]))
        candidatos.setdefault(llave, []).append((fila["candidato"], filas))

    solos = [llave for llave, c in candidatos.items() if len(c) < 2]
    if solos:
        raise ValueError(f"{ruta.name}: {len(solos)} valores con un solo candidato, "
                         f"como {solos[0]}; ésos van al diccionario, no aquí")
    return Tablas(diccionario, candidatos)


def _comprobar_entrada(ruta, n, llave, reparado, aplica):
    columna, roto = llave
    if columna not in aplica:
        raise ValueError(f"{ruta.name}, renglón {n}: la columna «{columna}» no es de "
                         "`reparar_interrogantes.aplica_a`")
    if INTERROGANTE not in roto:
        raise ValueError(f"{ruta.name}, renglón {n}: «{roto}» no trae `?`")
    if not es_gemelo(roto, reparado):
        raise ValueError(f"{ruta.name}, renglón {n}: «{reparado}» no es gemelo de "
                         f"«{roto}» (misma longitud y misma letra donde no hay `?`)")


# ── La decisión, valor por valor ───────────────────────────────────────────

def decisiones(contrato, tablas=None):
    """{(columna, valor_roto): Decision} para cada valor de las dos tablas.

    Un valor que no está en ninguna no tiene gemelo conocido en el corpus y no se
    decide aquí: `decidir()` le da el motivo de `sin_gemelo`.
    """
    r = regla(contrato)
    tablas = tablas or leer_tablas(contrato)
    salida = {llave: Decision(reparado, None, "diccionario", [(reparado, None)])
              for llave, reparado in tablas.diccionario.items()}
    for llave, cands in tablas.candidatos.items():
        # Más filas primero; a igual número, por el texto, para que el orden no
        # dependa del archivo. El orden sólo decide qué se muestra como evidencia:
        # si los dos primeros empatan, ninguno domina.
        orden = sorted(cands, key=lambda c: (-c[1], c[0]))
        (primero, filas_1), (_, filas_2) = orden[0], orden[1]
        if filas_1 >= r["umbral"] * filas_2:
            salida[llave] = Decision(primero, None, "frecuencia", orden)
        else:
            salida[llave] = Decision(None, r["motivo_empate"], "empate", orden)
    return salida


def decidir(decs, r, llave):
    """La decisión para un valor roto, aunque no esté en ninguna tabla. `r` es lo
    que devuelve `regla()`."""
    d = decs.get(llave)
    if d is not None:
        return d
    return Decision(None, r["motivo_sin_gemelo"], "sin_gemelo", [])


def reparaciones_del_contrato(contrato, columnas=None):
    """{(columna, valor_roto): reparado}: el diccionario y los ambiguos que la
    frecuencia resuelve. Es lo que la clave de fila compara (`lote.py`) y lo que
    la capa intermedia escribe (`intermedia.py`): las dos con el mismo mapa."""
    permitidas = set(regla(contrato)["aplica_a"])
    if columnas is not None:
        permitidas &= set(columnas)
    return {llave: d.reparado for llave, d in decisiones(contrato).items()
            if d.reparado is not None and llave[0] in permitidas}


# ── La compuerta ───────────────────────────────────────────────────────────

def _texto(v):
    """El valor como lo escribe la cuarentena: igual que `compuerta.revisar_lote()`."""
    import pandas as pd

    if v is None or (not isinstance(v, str) and pd.isna(v)):
        return None
    return v.isoformat() if hasattr(v, "isoformat") else str(v)


def apartar_irreparables(df, contrato=None, compuerta=NOMBRE_COMPUERTA):
    """Devuelve (filas, registros, resumen).

    `filas` son las del lote **tal como llegaron**, menos las que no se pueden
    reparar: la reparación se aplica en la capa intermedia, y la cuarentena guarda
    la fila como llegó. `registros` trae uno por (fila, motivo), con la misma forma
    que `compuerta.revisar_lote()` y `lote.revisar_grupos()`, más los valores que lo
    causaron. `resumen` cuenta por columna y por motivo.

    Una fila con dos `?` irreparables en dos columnas lleva un registro por motivo,
    no uno por columna: la tabla `cuarentena` es única por (corrida, huella, motivo).
    """
    from compuerta import huella

    contrato = contrato or leer_contrato()
    r = regla(contrato)
    columnas = columnas_del_contrato(contrato)
    decs = decisiones(contrato)

    motivos_por_fila, valores_por_fila, por_columna = {}, {}, {}
    via = {"diccionario": 0, "frecuencia": 0}
    for c in r["aplica_a"]:
        if c not in df.columns:
            continue
        texto = df[c].astype("string")
        con_q = texto.str.contains(INTERROGANTE, regex=False).fillna(False).to_numpy()
        cuenta = {"ocurrencias": int(con_q.sum()), "reparables": 0, "a_cuarentena": 0}
        for posicion in con_q.nonzero()[0]:
            valor = texto.iat[posicion]
            d = decidir(decs, r, (c, valor))
            if d.reparado is not None:
                cuenta["reparables"] += 1
                via[d.via] += 1
                continue
            cuenta["a_cuarentena"] += 1
            motivos_por_fila.setdefault(posicion, set()).add(d.motivo)
            valores_por_fila.setdefault(posicion, []).append({
                "columna": c, "valor": valor, "motivo": d.motivo,
                "candidatos": [{"candidato": k, "filas": n} for k, n in d.candidatos]})
        por_columna[c] = cuenta

    registros = []
    for posicion in sorted(motivos_por_fila):
        fila = {c: _texto(df.iloc[posicion][c]) for c in columnas}
        h = huella(fila, columnas)
        for motivo in sorted(motivos_por_fila[posicion]):
            registros.append({
                "motivo": motivo, "nivel": "FILA", "compuerta": compuerta,
                "huella_fila": h, "grupo": None, "fila": fila,
                # La evidencia de por qué: qué valor, en qué columna, y con qué
                # gemelos se comparó. Sin esto, quien revise la cuarentena tiene
                # que volver a buscarlos para creerla.
                "valores": [v for v in valores_por_fila[posicion] if v["motivo"] == motivo],
            })

    fuera = [df.index[p] for p in motivos_por_fila]
    filas = df.drop(index=fuera) if fuera else df
    resumen = {
        "filas_entrada": len(df),
        "filas_en_cuarentena": len(motivos_por_fila),     # FILAS distintas
        "registros_de_cuarentena": len(registros),
        "filas_salida": len(filas),
        "por_motivo": {m: sum(1 for x in registros if x["motivo"] == m)
                       for m in sorted({x["motivo"] for x in registros})},
        "por_columna": por_columna,
        "valores_reparados": {"por_diccionario": via["diccionario"],
                              "por_frecuencia": via["frecuencia"]},
        "umbral": r["umbral"],
    }
    return filas, registros, resumen


# ── La cifra de CU-03 ──────────────────────────────────────────────────────

def medir(rutas, contrato=None):
    """Las filas con `?` del alcance que van a cuarentena, lote por lote.

    Sobre el alcance completo (las 2,658,906 filas de `medicion.filas` cuando son
    los 38 lotes), con la misma lectura que la ingesta y la compuerta
    (`compuerta.leer_alcance()`), y con esta misma función: la cifra que va a
    CU-03 es la que la plataforma aplica, no una estimación aparte.
    """
    from compuerta import leer_alcance

    contrato = contrato or leer_contrato()
    aplica = regla(contrato)["aplica_a"]
    filas, total = [], {"alcance": 0, "con_interrogante": 0, "a_cuarentena": 0,
                        "por_motivo": {}}
    for ruta in sorted(Path(p) for p in rutas):
        df = leer_alcance(ruta, contrato)
        _, _, res = apartar_irreparables(df, contrato)
        con_q = 0
        if len(df):
            mascara = None
            for c in aplica:
                m = df[c].astype("string").str.contains(INTERROGANTE, regex=False).fillna(False)
                mascara = m if mascara is None else (mascara | m)
            con_q = int(mascara.sum())
        filas.append({"lote": ruta.stem, "alcance": len(df), "con_interrogante": con_q,
                      "a_cuarentena": res["filas_en_cuarentena"],
                      "por_motivo": res["por_motivo"]})
        total["alcance"] += len(df)
        total["con_interrogante"] += con_q
        total["a_cuarentena"] += res["filas_en_cuarentena"]
        for m, n in res["por_motivo"].items():
            total["por_motivo"][m] = total["por_motivo"].get(m, 0) + n
    return filas, total


def bloque_para_cu03(filas, total, contrato):
    esperado = contrato["medicion"]["filas"]
    hoy = dt.datetime.now(dt.UTC).date().isoformat()
    motivos = ", ".join(f"`{m}` {n:,}" for m, n in sorted(total["por_motivo"].items())) or "ninguno"
    return (f"{MARCA_INICIO}\n"
            f"> Medido el {hoy} con `services/data-platform/ingestion/reparacion.py "
            f"--medir`, contrato {contrato['version']}, sobre {len(filas)} lotes y "
            f"{total['alcance']:,} filas del alcance (el contrato dice {esperado:,}). "
            "No se escribe a mano: si algo cambia, se vuelve a correr.\n\n"
            f"- Filas del alcance con `?` en alguna de las once columnas: "
            f"**{total['con_interrogante']:,}**.\n"
            f"- Filas que van a cuarentena por el `?`: **{total['a_cuarentena']:,}** "
            f"({100 * total['a_cuarentena'] / max(total['alcance'], 1):.4f}% del "
            f"alcance). Registros por motivo: {motivos}.\n"
            f"{MARCA_FIN}")


def main():
    preparar_salida()
    import argparse

    ap = argparse.ArgumentParser(description="El `?` de CU-03: cuánto se repara y "
                                             "cuánto va a cuarentena, sobre el alcance")
    ap.add_argument("--medir", nargs="+", metavar="LOTE",
                    help="los archivos de los lotes (.parquet o .csv)")
    ap.add_argument("--escribir", help="el documento donde dejar la cifra, entre "
                                       f"las marcas {MARCA_INICIO} y {MARCA_FIN}")
    a = ap.parse_args()
    if not a.medir:
        ap.error("falta --medir con los archivos de los lotes")

    contrato = leer_contrato()
    filas, total = medir(a.medir, contrato)
    print(f"contrato {contrato['version']} · {len(filas)} lotes · población: ALCANCE\n")
    print(f"  {'lote':<14}{'alcance':>12}{'con ?':>10}{'a cuarentena':>14}   por motivo")
    for f in filas:
        print(f"  {f['lote']:<14}{f['alcance']:>12,}{f['con_interrogante']:>10,}"
              f"{f['a_cuarentena']:>14,}   {f['por_motivo'] or ''}")
    print(f"  {'total':<14}{total['alcance']:>12,}{total['con_interrogante']:>10,}"
          f"{total['a_cuarentena']:>14,}   {total['por_motivo']}")
    if a.escribir:
        doc = Path(a.escribir)
        texto = doc.read_text(encoding="utf-8")
        if texto.count(MARCA_INICIO) != 1 or texto.count(MARCA_FIN) != 1:
            print(f"✗ {doc} no trae una sola vez las marcas {MARCA_INICIO} y {MARCA_FIN}",
                  file=sys.stderr)
            return 1
        ini, fin = texto.index(MARCA_INICIO), texto.index(MARCA_FIN) + len(MARCA_FIN)
        doc.write_text(texto[:ini] + bloque_para_cu03(filas, total, contrato) + texto[fin:],
                       encoding="utf-8")
        print(f"\n✓ cifra escrita en {doc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
