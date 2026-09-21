"""
Cuánto pesa la data, de verdad · para el ADR 006 · QQP

Por qué existe este guión
-------------------------
El ADR 006 elige una máquina virtual con **12 GB de memoria** y dice, con razón,
que la restricción real es la memoria y no el disco. Pero la única cifra de peso
que trae son «~1,373 MB», sin decir de qué población salen ni en qué formato
están medidos. Con eso no se puede presupuestar nada, por dos motivos:

1. **Parquet y PostgreSQL no pesan lo mismo.** Parquet es columnar y comprimido;
   PostgreSQL guarda fila por fila, con 24 bytes de encabezado por tupla y sin
   compresión salvo TOAST. El mismo recorte puede pesar 1.4 GB en Parquet y 4 GB
   en Postgres. Presupuestar la VM con el número de Parquet es subestimar.

2. **Los índices pueden pesar más que la tabla.** La `clave_de_fila` del contrato
   son seis columnas y cuatro de ellas son texto largo (`direccion` sola llega a
   255). Un índice único sobre eso no es gratis, y es justo el que la compuerta
   de duplicados necesita.

Y hay una tercera cosa que el ADR no separa: **la data no cae en un solo lugar**.

    MinIO             los Parquet crudos y la capa intermedia
    postgres-analytics  el esquema estrella — aquí cae QQP
    postgres-oltp     usuarios, canastas y alertas — crece con usuarios,
                      no con QQP, y es minúsculo en comparación

Qué contesta
------------
1. Cuántas filas y cuántos bytes **reales de Parquet** hay en cada una de las
   tres poblaciones, escribiendo el recorte a disco y midiéndolo, no estimándolo.
2. Cuánto pesaría eso **en PostgreSQL**: tabla, índices y total, con la fórmula
   escrita para que se pueda discutir.
3. Deja lista una muestra y un `.sql` para que B lo **compruebe cargándolo** en
   el contenedor, que es el único número que se puede defender.

Uso
---
    python docs/datos/perfilado/medir-el-peso.py
    python docs/datos/perfilado/medir-el-peso.py --muestra 1000000

Salidas
-------
    docs/datos/perfilado/salidas/peso-por-poblacion.csv
    docs/datos/perfilado/salidas/peso-por-columna.csv
    docs/datos/perfilado/salidas/muestra-para-pesar.csv
    docs/datos/perfilado/salidas/pesar-en-postgres.sql
"""
import csv
import os
import sys
import tempfile
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

TERRITORIAL = f"(({FILTRO_SIETE}) AND {FILTRO_ANIO})"
ALCANCE = f"{TERRITORIAL} AND {FILTRO_CAT}"

POBLACIONES = [
    ("corpus",               "TRUE",       "los 38 archivos"),
    ("recorte territorial",  TERRITORIAL,  "7 entidades x ventana"),
    ("alcance del contrato", ALCANCE,      "+ los 5 catálogos del ADR 005"),
]

TEXTO = ["producto", "presentacion", "marca", "categoria", "cadena_comercial",
         "giro", "nombre_comercial", "direccion", "estado", "municipio",
         "catalogo"]
FECHA = ["fecha_registro"]
REALES = ["latitud", "longitud"]
DECIMAL = ["precio"]
COLUMNAS = TEXTO + FECHA + REALES + DECIMAL

# La clave de fila del contrato (contracts/qqp-v1.yaml -> clave_de_fila).
CLAVE_DE_FILA = ["producto", "presentacion", "marca",
                 "nombre_comercial", "direccion", "fecha_registro"]

MB = 1024 * 1024


