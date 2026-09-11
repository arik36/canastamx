"""
Perfilado nivel 3 · Variantes de escritura · QQP (T005)

Qué se está midiendo, con precisión
-----------------------------------
«Variante de escritura» = dos textos DISTINTOS que se refieren a lo mismo.
Se detecta normalizando y viendo cuántos literales crudos caen en la misma
clave. Se calculan dos normalizaciones para que la cifra no dependa de una
decisión escondida:

  suave  = minúsculas + quitar acentos + colapsar espacios
  fuerte = lo anterior + quitar toda puntuación

Y se separan dos cosas que se confunden todo el tiempo:

  · variación de ESCRITURA — «1 Kg. Granel. Hass» vs «1 kg granel hass».
    Es un problema de normalización y se arregla con reglas.
  · variación de PRODUCTO — «1 Kg. Granel. Hass» vs «Pieza». Son dos cosas
    distintas de verdad; ninguna normalización las va a juntar, y no debe.

El número que va en el blanco de la plantilla es el primero: literales crudos
por clave normalizada. Si sale 1, la fuente ya viene normalizada. El segundo
se reporta aparte porque también afecta a H3, pero por otro motivo.

Uso
---
    python docs/datos/perfilado/perfilado_nivel3.py
    CANASTAMX_DATOS=/otra/ruta python docs/datos/perfilado/perfilado_nivel3.py
"""
import os
from pathlib import Path

import duckdb

RAIZ = Path(os.environ.get("CANASTAMX_DATOS", Path.home() / "canastamx-datos"))
PARQUETS = RAIZ / "procesado" / "por_archivo"
SALIDA = Path("docs/datos/perfilado")

