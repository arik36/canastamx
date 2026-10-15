#!/usr/bin/env python3
"""
compuerta.py — CanastaMX · T043 · la compuerta de calidad contra el contrato

QUÉ HACE
--------
Revisa un lote **fila por fila** contra `contracts/qqp-v1.yaml` y separa las que
no cumplen, cada una **con su motivo**. Después aplica la regla de lote: si más
del 5% de las filas quedó apartada, el lote entero no se promueve (D-07).

Es la pieza que `ingesta.py` anunciaba y no hacía: su docstring dice «no valida:
eso es de la semana 6, cuando entra la compuerta de calidad contra
`contracts/qqp-v1.yaml`». Esto es esa compuerta.

EL ESQUEMA NO SE ESCRIBE AQUÍ: SE GENERA DEL CONTRATO
-----------------------------------------------------
Éste es el punto entero del archivo, y es lo que el proyecto investiga.

Las reglas de columna —qué no puede ir vacío, qué largo máximo tiene cada texto,
qué tipo es cada valor— **viven en el contrato y en ningún otro lado**. Este
módulo las lee y construye el esquema de Pandera a partir de ellas. Cambiar
`largo_maximo: 65` a `70` en el YAML cambia la compuerta sin tocar una línea de
Python.

La alternativa —escribir las reglas otra vez, en código— es la que este trabajo
estudia como falla: dos documentos que dicen lo mismo y se separan en silencio.
Por eso aquí no hay ni un solo `65` escrito a mano. Si lo ves, es un error.

LOS CINCO MOTIVOS QUE EMITE, Y LOS QUE NO
-----------------------------------------
De fila, y los cinco están en el catálogo de `docs/datos/esquema-de-operacion.sql`:

    valor_requerido_vacio    columnas.*.valor_requerido        en_contrato: false
    largo_excedido           columnas.*.largo_maximo           en_contrato: false
    tipo_invalido            columnas.*.tipo                   en_contrato: false
    fecha_fuera_de_ventana   columnas.fecha_registro.rango     en_contrato: true
    precio_fuera_de_rango    columnas.precio.al_exceder        en_contrato: true

**Los tres primeros todavía no están declarados en el contrato.** El catálogo ya
los marca con `en_contrato = false` y el protocolo pide declararlos antes del 9 de
noviembre. Esta compuerta los produce hoy, y `--motivos` imprime cuáles le faltan
al contrato: ésa es la lista de trabajo, generada en vez de recordada.

Lo que **no** emite, a propósito, porque necesita ver más de una fila y vive en
DuckDB: `colision_precio_alta` (compara grupos), `codificacion_irrecuperable` y
`revision_humana` (necesitan el diccionario y la frecuencia sobre el corpus),
y las compuertas de corrida (`frescura_*`).

UNA FILA PUEDE LLEVAR VARIOS MOTIVOS
------------------------------------
No se elige «el peor». La tabla `cuarentena` tiene `UNIQUE (corrida_id,
huella_fila, motivo)`: la llave admite la misma fila con motivos distintos, y lo
contrario —quedarse con uno— perdería información que SLA-D-09 pide conservar.
Un precio vacío en una columna requerida y un largo excedido en otra son dos
hallazgos, y se registran los dos.

Para el umbral del 5% se cuentan **filas distintas**, no registros de cuarentena.
Con 12 motivos sobre 10 filas, lo que se compara contra el 5% es 10.

LO QUE PRODUCE
--------------
Dos cosas, con la forma exacta de las tablas del esquema de operación, para que
cargarlas sea un `COPY` el día que la base exista (hoy no existe: ver
`docs/datos/esquema-de-operacion.md`):

    cuarentena-<lote>.jsonl   un registro por (fila, motivo), con motivo, nivel,
                              compuerta, huella_fila, grupo y la fila tal como llegó
    compuerta-<lote>.json     el registro de `paso`, con capa COMPUERTA, las tres
                              cuentas de filas y el resultado

USO
---
    python services/data-platform/ingestion/compuerta.py <archivo> --lote 07-2026_Q2
    python services/data-platform/ingestion/compuerta.py --motivos     # qué le falta al contrato
"""

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ingesta import (
    columnas_del_contrato,
    lector,
    lectura_declarada,
    leer_contrato,
    morir,
    recorte_del_contrato,
)

NOMBRE_COMPUERTA = "contrato_por_fila"
SALIDAS = Path(__file__).resolve().parent / "corridas"

