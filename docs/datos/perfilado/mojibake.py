"""
Corrupción de texto · QQP (corrige las secciones 2 y 3 de perfilado.md)

Contesta tres preguntas que quedaron abiertas después de diagnostico.py:

  1. ¿El '?' está de verdad en los datos o lo mete el guión al leer?
     Se responde sola: ninguna de las dos codificaciones que usa el pipeline
     puede FABRICAR un '?'. utf-8-sig revienta con UnicodeDecodeError ante un
     byte inválido, y latin-1 mapea los 256 bytes a un carácter cada uno.
     Un '?' (byte 0x3F) sólo puede venir de los bytes del archivo.
     Este guión lo comprueba además contra el CSV crudo, sin pasar por parquet.

  2. ¿En cuántos archivos está, de verdad?
     diagnostico.py usa GROUP BY, y un GROUP BY no devuelve renglón para los
     archivos que tienen CERO coincidencias. Por eso su tabla trae 36 filas y
     no 38: los archivos que faltan no son un error, son los que están limpios.
     Aquí se listan los 38 explícitamente, con cero incluido.

  3. ¿Es irrecuperable?
     No necesariamente, y eso cambia la regla del contrato. Cuando el '?' se
     comió exactamente una letra, el valor correcto suele seguir en los datos:
     'Art?culos Deportivos' y 'Artículos Deportivos' conviven en la misma
     columna. Se busca, para cada valor roto, un gemelo de la MISMA longitud
     que coincida en todo salvo donde está el '?'. Si hay exactamente uno, la
     reparación es determinista y se puede escribir en el contrato. Si hay
     cero o hay varios, eso sí va a cuarentena.

  Y de paso detecta una corrupción DISTINTA que el '?' no ve: los caracteres
  de control C1 (U+0080–U+009F) que aparecen cuando un archivo en página de
  códigos de DOS se lee como latin-1. No son '?', son invisibles, y por eso
  ningún LIKE '%?%' los encuentra. Ver la sección de mayo de 2026 abajo.

Uso
---
    python docs/datos/perfilado/mojibake.py
    CANASTAMX_DATOS=/otra/ruta python docs/datos/perfilado/mojibake.py
"""
import os
import re
from collections import defaultdict
from pathlib import Path

import duckdb
import pandas as pd

RAIZ = Path(os.environ.get("CANASTAMX_DATOS", Path.home() / "canastamx-datos"))
PARQUETS = RAIZ / "procesado" / "por_archivo"
CRUDO = RAIZ / "crudo"
SALIDA = Path("docs/datos/perfilado")

COLUMNAS_TEXTO = ["producto", "presentacion", "marca", "categoria", "catalogo",
                  "cadena_comercial", "giro", "nombre_comercial", "direccion",
                  "estado", "municipio"]

# Los 38 archivos que DEBEN existir. Se escriben aquí para poder afirmar
# "cero" en vez de "no salió en la tabla".
ESPERADOS = ([f"{m:02d}-2025_{q:02d}" for m in range(1, 13) for q in (1, 2)] +
             [f"{m:02d}-2026_Q{q}" for m in range(1, 8) for q in (1, 2)])

CONTROL_C1 = r"[\x{0080}-\x{009F}]"


def conectar():
    con = duckdb.connect()
    con.sql("SET memory_limit='4GB'")
    tmp = RAIZ / "tmp-duckdb"
    tmp.mkdir(parents=True, exist_ok=True)
    con.sql(f"SET temp_directory='{tmp}'")
    return con


