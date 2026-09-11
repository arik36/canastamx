"""
Perfilado nivel 1 · QQP (T003) · versión 2

Qué cambió respecto de la versión 1 y por qué
---------------------------------------------
La v1 leía con `pd.read_csv(...)` a secas. Por omisión, pandas convierte a nulo
los textos `NA`, `N/A`, `NULL`, `null`, `NaN`, `nan`, `None`, `-` y unos cuantos
más. Eso mezcla dos cosas que el contrato de datos tiene que distinguir:

    celda vacía        →  el capturista no escribió nada
    celda con «NULL»   →  el capturista escribió la palabra NULL

Las dos salían como «nulo» y las dos se perdían de la lista de valores
distintos, porque `distintos[col]` usaba `.dropna()`. C2 midió su diccionario
con `keep_default_na=False, na_filter=False` justamente para no mezclarlas, así
que los dos documentos estaban midiendo cosas distintas y decían «0» por
motivos distintos.

Esta versión lee TODO como texto crudo (`dtype=str`, sin conversión automática)
y cuenta por separado:

    ausente          la columna no existe en ese archivo
    vacía            existe y vale ""
    sólo espacios    existe y vale "   "
    marcador textual existe y vale "NA", "NULL", "S/m", …

El caso «ausente» arregla de paso el sesgo de `folio`: en la v1, un archivo sin
la columna aportaba 0 nulos en vez de aportar todas sus filas, y por eso el
porcentaje de `folio` salía 0% cuando en realidad falta en 36 de 38 archivos.

Y como ya nada se convierte solo, los tipos se COMPRUEBAN en vez de inferirse:
se intenta convertir `precio`, `latitud` y `longitud` a número y `fecha_registro`
a fecha con el formato que le toca a cada archivo, y se cuenta lo que no pasa.
Eso es un hallazgo del contrato; el `dtype` que adivinaba pandas no lo era.

Uso
---
    python docs/datos/perfilado/perfilado_nivel1.py
    CANASTAMX_DATOS=/otra/ruta python docs/datos/perfilado/perfilado_nivel1.py

NO genera los parquet. De eso se encarga perfilado_nivel2.py.
"""
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

RAIZ = Path(os.environ.get("CANASTAMX_DATOS", Path.home() / "canastamx-datos"))
CARPETAS = [RAIZ / "crudo" / "QQP_2025", RAIZ / "crudo" / "QQP_2026"]
SALIDA = Path("docs/datos/perfilado")

# Los únicos dos archivos que rompen el patrón general (ver docs/datos/fuente-qqp.md).
# Comprobado el 10/09/2026 con mojibake.py: NO traen bytes 0x80–0x9F, así que
# latin-1 es la lectura correcta y no una suposición.
ATIPICOS_MAYO_2026 = {"05-2026_Q1.csv", "05-2026_Q2.csv"}

# Los textos que pandas convertiría a nulo por su cuenta, más los que usa esta
# fuente. Se cuentan, no se convierten: que exista no significa que sea nulo.
MARCADORES = ["NA", "N/A", "NULL", "null", "NaN", "nan", "None", "none",
              "N/D", "ND", "-", "--", "S/m", "S/M", "s/m", "#N/A", "SIN DATO"]

NUMERICAS = ["precio", "latitud", "longitud"]

# Controles C1 (U+0080\u2013U+009F): la firma de una codificaci\u00f3n equivocada.
# OJO con la sintaxis: pandas 3 respalda las cadenas con PyArrow, y
# `str.contains(regex=True)` termina en RE2, que NO entiende `\uXXXX` \u2014
# revienta con \u00abinvalid escape sequence: \u\u00bb. RE2 quiere `\x{0080}`.
# Se deja adem\u00e1s un respaldo en Python puro por si el respaldo de cadenas
# cambia y la expresi\u00f3n deja de ser v\u00e1lida.
CONTROL_C1 = r"[\x{0080}-\x{009F}]"
CONTROL_C1_CHARS = "".join(chr(c) for c in range(0x80, 0xA0))