# Los motivos que esta compuerta sabe emitir, con la regla del contrato de la que
# salen. La prueba `test_compuerta.py` comprueba que los cinco existan en el
# catálogo de `esquema-de-operacion.sql` con nivel FILA y efecto CUARENTENA: si
# alguien renombra uno allá, la prueba truena aquí.
# Pandera reporta un nulo en una columna `nullable=False` con su propio nombre
# interno. No se puede renombrar, así que se traduce: un nulo en una columna con
# `valor_requerido` ES un valor requerido vacío.
NULO_PANDERA = "not_nullable"

MOTIVOS = {
    "valor_requerido_vacio":  "columnas.*.valor_requerido",
    "largo_excedido":         "columnas.*.largo_maximo",
    "tipo_invalido":          "columnas.*.tipo",
    "fecha_fuera_de_ventana": "columnas.fecha_registro.al_estar_fuera_de_rango",
    "precio_fuera_de_rango":  "columnas.precio.al_exceder",
}


# ── Conversiones tolerantes ────────────────────────────────────────────────
# El lote puede llegar como CSV —todo texto— o desde la capa cruda, donde la
# ingesta ya resolvió los tipos. Las dos formas tienen que poder revisarse con
# el mismo esquema, así que cada conversión acepta las dos y devuelve NaT/NaN
# donde no pudo. Eso es lo que vuelve `tipo_invalido` detectable en lugar de
# hacer reventar la corrida.

def como_decimal(serie):
    import pandas as pd
    return pd.to_numeric(serie, errors="coerce")


def como_fecha(serie, formato=None):
    import pandas as pd
    if pd.api.types.is_datetime64_any_dtype(serie):
        return serie
    return pd.to_datetime(serie, format=formato, errors="coerce")


def _vacio(serie):
    """Vacío es nulo **o** cadena en blanco. El contrato dice «la celda no puede
    venir vacía», y en un CSV eso llega como `""`, no como nulo."""
    return serie.isna() | (serie.astype("string").fillna("").str.strip() == "")


def formato_de_fecha(contrato, nombre_archivo):
    """El contrato declara el formato POR ARCHIVO. Se reusa el traductor de
    `ingesta.py` para no tener dos tablas de formatos."""
    from ingesta import _FMT
    fec = contrato.get("archivo", {}).get("formato_de_fecha", {})
    humano = fec.get("excepciones", {}).get(nombre_archivo) or fec.get("por_defecto")
    return _FMT.get(humano)


def hasta_de_la_ventana(contrato):
    """`rango_aceptado.hasta` puede decir `hoy`, que no es una fecha: es una regla."""
    rango = contrato["columnas"]["fecha_registro"]["rango_aceptado"]
    desde, hasta = rango["desde"], rango["hasta"]
    if str(hasta) == "hoy":
        hasta = dt.date.today().isoformat()
    return str(desde), str(hasta)


# ── El esquema, generado del contrato ──────────────────────────────────────

def esquema_del_contrato(contrato, nombre_archivo=None):
    """Construye el esquema de Pandera leyendo `columnas` del contrato.

    Cada comprobación lleva como `name` el código del motivo, así que el informe
    de Pandera ya viene con el vocabulario del esquema de operación y no hace
    falta traducir nombres internos.
    """
    try:
        import pandas as pd
        import pandera.pandas as pa
        from pandera.pandas import Check, Column, DataFrameSchema
    except ImportError:
        morir("falta pandera.  pip install -r services/data-platform/requirements.txt")

    cols, columnas = {}, contrato["columnas"]
    fmt = formato_de_fecha(contrato, nombre_archivo) if nombre_archivo else None

    for nombre, decl in columnas.items():
        checks = []
        requerido = bool(decl.get("valor_requerido"))

        # Un valor requerido puede faltar de dos formas y Pandera las trata
        # distinto: el NULO lo atrapa `nullable=False`, y la CADENA EN BLANCO
        # tiene que atraparla una comprobación, porque para Pandera no es nula.
        # Las dos caen en el mismo motivo; `NULO_PANDERA` las junta al leer.
        if requerido:
            checks.append(Check(lambda s: ~_vacio(s), name="valor_requerido_vacio"))

        largo = decl.get("largo_maximo")
        if largo:
            checks.append(Check(
                lambda s, n=largo: _vacio(s) | (s.astype("string").str.len() <= n),
                name="largo_excedido"))

        tipo = str(decl.get("tipo", "texto"))
        if tipo.startswith("decimal"):
            checks.append(Check(lambda s: _vacio(s) | como_decimal(s).notna(),
                                name="tipo_invalido"))
        elif tipo == "fecha":
            checks.append(Check(lambda s, f=fmt: _vacio(s) | como_fecha(s, f).notna(),
                                name="tipo_invalido"))

        cols[nombre] = Column(None, checks, nullable=not requerido, required=True)

    # ── fecha_registro · la ventana del alcance ────────────────────────────
    desde, hasta = hasta_de_la_ventana(contrato)

    def en_la_ventana(serie, formato=fmt, d=desde, h=hasta):
        v = como_fecha(serie, formato)
        return v.isna() | ((v >= pd.Timestamp(d)) & (v <= pd.Timestamp(h)))

    cols["fecha_registro"].checks.append(
        Check(en_la_ventana, name="fecha_fuera_de_ventana"))

    # ── precio · mínimo global y techo por catálogo ────────────────────────
    # Va al nivel del DataFrame porque el techo depende de `catalogo`, que es otra
    # columna. Pandera lo reporta bajo cada columna; el índice de la fila es el
    # mismo, y es lo único que se usa.
    precio = columnas["precio"]
    minimo = precio.get("minimo")
    techos = {str(k).strip().upper(): float(v)
              for k, v in (precio.get("maximo_por_catalogo") or {}).items()}

    def en_rango(df, minimo=minimo, techos=techos):
        v = como_decimal(df["precio"])
        techo = (df["catalogo"].astype("string").str.strip().str.upper()
                 .map(techos).astype("float64"))
        ok = v.isna()                                   # lo que no parsea es tipo_invalido
        ok = ok | ((v >= (minimo if minimo is not None else -float("inf")))
                   & (techo.isna() | (v <= techo)))
        return ok

    esquema = DataFrameSchema(
        cols,
        checks=[Check(en_rango, name="precio_fuera_de_rango")],
        strict=False, coerce=False, name="contrato_qqp")
    return esquema, pa


