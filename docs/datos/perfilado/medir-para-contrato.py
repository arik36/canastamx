"""
Las tres cifras que le faltan al contrato · medidas sobre SU alcance · QQP

Por qué existe este guión
-------------------------
El contrato v1.2.0 deja tres campos marcados `POR_MEDIR`, y los tres se podrían
haber llenado copiando una cifra que ya existe. **Ése es justo el error que este
proyecto ya cometió tres veces**: `colisiones_conocidas` traía 77,670 (medido
sobre el recorte territorial) cuando el bueno era 74,992; el porcentaje de `S/M`
traía 37.40% (territorial) cuando era 20.02%; y el caso del $15,100 resultó ser
un Centro de Lavado de un catálogo que el contrato ni siquiera ingiere.

Las tres veces el número estaba bien medido. Estaba bien medido **sobre otra
cosa**.

Hay tres poblaciones vivas y no son intercambiables:

    corpus                21,357,873   los 38 archivos       -> perfilado.md
    recorte territorial    4,384,962   7 entidades x ventana -> ADR 001, ADR 002
    alcance del contrato   2,658,906   + los 5 catálogos     -> contracts/

Todo lo que mide este guión es sobre la tercera.

Qué contesta
------------
1. `clave_de_articulo.articulos` — cuántos artículos expone el producto, con la
   normalización canónica y con el `?` reparado. Cierra el pendiente
   `conteo_de_articulos`, donde circulaban 5,015 y 6,172 y ninguno servía.

2. `normalizacion.reparar_interrogantes.medido_en_el_alcance` — cuánto `?` hay
   dentro del alcance y cuánto de eso se repara solo. Las cifras del perfilado
   (770,273 · 96.82%) son del corpus.

3. `presentacion.ocultar_por_defecto_en_canasta_basica.filas_afectadas` — qué
   categorías de BASICOS caerían en la vista por omisión y cuánto pesan. Es la
   decisión de Ron y Copa Menstrual, resuelta con la lista real de la fuente en
   vez de a mano.

Uso
---
    python docs/datos/perfilado/medir-para-contrato.py

Salidas
-------
    docs/datos/perfilado/salidas/articulos-en-alcance.csv
    docs/datos/perfilado/salidas/interrogantes-en-alcance.csv
    docs/datos/perfilado/salidas/categorias-de-basicos.csv
"""
import os
from collections import defaultdict
from pathlib import Path

import duckdb

RAIZ = Path(os.environ.get("CANASTAMX_DATOS", Path.home() / "canastamx-datos"))
PARQUETS = RAIZ / "procesado" / "por_archivo"
SALIDA = Path("docs/datos/perfilado/salidas")

SIETE = ["aguascalientes", "guanajuato", "jalisco", "michoacan",
         "queretaro", "san luis potosi", "zacatecas"]
ANIOS = (2025, 2026)
CATALOGOS = ["basicos", "pacic", "frutas y legumbres", "mercados",
             "pescados y mariscos"]

NORM_EDO = "trim(lower(strip_accents(estado)))"
NORM_CAT = "trim(lower(strip_accents(catalogo)))"
FILTRO_SIETE = " OR ".join(f"{NORM_EDO} LIKE '{e}%'" for e in SIETE)
FILTRO_ANIO = f"year(fecha_registro) BETWEEN {ANIOS[0]} AND {ANIOS[1]}"
FILTRO_CAT = f"{NORM_CAT} IN ({', '.join(repr(c) for c in CATALOGOS)})"
ALCANCE = f"(({FILTRO_SIETE}) AND {FILTRO_ANIO}) AND {FILTRO_CAT}"