def tiene_control(idx):
    """\u00bfCada valor del \u00edndice trae alg\u00fan car\u00e1cter de control C1?"""
    try:
        return idx.str.contains(CONTROL_C1, regex=True, na=False).to_numpy()
    except Exception:
        return [any(ch in CONTROL_C1_CHARS for ch in v) for v in idx]

# Lo que declara el diccionario oficial (C2 · T013). Sirve para poner el tipo
# declarado al lado del comprobado y que la discrepancia salte sola.
DECLARADO = {
    "producto": "Carácter (65)", "presentacion": "Carácter (180)",
    "marca": "Carácter (65)", "categoria": "Carácter (65)",
    "catalogo": "Carácter (65)", "precio": "Número (18,2)",
    "fecha_registro": "Datetime (8)", "cadena_comercial": "Carácter (65)",
    "giro": "Carácter (65)", "nombre_comercial": "Carácter (120)",
    "direccion": "Carácter (255)", "estado": "Carácter (120)",
    "municipio": "Carácter (120)", "latitud": "Número (18,6)",
    "longitud": "Número (18,6)",
    "folio": "(no está en el diccionario)",
    "cv_producto": "(no está en el diccionario)",
    "cv_marca": "(no está en el diccionario)",
}

TROZO = 200_000   # filas por lectura. Con dtype=str el texto ocupa más que los
                  # float de la v1, así que se lee por partes y no de golpe.

# ── acumuladores ────────────────────────────────────────────────────────────
filas_totales = 0
por_archivo = []                       # una fila por CSV
presentes = Counter()                  # col -> filas donde la columna EXISTE
vacios = Counter()
espacios = Counter()
interrogacion = Counter()
control = Counter()
largo_max = Counter()
marcadores = defaultdict(Counter)      # col -> {marcador: filas}
distintos = defaultdict(set)
ejemplo = {}
no_numerico = Counter()                # sólo NUMERICAS
fechas_malas = 0
fecha_min = fecha_max = None


def contar_columna(col, s):
    """Todo lo que se puede saber de una columna de texto crudo, de una pasada.

    Se usa value_counts() una sola vez y de ahí sale todo: los conteos son por
    FILA porque value_counts ya trae cuántas filas tiene cada valor.
    """
    global largo_max
    vc = s.value_counts()
    idx = vc.index

    presentes[col] += int(vc.sum())
    distintos[col].update(idx)
    vacios[col] += int(vc.get("", 0))

    solo_esp = idx.to_series().str.strip().eq("") & idx.to_series().ne("")
    espacios[col] += int(vc[solo_esp.values].sum())

    tiene_q = idx.str.contains("?", regex=False)
    interrogacion[col] += int(vc[tiene_q].sum())

    control[col] += int(vc[tiene_control(idx)].sum())

    for m in MARCADORES:
        n = int(vc.get(m, 0))
        if n:
            marcadores[col][m] += n

    if len(idx):
        largo_max[col] = max(largo_max[col], int(idx.str.len().max()))
    if col not in ejemplo and len(idx):
        # Se prefiere un valor de contenido: un ejemplo que sea «S/m» o «NULL»
        # no le dice nada a nadie. Si la columna sólo tiene marcadores, se
        # muestra el marcador — que también es información.
        reales = [v for v in idx if v.strip() and v not in MARCADORES]
        ejemplo[col] = reales[0] if reales else idx[0]