# ── La revisión de un lote ─────────────────────────────────────────────────

def huella(fila, columnas):
    """sha256 de la fila tal como llegó, en el orden del contrato. `char(64)` en
    la tabla `cuarentena`, y la mitad de su llave única."""
    crudo = "\x1f".join("" if fila.get(c) is None else str(fila.get(c)) for c in columnas)
    return hashlib.sha256(crudo.encode("utf-8")).hexdigest()


def revisar_lote(df, contrato, nombre_archivo=None, compuerta=NOMBRE_COMPUERTA):
    """Devuelve (limpias, cuarentena, resumen).

    `cuarentena` trae un registro por (fila, motivo), con los campos de la tabla.
    `limpias` son las filas sin ningún motivo: las que se promueven.
    """
    import pandas as pd
    columnas = columnas_del_contrato(contrato)
    faltantes = [c for c in columnas if c not in df.columns]
    if faltantes:
        # Nivel LOTE, no FILA: le falta una columna al archivo entero (CU-02 · 2b).
        return None, None, {"resultado": "DETENIDO", "motivo_lote": "columna_requerida_faltante",
                            "columnas_faltantes": faltantes, "filas_entrada": len(df)}

    esquema, pa = esquema_del_contrato(contrato, nombre_archivo)
    try:
        esquema.validate(df, lazy=True)
        fallos = pd.DataFrame(columns=["column", "check", "index"])
    except pa.errors.SchemaErrors as e:
        fallos = e.failure_cases

    fallos = fallos.copy()
    fallos["check"] = fallos["check"].replace(NULO_PANDERA, "valor_requerido_vacio")
    fallos = fallos[fallos["index"].notna() & fallos["check"].isin(MOTIVOS)]
    registros, por_fila = [], {}
    for idx, motivo in (fallos[["index", "check"]].drop_duplicates()
                        .itertuples(index=False, name=None)):
        i = int(idx)
        por_fila.setdefault(i, set()).add(motivo)

    for i, motivos in sorted(por_fila.items()):
        fila = {c: (None if pd.isna(df.iloc[i][c]) else df.iloc[i][c]) for c in columnas}
        fila = {c: (v.isoformat() if hasattr(v, "isoformat") else
                    (str(v) if v is not None else None)) for c, v in fila.items()}
        h = huella(fila, columnas)
        for motivo in sorted(motivos):
            registros.append({"motivo": motivo, "nivel": "FILA", "compuerta": compuerta,
                              "huella_fila": h, "grupo": None, "fila": fila})

    limpias = df.drop(index=[df.index[i] for i in por_fila]) if por_fila else df
    resumen = {
        "filas_entrada": len(df),
        "filas_en_cuarentena": len(por_fila),     # FILAS distintas, no registros
        "registros_de_cuarentena": len(registros),
        "filas_salida": len(limpias),
        "por_motivo": {m: sum(1 for r in registros if r["motivo"] == m)
                       for m in sorted({r["motivo"] for r in registros})},
    }
    return limpias, registros, resumen


