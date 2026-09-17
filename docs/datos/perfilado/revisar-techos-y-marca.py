"""
Dos preguntas abiertas antes de la reunión del 16/sep

1. `maximo_por_catalogo` se calculó como max_observado * 1.25. Nunca vimos
   qué producto específico pone ese máximo en cada catálogo -la misma
   pregunta que resolvimos para `Especial` (mercancía de campaña, no
   canasta básica) pero para los cinco catálogos que sí quedan dentro.

2. `normalizacion.marca.colapsa: {"S/m": "S/M"}` asume que las "2 formas
   distintas de escribirlo" que reportó medir-decisiones.py son una
   diferencia de mayúsculas. Nunca se vieron los literales crudos, y esa
   cifra (37.40%) está medida sobre el recorte territorial, no sobre el
   alcance del contrato.

Este guión no asume nada de lo anterior: lo mide.

Uso
---
    python docs/datos/perfilado/revisar-techos-y-marca.py

Salidas
-------
    docs/datos/perfilado/salidas/techo-por-producto.csv
    docs/datos/perfilado/salidas/marca-normalizada.csv
"""
import os
from pathlib import Path

import duckdb

RAIZ = Path(os.environ.get("CANASTAMX_DATOS", Path.home() / "canastamx-datos"))
PARQUETS = RAIZ / "procesado" / "por_archivo"
SALIDA = Path("docs/datos/perfilado/salidas")

SIETE = [
    "aguascalientes", "guanajuato", "jalisco", "michoacan",
    "queretaro", "san luis potosi", "zacatecas",
]
ANIOS = (2025, 2026)

NORM_EDO = "trim(lower(strip_accents(estado)))"
FILTRO_SIETE = " OR ".join(f"{NORM_EDO} LIKE '{e}%'" for e in SIETE)
FILTRO_ANIO = f"year(fecha_registro) BETWEEN {ANIOS[0]} AND {ANIOS[1]}"
RECORTE = f"({FILTRO_SIETE}) AND {FILTRO_ANIO}"

NORM_CAT = "trim(lower(strip_accents(catalogo)))"
CATALOGOS_ADR005 = [
    "basicos", "pacic", "frutas y legumbres", "mercados", "pescados y mariscos",
]
_lista = ", ".join(f"'{c}'" for c in CATALOGOS_ADR005)
FILTRO_CATALOGO = f"{NORM_CAT} IN ({_lista})"
ALCANCE = f"{RECORTE} AND {FILTRO_CATALOGO}"     # el alcance del contrato, no el territorial

PRECIO = "CAST(precio AS DECIMAL(12,2))"


def conectar():
    con = duckdb.connect()
    con.sql("SET memory_limit='4GB'")
    tmp = RAIZ / "tmp-duckdb"
    tmp.mkdir(parents=True, exist_ok=True)
    con.sql(f"SET temp_directory='{tmp}'")
    con.sql(f"""
        CREATE VIEW q AS
        SELECT * FROM read_parquet('{PARQUETS}/*.parquet', union_by_name=true)
    """)
    return con


# ── 1. Qué producto fija cada techo de `maximo_por_catalogo` ────────────────

def top_precios_por_catalogo(con, n=5):
    """Las `n` filas de precio más alto de cada uno de los cinco catálogos.

    Si la fila que fija el techo es un producto que de verdad pertenece al
    catálogo (un pescado, no una fila mal etiquetada), el techo está bien
    anclado. Si es rara -presentación truncada, marca vacía donde no
    debería, producto que no encaja-, el `maximo_por_catalogo` hereda ese
    error antes de que exista un solo dato nuevo.
    """
    return con.sql(f"""
        WITH rankeado AS (
            SELECT {NORM_CAT}   AS catalogo,
                   producto, presentacion, marca, cadena_comercial,
                   round({PRECIO}, 2) AS precio,
                   fecha_registro,
                   row_number() OVER (
                       PARTITION BY {NORM_CAT} ORDER BY {PRECIO} DESC
                   ) AS puesto
            FROM q WHERE {ALCANCE}
        )
        SELECT * EXCLUDE (puesto) FROM rankeado WHERE puesto <= {n}
        ORDER BY catalogo, precio DESC
    """).df()


def productos_cerca_del_techo(con, margen=0.20):
    """Dentro de cada catálogo, qué productos tienen SU propio máximo dentro
    del `margen` superior del máximo del catálogo.

    Si el máximo de un catálogo es un solo producto aislado y nada más se le
    acerca, es una cola solitaria -el mismo patrón que el $15,100 de
    Electrodomésticos, pero dentro de un catálogo que sí está en el ADR 005-.
    Si varios productos parecidos están ahí arriba, el techo refleja al
    catálogo completo, no a una fila.
    """
    return con.sql(f"""
        WITH por_producto AS (
            SELECT {NORM_CAT} AS catalogo, producto,
                   max({PRECIO}) AS max_producto, count(*) AS filas
            FROM q WHERE {ALCANCE}
            GROUP BY 1, 2
        ),
        techo AS (
            SELECT catalogo, max(max_producto) AS techo_catalogo
            FROM por_producto GROUP BY 1
        )
        SELECT pp.catalogo, pp.producto, pp.max_producto, pp.filas
        FROM por_producto pp
        JOIN techo t USING (catalogo)
        WHERE pp.max_producto >= t.techo_catalogo * (1 - {margen})
        ORDER BY pp.catalogo, pp.max_producto DESC
    """).df()