# suave: minúsculas, sin acentos, espacios colapsados
SUAVE = "trim(regexp_replace(lower(strip_accents({0})), '\\s+', ' ', 'g'))"
# fuerte: además sin puntuación
FUERTE = ("trim(regexp_replace(regexp_replace(lower(strip_accents({0})), "
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
        SELECT producto, presentacion, marca, categoria, precio,
               (producto LIKE '%?%' OR presentacion LIKE '%?%'
                OR marca LIKE '%?%')                       AS roto,
               {SUAVE.format('producto')}     AS prod_s,
               {FUERTE.format('producto')}    AS prod_f,
               {SUAVE.format('presentacion')} AS pres_s,
               {FUERTE.format('presentacion')} AS pres_f,
               {SUAVE.format('marca')}        AS marca_s,
               {FUERTE.format('marca')}       AS marca_f
        FROM {fuente}
    """)
    return con


def resumen(con, etiqueta, condicion="TRUE"):
    """Literales crudos por clave normalizada, en las tres columnas y en el trío."""
    print(f"\n── {etiqueta}")
    filas = con.sql(f"SELECT count(*) FROM q WHERE {condicion}").fetchone()[0]
    print(f"   filas consideradas: {filas:,}")
    print(f"\n   {'columna':<14} {'literales':>10} {'clave suave':>12} {'clave fuerte':>13} "
          f"{'var/clave':>10} {'máx':>5}")
    for col, s, f in (("producto", "prod_s", "prod_f"),
                      ("presentacion", "pres_s", "pres_f"),
                      ("marca", "marca_s", "marca_f")):
        r = con.sql(f"""
            SELECT count(DISTINCT {col}) crudos,
                   count(DISTINCT {s}) suaves,
                   count(DISTINCT {f}) fuertes
            FROM q WHERE {condicion}
        """).fetchone()
        mx = con.sql(f"""
            SELECT max(v) FROM (SELECT count(DISTINCT {col}) v FROM q
                                WHERE {condicion} GROUP BY {f})
        """).fetchone()[0]
        print(f"   {col:<14} {r[0]:>10,} {r[1]:>12,} {r[2]:>13,} "
              f"{r[0]/max(r[2],1):>10.2f} {mx:>5}")

    tri = con.sql(f"""
        WITH t AS (
            SELECT producto || '§' || presentacion || '§' || marca AS crudo,
                   prod_f   || '§' || pres_f       || '§' || marca_f AS clave
            FROM q WHERE {condicion}
        ),
        g AS (SELECT clave, count(DISTINCT crudo) AS variantes FROM t GROUP BY clave)
        SELECT count(*) claves, sum(variantes) literales,
               avg(variantes) media, median(variantes) mediana,
               max(variantes) maximo,
               count(*) FILTER (WHERE variantes > 10) mas_de_10,
               count(*) FILTER (WHERE variantes > 1)  mas_de_1
        FROM g
    """).fetchone()
    claves, literales, media, mediana, maximo, m10, m1 = tri
    print(f"\n   EL NÚMERO DE LA PLANTILLA — trío (producto + presentacion + marca):")
    print(f"     artículos distintos tras normalizar : {claves:,}")
    print(f"     literales crudos                    : {literales:,}")
    print(f"     variantes por artículo — media      : {media:.2f}")
    print(f"     variantes por artículo — mediana    : {mediana:.0f}")
    print(f"     variantes por artículo — máximo     : {maximo:,}")
    print(f"     artículos con más de 1 variante     : {m1:,} de {claves:,} ({m1/claves:.1%})")
    print(f"     artículos con más de 10 variantes   : {m10:,} de {claves:,} ({m10/claves:.1%})")
    return {"claves": claves, "media": media, "mediana": mediana,
            "maximo": maximo, "mas_de_10": m10, "pct_10": m10 / claves}


def presentaciones_por_producto(con):
    """Cuántas presentaciones distintas tiene un producto — variación REAL."""
    r = con.sql("""
        WITH g AS (
            SELECT prod_f,
                   count(DISTINCT presentacion) AS crudas,
                   count(DISTINCT pres_f)       AS normalizadas,
                   count(DISTINCT marca)        AS marcas,
                   count(*)                     AS filas
            FROM q GROUP BY prod_f
        )
        SELECT count(*) productos,
               avg(crudas) media_crudas, median(crudas) mediana_crudas,
               max(crudas) max_crudas,
               avg(normalizadas) media_norm, median(normalizadas) mediana_norm,
               max(normalizadas) max_norm,
               count(*) FILTER (WHERE normalizadas > 10) mas_de_10,
               avg(marcas) media_marcas
        FROM g
    """).fetchone()
    print(f"\n── Presentaciones por producto (variación de PRODUCTO, no de escritura)")
    print(f"   productos (clave fuerte)                : {r[0]:,}")
    print(f"   presentaciones crudas   media/mediana/máx: {r[1]:.1f} / {r[2]:.0f} / {r[3]:,}")
    print(f"   presentaciones normaliz. media/mediana/máx: {r[4]:.1f} / {r[5]:.0f} / {r[6]:,}")
    print(f"   productos con más de 10 presentaciones  : {r[7]:,} de {r[0]:,} ({r[7]/r[0]:.1%})")
    print(f"   marcas por producto, media              : {r[8]:.1f}")
    print(f"\n   De cada {r[1]:.1f} presentaciones escritas, {r[4]:.1f} son distintas de verdad;")
    print(f"   la diferencia, {r[1]-r[4]:.1f}, es puramente cómo se escribió.")
    return r


def top_productos(con, n=20):
    print(f"\n── Los {n} productos con más filas — para la tabla del informe")
    r = con.sql(f"""
        SELECT any_value(producto) AS producto, count(*) AS filas,
               count(DISTINCT producto)     AS var_nombre,
               count(DISTINCT presentacion) AS pres_crudas,
               count(DISTINCT pres_f)       AS pres_norm,
               count(DISTINCT marca)        AS marcas,
               round(median(precio), 2)     AS precio_mediano
        FROM q GROUP BY prod_f ORDER BY filas DESC LIMIT {n}
    """).df()
    print(r.to_string(index=False))
    return r


def muestra_para_revision(con, n_grandes=10, n_azar=10):
    """Vuelca grupos completos a un archivo para la verificación a mano.

    La plantilla lo pide explícitamente y tiene razón: si la normalización
    juntó productos distintos, la cifra sale inflada y nadie se entera.
    Se toman los grupos con MÁS variantes, que es donde estaría el error, y
    unos cuantos al azar para no mirar sólo los casos extremos.
    """
    SALIDA.mkdir(parents=True, exist_ok=True)
    destino = SALIDA / "variantes-para-revisar.txt"
    grandes = con.sql(f"""
        SELECT prod_f, count(DISTINCT producto) v FROM q
        GROUP BY prod_f HAVING count(DISTINCT producto) > 1
        ORDER BY v DESC LIMIT {n_grandes}
    """).df()
    azar = con.sql(f"""
        SELECT prod_f, count(DISTINCT producto) v FROM q
        GROUP BY prod_f ORDER BY random() LIMIT {n_azar}
    """).df()

    lineas = ["VERIFICACIÓN MANUAL DE LA NORMALIZACIÓN (T005)",
              "",
              "Para cada grupo: ¿todos los literales de abajo son de verdad LO MISMO?",
              "Si alguno no lo es, la normalización lo juntó mal y hay que anotarlo",
              "en «Agrupamientos incorrectos» de la sección 3 de perfilado.md.",
              "", "=" * 70, ""]
    for etiqueta, df in (("CON MÁS VARIANTES (donde estaría el error)", grandes),
                         ("AL AZAR (control)", azar)):
        lineas += [f"### {etiqueta}", ""]
        for clave in df.prod_f:
            k = clave.replace("'", "''")
            vals = con.sql(f"""
                SELECT producto, count(*) filas FROM q
                WHERE prod_f = '{k}' GROUP BY producto ORDER BY filas DESC
            """).df()
            lineas.append(f"clave: {clave}   ({len(vals)} literal/es)")
            for _, row in vals.iterrows():
                lineas.append(f"    {row.filas:>10,}  {row.producto!r}")
            lineas.append("    ¿correcto? [ ] sí   [ ] no →")
            lineas.append("")
    destino.write_text("\n".join(lineas), encoding="utf-8")
    print(f"\n── {len(grandes)+len(azar)} grupos volcados en {destino}")
    print("   Ábrelo, marca los que estén mal y llena «Verificación manual» de la")
    print("   sección 3. Sin ese paso la cifra no se puede defender el viernes.")


def lectura_para_h3(res):
    """La guía de lectura que ya venía en la plantilla, aplicada a la cifra."""
    m = res["media"]
    print("\n" + "=" * 78)
    print("Qué implica para H3")
    print("=" * 78)
    print(f"  Variantes de escritura por artículo, media: {m:.2f}")
    if m <= 3:
        veredicto = ("1 a 3 → la fuente ya viene normalizada. 85% es cómodo.\n"
                     "  Se puede sostener H3 sin comparación difusa.")
    elif m <= 8:
        veredicto = ("4 a 8 → normal. 85% alcanzable CON comparación difusa.\n"
                     "  Hay que presupuestar esa comparación en el diseño, no darla por hecha.")
    else:
        veredicto = ("más de 10 → hay que bajar la meta o acotar el recorte,\n"
                     "  y decirlo el viernes en la reunión de decisión, no en noviembre.")
    print(f"  → {veredicto}")
    print(f"\n  Advertencia: esta lectura vale para la variación de ESCRITURA.")
    print(f"  La variación de PRODUCTO (presentaciones distintas de verdad) es")
    print(f"  otro problema y no se arregla normalizando: se arregla decidiendo")
    print(f"  qué es «el mismo artículo» para el usuario que arma su despensa.")
    print(f"  Ésa es una decisión de producto y le toca a la reunión del viernes.")


if __name__ == "__main__":
    if not any(PARQUETS.glob("*.parquet")):
        raise SystemExit(f"No hay parquets en {PARQUETS}. Corre antes perfilado_nivel2.py")
    con = conectar()
    total = con.sql("SELECT count(*) FROM q").fetchone()[0]
    rotas = con.sql("SELECT count(*) FROM q WHERE roto").fetchone()[0]
    print("=" * 78)
    print(f"T005 · Variantes de escritura · {total:,} filas")
    print("=" * 78)

    res = resumen(con, "TODAS las filas")
    if rotas:
        fantasmas = con.sql("""
            SELECT count(*) FROM (
                SELECT prod_f || '§' || pres_f || '§' || marca_f AS k
                FROM q GROUP BY 1 HAVING any_value(roto))
        """).fetchone()[0]
        print(f"\n   OJO: {rotas:,} filas ({rotas/total:.3%}) traen '?' en producto,")
        print("   presentacion o marca. El '?' no se normaliza a la letra que se")
        print("   comió, así que 'Art?culos' y 'Artículos' quedan como DOS artículos")
        print(f"   distintos. Claves contaminadas por '?': {fantasmas:,} de "
              f"{res['claves']:,} ({fantasmas/res['claves']:.1%}).")
        print("   Ésos no son variantes de escritura de más: son artículos")
        print("   fantasma de más, y eso desplaza la media en cualquier dirección.")
        print("   La misma medición dejando fuera esas filas:")
        limpio = resumen(con, "SÓLO filas SIN '?'", "NOT roto")
        print(f"\n   Media con '?': {res['media']:.2f}   ·   sin '?': {limpio['media']:.2f}")
        print(f"   Artículos     : {res['claves']:,}   ·   {limpio['claves']:,}")
        print("   La cifra que se defiende el viernes es la de ABAJO (sin '?'),")
        print("   diciendo en voz alta que deja fuera el 3.6% corrupto — y que")
        print("   mojibake.py mide cuánto de ese 3.6% es reparable.")
        res = limpio

    presentaciones_por_producto(con)
    top_productos(con)
    muestra_para_revision(con)
    lectura_para_h3(res)
