"""Pruebas de verificar-entorno-pruebas.py, la comprobación de aislamiento de T049.

Corren con: python3 -m unittest discover -s infra/envs/test

Cada prueba corre el script como lo corre una persona: en un proceso aparte, con
las variables en el entorno. Los valores de pruebas y de desarrollo se leen de los
dos .env.example del repositorio: si alguno cambia sin que cambie la comprobación,
estas pruebas fallan.

`docker` es uno de mentira, puesto primero en el PATH: contesta a `docker ps` lo que
la prueba le deje en FALSO_DOCKER_PS. Así no hace falta Docker, y la CI no depende de
qué contenedores tenga el runner.
"""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
SCRIPT = AQUI / "verificar-entorno-pruebas.py"
LAS_DEL_BUCKET_Y_LA_BASE = ("S3_BUCKET", "S3_ENDPOINT", "ANALYTICS_PORT", "ANALYTICS_DB")
SECRETO = "no-debe-salir-en-pantalla-1234"

def salida_de_docker_ps(*contenedores):
    """Lo que imprime `docker ps --format` del script: nombre, proyecto de Compose y
    puertos, separados por tabuladores, un contenedor por línea."""
    return "".join("\t".join(c) + "\n" for c in contenedores)


# Lo que dio `docker ps` en la máquina de B el 15 de noviembre, con los dos entornos
# bien levantados.
BIEN = salida_de_docker_ps(
    ("canastamx_test_postgres_analytics", "canastamx_test", "0.0.0.0:5443->5432/tcp, [::]:5443->5432/tcp"),
    ("canastamx_test_postgres_oltp", "canastamx_test", "0.0.0.0:5442->5432/tcp, [::]:5442->5432/tcp"),
    ("canastamx_test_minio", "canastamx_test",
     "0.0.0.0:9010->9000/tcp, [::]:9010->9000/tcp, 0.0.0.0:9011->9001/tcp, [::]:9011->9001/tcp"),
    ("canastamx_test_minio_init", "canastamx_test", ""),
    ("cmx-postgres-analytics", "git", "0.0.0.0:5433->5432/tcp, [::]:5433->5432/tcp"),
    ("cmx-postgres-oltp", "git", "0.0.0.0:5432->5432/tcp, [::]:5432->5432/tcp"),
    ("cmx-minio", "git", "0.0.0.0:9000-9001->9000-9001/tcp, [::]:9000-9001->9000-9001/tcp"),
)

# Y lo que dio ese mismo día con cada entorno levantado desde la terminal del otro:
# los puertos cruzados.
CRUZADOS = salida_de_docker_ps(
    ("canastamx_test_postgres_analytics", "canastamx_test", "0.0.0.0:5433->5432/tcp"),
    ("canastamx_test_minio", "canastamx_test", "0.0.0.0:9000-9001->9000-9001/tcp"),
    ("cmx-postgres-analytics", "git", "0.0.0.0:5443->5432/tcp, [::]:5443->5432/tcp"),
    ("cmx-minio", "git", "0.0.0.0:9010->9000/tcp, [::]:9010->9000/tcp, 0.0.0.0:9011->9001/tcp"),
)

FALSO_DOCKER = f"""#!{sys.executable}
import os, sys
sys.stdout.write(os.environ.get("FALSO_DOCKER_PS", ""))
sys.exit(int(os.environ.get("FALSO_DOCKER_SALIDA", "0")))
"""


def leer_ejemplo(ruta):
    """Las variables con valor de un .env.example, sin comentarios."""
    variables = {}
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if linea and not linea.startswith("#") and "=" in linea:
            clave, valor = linea.split("=", 1)
            if valor:
                variables[clave] = valor
    return variables


PRUEBAS = leer_ejemplo(RAIZ / "infra" / "envs" / "test" / ".env.example")
DESARROLLO = leer_ejemplo(RAIZ / ".env.example")