# La normalización canónica del flujo, escrita una sola vez. Es la misma de
# perfilado_nivel3.py, h3-entre-cadenas.py y h3-muestra-para-calificar.py.
# Una normalización PARECIDA no es la misma: la primera versión del guión de
# muestreo usó `upper(strip_accents(trim(col)))` —que no quita puntuación— y por
# eso `Kellogg's` y `Kellogg´s` salían como artículos distintos.
NORM = ("trim(regexp_replace(regexp_replace(lower(strip_accents({0})), "
        "'[^a-z0-9 ]', ' ', 'g'), '\\s+', ' ', 'g'))")

# Las columnas de texto donde el perfilado encontró `?`.
TEXTO = ["producto", "presentacion", "marca", "categoria", "cadena_comercial",
         "giro", "nombre_comercial", "direccion", "municipio"]

# Lo que la vista por omisión de «canasta básica» ocultaría. Son valores reales
# de la columna `categoria`, no una lista inventada de productos.
CATEGORIAS_OCULTAS = ["vinos y licores", "cerveza", "cigarrillos"]


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
    con.sql(f"CREATE VIEW a AS SELECT * FROM q WHERE {ALCANCE}")
    return con


# ── 1 · cuántos artículos expone el producto ────────────────────────────────

def articulos(con):
    """Los tres niveles de frontera, sobre el alcance y con la normalización
    canónica. Se cuentan dos veces: dejando fuera las filas con `?` y
    metiéndolas, para que se vea cuánto infla el bug el catálogo.

    La diferencia entre las dos columnas es el número de artículos fantasma que
    el producto mostraría hoy si no se reparara el `?`: `Camarón` y `Camar?n`
    como dos renglones distintos del mismo camarón.
    """
    limpio = " AND ".join(f"{c} NOT LIKE '%?%'" for c in
                          ["producto", "presentacion", "marca"])
    filas = []
    for etiqueta, donde in (("sin filas con ?", f"WHERE {limpio}"),
                            ("con todas las filas", "")):
        r = con.sql(f"""
            WITH n AS (
                SELECT {NORM.format('producto')}     AS p,
                       {NORM.format('presentacion')} AS pr,
                       {NORM.format('marca')}        AS m
                FROM a {donde}
            )
            SELECT count(*)                   AS filas,
                   count(DISTINCT p)          AS solo_producto,
                   count(DISTINCT (p, pr))    AS producto_presentacion,
                   count(DISTINCT (p, pr, m)) AS con_marca
            FROM n
        """).fetchone()
        filas.append((etiqueta, *r))
    import pandas as pd
    return pd.DataFrame(filas, columns=["poblacion", "filas", "solo_producto",
                                        "producto_presentacion", "con_marca"])


# ── 2 · el `?` dentro del alcance ───────────────────────────────────────────

def interrogantes_por_columna(con):
    """Cuántas filas del alcance traen `?` en cada columna de texto."""
    casos = ",\n".join(
        f"count(*) FILTER (WHERE {c} LIKE '%?%') AS {c}" for c in TEXTO)
    d = con.sql(f"SELECT count(*) AS filas_del_alcance, {casos} FROM a").df()
    return d.T.rename(columns={0: "filas_con_interrogante"})


