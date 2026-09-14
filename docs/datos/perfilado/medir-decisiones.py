"""
Las cifras que faltan después de la reunión del 11 de septiembre · QQP

Por qué existe este guión
-------------------------
En la reunión del 11 se decidieron cosas que cambian el tamaño del proyecto, y
ninguna venía con un número. Este guión las mide todas de una pasada, para que
el ADR 001, el ADR 002 y el contrato de datos de la semana 2 se escriban con
cifras y no con estimaciones de sobremesa.

Lo que se decidió:

  1. La base de trabajo queda NACIONAL y local (en la máquina de A), pero
     **el producto desplegado cubre siete entidades de centro-occidente**:
     Aguascalientes, Guanajuato, Jalisco, Michoacán, Querétaro,
     San Luis Potosí y Zacatecas. El primer despliegue arranca sólo con
     Guanajuato y de ahí crece.
  2. El artículo se identifica por **producto + presentacion**, y `marca`
     deja de ser parte de la identidad para volverse un atributo por el que
     se ordena y se filtra.

De la primera decisión salen tres preguntas que el ADR 001 necesita
contestadas con cifras, no con estimaciones de sobremesa:

  · ¿Cuántas filas tiene el recorte de siete entidades?  Porque el protocolo
    comprometió «entre dos y cuatro millones» y hay que saber si ese número
    ahora se sostiene o hay que corregirlo.
  · ¿Cuánto pesa? Se descartó Supabase para los 21 millones. Nadie ha
    comprobado que Supabase aguante los siete estados. Mejor saberlo el lunes
    que en noviembre.
  · ¿Cuánto es Guanajuato solo? Es el primer despliegue.

De la segunda sale una más, y es la que puede romper la ingesta:

  · Si `marca` ya no identifica al artículo, ¿la clave de unicidad del
    CONTRATO también deja de llevarla? **No.** Son dos claves distintas y
    este guión lo demuestra con el conteo, porque si A escribe el contrato
    con la clave equivocada, la compuerta de calidad va a rechazar millones
    de filas legítimas el día de la primera ingesta.

Y una que NO se decidió, y que el protocolo sí compromete:

  · La sección 8 del protocolo dice «recorte de productos a la canasta básica,
    conforme a la clasificación de productos de consumo generalizado de la
    fuente». Esa clasificación **es la columna `catalogo`**, que trae 16
    valores. Nadie ha decidido cuáles entran. Mientras no se decida, el
    producto le muestra al usuario una pantalla de televisión junto al kilo de
    tortilla. Este guión lista los 16 con su volumen y su precio mediano, para
    que la decisión se tome mirando la lista.

Uso
---
    python docs/datos/perfilado/medir-decisiones.py
    CANASTAMX_DATOS=/otra/ruta python docs/datos/perfilado/medir-decisiones.py

Salidas
-------
    docs/datos/perfilado/salidas/estados-literales.csv
    docs/datos/perfilado/salidas/catalogos.csv
    docs/datos/perfilado/salidas/recorte-resumen.csv
"""
import os
from pathlib import Path

import duckdb

RAIZ = Path(os.environ.get("CANASTAMX_DATOS", Path.home() / "canastamx-datos"))
PARQUETS = RAIZ / "procesado" / "por_archivo"
SALIDA = Path("docs/datos/perfilado/salidas")

# Lo que el protocolo comprometió en Alcances, para poder contrastar.
PROTOCOLO_MIN = 2_000_000
PROTOCOLO_MAX = 4_000_000

# Lo que aguanta el plan gratuito de Supabase. Si el recorte no cabe, hay que
# saberlo ahora: son 500 MB de base, no de archivo.
SUPABASE_MB = 500

# Las siete entidades, escritas como quedan después de quitar acentos y pasar a
# minúsculas. Se comparan por PREFIJO porque la fuente escribe algunas con
# apellido: «MICHOACÁN DE OCAMPO», «QUERÉTARO DE ARTEAGA».
SIETE = [
    "aguascalientes",
    "guanajuato",
    "jalisco",
    "michoacan",
    "queretaro",
    "san luis potosi",
    "zacatecas",
]
PRIMER_DESPLIEGUE = "guanajuato"

ANIOS = (2025, 2026)

NORM_EDO = "trim(lower(strip_accents(estado)))"
FILTRO_SIETE = " OR ".join(f"{NORM_EDO} LIKE '{e}%'" for e in SIETE)
FILTRO_ANIO = f"year(fecha_registro) BETWEEN {ANIOS[0]} AND {ANIOS[1]}"

