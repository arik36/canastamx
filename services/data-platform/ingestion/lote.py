#!/usr/bin/env python3
"""CanastaMX · las comprobaciones que necesitan ver el LOTE COMPLETO.

`compuerta.py` revisa fila por fila: Pandera mira una fila y dice si cumple el
contrato. Hay reglas que con una fila no se pueden ni plantear:

  · **Colisión de precio alta** (contrato 1.3.3 · `clave_de_fila`). Dos filas con
    la misma clave y precios que difieren en más de $50: no se sabe cuál precio es
    el bueno. Para verlo hacen falta las dos filas, y la decisión es sobre el
    GRUPO, no sobre una fila.
  · **Frescura** (contrato · `frescura`). Son días desde el `fecha_registro` más
    reciente que se logró ingerir. Eso es un máximo sobre el lote entero.

Las dos se calculan **en DuckDB** y no en pandas, y no es preferencia: la
normalización canónica que el contrato manda usar para comparar claves está
escrita en el contrato como **expresión SQL de DuckDB**
(`normalizacion.canonica`). Reimplementarla en pandas sería escribir una
normalización PARECIDA, que es justo el error que el contrato documenta en esa
misma línea.

## Qué se lee del contrato y qué NO se escribe aquí

Igual que en `compuerta.py`: ninguna cifra del contrato vive en este archivo.

| Del contrato | Para qué |
|---|---|
| `normalizacion.canonica` | la expresión SQL con que se comparan las claves |
| `normalizacion.orden` | que reparar el `?` va ANTES de normalizar |
| `normalizacion.reparar_interrogantes.diccionario` | las 1,650 reparaciones |
| `clave_de_fila.columnas` | qué columnas forman el grupo |
| `clave_de_fila.colision_precio_alta.mas_de` | el umbral de la colisión alta |
| `clave_de_fila.colision_precio_alta.a_cuarentena` | si va el grupo o la fila |
| `frescura.avisa_dias` · `frescura.bloquea_dias` | los dos umbrales |
| `frescura.no_aplica_mientras` | por qué hoy la frescura no aplica |

## Lo que este archivo NO hace, y por qué

**No deduplica la captura doble.** El contrato dice qué hacer
(`clave_de_fila.desempate: min_precio`) pero el umbral que distingue una captura
doble de una observación múltiple —el $1— está sólo en un **comentario** de esa
línea, no como dato. Aplicarlo obligaría a escribir `1` en este código, que es
exactamente lo que el proyecto decidió no hacer. Así que no se aplica y se
reporta: `cifras_que_el_contrato_no_declara()`. Un comentario no es una
declaración, y ningún programa puede obedecerlo.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ingesta import CONTRATO, leer_contrato

NOMBRE_COMPUERTA = "lote_contra_el_contrato"

# Igual que en compuerta.py: el motivo apunta a la regla del contrato que lo
# produce. Si el contrato deja de declararla, la compuerta deja de poder emitirlo.
MOTIVOS_DE_GRUPO = {
    "colision_precio_alta": "clave_de_fila.colision_precio_alta",
}

# El umbral de la captura doble. Está en el contrato, pero en prosa.
CIFRAS_EN_PROSA = {
    "umbral_de_captura_doble": "clave_de_fila.desempate",
}


def _con():
    import duckdb

    return duckdb.connect(":memory:")


def expresion_canonica(contrato, columna):
    """La normalización canónica del contrato, con `col` sustituida por la columna.

    Se lee; no se escribe. El contrato guarda la expresión completa a propósito, y
    dice por qué: «una normalización PARECIDA no es la misma normalización».
    """
    plantilla = contrato["normalizacion"]["canonica"]
    # El contrato guarda la expresión y, debajo, la explicación de por qué está
    # completa. La expresión es lo que va hasta el primer renglón en blanco.
    expresion = plantilla.split("\n\n")[0].strip()
    # `col` como palabra completa: un reemplazo ingenuo también tocaría un `col`
    # dentro de otro identificador el día que la expresión crezca.
    nueva, n = re.subn(r"\bcol\b", f'"{columna}"', expresion)
    if n != 1:
        raise ValueError(
            f"`normalizacion.canonica` del contrato menciona `col` {n} veces; "
            "se esperaba exactamente una, para saber dónde va la columna"
        )
    return nueva


def reparaciones(contrato, columnas=None):
    """El diccionario del `?`, leído del archivo que el contrato declara.

    Devuelve {(columna, valor_roto): reparado}. Si el contrato declara el
    diccionario y el archivo no está, es un error del repositorio, no un detalle:
    sin él las claves se comparan rotas y los grupos salen mal.
    """
    rep = contrato["normalizacion"]["reparar_interrogantes"]
    ruta = CONTRATO.parent.parent / rep["diccionario"]
    if not ruta.exists():
        raise FileNotFoundError(
            f"el contrato declara el diccionario {rep['diccionario']} y no existe "
            f"en {ruta}"
        )
    permitidas = set(rep["aplica_a"])
    if columnas is not None:
        permitidas &= set(columnas)
    with ruta.open(encoding="utf-8") as f:
        return {
            (r["columna"], r["valor_roto"]): r["reparado"]
            for r in csv.DictReader(f)
            if r["columna"] in permitidas
        }


def cifras_que_el_contrato_no_declara(contrato=None):
    """Qué cifras usa esta compuerta que el contrato sólo tiene en prosa.

    Hermana de `compuerta.motivos_que_el_contrato_no_declara()`, y por la misma
    razón: se busca sobre el TEXTO del contrato, porque un comentario desaparece al
    interpretar el YAML. Hoy devuelve el umbral de la captura doble, cuyo `$1` vive
    en el comentario de `clave_de_fila.desempate`.
    """
    contrato = contrato or leer_contrato()
    faltan = []
    clave = contrato["clave_de_fila"]
    if clave.get("desempate") and "umbral_de_captura_doble" not in str(clave):
        faltan.append("umbral_de_captura_doble")
    return faltan


def _sql_de_la_clave(contrato, columnas_clave):
    """Las expresiones que forman la clave, reparadas y normalizadas, en ese orden.

    El orden lo manda el contrato (`normalizacion.orden`), y no es cosmético:
    normalizar primero borra el `?` del valor roto y el diccionario ya no lo
    encuentra.
    """
    orden = contrato["normalizacion"]["orden"]
    if orden != ["reparar_interrogantes", "canonica"]:
        raise ValueError(
            f"`normalizacion.orden` del contrato cambió a {orden}; esta compuerta "
            "sólo sabe reparar y luego normalizar"
        )
    partes = []
    for c in columnas_clave:
        # La reparación entra como COALESCE contra la tabla del diccionario, que se
        # une por (columna, valor tal como llegó).
        reparado = f'COALESCE(d_{c}.reparado, CAST(l."{c}" AS VARCHAR))'
        canonica = expresion_canonica(contrato, "__v__").replace(
            '"__v__"', f"({reparado})"
        )
        partes.append(f"{canonica} AS k_{c}")
    return partes


def revisar_grupos(df, contrato=None, compuerta=NOMBRE_COMPUERTA):
    """Devuelve (limpias, registros, resumen) para las reglas de GRUPO.

    Misma forma que `compuerta.revisar_lote()` a propósito: las dos listas de
    cuarentena se concatenan sin convertir nada, y el resumen de las dos entra al
    mismo `decidir_promocion()`.
    """
    import pandas as pd

    contrato = contrato or leer_contrato()
    clave = contrato["clave_de_fila"]
    columnas_clave = list(clave["columnas"])
    umbral = clave["colision_precio_alta"]["mas_de"]
    alcance = clave["colision_precio_alta"]["a_cuarentena"]
    if alcance != "grupo_completo":
        raise ValueError(
            f"`colision_precio_alta.a_cuarentena` dice «{alcance}»; esta compuerta "
            "sólo sabe mandar el grupo completo"
        )

    columnas = list(df.columns)
    if df.empty:
        return df, [], {"filas_entrada": 0, "grupos": 0, "grupos_en_colision": 0,
                        "filas_en_cuarentena": 0, "registros_de_cuarentena": 0,
                        "filas_salida": 0, "por_motivo": {}}

    dic = reparaciones(contrato, columnas_clave)
    filas_dic = [{"columna": k[0], "valor_roto": k[1], "reparado": v}
                 for k, v in dic.items()]
    tabla_dic = pd.DataFrame(filas_dic, columns=["columna", "valor_roto", "reparado"])

    con = _con()
    con.register("lote", df.reset_index(drop=True).assign(__i__=range(len(df))))
    con.register("diccionario", tabla_dic)

    uniones = "\n".join(
        f'LEFT JOIN diccionario d_{c} ON d_{c}.columna = \'{c}\' '
        f'AND d_{c}.valor_roto = CAST(l."{c}" AS VARCHAR)'
        for c in columnas_clave
    )
    claves = ",\n           ".join(_sql_de_la_clave(contrato, columnas_clave))
    ks = ", ".join(f"k_{c}" for c in columnas_clave)

    # TRY_CAST y no CAST: una fila con el precio ilegible ya la aparta
    # `compuerta.py` con motivo `tipo_invalido`. Aquí no se vuelve a juzgar: se
    # deja fuera del cálculo de la diferencia para no inventar una colisión.
    con.execute(f"""
        CREATE OR REPLACE TABLE con_clave AS
        SELECT l.__i__,
               TRY_CAST(l."precio" AS DECIMAL(12,2)) AS __precio__,
               {claves}
        FROM lote l
        {uniones}
    """)
    con.execute(f"""
        CREATE OR REPLACE TABLE grupos AS
        SELECT md5(concat_ws(chr(31), {ks})) AS grupo,
               count(*)                      AS filas,
               max(__precio__) - min(__precio__) AS diferencia
        FROM con_clave
        WHERE __precio__ IS NOT NULL
        GROUP BY {ks}
        HAVING count(*) > 1
    """)
    en_colision = con.execute(f"""
        SELECT c.__i__, g.grupo, g.diferencia, g.filas
        FROM con_clave c
        JOIN grupos g ON g.grupo = md5(concat_ws(chr(31), {ks}))
        WHERE g.diferencia > {umbral}
        ORDER BY c.__i__
    """).fetchall()
    totales = con.execute("""
        SELECT count(*), coalesce(sum(filas), 0)
        FROM grupos
    """).fetchone()

    from compuerta import huella

    registros, indices = [], []
    for i, grupo, diferencia, filas_del_grupo in en_colision:
        fila = {c: (None if pd.isna(df.iloc[i][c]) else df.iloc[i][c]) for c in columnas}
        fila = {c: (v.isoformat() if hasattr(v, "isoformat") else
                    (str(v) if v is not None else None)) for c, v in fila.items()}
        registros.append({
            "motivo": "colision_precio_alta",
            "nivel": "GRUPO",
            "compuerta": compuerta,
            "huella_fila": huella(fila, columnas),
            "grupo": grupo,
            "fila": fila,
            # La diferencia es la evidencia de por qué el grupo se apartó. Sin ella
            # quien revise la cuarentena tiene que recalcularla para creerla.
            "diferencia": float(diferencia),
            "filas_del_grupo": int(filas_del_grupo),
        })
        indices.append(i)

    limpias = df.drop(index=[df.index[i] for i in indices]) if indices else df
    resumen = {
        "filas_entrada": len(df),
        "grupos": int(totales[0]),
        "grupos_en_colision": len({r["grupo"] for r in registros}),
        "filas_en_cuarentena": len(indices),
        "registros_de_cuarentena": len(registros),
        "filas_salida": len(limpias),
        "umbral_de_colision": umbral,
        "por_motivo": {"colision_precio_alta": len(registros)} if registros else {},
        "cifras_en_prosa_no_aplicadas": cifras_que_el_contrato_no_declara(contrato),
    }
    return limpias, registros, resumen


def revisar_frescura(df, contrato=None, fecha_referencia=None, corpus_congelado=True):
    """Días desde el `fecha_registro` más reciente del lote, contra los dos umbrales.

    `fecha_referencia` es **parámetro de la corrida**, como declara el contrato, y
    no `TODAY()`. El contrato explica por qué: con datos hasta julio y la fecha de
    hoy, cualquier corrida daría «bloquea» y la compuerta nunca podría mostrar «ok»
    ni «avisa».

    `corpus_congelado` refleja `frescura.no_aplica_mientras`. Mientras sea verdad,
    el resultado se calcula igual pero se marca `aplica: False`: es la cifra que la
    consola necesita para escribir «no aplica: la fuente no publica desde julio»
    (`diseno.md` §7 · 3), en lugar de un semáforo rojo que no significa nada.
    """
    contrato = contrato or leer_contrato()
    f = contrato["frescura"]
    if f["fecha_referencia"] != "parametro_de_la_corrida":
        raise ValueError(
            f"`frescura.fecha_referencia` dice «{f['fecha_referencia']}»; esta "
            "compuerta sólo sabe recibirla como parámetro de la corrida"
        )

    # Un lote sin filas es un resultado posible, no un error: pasa cuando la
    # compuerta de fila aparta todo. La frescura simplemente no tiene de dónde
    # medirse, y eso se dice en lugar de reventar.
    if df.empty or "fecha_registro" not in df.columns:
        return {"aplica": False,
                "razon": "el lote no dejó ninguna fila con fecha que medir",
                "ultima_fecha": None, "dias": None, "estado": None}

    con = _con()
    con.register("lote", df)
    ultima = con.execute(
        'SELECT max(TRY_CAST("fecha_registro" AS DATE)) FROM lote'
    ).fetchone()[0]
    if ultima is None:
        return {"aplica": False, "razon": "el lote no trae ninguna fecha legible",
                "ultima_fecha": None, "dias": None, "estado": None}

    if fecha_referencia is None:
        fecha_referencia = dt.date.today()
    elif isinstance(fecha_referencia, str):
        fecha_referencia = dt.date.fromisoformat(fecha_referencia)

    dias = (fecha_referencia - ultima).days
    if dias >= f["bloquea_dias"]:
        estado = "BLOQUEA"
    elif dias >= f["avisa_dias"]:
        estado = "AVISA"
    else:
        estado = "OK"

    return {
        "aplica": not corpus_congelado,
        "razon": (f"no aplica: {f['no_aplica_mientras']} (ADR 010)"
                  if corpus_congelado else None),
        "mide": f["mide"],
        "ultima_fecha": ultima.isoformat(),
        "fecha_referencia": fecha_referencia.isoformat(),
        "dias": dias,
        "avisa_dias": f["avisa_dias"],
        "bloquea_dias": f["bloquea_dias"],
        "estado": estado,
    }


def main():
    import argparse

    import pandas as pd

    ap = argparse.ArgumentParser(
        description="Las comprobaciones de lote completo: colisión y frescura")
    ap.add_argument("archivo", nargs="?", help="el lote (.parquet o .csv)")
    ap.add_argument("--fecha-referencia", dest="fecha",
                    help="la fecha contra la que se mide la frescura "
                         "(AAAA-MM-DD). El contrato la pide como parámetro")
    ap.add_argument("--cifras-en-prosa", action="store_true",
                    help="qué cifras usa esta compuerta que el contrato sólo "
                         "tiene en comentarios, y por eso no se aplican")
    a = ap.parse_args()

    contrato = leer_contrato()

    if a.cifras_en_prosa:
        faltan = cifras_que_el_contrato_no_declara(contrato)
        print(f"contrato {contrato['version']} · cifras en prosa: "
              f"{len(faltan)} de {len(CIFRAS_EN_PROSA)}")
        for c in faltan:
            print(f"  ✗ {c:28} declarada en prosa en {CIFRAS_EN_PROSA[c]}")
        if faltan:
            print("\n  No se aplican. Aplicarlas obligaría a escribir la cifra en "
                  "el código,\n  que es lo que la compuerta existe para evitar.")
        return

    if not a.archivo:
        ap.error("falta el archivo del lote")

    ruta = Path(a.archivo).expanduser().resolve()
    df = (pd.read_parquet(ruta) if ruta.suffix.lower() == ".parquet"
          else pd.read_csv(ruta, dtype="string", keep_default_na=False, na_values=[""]))

    limpias, _registros, resumen = revisar_grupos(df, contrato)
    frescura = revisar_frescura(df, contrato, a.fecha)

    print(json.dumps({"colision": resumen, "frescura": frescura},
                     ensure_ascii=False, indent=2))
    print(f"\nfilas de salida: {len(limpias):,}")


if __name__ == "__main__":
    main()
