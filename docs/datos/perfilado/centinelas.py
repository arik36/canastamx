"""
Centinelas y atípicos · QQP (corrige la sección 2 de perfilado.md · T004)

Reemplaza la función sospechosos() de perfilado_nivel2.py, que devolvía 0 y no
podía devolver otra cosa. Este guión primero DEMUESTRA por qué esa regla estaba
muerta y luego aplica tres detectores que sí funcionan sobre precios.

Por qué la regla anterior nunca iba a disparar
----------------------------------------------
1. En una distribución de precios el p99 ya está pegado al máximo. En las 46
   categorías del corpus la razón máx/p99 más grande es 6.29x (pan). Pedir 10x
   el p99 es pedir algo que no ocurre en NINGUNA categoría: cero disparos por
   construcción, aunque no hubiera un solo dato malo.
2. Un centinela repetido 4,515 veces no es un valor raro: es cuerpo de la
   distribución. Ningún umbral de percentil lo va a encontrar, porque el
   centinela ayudó a calcular el percentil.
3. `categoria` es una agrupación demasiado gruesa. "Aparatos Electricos" mete
   una plancha de $181 y un refrigerador de $99,999 en el mismo cálculo: un
   rango de 551x dentro de un solo grupo. El p99 de esa mezcla no describe a
   ningún producto. La unidad correcta es `producto`.

Los tres detectores
-------------------
D1 · Precios redondos anormalmente repetidos, y su clasificación. Un precio
     repdigit (9, 99, 999, 9999…) que se repite muchísimo más que los precios
     vecinos del MISMO producto. Pero repetirse NO basta para ser un comodín:
     el comercio mexicano pone precios redondos a propósito, y por eso el
     yoghurt a $9.00 exacto aparece cientos de veces. Se separan los dos casos
     por DÓNDE cae el precio dentro del rango de su propio producto — un
     comodín está en el extremo, un punto de precio está en medio.
D2 · Distribución contaminada. Productos cuya mediana o cuyo precio más
     frecuente ES un repdigit. Es el caso que rompió la regla anterior: el
     centinela ya se comió el centro de la distribución.
D3 · Atípico por dispersión robusta, en escala logarítmica y por producto.
     |ln(p) − mediana(ln p)| / (1.4826 · MAD) > 3.5. Logaritmo porque los
     precios son multiplicativos y sesgados a la derecha; mediana y MAD porque
     ni la media ni la desviación estándar sobreviven a los propios atípicos.

Uso
---
    python docs/datos/perfilado/centinelas.py

Lee los parquets que ya dejó perfilado_nivel2.py. Para apuntar a otra carpeta:
    CANASTAMX_DATOS=/otra/ruta python docs/datos/perfilado/centinelas.py
"""
import os
from pathlib import Path

import duckdb

RAIZ = Path(os.environ.get("CANASTAMX_DATOS", Path.home() / "canastamx-datos"))
PARQUETS = RAIZ / "procesado" / "por_archivo"
SALIDA = Path("docs/datos/perfilado")

# Un repdigit: 9, 99, 999, 9999, 99999… con centavos .00 o .99
REPDIGIT = r"^9+\.(00|99)$"
# Un precio es "muy repetido" si aparece este múltiplo de veces por encima de
# lo que se repite un precio vecino normal del mismo producto.
SALTO = 20
# Mínimo de repeticiones para molestarse en mirar. Debajo de esto es anécdota.
MINIMO_VECES = 30
# Umbral clásico de la z robusta. 3.5 es el valor que recomienda la literatura
# de MAD (Iglewicz y Hoaglin), no un número elegido a ojo.
Z_ROBUSTA = 3.5
# Un comodín tiene que estar en el EXTREMO del rango de su producto: su función
# es ser reconociblemente imposible. Un precio redondo que cae en medio del
# rango es un punto de precio del comercio, no un comodín.
POSICION_CENTINELA = 0.99
# …o que sea desproporcionado respecto de la mediana de SU producto. Hace falta
# este segundo camino porque un producto de rango ancho (los medicamentos van de
# $5 a $2,700) puede tener un 15% de cotizaciones por encima del comodín, y
# entonces la posición sola no lo delata. 3x la mediana es un juicio, no una ley:
# la salida son CANDIDATOS para revisar a mano, no un veredicto.
RAZON_MEDIANA_CENTINELA = 3.0