for carpeta in CARPETAS:
    if not carpeta.exists():
        print(f"(no existe {carpeta}, la salto)")
        continue
    for path in sorted(carpeta.glob("*.csv")):
        if ":Zone.Identifier" in path.name:
            continue
        atipico = path.name in ATIPICOS_MAYO_2026
        encoding = "latin-1" if atipico else "utf-8-sig"
        formato = "%d/%m/%Y" if atipico else "%Y/%m/%d"

        filas_archivo = 0
        columnas = None
        for trozo in pd.read_csv(path, encoding=encoding, dtype=str,
                                 keep_default_na=False, na_filter=False,
                                 chunksize=TROZO):
            if columnas is None:
                columnas = list(trozo.columns)
            filas_archivo += len(trozo)

            for col in trozo.columns:
                contar_columna(col, trozo[col])

            for col in NUMERICAS:
                if col in trozo.columns:
                    s = trozo[col]
                    n = pd.to_numeric(s, errors="coerce")
                    # no numérico = no convierte Y no está vacío. Un vacío ya
                    # se contó como vacío; contarlo otra vez sería doble.
                    no_numerico[col] += int((n.isna() & s.str.strip().ne("")).sum())

            f = pd.to_datetime(trozo["fecha_registro"], format=formato, errors="coerce")
            fechas_malas += int(f.isna().sum())
            if f.notna().any():
                lo, hi = f.min(), f.max()
                fecha_min = lo if fecha_min is None or lo < fecha_min else fecha_min
                fecha_max = hi if fecha_max is None or hi > fecha_max else fecha_max

        filas_totales += filas_archivo
        por_archivo.append({"archivo": path.name, "carpeta": path.parent.name,
                            "filas": filas_archivo, "codificacion": encoding,
                            "formato_fecha": formato, "columnas": len(columnas)})
        print(f"{path.parent.name}/{path.name}: {filas_archivo:,} filas · "
              f"{len(columnas)} columnas · {encoding}"
              f"{' · dayfirst' if atipico else ''}")

if not filas_totales:
    raise SystemExit(f"No encontré ningún CSV bajo {RAIZ/'crudo'}")

# ── 1 · estructura ──────────────────────────────────────────────────────────
arch = pd.DataFrame(por_archivo)
print(f"\n{'='*78}\n1 · Estructura\n{'='*78}")
print(f"Archivos leídos : {len(arch)}")
print(f"Filas totales   : {filas_totales:,}")
print(f"Rango de fechas : {fecha_min.date()} a {fecha_max.date()}"
      f"   (no interpretables: {fechas_malas:,})")

print("\nJuegos de columnas — un renglón por forma distinta de archivo:")
for n, grupo in arch.groupby("columnas"):
    print(f"  {len(grupo):>2} archivo(s) con {n} columnas: {sorted(grupo.archivo)}")

print("\nCodificaciones:")
for (enc, fmt), grupo in arch.groupby(["codificacion", "formato_fecha"]):
    print(f"  {len(grupo):>2} archivo(s) · {enc} · fecha {fmt}")

# ── 2 · por columna ─────────────────────────────────────────────────────────
todas = sorted(presentes, key=lambda c: -presentes[c])
resumen = pd.DataFrame({
    "declarado":   {c: DECLARADO.get(c, "?") for c in todas},
    "ausente":     {c: filas_totales - presentes[c] for c in todas},
    "pct_ausente": {c: round((filas_totales - presentes[c]) / filas_totales * 100, 2)
                    for c in todas},
    "vacia":       {c: vacios[c] for c in todas},
    "espacios":    {c: espacios[c] for c in todas},
    "marcador":    {c: sum(marcadores[c].values()) for c in todas},
    "distintos":   {c: len(distintos[c]) for c in todas},
    "largo_max":   {c: largo_max[c] for c in todas},
    "ejemplo":     {c: str(ejemplo.get(c, ""))[:28] for c in todas},
})
print(f"\n{'='*78}\n2 · Por columna\n{'='*78}")
print("ausente = la columna NO EXISTE en ese archivo · vacia = existe y vale \"\"")
print("marcador = texto como NA, NULL o S/m, que NO se convirtió a nulo\n")
print(resumen.to_string())

# ── 3 · marcadores textuales ────────────────────────────────────────────────
print(f"\n{'='*78}\n3 · Marcadores textuales — lo que la v1 convertía a nulo en silencio\n{'='*78}")
hay = False
for col in todas:
    if marcadores[col]:
        hay = True
        detalle = " · ".join(f"{m}: {n:,}" for m, n in marcadores[col].most_common())
        tot = sum(marcadores[col].values())
        print(f"  {col:<18} {tot:>10,} filas ({tot/filas_totales:6.2%})  {detalle}")
if not hay:
    print("  (ninguno)")