def reparabilidad(con):
    """Cuántos valores rotos tienen un gemelo único que los explica.

    El método es el del perfilado: para un valor con `?`, se busca entre los
    valores limpios de la MISMA columna uno de idéntica longitud que coincida en
    todas las posiciones salvo donde está el `?`. Si hay exactamente uno, la
    reparación es determinista. Si hay varios, es ambiguo y se resuelve por
    frecuencia. Si no hay ninguno, es irrecuperable y va a cuarentena.

    Se hace en Python y no en SQL porque son unos miles de valores distintos por
    columna, no millones de filas: el costo es irrelevante y el código se lee.
    """
    import pandas as pd
    filas = []
    for col in TEXTO:
        vals = con.sql(f"""
            SELECT {col} AS v, count(*) AS n FROM a GROUP BY 1
        """).df()
        rotos = vals[vals.v.astype(str).str.contains(r"\?", na=False)]
        limpios = vals[~vals.v.astype(str).str.contains(r"\?", na=False)]
        if rotos.empty:
            filas.append((col, 0, 0, 0, 0, 0))
            continue
        # Índice por longitud: sólo un gemelo de la misma longitud puede serlo.
        por_largo = defaultdict(list)
        for v in limpios.v.astype(str):
            por_largo[len(v)].append(v)

        unico = ambiguo = huerfano = 0
        filas_unico = 0
        for v, n in zip(rotos.v.astype(str), rotos.n):
            pos = [i for i, ch in enumerate(v) if ch == "?"]
            cand = [c for c in por_largo.get(len(v), ())
                    if all(c[i] == v[i] for i in range(len(v)) if i not in pos)]
            if len(cand) == 1:
                unico += 1
                filas_unico += int(n)
            elif len(cand) > 1:
                ambiguo += 1
            else:
                huerfano += 1
        filas.append((col, len(rotos), unico, ambiguo, huerfano, filas_unico))

    d = pd.DataFrame(filas, columns=["columna", "valores_rotos", "gemelo_unico",
                                     "ambiguos", "sin_gemelo", "filas_reparables"])
    return d[d.valores_rotos > 0].sort_values("valores_rotos", ascending=False)


# ── 3 · las categorías de BASICOS ───────────────────────────────────────────

def categorias_de_basicos(con):
    """Qué categorías viven dentro de `Basicos` y cuánto pesa cada una.

    El protocolo compromete un recorte «conforme a la clasificación de la
    fuente», así que el contrato ingiere `Basicos` completo. Pero la vista por
    omisión del producto puede ocultar categorías, y esta tabla dice cuáles hay
    y qué costaría ocultarlas. La decisión es del equipo, no del frente de datos.
    """
    return con.sql(f"""
        SELECT trim(lower(strip_accents(categoria)))  AS categoria,
               count(*)                                AS filas,
               count(DISTINCT producto)                AS productos,
               round(median(CAST(precio AS DECIMAL(12,2))), 2) AS mediana,
               round(max(CAST(precio AS DECIMAL(12,2))), 2)    AS maximo
        FROM a
        WHERE {NORM_CAT} = 'basicos'
        GROUP BY 1
        ORDER BY filas DESC
    """).df()


def peso_de_lo_oculto(con):
    """Cuántas filas del alcance esconde la vista por omisión."""
    lista = ", ".join(repr(c) for c in CATEGORIAS_OCULTAS)
    return con.sql(f"""
        SELECT count(*) FILTER (
                 WHERE trim(lower(strip_accents(categoria))) IN ({lista})
               )                                      AS filas_ocultas,
               count(*)                               AS filas_del_alcance
        FROM a
    """).fetchone()


def pct(parte, todo):
    return f"{parte / todo:.2%}" if todo else "—"


