#!/usr/bin/env python3
"""Verifica que la TERMINAL esté apuntando al entorno de pruebas.

Lee os.environ (lo que la terminal tiene cargado), no el archivo .env.
Se detiene con código 1 si algo apunta a desarrollo o está mal definido.
Nunca imprime contraseñas, claves ni tokens: solo revisa variables que no son secretos.

Uso, desde la raíz del repositorio (con el .env de pruebas cargado):
    set -a; source infra/envs/test/.env; set +a
    python3 infra/envs/test/verificar-entorno-pruebas.py

Es la comprobación de aislamiento de T049: T070 y T076 la corren antes de cada
corrida. Además de las variables, le pregunta a Docker qué contenedor publica el
puerto del bucket y el de la base. Lo que revisa y lo que no está en
infra/envs/test/README.md.
"""

import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

RAIZ_REPO = Path(__file__).resolve().parents[3]   # infra/envs/test/ → la raíz
COMPOSE_DE_PRUEBAS = Path(__file__).resolve().parent / "docker-compose.yml"

fallas: list[str] = []
aciertos: list[str] = []


def falla(variable: str, actual: str, esperado: str) -> None:
    fallas.append(f"  ✗ {variable}: vale {actual}; se esperaba {esperado}")


def ok(variable: str, detalle: str) -> None:
    aciertos.append(f"  ✓ {variable}: {detalle}")


def quitar_ok(variable: str) -> None:
    """Quita el ✓ de una variable que pasó su revisión pero falla otra."""
    aciertos[:] = [a for a in aciertos if not a.startswith(f"  ✓ {variable}:")]


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
    if puerto is None:
        falla(variable, f"«{url.scheme}://{url.hostname}», sin puerto", esperado)
    elif puerto != 9010:
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


def revisar_que_no_se_encimen(carpetas: dict[str, Path | None]) -> None:
    """Las tres carpetas, cada una por su lado: ni la misma ni una dentro de otra.

    Si los lotes y el estado de Dagster comparten carpeta, el sensor vigila la
    carpeta donde Dagster escribe; si la evidencia y los lotes la comparten, la
    evidencia queda revuelta con la entrada del experimento.
    """
    validas = [(v, r) for v, r in carpetas.items() if r is not None]
    for i, (una, ruta_una) in enumerate(validas):
        for otra, ruta_otra in validas[i + 1:]:
            if ruta_una == ruta_otra:
                problema = f"es la misma carpeta que {otra}"
            elif ruta_una in ruta_otra.parents:
                problema = f"contiene a {otra}"
            elif ruta_otra in ruta_una.parents:
                problema = f"está dentro de {otra}"
            else:
                continue
            quitar_ok(una)
            quitar_ok(otra)
            falla(una, f"«{ruta_una}», que {problema} («{ruta_otra}»)",
                  "una carpeta propia para cada variable")


def proyecto_de_pruebas() -> str:
    """El `name:` del docker-compose.yml de pruebas: el proyecto de sus contenedores."""
    for linea in COMPOSE_DE_PRUEBAS.read_text(encoding="utf-8").splitlines():
        nombre = re.fullmatch(r"name:\s*(\S+)\s*", linea)
        if nombre:
            return nombre.group(1)
    return "canastamx_test"


