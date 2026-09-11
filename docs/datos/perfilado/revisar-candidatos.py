"""
Revisión de los candidatos a centinela · QQP

`centinelas.py` deja una lista corta de pares (producto, precio) sospechosos y
dice, con razón, que la decisión final es de una persona. Este guión hace la
comprobación que esa persona necesita para decidir, en vez de dejarla a ojo.

La pregunta que resuelve
------------------------
Un candidato sale sospechoso porque su precio es alto comparado con la MEDIANA
DE SU PRODUCTO. Pero `producto` es una etiqueta gruesa: «yoghurt» cubre un
vasito de 150 g y un bote de un kilo; «termometro» cubre uno de mercurio de $30
y uno infrarrojo de $1,300. Si el precio alto corresponde a una presentación
GRANDE, entonces no es un comodín: es un producto distinto con la misma
etiqueta, y el problema era la agrupación, no el dato.

Así que se baja un nivel:

  1. ¿Qué presentaciones aparecen exactamente a ese precio?
  2. Esas mismas presentaciones, en el resto de sus filas, ¿cuánto cuestan?

Si el precio candidato se parece a lo que cuestan sus propias presentaciones,
es un PRECIO REAL y lo que estaba mal era comparar contra la mediana de toda
la etiqueta. Si sigue disparado incluso contra su propia presentación, ahí sí
hay algo que explicar.

Uso
---
    python docs/datos/perfilado/revisar-candidatos.py
    CANASTAMX_DATOS=/otra/ruta python docs/datos/perfilado/revisar-candidatos.py

Necesita que centinelas.py haya dejado centinelas-confirmados.csv.
"""
import os
from pathlib import Path

import duckdb

RAIZ = Path(os.environ.get("CANASTAMX_DATOS", Path.home() / "canastamx-datos"))
PARQUETS = RAIZ / "procesado" / "por_archivo"
SALIDA = Path("docs/datos/perfilado")
CANDIDATOS = SALIDA / "centinelas-confirmados.csv"

# Si el precio candidato está a menos de esta razón de lo que cuestan sus
# propias presentaciones, se considera precio real. 1.5 es holgado a propósito:
# la idea es descartar con confianza, no acusar.
RAZON_LIMPIA = 1.5


def conectar():
    con = duckdb.connect()
    con.sql("SET memory_limit='4GB'")
    tmp = RAIZ / "tmp-duckdb"
    tmp.mkdir(parents=True, exist_ok=True)
    con.sql(f"SET temp_directory='{tmp}'")
    fuente = f"read_parquet('{PARQUETS}/*.parquet', union_by_name=true)"
    con.sql(f"""
        CREATE VIEW base AS
        SELECT lower(strip_accents(trim(producto))) AS producto,
               presentacion, precio
        FROM {fuente} WHERE precio IS NOT NULL AND precio > 0
    """)
    con.sql(f"""CREATE TABLE cand AS
                SELECT producto, precio, veces, mediana, razon_mediana
                FROM read_csv('{CANDIDATOS}')""")
    return con


def comparar_contra_su_presentacion(con):
    """Compara el precio candidato contra el de SUS PROPIAS presentaciones."""
    return con.sql(f"""
        WITH pres_cand AS (
            -- qué presentaciones aparecen exactamente al precio candidato
            SELECT c.producto, c.precio AS precio_cand, b.presentacion,
                   count(*) AS filas_al_precio
            FROM cand c
            JOIN base b ON b.producto = c.producto AND b.precio = c.precio
            GROUP BY 1, 2, 3
        ),
        resto AS (
            -- esas mismas presentaciones, a cualquier OTRO precio
            SELECT p.producto, p.precio_cand,
                   median(b.precio) AS mediana_de_su_presentacion,
                   count(*) AS filas_comparadas
            FROM pres_cand p
            JOIN base b ON b.producto = p.producto
                       AND b.presentacion = p.presentacion
                       AND b.precio <> p.precio_cand
            GROUP BY 1, 2
        )
        SELECT c.producto, c.precio, c.veces,
               c.mediana                       AS mediana_del_producto,
               c.razon_mediana                 AS razon_vs_producto,
               r.mediana_de_su_presentacion,
               c.precio / nullif(r.mediana_de_su_presentacion, 0)
                                               AS razon_vs_presentacion,
               r.filas_comparadas,
               (SELECT count(DISTINCT presentacion) FROM pres_cand p2
                 WHERE p2.producto = c.producto AND p2.precio_cand = c.precio)
                                               AS presentaciones_a_ese_precio
        FROM cand c
        LEFT JOIN resto r ON r.producto = c.producto AND r.precio_cand = c.precio
        ORDER BY c.veces DESC
    """).df()


