"""
H3 · ¿hay problema de reconciliación ENTRE CADENAS? · QQP

Por qué hace falta este guión
-----------------------------
H3 está enunciada así en el cronograma:

    «Cobertura y precisión de la normalización de nombres ENTRE CADENAS.
     Cobertura ≥ 85%, precisión ≥ 90% sobre 200 pares»

Y la ficha de T005 explica la premisa: «Cuatro cadenas, cuatro escrituras, un
producto. Sin reconciliar, comparar precios entre cadenas es imposible.»

`perfilado_nivel3.py` midió la variación de escritura en TODO el corpus junto
—1.29 variantes por artículo— pero eso no es exactamente lo que H3 pide. H3
pregunta algo más específico: **¿Walmart y Soriana escriben distinto el mismo
producto?** Puede haber mucha variación en el corpus y ninguna entre cadenas, o
al revés. Hay que medirlo aparte.

Qué mide
--------
1. De los productos que aparecen en DOS O MÁS cadenas, ¿en cuántos las cadenas
   usan escrituras distintas? Ése es el tamaño real del problema de H3.
2. Cuántos PARES se pueden formar: mismo artículo, dos cadenas distintas,
   escritura distinta. H3 pide 200. Si no salen 200, eso ya es el resultado.
3. Una muestra de esos pares, para poder verlos.

Uso
---
    python docs/datos/perfilado/h3-entre-cadenas.py
    CANASTAMX_DATOS=/otra/ruta python docs/datos/perfilado/h3-entre-cadenas.py
"""
import os
from pathlib import Path

import duckdb

RAIZ = Path(os.environ.get("CANASTAMX_DATOS", Path.home() / "canastamx-datos"))
PARQUETS = RAIZ / "procesado" / "por_archivo"
SALIDA = Path("docs/datos/perfilado")

PARES_QUE_PIDE_H3 = 200

# La misma normalización que perfilado_nivel3.py, para que las cifras sean
# comparables entre los dos guiones.
NORM = ("trim(regexp_replace(regexp_replace(lower(strip_accents({0})), "
        "'[^a-z0-9 ]', ' ', 'g'), '\\s+', ' ', 'g'))")


def conectar():
    con = duckdb.connect()
    con.sql("SET memory_limit='4GB'")
    tmp = RAIZ / "tmp-duckdb"
    tmp.mkdir(parents=True, exist_ok=True)
    con.sql(f"SET temp_directory='{tmp}'")
    fuente = f"read_parquet('{PARQUETS}/*.parquet', union_by_name=true)"
    con.sql(f"""
        CREATE VIEW q AS
        SELECT producto, presentacion, marca, cadena_comercial,
               {NORM.format('producto')}     AS prod_n,
               {NORM.format('presentacion')} AS pres_n,
               {NORM.format('marca')}        AS marca_n
        FROM {fuente}
        WHERE producto NOT LIKE '%?%'
          AND presentacion NOT LIKE '%?%'
          AND marca NOT LIKE '%?%'
    """)
    return con


def por_producto(con):
    """De los productos presentes en 2+ cadenas, ¿cuántos se escriben distinto?"""
    return con.sql("""
        WITH g AS (
            SELECT prod_n,
                   count(DISTINCT cadena_comercial) AS cadenas,
                   count(DISTINCT producto)         AS literales,
                   count(*)                         AS filas
            FROM q GROUP BY prod_n
        )
        SELECT count(*)                                        AS productos,
               count(*) FILTER (WHERE cadenas >= 2)            AS en_2_o_mas_cadenas,
               count(*) FILTER (WHERE cadenas >= 2 AND literales > 1)
                                                               AS escritos_distinto,
               max(cadenas)                                    AS max_cadenas,
               max(literales)                                  AS max_literales
        FROM g
    """).fetchone()


def por_articulo(con):
    """Lo mismo, pero sobre el artículo completo: producto + presentacion + marca."""
    return con.sql("""
        WITH g AS (
            SELECT prod_n || '§' || pres_n || '§' || marca_n AS clave,
                   count(DISTINCT cadena_comercial) AS cadenas,
                   count(DISTINCT producto || '§' || presentacion || '§' || marca)
                                                    AS literales
            FROM q GROUP BY 1
        )
        SELECT count(*)                                  AS articulos,
               count(*) FILTER (WHERE cadenas >= 2)      AS en_2_o_mas_cadenas,
               count(*) FILTER (WHERE cadenas >= 2 AND literales > 1)
                                                         AS escritos_distinto
        FROM g
    """).fetchone()