if __name__ == "__main__":
    if not any(PARQUETS.glob("*.parquet")):
        raise SystemExit(f"No hay parquets en {PARQUETS}. Corre antes perfilado_nivel2.py")
    con = conectar()
    SALIDA.mkdir(parents=True, exist_ok=True)

    total = con.sql("SELECT count(*) FROM a").fetchone()[0]
    print("=" * 78)
    print("Las tres cifras que le faltan al contrato · medidas sobre SU alcance")
    print("=" * 78)
    print(f"  Alcance del contrato : {total:,} filas")
    print("  (7 entidades ∩ 2025-2026 ∩ los 5 catálogos del ADR 005)")
    print("\n  Ninguna cifra de aquí se puede copiar del perfilado ni del ADR 001:")
    print("  aquéllos miden el corpus (21,357,873) y el recorte territorial")
    print("  (4,384,962). Ése es el error que ya nos costó tres campos del yaml.")

    # ── 1
    print("\n" + "=" * 78)
    print("1 · Cuántos artículos expone el producto")
    print("=" * 78)
    art = articulos(con)
    art.to_csv(SALIDA / "articulos-en-alcance.csv", index=False)
    print(art.to_string(index=False))
    limpio = art.iloc[0]
    todas = art.iloc[1]
    fantasma = int(todas.producto_presentacion) - int(limpio.producto_presentacion)
    print(f"\n  → `clave_de_articulo.articulos` = {int(limpio.producto_presentacion):,}")
    print("    (producto + presentacion, normalización canónica, sin filas con `?`)")
    print(f"\n  Artículos fantasma que el `?` agrega hoy: {fantasma:,}")
    print("  Son los `Camar?n` del catálogo: el mismo artículo contado dos veces.")
    print("  Con la reparación declarada en el contrato, desaparecen.")
    print("\n  Para comparar con lo que circulaba:")
    print("    6,172 · recorte territorial · literales crudos (formas de escribir)")
    print("    5,015 · corpus sin `?`      · normalización canónica")
    print(f"    {int(limpio.producto_presentacion):,} · alcance del contrato · ← el que va al yaml")

    # ── 2
    print("\n" + "=" * 78)
    print("2 · El `?` dentro del alcance")
    print("=" * 78)
    ipc = interrogantes_por_columna(con)
    print(ipc.to_string())
    rep = reparabilidad(con)
    rep.to_csv(SALIDA / "interrogantes-en-alcance.csv", index=False)
    print("\n── Qué tan reparable es, por columna")
    if rep.empty:
        print("   No hay valores con `?` dentro del alcance.")
    else:
        print(rep.to_string(index=False))
        rotos = int(rep.valores_rotos.sum())
        unicos = int(rep.gemelo_unico.sum())
        print(f"\n  Valores rotos distintos : {rotos:,}")
        print(f"  Con gemelo único        : {unicos:,} ({pct(unicos, rotos)})"
              "  → se reparan solos")
        print(f"  Ambiguos                : {int(rep.ambiguos.sum()):,}"
              "  → se resuelven por frecuencia (10:1)")
        print(f"  Sin gemelo              : {int(rep.sin_gemelo.sum()):,}"
              "  → cuarentena, motivo codificacion_irrecuperable")
        print("\n  Compara contra el corpus, donde el perfilado midió 96.82%")
        print("  reparable. Si aquí sale muy distinto, es que el daño no se")
        print("  reparte igual entre catálogos, y eso también hay que decirlo.")

    # ── 3
    print("\n" + "=" * 78)
    print("3 · Las categorías de BASICOS · la decisión de Ron y Copa Menstrual")
    print("=" * 78)
    cats = categorias_de_basicos(con)
    cats.to_csv(SALIDA / "categorias-de-basicos.csv", index=False)
    print(cats.to_string(index=False))

    ocultas, _ = peso_de_lo_oculto(con)
    print(f"\n  Categorías que la vista por omisión ocultaría: {CATEGORIAS_OCULTAS}")
    print(f"  Filas afectadas: {ocultas:,} ({pct(ocultas, total)} del alcance)")
    print("\n  → `presentacion.ocultar_por_defecto_en_canasta_basica.filas_afectadas`")
    print("\n  El contrato NO deja de ingerirlas: entran, y el usuario puede verlas.")
    print("  Lo que cambia es qué muestra la app por omisión cuando dice")
    print("  «canasta básica». Si alguna de esas tres categorías no aparece en la")
    print("  tabla de arriba, no está dentro de BASICOS y hay que quitarla de la")
    print("  lista en vez de dejarla escrita sin efecto.")

    print("\n" + "=" * 78)
    print("Qué hacer con estas cifras")
    print("=" * 78)
    print("  Los tres campos `POR_MEDIR` de contracts/qqp-v1.yaml se llenan con")
    print("  esto, y el yaml pasa a 1.2.1. Fecha la medición: están atadas a los")
    print("  cinco catálogos del ADR 005 y cambian si la lista cambia.")