def conectar():
    con = duckdb.connect()
    con.sql("SET memory_limit='4GB'")
    # Cuando una operación no cabe en memory_limit, DuckDB derrama a disco. Por
    # omisión usa `.tmp` relativo a la carpeta desde la que corres el guión —
    # es decir, dentro del repositorio. Con 21 millones de filas, el median()
    # por producto puede dejar ahí gigabytes de temporales. Esto lo manda junto
    # a los parquet, fuera del repositorio y en el disco grande.
    tmp = RAIZ / "tmp-duckdb"
    tmp.mkdir(parents=True, exist_ok=True)
    con.sql(f"SET temp_directory='{tmp}'")
    fuente = f"read_parquet('{PARQUETS}/*.parquet', union_by_name=true)"

    # Mismo criterio que perfilado_nivel2.py: si mojibake.py ya midió las
    # sustituciones, se aplican. Si no, `art?culos deportivos` cuenta como una
    # categoría aparte y el informe queda con 46 donde el nivel 2 dice 45.
    dicc = SALIDA / "mojibake-diccionario.csv"
    if dicc.exists():
        con.sql(f"""CREATE OR REPLACE TABLE repara AS
                    SELECT columna, valor_roto, reparado FROM read_csv('{dicc}')""")
        cat = "coalesce(r.reparado, f.categoria)"
        join = "LEFT JOIN repara r ON r.columna='categoria' AND r.valor_roto = f.categoria"
    else:
        print("AVISO: sin mojibake-diccionario.csv las categorías rotas cuentan aparte.")
        cat, join = "f.categoria", ""

    # strip_accents() de DuckDB en vez de cinco replace() encadenados: también
    # arregla mayúsculas acentuadas y ü. OJO: convierte ñ→n, así que sirve como
    # clave de agrupación, no como texto para mostrarle al usuario.
    con.sql(f"""
        CREATE VIEW q AS
        SELECT lower(strip_accents(trim({cat})))         AS categoria,
               lower(strip_accents(trim(f.producto)))    AS producto,
               f.precio
        FROM {fuente} f
        {join}
        WHERE f.precio IS NOT NULL
    """)
    con.sql("""
        CREATE TABLE prec AS
        SELECT producto, precio, count(*) AS veces
        FROM q WHERE precio > 0 GROUP BY producto, precio
    """)
    con.sql("""
        CREATE TABLE prod AS
        SELECT producto, count(*) AS n,
               median(precio) AS mediana,
               quantile_cont(precio, 0.99) AS p99,
               max(precio) AS maximo
        FROM q WHERE precio > 0 GROUP BY producto
    """)
    return con


# ─────────────────────────────────────────────────────────────────────────────
def d0_la_regla_estaba_muerta(con):
    """Demuestra con los propios datos que 10x el p99 no podía disparar."""
    r = con.sql("""
        SELECT categoria,
               quantile_cont(precio, 0.99) AS p99,
               max(precio) AS maximo,
               max(precio) / nullif(quantile_cont(precio, 0.99), 0) AS razon
        FROM q WHERE precio > 0
        GROUP BY categoria ORDER BY razon DESC
    """).df()
    peor = r.iloc[0]
    print(f"  Categorías evaluadas                      : {len(r)}")
    print(f"  Razón máx/p99 más alta de todo el corpus  : {peor.razon:.2f}x  ({peor.categoria})")
    print(f"  Umbral que pedía la regla                 : 10.00x")
    print(f"  Categorías donde la regla podía disparar  : {(r.razon > 10).sum()} de {len(r)}")
    print("\n  Las cinco categorías con más cola:")
    print(r.head(5).round(2).to_string(index=False))
    return r


