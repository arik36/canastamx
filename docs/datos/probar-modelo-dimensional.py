"""
probar-modelo-dimensional.py — T031 · el esquema estrella, armado y medido

Arma EN MEMORIA el modelo de docs/datos/modelo-dimensional.md sobre la capa
cruda (T020), con las reglas del contrato 1.3.3, y mide lo que el documento
necesita: tamaños, completitud, cuarentena, peso y las tres consultas de la
prueba del grano. No escribe nada en MinIO ni en Postgres.

POBLACIÓN: ALCANCE DEL CONTRATO. El recorte se vuelve a aplicar aquí, así que
da lo mismo leer la capa cruda o los parquet completos del corpus.

Uso, desde la raíz del repositorio:

    # la capa cruda en MinIO, con las S3_* de tu .env cargadas
    python docs/datos/probar-modelo-dimensional.py
    # y, además, escribir las cifras dentro del documento
    python docs/datos/probar-modelo-dimensional.py --escribir docs/datos/modelo-dimensional.md

    # o cualquier conjunto de parquet con las 15 columnas del contrato
    python docs/datos/probar-modelo-dimensional.py --origen "$HOME/canastamx-datos/procesado/por_archivo/*.parquet"
"""

import argparse
import datetime as dt
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

RAIZ = Path(__file__).resolve().parents[2]
CONTRATO = RAIZ / "contracts" / "qqp-v1.yaml"
DICCIONARIO = RAIZ / "contracts" / "mojibake-diccionario.csv"
INICIO, FIN = "<!-- cifras:inicio -->", "<!-- cifras:fin -->"

# Medido por verificar-precios.py el 15-sep, SIN normalizar y antes de reparar el
# `?`. Con la comparación del contrato 1.3.3 puede subir un poco: es esperado.
COLISIONES_CONTRATO = {"captura_doble": 72_631, "observacion_multiple": 2_105,
                       "colision_precio_alta": 256}

CANON = (r"trim(regexp_replace(regexp_replace(lower(strip_accents({x})),"
         r" '[^a-z0-9 ]', ' ', 'g'), '\s+', ' ', 'g'))")


def morir(msg):
    print(f"\n✗ {msg}", file=sys.stderr)
    sys.exit(1)


def canon(x):
    return CANON.format(x=x)


def esc(v):
    return str(v).replace("'", "''")


def conectar(origen):
    import duckdb
    con = duckdb.connect()
    if not origen.startswith("s3://"):
        return con
    faltan = [v for v in ("S3_ENDPOINT", "S3_ACCESS_KEY", "S3_SECRET_KEY") if not os.environ.get(v)]
    if faltan:
        morir("faltan variables de entorno: " + ", ".join(faltan) + ". Carga tu .env: set -a; source .env; set +a")
    url = urlparse(os.environ["S3_ENDPOINT"])
    con.sql("INSTALL httpfs; LOAD httpfs;")
    con.sql(f"SET s3_endpoint='{url.netloc}'")
    con.sql(f"SET s3_access_key_id='{os.environ['S3_ACCESS_KEY']}'")
    con.sql(f"SET s3_secret_access_key='{os.environ['S3_SECRET_KEY']}'")
    con.sql("SET s3_url_style='path'")
    con.sql(f"SET s3_use_ssl={'true' if url.scheme == 'https' else 'false'}")
    con.sql("SET s3_region='us-east-1'")
    return con


