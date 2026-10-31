#!/usr/bin/env python3
"""CanastaMX · las comprobaciones que necesitan ver el LOTE COMPLETO.

`compuerta.py` revisa fila por fila: Pandera mira una fila y dice si cumple el
contrato. Hay reglas que con una fila no se pueden ni plantear:

  · **La clave de fila** (contrato · `clave_de_fila`). Filas con la misma clave
    forman un grupo, y la diferencia entre el precio mayor y el menor del grupo
    lo pone en uno de tres cubos: captura doble, observaciones múltiples o
    colisión alta. Sólo la colisión alta aparta filas, y aparta el GRUPO
    completo: con más de $50 de diferencia no se sabe cuál precio es el bueno.
  · **Frescura** (contrato · `frescura`). Son días desde el `fecha_registro` más
    reciente que se logró ingerir. Eso es un máximo sobre el lote entero.

Las dos se calculan **en DuckDB** y no en pandas, y no es preferencia: las dos
normalizaciones con que el contrato manda comparar la clave están escritas en el
contrato como **expresiones SQL de DuckDB** (`normalizacion.canonica` y
`normalizacion.mayusculas_sin_acentos`). Reimplementarlas en pandas sería
escribir una normalización PARECIDA, que es justo el error que el contrato
documenta en el párrafo de `canonica`.

## Qué se lee del contrato y qué NO se escribe aquí

Igual que en `compuerta.py`: ninguna cifra del contrato vive en este archivo.

| Del contrato | Para qué |
|---|---|
| `normalizacion.canonica` · `.mayusculas_sin_acentos` | las expresiones SQL |
| `normalizacion.orden` | que reparar el `?` va ANTES de normalizar |
| `normalizacion.reparar_interrogantes` | las 1,650 del diccionario y los ambiguos que resuelve la frecuencia, por `reparacion.py` |
| `columnas.precio.se_compara_como` | el tipo en que se resta el precio |
| `clave_de_fila.columnas` | qué columnas forman el grupo |
| `clave_de_fila.normaliza_por_columna` | con qué expresión se compara cada una |
| `clave_de_fila.captura_doble.menos_de` | la frontera de la captura doble ($1) |
| `clave_de_fila.colision_precio_alta.mas_de` | la frontera de la colisión alta ($50) |
| `clave_de_fila.colision_precio_alta.a_cuarentena` | si va el grupo o la fila |
| `frescura.avisa_dias` · `frescura.bloquea_dias` | los dos umbrales |
| `frescura.no_aplica_mientras` | por qué hoy la frescura no aplica |

## Lo que este archivo NO hace, y por qué

**No deduplica la captura doble: la cuenta.** Deduplicar es transformar, y eso lo
hace la capa intermedia (`intermedia.py`, T048). Aquí se cuentan los tres cubos
—grupos y filas sobrantes de cada uno— para que la deduplicación se compruebe
contra estas cifras, y para volver a medir lo que el contrato 1.3.3 pidió medir en
la primera corrida de la compuerta. Las dos usan la misma consulta para la clave
(`sql_con_clave()`): si cada una armara la suya, la cuenta dejaría de cuadrar en
cuanto una cambiara.

## Dos errores de la versión anterior, corregidos el 15 de octubre de 2026

1. **La marca se comparaba en forma canónica.** El contrato dice, desde 1.3.3, que
   la marca se compara en mayúsculas sin acentos (`normalizacion.marca.a`, ADR
   002 · 3) y las otras cuatro columnas en forma canónica. La canónica quita la
   puntuación y une `Kellogg's` con `Kellogg´s`; la de la marca no. Esta
   compuerta aplicaba la canónica a las cinco. La 1.3.5 lo deja como dato en
   `clave_de_fila.normaliza_por_columna` y aquí se lee.
2. **La cuarentena de colisión salía con nivel `GRUPO`.** La tabla `cuarentena`
   del esquema de operación sólo acepta `FILA` —su `CHECK (nivel = 'FILA')` y su
   llave foránea al catálogo lo exigen—, y el grupo va en la columna `grupo`.
   Cargar esta cuarentena habría fallado fila por fila el día que la base exista.
"""

