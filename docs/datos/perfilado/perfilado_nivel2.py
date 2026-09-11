"""
Perfilado nivel 2 · QQP (T004) · versión 2

Cada CSV se normaliza a su propio parquet (uno a la vez, sin saturar RAM);
DuckDB agrega los 38 parquets sin juntarlos nunca en un DataFrame de pandas.

Qué cambió respecto de la v1
----------------------------
1. `normalizar()` sólo se llamaba `if not any(PARQUETS.glob("*.parquet"))`.
   Es decir: bastaba con que existiera UN parquet para que no se generara
   ninguno más. Borrar los dos de mayo para rehacerlos no hacía nada — sin
   error y sin aviso. Ahora se llama siempre, y el `if destino.exists()` de
   adentro se encarga de saltarse los que ya están.

2. `categoria` se repara con el diccionario que midió mojibake.py antes de
   normalizar acentos. Sin eso, `art?culos deportivos` y `articulos
   deportivos` salían como dos categorías en la tabla del informe, cada una
   con la mitad de la muestra para calcular su p99.

3. `strip_accents()` de DuckDB en lugar de cinco `replace()` encadenados:
   también cubre mayúsculas acentuadas y `ü`. (Convierte `ñ` a `n`; sirve como
   clave de agrupación, no como texto para mostrar.)

4. `sospechosos()` ya no devuelve un número que no significa nada. Devolvía 0
   y no podía devolver otra cosa: en las 46 categorías la razón máx/p99 más
   alta es 6.29x y la regla pedía 10x. Ahora imprime la demostración y manda
   a centinelas.py, que es donde está la detección que sí funciona.

5. `cardinalidad()` usaba `nombre_comercial || '§' || direccion`. En SQL, `||`
   con un NULL devuelve NULL y esa fila desaparece del `count(DISTINCT)`. Hoy
   no hay nulos ahí, pero el día que los haya el conteo bajaría en silencio.
   `concat()` trata el NULL como cadena vacía.

6. `SET temp_directory`: una base DuckDB en memoria no puede derramar a disco
   sin eso, y con 21 millones de filas eso es la diferencia entre tardarse y
   morir con «Out of Memory Error».

Sobre los parquet que YA existen
--------------------------------
No hace falta rehacerlos. `read_csv` sin `keep_default_na=False` convertiría a
nulo textos como `NA` o `NULL`, pero C2 comprobó que esos literales no
aparecen en esta fuente: los únicos marcadores textuales son `S/m` y `S/M`, que
pandas no toca. Los parquet actuales son equivalentes a los que produciría esta
versión. El arreglo queda puesto para la quincena que sí los traiga — que es
justo el caso que el proyecto dice que va a detectar.

Uso
---
    python docs/datos/perfilado/perfilado_nivel2.py
    python docs/datos/perfilado/perfilado_nivel2.py --rehacer 05-2026_Q1 06-2026_Q2
    python docs/datos/perfilado/perfilado_nivel2.py --rehacer-todo
"""
import os
import sys
from pathlib import Path

import duckdb
import pandas as pd

RAIZ = Path(os.environ.get("CANASTAMX_DATOS", Path.home() / "canastamx-datos"))
CRUDO = RAIZ / "crudo"
CARPETAS = [CRUDO / "QQP_2025", CRUDO / "QQP_2026"]
PARQUETS = RAIZ / "procesado" / "por_archivo"
SALIDA = Path("docs/datos/perfilado")

# Comprobado el 10/09/2026 con mojibake.py: estos dos NO traen bytes 0x80–0x9F,
# así que latin-1 es la lectura correcta y no una suposición.
ATIPICOS_MAYO_2026 = {"05-2026_Q1.csv", "05-2026_Q2.csv"}

REPDIGIT = r"^9+\.(00|99)$"


