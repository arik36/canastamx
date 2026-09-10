"""
Bitácora de verificaciones puntuales sobre la fuente QQP.
No es el pipeline de T004 (eso es perfilado_nivel2.py) — es el "por qué"
detrás de sus decisiones. Corre una vez; la conclusión se anota como texto
en docs/datos/perfilado.md, no hace falta reejecutar esto cada vez.
"""
import pyarrow.parquet as pq
import duckdb
from pathlib import Path

PARQUETS = Path.home() / "canastamx-datos" / "procesado" / "por_archivo"
FUENTE = f"read_parquet('{PARQUETS}/*.parquet', union_by_name=True)"
FUENTE_CON_ARCHIVO = f"read_parquet('{PARQUETS}/*.parquet', union_by_name=True, filename=True)"

COLUMNAS_TEXTO = ["producto", "presentacion", "marca", "categoria", "catalogo",
                  "cadena_comercial", "giro", "nombre_comercial", "direccion",
                  "estado", "municipio"]


def verificar_esquemas():
    """¿Los 38 parquets tienen las mismas columnas? ¿Cuáles no, y cuáles son?"""
    esquemas = {}
    for p in sorted(PARQUETS.glob("*.parquet")):
        cols = tuple(pq.read_schema(p).names)
        esquemas.setdefault(cols, []).append(p.name)
    for cols, archivos in esquemas.items():
        print(f"{len(archivos)} archivo(s) con {len(cols)} columnas: {archivos}")
    return esquemas


def verificar_mojibake():
    """¿Dónde aparece un '?' sospechoso de codificación rota, por columna?
    OJO: estos conteos NO son mutuamente excluyentes entre columnas — una
    misma fila corrupta suele traer '?' en varias columnas de texto a la vez.
    """
    con = duckdb.connect()
    for col in COLUMNAS_TEXTO:
        n = con.sql(f"SELECT count(*) FROM {FUENTE} WHERE {col} LIKE '%?%'").fetchone()[0]
        if n:
            r = con.sql(f"SELECT DISTINCT {col} FROM {FUENTE} WHERE {col} LIKE '%?%'").df()
            print(f"{col}: {n:,} filas con '?' ({len(r)} valores distintos)")


def alcance_mojibake():
    """¿Cuántas FILAS (no columnas) están afectadas, por archivo?
    Usa OR sobre las 11 columnas de texto — con solo 4 (versión anterior)
    se subestimaba el alcance real, como confirmó 'municipio' por sí solo.
    """
    con = duckdb.connect()
    condicion = " OR ".join(f"{c} LIKE '%?%'" for c in COLUMNAS_TEXTO)
    r = con.sql(f"""
        SELECT filename, count(*) AS filas_con_interrogacion
        FROM {FUENTE_CON_ARCHIVO}
        WHERE {condicion}
        GROUP BY filename ORDER BY filename
    """).df()
    print(r.to_string(index=False) if not r.empty else "(no aparece en ningún archivo)")
    return r


def validacion_centinela():
    """¿Los precios redondos (99999, etc.) se repiten mucho — señal de
    centinela — o aparecen una sola vez y probablemente son reales?
    Usa FUENTE directo: la vista 'qqp' de perfilado_nivel2.py vive en OTRO
    proceso y no existe aquí.
    """
    con = duckdb.connect()
    con.sql(f"""
        SELECT categoria, producto, precio, count(*) AS veces
        FROM {FUENTE}
        WHERE precio IN (999, 9999, 99999, 999999, 9999.99, 99999.99)
        GROUP BY categoria, producto, precio
        ORDER BY veces DESC
    """).show()


if __name__ == "__main__":
    print("=== ¿Mismas columnas en los 38 archivos? ===")
    esquemas = verificar_esquemas()
    minoria = min(esquemas.values(), key=len)
    print(f"\n→ folio/cv_producto/cv_marca viven exactamente en: {minoria}")

    print("\n=== ¿Dónde aparece '?' (por columna, no exclusivo entre columnas) ===")
    verificar_mojibake()

    print("\n=== ¿Cuántas filas por archivo tienen '?' en CUALQUIERA de las 11 columnas ===")
    alcance_mojibake()

    print("\n=== Validación de centinelas ===")
    validacion_centinela()
