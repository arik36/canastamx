"""
Lo que falta medir antes de cerrar el campo `precio` del contrato · QQP

Por qué existe este guión
-------------------------
`medir-decisiones.py` mide las colisiones de la clave de fila sobre el recorte
TERRITORIAL (siete entidades, 2025-2026) — los 4,384,962. Pero el contrato
declara un alcance más chico: los cinco catálogos del ADR 005. Son 2,658,906
filas, el 61% de lo medido.

Eso importa para tres campos del yaml que hoy están puestos con números de la
población equivocada:

  · `clave_de_fila.colisiones_conocidas: 77670`  ← medido sobre 16 catálogos
  · el desglose 94.8% / 4.5% / 0.6% de `que_se_hace`
  · `precio.maximo: 1775`, que sí sale de los cinco, pero está marcado REVISAR

Y contesta la pregunta del outlier de $15,100 sin suponer nada: imprime a qué
catálogo pertenece cada colisión extrema. Si cae en Electrodomésticos o
Juguetes, no es error de captura: es un artículo que el contrato ni siquiera
ingiere.

Uso
---
    python docs/datos/perfilado/verificar-precios.py
    CANASTAMX_DATOS=/otra/ruta python docs/datos/perfilado/verificar-precios.py

Si se prefiere en una sola pasada, las funciones se pegan en
`medir-decisiones.py` después de `siguen_chocando()`, y los bloques de
impresión después de la sección 6.

Salidas
-------
    docs/datos/perfilado/salidas/precio-por-catalogo.csv
    docs/datos/perfilado/salidas/colisiones-extremas.csv
    docs/datos/perfilado/salidas/techo-candidato.csv
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

# ── Lo nuevo ────────────────────────────────────────────────────────────────

# Los cinco catálogos que el ADR 005 propone (por ratificar el 16/sep). Se
# comparan YA NORMALIZADOS porque la fuente escribe `Basicos` y `Básicos` como
# dos literales del mismo catálogo, igual que `Pacic` y `PACIC`. Si se filtrara
# por el literal crudo se perderían 121,491 filas de Básicos y 8,704 de PACIC
# sin que nada avise.
CATALOGOS_ADR005 = [
    "basicos", "pacic", "frutas y legumbres", "mercados", "pescados y mariscos",
]
NORM_CAT = "trim(lower(strip_accents(catalogo)))"
_lista = ", ".join(f"'{c}'" for c in CATALOGOS_ADR005)
FILTRO_CATALOGO = f"{NORM_CAT} IN ({_lista})"
ALCANCE = f"{RECORTE} AND {FILTRO_CATALOGO}"

# El contrato declara `precio` como decimal. La medición tiene que respetarlo:
# con `precio` en DOUBLE, una diferencia real de $1.00 puede salir 0.99999999 y
# caer del lado equivocado de la frontera del bucket — y el bucket decide si la
# fila se deduplica o se conserva. Se castea antes de restar.
PRECIO = "CAST(precio AS DECIMAL(12,2))"

# Techos candidatos para cerrar el REVISAR de `precio.maximo`.
TECHOS = {
    "1775 · el máximo exacto medido": 1775,
    "2000 · redondeado hacia arriba": 2000,
    "2041 · el medido +15%": 1775 * 1.15,
    "2663 · el medido +50%": 1775 * 1.50,
}

CLAVE_FILA = ("producto, presentacion, marca, nombre_comercial, "
              "direccion, fecha_registro")


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


def alcance_real(con):
    """Cuánto del recorte territorial entra de verdad al contrato.

    Es el número que faltaba para leer bien todo lo demás: las 77,670
    colisiones están medidas sobre el recorte completo, no sobre esto.
    """
    return con.sql(f"""
        SELECT count(*)                                        AS recorte,
               count(*) FILTER (WHERE {FILTRO_CATALOGO})       AS en_alcance,
               count(*) FILTER (WHERE NOT ({FILTRO_CATALOGO})) AS fuera
        FROM q WHERE {RECORTE}
    """).fetchone()


def salud_de_precio(con):
    """Los tres supuestos que el yaml declara sobre `precio`, contados.

    `nulos_permitidos: false` y `minimo: 0.01` hoy están puestos citando
    perfilado.md §2, que midió sobre otra población. Aquí se recuentan dentro
    del alcance, y de paso se buscan los negativos y los ceros, que son el
    error espejo del «cero de más»: un punto decimal corrido al otro lado.
    """
    return con.sql(f"""
        SELECT count(*)                                      AS filas,
               count(*) FILTER (WHERE precio IS NULL)         AS nulos,
               count(*) FILTER (WHERE {PRECIO} = 0)           AS ceros,
               count(*) FILTER (WHERE {PRECIO} < 0)           AS negativos,
               count(*) FILTER (WHERE {PRECIO} < 0.01
                                 AND precio IS NOT NULL)      AS bajo_minimo
        FROM q WHERE {ALCANCE}
    """).fetchone()


def precio_por_catalogo(con):
    """Perfil de precio de los cinco catálogos, ya normalizados.

    El yaml pone `maximo: 1775` y lo marca REVISAR. La pregunta que contesta
    esta tabla es si 1775 es un techo representativo o la cola de un solo
    catálogo: Pescados y Mariscos es perecedero y estacional, Basicos no.
    Los percentiles dicen a qué distancia está el máximo del cuerpo de la
    distribución — si p999 son 600 y el máximo 1775, el máximo es un caso
    aislado y no la frontera natural del catálogo.
    """
    return con.sql(f"""
        SELECT {NORM_CAT}                                  AS catalogo,
               count(*)                                    AS filas,
               round(min({PRECIO}), 2)                     AS minimo,
               round(median({PRECIO}), 2)                  AS mediano,
               round(quantile_cont({PRECIO}, 0.99), 2)     AS p99,
               round(quantile_cont({PRECIO}, 0.999), 2)    AS p999,
               round(max({PRECIO}), 2)                     AS maximo
        FROM q WHERE {ALCANCE}
        GROUP BY 1
        ORDER BY maximo DESC
    """).df()


def techo_candidato(con):
    """Cuántas filas legítimas rechazaría cada techo posible.

    Cierra el REVISAR con un número en vez de una preferencia. La ventana del
    contrato está abierta (`hasta: null`), así que el techo no sólo tiene que
    cubrir lo medido: tiene que aguantar las quincenas que faltan.
    """
    casos = ",\n".join(
        f"count(*) FILTER (WHERE {PRECIO} > {v}) AS \"{k}\""
        for k, v in TECHOS.items()
    )
    return con.sql(f"SELECT {casos} FROM q WHERE {ALCANCE}").df().T.rename(
        columns={0: "filas_que_rechaza"}
    )


def maximo_por_mes(con):
    """El máximo de cada catálogo, mes a mes.

    Si 1775 aparece una sola vez en 19 meses, es un caso aislado y el techo
    no debe calibrarse con él. Si el máximo mensual sube con el tiempo, es
    inflación y un techo fijo va a empezar a rechazar datos buenos solo.
    """
    return con.sql(f"""
        SELECT strftime(fecha_registro, '%Y-%m')  AS mes,
               {NORM_CAT}                         AS catalogo,
               round(max({PRECIO}), 2)            AS maximo
        FROM q WHERE {ALCANCE}
        GROUP BY 1, 2
        ORDER BY maximo DESC
        LIMIT 15
    """).df()


def colisiones_en_alcance(con):
    """Los tres buckets del yaml, pero medidos sobre lo que el contrato ingiere.

    Es `siguen_chocando()` con el filtro de catálogo puesto y el precio
    casteado a decimal. El resultado es el número que debe ir en
    `clave_de_fila.colisiones_conocidas`, y los porcentajes que deben ir en
    `que_se_hace`. Los de hoy salen de una población 65% más grande.
    """
    return con.sql(f"""
        WITH grupos AS (
            SELECT count(*)                            AS filas,
                   max({PRECIO}) - min({PRECIO})       AS diferencia
            FROM q WHERE {ALCANCE}
            GROUP BY {CLAVE_FILA}
            HAVING count(*) > 1
        )
        SELECT CASE WHEN diferencia < 1   THEN 'de centavos'
                    WHEN diferencia <= 50 THEN 'de $1 a $50'
                    ELSE                       'de más de $50'
               END                        AS clase,
               count(*)                   AS grupos,
               sum(filas - 1)             AS filas_sobrantes,
               round(avg(diferencia), 2)  AS diferencia_promedio,
               round(max(diferencia), 2)  AS diferencia_maxima
        FROM grupos
        GROUP BY 1
        ORDER BY CASE clase WHEN 'de centavos' THEN 1
                            WHEN 'de $1 a $50' THEN 2
                            ELSE 3 END
    """).df()


def extremos_por_catalogo(con):
    """El bucket de «más de $50», abierto por catálogo y por dentro/fuera.

    Contesta de una vez la pregunta del $15,100: si las diferencias enormes
    viven en Electrodomésticos y Juguetes, no son errores de captura — son
    artículos que el contrato no ingiere, y el promedio de $390.29 del yaml
    está inflado por ellos.
    """
    return con.sql(f"""
        WITH grupos AS (
            SELECT any_value({NORM_CAT})               AS catalogo,
                   {FILTRO_CATALOGO}                   AS en_alcance,
                   max({PRECIO}) - min({PRECIO})       AS diferencia
            FROM q WHERE {RECORTE}
            GROUP BY {CLAVE_FILA}, {FILTRO_CATALOGO}
            HAVING count(*) > 1 AND max({PRECIO}) - min({PRECIO}) > 50
        )
        SELECT catalogo, en_alcance,
               count(*)                   AS grupos,
               round(avg(diferencia), 2)  AS diferencia_promedio,
               round(max(diferencia), 2)  AS diferencia_maxima
        FROM grupos
        GROUP BY 1, 2
        ORDER BY diferencia_maxima DESC
    """).df()


def colisiones_extremas(con, n=20):
    """Las n colisiones más grandes, con nombre y apellido.

    Para que quien revise el PR mire filas, no promedios. `razon` es
    max/min: si da 10, 100 o 1000 clavado, es un cero de más o un punto
    corrido, y entonces sí es error de captura. Si da 1.4, es precio.
    """
    return con.sql(f"""
        WITH grupos AS (
            SELECT producto, presentacion, marca, nombre_comercial,
                   fecha_registro,
                   any_value({NORM_CAT})          AS catalogo,
                   {FILTRO_CATALOGO}              AS en_alcance,
                   min({PRECIO})                  AS precio_min,
                   max({PRECIO})                  AS precio_max
            FROM q WHERE {RECORTE}
            GROUP BY producto, presentacion, marca, nombre_comercial,
                     direccion, fecha_registro, {FILTRO_CATALOGO}
            HAVING count(*) > 1
        )
        SELECT catalogo, en_alcance, producto, presentacion, marca,
               precio_min, precio_max,
               round(precio_max - precio_min, 2)                  AS diferencia,
               round(precio_max / nullif(precio_min, 0), 2)       AS razon,
               CASE
                 WHEN abs(precio_max / nullif(precio_min, 0) -   10) < 0.05
                      THEN 'factor 10 · un cero de mas'
                 WHEN abs(precio_max / nullif(precio_min, 0) -  100) < 0.50
                      THEN 'factor 100 · punto corrido'
                 WHEN abs(precio_max / nullif(precio_min, 0) - 1000) < 5.00
                      THEN 'factor 1000'
                 ELSE ''
               END                                                AS sospecha
        FROM grupos
        ORDER BY diferencia DESC
        LIMIT {n}
    """).df()


def pct(parte, todo):
    return f"{parte / todo:.2%}" if todo else "—"


if __name__ == "__main__":
    if not any(PARQUETS.glob("*.parquet")):
        raise SystemExit(f"No hay parquets en {PARQUETS}. Corre antes perfilado_nivel2.py")
    con = conectar()
    SALIDA.mkdir(parents=True, exist_ok=True)

    print("=" * 78)
    print("El alcance que el contrato declara · cinco catálogos del ADR 005")
    print("=" * 78)
    recorte, dentro, fuera = alcance_real(con)
    print(f"  Recorte territorial (lo que mide medir-decisiones.py) : {recorte:>10,}")
    print(f"  Dentro de los cinco catálogos (lo que ingiere)        : {dentro:>10,}"
          f"  ({pct(dentro, recorte)})")
    print(f"  Fuera del alcance                                     : {fuera:>10,}"
          f"  ({pct(fuera, recorte)})")
    print("\n  Las 77,670 colisiones del yaml están medidas sobre la primera")
    print("  cifra, no sobre la segunda. Lo que sigue las vuelve a medir sobre")
    print("  el alcance de verdad.")

    # ── salud del campo
    filas, nulos, ceros, negativos, bajo_min = salud_de_precio(con)
    print("\n── Los supuestos del yaml sobre `precio`, dentro del alcance")
    print(f"   filas                                : {filas:,}")
    print(f"   nulos  (yaml dice: ninguno permitido): {nulos:,}")
    print(f"   en cero                              : {ceros:,}")
    print(f"   negativos                            : {negativos:,}")
    print(f"   por debajo de 0.01 (yaml: `minimo`)  : {bajo_min:,}")
    if nulos or negativos or bajo_min:
        print("   Hay violaciones. `nulos_permitidos: false` y `minimo: 0.01` se")
        print("   pusieron citando perfilado.md §2, que midió otra población.")

    # ── el techo
    print("\n" + "=" * 78)
    print("El REVISAR de `precio.maximo` · qué techo aguanta")
    print("=" * 78)
    ppc = precio_por_catalogo(con)
    ppc.to_csv(SALIDA / "precio-por-catalogo.csv", index=False)
    print(ppc.to_string(index=False))
    print("\n  Si el máximo de un catálogo está muy arriba de su p999, ese máximo")
    print("  es un caso aislado y no sirve de frontera. Si están pegados, el")
    print("  catálogo de verdad llega hasta ahí.")

    tc = techo_candidato(con)
    tc.to_csv(SALIDA / "techo-candidato.csv")
    print("\n── Cuántas filas rechazaría cada techo, hoy")
    print(tc.to_string())
    print("\n  Todos rechazan 0 o casi 0 sobre lo ya medido: es el pasado. La")
    print("  ventana está abierta (`hasta: null`), así que el techo tiene que")
    print("  aguantar las quincenas que faltan, no las que ya están.")

    print("\n── Los quince máximos mensuales más altos")
    print(maximo_por_mes(con).to_string(index=False))
    print("\n  Si 1775 aparece un solo mes, no calibres el techo con él.")

    # ── colisiones, ya en alcance
    print("\n" + "=" * 78)
    print("Las colisiones, medidas sobre lo que el contrato sí ingiere")
    print("=" * 78)
    cea = colisiones_en_alcance(con)
    print(cea.to_string(index=False))
    total = int(cea.filas_sobrantes.sum())
    print(f"\n  Suma de filas_sobrantes: {total:,}")
    print(f"  El yaml dice 77,670, medido sobre {recorte:,} filas.")
    print(f"  Este número está medido sobre {dentro:,}. Es el que va al contrato,")
    print("  junto con sus porcentajes recalculados para `que_se_hace`.")

    # ── el outlier
    print("\n" + "=" * 78)
    print("El bucket de «más de $50», abierto por catálogo")
    print("=" * 78)
    epc = extremos_por_catalogo(con)
    print(epc.to_string(index=False))
    print("\n  En los cinco catálogos del ADR 005 el precio máximo es 1775, así")
    print("  que ahí ninguna diferencia puede pasar de 1775. Toda diferencia por")
    print("  encima de eso viene de un catálogo que el contrato NO ingiere.")

    ce = colisiones_extremas(con)
    ce.to_csv(SALIDA / "colisiones-extremas.csv", index=False)
    print("\n── Las veinte colisiones más grandes, fila por fila")
    print(ce.to_string(index=False))
    print("\n  `razon` = precio_max / precio_min. En 10, 100 o 1000 clavado es")
    print("  error de captura. En 1.4 es precio. Esta tabla es la que se anexa")
    print("  al PR: quien revise mira filas, no promedios.")

    print("\n" + "=" * 78)
    print("Qué hacer con estas cifras")
    print("=" * 78)
    print("  · `colisiones_conocidas` y los porcentajes de `que_se_hace` se")
    print("    reemplazan por los de aquí, con nota de que los anteriores eran")
    print("    del recorte territorial.")
    print("  · `precio.maximo` se cierra con el techo elegido y su razón, y deja")
    print("    de decir REVISAR.")
    print("  · Si el ADR 005 no se ratifica el 16, estas cifras cambian: están")
    print("    atadas a los cinco catálogos. Fecharlas.")
