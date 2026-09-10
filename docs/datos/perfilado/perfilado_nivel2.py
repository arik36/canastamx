"""
Perfilado nivel 2 · QQP (T004)
Depende de T003. Cada CSV se normaliza a su propio parquet (uno a la vez,
sin saturar RAM); DuckDB agrega los 38 parquets sin juntarlos nunca en un
solo DataFrame de pandas.
"""

import pandas as pd
import duckdb
from pathlib import Path

CRUDO = Path.home() / "canastamx-datos" / "crudo"
CARPETAS = [CRUDO / "QQP_2025", CRUDO / "QQP_2026"]
PARQUETS = Path.home() / "canastamx-datos" / "procesado" / "por_archivo"
ATIPICOS_MAYO_2026 = {"05-2026_Q1.csv", "05-2026_Q2.csv"}


def normalizar():
    PARQUETS.mkdir(parents=True, exist_ok=True)
    for carpeta in CARPETAS:
        for path in sorted(carpeta.glob("*.csv")):
            destino = PARQUETS / f"{path.stem}.parquet"
            if destino.exists():
                continue
            atipico = path.name in ATIPICOS_MAYO_2026
            encoding = "latin-1" if atipico else "utf-8-sig"
            formato_fecha = "%d/%m/%Y" if atipico else "%Y/%m/%d"

            df = pd.read_csv(path, encoding=encoding, low_memory=False)
            df["fecha_registro"] = pd.to_datetime(
                df["fecha_registro"], format=formato_fecha, errors="coerce"
            )
            df.to_parquet(destino, index=False)
            print(f"normalizado: {path.name} ({len(df):,} filas)")
            del df


def conectar():
    con = duckdb.connect()
    con.sql("SET memory_limit='4GB'")  # bájalo si tu máquina/WSL tiene menos
    fuente = f"read_parquet('{PARQUETS}/*.parquet', union_by_name=true)"
    # Vista con categoria sin acentos. El '?' de mojibake (Art?culos) queda
    # SIN tocar a propósito hasta ver qué dice diagnostico.py — no adivinar.
    con.sql(f"""
        CREATE VIEW qqp AS
        SELECT *, lower(replace(replace(replace(replace(replace(
                   categoria,'á','a'),'é','e'),'í','i'),'ó','o'),'ú','u')) AS categoria_norm
        FROM {fuente}
    """)
    return con


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
    en_cero, negativos, nulos = con.sql("""
        SELECT sum((precio = 0)::INT), sum((precio < 0)::INT), sum(precio IS NULL)
        FROM qqp
    """).fetchone()
    return en_cero, negativos, nulos


def sospechosos(con):
    # mismo categoria_norm que la distribución: si no, el umbral p99 se
    # calcula sobre la categoría partida por acento, con menos muestra
    return con.sql("""
        WITH p99_cat AS (
            SELECT categoria_norm, quantile_cont(precio, 0.99) AS p99
            FROM qqp GROUP BY categoria_norm
        )
        SELECT count(*) FROM qqp f
        JOIN p99_cat p USING (categoria_norm)
        WHERE f.precio > p.p99 * 10
    """).fetchone()[0]


def duplicados_exactos(con):
    # excluye folio/cv_producto/cv_marca — según T003 no está confirmado
    # que estén en los 38 archivos (correr diagnostico.py primero)
    return con.sql("""
        WITH grupos AS (
            SELECT * EXCLUDE (folio, cv_producto, cv_marca), count(*) AS n
            FROM qqp GROUP BY ALL
        )
        SELECT coalesce(sum(n - 1), 0) FROM grupos WHERE n > 1
    """).fetchone()[0]


def cardinalidad(con):
    return con.sql("""
        SELECT count(DISTINCT cadena_comercial),
               count(DISTINCT estado),
               count(DISTINCT municipio),
               count(DISTINCT nombre_comercial || '§' || direccion)
        FROM qqp
    """).fetchone()


if __name__ == "__main__":
    if not any(PARQUETS.glob("*.parquet")):
        normalizar()

    con = conectar()
    total = con.sql("SELECT count(*) FROM qqp").fetchone()[0]
    print(f"\n=== {total:,} filas (agregadas por DuckDB, nunca cargadas enteras a pandas) ===")

    print("\n=== Distribución de precio por categoría (acentos normalizados) ===")
    print(distribucion_por_categoria(con).round(2).to_string(index=False))

    en_cero, negativos, nulos = valores_imposibles(con)
    print(f"\nEn cero: {en_cero:,} ({en_cero/total:.4%}) · Negativos: {negativos:,} · Nulos: {nulos:,}")

    n_sosp = sospechosos(con)
    print(f"Sospechosos (>10x p99 de su categoría): {n_sosp:,}")

    n_dup = duplicados_exactos(con)
    print(f"Duplicados exactos (sin folio/cv_*): {n_dup:,} ({n_dup/total:.4%})")

    cadenas, entidades, municipios, establecimientos = cardinalidad(con)
    print(f"\nCadenas: {cadenas:,} · Entidades: {entidades:,} · Municipios: {municipios:,}")
    print(f"Establecimientos (nombre_comercial+dirección, proxy — confirmar con C2): {establecimientos:,}")