def construir(con, contrato, origen, diccionario):
    """Capa intermedia mínima + estrella, con las reglas del contrato 1.3.3."""
    cols = list(contrato["columnas"])
    alc = contrato["alcance"]
    desde, hasta = alc["ventana"]["desde"], alc["ventana"]["hasta"]
    ent_sql = " ".join(f"WHEN upper(strip_accents(trim(estado))) = upper(strip_accents('{esc(e)}')) "
                       f"THEN '{esc(e)}'" for e in alc["entidades"])
    cats = ", ".join(f"'{esc(c)}'" for c in alc["catalogos_normalizados"])
    con.sql(f"""CREATE TABLE alcance AS
                SELECT {', '.join(cols)}, row_number() OVER () AS rid, CASE {ent_sql} END AS entidad
                FROM read_parquet('{origen}', union_by_name=true)
                WHERE (CASE {ent_sql} END) IS NOT NULL
                  AND upper(strip_accents(trim(catalogo))) IN ({cats})
                  AND CAST(fecha_registro AS DATE) BETWEEN DATE '{desde}' AND DATE '{hasta}'""")

    # Reparar el `?` con el diccionario del contrato (reparar_interrogantes)
    con.sql(f"CREATE TABLE dicc AS SELECT * FROM read_csv('{diccionario}', header=true, all_varchar=true)")
    con_dicc = {r[0] for r in con.sql("SELECT DISTINCT columna FROM dicc").fetchall()}
    texto = [c for c in cols if contrato["columnas"][c]["tipo"] == "texto"]
    partes, uniones = [], []
    for i, c in enumerate(texto):
        if c in con_dicc:
            partes.append(f"coalesce(d{i}.reparado, s.{c}) AS {c}")
            uniones.append(f"LEFT JOIN dicc d{i} ON d{i}.columna = '{c}' AND d{i}.valor_roto = s.{c}")
        else:
            partes.append(f"s.{c}")
    llave_txt = ["producto", "presentacion", "marca", "nombre_comercial", "direccion", "municipio"]
    con.sql(f"""CREATE TABLE limpio AS
                SELECT r.*,
                       {canon('r.producto')} AS producto_c, {canon('r.presentacion')} AS presentacion_c,
                       upper(strip_accents(trim(r.marca))) AS marca_n,
                       upper(strip_accents(trim(r.catalogo))) AS catalogo_n,
                       {canon('r.categoria')} AS categoria_c, regexp_replace({canon('r.cadena_comercial')}, 's$', '') AS cadena_c,
                       {canon('r.nombre_comercial')} AS nombre_c, {canon('r.direccion')} AS direccion_c,
                       {canon('r.municipio')} AS municipio_c,
                       CAST(r.fecha_registro AS DATE) AS fecha, CAST(r.precio AS DECIMAL(12,2)) AS precio_d,
                       ({' OR '.join(f"contains(r.{c}, '?')" for c in llave_txt)}) AS con_interrogante
                FROM (SELECT {', '.join(partes)}, s.fecha_registro, s.latitud, s.longitud, s.precio,
                             s.rid, s.entidad FROM alcance s {' '.join(uniones)}) r""")

    # Clave de fila del contrato 1.3.3: compara tras reparar y normalizar;
    # captura doble (< $1) → se queda una; $1 a $50 → se quedan todas;
    # más de $50 → el GRUPO COMPLETO a cuarentena.
    clave = "producto_c, presentacion_c, marca_n, nombre_c, direccion_c, fecha"
    alta = contrato["clave_de_fila"]["colision_precio_alta"]
    con.sql(f"""CREATE TABLE clasif AS
                SELECT *, CASE WHEN n_grupo = 1 THEN 'unica' WHEN dif < 1 THEN 'captura_doble'
                               WHEN dif <= {alta['mas_de']} THEN 'observacion_multiple'
                               ELSE 'colision_precio_alta' END AS clase
                FROM (SELECT *, count(*) OVER w AS n_grupo,
                             max(precio_d) OVER w - min(precio_d) OVER w AS dif,
                             count(DISTINCT municipio_c || '|' || entidad) OVER w AS lugares,
                             row_number() OVER (PARTITION BY {clave} ORDER BY precio_d, rid) AS orden
                      FROM limpio WHERE NOT con_interrogante WINDOW w AS (PARTITION BY {clave}))""")
    grupo_completo = alta["a_cuarentena"] == "grupo_completo"
    con.sql(f"""CREATE TABLE plana AS SELECT * FROM clasif
                WHERE clase IN ('unica', 'observacion_multiple')
                   OR (clase = 'captura_doble' AND orden = 1)
                   {'' if grupo_completo else "OR (clase = 'colision_precio_alta' AND orden = 1)"}""")

    ocultas = ", ".join("'" + esc(v.lower()) + "'" for v in
                        contrato["presentacion"]["ocultar_por_defecto_en_canasta_basica"]["valores"])
    con.sql(f"""CREATE TABLE dim_articulo AS
                SELECT row_number() OVER (ORDER BY producto_c, presentacion_c) AS articulo_key,
                       producto_c, presentacion_c, mode(producto) AS producto, mode(presentacion) AS presentacion,
                       mode(categoria_c) AS categoria, mode(catalogo_n) AS catalogo_principal,
                       count(DISTINCT categoria_c) AS n_categorias, count(DISTINCT catalogo_n) AS n_catalogos,
                       mode(categoria_c) IN ({ocultas}) AS oculto_por_omision
                FROM plana GROUP BY producto_c, presentacion_c""")
    con.sql("ALTER TABLE dim_articulo ADD COLUMN articulo_canonico_key BIGINT")
    con.sql("UPDATE dim_articulo SET articulo_canonico_key = articulo_key")  # T053 lo reescribe
    con.sql("""CREATE TABLE dim_establecimiento AS
               SELECT row_number() OVER (ORDER BY entidad, municipio_c, nombre_c, direccion_c) AS establecimiento_key,
                      nombre_c, direccion_c, municipio_c, entidad,
                      mode(nombre_comercial) AS nombre_comercial, mode(direccion) AS direccion,
                      mode(municipio) AS municipio, mode(giro) AS giro,
                      avg(latitud) AS latitud, avg(longitud) AS longitud, count(DISTINCT cadena_c) AS n_cadenas
               FROM plana GROUP BY nombre_c, direccion_c, municipio_c, entidad""")
    con.sql("""CREATE TABLE dim_cadena AS
               SELECT row_number() OVER (ORDER BY cadena_c) AS cadena_key, cadena_c,
                      mode(cadena_comercial) AS cadena_comercial
               FROM plana GROUP BY cadena_c""")
    con.sql(f"""CREATE TABLE dim_fecha AS
                SELECT CAST(strftime(d, '%Y%m%d') AS INTEGER) AS fecha_key, CAST(d AS DATE) AS fecha,
                       year(d) AS anio, month(d) AS mes,
                       strftime(d, '%Y-%m') || '-Q' || CASE WHEN day(d) <= 15 THEN '1' ELSE '2' END AS quincena,
                       isodow(d) AS dia_semana, isodow(d) >= 6 AS es_fin_de_semana
                FROM (SELECT unnest(generate_series(TIMESTAMP '{desde}', TIMESTAMP '{hasta}', INTERVAL 1 DAY)) AS d)""")
    con.sql("""CREATE TABLE hechos_precio AS
               SELECT p.rid AS observacion_id, CAST(strftime(p.fecha, '%Y%m%d') AS INTEGER) AS fecha_key,
                      a.articulo_key, e.establecimiento_key, c.cadena_key,
                      p.marca_n AS marca, p.marca_n = 'S/M' AS es_generico,
                      p.catalogo_n AS catalogo, p.precio_d AS precio
               FROM plana p
               JOIN dim_articulo a USING (producto_c, presentacion_c)
               JOIN dim_establecimiento e USING (nombre_c, direccion_c, municipio_c, entidad)
               JOIN dim_cadena c USING (cadena_c)""")

    # Agregados
    con.sql("""CREATE TABLE agg_articulo_entidad_quincena AS
               SELECT a.articulo_canonico_key, e.entidad, f.quincena, count(*) AS n,
                      min(h.precio) AS minimo, quantile_cont(h.precio, 0.25) AS p25,
                      median(h.precio) AS mediana, quantile_cont(h.precio, 0.75) AS p75, max(h.precio) AS maximo
               FROM hechos_precio h JOIN dim_articulo a USING (articulo_key)
               JOIN dim_establecimiento e USING (establecimiento_key) JOIN dim_fecha f USING (fecha_key)
               GROUP BY ALL""")
    con.sql("""CREATE TABLE agg_articulo_cadena_entidad_quincena AS
               SELECT a.articulo_canonico_key, h.cadena_key, e.entidad, f.quincena, count(*) AS n,
                      count(DISTINCT h.establecimiento_key) AS n_tiendas, median(h.precio) AS mediana
               FROM hechos_precio h JOIN dim_articulo a USING (articulo_key)
               JOIN dim_establecimiento e USING (establecimiento_key) JOIN dim_fecha f USING (fecha_key)
               GROUP BY ALL""")
    con.sql("""CREATE TABLE rango_historico AS
               SELECT articulo_canonico_key, entidad, min(mediana) AS desde, max(mediana) AS hasta,
                      count(*) AS quincenas
               FROM agg_articulo_entidad_quincena GROUP BY ALL""")
    return texto