def armar_pares(con):
    """Los pares que H3 necesita: mismo artículo, dos cadenas, escrituras distintas."""
    return con.sql("""
        WITH lit AS (
            SELECT prod_n || '§' || pres_n || '§' || marca_n AS clave,
                   producto || ' · ' || presentacion || ' · ' || marca AS literal,
                   cadena_comercial,
                   count(*) AS filas
            FROM q GROUP BY 1, 2, 3
        )
        SELECT a.clave,
               a.cadena_comercial AS cadena_a, a.literal AS escritura_a,
               b.cadena_comercial AS cadena_b, b.literal AS escritura_b
        FROM lit a JOIN lit b
          ON a.clave = b.clave
         AND a.cadena_comercial < b.cadena_comercial   -- cada par una sola vez
         AND a.literal <> b.literal                    -- y sólo si se escriben distinto
        ORDER BY a.filas + b.filas DESC
    """).df()


def cadenas_grandes(con, n=8):
    """Las cadenas con más filas, para tener a quién señalar en la reunión."""
    return con.sql(f"""
        SELECT cadena_comercial, count(*) AS filas,
               count(DISTINCT producto) AS productos_distintos
        FROM q GROUP BY 1 ORDER BY filas DESC LIMIT {n}
    """).df()


if __name__ == "__main__":
    if not any(PARQUETS.glob("*.parquet")):
        raise SystemExit(f"No hay parquets en {PARQUETS}. Corre antes perfilado_nivel2.py")
    con = conectar()
    total = con.sql("SELECT count(*) FROM q").fetchone()[0]
    print("=" * 78)
    print(f"H3 · ¿las cadenas escriben distinto el mismo producto? · {total:,} filas")
    print("=" * 78)

    print("\n── Las cadenas más grandes")
    print(cadenas_grandes(con).to_string(index=False))

    prods, en2, distinto, maxc, maxl = por_producto(con)
    print(f"\n── Al nivel de `producto`")
    print(f"   productos distintos                        : {prods:,}")
    print(f"   presentes en 2 o más cadenas               : {en2:,} ({en2/prods:.1%})")
    print(f"   de ésos, ESCRITOS DISTINTO entre cadenas   : {distinto:,} "
          f"({distinto/max(en2,1):.1%})")
    print(f"   producto presente en más cadenas           : {maxc} cadenas")
    print(f"   máximo de escrituras de un mismo producto  : {maxl}")

    arts, aen2, adist = por_articulo(con)
    print(f"\n── Al nivel de artículo (producto + presentacion + marca)")
    print(f"   artículos distintos                        : {arts:,}")
    print(f"   presentes en 2 o más cadenas               : {aen2:,} ({aen2/arts:.1%})")
    print(f"   de ésos, ESCRITOS DISTINTO entre cadenas   : {adist:,} "
          f"({adist/max(aen2,1):.1%})")

    print("\n" + "=" * 78)
    print(f"Los pares que H3 pide ({PARES_QUE_PIDE_H3})")
    print("=" * 78)
    pares = armar_pares(con)
    print(f"  Pares formables (mismo artículo, dos cadenas, escritura distinta): "
          f"{len(pares):,}")

    if len(pares) < PARES_QUE_PIDE_H3:
        print(f"\n  SON MENOS DE {PARES_QUE_PIDE_H3}. Eso NO es un fallo de la medición:")
        print("  es el resultado. Quiere decir que en esta fuente el problema que")
        print("  H3 describe —cada cadena escribe el producto a su manera— casi no")
        print("  existe, porque PROFECO captura con su propio catálogo y no con el")
        print("  texto que pone cada tienda.")
        print("\n  H3 no se puede medir como está enunciada. Hay que decidir en la")
        print("  reunión si se declara satisfecha con evidencia, si se reenuncia")
        print("  sobre otro eje, o si se guarda para cuando entre una segunda fuente.")
    else:
        print(f"\n  Hay material suficiente para la prueba de H3.")

    if not pares.empty:
        print("\n  Muestra de pares (los de más volumen):")
        for _, f in pares.head(10).iterrows():
            print(f"\n    {f.cadena_a:<28} → {f.escritura_a}")
            print(f"    {f.cadena_b:<28} → {f.escritura_b}")
        SALIDA.mkdir(parents=True, exist_ok=True)
        destino = SALIDA / "h3-pares-entre-cadenas.csv"
        pares.to_csv(destino, index=False)
        print(f"\n  Todos en {destino}")

    print("\n" + "=" * 78)
    print("Cómo leer esto en la reunión")
    print("=" * 78)
    print("  Si «escritos distinto entre cadenas» es bajo, la fuente ya viene")
    print("  reconciliada: PROFECO no deja que cada tienda escriba el nombre.")
    print("  Eso es BUENA noticia para el producto y una MALA pregunta para H3,")
    print("  porque H3 mide la solución a un problema que esta fuente no tiene.")
    print("\n  No es un fracaso: es un hallazgo, y llegó en septiembre, que es")
    print("  cuando todavía se puede reenunciar la hipótesis sin costo.")