def presentaciones_de(con, producto, precio, n=4):
    """Las presentaciones más comunes a ese precio y a los demás precios."""
    arriba = con.sql(f"""
        SELECT presentacion, count(*) AS filas
        FROM base WHERE producto = ? AND precio = ?
        GROUP BY 1 ORDER BY filas DESC LIMIT {n}
    """, params=[producto, precio]).df()
    normal = con.sql(f"""
        SELECT presentacion, count(*) AS filas, round(median(precio), 2) AS precio_mediano
        FROM base WHERE producto = ? AND precio <> ?
        GROUP BY 1 ORDER BY filas DESC LIMIT {n}
    """, params=[producto, precio]).df()
    return arriba, normal


if __name__ == "__main__":
    if not CANDIDATOS.exists():
        raise SystemExit(f"No encuentro {CANDIDATOS}. Corre antes centinelas.py")
    con = conectar()
    n_cand = con.sql("SELECT count(*) FROM cand").fetchone()[0]
    print("=" * 78)
    print(f"Revisión de los {n_cand} candidatos a centinela")
    print("=" * 78)
    print("La pregunta no es «¿este precio es alto?» sino «¿es alto PARA LA")
    print("PRESENTACIÓN que tiene?». Un yoghurt de un kilo a $99 no es un comodín:")
    print("es un yoghurt de un kilo.\n")

    r = comparar_contra_su_presentacion(con)
    r["veredicto"] = [
        "precio real" if (rv is not None and rv == rv and rv < RAZON_LIMPIA)
        else "sigue raro"
        for rv in r.razon_vs_presentacion
    ]
    cols = ["producto", "precio", "veces", "mediana_del_producto",
            "razon_vs_producto", "mediana_de_su_presentacion",
            "razon_vs_presentacion", "presentaciones_a_ese_precio", "veredicto"]
    print(r[cols].round(3).to_string(index=False))

    limpios = (r.veredicto == "precio real").sum()
    print(f"\n  {limpios} de {len(r)} se explican solos al bajar a la presentación.")
    print(f"  Los otros {len(r) - limpios} hay que mirarlos uno por uno, abajo.")

    raros = r[r.veredicto == "sigue raro"]
    for _, fila in raros.iterrows():
        print("\n" + "─" * 78)
        print(f"{fila.producto} a ${fila.precio:,.2f} — {int(fila.veces):,} veces")
        print(f"  mediana del producto: ${fila.mediana_del_producto:,.2f}")
        if fila.mediana_de_su_presentacion == fila.mediana_de_su_presentacion:
            print(f"  mediana de SUS presentaciones: "
                  f"${fila.mediana_de_su_presentacion:,.2f}  "
                  f"(razón {fila.razon_vs_presentacion:.2f}x)")
        else:
            print("  Ninguna de sus presentaciones aparece a otro precio: no hay")
            print("  con qué compararlo. Eso ya es raro por sí solo.")
        arriba, normal = presentaciones_de(con, fila.producto, fila.precio)
        print(f"\n  Presentaciones A ESE PRECIO:")
        print("    " + arriba.to_string(index=False).replace("\n", "\n    "))
        print(f"\n  Presentaciones del producto en general:")
        print("    " + normal.to_string(index=False).replace("\n", "\n    "))

    SALIDA.mkdir(parents=True, exist_ok=True)
    destino = SALIDA / "candidatos-revisados.csv"
    r[cols].to_csv(destino, index=False)
    print("\n" + "=" * 78)
    print(f"Tabla completa en {destino}")
    print("Al contrato sólo van los que sigan raros DESPUÉS de esta revisión y")
    print("después de que una persona mire la presentación y diga «eso no puede")
    print("costar eso». Un comodín se reconoce por el producto, no por el número.")