# Las once columnas de texto que van a Postgres. `folio`, `cv_producto` y
# `cv_marca` NO están: se decidió no ingerirlas (ADR 001, decisión 2.4).
TEXTO = ["producto", "presentacion", "marca", "categoria", "catalogo",
         "cadena_comercial", "giro", "nombre_comercial", "direccion",
         "estado", "municipio"]

# Bytes por fila que no son texto, estimando en Postgres:
#   precio 8 · latitud 8 · longitud 8 · fecha 4 · encabezado de fila 24
#   + ~1 byte de encabezado por cada campo de texto variable
FIJOS_POR_FILA = 8 + 8 + 8 + 4 + 24 + len(TEXTO)


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


def literales_de_estado(con):
    """Los 37 literales con su forma normalizada, para poder auditar el mapeo.

    Existe porque el perfilado encontró 37 formas de escribir 30 entidades.
    Antes de filtrar por siete estados hay que poder mirar con qué literal se
    quedó cada uno, y con cuál no.
    """
    return con.sql(f"""
        SELECT estado                                   AS literal,
               {NORM_EDO}                               AS normalizado,
               ({FILTRO_SIETE})                         AS entra_al_recorte,
               count(*)                                 AS filas
        FROM q
        GROUP BY 1, 2, 3
        ORDER BY entra_al_recorte DESC, filas DESC
    """).df()


def cobertura(con):
    """Cuántas filas quedan tras cada recorte, y cuánto quita cada uno por separado."""
    return con.sql(f"""
        SELECT
            count(*)                                                  AS total,
            count(*) FILTER (WHERE {FILTRO_ANIO})                      AS solo_anios,
            count(*) FILTER (WHERE {FILTRO_SIETE})                     AS solo_siete,
            count(*) FILTER (WHERE ({FILTRO_SIETE}) AND {FILTRO_ANIO}) AS recorte,
            count(*) FILTER (WHERE {NORM_EDO} LIKE '{PRIMER_DESPLIEGUE}%'
                             AND {FILTRO_ANIO})                        AS primer_despliegue
        FROM q
    """).fetchone()


def forma_del_recorte(con):
    """Productos, cadenas y establecimientos dentro del recorte desplegado."""
    return con.sql(f"""
        SELECT count(DISTINCT producto)                        AS productos,
               count(DISTINCT (producto, presentacion))        AS articulos,
               count(DISTINCT cadena_comercial)                AS cadenas,
               count(DISTINCT (nombre_comercial, direccion))   AS establecimientos,
               count(DISTINCT estado)                          AS literales_estado,
               min(fecha_registro)                             AS desde,
               max(fecha_registro)                             AS hasta
        FROM q
        WHERE ({FILTRO_SIETE}) AND {FILTRO_ANIO}
    """).fetchone()


def peso_estimado(con):
    """Estimación gruesa de cuánto ocupa el recorte en Postgres, sin índices.

    No es una medición: es una cota para decidir si vale la pena intentar
    Supabase o ni acercarse. Los índices suelen agregar entre 30% y 60%.
    """
    suma = " + ".join(f"coalesce(strlen({c}), 0)" for c in TEXTO)
    return con.sql(f"""
        SELECT count(*)               AS filas,
               sum({suma})            AS bytes_texto,
               avg({suma})            AS bytes_texto_por_fila
        FROM q
        WHERE ({FILTRO_SIETE}) AND {FILTRO_ANIO}
    """).fetchone()


def clave_de_unicidad(con, donde, etiqueta):
    """Prueba tres claves candidatas sobre el mismo conjunto de filas.

    La pregunta que contesta: si el contrato declara esta combinación como
    única, ¿cuántas filas legítimas rechazaría la compuerta de calidad?

    `sobran` = filas − combinaciones distintas. Un cero significa que la clave
    identifica una fila y sólo una. Cualquier otro número son filas reales que
    la compuerta tiraría por creerlas duplicadas.
    """
    filas = ("producto, nombre_comercial, direccion, fecha_registro",
             "producto, presentacion, nombre_comercial, direccion, fecha_registro",
             "producto, presentacion, marca, nombre_comercial, direccion, fecha_registro")
    nombres = ("la del protocolo (sin presentacion ni marca)",
               "identidad del articulo + establecimiento + fecha",
               "la anterior + marca")
    salida = []
    for nombre, cols in zip(nombres, filas):
        total, distintas = con.sql(f"""
            SELECT count(*), count(DISTINCT ({cols})) FROM q WHERE {donde}
        """).fetchone()
        salida.append((etiqueta, nombre, total, distintas, total - distintas))
    return salida