# ── 1 · ¿de verdad está en el archivo, o lo mete pandas? ─────────────────────
def viene_del_archivo():
    """Lee los BYTES del CSV crudo y busca el 0x3F donde debería haber acento.

    Es la prueba que cierra la duda: si el byte 0x3F está en el disco, no lo
    puso pandas. Si no está y aun así aparece '?', entonces sí sería el guión.
    """
    print("Buscando '?' en los bytes crudos, sin pasar por pandas ni por parquet.")
    encontrados = 0
    for carpeta in sorted(CRUDO.glob("QQP_*")):
        for path in sorted(carpeta.glob("*.csv")):
            if ":Zone.Identifier" in path.name:
                continue
            with open(path, "rb") as f:
                cabeza = f.read(4_000_000)          # 4 MB bastan y sobran
            n = cabeza.count(b"?")
            if n:
                i = cabeza.find(b"?")
                contexto = cabeza[max(0, i - 30):i + 30]
                print(f"  {path.name:<20} {n:>6} bytes 0x3F en los primeros 4 MB")
                print(f"      contexto: {contexto!r}")
                encontrados += 1
                if encontrados >= 4:
                    print("      (basta con estos; el patrón se repite)")
                    return
    if not encontrados:
        print("  No apareció ninguno en los primeros 4 MB de cada archivo.")
        print("  Eso NO descarta el hallazgo: el '?' está concentrado en junio")
        print("  de 2026 y puede caer más adelante en el archivo. Revisa un")
        print("  archivo de junio completo con:  grep -c '?' 06-2026_Q1.csv")


def revisar_codificacion_mayo():
    """Los dos archivos de mayo se leen con latin-1. ¿Es la codificación correcta?

    latin-1 nunca falla: mapea los 256 bytes posibles. Eso lo vuelve la
    codificación más peligrosa que existe, porque una elección equivocada no
    da error — da texto silenciosamente roto. Los bytes 0x80–0x9F, que en las
    páginas de códigos de DOS son letras acentuadas, en latin-1 son caracteres
    de control invisibles.
    """
    print("\nLos dos archivos de mayo de 2026 (los que se leen con latin-1):")
    print("En texto ISO-8859-1 de verdad, los bytes 0x80–0x9F NO APARECEN NUNCA:")
    print("son caracteres de control, nadie los escribe en un CSV. Si aparecen,")
    print("el archivo no es latin-1, y latin-1 no se va a quejar — por eso hay")
    print("que mirar los bytes.\n")

    for nombre in ("05-2026_Q1.csv", "05-2026_Q2.csv"):
        cand = list(CRUDO.glob(f"*/{nombre}"))
        if not cand:
            print(f"  {nombre}: no está en {CRUDO}")
            continue
        with open(cand[0], "rb") as f:
            cabeza = f.read(4_000_000)
        cuenta = {b: cabeza.count(bytes([b])) for b in range(0x80, 0x100)}
        c1 = sum(n for b, n in cuenta.items() if b < 0xA0)
        alto = sum(n for b, n in cuenta.items() if b >= 0xA0)
        print(f"  ── {nombre} · primeros {len(cabeza):,} bytes")
        print(f"     bytes 0x80–0x9F (controles en latin-1): {c1:>8,}")
        print(f"     bytes 0xA0–0xFF (acentos en latin-1)  : {alto:>8,}")

        if not c1:
            print("     Sin bytes de control: latin-1 es una lectura defendible.\n")
            continue

        print("     HAY BYTES DE CONTROL → latin-1 NO es la codificación de este archivo.")
        print("     Qué letra sería cada byte según cada página de códigos:\n")
        print(f"     {'byte':>5} {'veces':>9}  {'latin-1':<9} {'cp850':<8} {'cp437':<8} {'cp1252':<8}")
        for b, n in sorted(cuenta.items(), key=lambda kv: -kv[1])[:8]:
            if not n:
                continue
            def leer(cp):
                try:
                    ch = bytes([b]).decode(cp)
                    return repr(ch) if ch.isprintable() else f"U+{ord(ch):04X}"
                except UnicodeDecodeError:
                    return "—"
            print(f"     0x{b:02X} {n:>9,}  {leer('latin-1'):<9} {leer('cp850'):<8} "
                  f"{leer('cp437'):<8} {leer('cp1252'):<8}")

        i = next(k for k, b in enumerate(cabeza) if 0x80 <= b < 0xA0)
        ctx = cabeza[max(0, i - 30):i + 30]
        print(f"\n     Un caso concreto:")
        print(f"       bytes    : {ctx!r}")
        for cp in ("latin-1", "cp850", "cp437", "cp1252"):
            try:
                print(f"       {cp:<8} : {ctx.decode(cp)}")
            except UnicodeDecodeError:
                print(f"       {cp:<8} : falla al decodificar")
        print("\n     Elige la que produzca palabras en español y cámbiala en")
        print("     ATIPICOS_MAYO_2026 de perfilado_nivel1.py y perfilado_nivel2.py.")
        print("     Después hay que BORRAR los dos parquet de mayo y regenerarlos:")
        print("     el parquet ya guardó el texto roto, no se arregla solo.\n")