def decidir_promocion(resumen, contrato):
    """La regla de lote de D-07: más del 5% de las filas en cuarentena y el lote
    entero se detiene. El umbral se lee del contrato, no se escribe aquí."""
    umbral = contrato["promocion_del_lote"]["rechazo_maximo"]
    entrada = resumen["filas_entrada"] or 1
    proporcion = resumen["filas_en_cuarentena"] / entrada
    resumen["proporcion_en_cuarentena"] = round(proporcion, 6)
    resumen["umbral"] = umbral
    if proporcion > umbral:
        resumen["resultado"] = "DETENIDO"
        resumen["motivo_lote"] = "rechazo_mayor_al_umbral"
        resumen["filas_salida"] = 0          # no se promueve ni la parte que pasó
    else:
        resumen["resultado"] = "PASO" if not resumen["filas_en_cuarentena"] else "AVISO"
    return resumen


def motivos_que_el_contrato_no_declara(contrato=None):
    """Qué motivos de esta compuerta no aparecen en el contrato. Es la lista de
    trabajo de `pendientes`, generada en vez de recordada: pendiente antes del 9
    de noviembre.

    Se busca sobre el **texto** del contrato, no sobre el YAML ya interpretado, y
    la razón vale la pena: hoy `fecha_fuera_de_ventana` y `precio_fuera_de_rango`
    sólo aparecen en sendos COMENTARIOS (líneas 565 y 601 de la 1.3.4), y un
    comentario desaparece al interpretar el archivo. Buscar sobre el texto es lo
    que hace un humano al leerlo.

    Que estén nada más en un comentario es, de todas formas, la mitad del
    problema: un comentario no es una declaración y ningún programa puede
    obedecerlo. Lo que el contrato necesita en la 1.3.5 es nombrar los cinco
    motivos como DATO, no en prosa.
    """
    from ingesta import CONTRATO
    texto = CONTRATO.read_text(encoding="utf-8")
    return [m for m in MOTIVOS if m not in texto]


# ── Línea de comandos ──────────────────────────────────────────────────────

def leer_alcance(ruta, contrato, sin_recorte=False):
    """Las filas del lote que el contrato considera suyas, y sólo ésas.

    **Ésta es la población sobre la que la compuerta juzga, y no es un detalle.**
    Un archivo del corpus trae las 32 entidades y todos los catálogos: en
    promedio, sólo el 12.45% de sus filas es del alcance del contrato. La
    compuerta mide el 5% de D-07 y la contención de H1 sobre **el alcance**
    (2,658,906 filas en los 38 lotes), no sobre el corpus (21,357,873). Si
    juzgara el archivo entero, el denominador sería otro y las cifras dejarían de
    ser comparables con todo lo demás del proyecto.

    La primera versión de esta compuerta leía el archivo entero con pandas, y eso
    tenía dos problemas que no se veían con los lotes de prueba, porque todas sus
    filas eran del alcance:

      1. **La población equivocada.** Medido sobre un parquet con 91 filas de las
         que 11 son del alcance: la compuerta revisaba las 91.
      2. **`pd.read_parquet` necesita pyarrow**, que no está en `requirements.txt`.
         Los 38 archivos del corpus son parquet, así que cualquier lote real
         fallaba al leerse. Las pruebas no lo veían porque todas eran CSV.

    Esta versión lee **exactamente como `ingesta.py`**: con su `lector()` —que
    respeta la codificación y el formato de fecha que el contrato declara para
    cada archivo— y con su `recorte_del_contrato()`, las mismas tres condiciones
    (entidad, ventana y catálogo). No se reescriben aquí: una condición PARECIDA
    no es la misma condición, y las filas que la compuerta revisa tienen que ser
    las mismas que la ingesta escribe al bucket. DuckDB lee el parquet sin
    pyarrow.

    Una consecuencia, dicha en voz alta: con el recorte, una fila fechada fuera de
    `alcance.ventana` ya no llega a la compuerta —la ingesta la cuenta como «fuera
    por ventana», no como defecto—, así que el motivo `fecha_fuera_de_ventana`
    sólo puede dispararse con `sin_recorte=True`. Es lo coherente: una fila que no
    es del alcance no cuenta contra el 5% del alcance.

    Con CSV, una fecha ilegible detiene la lectura en lugar de ir a cuarentena,
    porque la condición de la ventana necesita la fecha. Es lo mismo que ya hace
    `ingesta.py` con ese archivo, así que la compuerta no es más estricta que la
    ingesta. Con el corpus no puede pasar: en parquet la fecha viene tipada.
    """
    import duckdb

    ruta = Path(ruta)
    decl = lectura_declarada(contrato, ruta.name)
    # SELECT * y no las 15: si al archivo le falta una columna que no es de las
    # del recorte, `revisar_lote()` lo devuelve como `columna_requerida_faltante`
    # a nivel LOTE (CU-02 · 2b), que es mejor que un error de SQL.
    sql = f"SELECT * FROM {lector(ruta, decl)}"
    if not sin_recorte:
        s = recorte_del_contrato(contrato)["sql"]
        sql += f" WHERE ({s['estado']}) AND ({s['ventana']}) AND ({s['catalogo']})"
    return duckdb.connect(":memory:").sql(sql).df()