class Comprobacion(unittest.TestCase):

    def setUp(self):
        temporal = tempfile.TemporaryDirectory()
        self.addCleanup(temporal.cleanup)
        self.casa = Path(temporal.name).resolve()
        self.carpetas = {}
        for variable, nombre in (("CANASTAMX_LOTES", "lotes"), ("CANASTAMX_CORRIDAS", "corridas"),
                                 ("DAGSTER_HOME", "dagster")):
            ruta = self.casa / "canastamx-pruebas" / nombre
            ruta.mkdir(parents=True)
            self.carpetas[variable] = str(ruta)
        self.bin = self.casa / "bin"
        self.bin.mkdir()
        docker = self.bin / "docker"
        docker.write_text(FALSO_DOCKER, encoding="utf-8")
        docker.chmod(0o755)

    def correr(self, **cambios):
        """Corre la comprobación con la terminal de pruebas y los `cambios` encima.
        Un cambio a None quita la variable."""
        entorno = {"PATH": f"{self.bin}{os.pathsep}{os.environ.get('PATH', '')}",
                   "HOME": str(self.casa), "FALSO_DOCKER_PS": BIEN,
                   "S3_SECRET_KEY": SECRETO, "ANALYTICS_PASSWORD": SECRETO,
                   **{c: PRUEBAS[c] for c in LAS_DEL_BUCKET_Y_LA_BASE},
                   "CANASTAMX_SIMULAR": PRUEBAS["CANASTAMX_SIMULAR"],
                   "CANASTAMX_FECHA_REFERENCIA": PRUEBAS["CANASTAMX_FECHA_REFERENCIA"],
                   **self.carpetas}
        for clave, valor in cambios.items():
            if valor is None:
                entorno.pop(clave, None)
            else:
                entorno[clave] = valor
        hecho = subprocess.run([sys.executable, str(SCRIPT)], env=entorno, capture_output=True,
                               text=True, encoding="utf-8", check=False)
        self.assertNotIn(SECRETO, hecho.stdout + hecho.stderr)
        return hecho

    def assertDetenida(self, hecho, *textos):
        self.assertEqual(1, hecho.returncode, hecho.stdout)
        self.assertIn("DETENIDO", hecho.stdout)
        for texto in textos:
            self.assertIn(texto, hecho.stdout)

    def test_con_la_terminal_de_pruebas_pasa(self):
        hecho = self.correr()
        self.assertEqual(0, hecho.returncode, hecho.stdout)
        self.assertIn("OK: la terminal apunta al entorno de pruebas", hecho.stdout)
        self.assertNotIn("✗", hecho.stdout)

    def test_con_la_terminal_de_desarrollo_se_detiene_y_dice_que_falla(self):
        de_desarrollo = {c: DESARROLLO[c] for c in LAS_DEL_BUCKET_Y_LA_BASE}
        hecho = self.correr(**de_desarrollo, CANASTAMX_SIMULAR=None,
                            CANASTAMX_FECHA_REFERENCIA=None, CANASTAMX_LOTES=None,
                            CANASTAMX_CORRIDAS=None, DAGSTER_HOME=None)
        self.assertDetenida(hecho, "9 variable(s) mal")
        for variable in LAS_DEL_BUCKET_Y_LA_BASE:
            with self.subTest(variable=variable):
                linea = next(lin for lin in hecho.stdout.splitlines() if f"✗ {variable}:" in lin)
                self.assertIn("DESARROLLO", linea)

    def test_basta_una_variable_de_desarrollo_para_detenerse(self):
        for variable in LAS_DEL_BUCKET_Y_LA_BASE:
            with self.subTest(variable=variable):
                hecho = self.correr(**{variable: DESARROLLO[variable]})
                self.assertDetenida(hecho, f"✗ {variable}:", "1 variable(s) mal")

    def test_una_terminal_que_simula_se_detiene(self):
        self.assertDetenida(self.correr(CANASTAMX_SIMULAR="1"), "✗ CANASTAMX_SIMULAR:")

    def test_las_carpetas_tienen_que_ser_rutas_absolutas_que_existan(self):
        casos = {"~/canastamx-pruebas/lotes": "sin ~ ni $HOME",
                 "$HOME/canastamx-pruebas/lotes": "sin ~ ni $HOME",
                 "canastamx-pruebas/lotes": "ABSOLUTA",
                 str(self.casa / "no-existe"): "que exista"}
        for valor, esperado in casos.items():
            with self.subTest(valor=valor):
                self.assertDetenida(self.correr(CANASTAMX_LOTES=valor), esperado)

    def test_una_carpeta_dentro_del_repositorio_se_detiene(self):
        dentro = RAIZ / "services" / "data-platform" / "ingestion"
        self.assertDetenida(self.correr(CANASTAMX_CORRIDAS=str(dentro)), "FUERA del repositorio")

    def test_un_enlace_fuera_del_repositorio_que_apunta_adentro_se_detiene(self):
        enlace = self.casa / "enlace"
        enlace.symlink_to(RAIZ / "services" / "data-platform" / "ingestion")
        self.assertDetenida(self.correr(CANASTAMX_CORRIDAS=str(enlace)), "FUERA del repositorio")

    def test_el_dagster_home_de_desarrollo_se_detiene(self):
        de_desarrollo = self.casa / ".dagster"
        de_desarrollo.mkdir()
        self.assertDetenida(self.correr(DAGSTER_HOME=str(de_desarrollo)), "~/.dagster")

    def test_dos_variables_en_la_misma_carpeta_se_detiene(self):
        lotes = self.carpetas["CANASTAMX_LOTES"]
        hecho = self.correr(DAGSTER_HOME=lotes)
        self.assertDetenida(hecho, "es la misma carpeta que DAGSTER_HOME")
        self.assertNotIn("✓ DAGSTER_HOME", hecho.stdout)
        self.assertNotIn("✓ CANASTAMX_LOTES", hecho.stdout)

    def test_una_carpeta_dentro_de_otra_se_detiene(self):
        adentro = Path(self.carpetas["CANASTAMX_LOTES"]) / "corridas"
        adentro.mkdir()
        hecho = self.correr(CANASTAMX_CORRIDAS=str(adentro))
        self.assertDetenida(hecho, "contiene a CANASTAMX_CORRIDAS")

    def test_un_endpoint_sin_puerto_lo_dice(self):
        hecho = self.correr(S3_ENDPOINT="http://localhost")
        self.assertDetenida(hecho, "sin puerto")
        self.assertNotIn("None", hecho.stdout)


    def test_con_los_puertos_de_pruebas_en_sus_contenedores_lo_dice(self):
        hecho = self.correr()
        self.assertIn("✓ puerto 9010: canastamx_test_minio (proyecto canastamx_test)", hecho.stdout)
        self.assertIn("✓ puerto 5443: canastamx_test_postgres_analytics", hecho.stdout)

    def test_con_los_puertos_cruzados_se_detiene_aunque_las_variables_esten_bien(self):
        hecho = self.correr(FALSO_DOCKER_PS=CRUZADOS)
        self.assertDetenida(hecho, "2 variable(s) mal", "cmx-minio (proyecto git)",
                            "cmx-postgres-analytics (proyecto git)", "sin ningún .env cargado")
        self.assertNotIn("✓ S3_ENDPOINT", hecho.stdout)
        self.assertNotIn("✓ ANALYTICS_PORT", hecho.stdout)

    def test_un_puerto_dentro_de_un_rango_tambien_se_reconoce(self):
        # Docker junta en un rango los puertos seguidos: «9010-9011->9000-9001».
        en_rango = CRUZADOS.replace("0.0.0.0:9010->9000/tcp, [::]:9010->9000/tcp, 0.0.0.0:9011->9001/tcp",
                                    "0.0.0.0:9010-9011->9000-9001/tcp")
        self.assertNotEqual(CRUZADOS, en_rango)
        self.assertDetenida(self.correr(FALSO_DOCKER_PS=en_rango), "que publica cmx-minio (proyecto git)")

    def test_con_el_entorno_de_pruebas_abajo_se_detiene(self):
        sin_pruebas = "".join(f"{lin}\n" for lin in BIEN.splitlines() if "canastamx_test" not in lin)
        hecho = self.correr(FALSO_DOCKER_PS=sin_pruebas)
        self.assertDetenida(hecho, "que ningún contenedor publica")

    def test_si_docker_no_contesta_se_detiene(self):
        self.assertDetenida(self.correr(FALSO_DOCKER_SALIDA="1"), "✗ Docker: no contesta")

    def test_con_la_terminal_de_desarrollo_no_le_pregunta_a_docker_lo_que_ya_falla(self):
        de_desarrollo = {c: DESARROLLO[c] for c in LAS_DEL_BUCKET_Y_LA_BASE}
        hecho = self.correr(**de_desarrollo, FALSO_DOCKER_SALIDA="1")
        self.assertDetenida(hecho, "4 variable(s) mal")
        self.assertNotIn("Docker", hecho.stdout.replace("DESARROLLO", ""))


if __name__ == "__main__":
    unittest.main()