# ── generación de parquet ───────────────────────────────────────────────────
def normalizar(rehacer=()):
    """Escribe un parquet por CSV. Sólo los que faltan, salvo los de `rehacer`."""
    PARQUETS.mkdir(parents=True, exist_ok=True)
    hechos = 0
    for carpeta in CARPETAS:
        if not carpeta.exists():
            continue
        for path in sorted(carpeta.glob("*.csv")):
            if ":Zone.Identifier" in path.name:
                continue
            destino = PARQUETS / f"{path.stem}.parquet"
            if path.stem in rehacer and destino.exists():
                destino.unlink()
                print(f"borrado para rehacer: {destino.name}")
            if destino.exists():
                continue

            atipico = path.name in ATIPICOS_MAYO_2026
            encoding = "latin-1" if atipico else "utf-8-sig"
            formato_fecha = "%d/%m/%Y" if atipico else "%Y/%m/%d"

            # dtype=str + keep_default_na=False: nada se convierte solo. Los
            # tipos se aplican abajo, a mano y a propósito. Así un «NULL» de
            # texto llega al parquet como el texto que es, y el contrato decide
            # qué hacer con él en vez de que pandas lo decida por nosotros.
            df = pd.read_csv(path, encoding=encoding, dtype=str,
                             keep_default_na=False, na_filter=False)
            for col in ("precio", "latitud", "longitud"):
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            for col in ("folio", "cv_producto", "cv_marca"):
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
            df["fecha_registro"] = pd.to_datetime(
                df["fecha_registro"], format=formato_fecha, errors="coerce")

            df.to_parquet(destino, index=False)
            print(f"normalizado: {path.name} ({len(df):,} filas, {len(df.columns)} columnas)")
            hechos += 1
            del df
    if not hechos:
        print("(los 38 parquet ya existían; no se rehizo ninguno)")


# ── conexión y vista ────────────────────────────────────────────────────────
def conectar():
    con = duckdb.connect()
    con.sql("SET memory_limit='4GB'")      # bájalo si tu máquina/WSL tiene menos
    tmp = RAIZ / "tmp-duckdb"
    tmp.mkdir(parents=True, exist_ok=True)
    con.sql(f"SET temp_directory='{tmp}'")

    fuente = f"read_parquet('{PARQUETS}/*.parquet', union_by_name=true)"

    # Si mojibake.py ya corrió, se usan SUS sustituciones medidas. Si no, se
    # sigue adelante sin reparar y se avisa: mejor una tabla con la categoría
    # partida y un aviso, que una reparación inventada.
    dicc = SALIDA / "mojibake-diccionario.csv"
    if dicc.exists():
        con.sql(f"""CREATE OR REPLACE TABLE repara AS
                    SELECT columna, valor_roto, reparado
                    FROM read_csv('{dicc}')""")
        n = con.sql("SELECT count(*) FROM repara WHERE columna='categoria'").fetchone()[0]
        print(f"Diccionario de mojibake cargado: {n} sustitución/es para `categoria`.")
        categoria_limpia = "coalesce(r.reparado, f.categoria)"
        join = "LEFT JOIN repara r ON r.columna = 'categoria' AND r.valor_roto = f.categoria"
    else:
        print("AVISO: no encuentro mojibake-diccionario.csv — corre antes mojibake.py.")
        print("       Sin él, `art?culos deportivos` queda separada de `articulos")
        print("       deportivos` y su p99 se calcula con media muestra.")
        categoria_limpia = "f.categoria"
        join = ""

    con.sql(f"""
        CREATE VIEW qqp AS
        SELECT f.* EXCLUDE (categoria),
               {categoria_limpia}                        AS categoria,
               lower(strip_accents({categoria_limpia}))  AS categoria_norm
        FROM {fuente} f
        {join}
    """)
    return con