CONSULTAS = {
    "1": ("¿Cuánto costó el huevo blanco de 30 piezas en Guanajuato en julio de {anio}?", """
SELECT a.producto, a.presentacion, count(*) AS observaciones,
       median(h.precio) AS mediana, round(avg(h.precio), 2) AS promedio,
       min(h.precio) AS minimo, max(h.precio) AS maximo
FROM hechos_precio h
JOIN dim_articulo a USING (articulo_key)
JOIN dim_establecimiento e USING (establecimiento_key)
JOIN dim_fecha f USING (fecha_key)
WHERE a.producto_c LIKE 'huevo%'
  AND regexp_matches(a.presentacion_c, '\\b30\\b')
  AND (a.producto_c LIKE '%blanc%' OR a.presentacion_c LIKE '%blanc%')
  AND e.entidad = 'Guanajuato' AND f.anio = {anio} AND f.mes = 7
GROUP BY ALL ORDER BY observaciones DESC"""),
    "2": ("¿Qué cadena tuvo la canasta más barata en junio de {anio}? (índice relativo, sin alcohol ni tabaco)", """
WITH obs AS (
  SELECT h.cadena_key, a.articulo_canonico_key AS art, h.precio
  FROM hechos_precio h JOIN dim_articulo a USING (articulo_key) JOIN dim_fecha f USING (fecha_key)
  WHERE f.anio = {anio} AND f.mes = 6 AND NOT a.oculto_por_omision),
ref AS (SELECT art, median(precio) AS m FROM obs GROUP BY art),
por_art AS (SELECT o.cadena_key, o.art, median(o.precio) / r.m AS rel
            FROM obs o JOIN ref r USING (art) GROUP BY o.cadena_key, o.art, r.m)
SELECT c.cadena_comercial, count(*) AS articulos, round(exp(avg(ln(rel))), 3) AS indice
FROM por_art JOIN dim_cadena c USING (cadena_key)
GROUP BY ALL HAVING count(*) >= {minimo} ORDER BY indice LIMIT 5"""),
    "3": ("¿Cuántos artículos distintos se observaron en Michoacán la última quincena?", """
SELECT f.quincena, count(DISTINCT a.articulo_canonico_key) AS articulos
FROM hechos_precio h
JOIN dim_articulo a USING (articulo_key)
JOIN dim_establecimiento e USING (establecimiento_key)
JOIN dim_fecha f USING (fecha_key)
WHERE e.entidad = 'Michoacán'
  AND f.quincena = (SELECT max(f2.quincena) FROM hechos_precio h2 JOIN dim_fecha f2 USING (fecha_key))
GROUP BY ALL"""),
}


