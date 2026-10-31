"""Pruebas de `ingestion/reparacion.py` · el `?` de CU-03, antes del 5% de D-07.

Escritas contra el contrato y el caso de uso, frase por frase:

  · «el diccionario para los valores con un solo candidato»          (CU-03 · 2)
  · «si un candidato aparece al menos 10 veces más que el siguiente,
    el proceso repara con él; si no, revision_humana»                (CU-03 · 2a)
  · «el valor no tiene ningún candidato → codificacion_irrecuperable» (CU-03 · 2b)
  · «el diccionario no se puede leer → el lote no avanza»            (CU-03 · 2c)
  · «las once columnas de aplica_a», y no las seis de T031

Las tablas de prueba se escriben en una carpeta temporal y una COPIA del contrato
apunta a ellas: así cada prueba dice exactamente qué gemelos hay y cuántas filas
tienen, sin depender de lo que traiga la tabla real del corpus. Dos pruebas, al
principio, revisan las tablas reales.
"""

import copy
import csv
import io
import subprocess
import sys
import tokenize
from pathlib import Path

import pandas as pd
import pytest

PLATAFORMA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATAFORMA / "ingestion"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import lote
import reparacion
from ambiguos import con_candidatos
from codigo import codigo_sin_comentarios
from ingesta import CONTRATO, columnas_del_contrato, leer_contrato


@pytest.fixture(scope="module")
def contrato():
    return leer_contrato()


@pytest.fixture(scope="module")
def columnas(contrato):
    return columnas_del_contrato(contrato)


def fila(columnas, **kw):
    r = {c: "x" for c in columnas}
    r.update({"estado": "Guanajuato", "catalogo": "Basicos",
              "fecha_registro": "2026/07/20", "precio": "25.00",
              "latitud": "21.12", "longitud": "-101.68"})
    r.update(kw)
    return r


def marco(columnas, filas):
    return pd.DataFrame(filas, columns=columnas, dtype="string")


# ── Las tablas reales ──────────────────────────────────────────────────────

