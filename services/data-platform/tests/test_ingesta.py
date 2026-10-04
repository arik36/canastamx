"""
Pruebas de las cuatro protecciones de la ingesta a la capa cruda.

Corren el guion de verdad, en modo --simular, sobre archivos chicos hechos a
mano: no necesitan MinIO ni los datos del corpus.

    python -m pytest services/data-platform/tests -q
"""
import json
import subprocess
import sys
from pathlib import Path

import yaml

INGESTION = Path(__file__).resolve().parents[1] / "ingestion"
RAIZ = Path(__file__).resolve().parents[3]
CONTRATO = yaml.safe_load((RAIZ / "contracts" / "qqp-v1.yaml").read_text(encoding="utf-8"))
COLUMNAS = list(CONTRATO["columnas"])


def fila(estado="Guanajuato", catalogo="Basicos", fecha="2025/01/10", producto="Frijol"):
    v = {"producto": producto, "presentacion": "Bolsa 1 Kg", "marca": "S/m", "categoria": "legumbres",
             "cadena_comercial": "Soriana", "giro": "Supermercado", "nombre_comercial": "Soriana Centro",
             "direccion": "Av. Juarez 100", "estado": estado, "municipio": "Leon", "catalogo": catalogo,
             "fecha_registro": fecha, "latitud": "21.1", "longitud": "-101.6", "precio": "32.50"}
    return ",".join(v[c] for c in COLUMNAS)


def archivo(tmp_path, nombre, filas):
    ruta = tmp_path / nombre
    ruta.write_text(",".join(COLUMNAS) + "\n" + "\n".join(filas) + "\n", encoding="utf-8")
    return ruta


def ingerir(ruta, *extra):
    return subprocess.run([sys.executable, str(INGESTION / "ingesta.py"), str(ruta), "--simular", *extra],
                          capture_output=True, text=True, check=False)


def test_un_lote_limpio_pasa(tmp_path):
    r = ingerir(archivo(tmp_path, "01-2025_01.csv", [fila(), fila(estado="Michoacán")]))
    assert r.returncode == 0, r.stderr
    assert "2025-01-Q1, la quincena del lote" in r.stdout


def test_un_interrogante_en_estado_detiene_el_lote(tmp_path):
    r = ingerir(archivo(tmp_path, "01-2025_01.csv", [fila(), fila(estado="Michoac?n")]))
    assert r.returncode == 1
    assert "traen `?` en estado o catalogo" in r.stderr


def test_un_interrogante_en_catalogo_detiene_el_lote(tmp_path):
    r = ingerir(archivo(tmp_path, "01-2025_01.csv", [fila(), fila(catalogo="B?sicos")]))
    assert r.returncode == 1


def test_un_control_c1_detiene_el_lote(tmp_path):
    r = ingerir(archivo(tmp_path, "01-2025_01.csv", [fila(), fila(producto="Caf\x93")]))
    assert r.returncode == 1
    assert "detectar_controles_C1" in r.stderr


def test_una_fila_de_otra_quincena_detiene_el_lote(tmp_path):
    r = ingerir(archivo(tmp_path, "01-2025_01.csv", [fila(), fila(fecha="2025/01/20")]))
    assert r.returncode == 1
    assert "caen en otra quincena (2025-01-Q2)" in r.stderr


def test_un_nombre_sin_quincena_la_pide(tmp_path):
    ruta = archivo(tmp_path, "prueba.csv", [fila()])
    assert ingerir(ruta).returncode == 1
    assert ingerir(ruta, "--quincena", "2025-01-Q1").returncode == 0


def registro(carpeta, lote, corrida, dentro, en_bucket):
    d = {"lote": lote, "archivo": f"/datos/{lote}.parquet", "sha256_entrada": "0" * 64,
         "recorte": {"filas_del_archivo": dentro * 10, "dentro_del_alcance": dentro,
                     "fuera_por_estado": 0, "fuera_por_ventana": 0, "fuera_por_catalogo": 0},
         "lectura_declarada": {}, "columnas_extra_ignoradas": [],
         "cinco_cifras": {"objetos": 7, "bytes": 1}, "particiones": [{"entidad": "Guanajuato", "quincena": "x"}],
         "acumulado_en_el_bucket": {"filas": en_bucket}, "corrida": corrida}
    (carpeta / f"{corrida[:10]}-{lote}.json").write_text(json.dumps(d), encoding="utf-8")


def consolidar(tmp_path):
    return subprocess.run([sys.executable, str(INGESTION / "consolidar-corridas.py"),
                           "--corridas", str(tmp_path / "corridas"), "--salida", str(tmp_path / "salida.md")],
                          capture_output=True, text=True, check=False)


def test_el_consolidado_cuenta_una_vez_cada_lote_y_cuadra_con_el_bucket(tmp_path):
    (tmp_path / "corridas").mkdir()
    registro(tmp_path / "corridas", "01-2025_01", "2026-09-27T10:00:00+00:00", 10, 10)
    registro(tmp_path / "corridas", "01-2025_01", "2026-09-28T10:00:00+00:00", 10, 10)   # la misma, otro día
    registro(tmp_path / "corridas", "01-2025_02", "2026-09-28T11:00:00+00:00", 5, 15)
    r = consolidar(tmp_path)
    assert r.returncode == 0, r.stderr
    assert "bucket 15 · leídas 15 · CUADRA" in r.stdout


def test_el_consolidado_avisa_si_el_bucket_perdio_filas(tmp_path):
    (tmp_path / "corridas").mkdir()
    registro(tmp_path / "corridas", "01-2025_01", "2026-09-28T10:00:00+00:00", 10, 10)
    registro(tmp_path / "corridas", "01-2025_02", "2026-09-28T11:00:00+00:00", 5, 12)    # 3 filas perdidas
    r = consolidar(tmp_path)
    assert r.returncode == 1
    assert "NO CUADRA" in r.stdout