# ── 2 · ¿en cuántos archivos, de verdad? ────────────────────────────────────
def por_archivo(con):
    fuente = f"read_parquet('{PARQUETS}/*.parquet', union_by_name=True, filename=True)"
    cond_q = " OR ".join(f"{c} LIKE '%?%'" for c in COLUMNAS_TEXTO)
    cond_c = " OR ".join(f"regexp_matches({c}, '{CONTROL_C1}')" for c in COLUMNAS_TEXTO)
    r = con.sql(f"""
        SELECT regexp_extract(filename, '([^/]+)\\.parquet$', 1) AS archivo,
               count(*) AS filas,
               count(*) FILTER (WHERE {cond_q}) AS con_interrogacion,
               count(*) FILTER (WHERE {cond_c}) AS con_control
        FROM {fuente} GROUP BY 1
    """).df().set_index("archivo")

    faltan = [a for a in ESPERADOS if a not in r.index]
    sobran = [a for a in r.index if a not in ESPERADOS]
    tabla = r.reindex(ESPERADOS).fillna(0).astype("int64")
    tabla["pct"] = (tabla.con_interrogacion / tabla.filas.clip(lower=1) * 100).round(4)

    print(f"  Archivos encontrados: {len(r)} de {len(ESPERADOS)} esperados")
    if faltan:
        print(f"  NO ESTÁN en la carpeta de parquets: {faltan}")
    if sobran:
        print(f"  Están y no se esperaban: {sobran}")
    limpios = tabla[tabla.con_interrogacion == 0]
    print(f"\n  Archivos con CERO '?' : {len(limpios)} → {list(limpios.index)}")
    print(f"  Archivos con algún '?': {len(tabla) - len(limpios)}")
    ctrl = tabla[tabla.con_control > 0]
    if len(ctrl):
        print(f"\n  Archivos con caracteres de CONTROL C1 (corrupción que el '?' no ve):")
        print(ctrl[["filas", "con_control"]].to_string())
    else:
        print("\n  Ningún archivo trae caracteres de control C1.")

    print("\n  Los ocho archivos más afectados por '?':")
    print(tabla.sort_values("con_interrogacion", ascending=False)
              .head(8)[["filas", "con_interrogacion", "pct"]].to_string())
    return tabla


# ── 3 · ¿cuánto se puede reparar? ───────────────────────────────────────────
def gemelos_de_una_columna(con, col):
    fuente = f"read_parquet('{PARQUETS}/*.parquet', union_by_name=True)"
    vals = con.sql(f"""
        SELECT {col} AS v, count(*) AS filas
        FROM {fuente} WHERE {col} IS NOT NULL GROUP BY 1
    """).df()
    rotos = vals[vals.v.str.contains("?", regex=False)]
    sanos = vals[~vals.v.str.contains("?", regex=False)]
    if rotos.empty:
        return None

    # Un '?' sustituye exactamente un carácter, así que el gemelo tiene que
    # medir lo mismo. Agrupar por longitud reduce la búsqueda de un producto
    # cartesiano a unas pocas comparaciones, y sirve además de comprobación:
    # si un valor roto no tiene NINGÚN candidato de su longitud, la suposición
    # de "un '?' = una letra" no se sostiene para ese caso.
    por_largo = defaultdict(list)
    for v in sanos.v:
        por_largo[len(v)].append(v)
    filas_sanas = dict(zip(sanos.v, sanos.filas))

    out = []
    for v, filas in zip(rotos.v, rotos.filas):
        patron = re.compile("^" + "".join("." if ch == "?" else re.escape(ch) for ch in v) + "$")
        cand = [b for b in por_largo.get(len(v), ()) if patron.match(b)]
        clase = "reparable" if len(cand) == 1 else ("ambiguo" if cand else "sin gemelo")
        out.append({
            "columna": col, "valor_roto": v, "filas": int(filas),
            "clase": clase, "candidatos": len(cand),
            "reparado": cand[0] if len(cand) == 1 else "",
            "filas_del_gemelo": int(filas_sanas.get(cand[0], 0)) if len(cand) == 1 else 0,
            "todos_los_candidatos": " | ".join(cand[:5]),
        })
    return pd.DataFrame(out)