def test_el_diccionario_real_cumple_la_definicion_de_gemelo(contrato):
    """El contrato lo afirma (1.3.1): 0 pares de distinta longitud, 0 que difieran
    fuera del `?`, 0 llaves repetidas. Aquí se comprueba, entrada por entrada."""
    rep = contrato["normalizacion"]["reparar_interrogantes"]
    with (CONTRATO.parent.parent / rep["diccionario"]).open(encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    assert filas, "el diccionario está vacío"
    assert all(reparacion.es_gemelo(r["valor_roto"], r["reparado"]) for r in filas)
    assert len({(r["columna"], r["valor_roto"]) for r in filas}) == len(filas)
    assert {r["columna"] for r in filas} <= set(rep["aplica_a"])
    assert any(r["valor_roto"].count("?") > 1 for r in filas), (
        "el contrato advierte que un valor puede traer más de un `?`")


def test_la_tabla_de_candidatos_del_contrato_existe_y_cumple(contrato):
    """La declara la 1.3.6 y sale del corpus con
    `docs/datos/perfilado/mojibake-ambiguos.py --escribir`. Si falta, ningún lote
    avanza (CU-03 · 2c): por eso esta prueba no se salta, falla."""
    tablas = reparacion.leer_tablas(contrato)
    assert tablas.candidatos, "la tabla de candidatos no trae ningún ambiguo"
    assert all(len(c) >= 2 for c in tablas.candidatos.values())
    assert not set(tablas.candidatos) & set(tablas.diccionario)


# ── Qué es un gemelo ───────────────────────────────────────────────────────

@pytest.mark.parametrize("roto,sano,es", [
    ("Camar?n", "Camarón", True),
    ("F?rmula L?ctea", "Fórmula Láctea", True),     # más de un `?`
    ("Camar?n", "Camaron", True),                   # el `?` acepta cualquier letra
    ("Camar?n", "Camarones", False),                # otra longitud
    ("Camar?n", "Comarón", False),                  # difiere fuera del `?`
    ("Camar?n", "Camar?n", False),                  # un candidato no trae `?`
    ("a?b", "a\nb", False),                         # como el `.` de mojibake.py
])
def test_es_gemelo_es_la_definicion_del_contrato(roto, sano, es):
    assert reparacion.es_gemelo(roto, sano) is es


# ── CU-03 · 2 · el diccionario ─────────────────────────────────────────────

def test_lo_del_diccionario_se_repara_y_no_se_aparta(contrato, columnas):
    df = marco(columnas, [fila(columnas, producto="Camar?n"),
                          fila(columnas, producto="F?rmula L?ctea")])
    filas, registros, r = reparacion.apartar_irreparables(df, contrato)
    assert registros == [] and len(filas) == 2
    assert r["por_columna"]["producto"] == {"ocurrencias": 2, "reparables": 2,
                                            "a_cuarentena": 0}
    assert r["valores_reparados"]["por_diccionario"] == 2


def test_las_filas_salen_tal_como_llegaron(contrato, columnas):
    """La reparación la aplica la capa intermedia; la compuerta sólo decide. Así la
    cuarentena y la clave de fila ven la fila como llegó."""
    df = marco(columnas, [fila(columnas, producto="Camar?n")])
    filas, _, _ = reparacion.apartar_irreparables(df, contrato)
    assert filas["producto"].tolist() == ["Camar?n"]


# ── CU-03 · 2a · la frecuencia ─────────────────────────────────────────────

def test_el_ambiguo_que_domina_se_repara_y_el_parejo_va_a_revision_humana(
        contrato, columnas, tmp_path):
    otro = con_candidatos(contrato, tmp_path)
    df = marco(columnas, [fila(columnas, marca="Kellogg?s"),
                          fila(columnas, marca="Nestl?")])
    filas, registros, r = reparacion.apartar_irreparables(df, otro)
    assert filas["marca"].tolist() == ["Kellogg?s"]
    assert [x["motivo"] for x in registros] == ["revision_humana"]
    assert registros[0]["valores"][0]["candidatos"] == [
        {"candidato": "Nestlé", "filas": 300}, {"candidato": "Nestle", "filas": 200}]
    assert r["valores_reparados"]["por_frecuencia"] == 1
    mapa = reparacion.reparaciones_del_contrato(otro)
    assert mapa[("marca", "Kellogg?s")] == "Kellogg's"
    assert ("marca", "Nestl?") not in mapa


def test_el_umbral_lo_decide_el_contrato(contrato, columnas, tmp_path):
    """El 10 no se puede buscar en el código como otras cifras —aparece en
    cualquier lado—, así que se comprueba por su efecto: se mueve en una copia del
    contrato y la misma fila cambia de destino."""
    df = marco(columnas, [fila(columnas, marca="Kellogg?s"), fila(columnas, marca="Nestl?")])
    estricto = con_candidatos(contrato, tmp_path, umbral=50)      # 5000/120 = 41.7
    _, registros, _ = reparacion.apartar_irreparables(df, estricto)
    assert sorted(x["fila"]["marca"] for x in registros) == ["Kellogg?s", "Nestl?"]

    laxo = con_candidatos(contrato, tmp_path, umbral=1.4)         # 300/200 = 1.5
    _, registros, _ = reparacion.apartar_irreparables(df, laxo)
    assert registros == []
    assert reparacion.reparaciones_del_contrato(laxo)[("marca", "Nestl?")] == "Nestlé"


def test_domina_desde_el_umbral_exacto(contrato, columnas, tmp_path):
    """CU-03 · 2a dice «al menos 10 veces más»: 10 a 1 exacto ya gana."""
    otro = con_candidatos(contrato, tmp_path, filas=[
        ("marca", "Ar?el", "Ariel", 1000), ("marca", "Ar?el", "Arpel", 100)])
    assert reparacion.reparaciones_del_contrato(otro)[("marca", "Ar?el")] == "Ariel"


def test_dos_gemelos_empatados_nunca_dominan(contrato, tmp_path):
    otro = con_candidatos(contrato, tmp_path, filas=[
        ("marca", "Ar?el", "Ariel", 100), ("marca", "Ar?el", "Arpel", 100)])
    d = reparacion.decisiones(otro)[("marca", "Ar?el")]
    assert d.reparado is None and d.motivo == "revision_humana"


# ── CU-03 · 2b · sin gemelo ────────────────────────────────────────────────

def test_lo_que_no_esta_en_ninguna_tabla_es_codificacion_irrecuperable(contrato, columnas):
    df = marco(columnas, [fila(columnas, producto="Adivina Qui?n Juego Xq7")])
    filas, registros, r = reparacion.apartar_irreparables(df, contrato)
    assert filas.empty
    assert [x["motivo"] for x in registros] == ["codificacion_irrecuperable"]
    assert registros[0]["valores"] == [{"columna": "producto",
                                        "valor": "Adivina Qui?n Juego Xq7",
                                        "motivo": "codificacion_irrecuperable",
                                        "candidatos": []}]
    assert r["por_motivo"] == {"codificacion_irrecuperable": 1}


# ── Las once columnas, no las seis de T031 ─────────────────────────────────

def test_se_busca_el_interrogante_en_las_once_columnas_de_aplica_a(contrato, columnas):
    """T031 lo buscaba en seis columnas. El contrato dice once, y entre ellas
    `catalogo` y `estado`, que son las del recorte del alcance."""
    aplica = contrato["normalizacion"]["reparar_interrogantes"]["aplica_a"]
    assert len(aplica) == 11
    df = marco(columnas, [fila(columnas, **{c: f"Roto?{i}"}) for i, c in enumerate(aplica)])
    _, registros, r = reparacion.apartar_irreparables(df, contrato)
    assert r["filas_en_cuarentena"] == 11
    assert {x["valores"][0]["columna"] for x in registros} == set(aplica)


def test_las_columnas_las_decide_el_contrato(contrato, columnas, tmp_path):
    """Si `giro` sale de `aplica_a`, un `?` en `giro` deja de buscarse."""
    df = marco(columnas, [fila(columnas, giro="Roto?")])
    otro = copy.deepcopy(contrato)
    rep = otro["normalizacion"]["reparar_interrogantes"]
    rep["aplica_a"] = [c for c in rep["aplica_a"] if c != "giro"]
    # El diccionario real trae `giro`; sin la columna en aplica_a, sus entradas
    # dejarían de ser válidas, así que se usa uno sin ellas.
    with (CONTRATO.parent.parent / rep["diccionario"]).open(encoding="utf-8") as f:
        lineas = [x for x in f if not x.startswith("giro,")]
    sin_giro = tmp_path / "sin-giro.csv"
    sin_giro.write_text("".join(lineas), encoding="utf-8")
    rep["diccionario"] = str(sin_giro)
    _, registros, _ = reparacion.apartar_irreparables(df, otro)
    assert registros == []
    _, registros, _ = reparacion.apartar_irreparables(df, contrato)
    assert len(registros) == 1


# ── Los registros de cuarentena ────────────────────────────────────────────

def test_una_fila_con_dos_motivos_lleva_dos_registros_y_cuenta_una_vez(
        contrato, columnas, tmp_path):
    """La tabla `cuarentena` es única por (corrida, huella, motivo), y para el 5%
    se cuentan FILAS distintas, no registros."""
    otro = con_candidatos(contrato, tmp_path)
    df = marco(columnas, [fila(columnas, producto="Nada?Igual", marca="Nestl?"),
                          fila(columnas, producto="P")])
    filas, registros, r = reparacion.apartar_irreparables(df, otro)
    assert sorted(x["motivo"] for x in registros) == ["codificacion_irrecuperable",
                                                      "revision_humana"]
    assert r["filas_en_cuarentena"] == 1 and r["registros_de_cuarentena"] == 2
    assert len(filas) == 1


def test_el_registro_tiene_la_forma_de_la_tabla_y_la_huella_de_la_compuerta(
        contrato, columnas):
    from compuerta import huella

    df = marco(columnas, [fila(columnas, producto="Nada?Igual")])
    _, registros, _ = reparacion.apartar_irreparables(df, contrato)
    x = registros[0]
    assert x["nivel"] == "FILA" and x["grupo"] is None
    assert x["compuerta"] == reparacion.NOMBRE_COMPUERTA
    assert x["fila"]["producto"] == "Nada?Igual"
    assert x["huella_fila"] == huella(x["fila"], columnas)


def test_los_dos_motivos_estan_en_el_catalogo_con_su_regla(contrato):
    declarados = contrato["motivos_de_fila"]
    r = reparacion.regla(contrato)
    assert declarados[r["motivo_sin_gemelo"]] == reparacion.REGLAS_DE_LOS_MOTIVOS["sin_gemelo"]
    assert declarados[r["motivo_empate"]] == reparacion.REGLAS_DE_LOS_MOTIVOS["empate"]


# ── CU-03 · 2c · sin tabla, el lote no avanza ──────────────────────────────

def test_sin_la_tabla_de_candidatos_el_lote_no_avanza(contrato, columnas, tmp_path):
    otro = copy.deepcopy(contrato)
    otro["normalizacion"]["reparar_interrogantes"]["ambiguo"]["candidatos"] = str(
        tmp_path / "no-existe.csv")
    with pytest.raises(FileNotFoundError, match="CU-03"):
        reparacion.apartar_irreparables(marco(columnas, [fila(columnas)]), otro)


def test_sin_el_campo_en_el_contrato_se_niega(contrato):
    otro = copy.deepcopy(contrato)
    del otro["normalizacion"]["reparar_interrogantes"]["ambiguo"]["candidatos"]
    with pytest.raises(ValueError, match="candidatos"):
        reparacion.regla(otro)


@pytest.mark.parametrize("filas,mensaje", [
    ([("marca", "Ar?el", "Arielito", 9), ("marca", "Ar?el", "Arpel", 1)], "no es gemelo"),
    ([("marca", "Ar?el", "Ariel", 9)], "un solo candidato"),
    ([("producto", "Camar?n", "Camarón", 9), ("producto", "Camar?n", "Camaron", 1)],
     "también está en el diccionario"),
    ([("marca", "Ar?el", "Ariel", 0), ("marca", "Ar?el", "Arpel", 1)], "entero positivo"),
    ([("folio", "Ar?el", "Ariel", 9), ("folio", "Ar?el", "Arpel", 1)], "aplica_a"),
])
def test_una_tabla_que_no_cumple_su_definicion_se_rechaza(contrato, tmp_path, filas, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        reparacion.leer_tablas(con_candidatos(contrato, tmp_path, filas=filas))


@pytest.mark.parametrize("ruta,valor", [
    (("metodo",), "por_parecido"),
    (("ambiguo", "poblacion"), "alcance"),
    (("ambiguo", "regla"), "a_mano"),
    (("ambiguo", "umbral"), 1),
    (("sin_gemelo", "accion"), "descartar"),
])
def test_si_el_contrato_cambia_la_regla_el_modulo_se_niega(contrato, ruta, valor):
    otro = copy.deepcopy(contrato)
    nodo = otro["normalizacion"]["reparar_interrogantes"]
    for paso in ruta[:-1]:
        nodo = nodo[paso]
    nodo[ruta[-1]] = valor
    with pytest.raises(ValueError):
        reparacion.regla(otro)


# ── La clave de fila compara con la regla entera ───────────────────────────

def test_la_clave_de_fila_une_lo_que_la_frecuencia_repara(contrato, columnas, tmp_path):
    """`clave_de_fila.compara` dice `repara_interrogantes`: la regla entera, no sólo
    el diccionario. Con sólo el diccionario, `Kellogg?s` partía su grupo."""
    otro = con_candidatos(contrato, tmp_path)
    df = marco(columnas, [fila(columnas, producto="Cereal", marca="Kellogg's", precio="40.00"),
                          fila(columnas, producto="Cereal", marca="Kellogg?s", precio="40.50")])
    _, _, r = lote.revisar_grupos(df, otro)
    assert r["grupos_captura_doble"] == 1 and r["sobrantes_captura_doble"] == 1


# ── Ninguna cifra escrita a mano ───────────────────────────────────────────

def _numeros(ruta):
    fuente = Path(ruta).read_text(encoding="utf-8")
    return {tok.string for tok in tokenize.generate_tokens(io.StringIO(fuente).readline)
            if tok.type == tokenize.NUMBER}


def test_el_umbral_no_esta_escrito_en_el_codigo(contrato):
    umbral = str(contrato["normalizacion"]["reparar_interrogantes"]["ambiguo"]["umbral"])
    for nombre in ("reparacion.py", "intermedia.py"):
        assert umbral not in _numeros(PLATAFORMA / "ingestion" / nombre), (
            f"el umbral ({umbral}) aparece como número en {nombre}; se lee del contrato")
        codigo = codigo_sin_comentarios(PLATAFORMA / "ingestion" / nombre)
        assert "dagster" not in codigo.lower()


# ── La cifra de CU-03 ──────────────────────────────────────────────────────

def test_la_cifra_de_cu03_se_mide_y_se_escribe_entre_sus_marcas(columnas, tmp_path):
    lote_csv = tmp_path / "07-2026_Q2.csv"
    filas = [fila(columnas, producto=f"P{i}", direccion=f"C{i}") for i in range(8)]
    filas += [fila(columnas, producto="Camar?n"),          # se repara
              fila(columnas, producto="Nada?Igual")]       # va a cuarentena
    with lote_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columnas)
        w.writeheader()
        w.writerows(filas)
    doc = tmp_path / "CU-03.md"
    doc.write_text(f"antes\n{reparacion.MARCA_INICIO}\nviejo\n{reparacion.MARCA_FIN}\ndespués\n",
                   encoding="utf-8")
    hecho = subprocess.run([sys.executable, str(PLATAFORMA / "ingestion" / "reparacion.py"),
                            "--medir", str(lote_csv), "--escribir", str(doc)],
                           capture_output=True, text=True, encoding="utf-8", check=False)
    assert hecho.returncode == 0, hecho.stderr
    texto = doc.read_text(encoding="utf-8")
    assert texto.startswith("antes\n") and texto.endswith("después\n")
    assert "viejo" not in texto
    assert "**2**" in texto, "dos filas del alcance traen `?`"
    assert "**1** (10.0000% del alcance)" in texto, texto
