"""Un ayudante de las pruebas: escribir un lote con la FORMA del corpus real.

Hasta el 15 de octubre de 2026 todas las pruebas de la plataforma de datos usaban
CSV con todas sus filas dentro del alcance, y por eso no vieron dos errores que
el corpus habría mostrado en la primera corrida:

  · los 38 archivos del corpus son **parquet**, y `pd.read_parquet` necesita
    pyarrow, que no está en `requirements.txt`;
  · un archivo del corpus trae las 32 entidades y todos los catálogos: sólo el
    12.45% de sus filas es del alcance, y la compuerta revisaba el archivo entero.

Este ayudante escribe el lote como es de verdad: parquet, con la fecha tipada como
DATE y el precio y las coordenadas como DOUBLE, que es lo que el SQL de
`ingesta.py` necesita del corpus (`strftime(fecha_registro, …)` no funciona sobre
texto). Se escribe con DuckDB, que ya es dependencia, para no meter pyarrow sólo
para las pruebas.
"""

from pathlib import Path


def escribir_parquet(ruta, filas, columnas):
    """`filas` son diccionarios de texto, igual que en las pruebas con CSV. La fecha
    puede venir como `AAAA/MM/DD` o `AAAA-MM-DD`."""
    import duckdb
    import pandas as pd

    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    marco = pd.DataFrame(filas, columns=columnas, dtype="string")
    con = duckdb.connect(":memory:")
    con.register("texto", marco)

    def tipo(c):
        if c == "fecha_registro":
            return (f"COALESCE(TRY_STRPTIME(\"{c}\", '%Y/%m/%d'), "
                    f"TRY_STRPTIME(\"{c}\", '%Y-%m-%d'))::DATE AS \"{c}\"")
        if c in ("precio", "latitud", "longitud"):
            return f'TRY_CAST("{c}" AS DOUBLE) AS "{c}"'
        return f'"{c}"'

    sel = ", ".join(tipo(c) for c in columnas)
    con.execute(f"COPY (SELECT {sel} FROM texto) TO '{ruta}' (FORMAT parquet)")
    return ruta