def catalogos(con):
    """Los valores de `catalogo`: la clasificación propia de la fuente.

    El protocolo compromete en Alcances un «recorte de productos a la canasta
    básica, conforme a la clasificación de productos de consumo generalizado de
    la fuente». Esa clasificación es esta columna, y no está decidida.

    Se imprime con el precio mediano y el máximo de cada catálogo porque es lo
    que hace obvia la decisión: un catálogo cuyo precio mediano son cientos de
    pesos no es canasta básica, se llame como se llame.
    """
    return con.sql(f"""
        SELECT catalogo,
               count(*)                   AS filas,
               count(DISTINCT producto)   AS productos,
               round(median(precio), 2)   AS precio_mediano,
               round(max(precio), 2)      AS precio_maximo
        FROM q
        WHERE ({FILTRO_SIETE}) AND {FILTRO_ANIO}
        GROUP BY 1
        ORDER BY filas DESC
    """).df()


def articulos_por_nivel(con):
    """Cuántos artículos hay según dónde se ponga la frontera de «el mismo artículo».

    Existe para corregir un número mal puesto. La tabla de `perfilado.md` y el
    informe traían «~6,000» para `producto` + `presentacion` y «5,750» para el
    trío con `marca`. **Eso no puede ser:** agregar una columna a una clave
    nunca reduce el número de claves distintas. El ~6,000 era una estimación a
    ojo y se coló como si fuera medida. Aquí se miden los tres niveles de una
    sola pasada y con la misma normalización, para que sean comparables.

    Se mide sobre las filas SIN `?`, igual que `perfilado_nivel3.py`: el signo
    de interrogación no se normaliza a la letra que se comió, y `Art?culos`
    contaría como un artículo aparte de `Artículos`.
    """
    norm = ("trim(regexp_replace(regexp_replace(lower(strip_accents({0})), "
            "'[^a-z0-9 ]', ' ', 'g'), '\\s+', ' ', 'g'))")
    return con.sql(f"""
        WITH limpio AS (
            SELECT {norm.format('producto')}     AS p,
                   {norm.format('presentacion')} AS pr,
                   {norm.format('marca')}        AS m
            FROM q
            WHERE producto     NOT LIKE '%?%'
              AND presentacion NOT LIKE '%?%'
              AND marca        NOT LIKE '%?%'
        )
        SELECT count(*)                       AS filas,
               count(DISTINCT p)              AS solo_producto,
               count(DISTINCT (p, pr))        AS producto_presentacion,
               count(DISTINCT (p, pr, m))     AS con_marca
        FROM limpio
    """).fetchone()


def sin_marca(con):
    """Cuánto del recorte declara `S/m`, y si eso choca con la clave.

    Importa porque se decidió que `S/m` es una categoría propia. Si dos filas
    del mismo establecimiento, el mismo día, traen el mismo producto y la misma
    presentacion con `S/m` las dos, `marca` deja de desempatarlas.
    """
    return con.sql(f"""
        SELECT count(*)                                                   AS filas,
               count(*) FILTER (WHERE upper(trim(marca)) = 'S/M')         AS con_sm,
               count(DISTINCT marca) FILTER (WHERE upper(trim(marca)) = 'S/M')
                                                                          AS literales_sm
        FROM q
        WHERE ({FILTRO_SIETE}) AND {FILTRO_ANIO}
    """).fetchone()


def pct(parte, todo):
    return f"{parte / todo:.2%}" if todo else "—"