def d0b_la_categoria_es_demasiado_gruesa(con):
    """Compara la dispersión dentro de una categoría contra la de un producto."""
    cat = con.sql("""
        SELECT categoria, min(precio) AS minimo, max(precio) AS maximo,
               max(precio) / nullif(min(precio), 0) AS rango
        FROM q WHERE precio > 0 GROUP BY categoria ORDER BY rango DESC LIMIT 5
    """).df()
    print("\n  Rango (máx/mín) DENTRO de una sola categoría — las cinco peores:")
    print(cat.round(1).to_string(index=False))
    peor = cat.iloc[0].categoria
    det = con.sql(f"""
        SELECT producto, count(*) AS n, median(precio) AS mediana,
               min(precio) AS minimo, max(precio) AS maximo
        FROM q WHERE precio > 0 AND categoria = '{peor.replace("'", "''")}'
        GROUP BY producto ORDER BY mediana DESC LIMIT 8
    """).df()
    print(f"\n  Qué hay realmente dentro de «{peor}» (8 productos por mediana):")
    print(det.round(2).to_string(index=False))
    print("\n  → Un p99 calculado sobre esta mezcla no describe a ningún producto.")


# ─────────────────────────────────────────────────────────────────────────────
def d1_redondos_repetidos(con):
    """Precios redondos que se repiten mucho más que sus vecinos.

    OJO CON EL NOMBRE. Esto NO devuelve centinelas: devuelve precios redondos
    anormalmente repetidos, que son un conjunto MÁS GRANDE. Dentro caben dos
    cosas que se parecen en los números y no se parecen en nada más:

      · punto de precio — $9.00 el yoghurt, $99.00 el shampoo. El comercio
        pone precios redondos a propósito, y por eso el $9.00 exacto aparece
        cien veces más que el $9.50. Es un precio REAL y hay que conservarlo.
      · centinela — el capturista no supo el precio y tecleó algo obviamente
        fuera de rango para marcar «no hay dato».

    Lo que los separa no es cuánto se repiten: es DÓNDE CAEN dentro de la
    distribución de su propio producto. Un punto de precio está en medio del
    rango normal. Un centinela está en el extremo, porque su función es ser
    reconociblemente imposible.

    Por eso se calcula `posicion`: de las DEMÁS cotizaciones de ese producto,
    qué fracción es más barata. 0 significa «es lo más barato que hay»; 1,
    «es más caro que todo lo demás».

    Se excluyen sus propias filas del denominador a propósito. Si no, un valor
    muy repetido nunca podría llegar arriba: sus miles de filas ocupan el
    extremo y empujan su propio percentil hacia abajo. Comprobado con datos
    hechos a mano: un comodín con el 7% de las filas se quedaba en 0.93 y
    parecía «no tan extremo» cuando en realidad era más caro que TODO el resto.
    """
    return con.sql(f"""
        WITH acum AS (
            SELECT producto, precio, veces,
                   coalesce(sum(veces) OVER (PARTITION BY producto ORDER BY precio
                             ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING), 0) AS abajo,
                   sum(veces) OVER (PARTITION BY producto) AS total_prod
            FROM prec
        ),
        candidatos AS (
            SELECT a.producto, a.precio, a.veces, d.n, d.mediana, d.maximo,
                   a.abajo::DOUBLE / nullif(a.total_prod - a.veces, 0) AS posicion
            FROM acum a JOIN prod d USING (producto)
            WHERE regexp_matches(printf('%.2f', a.precio), '{REPDIGIT}')
              AND a.veces >= {MINIMO_VECES}
        )
        SELECT c.producto, c.precio, c.veces, c.n,
               c.veces::DOUBLE / c.n                       AS parte,
               c.posicion,
               c.mediana,
               c.precio / nullif(c.mediana, 0)             AS razon_mediana,
               coalesce((SELECT median(o.veces) FROM prec o
                          WHERE o.producto = c.producto
                            AND o.precio <> c.precio
                            AND o.precio BETWEEN c.precio * 0.8 AND c.precio * 1.2), 0)
                                                           AS veces_vecinas,
               c.precio = c.maximo                         AS es_el_maximo
        FROM candidatos c
        ORDER BY c.veces DESC
    """).df()


def d2_distribucion_contaminada(con):
    """Productos cuya mediana o cuyo precio más frecuente ya es un repdigit."""
    return con.sql(f"""
        WITH modal AS (
            SELECT producto, precio AS precio_modal, veces AS veces_modal,
                   row_number() OVER (PARTITION BY producto
                                      ORDER BY veces DESC, precio DESC) AS rk
            FROM prec
        )
        SELECT d.producto, d.n, d.mediana, m.precio_modal, m.veces_modal,
               m.veces_modal::DOUBLE / d.n AS parte_modal,
               regexp_matches(printf('%.2f', d.mediana), '{REPDIGIT}')      AS mediana_repdigit,
               regexp_matches(printf('%.2f', m.precio_modal), '{REPDIGIT}') AS modal_repdigit
        FROM prod d JOIN modal m ON m.producto = d.producto AND m.rk = 1
        WHERE regexp_matches(printf('%.2f', d.mediana), '{REPDIGIT}')
           OR regexp_matches(printf('%.2f', m.precio_modal), '{REPDIGIT}')
        ORDER BY d.n DESC
    """).df()