import datetime as dt
import json
import numbers
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ingesta import leer_contrato
from salida_segura import preparar_salida

NOMBRE_COMPUERTA = "lote_contra_el_contrato"

# Igual que en compuerta.py: el motivo apunta a la regla del contrato que lo
# produce, y tiene que estar en `motivos_de_fila`. Se DECIDE sobre el grupo, pero
# se REGISTRA por fila, con nivel FILA y el grupo anotado: así lo pide la tabla
# `cuarentena` del esquema de operación.
MOTIVOS_DE_GRUPO = {
    "colision_precio_alta": "clave_de_fila.colision_precio_alta",
}

# Las cifras que esta compuerta necesita del contrato COMO DATO. Hasta 1.3.4 el
# umbral de la captura doble vivía en un comentario y no se podía obedecer.
CIFRAS_DEL_CONTRATO = {
    "umbral_de_captura_doble": "clave_de_fila.captura_doble.menos_de",
}

# Las normalizaciones que la clave de fila puede pedir. Cada nombre es una
# expresión que el contrato declara en `normalizacion`; `ninguna` compara el valor
# tal como llegó, que es lo que se hace con una fecha.
NORMALIZACIONES = ("canonica", "mayusculas_sin_acentos", "ninguna")


def _con():
    import duckdb

    return duckdb.connect(":memory:")


def _nodo(contrato, ruta):
    """El valor en una ruta del contrato como `a.b.c`, o None si no está."""
    nodo = contrato
    for paso in ruta.split("."):
        if not isinstance(nodo, dict) or paso not in nodo:
            return None
        nodo = nodo[paso]
    return nodo


def expresion(contrato, nombre, columna):
    """Una normalización del contrato, con `col` sustituida por la columna.

    Se lee; no se escribe. El contrato guarda `canonica` con su explicación
    debajo, así que la expresión es lo que va hasta el primer renglón en blanco;
    `mayusculas_sin_acentos` es un solo renglón.
    """
    plantilla = contrato["normalizacion"].get(nombre)
    if plantilla is None:
        raise ValueError(
            f"el contrato no declara la expresión de `normalizacion.{nombre}`")
    if not isinstance(plantilla, str):
        # `normalizacion.marca` es un diccionario ({a: …}), no una expresión: pedir
        # su expresión es un error de quien llama, y se dice así.
        raise TypeError(
            f"`normalizacion.{nombre}` del contrato no es una expresión SQL: "
            f"es {type(plantilla).__name__}")
    sql = plantilla.split("\n\n")[0].strip()
    # `col` como palabra completa: un reemplazo ingenuo también tocaría un `col`
    # dentro de otro identificador el día que la expresión crezca.
    nueva, n = re.subn(r"\bcol\b", f'"{columna}"', sql)
    if n != 1:
        raise ValueError(
            f"`normalizacion.{nombre}` del contrato menciona `col` {n} veces; "
            "se esperaba exactamente una, para saber dónde va la columna"
        )
    return nueva


def expresion_canonica(contrato, columna):
    """La normalización canónica. Se queda por compatibilidad: es `expresion()`."""
    return expresion(contrato, "canonica", columna)


def reparaciones(contrato, columnas=None):
    """Las reparaciones del `?` con que se compara la clave: {(columna, valor_roto):
    reparado}.

    Son las del diccionario **y** las de los ambiguos que la regla por frecuencia
    resuelve, porque `clave_de_fila.compara` dice `repara_interrogantes`, que es
    la regla entera y no sólo su diccionario. Hasta T048 aquí se leía sólo el
    diccionario, y un `Kellogg?s` que la frecuencia repara seguía partiendo su
    grupo. La regla vive en `reparacion.py`, que es quien también aparta lo
    irreparable: así las dos leen lo mismo.

    Si el contrato declara una tabla y el archivo no está, es un error del
    repositorio, no un detalle: sin ella las claves se comparan rotas.
    """
    from reparacion import reparaciones_del_contrato

    return reparaciones_del_contrato(contrato, columnas)