# ── cómo se estima el tamaño en PostgreSQL ─────────────────────────────────
#
# Por fila, en el montón (heap):
#
#   24 bytes   encabezado de tupla, ya alineado a 8
#    4 bytes   puntero del elemento dentro de la página
#   +1 byte por cada columna de texto (encabezado varlena corto, <127 bytes)
#   + el largo promedio en bytes de cada texto
#    4 bytes   date
#    8 bytes   double precision (latitud, longitud)
#   10 bytes   numeric(12,2) — encabezado de 8 más un grupo de dígitos
#
# El total se redondea al múltiplo de 8 (MAXALIGN) y se le suma 4% por
# encabezados de página y espacio libre. Es una estimación, no una medición:
# el número que se puede defender sale de la etapa 3.
#
ENCABEZADO_TUPLA = 24
PUNTERO = 4
BYTES_FECHA = 4
BYTES_REAL = 8
BYTES_DECIMAL = 10
SOBRECARGA_PAGINA = 1.04
RELLENO_INDICE = 0.70      # un btree no se llena al 100%
ENCABEZADO_INDICE = 16     # puntero + encabezado por entrada, redondeado


def alinear(n, a=8):
    return ((n + a - 1) // a) * a


def anchos_de_texto(con, filtro):
    """Largo promedio en BYTES (no en caracteres) de cada columna de texto."""
    # strlen() de DuckDB cuenta BYTES; length() cuenta caracteres. Aquí importan
    # los bytes: `Camarón` ocupa 8, no 7, y la mitad de esta fuente trae acentos.
    sel = ", ".join(
        f"avg(strlen(coalesce({c}, ''))) AS {c}" for c in TEXTO)
    fila = con.execute(
        f"SELECT {sel} FROM parquet_scan('{PARQUETS}/*.parquet') WHERE {filtro}"
    ).fetchone()
    return dict(zip(TEXTO, [float(v or 0) for v in fila]))


def bytes_por_fila(anchos):
    d = ENCABEZADO_TUPLA + PUNTERO
    for c in TEXTO:
        d += 1 + anchos[c]
    d += BYTES_FECHA * len(FECHA)
    d += BYTES_REAL * len(REALES)
    d += BYTES_DECIMAL * len(DECIMAL)
    return alinear(int(round(d)))


def bytes_del_indice(anchos, columnas, filas):
    """Un btree sobre `columnas`: la clave más el encabezado, sin llenarse."""
    clave = 0
    for c in columnas:
        if c in TEXTO:
            clave += 1 + anchos[c]
        elif c in FECHA:
            clave += BYTES_FECHA
        elif c in REALES:
            clave += BYTES_REAL
        else:
            clave += BYTES_DECIMAL
    entrada = alinear(int(round(clave)) + ENCABEZADO_INDICE)
    return int(entrada * filas / RELLENO_INDICE)


def parquet_de(con, filtro, nombre):
    """Escribe el recorte a Parquet y devuelve (filas, bytes reales en disco).

    Las TRES poblaciones se reescriben igual —mismas 15 columnas, misma
    compresión— aunque para el corpus eso signifique volver a escribir lo que ya
    está en disco. Si no, la comparación miente: los archivos originales traen
    columnas que el contrato no ingiere y vienen comprimidos de otra forma.
    """
    with tempfile.TemporaryDirectory() as tmp:
        destino = Path(tmp) / "recorte.parquet"
        con.execute(f"""
            COPY (SELECT {', '.join(COLUMNAS)}
                    FROM parquet_scan('{PARQUETS}/*.parquet')
                   WHERE {filtro})
            TO '{destino}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """)
        filas = con.execute(
            f"SELECT count(*) FROM parquet_scan('{destino}')").fetchone()[0]
        return filas, destino.stat().st_size


def escribir_muestra(con, n):
    SALIDA.mkdir(parents=True, exist_ok=True)
    destino = SALIDA / "muestra-para-pesar.csv"
    con.execute(f"""
        COPY (SELECT {', '.join(COLUMNAS)}
                FROM parquet_scan('{PARQUETS}/*.parquet')
               WHERE {ALCANCE}
               USING SAMPLE reservoir({n} ROWS) REPEATABLE (42))
        TO '{destino}' (HEADER, DELIMITER ',')
    """)
    reales = sum(1 for _ in open(destino, encoding="utf-8")) - 1
    return destino, reales


SQL = """-- pesar-en-postgres.sql · generado por medir-el-peso.py
--
-- Carga la muestra en una tabla temporal, le pone los mismos índices que va a
-- llevar el esquema estrella y reporta cuánto ocupa cada cosa. Es la única
-- medición que se puede defender: lo demás son estimaciones.
--
-- Cómo correrlo, desde la raíz del repositorio y con los contenedores arriba:
--
--   docker compose cp docs/datos/perfilado/salidas/muestra-para-pesar.csv \\
--     postgres-analytics:/tmp/muestra.csv
--   docker compose cp docs/datos/perfilado/salidas/pesar-en-postgres.sql \\
--     postgres-analytics:/tmp/pesar.sql
--   docker compose exec postgres-analytics \\
--     psql -U $POSTGRES_USER -d $POSTGRES_DB -f /tmp/pesar.sql

DROP TABLE IF EXISTS peso_muestra;

CREATE TABLE peso_muestra (
  producto          text,
  presentacion      text,
  marca             text,
  categoria         text,
  cadena_comercial  text,
  giro              text,
  nombre_comercial  text,
  direccion         text,
  estado            text,
  municipio         text,
  catalogo          text,
  fecha_registro    date,
  latitud           double precision,
  longitud          double precision,
  precio            numeric(12,2)
);

COPY peso_muestra FROM '/tmp/muestra.csv' WITH (FORMAT csv, HEADER true);

-- Sin índices todavía: cuánto pesa el puro montón.
SELECT 'solo la tabla'                             AS que,
       count(*)                                    AS filas,
       pg_size_pretty(pg_relation_size('peso_muestra'))       AS tamano,
       pg_relation_size('peso_muestra')::float / count(*)     AS bytes_por_fila
  FROM peso_muestra;

-- Los índices que el modelo sí va a necesitar.
CREATE INDEX ix_peso_clave_de_fila ON peso_muestra
  (producto, presentacion, marca, nombre_comercial, direccion, fecha_registro);
CREATE INDEX ix_peso_articulo ON peso_muestra (producto, presentacion);
CREATE INDEX ix_peso_fecha    ON peso_muestra (fecha_registro);
ANALYZE peso_muestra;

SELECT 'tabla + indices'                                       AS que,
       pg_size_pretty(pg_relation_size('peso_muestra'))         AS solo_tabla,
       pg_size_pretty(pg_indexes_size('peso_muestra'))          AS solo_indices,
       pg_size_pretty(pg_total_relation_size('peso_muestra'))   AS total;

-- Cada índice por separado: el de la clave de fila suele ser el caro.
SELECT indexrelname                                AS indice,
       pg_size_pretty(pg_relation_size(indexrelid)) AS tamano
  FROM pg_stat_user_indexes
 WHERE relname = 'peso_muestra'
 ORDER BY pg_relation_size(indexrelid) DESC;

-- Multiplica el total por  (FILAS_DEL_ALCANCE / filas_de_la_muestra)  y ése es
-- el número que va al ADR 006. Postgres crece casi lineal con las filas, así
-- que extrapolar aquí es honesto.
"""


def main():
    n_muestra = 500_000
    if "--muestra" in sys.argv:
        n_muestra = int(sys.argv[sys.argv.index("--muestra") + 1])

    if not PARQUETS.is_dir():
        raise SystemExit(
            f"No encuentro los Parquet en {PARQUETS}.\n"
            f"Exporta CANASTAMX_DATOS si viven en otro lado.")

    SALIDA.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()

    print("=" * 74)
    print("1 · Cuánto pesa, por población")
    print("=" * 74)
    print("  El Parquet se mide escribiendo el recorte a disco, no estimando.")
    print("  El de PostgreSQL SÍ es estimación — la fórmula está arriba en el")
    print("  guión y la comprobación de verdad es la etapa 3.\n")

    anchos = anchos_de_texto(con, ALCANCE)
    fila_pg = bytes_por_fila(anchos)

    filas_y_bytes = []
    print(f"  {'población':<22}{'filas':>14}{'parquet':>13}{'postgres est.':>16}")
    print("  " + "-" * 65)
    for nombre, filtro, nota in POBLACIONES:
        filas, parq = parquet_de(con, filtro, nombre)
        heap = int(filas * fila_pg * SOBRECARGA_PAGINA)
        idx = (bytes_del_indice(anchos, CLAVE_DE_FILA, filas)
               + bytes_del_indice(anchos, ["producto", "presentacion"], filas)
               + bytes_del_indice(anchos, ["fecha_registro"], filas))
        filas_y_bytes.append((nombre, nota, filas, parq, heap, idx))
        print(f"  {nombre:<22}{filas:>14,}{parq/MB:>10.1f} MB"
              f"{(heap+idx)/MB:>13.1f} MB")

    en_disco = sum(p.stat().st_size for p in PARQUETS.glob("*.parquet"))
    print(f"\n  Los archivos tal cual están en disco hoy: {en_disco/MB:,.0f} MB")
    print("  (traen columnas que el contrato no ingiere y otra compresión;")
    print("   por eso no se comparan directo con el renglón del corpus)")

    print()
    nombre, nota, filas, parq, heap, idx = filas_y_bytes[-1]
    i_fila = bytes_del_indice(anchos, CLAVE_DE_FILA, filas)
    i_art = bytes_del_indice(anchos, ["producto", "presentacion"], filas)
    i_fec = bytes_del_indice(anchos, ["fecha_registro"], filas)
    print(f"  Desglose del alcance del contrato ({filas:,} filas):")
    print(f"    {'tabla':<26}{heap/MB:>9.1f} MB")
    print(f"    {'índice de clave_de_fila':<26}{i_fila/MB:>9.1f} MB"
          f"   <- seis columnas, cuatro de texto")
    print(f"    {'índice de artículo':<26}{i_art/MB:>9.1f} MB")
    print(f"    {'índice de fecha':<26}{i_fec/MB:>9.1f} MB")
    print(f"    {'TOTAL':<26}{(heap+idx)/MB:>9.1f} MB")
    print(f"\n    {fila_pg} bytes por fila en Postgres contra "
          f"{parq/filas:.1f} en Parquet · {(heap+idx)/parq:.1f}x más pesado")
    print(f"    Los índices son el {100*idx/(heap+idx):.0f}% del total.")

    with open(SALIDA / "peso-por-poblacion.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["poblacion", "nota", "filas", "parquet_bytes",
                    "postgres_tabla_bytes", "postgres_indices_bytes"])
        w.writerows(filas_y_bytes)

    print("\n" + "=" * 74)
    print("2 · Qué columna se lleva el peso, dentro del alcance")
    print("=" * 74 + "\n")
    orden = sorted(anchos.items(), key=lambda kv: -kv[1])
    total_texto = sum(anchos.values())
    print(f"  {'columna':<20}{'bytes/fila':>12}{'% del texto':>14}")
    print("  " + "-" * 46)
    for c, v in orden:
        print(f"  {c:<20}{v:>12.1f}{100*v/total_texto:>13.1f}%")
    with open(SALIDA / "peso-por-columna.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["columna", "bytes_promedio_por_fila"])
        w.writerows(orden)

    print("\n" + "=" * 74)
    print("3 · Para comprobarlo de verdad")
    print("=" * 74 + "\n")
    destino, reales = escribir_muestra(con, n_muestra)
    (SALIDA / "pesar-en-postgres.sql").write_text(SQL, encoding="utf-8")
    print(f"  Muestra escrita: {destino}")
    print(f"  {reales:,} filas · {destino.stat().st_size/MB:.0f} MB en CSV")
    print(f"  Guión SQL:       {SALIDA / 'pesar-en-postgres.sql'}")
    print(f"\n  Pásaselos a B. El factor de extrapolación es "
          f"{filas/reales:.2f} ({filas:,} / {reales:,}).")
    print("\n  Lo que este guión estima puede irse 30% arriba o abajo. Lo que")
    print("  salga de cargarlo en el contenedor, no.")


if __name__ == "__main__":
    main()