def d3_atipicos_robustos(con):
    """z robusta sobre ln(precio), por producto. Devuelve (resumen, sin_dispersion)."""
    con.sql("""
        CREATE OR REPLACE TABLE lg AS
        SELECT producto, ln(precio) AS l FROM q WHERE precio > 0
    """)
    con.sql("""
        CREATE OR REPLACE TABLE centro AS
        SELECT producto, median(l) AS mu, count(*) AS n FROM lg GROUP BY producto
    """)
    con.sql("""
        CREATE OR REPLACE TABLE disp AS
        SELECT g.producto, median(abs(g.l - c.mu)) AS mad
        FROM lg g JOIN centro c USING (producto) GROUP BY g.producto
    """)
    atipicos = con.sql(f"""
        SELECT g.producto, count(*) AS filas_atipicas,
               min(exp(g.l)) AS precio_min, max(exp(g.l)) AS precio_max
        FROM lg g JOIN centro c USING (producto) JOIN disp d USING (producto)
        WHERE d.mad > 0
          AND abs(g.l - c.mu) / (1.4826 * d.mad) > {Z_ROBUSTA}
        GROUP BY g.producto ORDER BY filas_atipicas DESC
    """).df()
    # MAD = 0 significa que MÁS DE LA MITAD de las filas comparten el mismo
    # precio exacto. No es que el producto sea "estable": es la firma de que
    # un valor único domina la distribución. Se reporta aparte, no se ignora.
    sin_dispersion = con.sql("""
        SELECT d.producto, c.n, exp(c.mu) AS precio_dominante
        FROM disp d JOIN centro c USING (producto)
        WHERE d.mad = 0 ORDER BY c.n DESC
    """).df()
    return atipicos, sin_dispersion


# ─────────────────────────────────────────────────────────────────────────────
def demostracion():
    """Caso de juguete para ver funcionar D3 sin esperar 21 millones de filas.

    Dos productos: uno con precios apretados y tres atípicos de verdad, y otro
    donde un centinela ocupa más de la mitad de las filas. Sirve para entender
    qué hace cada detector antes de creerle en los datos reales.
    """
    import random
    random.seed(1)
    filas = [("tortillas", round(random.uniform(22, 26), 2)) for _ in range(2000)]
    filas += [("tortillas", 850.0), ("tortillas", 0.05), ("tortillas", 1200.0)]
    filas += [("lavadoras", 9999.0)] * 500
    filas += [("lavadoras", round(random.uniform(6000, 14000), 2)) for _ in range(400)]

    con = duckdb.connect()
    con.sql("CREATE TABLE q AS SELECT * FROM (VALUES " +
            ",".join(f"('{p}',{v})" for p, v in filas) + ") t(producto, precio)")
    con.sql("CREATE TABLE lg AS SELECT producto, ln(precio) l FROM q WHERE precio>0")
    con.sql("CREATE TABLE centro AS SELECT producto, median(l) mu, count(*) n FROM lg GROUP BY producto")
    con.sql("CREATE TABLE disp AS SELECT g.producto, median(abs(g.l-c.mu)) mad "
            "FROM lg g JOIN centro c USING(producto) GROUP BY g.producto")

    print("Centro y dispersión de cada producto (en escala logarítmica):")
    print(con.sql("SELECT c.producto, c.n, exp(c.mu) AS mediana, d.mad "
                  "FROM centro c JOIN disp d USING(producto)").df().round(4).to_string(index=False))
    print(f"\nAtípicos con z robusta > {Z_ROBUSTA}:")
    print(con.sql(f"""SELECT g.producto, exp(g.l) AS precio,
                             abs(g.l-c.mu)/(1.4826*d.mad) AS z
                      FROM lg g JOIN centro c USING(producto) JOIN disp d USING(producto)
                      WHERE d.mad>0 AND abs(g.l-c.mu)/(1.4826*d.mad) > {Z_ROBUSTA}
                      ORDER BY z DESC""").df().round(3).to_string(index=False))
    print("\nProductos con MAD = 0 (el detector NO los evalúa; se reportan aparte):")
    print(con.sql("SELECT producto, exp(c.mu) AS precio_dominante FROM disp d "
                  "JOIN centro c USING(producto) WHERE mad=0").df().to_string(index=False))
    print("\nLo que hay que ver aquí:")
    print("  · tortillas tiene MAD 0.04 y el detector caza 0.05, 850 y 1200.")
    print("  · lavadoras tiene MAD 0: más de la mitad de sus filas valen 9999.")
    print("    El detector no puede dividir entre cero, así que NO lo marca como")
    print("    atípico — lo manda a la lista de «mirar a mano». Ese es exactamente")
    print("    el caso que la regla del 10x p99 dejaba pasar en silencio.")