def precio_como_se_compara(contrato):
    """El tipo en que se resta el precio: `columnas.precio.se_compara_como`.

    En flotante, una diferencia de $1.00 sale 0.99999 y cae en el cubo
    equivocado (`razon_del_casteo`). Hasta T048 el `DECIMAL(12,2)` estaba escrito
    en la consulta; ahora se lee, y se acepta sólo con forma `DECIMAL(p,s)`.
    """
    tipo = str(contrato["columnas"]["precio"].get("se_compara_como") or "")
    encontrado = re.fullmatch(r"\s*DECIMAL\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)\s*", tipo,
                              re.IGNORECASE)
    if not encontrado:
        raise ValueError(
            f"`columnas.precio.se_compara_como` dice «{tipo}»; se esperaba "
            "DECIMAL(p,s)")
    return f"DECIMAL({encontrado.group(1)},{encontrado.group(2)})"


def cifras_que_el_contrato_no_declara(contrato=None):
    """Qué cifras de `CIFRAS_DEL_CONTRATO` no están en el contrato como número.

    Hermana de `compuerta.motivos_que_el_contrato_no_declara()`. Hasta 1.3.4 se
    buscaba sobre el texto y devolvía el umbral de la captura doble, cuyo `$1`
    estaba en un comentario. Desde 1.3.5 se busca sobre el DATO, que es lo único
    que un programa puede obedecer: un comentario ya no cuenta.
    """
    contrato = contrato or leer_contrato()
    return [nombre for nombre, ruta in CIFRAS_DEL_CONTRATO.items()
            if not isinstance(_nodo(contrato, ruta), numbers.Real)
            or isinstance(_nodo(contrato, ruta), bool)]


def _normalizacion_de(contrato, columna):
    """Con qué se compara una columna de la clave: lo dice el contrato, columna por
    columna. Si una columna de la clave no lo dice, la compuerta se niega: adivinar
    es como se coló la canónica en la marca."""
    por_columna = contrato["clave_de_fila"].get("normaliza_por_columna") or {}
    nombre = por_columna.get(columna)
    if nombre not in NORMALIZACIONES:
        raise ValueError(
            f"`clave_de_fila.normaliza_por_columna.{columna}` dice «{nombre}»; "
            f"tiene que ser una de {', '.join(NORMALIZACIONES)}"
        )
    return nombre