# ── mediciones ──────────────────────────────────────────────────────────────
def distribucion_por_categoria(con):
    return con.sql("""
        SELECT categoria_norm,
               min(precio) AS min,
               quantile_cont(precio, 0.25) AS p25,
               quantile_cont(precio, 0.5)  AS mediana,
               quantile_cont(precio, 0.75) AS p75,
               quantile_cont(precio, 0.95) AS p95,
               quantile_cont(precio, 0.99) AS p99,
               max(precio) AS max
        FROM qqp GROUP BY categoria_norm ORDER BY categoria_norm
    """).df()


def valores_imposibles(con):
    return con.sql("""
        SELECT sum((precio = 0)::INT), sum((precio < 0)::INT), sum(precio IS NULL)
        FROM qqp
    """).fetchone()


def por_que_el_p99_no_sirve(con):
    """Antes se llamaba sospechosos() y devolvía 0. Ahora dice POR QUÉ.

    No es que no hubiera datos malos: es que el umbral era inalcanzable. En una
    distribución de precios el p99 ya está pegado al máximo, así que pedir 10x
    el p99 es pedir algo que no pasa en ninguna categoría.
    """
    r = con.sql("""
        SELECT categoria_norm,
               quantile_cont(precio, 0.99) AS p99,
               max(precio) AS maximo,
               max(precio) / nullif(quantile_cont(precio, 0.99), 0) AS razon
        FROM qqp WHERE precio > 0
        GROUP BY categoria_norm ORDER BY razon DESC
    """).df()
    n = con.sql("""
        WITH p AS (SELECT categoria_norm, quantile_cont(precio,0.99) AS p99
                   FROM qqp GROUP BY categoria_norm)
        SELECT count(*) FROM qqp f JOIN p USING (categoria_norm)
        WHERE f.precio > p.p99 * 10
    """).fetchone()[0]
    return n, r


def duplicados_exactos(con):
    """Filas idénticas en todo salvo folio/cv_*, que sólo existen en 2 archivos."""
    return con.sql("""
        WITH grupos AS (
            SELECT * EXCLUDE (folio, cv_producto, cv_marca, categoria_norm),
                   count(*) AS n
            FROM qqp GROUP BY ALL
        )
        SELECT coalesce(sum(n - 1), 0) FROM grupos WHERE n > 1
    """).fetchone()[0]


def duplicados_por_origen(con):
    """¿Los duplicados son del mismo archivo o de dos quincenas distintas?

    Cambia la regla del contrato: dentro de un archivo es captura duplicada;
    entre dos, es solape de la fuente y se resuelve al ingerir, no al validar.
    """
    fuente = f"read_parquet('{PARQUETS}/*.parquet', union_by_name=true, filename=true)"
    return con.sql(f"""
        WITH g AS (
            SELECT producto, presentacion, marca, categoria, catalogo, precio,
                   fecha_registro, cadena_comercial, giro, nombre_comercial,
                   direccion, estado, municipio, latitud, longitud,
                   count(*) AS n, count(DISTINCT filename) AS archivos
            FROM {fuente} GROUP BY ALL
        )
        SELECT coalesce(sum(n - 1) FILTER (WHERE archivos = 1), 0) AS mismo_archivo,
               coalesce(sum(n - 1) FILTER (WHERE archivos > 1), 0) AS archivos_distintos
        FROM g WHERE n > 1
    """).fetchone()


def clave_candidata(con):
    """¿(producto, nombre_comercial, direccion, fecha_registro) es única?"""
    return con.sql("""
        WITH g AS (
            SELECT producto, nombre_comercial, direccion, fecha_registro,
                   count(*) AS n
            FROM qqp GROUP BY ALL
        )
        SELECT count(*) AS combinaciones,
               count(*) FILTER (WHERE n > 1) AS repetidas,
               coalesce(sum(n - 1) FILTER (WHERE n > 1), 0) AS filas_de_mas,
               max(n) AS peor_caso
        FROM g
    """).fetchone()