# ── 2. Qué hay realmente detrás de S/M ───────────────────────────────────────

def resumen_marca_normalizada(con, top=10):
    """Agrupa `marca` dos veces: por su literal crudo (tal cual viene de la
    fuente) y por su forma normalizada (mayúsculas, sin acentos). Muestra,
    para cada forma normalizada, cuántos literales crudos distintos la
    alimentan y un ejemplo de cada uno.

    Si la fila de "S/M" (o lo que sea que salga arriba) trae
    `literales_crudos = 1`, la normalización de mayúsculas ya resuelve el
    problema sola y el `colapsa` del yaml no hace nada. Si trae más de 1,
    el mapa es necesario -y sus llaves deben ser EXACTAMENTE los literales
    de la columna `ejemplos_crudos`, no una suposición de que es solo un
    cambio de mayúsculas.
    """
    return con.sql(f"""
        WITH crudos AS (
            SELECT marca,
                   upper(trim(strip_accents(marca))) AS marca_normalizada,
                   count(*) AS filas
            FROM q WHERE {ALCANCE}
            GROUP BY marca
        ),
        total AS (SELECT sum(filas) AS n FROM crudos)
        SELECT marca_normalizada,
               count(*)                              AS literales_crudos,
               list(marca)                            AS ejemplos_crudos,
               sum(filas)                             AS filas,
               round(100.0 * sum(filas) / (SELECT n FROM total), 2) AS pct
        FROM crudos
        GROUP BY marca_normalizada
        ORDER BY filas DESC
        LIMIT {top}
    """).df()


def nulos_y_vacios_de_marca(con):
    """`marca` está declarada `obligatoria: true, nulos_permitidos: false`.
    Si "no declara marca" siempre se representa con el literal S/M (o su
    variante), esto debe dar cero en ambas columnas -confirma que ADR 002
    punto 3 se cumple en los datos, no solo en el papel.
    """
    return con.sql(f"""
        SELECT count(*) FILTER (WHERE marca IS NULL)   AS nulos,
               count(*) FILTER (WHERE trim(marca) = '') AS vacios
        FROM q WHERE {ALCANCE}
    """).fetchone()


if __name__ == "__main__":
    if not any(PARQUETS.glob("*.parquet")):
        raise SystemExit(f"No hay parquets en {PARQUETS}. Corre antes perfilado_nivel2.py")
    con = conectar()
    SALIDA.mkdir(parents=True, exist_ok=True)

    print("=" * 78)
    print("1 · Qué producto fija cada techo de `maximo_por_catalogo`")
    print("=" * 78)
    tp = top_precios_por_catalogo(con)
    tp.to_csv(SALIDA / "techo-por-producto.csv", index=False)
    print(tp.to_string(index=False))
    print("\n  Si el producto en el primer lugar de cada catálogo pertenece de")
    print("  verdad ahí, el techo está bien anclado. Si algo se ve fuera de")
    print("  lugar, revísalo con los mismos ojos que el Centro de Lavado.")

    print("\n── Qué tan solo está el máximo de cada catálogo")
    pc = productos_cerca_del_techo(con)
    print(pc.to_string(index=False))
    print("\n  Si un catálogo aparece con un solo renglón aquí, su techo depende")
    print("  de un único producto -vale la pena mirarlo antes del miércoles-.")
    print("  Si aparecen varios, el techo refleja al catálogo, no a una fila.")

    print("\n" + "=" * 78)
    print("2 · Qué hay detrás de `S/M` -y si el `colapsa` del yaml basta-")
    print("=" * 78)
    rmn = resumen_marca_normalizada(con)
    rmn.to_csv(SALIDA / "marca-normalizada.csv", index=False)
    print(rmn.to_string(index=False))
    print("\n  Busca la fila que corresponde a "'"'"sin marca"'"'". Si su")
    print("  `literales_crudos` es 1, el `colapsa` del yaml no hace nada útil.")
    print("  Si es 2 o más, copia los literales exactos de `ejemplos_crudos`")
    print("  a las llaves de `colapsa` -no textos parecidos, los exactos-.")
    print("  El `pct` de esa fila es el número que reemplaza al 37.40% del")
    print("  yaml, medido sobre el alcance real y no sobre el territorial.")

    nulos, vacios = nulos_y_vacios_de_marca(con)
    print(f"\n── marca IS NULL: {nulos}  ·  marca = '' (vacío): {vacios}")
    if nulos or vacios:
        print("  El yaml declara `nulos_permitidos: false` para `marca`. Si esto")
        print("  no da cero, hay filas que violan el contrato hoy mismo, antes")
        print("  de tocar nada de S/M.")
    else:
        print("  En cero. ADR 002 punto 3 se cumple: \"no marca\" siempre llega")
        print("  como un literal, nunca como ausencia de dato.")

    print("\n" + "=" * 78)
    print("Qué hacer con esto")
    print("=" * 78)
    print("  · El `colapsa` del yaml se reescribe con los literales exactos de")
    print("    `ejemplos_crudos`, y se fija el orden: colapsa corre sobre el")
    print("    valor CRUDO, antes de `mayusculas_sin_acentos` -o se elimina si")
    print("    `literales_crudos` da 1 y la normalización ya basta sola-.")
    print("  · El % de S/M en el yaml se reemplaza por el medido aquí sobre el")
    print("    alcance, con nota de que el 37.40% original era territorial.")
    print("  · Si algún catálogo del ADR 005 depende de un solo producto para")
    print("    su techo, se anota esa dependencia en `razon_del_techo`.")