if __name__ == "__main__":
    if not any(PARQUETS.glob("*.parquet")):
        raise SystemExit(f"No hay parquets en {PARQUETS}. Corre antes perfilado_nivel2.py")
    con = conectar()
    SALIDA.mkdir(parents=True, exist_ok=True)

    print("=" * 78)
    print("El recorte decidido el 11 de septiembre · siete entidades · 2025-2026")
    print("=" * 78)

    # ── 1 · qué literal de `estado` entra y cuál no
    lit = literales_de_estado(con)
    lit.to_csv(SALIDA / "estados-literales.csv", index=False)
    dentro = lit[lit.entra_al_recorte]
    fuera = lit[~lit.entra_al_recorte]
    print(f"\n── Literales de `estado` que entran al recorte ({len(dentro)} de {len(lit)})")
    print(dentro[["literal", "filas"]].to_string(index=False))
    print(f"\n   Quedan fuera {len(fuera)} literales. Los cinco más grandes:")
    print(fuera[["literal", "filas"]].head(5).to_string(index=False))
    print(f"\n   Lista completa en {SALIDA / 'estados-literales.csv'} — revísala antes de")
    print("   dar el número por bueno: si una entidad se escribe de dos maneras y una")
    print("   no empieza igual, el filtro la deja fuera sin avisar.")

    # ── 2 · cuánto quita cada recorte
    total, solo_anios, solo_siete, recorte, gto = cobertura(con)
    print("\n" + "=" * 78)
    print("Cuánto quita cada decisión, por separado")
    print("=" * 78)
    print(f"  Corpus completo                        : {total:>12,}")
    print(f"  Sólo 2025-2026                         : {solo_anios:>12,}  "
          f"(quita {total - solo_anios:,})")
    print(f"  Sólo las siete entidades               : {solo_siete:>12,}  "
          f"(quita {total - solo_siete:,})")
    print(f"  Las dos juntas → RECORTE DESPLEGADO    : {recorte:>12,}  "
          f"({pct(recorte, total)} del corpus)")
    print(f"  Primer despliegue (Guanajuato solo)    : {gto:>12,}  "
          f"({pct(gto, recorte)} del recorte)")

    if total == solo_anios:
        print("\n  Nota: el filtro de año no quita NADA. La fuente descargada ya es")
        print("  2025-2026 completa. La decisión de la ventana no reduce volumen:")
        print("  lo que reduce es el territorio. Eso hay que decirlo tal cual en el ADR.")

    # ── 3 · contra lo que comprometió el protocolo
    print("\n" + "=" * 78)
    print("Contra el protocolo · comprometió «entre dos y cuatro millones»")
    print("=" * 78)
    if PROTOCOLO_MIN <= recorte <= PROTOCOLO_MAX:
        print(f"  {recorte:,} filas CAE DENTRO del rango comprometido.")
        print("  El recorte territorial rescata la cifra del protocolo: no hay que")
        print("  corregir el volumen, sólo la ventana (2024-2026 → 2025-2026).")
    elif recorte > PROTOCOLO_MAX:
        print(f"  {recorte:,} filas EXCEDE el máximo comprometido ({PROTOCOLO_MAX:,}).")
        print(f"  Sobran {recorte - PROTOCOLO_MAX:,}. Hay que corregir el volumen en el")
        print("  protocolo, con esta cifra y su fecha de medición.")
    else:
        print(f"  {recorte:,} filas QUEDA POR DEBAJO del mínimo ({PROTOCOLO_MIN:,}).")
        print("  Hay que corregir el protocolo a la baja, o revisar si el filtro de")
        print("  entidades está dejando literales fuera (mira la lista de arriba).")

    # ── 4 · forma del recorte
    prods, arts, cadenas, establecimientos, lits, desde, hasta = forma_del_recorte(con)
    print("\n── Qué hay dentro del recorte")
    print(f"   productos distintos                  : {prods:,}")
    print(f"   artículos (producto + presentacion)  : {arts:,}")
    print(f"   cadenas comerciales                  : {cadenas:,}")
    print(f"   establecimientos                     : {establecimientos:,}")
    print(f"   rango de fechas                      : {desde} a {hasta}")

    # ── 5 · si cabe en Supabase
    filas_p, bytes_texto, bytes_fila = peso_estimado(con)
    crudo = bytes_texto + filas_p * FIJOS_POR_FILA
    mb = crudo / 1024 / 1024
    print("\n" + "=" * 78)
    print(f"¿Cabe en Supabase? · plan gratuito = {SUPABASE_MB} MB de base")
    print("=" * 78)
    print(f"  Bytes de texto por fila (medidos)      : {bytes_fila:.1f}")
    print(f"  Estimación de tabla sin índices        : {mb:,.0f} MB")
    print(f"  Con índices (+30% a +60%)              : {mb*1.3:,.0f} a {mb*1.6:,.0f} MB")
    if mb * 1.6 < SUPABASE_MB:
        print(f"\n  CABE con holgura. Supabase es viable para las siete entidades.")
    elif mb * 1.3 < SUPABASE_MB:
        print(f"\n  CABE JUSTO, y sólo si los índices salen baratos. Conviene arrancar")
        print(f"  con Guanajuato ({gto:,} filas) y medir de verdad antes de subir el resto.")
    else:
        print(f"\n  NO CABE. Se descartó Supabase por los 21 millones, pero tampoco")
        print(f"  aguanta los siete estados. Guanajuato solo serían ~{mb*gto/max(recorte,1):,.0f} MB:")
        print(f"  el despliegue por etapas que se acordó deja de ser una preferencia y")
        print(f"  pasa a ser la única forma. Hay que decidir a qué se migra al crecer, y")
        print(f"  eso es un ADR aparte.")
    print("\n  Es una ESTIMACIÓN, no una medición. La medición de verdad es cargar")
    print("  Guanajuato y mirar el tamaño real de la tabla.")

    # ── 6 · la clave de unicidad
    print("\n" + "=" * 78)
    print("La clave de unicidad del contrato · lo que A escribe el lunes")
    print("=" * 78)
    pruebas = (clave_de_unicidad(con, "TRUE", "corpus completo")
               + clave_de_unicidad(con, f"({FILTRO_SIETE}) AND {FILTRO_ANIO}", "recorte"))
    import pandas as pd
    tabla = pd.DataFrame(pruebas, columns=["ambito", "clave", "filas", "distintas", "sobran"])
    tabla["sobran_pct"] = (tabla.sobran / tabla.filas).map("{:.2%}".format)
    tabla.to_csv(SALIDA / "recorte-resumen.csv", index=False)
    print(tabla.to_string(index=False))
    print(f"\n  `sobran` = filas que la compuerta de calidad RECHAZARÍA por creerlas")
    print(f"  duplicadas si el contrato declara esa combinación como única.")

    del_recorte = tabla[tabla.ambito == "recorte"]
    con_marca = del_recorte.iloc[2]
    sin_marca_fila = del_recorte.iloc[1]
    if con_marca.sobran < sin_marca_fila.sobran:
        print(f"\n  Agregar `marca` a la clave salva {sin_marca_fila.sobran - con_marca.sobran:,}")
        print("  filas legítimas. Eso confirma que son DOS claves distintas:")
        print("    · identidad del artículo (lo que ve el usuario) : producto + presentacion")
        print("    · clave de fila del contrato                    : + marca + establecimiento + fecha")
        print("  El ADR 002 tiene que decir las dos, o el contrato sale mal.")

    # ── 7 · el recorte de productos que el protocolo pide y nadie decidió
    cat = catalogos(con)
    cat.to_csv(SALIDA / "catalogos.csv", index=False)
    print("\n" + "=" * 78)
    print("El recorte de PRODUCTOS · lo que el protocolo pide y no se ha decidido")
    print("=" * 78)
    print("  El protocolo, sección 8: «recorte de productos a la canasta básica,")
    print("  conforme a la clasificación de productos de consumo generalizado de la")
    print("  fuente». Esa clasificación es la columna `catalogo`. Estos son sus")
    print("  valores dentro del recorte de siete entidades:\n")
    print(cat.to_string(index=False))
    caros = cat[cat.precio_mediano > 300]
    if not caros.empty:
        print(f"\n  {len(caros)} catálogo(s) con precio mediano arriba de $300. Difícil")
        print("  llamarles canasta básica. Ésa es la decisión que falta: cuáles de")
        print(f"  los {len(cat)} entran. Va a la reunión del miércoles 16.")

    # ── 8 · cuántos artículos hay en cada nivel
    f_lim, n_prod, n_pp, n_ppm = articulos_por_nivel(con)
    print("\n" + "=" * 78)
    print("Cuántos artículos hay según dónde se ponga la frontera")
    print("=" * 78)
    print(f"  (medido sobre {f_lim:,} filas sin `?`)")
    print(f"  `producto` solo                        : {n_prod:>9,}")
    print(f"  `producto` + `presentacion`  ← DECIDIDO: {n_pp:>9,}")
    print(f"  `producto` + `presentacion` + `marca`  : {n_ppm:>9,}")
    print(f"\n  Corrige la tabla de perfilado.md y del informe, que traían «~6,000»")
    print(f"  para el nivel de en medio y «5,750» para el de abajo. Ese ~6,000 era")
    print(f"  una estimación a ojo y no podía ser: agregar `marca` a la clave nunca")
    print(f"  reduce el número de artículos. El número bueno es {n_pp:,}.")

    # ── 9 · S/m
    f_rec, con_sm, lits_sm = sin_marca(con)
    print("\n── `S/m` dentro del recorte")
    print(f"   filas sin marca declarada            : {con_sm:,} ({pct(con_sm, f_rec)})")
    print(f"   formas distintas de escribirlo       : {lits_sm}")
    if lits_sm > 1:
        print("   Se escribe de más de una manera. El contrato tiene que normalizarlo")
        print("   a un solo literal, o `S/m` no va a ser una categoría: van a ser dos.")

    print("\n" + "=" * 78)
    print("Qué hacer con estas cifras")
    print("=" * 78)
    print("  · El volumen del recorte va al ADR 001, sección Consecuencias, junto")
    print("    con la corrección al protocolo.")
    print("  · La clave que gane va al contrato de datos de la semana 2 (`contracts/`).")
    print("  · El número de Guanajuato va a B y a C2: es el tamaño del primer")
    print("    despliegue y de los datos semilla.")