def tabla_md(rel):
    cols = rel.columns
    filas = rel.fetchall()
    if not filas:
        return "_sin filas_"
    lineas = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for f in filas:
        lineas.append("| " + " | ".join(f"{v:,}" if isinstance(v, int) else str(v) for v in f) + " |")
    return "\n".join(lineas)


def main():
    ap = argparse.ArgumentParser(description="T031 · arma y mide el modelo dimensional")
    ap.add_argument("--origen", help="glob de parquet; por omisión la capa cruda en MinIO")
    ap.add_argument("--diccionario", default=str(DICCIONARIO))
    ap.add_argument("--anio", type=int, default=2026)
    ap.add_argument("--min-articulos", type=int, default=30)
    ap.add_argument("--escribir", help="documento donde dejar las cifras, entre las marcas")
    a = ap.parse_args()
    import yaml
    contrato = yaml.safe_load(CONTRATO.read_text(encoding="utf-8"))
    origen = a.origen
    if not origen:
        bucket = os.environ.get("S3_BUCKET") or morir("sin --origen hace falta S3_BUCKET (carga tu .env)")
        origen = f"s3://{bucket}/qqp/**/*.parquet"
    con = conectar(origen)
    t0 = time.time()
    texto = construir(con, contrato, origen, a.diccionario)
    segundos = round(time.time() - t0, 1)

    def q(sql):
        return con.sql(sql).fetchone()[0]

    alcance = q("SELECT count(*) FROM alcance")
    esperado = contrato["medicion"]["filas"]
    requeridas = [c for c, d in contrato["columnas"].items() if d.get("valor_requerido")]
    vacios = {c: q(f"SELECT count(*) FROM alcance WHERE {c} IS NULL"
                   + (f" OR trim({c}) = ''" if c in texto else "")) for c in requeridas}
    interrog = q("SELECT count(*) FROM limpio WHERE con_interrogante")
    sobr = {k: q(f"SELECT count(*) FROM clasif WHERE clase = '{k}' AND orden > 1") for k in COLISIONES_CONTRATO}
    alta_filas = q("SELECT count(*) FROM clasif WHERE clase = 'colision_precio_alta'")
    hechos = q("SELECT count(*) FROM hechos_precio")
    cuarentena = interrog + alta_filas
    ancho = q("SELECT avg(strlen(marca)) + avg(strlen(catalogo)) FROM hechos_precio") or 0
    bpf = round(24 + 4 + 8 + 4 + 4 + 4 + 2 + 1 + (ancho + 2) + 10)
    cifras = [
        ("Filas del alcance", f"{alcance:,}", "alcance · el contrato dice " + f"{esperado:,}"
         + (" ✓" if alcance == esperado else " ✗")),
        ("Vacíos en las columnas con valor requerido", f"{sum(vacios.values()):,}",
         f"alcance · {len(requeridas)} columnas" + ("" if not sum(vacios.values()) else
                                                    " · " + ", ".join(f"{c}={n:,}" for c, n in vacios.items() if n))),
        ("`?` que el diccionario no repara → cuarentena", f"{interrog:,}",
         "alcance · COTA SUPERIOR: el contrato resuelve por frecuencia los ambiguos y aquí todavía no"),
        ("Capturas dobles (sobrantes que se quitan)", f"{sobr['captura_doble']:,}",
         f"alcance · el contrato midió {COLISIONES_CONTRATO['captura_doble']:,} sin normalizar"),
        ("Observaciones múltiples (sobrantes que se quedan)", f"{sobr['observacion_multiple']:,}",
         f"alcance · el contrato midió {COLISIONES_CONTRATO['observacion_multiple']:,} sin normalizar"),
        ("Colisión de precio alta · filas a cuarentena (grupo completo)", f"{alta_filas:,}",
         f"alcance · eran {COLISIONES_CONTRATO['colision_precio_alta']:,} sobrantes en el contrato"),
        ("Cuarentena total", f"{cuarentena:,} ({100 * cuarentena / alcance:.3f}%)", "porcentaje del alcance · cota superior"),
        ("Filas en hechos_precio", f"{hechos:,}", "alcance − capturas dobles − cuarentena · cota inferior"),
        ("Artículos (dim_articulo)", f"{q('SELECT count(*) FROM dim_articulo'):,}", "alcance"),
        ("Artículos con más de un catálogo", f"{q('SELECT count(*) FROM dim_articulo WHERE n_catalogos > 1'):,}",
         "alcance · por eso `catalogo` va en los hechos"),
        ("Artículos con más de una categoría", f"{q('SELECT count(*) FROM dim_articulo WHERE n_categorias > 1'):,}",
         "alcance"),
        ("Establecimientos (dim_establecimiento)", f"{q('SELECT count(*) FROM dim_establecimiento'):,}", "alcance"),
        ("Establecimientos con más de una cadena", f"{q('SELECT count(*) FROM dim_establecimiento WHERE n_cadenas > 1'):,}",
         "alcance"),
        ("Grupos de clave de fila que mezclan municipios o entidades",
         f"{q('SELECT count(DISTINCT (producto_c, presentacion_c, marca_n, nombre_c, direccion_c, fecha)) FROM clasif WHERE lugares > 1'):,}",
         "alcance · si es más de 0, la clave de fila necesita municipio y entidad"),
        ("Cadenas (dim_cadena)", f"{q('SELECT count(*) FROM dim_cadena'):,}", "alcance"),
        ("Días (dim_fecha)", f"{q('SELECT count(*) FROM dim_fecha'):,}", "ventana del contrato"),
        ("Particiones entidad × quincena con datos",
         f"{q('SELECT count(*) FROM (SELECT DISTINCT e.entidad, f.quincena FROM hechos_precio JOIN dim_establecimiento e USING (establecimiento_key) JOIN dim_fecha f USING (fecha_key))'):,}",
         "alcance · 7 × 38 = 266 si no falta ninguna"),
        ("agg_articulo_entidad_quincena · filas", f"{q('SELECT count(*) FROM agg_articulo_entidad_quincena'):,}", "alcance"),
        ("agg_articulo_cadena_entidad_quincena · filas",
         f"{q('SELECT count(*) FROM agg_articulo_cadena_entidad_quincena'):,}", "alcance"),
        ("Bytes por fila de hechos en Postgres (estimado)", f"{bpf}", "misma fórmula que medir-el-peso.py, sin índices"),
        ("Peso de hechos_precio (estimado, sin índices)", f"{hechos * bpf / 1e6:,.0f} MB", "alcance · para el presupuesto de B"),
        ("Armado completo del modelo", f"{segundos} s", "esta corrida, en esta máquina"),
    ]
    print(f"origen: {origen} · contrato {contrato['version']} · población: ALCANCE\n")
    for nombre, valor, pob in cifras:
        print(f"  {nombre:<62}{valor:>22}   {pob}")
    bloques = []
    for k, (titulo, sql) in CONSULTAS.items():
        rel = con.sql(sql.format(anio=a.anio, minimo=a.min_articulos))
        res = tabla_md(rel)
        if k == "1" and res == "_sin filas_":
            res = ("_Sin filas: no hay huevo blanco de 30 piezas en esa entidad y mes._ Lo que sí se observó "
                   "en Guanajuato en julio:\n\n" + tabla_md(con.sql(f"""
                SELECT a.producto, a.presentacion, count(*) AS observaciones, median(h.precio) AS mediana
                FROM hechos_precio h JOIN dim_articulo a USING (articulo_key)
                JOIN dim_establecimiento e USING (establecimiento_key) JOIN dim_fecha f USING (fecha_key)
                WHERE a.producto_c LIKE 'huevo%' AND e.entidad = 'Guanajuato'
                  AND f.anio = {a.anio} AND f.mes = 7
                GROUP BY ALL ORDER BY observaciones DESC LIMIT 15""")))
        print(f"\n{k} · {titulo.format(anio=a.anio)}\n{res}")
        bloques.append(f"**{k} · {titulo.format(anio=a.anio)}**\n\n{res}")

    print("\n── Para revisar a mano (no va al documento)")
    print("Establecimientos con más de una cadena:")
    print(con.sql("""SELECT e.nombre_comercial, e.municipio, e.entidad,
                            string_agg(DISTINCT c.cadena_comercial, ' | ') AS cadenas
                     FROM hechos_precio h JOIN dim_establecimiento e USING (establecimiento_key)
                     JOIN dim_cadena c USING (cadena_key)
                     GROUP BY ALL HAVING count(DISTINCT h.cadena_key) > 1 ORDER BY 3, 2, 1"""))
    print("Cadenas que podrían ser la misma (iguales sin espacios):")
    print(con.sql("""SELECT replace(cadena_c, ' ', '') AS clave, string_agg(cadena_comercial, ' | ') AS cadenas
                     FROM dim_cadena GROUP BY 1 HAVING count(*) > 1"""))
    print("Artículos con más de una categoría:")
    print(con.sql("""SELECT a.producto, a.presentacion, string_agg(DISTINCT p.categoria_c, ' | ') AS categorias
                     FROM plana p JOIN dim_articulo a USING (producto_c, presentacion_c)
                     WHERE a.n_categorias > 1 GROUP BY ALL"""))

    if a.escribir:
        doc = Path(a.escribir)
        t = doc.read_text(encoding="utf-8")
        if t.count(INICIO) != 1 or t.count(FIN) != 1:
            morir(f"{doc} no trae una sola vez las marcas {INICIO} y {FIN}")
        hoy = dt.datetime.now(dt.timezone.utc).date().isoformat()
        bloque = (f"{INICIO}\n> Generado el {hoy} por `docs/datos/probar-modelo-dimensional.py` con el contrato "
                  f"{contrato['version']}. **Población: alcance del contrato.** No se escribe a mano: si algo cambia, "
                  f"se vuelve a correr.\n\n| Cifra | Valor | Población · nota |\n|---|---:|---|\n"
                  + "\n".join(f"| {n} | {v} | {p} |" for n, v, p in cifras)
                  + "\n\n### Resultado de las tres consultas\n\n" + "\n\n".join(bloques) + f"\n{FIN}")
        ini, fin = t.index(INICIO), t.index(FIN) + len(FIN)
        doc.write_text(t[:ini] + bloque + t[fin:], encoding="utf-8")
        print(f"\n✓ cifras escritas en {doc}")


if __name__ == "__main__":
    main()