else:
    print("\n  Ninguno de éstos es un nulo hasta que el contrato diga que lo es.")
    print("  Decidirlo es punto de la reunión, no del guión.")

# ── 4 · tipos comprobados ───────────────────────────────────────────────────
print(f"\n{'='*78}\n4 · Tipos comprobados (no inferidos)\n{'='*78}")
for col in NUMERICAS:
    if col in presentes:
        n = no_numerico[col]
        estado = "todo convierte a número" if not n else f"{n:,} valores NO son número"
        print(f"  {col:<12} declarado {DECLARADO[col]:<14} → {estado}")
print(f"  {'fecha_registro':<12} declarado {DECLARADO['fecha_registro']:<14} → "
      f"{'todas interpretables' if not fechas_malas else f'{fechas_malas:,} no interpretables'}")
print(f"\n  Aviso: el formato de fecha NO es el mismo en los 38 archivos.")
print(f"  Aquí cada archivo se lee con el suyo; leer todo con uno solo")
print(f"  intercambiaría día y mes en las dos quincenas de mayo de 2026.")

# ── 5 · corrupción de texto ─────────────────────────────────────────────────
print(f"\n{'='*78}\n5 · Corrupción de texto (cuadra con mojibake.py)\n{'='*78}")
tq = {c: interrogacion[c] for c in todas if interrogacion[c]}
tc = {c: control[c] for c in todas if control[c]}
if tq:
    for c, n in sorted(tq.items(), key=lambda kv: -kv[1]):
        print(f"  '?' en {c:<18} {n:>10,} filas ({n/filas_totales:.4%})")
else:
    print("  Ningún '?' en columnas de texto.")
if tc:
    print()
    for c, n in sorted(tc.items(), key=lambda kv: -kv[1]):
        print(f"  control C1 en {c:<11} {n:>10,} filas  ← codificación equivocada")
else:
    print("\n  Ningún carácter de control C1: las codificaciones elegidas son correctas.")

# ── 6 · entidades ───────────────────────────────────────────────────────────
OFICIALES = {
    "Aguascalientes", "Baja California", "Baja California Sur", "Campeche", "Coahuila",
    "Colima", "Chiapas", "Chihuahua", "Ciudad de México", "Durango", "Guanajuato",
    "Guerrero", "Hidalgo", "Jalisco", "Estado de México", "Michoacán", "Morelos",
    "Nayarit", "Nuevo León", "Oaxaca", "Puebla", "Querétaro", "Quintana Roo",
    "San Luis Potosí", "Sinaloa", "Sonora", "Tabasco", "Tamaulipas", "Tlaxcala",
    "Veracruz", "Yucatán", "Zacatecas",
}
vistos = distintos.get("estado", set())
print(f"\n{'='*78}\n6 · Cobertura territorial\n{'='*78}")
print(f"  Literales distintos en `estado` : {len(vistos)}")
print(f"  Escritos distinto o de más     : {sorted(vistos - OFICIALES)}")
faltan = sorted(OFICIALES - vistos)
print(f"  FALTAN POR COMPLETO            : {faltan}")
print(f"  Cobertura                      : {32-len(faltan)} de 32 entidades "
      f"({(32-len(faltan))/32:.1%})")
if faltan:
    print(f"\n  Eso no es un defecto del perfilado, es una limitación del producto:")
    print(f"  un usuario de {faltan[0]} no obtiene nada. Va al informe.")

# ── salida en markdown ──────────────────────────────────────────────────────
try:
    SALIDA.mkdir(parents=True, exist_ok=True)
    destino = SALIDA / "resumen-nivel1.md"
    with open(destino, "w", encoding="utf-8") as fh:
        fh.write(f"<!-- generado por perfilado_nivel1.py · {filas_totales:,} filas -->\n\n")
        fh.write("## Por columna\n\n")
        fh.write(resumen.to_markdown())
        fh.write("\n\n## Archivos\n\n")
        fh.write(arch.to_markdown(index=False))
        fh.write("\n")
    print(f"\nTabla en {destino} — cópiala a perfilado.md")
except ImportError:
    print("\n(instala 'tabulate' si quieres el .md automático: pip install tabulate)")
