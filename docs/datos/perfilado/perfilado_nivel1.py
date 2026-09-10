"""
Perfilado nivel 1 · QQP (T003)
Adaptado a los hallazgos reales de T002:
- 38 archivos repartidos en QQP_2025/ (24) y QQP_2026/ (14)
- utf-8-sig en casi todos; latin-1 en 05-2026_Q1.csv y 05-2026_Q2.csv
- fecha_registro en YYYY/MM/DD, salvo esos mismos dos archivos (DD/MM/YYYY)
- el nombre real de columna es fecha_registro, no fechaRegistro
"""

import pandas as pd
from pathlib import Path

CARPETAS = [
    Path.home() / "canastamx-datos" / "crudo" / "QQP_2025",
    Path.home() / "canastamx-datos" / "crudo" / "QQP_2026",
]

# Los únicos dos archivos que rompen el patrón general (ver docs/datos/fuente-qqp.md)
ATIPICOS_MAYO_2026 = {"05-2026_Q1.csv", "05-2026_Q2.csv"}

total_filas = 0
nulos = {}
distintos = {}
dtypes_vistos = {}
ejemplo = {}
fecha_min, fecha_max = None, None
fechas_no_parseadas = 0

for carpeta in CARPETAS:
    for path in sorted(carpeta.glob("*.csv")):
        es_atipico = path.name in ATIPICOS_MAYO_2026
        encoding = "latin-1" if es_atipico else "utf-8-sig"

        df = pd.read_csv(path, encoding=encoding, low_memory=False)
        total_filas += len(df)

        for col in df.columns:
            nulos[col] = nulos.get(col, 0) + int(df[col].isna().sum())
            distintos.setdefault(col, set()).update(df[col].dropna().unique())
            dtypes_vistos.setdefault(col, set()).add(str(df[col].dtype))
            if col not in ejemplo and df[col].notna().any():
                ejemplo[col] = df[col].dropna().iloc[0]

        # fecha_registro: formato distinto en los dos atípicos de mayo
        f = pd.to_datetime(df["fecha_registro"], errors="coerce", dayfirst=es_atipico)
        fechas_no_parseadas += int(f.isna().sum())
        if fecha_min is None or f.min() < fecha_min:
            fecha_min = f.min()
        if fecha_max is None or f.max() > fecha_max:
            fecha_max = f.max()

        print(f"{path.parent.name}/{path.name}: {len(df):,} filas ({encoding}{', dayfirst' if es_atipico else ''})")

print(f"\n=== TOTAL: {total_filas:,} filas × {len(nulos)} columnas ===")
print(f"Rango de fechas: {fecha_min.date()} a {fecha_max.date()}  (no parseadas: {fechas_no_parseadas})")
print(f"Entidades federativas presentes ({len(distintos['estado'])}): {sorted(distintos['estado'])}")

resumen = pd.DataFrame({
    "tipo_real":  {c: "/".join(sorted(s)) for c, s in dtypes_vistos.items()},
    "nulos":      nulos,
    "pct_nulos":  {c: round(n / total_filas * 100, 4) for c, n in nulos.items()},
    "distintos":  {c: len(s) for c, s in distintos.items()},
    "ejemplo":    ejemplo,
})

print("\n=== Resumen por columna (tipo_real con '/' = inconsistente entre archivos) ===")
print(resumen.to_string())

oficiales = {
    "Aguascalientes","Baja California","Baja California Sur","Campeche","Coahuila",
    "Colima","Chiapas","Chihuahua","Ciudad de México","Durango","Guanajuato","Guerrero",
    "Hidalgo","Jalisco","Estado de México","Michoacán","Morelos","Nayarit","Nuevo León",
    "Oaxaca","Puebla","Querétaro","Quintana Roo","San Luis Potosí","Sinaloa","Sonora",
    "Tabasco","Tamaulipas","Tlaxcala","Veracruz","Yucatán","Zacatecas",
}
print("En tus datos, escritos distinto o de más:", distintos["estado"] - oficiales)
print("Faltan por completo:", oficiales - distintos["estado"])

try:
    resumen.to_markdown("docs/datos/perfilado/resumen-nivel1.md")
    print("\nTabla en markdown guardada en docs/datos/perfilado/resumen-nivel1.md — cópiala a perfilado.md")
except ImportError:
    print("\n(instala 'tabulate' con pip si quieres el .md automático; si no, copia el print de arriba a mano)")