def cardinalidad(con):
    # concat() en vez de ||: con `||`, un NULL en cualquiera de los dos vuelve
    # NULL toda la expresión y la fila se cae del count(DISTINCT) sin avisar.
    return con.sql("""
        SELECT count(DISTINCT cadena_comercial),
               count(DISTINCT estado),
               count(DISTINCT lower(strip_accents(estado))),
               count(DISTINCT municipio),
               count(DISTINCT concat(nombre_comercial, '§', direccion))
        FROM qqp
    """).fetchone()


def columnas_ausentes(con):
    """Cuántas filas NO tienen folio/cv_producto/cv_marca, de verdad."""
    return con.sql("""
        SELECT count(*) AS filas,
               count(folio) AS con_folio,
               count(*) - count(folio) AS sin_folio,
               round((count(*) - count(folio)) * 100.0 / count(*), 2) AS pct
        FROM qqp
    """).df()


if __name__ == "__main__":
    rehacer = set()
    if "--rehacer-todo" in sys.argv:
        rehacer = {p.stem for p in PARQUETS.glob("*.parquet")}
    elif "--rehacer" in sys.argv:
        rehacer = set(sys.argv[sys.argv.index("--rehacer") + 1:])

    normalizar(rehacer)

    con = conectar()
    total = con.sql("SELECT count(*) FROM qqp").fetchone()[0]
    print(f"\n=== {total:,} filas (agregadas por DuckDB, nunca cargadas enteras a pandas) ===")

    print("\n=== Distribución de precio por categoría (acentos normalizados) ===")
    dist = distribucion_por_categoria(con)
    print(dist.round(2).to_string(index=False))
    print(f"\nCategorías tras normalizar: {len(dist)}")

    en_cero, negativos, nulos = valores_imposibles(con)
    print(f"\nEn cero: {en_cero:,} ({en_cero/total:.4%}) · Negativos: {negativos:,} · Nulos: {nulos:,}")

    n_sosp, razones = por_que_el_p99_no_sirve(con)
    peor = razones.iloc[0]
    print(f"\nRegla vieja «>10x el p99 de su categoría»: {n_sosp:,} sospechosos.")
    print(f"  Y no podía dar otra cosa: la razón máx/p99 más alta de todo el corpus")
    print(f"  es {peor.razon:.2f}x ({peor.categoria_norm}), y la regla pedía 10x.")
    print(f"  Categorías donde podía disparar: {(razones.razon > 10).sum()} de {len(razones)}.")
    print(f"  La detección que sí funciona está en centinelas.py.")

    n_dup = duplicados_exactos(con)
    print(f"\nDuplicados exactos (sin folio/cv_*): {n_dup:,} ({n_dup/total:.4%})")
    mismo, distintos = duplicados_por_origen(con)
    print(f"  del mismo archivo: {mismo:,} · entre archivos distintos: {distintos:,}")

    comb, rep, demas, peor_n = clave_candidata(con)
    print(f"\nClave candidata (producto, nombre_comercial, direccion, fecha_registro):")
    print(f"  combinaciones: {comb:,} · repetidas: {rep:,} · filas de más: {demas:,}"
          f" · peor caso: {peor_n:,}")
    if rep:
        print(f"  NO es única. Falta al menos `presentacion` y `marca` para serlo.")

    cadenas, ent_crudas, ent_norm, municipios, establecimientos = cardinalidad(con)
    print(f"\nCadenas: {cadenas:,} · Municipios: {municipios:,}")
    print(f"Entidades: {ent_crudas} literales → {ent_norm} reales")
    print(f"Establecimientos (nombre_comercial+dirección, proxy — confirmar con C2): "
          f"{establecimientos:,}")

    print("\n=== folio / cv_producto / cv_marca: el porcentaje real ===")
    print(columnas_ausentes(con).to_string(index=False))
    print("  «sin_folio» son filas cuyo archivo NO TRAE la columna. Eso no es")
    print("  un nulo del capturista: es una estructura distinta. El contrato")
    print("  tiene que aceptar las 15 obligatorias y avisar de las extra.")
