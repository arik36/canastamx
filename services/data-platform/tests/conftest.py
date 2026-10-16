"""Las pruebas nunca escriben en la evidencia real.

La carpeta de corridas (`ingesta.CORRIDAS`, por omisión `ingestion/corridas/`)
guarda la evidencia de las corridas reales: el registro de cada lote, su
cuarentena, lo que la compuerta decidió. El 15 de octubre de 2026 se vio que la
suite escribía ahí: correr las pruebas sobrescribió el `lote-07-2026_Q2.json` real
de A —82,898 filas revisadas— con el de una prueba de 44, y la prueba de la línea
de comandos de la compuerta borraba `compuerta-07-2026_Q2.json` al terminar. En el
CI no se nota, porque cada corrida empieza de un repositorio limpio; en la máquina
donde vive la evidencia, sí.

Dos medidas, y la segunda es la que importa:

1. **Antes de que se importe cualquier módulo**, `CANASTAMX_CORRIDAS` apunta a una
   carpeta temporal. Todo lo que escribe la suite va ahí.
2. **Una guardia** toma una foto de la carpeta real —nombres, tamaños y fechas de
   modificación— al empezar, y otra al terminar. Si cambió algo, la suite termina
   con error y dice qué. Así, si mañana alguien escribe una prueba que se salta la
   variable, no lo descubre perdiendo evidencia.
"""

import os
import tempfile
from pathlib import Path

import pytest

_POR_OMISION = Path(__file__).resolve().parents[1] / "ingestion" / "corridas"
# La carpeta real es la que esté configurada en la terminal, o la de por omisión:
# si alguien guarda su evidencia en otro lado, la guardia la protege igual.
EVIDENCIA_REAL = Path(os.environ.get("CANASTAMX_CORRIDAS") or _POR_OMISION)


def pytest_configure(config):
    temporal = tempfile.mkdtemp(prefix="canastamx-corridas-de-prueba-")
    os.environ["CANASTAMX_CORRIDAS"] = temporal
    config._canastamx_corridas = temporal


def _foto(carpeta):
    if not carpeta.exists():
        return {}
    return {p.name: (p.stat().st_size, p.stat().st_mtime_ns)
            for p in sorted(carpeta.iterdir())}


@pytest.fixture(scope="session", autouse=True)
def la_evidencia_real_no_se_toca():
    antes = _foto(EVIDENCIA_REAL)
    yield
    despues = _foto(EVIDENCIA_REAL)
    nuevos = sorted(set(despues) - set(antes))
    borrados = sorted(set(antes) - set(despues))
    cambiados = sorted(n for n in set(antes) & set(despues) if antes[n] != despues[n])
    assert not (nuevos or borrados or cambiados), (
        f"las pruebas tocaron la evidencia real en {EVIDENCIA_REAL}: "
        f"nuevos {nuevos}, borrados {borrados}, cambiados {cambiados}")
