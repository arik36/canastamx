"""Pruebas de revisar-env.py. Corren con: python3 -m unittest discover -s infra/scripts"""

import base64
import importlib.util
import os
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]

_spec = importlib.util.spec_from_file_location("revisar_env", AQUI / "revisar-env.py")
revisar_env = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(revisar_env)

# Clave de prueba creada en cada corrida: el repositorio no guarda ninguna.
CLAVE = base64.b64encode(os.urandom(32)).decode("ascii")


def problemas(texto):
    return revisar_env.revisar(texto)[0]


class FormatoComun(unittest.TestCase):

    def test_un_env_en_el_formato_comun_no_tiene_problemas(self):
        texto = ("# comentario con acentos: sí\n\nOLTP_DB=canastamx_oltp\n"
                 f"OLTP_PASSWORD=\nJWT_SECRET={CLAVE}\nJWT_EXPIRATION_MINUTES=60\n")
        self.assertEqual([], problemas(texto))

    def test_cada_diferencia_entre_compose_y_spring_se_reporta(self):
        casos = {
            "OLTP_USER=\"canastamx\"": "comillas",
            "OLTP_USER='canastamx'": "comillas",
            "export OLTP_DB=canastamx_oltp": "export",
            "OLTP_DB=canastamx_oltp # la de desarrollo": "comentario",
            "OLTP_USER=canastamx\\b": "barra invertida",
            "OLTP_USER=canastamx$b": "«$»",
            "OLTP_DB=canastamx_año": "ASCII",
            "OLTP_DB=canastamx_oltp  ": "espacios",
            "OLTP_DB = canastamx_oltp": "nombre de variable",
            "esto no es una variable": "CLAVE=valor",
        }
        for linea, esperado in casos.items():
            with self.subTest(linea=linea):
                encontrados = problemas(linea + "\n")
                self.assertEqual(1, len(encontrados), encontrados)
                self.assertIn(esperado, encontrados[0])

    def test_una_clave_repetida_se_reporta(self):
        encontrados = problemas("OLTP_DB=a\nOLTP_DB=b\n")
        self.assertEqual(["línea 2: OLTP_DB ya estaba en la línea 1"], encontrados)

    def test_un_bom_se_reporta(self):
        self.assertIn("BOM", problemas("﻿# CanastaMX\nOLTP_DB=a\n")[0])


class JwtSecret(unittest.TestCase):

    def test_base64_de_32_bytes_pasa_y_cualquier_otra_cosa_no(self):
        self.assertEqual([], problemas(f"JWT_SECRET={CLAVE}\n"))
        self.assertEqual([], problemas("JWT_SECRET=\n"))      # vacía: la dará el entorno
        for valor in (base64.b64encode(os.urandom(31)).decode(),
                      base64.b64encode(os.urandom(64)).decode(),
                      os.urandom(32).hex(),                      # 64 caracteres: 48 bytes
                      "no-es-base64"):
            with self.subTest(largo=len(valor)):
                encontrados = problemas(f"JWT_SECRET={valor}\n")
                self.assertEqual(1, len(encontrados))
                self.assertIn("Base64 de 32 bytes", encontrados[0])


class NuncaMuestraValores(unittest.TestCase):

    def test_ningun_mensaje_incluye_el_valor(self):
        secreto = "valor-que-no-debe-verse"
        lineas = [f"OLTP_USER=\"{secreto}\"", f"OLTP_USER={secreto} # nota",
                  f"export OLTP_USER={secreto}", f"JWT_SECRET={secreto}",
                  f"{secreto} = x", f"{secreto}"]
        for linea in lineas:
            with self.subTest(linea=linea):
                for mensaje in problemas(linea + "\n"):
                    self.assertNotIn(secreto, mensaje)


class VariablesHeredadas(unittest.TestCase):

    def test_solo_cuentan_las_que_el_entorno_trae_con_otro_valor(self):
        _, variables = revisar_env.revisar(
            "OLTP_DB=canastamx_oltp\nOLTP_PORT=5432\nJWT_SECRET=\n")
        entorno = {"OLTP_DB": "otra_base", "OLTP_PORT": "5432", "JWT_SECRET": "x"}
        self.assertEqual(["OLTP_DB"], revisar_env.tapadas(variables, entorno))


class LosEjemplosDelRepositorio(unittest.TestCase):

    def test_los_env_example_estan_en_el_formato_comun(self):
        for ruta in (RAIZ / ".env.example", RAIZ / "infra" / "envs" / "test" / ".env.example"):
            with self.subTest(ruta=str(ruta.relative_to(RAIZ))):
                self.assertEqual([], problemas(ruta.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