def reparabilidad(con):
    partes = [p for c in COLUMNAS_TEXTO if (p := gemelos_de_una_columna(con, c)) is not None]
    if not partes:
        print("  No hay ningún valor con '?' en las columnas de texto.")
        return pd.DataFrame()
    todo = pd.concat(partes, ignore_index=True)

    resumen = (todo.groupby(["columna", "clase"])
                   .agg(valores=("valor_roto", "size"), filas=("filas", "sum"))
                   .unstack(fill_value=0))
    print("  Valores distintos y filas, por columna y por clase:\n")
    print(resumen.to_string())

    tot = todo.filas.sum()
    for clase in ("reparable", "ambiguo", "sin gemelo"):
        sub = todo[todo.clase == clase]
        print(f"\n  {clase:<12}: {len(sub):>5} valores distintos · "
              f"{sub.filas.sum():>10,} filas ({sub.filas.sum()/tot:6.2%} de lo corrupto)")

    rep = todo[todo.clase == "reparable"]
    print(f"\n  → Con un diccionario de {len(rep)} sustituciones se recupera el "
          f"{rep.filas.sum()/tot:.1%} de las filas corruptas.")
    print("  → El resto va a cuarentena, y ésa sí es la regla CU-03.")

    amb = todo[todo.clase == "ambiguo"]
    if not amb.empty:
        print(f"\n  Ambiguos (más de un gemelo posible) — hay que decidirlos a mano:")
        print(amb[["columna", "valor_roto", "filas", "todos_los_candidatos"]]
              .sort_values("filas", ascending=False).head(10).to_string(index=False))

    sin = todo[todo.clase == "sin gemelo"].sort_values("filas", ascending=False)
    if not sin.empty:
        print(f"\n  Sin gemelo — los diez con más filas:")
        print(sin[["columna", "valor_roto", "filas"]].head(10).to_string(index=False))
    return todo


if __name__ == "__main__":
    if not any(PARQUETS.glob("*.parquet")):
        raise SystemExit(f"No hay parquets en {PARQUETS}. Corre antes perfilado_nivel2.py")
    con = conectar()

    print("=" * 78)
    print("1 · ¿El '?' viene del archivo o lo mete el guión?")
    print("=" * 78)
    if CRUDO.exists():
        viene_del_archivo()
        revisar_codificacion_mayo()
    else:
        print(f"  (no encuentro {CRUDO}; me salto la comprobación sobre el CSV crudo)")

    print("\n" + "=" * 78)
    print("2 · Reparto real por archivo — con los ceros incluidos")
    print("=" * 78)
    por_archivo(con)

    print("\n" + "=" * 78)
    print("3 · ¿Cuánto de esto es reparable de forma determinista?")
    print("=" * 78)
    todo = reparabilidad(con)
    if not todo.empty:
        SALIDA.mkdir(parents=True, exist_ok=True)
        todo.to_csv(SALIDA / "mojibake-clasificado.csv", index=False)
        rep = todo[todo.clase == "reparable"]
        rep[["columna", "valor_roto", "reparado", "filas"]].to_csv(
            SALIDA / "mojibake-diccionario.csv", index=False)
        print(f"\n  {SALIDA/'mojibake-clasificado.csv'}  — todo, con su clase")
        print(f"  {SALIDA/'mojibake-diccionario.csv'}   — sólo las sustituciones seguras")
        print("\n  Ese segundo archivo es un insumo del contrato de la semana 2:")
        print("  se aplica ANTES de agrupar por categoría o municipio, y lo que")
        print("  no esté en él se manda a la tabla de rechazos con el motivo.")
