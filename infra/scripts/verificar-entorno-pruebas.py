#!/usr/bin/env python3
"""Verifica que la TERMINAL esté apuntando al entorno de pruebas.

Lee os.environ (lo que la terminal tiene cargado), no el archivo .env.
Se detiene con código 1 si algo apunta a desarrollo o está mal definido.
Nunca imprime contraseñas, claves ni tokens: solo revisa variables que no son secretos.

Uso, desde la raíz del repositorio (con el .env de pruebas cargado):
    set -a; source infra/envs/test/.env; set +a
    python3 infra/scripts/verificar-entorno-pruebas.py

Ubicación esperada: infra/scripts/verificar-entorno-pruebas.py
"""

import os
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

RAIZ_REPO = Path(__file__).resolve().parents[2]

fallas: list[str] = []
aciertos: list[str] = []


def falla(variable: str, actual: str, esperado: str) -> None:
    fallas.append(f"  ✗ {variable}: vale {actual}; se esperaba {esperado}")


def ok(variable: str, detalle: str) -> None:
    aciertos.append(f"  ✓ {variable}: {detalle}")


def leer(variable: str) -> str | None:
    valor = os.environ.get(variable)
    return valor if valor not in (None, "") else None


def mostrar(valor: str | None) -> str:
    return "«(sin definir)»" if valor is None else f"«{valor}»"


def exigir_igual(variable: str, esperado: str, dev: str) -> None:
    valor = leer(variable)
    if valor is None:
        falla(variable, mostrar(None), f"«{esperado}»")
    elif valor != esperado:
        pista = " (es el valor de DESARROLLO)" if valor == dev else ""
        falla(variable, mostrar(valor) + pista, f"«{esperado}»")
    else:
        ok(variable, esperado)


def revisar_s3_endpoint() -> None:
    variable, esperado = "S3_ENDPOINT", "puerto 9010 (p. ej. http://localhost:9010)"
    valor = leer(variable)
    if valor is None:
        falla(variable, mostrar(None), esperado)
        return
    try:
        url = urlparse(valor)
        puerto = url.port
        destino = f"{url.scheme}://{url.hostname}:{puerto}"  # sin usuario ni clave
    except ValueError:
        falla(variable, "una URL que no se puede leer", esperado)
        return
    if puerto != 9010:
        pista = " (es el puerto de DESARROLLO)" if puerto == 9000 else ""
        falla(variable, f"«{destino}»{pista}", esperado)
    else:
        ok(variable, destino)


def revisar_fecha_referencia() -> None:
    variable = "CANASTAMX_FECHA_REFERENCIA"
    valor = leer(variable)
    if valor is None:
        falla(variable, mostrar(None), "una fecha AAAA-MM-DD (p. ej. 2026-08-10)")
        return
    try:
        date.fromisoformat(valor)
    except ValueError:
        falla(variable, mostrar(valor), "una fecha válida AAAA-MM-DD")
        return
    ok(variable, valor)


def revisar_carpeta(variable: str) -> Path | None:
    """Ruta absoluta, existente, directorio y fuera del repo."""
    esperado = "una ruta absoluta a una carpeta existente, fuera del repositorio"
    valor = leer(variable)
    if valor is None:
        falla(variable, mostrar(None), esperado)
        return None
    if "~" in valor or "$" in valor:
        falla(variable, mostrar(valor), "una ruta absoluta sin ~ ni $HOME (escríbela completa)")
        return None
    if not os.path.isabs(valor):
        falla(variable, mostrar(valor), "una ruta ABSOLUTA (empieza con /)")
        return None
    ruta = Path(valor).resolve()
    if not ruta.exists():
        falla(variable, mostrar(valor), "una carpeta que exista (créala con mkdir -p)")
        return None
    if not ruta.is_dir():
        falla(variable, mostrar(valor), "una carpeta, no un archivo")
        return None
    if ruta == RAIZ_REPO or RAIZ_REPO in ruta.parents:
        falla(variable, mostrar(valor), f"una ruta FUERA del repositorio ({RAIZ_REPO})")
        return None
    ok(variable, str(ruta))
    return ruta


def main() -> int:
    print("Verificando las variables de la terminal (no el archivo .env)...\n")

    # --- Almacenamiento de objetos (bronze) ---
    exigir_igual("S3_BUCKET", "canastamx-bronze-test", dev="canastamx-bronze")
    revisar_s3_endpoint()

    # --- PostgreSQL analítico ---
    exigir_igual("ANALYTICS_PORT", "5443", dev="5433")
    exigir_igual("ANALYTICS_DB", "test-canastamx_analytics", dev="canastamx_analytics")

    # --- Simulación y fecha ---
    exigir_igual("CANASTAMX_SIMULAR", "0", dev="1")
    revisar_fecha_referencia()

    # --- Carpetas de la plataforma de datos ---
    revisar_carpeta("CANASTAMX_LOTES")
    revisar_carpeta("CANASTAMX_CORRIDAS")
    dagster = revisar_carpeta("DAGSTER_HOME")
    if dagster is not None and dagster == (Path.home() / ".dagster").resolve():
        # Quitamos el ✓ que acaba de agregar revisar_carpeta
        aciertos.pop()
        falla("DAGSTER_HOME", f"«{dagster}»", "una carpeta distinta de ~/.dagster (esa es la de desarrollo)")

    for linea in aciertos:
        print(linea)
    if fallas:
        print("\nFALLAS:")
        for linea in fallas:
            print(linea)
        print(f"\nDETENIDO: {len(fallas)} variable(s) mal. No corras nada contra pruebas hasta corregirlas.")
        print("Carga el entorno de pruebas: set -a; source infra/envs/test/.env; set +a")
        return 1

    print("\nOK: la terminal apunta al entorno de pruebas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