if __name__ == "__main__":
    import sys
    if "--demo" in sys.argv:
        demostracion()
        raise SystemExit

    if not any(PARQUETS.glob("*.parquet")):
        raise SystemExit(f"No hay parquets en {PARQUETS}. Corre antes perfilado_nivel2.py")

    con = conectar()
    total = con.sql("SELECT count(*) FROM q").fetchone()[0]
    print(f"=== {total:,} filas ===")

    print("\n" + "=" * 78)
    print("D0 · Por qué «>10x el p99» devolvía 0 y no podía devolver otra cosa")
    print("=" * 78)
    d0_la_regla_estaba_muerta(con)
    d0b_la_categoria_es_demasiado_gruesa(con)

    print("\n" + "=" * 78)
    print("D1 · Precios redondos anormalmente repetidos")
    print("=" * 78)
    d1 = d1_redondos_repetidos(con)
    confirmados = d1
    if d1.empty:
        print("  (ninguno)")
    else:
        d1["salto"] = d1.veces / d1.veces_vecinas.clip(lower=1)
        picos = d1[d1.salto >= SALTO].copy()
        # La separación que importa: dónde cae el precio dentro del rango de su
        # propio producto. Posición ≥ 0.99 = más caro que casi todo el resto, que
        # es donde vive un comodín. Abajo = es un precio real del mercado.
        es_candidato = ((picos.posicion >= POSICION_CENTINELA) |
                        (picos.razon_mediana >= RAZON_MEDIANA_CENTINELA))
        picos["clase"] = ["posible_centinela" if c else "punto_de_precio" for c in es_candidato]
        centinelas = picos[picos.clase == "posible_centinela"]
        puntos = picos[picos.clase == "punto_de_precio"]
        confirmados = picos

        print(f"  Precios redondos con ≥{MINIMO_VECES} repeticiones        : {len(d1)}")
        print(f"  De ésos, con salto ≥{SALTO}x sobre sus vecinos      : {len(picos)}")
        print(f"\n  Y de ésos, separados por DÓNDE caen en su producto:")
        print(f"    · punto_de_precio   : {len(puntos):>4} pares · {int(puntos.veces.sum()):>9,} "
              f"filas  ← precios REALES, no tocar")
        print(f"    · posible_centinela : {len(centinelas):>4} pares · {int(centinelas.veces.sum()):>9,} "
              f"filas  ← candidatos a revisar")
        print(f"      (candidato = posicion ≥ {POSICION_CENTINELA} o "
              f"razon_mediana ≥ {RAZON_MEDIANA_CENTINELA})")

        cols = ["producto", "precio", "veces", "n", "parte", "posicion",
                "mediana", "razon_mediana", "salto", "es_el_maximo"]
        if not centinelas.empty:
            print("\n  POSIBLES CENTINELAS — los 15 con más repeticiones:")
            print(centinelas.sort_values("veces", ascending=False)[cols]
                  .head(15).round(3).to_string(index=False))
        else:
            print("\n  Ningún precio redondo cae en el extremo alto de su producto.")
            print("  Eso es un hallazgo en sí: esta fuente puede no tener centinelas,")
            print("  sólo puntos de precio del comercio mexicano.")
        if not puntos.empty:
            print("\n  PUNTOS DE PRECIO — los 10 más grandes. Fíjate en `posicion` y")
            print("  `razon_mediana`: caen DENTRO del rango normal de su producto.")
            print(puntos.sort_values("veces", ascending=False)[cols]
                  .head(10).round(3).to_string(index=False))

    print("\n" + "=" * 78)
    print("D2 · Productos con la distribución ya contaminada")
    print("=" * 78)
    d2 = d2_distribucion_contaminada(con)
    if d2.empty:
        print("  (ninguno)")
    else:
        print(f"  Productos cuya mediana o moda ES un número redondo: {len(d2)}")
        print("  Puede ser un comodín que se comió el centro de la distribución, o")
        print("  puede ser que el producto simplemente se venda a ese precio. Lo que")
        print("  sí es seguro: en éstos ninguna regla de percentil sirve, porque el")
        print("  valor redondo ayudó a calcular el percentil. Hay que mirarlos.\n")
        print(d2.head(15).round(3).to_string(index=False))

    print("\n" + "=" * 78)
    print("D3 · Atípicos por dispersión robusta, en escala logarítmica")
    print("=" * 78)
    d3, sin_disp = d3_atipicos_robustos(con)
    tot3 = int(d3.filas_atipicas.sum()) if not d3.empty else 0
    print(f"  Filas marcadas (|z robusta| > {Z_ROBUSTA}) : {tot3:,} ({tot3/total:.4%})")
    print(f"  Productos con al menos una          : {len(d3)}")
    if not d3.empty:
        print("\n  Los 12 productos con más atípicos:")
        print(d3.head(12).round(2).to_string(index=False))
    if not sin_disp.empty:
        print(f"\n  Productos con MAD = 0 — más de la mitad de sus filas comparten")
        print(f"  el mismo precio exacto. Son {len(sin_disp)} y hay que mirarlos a mano:")
        print(sin_disp.head(10).round(2).to_string(index=False))

    print("\n" + "=" * 78)
    print("Resumen para la sección 2 de perfilado.md")
    print("=" * 78)
    n_cent = len(confirmados[confirmados.clase == "posible_centinela"]) if not confirmados.empty else 0
    f_cent = int(confirmados[confirmados.clase == "posible_centinela"].veces.sum()) if n_cent else 0
    n_pto = len(confirmados[confirmados.clase == "punto_de_precio"]) if not confirmados.empty else 0
    f_pto = int(confirmados[confirmados.clase == "punto_de_precio"].veces.sum()) if n_pto else 0
    print(f"  Regla anterior (>10x p99 por categoría)   : 0 filas — imposible que fuera otra cosa")
    print(f"  D1 posibles centinelas                    : {n_cent} pares · {f_cent:,} filas "
          f"({f_cent/total:.4%})")
    print(f"  D1 puntos de precio (NO son error)        : {n_pto} pares · {f_pto:,} filas "
          f"({f_pto/total:.4%})")
    print(f"  D2 productos con distribución contaminada : {len(d2)} productos")
    print(f"  D3 atípicos robustos por producto         : {tot3:,} filas ({tot3/total:.4%})")

    if not confirmados.empty:
        SALIDA.mkdir(parents=True, exist_ok=True)
        todo = SALIDA / "precios-redondos-clasificados.csv"
        confirmados.sort_values("veces", ascending=False).to_csv(todo, index=False)
        cent = confirmados[confirmados.clase == "posible_centinela"]
        destino = SALIDA / "centinelas-confirmados.csv"
        cent.sort_values("veces", ascending=False).to_csv(destino, index=False)
        print(f"\n  {todo}")
        print(f"     todos los precios redondos repetidos, con su clase")
        print(f"  {destino}")
        print(f"     SÓLO los {n_cent} candidatos a comodín — ésos son los que van al contrato")
        print("\n  La regla del contrato es el par (producto, precio) medido, nunca un")
        print("  `precio NOT IN (999, 9999)` a ciegas: el 9 del yoghurt y el 99 del")
        print("  shampoo son precios reales y tirarlos sería inventar un problema.")
        print("\n  ANTES DE ESCRIBIRLA EN EL CONTRATO, mira a mano los candidatos:")
        print("  un comodín se reconoce porque el precio es absurdo PARA ESE PRODUCTO,")
        print("  y eso lo decide una persona, no el percentil.")
