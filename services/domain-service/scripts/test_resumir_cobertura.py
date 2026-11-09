import tempfile
import unittest
from pathlib import Path

from resumir_cobertura import PAQUETE, cobertura, pruebas, resumen


class ResumenCoberturaTest(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.carpeta = Path(self.temporal.name)

    def archivo(self, nombre, texto):
        archivo = self.carpeta / nombre
        archivo.write_text(texto, encoding="utf-8")
        return archivo

    def test_poblacion_incluye_clases_internas_y_excluye_paquetes_ajenos(self):
        archivo = self.archivo("jacoco.csv", f"""PACKAGE,CLASS,LINE_MISSED,LINE_COVERED,BRANCH_MISSED,BRANCH_COVERED
{PAQUETE}.canasta,Canasta,2,8,1,3
{PAQUETE}.canasta,Canasta.ArticuloNoExisteException,2,0,0,0
{PAQUETE}_ajeno,Ajena,999,0,0,0
mx.tecnm.canastamx.domain_service.application,Servicio,999,0,0,0
""")
        clases = cobertura(archivo)
        self.assertEqual(2, len(clases))
        texto = resumen(clases, {"tests": 76, "failures": 0, "errors": 0, "skipped": 0}, "abc", True)
        self.assertIn("Líneas: **8/12 (66.67%)**", texto)
        self.assertIn("Ramas: **3/4 (75.00%)**", texto)
        self.assertIn("N/A (sin ramas)", texto)
        self.assertIn(f"Clases sin líneas ejecutadas: `{PAQUETE}.canasta."
                      "Canasta.ArticuloNoExisteException`", texto)
        self.assertIn("cambios locales sin commit", texto)

    def test_rechaza_cobertura_sin_poblacion(self):
        archivo = self.archivo("jacoco.csv", "PACKAGE,CLASS,LINE_MISSED,LINE_COVERED\n")
        with self.assertRaisesRegex(ValueError, "domain"):
            cobertura(archivo)

    def test_suma_las_suites_surefire(self):
        self.archivo("TEST-A.xml", '<testsuite tests="4" failures="0" errors="0" skipped="1"/>')
        self.archivo("TEST-B.xml", '<testsuite tests="6" failures="0" errors="0" skipped="0"/>')
        self.assertEqual({"tests": 10, "failures": 0, "errors": 0, "skipped": 1}, pruebas(self.carpeta))

    def test_rechaza_informes_ausentes_cero_pruebas_y_todas_omitidas(self):
        with self.assertRaises(ValueError):
            pruebas(self.carpeta)
        for tests, skipped in ((0, 0), (3, 3)):
            with self.subTest(tests=tests):
                self.archivo("TEST-A.xml", f'<testsuite tests="{tests}" skipped="{skipped}"/>')
                with self.assertRaises(ValueError):
                    pruebas(self.carpeta)

    def test_rechaza_pruebas_con_fallos_o_errores(self):
        for campo in ("failures", "errors"):
            with self.subTest(campo=campo):
                self.archivo("TEST-A.xml", f'<testsuite tests="3" {campo}="1"/>')
                with self.assertRaisesRegex(ValueError, "fallidas"):
                    pruebas(self.carpeta)


if __name__ == "__main__":
    unittest.main()