def _sql_de_la_clave(contrato, columnas_clave):
    """Las expresiones que forman la clave: reparadas y normalizadas, en ese orden,
    cada columna con la normalización que el contrato le asigna.

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
        nombre = _normalizacion_de(contrato, c)
        if nombre == "ninguna":
            partes.append(f"{reparado} AS k_{c}")
            continue
        sql = expresion(contrato, nombre, "__v__").replace(
            '"__v__"', f"({reparado})")
        partes.append(f"{sql} AS k_{c}")
    return partes


def sql_con_clave(contrato, origen="lote", reparaciones_tabla="diccionario"):
    """La consulta que da, por cada fila de `origen`, su `__i__`, su precio como lo
    compara el contrato (`__precio__`) y las columnas `k_` de la clave de fila.

    `origen` es una tabla con la columna `__i__`; `reparaciones_tabla`, una con
    (columna, valor_roto, reparado). La usan esta compuerta, para contar los cubos,
    y `intermedia.py`, para deduplicar: con dos consultas parecidas, una fila
    podría caer en un grupo aquí y en otro allá, y la cuenta de las sobrantes
    dejaría de cuadrar con lo que la capa intermedia quita.
    """
    columnas_clave = list(contrato["clave_de_fila"]["columnas"])
    uniones = "\n".join(
        f'LEFT JOIN {reparaciones_tabla} d_{c} ON d_{c}.columna = \'{c}\' '
        f'AND d_{c}.valor_roto = CAST(l."{c}" AS VARCHAR)'
        for c in columnas_clave
    )
    claves = ",\n           ".join(_sql_de_la_clave(contrato, columnas_clave))
    # TRY_CAST y no CAST: una fila con el precio ilegible ya la aparta
    # `compuerta.py` con motivo `tipo_invalido`. Aquí no se vuelve a juzgar: se
    # deja fuera del cálculo de la diferencia para no inventar una colisión.
    return f"""
        SELECT l.__i__,
               TRY_CAST(l."precio" AS {precio_como_se_compara(contrato)}) AS __precio__,
               {claves}
        FROM {origen} l
        {uniones}
    """


def _resumen_vacio():
    return {"filas_entrada": 0, "grupos": 0,
            "grupos_captura_doble": 0, "sobrantes_captura_doble": 0,
            "grupos_observaciones_multiples": 0,
            "sobrantes_observaciones_multiples": 0,
            "grupos_en_colision": 0, "sobrantes_en_colision": 0,
            "filas_en_cuarentena": 0, "registros_de_cuarentena": 0,
            "filas_salida": 0, "por_motivo": {},
            "cifras_que_el_contrato_no_declara": []}


def revisar_grupos(df, contrato=None, compuerta=NOMBRE_COMPUERTA):
    """Devuelve (limpias, registros, resumen) para las reglas de la clave de fila.

    Misma forma que `compuerta.revisar_lote()` a propósito: las dos listas de
    cuarentena se concatenan sin convertir nada, y el resumen de las dos entra al
    mismo `decidir_promocion()`.

    El resumen cuenta los tres cubos con grupos y **filas sobrantes** —las de un
    grupo menos la que se queda—, que es como el contrato 1.3.3 da sus cifras
    (72,631 · 2,105 · 256 sobre el alcance, medidas sin normalizar). Así la suma
    de los 38 lotes se compara directo contra ésas.
    """
    import pandas as pd

    contrato = contrato or leer_contrato()
    faltan = cifras_que_el_contrato_no_declara(contrato)
    if faltan:
        raise ValueError(
            "el contrato no declara como dato: " + ", ".join(
                f"{n} ({CIFRAS_DEL_CONTRATO[n]})" for n in faltan)
            + ". Sin eso la compuerta tendría que escribir la cifra a mano")
    clave = contrato["clave_de_fila"]
    columnas_clave = list(clave["columnas"])
    menos_de = clave["captura_doble"]["menos_de"]
    mas_de = clave["colision_precio_alta"]["mas_de"]
    alcance = clave["colision_precio_alta"]["a_cuarentena"]
    if alcance != "grupo_completo":
        raise ValueError(
            f"`colision_precio_alta.a_cuarentena` dice «{alcance}»; esta compuerta "
            "sólo sabe mandar el grupo completo"
        )

    columnas = list(df.columns)
    if df.empty:
        return df, [], _resumen_vacio()

    dic = reparaciones(contrato, columnas_clave)
    filas_dic = [{"columna": k[0], "valor_roto": k[1], "reparado": v}
                 for k, v in dic.items()]
    tabla_dic = pd.DataFrame(filas_dic, columns=["columna", "valor_roto", "reparado"])

    con = _con()
    con.register("lote", df.reset_index(drop=True).assign(__i__=range(len(df))))
    con.register("diccionario", tabla_dic)

    ks = ", ".join(f"k_{c}" for c in columnas_clave)
    # El precio va en el tipo de `columnas.precio.se_compara_como`: en flotante,
    # una diferencia de $1.00 sale 0.99999 y cae en el cubo equivocado.
    con.execute(f"CREATE OR REPLACE TABLE con_clave AS {sql_con_clave(contrato)}")
    # Las fronteras van como parámetros, no pegadas en el SQL: son cifras del
    # contrato y no se escriben aquí ni siquiera de paso.
    con.execute(f"""
        CREATE OR REPLACE TABLE grupos AS
        SELECT md5(concat_ws(chr(31), {ks})) AS grupo,
               count(*)                      AS filas,
               max(__precio__) - min(__precio__) AS diferencia,
               CASE WHEN max(__precio__) - min(__precio__) < $menos_de
                        THEN 'captura_doble'
                    WHEN max(__precio__) - min(__precio__) > $mas_de
                        THEN 'colision'
                    ELSE 'observaciones_multiples' END AS cubo
        FROM con_clave
        WHERE __precio__ IS NOT NULL
        GROUP BY {ks}
        HAVING count(*) > 1
    """, {"menos_de": menos_de, "mas_de": mas_de})
    en_colision = con.execute(f"""
        SELECT c.__i__, g.grupo, g.diferencia, g.filas
        FROM con_clave c
        JOIN grupos g ON g.grupo = md5(concat_ws(chr(31), {ks}))
        WHERE g.cubo = 'colision'
        ORDER BY c.__i__
    """).fetchall()
    por_cubo = {cubo: (int(grupos), int(sobrantes)) for cubo, grupos, sobrantes in
                con.execute("""
                    SELECT cubo, count(*), sum(filas - 1)
                    FROM grupos GROUP BY cubo
                """).fetchall()}

    from compuerta import huella

    registros, indices = [], []
    for i, grupo, diferencia, filas_del_grupo in en_colision:
        fila = {c: (None if pd.isna(df.iloc[i][c]) else df.iloc[i][c]) for c in columnas}
        fila = {c: (v.isoformat() if hasattr(v, "isoformat") else
                    (str(v) if v is not None else None)) for c, v in fila.items()}
        registros.append({
            "motivo": "colision_precio_alta",
            # FILA y no GRUPO: lo exige la tabla `cuarentena` del esquema de
            # operación. El grupo va en `grupo`, que esa tabla obliga a llenar
            # cuando el motivo es éste.
            "nivel": "FILA",
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

    def cubo(nombre):
        return por_cubo.get(nombre, (0, 0))

    limpias = df.drop(index=[df.index[i] for i in indices]) if indices else df
    resumen = {
        "filas_entrada": len(df),
        "grupos": sum(g for g, _ in por_cubo.values()),
        "grupos_captura_doble": cubo("captura_doble")[0],
        "sobrantes_captura_doble": cubo("captura_doble")[1],
        "grupos_observaciones_multiples": cubo("observaciones_multiples")[0],
        "sobrantes_observaciones_multiples": cubo("observaciones_multiples")[1],
        "grupos_en_colision": cubo("colision")[0],
        "sobrantes_en_colision": cubo("colision")[1],
        "filas_en_cuarentena": len(indices),
        "registros_de_cuarentena": len(registros),
        "filas_salida": len(limpias),
        "umbral_de_captura_doble": menos_de,
        "umbral_de_colision": mas_de,
        "por_motivo": {"colision_precio_alta": len(registros)} if registros else {},
        "cifras_que_el_contrato_no_declara": [],
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
    preparar_salida()
    import argparse

    from compuerta import leer_alcance

    ap = argparse.ArgumentParser(
        description="Las comprobaciones de lote completo: la clave de fila y la "
                    "frescura, sobre el alcance del contrato")
    ap.add_argument("archivo", nargs="?", help="el lote (.parquet o .csv)")
    ap.add_argument("--fecha-referencia", dest="fecha",
                    help="la fecha contra la que se mide la frescura "
                         "(AAAA-MM-DD). El contrato la pide como parámetro")
    ap.add_argument("--cifras", action="store_true",
                    help="qué cifras necesita esta compuerta del contrato como "
                         "dato, y si el contrato las declara")
    a = ap.parse_args()

    contrato = leer_contrato()

    if a.cifras:
        faltan = cifras_que_el_contrato_no_declara(contrato)
        print(f"contrato {contrato['version']} · cifras que esta compuerta lee:")
        for nombre, ruta in CIFRAS_DEL_CONTRATO.items():
            marca = "✗ sin declarar" if nombre in faltan else "✓ declarada   "
            print(f"  {marca}  {nombre:26} {ruta} = {_nodo(contrato, ruta)}")
        return 1 if faltan else 0

    if not a.archivo:
        ap.error("falta el archivo del lote")

    # El ALCANCE, con la misma lectura que la ingesta y la compuerta de fila: ver
    # `compuerta.leer_alcance()`. Hasta el 15 de octubre esta línea leía el
    # archivo entero con pandas, igual que la compuerta antes del #170.
    ruta = Path(a.archivo).expanduser().resolve()
    df = leer_alcance(ruta, contrato)

    limpias, _registros, resumen = revisar_grupos(df, contrato)
    frescura = revisar_frescura(df, contrato, a.fecha)

    print(json.dumps({"clave_de_fila": resumen, "frescura": frescura},
                     ensure_ascii=False, indent=2, default=str))
    print(f"\nfilas de salida: {len(limpias):,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