def contenedores_por_puerto() -> dict[int, set[tuple[str, str]]] | None:
    """{puerto de la máquina: {(contenedor, proyecto de Compose)}}, o None si Docker
    no contesta. Se lee de `docker ps` porque su filtro `publish` compara el puerto
    del contenedor, no el de la máquina."""
    formato = '{{.Names}}\t{{.Label "com.docker.compose.project"}}\t{{.Ports}}'
    try:
        hecho = subprocess.run(["docker", "ps", "--format", formato], capture_output=True,
                               text=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if hecho.returncode != 0:
        return None
    puertos: dict[int, set[tuple[str, str]]] = {}
    for linea in hecho.stdout.splitlines():
        nombre, proyecto, publicados = ([*linea.split("\t"), "", ""])[:3]
        # «0.0.0.0:9010->9000/tcp» o un rango, «0.0.0.0:9000-9001->9000-9001/tcp»
        for m in re.finditer(r":(\d+)(?:-(\d+))?->", publicados):
            inicio = int(m.group(1))
            for puerto in range(inicio, int(m.group(2) or inicio) + 1):
                puertos.setdefault(puerto, set()).add((nombre, proyecto))
    return puertos


def revisar_quien_publica_los_puertos() -> None:
    """Que detrás del puerto del bucket y del de la base estén los contenedores de
    pruebas. Docker Compose toma los puertos de la terminal antes que del --env-file:
    si desarrollo se levanta desde una terminal con el .env de pruebas cargado, se
    queda con el 9010 y el 5443, y las variables de la terminal se ven bien aunque
    apunten a desarrollo. Pasó el 15 de noviembre (#187).

    Sólo revisa las variables que ya pasaron su propia revisión: si el puerto ya
    está mal, eso ya se dijo.
    """
    revisar = []
    for variable in ("S3_ENDPOINT", "ANALYTICS_PORT"):
        if not any(a.startswith(f"  ✓ {variable}:") for a in aciertos):
            continue
        valor = leer(variable) or ""
        puerto = urlparse(valor).port if variable == "S3_ENDPOINT" else int(valor)
        revisar.append((variable, puerto))
    if not revisar:
        return

    proyecto = proyecto_de_pruebas()
    puertos = contenedores_por_puerto()
    if puertos is None:
        fallas.append("  ✗ Docker: no contesta (no está instalado, no está corriendo o tu "
                      "usuario no puede usarlo); sin él no se sabe qué contenedor hay detrás "
                      "de cada puerto")
        return
    for variable, puerto in revisar:
        duenos = sorted(puertos.get(puerto, set()))
        if not duenos:
            quitar_ok(variable)
            falla(variable, f"el puerto {puerto}, que ningún contenedor publica",
                  f"un contenedor del proyecto {proyecto} en ese puerto (levántalo con "
                  "-f infra/envs/test/docker-compose.yml)")
        elif any(suyo != proyecto for _, suyo in duenos):
            quitar_ok(variable)
            ajenos = ", ".join(f"{n} (proyecto {suyo or 'sin nombre'})" for n, suyo in duenos)
            falla(variable, f"el puerto {puerto}, que publica {ajenos}",
                  f"un contenedor del proyecto {proyecto}. Bájalos y vuelve a levantarlos "
                  "desde una terminal sin ningún .env cargado")
        else:
            ok(f"puerto {puerto}", f"{', '.join(n for n, _ in duenos)} (proyecto {proyecto})")


def main() -> int:
    print("Verificando las variables de la terminal (no el archivo .env)...\n")

    # --- Almacenamiento de objetos (bronze) ---
    exigir_igual("S3_BUCKET", "canastamx-bronze-test", dev="canastamx-bronze")
    revisar_s3_endpoint()

    # --- PostgreSQL analítico ---
    exigir_igual("ANALYTICS_PORT", "5443", dev="5433")
    exigir_igual("ANALYTICS_DB", "test-canastamx_analytics", dev="canastamx_analytics")

    # --- Quién está detrás de esos puertos ---
    revisar_quien_publica_los_puertos()

    # --- Simulación y fecha ---
    exigir_igual("CANASTAMX_SIMULAR", "0", dev="1")
    revisar_fecha_referencia()

    # --- Carpetas de la plataforma de datos ---
    carpetas = {variable: revisar_carpeta(variable)
                for variable in ("CANASTAMX_LOTES", "CANASTAMX_CORRIDAS", "DAGSTER_HOME")}
    dagster = carpetas["DAGSTER_HOME"]
    if dagster is not None and dagster == (Path.home() / ".dagster").resolve():
        quitar_ok("DAGSTER_HOME")
        falla("DAGSTER_HOME", f"«{dagster}»", "una carpeta distinta de ~/.dagster (esa es la de desarrollo)")
    revisar_que_no_se_encimen(carpetas)

    for linea in aciertos:
        print(linea)
    if fallas:
        print("\nFALLAS:")
        for linea in fallas:
            print(linea)
        print(f"\nDETENIDO: {len(fallas)} variable(s) mal. No corras nada contra pruebas hasta corregirlas.")
        print("Carga el entorno de pruebas: set -a; source infra/envs/test/.env; set +a")
        print("Y vuelve a correr: python3 infra/envs/test/verificar-entorno-pruebas.py")
        return 1

    print("\nOK: la terminal apunta al entorno de pruebas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
