"""
¿Qué hay dentro de `Especial`? · para la reunión del 16/sep

Por qué existe este guión
-------------------------
`catalogos()` en medir-decisiones.py mostró que `Especial` trae 14,465 filas,
25 productos, precio mediano $46.9 y precio MÁXIMO $3,999. La mediana es más
baja que la de Pescados y Mariscos ($153), que sí entró al ADR 005. Por el
mismo criterio con el que se seleccionaron los cinco catálogos (mediana baja
= canasta básica), `Especial` calificaría — y no está en la lista.

Puede ser una omisión, o puede haber una razón real (el catálogo es un cajón
de sastre: unos pocos productos baratos aplastando la mediana mientras algo
caro -no necesariamente canasta básica- sube el máximo a 3,999, igual que
pasó con el $15,100 de Electrodomésticos). Este guión no decide; separa esas
dos posibilidades con datos, para que la decisión del miércoles se tome
mirando la lista de productos, no el resumen de una fila.

Uso
---
    python docs/datos/perfilado/revisar-catalogo-especial.py

Salidas
-------
    docs/datos/perfilado/salidas/especial-por-producto.csv
    docs/datos/perfilado/salidas/especial-solapa.csv
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
RECORTE = f"({FILTRO_SIETE}) AND {FILTRO_ANIO}"          # recorte territorial, igual que siempre

NORM_CAT = "trim(lower(strip_accents(catalogo)))"
NORM_PROD = "trim(lower(strip_accents(producto)))"

# Los cinco que el ADR 005 propone, para poder preguntar si algo de Especial
# ya vive ahí con otro nombre de catálogo.
CATALOGOS_ADR005 = [
    "basicos", "pacic", "frutas y legumbres", "mercados", "pescados y mariscos",
]
_lista = ", ".join(f"'{c}'" for c in CATALOGOS_ADR005)
FILTRO_DECIDIDOS = f"{NORM_CAT} IN ({_lista})"

FILTRO_ESPECIAL = f"{NORM_CAT} = 'especial'"
DENTRO_ESPECIAL = f"{RECORTE} AND {FILTRO_ESPECIAL}"

PRECIO = "CAST(precio AS DECIMAL(12,2))"    # ver verificar-precios.py: nunca restar como flotante


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


def perfil_general(con):
    """Tamaño de `Especial` dentro del recorte territorial: filas, productos,
    cuántas cadenas y establecimientos lo capturan, y en qué rango de fechas.
    """
    return con.sql(f"""
        SELECT count(*)                                       AS filas,
               count(DISTINCT producto)                       AS productos,
               count(DISTINCT (producto, presentacion))       AS articulos,
               count(DISTINCT cadena_comercial)                AS cadenas,
               count(DISTINCT (nombre_comercial, direccion))   AS establecimientos,
               min(fecha_registro)                             AS desde,
               max(fecha_registro)                             AS hasta
        FROM q WHERE {DENTRO_ESPECIAL}
    """).fetchone()


def por_producto(con):
    """Cada uno de los productos de `Especial`, con su propio rango de precio.

    La pregunta que contesta: la mediana de $46.9 del catálogo completo
    ¿es representativa de los 25 productos, o es un puñado de productos
    baratos aplastando el número mientras uno o dos -escondidos ahí- suben
    el máximo a 3,999? Ordenado por máximo descendente para que lo raro
    quede arriba.
    """
    return con.sql(f"""
        SELECT producto,
               count(*)                               AS filas,
               count(DISTINCT presentacion)            AS presentaciones,
               round(min({PRECIO}), 2)                AS minimo,
               round(median({PRECIO}), 2)              AS mediano,
               round(max({PRECIO}), 2)                AS maximo
        FROM q WHERE {DENTRO_ESPECIAL}
        GROUP BY 1
        ORDER BY maximo DESC
    """).df()


def filas_mas_caras(con, n=15):
    """Las quince filas de precio más alto dentro de Especial, con nombre,
    presentación, marca y establecimiento — para ver con los ojos qué es
    lo que cuesta $3,999, igual que se hizo con la colisión de $15,100.
    """
    return con.sql(f"""
        SELECT producto, presentacion, marca, cadena_comercial,
               round({PRECIO}, 2) AS precio, fecha_registro
        FROM q WHERE {DENTRO_ESPECIAL}
        ORDER BY precio DESC
        LIMIT {n}
    """).df()


def solapa_con_decididos(con):
    """¿Algún producto de `Especial` ya existe, con el mismo nombre, dentro
    de los cinco catálogos del ADR 005?

    Si "Tortilla de Maiz" aparece en Especial Y en Basicos, no son dos
    categorías: es el mismo producto capturado dos veces con un catálogo
    distinto, y eso hay que decidirlo como problema de captura, no de
    alcance.
    """
    return con.sql(f"""
        WITH especial AS (
            SELECT DISTINCT {NORM_PROD} AS producto_norm
            FROM q WHERE {DENTRO_ESPECIAL}
        ),
        decididos AS (
            SELECT DISTINCT {NORM_PROD} AS producto_norm, {NORM_CAT} AS catalogo
            FROM q WHERE {RECORTE} AND {FILTRO_DECIDIDOS}
        )
        SELECT especial.producto_norm AS producto, decididos.catalogo
        FROM especial JOIN decididos USING (producto_norm)
        ORDER BY 1
    """).df()


def comparar_contra_todos(con):
    """`Especial` en la misma tabla que los 16 catálogos, ordenada por
    mediana en vez de por filas.

    Existe porque la tabla original de `catalogos()` no explica el criterio
    de selección: aquí, ordenado por precio mediano, se ve de un vistazo si
    Especial (46.9) queda entre los cinco elegidos o se separa de ellos.
    """
    return con.sql(f"""
        SELECT {NORM_CAT}                            AS catalogo,
               count(*)                               AS filas,
               count(DISTINCT producto)                AS productos,
               round(median({PRECIO}), 2)             AS precio_mediano,
               round(quantile_cont({PRECIO}, 0.999),2) AS p999,
               round(max({PRECIO}), 2)                AS precio_maximo,
               ({FILTRO_DECIDIDOS})                    AS en_adr005
        FROM q WHERE {RECORTE}
        GROUP BY 1
        ORDER BY precio_mediano
    """).df()


if __name__ == "__main__":
    if not any(PARQUETS.glob("*.parquet")):
        raise SystemExit(f"No hay parquets en {PARQUETS}. Corre antes perfilado_nivel2.py")
    con = conectar()
    SALIDA.mkdir(parents=True, exist_ok=True)

    print("=" * 78)
    print("¿Dónde queda `Especial` frente a los criterios del ADR 005?")
    print("=" * 78)
    comp = comparar_contra_todos(con)
    print(comp.to_string(index=False))
    print("\n  Ordenado por precio_mediano. Si `especial` aparece intercalado")
    print("  entre catálogos que SÍ están en el ADR 005, el criterio de mediana")
    print("  no explica por qué se dejó fuera — hace falta otra razón, y hay que")
    print("  escribirla.")

    filas, prods, arts, cadenas, estabs, desde, hasta = perfil_general(con)
    print("\n── Tamaño de `Especial`")
    print(f"   filas                  : {filas:,}")
    print(f"   productos distintos    : {prods}")
    print(f"   artículos (prod+pres)  : {arts}")
    print(f"   cadenas comerciales    : {cadenas}")
    print(f"   establecimientos       : {estabs}")
    print(f"   rango de fechas        : {desde} a {hasta}")

    print("\n" + "=" * 78)
    print("Los 25 productos de `Especial`, uno por uno")
    print("=" * 78)
    pp = por_producto(con)
    pp.to_csv(SALIDA / "especial-por-producto.csv", index=False)
    print(pp.to_string(index=False))
    print("\n  Si la mayoría tiene máximo parecido a su mediana, el catálogo es")
    print("  parejo y genuinamente barato. Si uno o dos productos tienen máximo")
    print("  muy por encima de su propia mediana (no de la del catálogo), son")
    print("  ellos los que arrastran el 3,999 — y la decisión no es sobre el")
    print("  catálogo completo, es sobre esos productos.")

    print("\n" + "=" * 78)
    print("Las quince filas más caras dentro de `Especial`")
    print("=" * 78)
    print(filas_mas_caras(con).to_string(index=False))
    print("\n  Mira esto con los mismos ojos que el Centro de Lavado de $15,100:")
    print("  ¿es un producto de canasta básica con precio raro, o algo que nunca")
    print("  debió estar en un catálogo de precios básicos?")

    print("\n" + "=" * 78)
    print("¿Especial duplica productos que ya están en los 5 decididos?")
    print("=" * 78)
    sol = solapa_con_decididos(con)
    sol.to_csv(SALIDA / "especial-solapa.csv", index=False)
    if sol.empty:
        print("  Ningún producto de Especial coincide por nombre con los cinco")
        print("  catálogos del ADR 005. Es un catálogo aparte, no una duplicación.")
    else:
        print(sol.to_string(index=False))
        print(f"\n  {sol.producto.nunique()} producto(s) de Especial ya aparecen en otro")
        print("  catálogo decidido. Para esos, ingerir Especial sería contar el")
        print("  mismo artículo dos veces bajo dos categorías.")

    print("\n" + "=" * 78)
    print("Qué mirar antes de decidir")
    print("=" * 78)
    print("  · Si la tabla por producto sale pareja (máximos cercanos a sus")
    print("    medianas) y sin solape -> Especial es candidato legítimo al ADR 005,")
    print("    y probablemente se omitió sin querer.")
    print("  · Si uno o dos productos concentran los precios altos -> la pregunta")
    print("    no es \"¿Especial sí o no?\", es \"¿qué hacemos con esos productos")
    print("    puntuales?\" (excluirlos, o mandarlos a cuarentena por precio como")
    print("    ya se hace con las colisiones).")
    print("  · Si hay solape con los cinco decididos -> hay que decidir cuál")
    print("    catálogo manda para ese producto antes de sumar filas.")