def main():
    p = argparse.ArgumentParser(description="Compuerta de calidad contra el contrato.")
    p.add_argument("archivo", nargs="?", help="CSV o Parquet del lote")
    p.add_argument("--lote", help="nombre del lote, p. ej. 07-2026_Q2")
    p.add_argument("--motivos", action="store_true",
                   help="imprime qué motivos no están declarados en el contrato y termina")
    p.add_argument("--simular", action="store_true", help="no escribe archivos de salida")
    p.add_argument("--sin-recorte", action="store_true", dest="sin_recorte",
                   help="revisa el archivo COMPLETO, no sólo el alcance del contrato. "
                        "Igual que en ingesta.py: para reprocesar si el ADR 001 o el "
                        "005 cambian. Las cifras que salen así NO son del alcance")
    a = p.parse_args()

    contrato = leer_contrato()
    if a.motivos:
        faltan = motivos_que_el_contrato_no_declara(contrato)
        print(f"contrato {contrato['version']} · la compuerta emite {len(MOTIVOS)} motivos de fila")
        for m, regla in MOTIVOS.items():
            print(f"  {'✗ sin declarar' if m in faltan else '✓ declarado   '}  {m:24} {regla}")
        if faltan:
            print(f"\nFaltan {len(faltan)} por declarar en el contrato, antes del 9 de noviembre.")
        return 0 if not faltan else 1

    if not a.archivo:
        p.error("falta el archivo del lote (o usa --motivos)")
    ruta = Path(a.archivo)
    if not ruta.exists():
        morir(f"no encuentro {ruta}")
    lote = a.lote or ruta.stem

    df = leer_alcance(ruta, contrato, sin_recorte=a.sin_recorte)
    limpias, cuarentena, resumen = revisar_lote(df, contrato, nombre_archivo=ruta.name)
    if limpias is None:
        print(f"✗ lote detenido: {resumen['motivo_lote']} · faltan "
              f"{', '.join(resumen['columnas_faltantes'])}", file=sys.stderr)
        return 1

    inicio = dt.datetime.now(dt.UTC)
    resumen = decidir_promocion(resumen, contrato)
    paso = {"lote": lote, "capa": "COMPUERTA", "nombre": NOMBRE_COMPUERTA,
            "filas_entrada": resumen["filas_entrada"], "filas_salida": resumen["filas_salida"],
            "filas_en_cuarentena": resumen["filas_en_cuarentena"],
            "iniciado_en": inicio.isoformat(timespec="seconds"),
            "terminado_en": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
            "resultado": resumen["resultado"], "detalle": resumen}

    marca = {"PASO": "✓", "AVISO": "⚠", "DETENIDO": "✗"}[resumen["resultado"]]
    print(f"{marca} {lote} · {resumen['filas_entrada']:,} filas · "
          f"{resumen['filas_en_cuarentena']:,} en cuarentena "
          f"({resumen['proporcion_en_cuarentena']:.2%}, umbral {resumen['umbral']:.0%}) · "
          f"{resumen['filas_salida']:,} se promueven")
    for m, n in resumen["por_motivo"].items():
        print(f"    {n:>7,}  {m}")
    if resumen["resultado"] == "DETENIDO":
        print(f"    el lote no se promueve: {resumen['motivo_lote']}")

    if not a.simular:
        SALIDAS.mkdir(parents=True, exist_ok=True)
        (SALIDAS / f"compuerta-{lote}.json").write_text(
            json.dumps(paso, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        with open(SALIDAS / f"cuarentena-{lote}.jsonl", "w", encoding="utf-8") as f:
            f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in cuarentena)
        print(f"    corridas/compuerta-{lote}.json · corridas/cuarentena-{lote}.jsonl")
    return 0 if resumen["resultado"] != "DETENIDO" else 2


if __name__ == "__main__":
    sys.exit(main())
