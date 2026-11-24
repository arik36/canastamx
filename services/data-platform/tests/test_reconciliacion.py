"""Pruebas de `ingestion/reconciliacion.py` y `ingestion/h3.py` · T053, segunda tarjeta (#206).

Contra el criterio de #206: «`articulo_canonico_key` sale de la reconciliación y los
agregados se recalculan sobre él sin tocar los hechos. La lista de palabras que no
identifican está en el repositorio, por producto o por categoría, y `congelado`
contra `descongelado` [...] no se une. H3 queda medida sobre los 200 pares como dicen
los ADR 004 y 014: cobertura y precisión con su población, y aparte los pares que sólo
difieren en `marca`. Si la meta no se alcanza, se reporta la cifra que salió.»

Las reglas son las de `contracts/reconciliacion-v1.yaml`, las mismas que corren en la
carga: una prueba con otras reglas probaría otra reconciliación. Los pares de las
pruebas son los de la muestra calificada, con su número.
"""

import dataclasses
import sys
from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest
import yaml

PLATAFORMA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATAFORMA / "ingestion"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import estrella
import h3
import reconciliacion as rec
from codigo import codigo_sin_comentarios
from ingesta import leer_contrato

duckdb = pytest.importorskip("duckdb")


@pytest.fixture(scope="module")
def contrato():
    return leer_contrato()


@pytest.fixture(scope="module")
def reglas(contrato):
    return rec.leer_reglas(contrato)


@pytest.fixture(scope="module")
def con():
    return duckdb.connect()


@pytest.fixture(scope="module")
def muestra():
    return h3.leer_muestra()


BASE = {"lote": "07-2026_Q2", "ocurrencia": 1, "ingerido_en": "2026-08-01 00:00:00+00",
        "entidad": "Guanajuato", "clave_producto": "pasta para sopa",
        "clave_presentacion": "paquete 200 gr letra", "producto": "Pasta para Sopa",
        "presentacion": "Paquete 200 Gr. Letra", "categoria": "Pastas",
        "catalogo_normalizado": "BASICOS", "clave_marca": "BARILLA",
        "clave_nombre_comercial": "soriana centro", "clave_direccion": "juarez 1",
        "municipio": "León", "nombre_comercial": "Soriana Centro", "direccion": "Juárez 1",
        "giro": "Supermercado", "latitud": 21.12, "longitud": -101.68,
        "cadena_comercial": "Soriana", "fecha_registro": "2026-07-20", "precio": "10.00"}
LETRAS = {"clave_presentacion": "paquete 200 gr letras", "presentacion": "Paquete 200 Gr. Letras"}


def _estrella(contrato, filas, reglas=None, orden=None):
    """La estrella de unas filas de la capa intermedia hechas a mano, como en
    test_estrella.py."""
    con = duckdb.connect()
    crudo = pd.DataFrame([{**BASE, "huella_fila": f"h{i:04d}", **f} for i, f in enumerate(filas)])
    con.register("crudo", crudo)
    con.execute(f"""CREATE OR REPLACE TABLE origen AS
        SELECT * REPLACE (CAST(ocurrencia AS INTEGER) AS ocurrencia,
                          CAST(ingerido_en AS TIMESTAMPTZ) AS ingerido_en,
                          CAST(latitud AS DOUBLE) AS latitud,
                          CAST(longitud AS DOUBLE) AS longitud,
                          CAST(fecha_registro AS DATE) AS fecha_registro,
                          CAST(precio AS DECIMAL(12,2)) AS precio)
        FROM crudo {orden or ''}""")
    return con, estrella.construir(con, contrato, origen="origen", reglas=reglas)


def _juntos(reglas, con, producto, *presentaciones):
    """¿La reconciliación deja todas estas presentaciones en un solo grupo?"""
    grupos = rec.agrupar([(i, producto, p, 1) for i, p in enumerate(presentaciones)], reglas, con)
    return len({canonico for canonico, _, _ in grupos.values()}) == 1


# ── Las reglas, una por una ────────────────────────────────────────────────

@pytest.mark.parametrize("producto, a, b", [
    ("pasta para sopa", "paquete 200 gr letra", "paquete 200 gr letras"),              # 001
    ("harina de trigo", "paquete 800 a 880 gr", "paquete 800 o 880 gr"),               # 008
    ("azucar", "bolsa plastico 2 kg estandar morena",
     "bolsa plastico 2 kg estandar o morena"),                                         # 009
    ("pasta para sopa", "paquete 200 gr fideo 2", "paquete 200 gr fideo no 2"),        # 012
    ("papel higienico", "paquete 4 rollos 200 hoja dobles",
     "paquete 4 rollos 200 hojas dobles"),                                             # 013
    ("cerveza", "paquete con 12 latas de 355 ml", "paquete con 12 latas de 355 ml c u"),  # 021
    ("jamon", "1 kg granel de cerdo y pavo virginia",
     "1 kg granel de pavo y cerdo virginia"),                                          # 033
    ("arroz", "bolsa 900 gr extra grano largo", "bolsa 900 gr grano extra largo"),     # 055
    ("crema solida", "frasco 200 gr", "frasco 200 ml"),                                # 078
    ("salchicha", "paquete 500 gr con pavo", "paquete 500 gr de pavo"),                # 154
    ("lavadora", "modelo mh1536", "modelo mh 1536"),                                   # ADR 004 §3
])
def test_lo_que_p1_llama_escritura_da_la_misma_llave(reglas, producto, a, b):
    assert rec.llave(producto, a, reglas) == rec.llave(producto, b, reglas)


@pytest.mark.parametrize("producto, a, b", [
    ("camaron", "1 kg granel congelado", "1 kg granel descongelado"),    # el caso del ADR 004
    ("pilas electricas", "paquete con 6 aa", "paquete con 6 aaa"),        # 002
    ("panales desechables", "paquete 40 piezas etapa 4 nina",
     "paquete 40 piezas etapa 4 nino"),                                   # 003
    ("toalla femenina", "bolsa 10 piezas con alas", "bolsa 10 piezas sin alas"),   # P2 · 019
    ("jitomate", "1 kg granel primera", "1 kg granel tercera"),           # P2
    ("pan de caja", "paquete 680 gr blanco", "paquete 680 gr integral"),  # ADR 014 §5 bis
    ("leche", "caja 1 lt entera", "caja 2 lt entera"),                    # el número define
    ("papel higienico", "paquete 4 rollos 200 hojas", "paquete 200 rollos 4 hojas"),  # y su orden
])
def test_lo_que_identifica_al_articulo_lo_deja_aparte(reglas, con, producto, a, b):
    assert rec.llave(producto, a, reglas) != rec.llave(producto, b, reglas)
    assert not _juntos(reglas, con, producto, a, b), "la comparación difusa los unió"


def test_la_lista_es_por_producto(reglas):
    """ADR 014 §5 bis: «La lista no puede ser global.»"""
    def igual(producto, a, b):
        return rec.llave(producto, a, reglas) == rec.llave(producto, b, reglas)

    assert igual("jabon de pasta", "barra 400 gr con envoltura azul",
                 "barra 400 gr con envoltura")                                  # 028
    assert not igual("detergente p ropa", "bolsa 1 kg polvo azul", "bolsa 1 kg polvo"), (
        "`azul` sólo se quita de los productos donde alguien lo clasificó")
    # La gelatina de limón siempre es de agua (039); la de otro sabor, no se sabe.
    assert igual("gelatina en polvo", "bolsa 120 gr agua limon", "bolsa 120 gr limon")
    assert not igual("gelatina en polvo", "bolsa 120 gr agua fresa", "bolsa 120 gr fresa")
    # Una frase de la lista se reconoce también en plural.
    assert igual("jabon de pasta", "barra 400 gr con envoltura rosas", "barra 400 gr con envoltura")


def test_lo_que_es_si_por_el_default_no_entra_a_la_lista(reglas):
    """El default de P3 es una postura de quien califica, no una clase (CU-06 · 2b)."""
    anotados = {(producto, palabra) for producto, palabra, _, _ in reglas.sin_clasificar}
    assert anotados == {("jabon de tocador", "aqua"), ("refresco", "naranja"),
                        ("arroz", "verde"), ("detergente p trastes", "pure lemon")}
    for producto, palabra in anotados:
        assert rec.llave(producto, f"barra 135 gr {palabra}", reglas) != rec.llave(
            producto, "barra 135 gr", reglas), f"`{palabra}` se quitó de {producto}"


def test_la_difusa_une_los_si_de_la_muestra_y_ningun_caso_de_prueba(reglas, con):
    assert _juntos(reglas, con, "pasta para sopa", "paquete 200 gr lengua",
                   "paquete 200 gr lenguita")                               # 006 · 0.950
    assert _juntos(reglas, con, "salchicha", "1 kg granel viena", "1 kg granel vienesa")   # 011
    assert reglas.no_se_unen, "la lista de casos de prueba no puede estar vacía"
    for a, b in reglas.no_se_unen:
        assert not _juntos(reglas, con, "camaron", f"1 kg granel {a}", f"1 kg granel {b}")


def test_ninguna_regla_esta_escrita_en_el_codigo(reglas):
    """El umbral, las unidades y las palabras de la lista viven en el contrato. En el
    código, sin comentarios ni textos (tests/codigo.py), no está ninguno. Las palabras
    de menos de tres letras no se buscan: `con` o `e` también son nombres de variable."""
    codigo = codigo_sin_comentarios(PLATAFORMA / "ingestion" / "reconciliacion.py")
    piezas = set(codigo.replace("(", " ").replace(")", " ").replace(",", " ").split())
    assert str(reglas.umbral) not in piezas, "el umbral está escrito en el código"
    de_la_lista = {p for frases in reglas.lista.values() for f in frases
                   for p in f.palabras + f.por} | set(reglas.unidad)
    escritas = {p for p in de_la_lista if len(p) >= 3} & piezas
    assert not escritas, f"en el código: {sorted(escritas)}"
    assert "dagster" not in codigo.lower()


# ── Las reglas se comprueban al leerlas ────────────────────────────────────

def _reglas_con(tmp_path, cambiar):
    crudo = yaml.safe_load((PLATAFORMA.parents[1] / "contracts" / "reconciliacion-v1.yaml")
                           .read_text(encoding="utf-8"))
    cambiar(crudo)
    ruta = tmp_path / "reconciliacion.yaml"
    ruta.write_text(yaml.safe_dump(crudo, allow_unicode=True), encoding="utf-8")
    return ruta


def _entrada(**kw):
    return {"clase": "color de empaque", "par": "999", "clasifico": "prueba", **kw}


@pytest.mark.parametrize("cambiar, dice", [
    (lambda c: c["no_identifican"].setdefault("arroz", []).append(
        _entrada(quitar="verde", clase="default de P3")), "sólo entra lo clasificado"),
    (lambda c: c["no_identifican"].setdefault("cerveza", []).append(
        _entrada(quitar="12 latas")), "número"),
    (lambda c: c["no_identifican"].setdefault("toalla femenina", []).append(
        _entrada(quitar="sin alas")), "nunca se quita"),
    (lambda c: c["no_identifican"].setdefault("refresco", []).append(
        _entrada(quitar="naranja")), "también en `no_identifican`"),
    (lambda c: c["no_identifican"].setdefault("Refresco", []).append(
        _entrada(quitar="naranja")), "forma canónica"),
    (lambda c: c["no_identifican"]["pan de caja"][0].pop("par"), "no dice su par"),
    (lambda c: c["formas_ortograficas"].update(orden="todo"), "conservan su orden"),
])
def test_una_lista_que_no_cumple_su_definicion_no_se_lee(tmp_path, cambiar, dice):
    with pytest.raises(rec.ReglasIlegibles, match=dice):
        rec.leer_reglas(ruta=_reglas_con(tmp_path, cambiar))


# ── En la estrella ─────────────────────────────────────────────────────────

def test_las_variantes_comparten_canonico_y_los_hechos_no_se_tocan(contrato):
    """**La prueba del criterio.** `letra` y `letras` (001) son un artículo: un solo
    canónico y un solo agregado, con los tres precios. Los hechos son los mismos que
    sin reconciliar."""
    filas = [{"precio": "10.00"}, {"precio": "11.00"}, {**LETRAS, "precio": "12.00"}]
    con, cuentas = _estrella(contrato, filas)
    assert cuentas["dim_articulo"] == 2, "la reconciliación no borra artículos"
    canonicos = dict(con.execute("SELECT presentacion_c, articulo_canonico_key "
                                 "FROM dim_articulo").fetchall())
    assert len(set(canonicos.values())) == 1
    assert con.execute("SELECT n, minimo, maximo FROM agg_articulo_entidad_quincena").fetchall() \
        == [(3, Decimal("10.00"), Decimal("12.00"))]
    assert con.execute("SELECT count(*) FROM rango_historico").fetchone()[0] == 1

    sin_reglas = {**contrato, "reconciliacion": {"reglas": "contracts/no-esta.yaml"}}
    sin, _ = _estrella(sin_reglas, filas)
    assert con.execute("SELECT * FROM hechos_precio ORDER BY observacion_id").fetchall() == \
        sin.execute("SELECT * FROM hechos_precio ORDER BY observacion_id").fetchall()
    assert sin.execute("SELECT count(*) FROM agg_articulo_entidad_quincena").fetchone()[0] == 2


def test_congelado_y_descongelado_no_se_unen(contrato):
    """El caso que dejó el ADR 004 para detectar un umbral flojo."""
    con, _ = _estrella(contrato, [
        {"clave_producto": "camaron", "producto": "Camarón",
         "clave_presentacion": "1 kg granel congelado", "presentacion": "1 Kg. Granel Congelado"},
        {"clave_producto": "camaron", "producto": "Camarón",
         "clave_presentacion": "1 kg granel descongelado",
         "presentacion": "1 Kg. Granel Descongelado"}])
    assert con.execute("SELECT count(DISTINCT articulo_canonico_key) FROM dim_articulo") \
        .fetchone()[0] == 2
    assert con.execute("SELECT count(*) FROM agg_articulo_entidad_quincena").fetchone()[0] == 2


def test_el_canonico_es_el_de_mas_hechos_y_el_empate_lo_decide_la_presentacion(contrato):
    def canonico(filas):
        con, _ = _estrella(contrato, filas)
        return con.execute("SELECT c.presentacion_c FROM dim_articulo a JOIN dim_articulo c "
                           "ON c.articulo_key = a.articulo_canonico_key").fetchall()

    assert canonico([{}, LETRAS, LETRAS]) == [("paquete 200 gr letras",)] * 2
    assert canonico([{}, LETRAS]) == [("paquete 200 gr letra",)] * 2
    assert canonico([LETRAS, {}]) == [("paquete 200 gr letra",)] * 2, "cambió con el orden"


def test_el_orden_de_las_filas_no_cambia_la_reconciliacion(contrato, muestra):
    """RF-25, con los 322 artículos de la muestra: la misma estrella, llaves y
    canónicos incluidos, en cualquier orden."""
    filas = _filas_de_la_muestra(muestra)
    uno, _ = _estrella(contrato, filas)
    otro, _ = _estrella(contrato, filas, orden="ORDER BY hash(huella_fila)")
    assert estrella.huella(uno) == estrella.huella(otro)


def test_sin_reglas_cada_articulo_es_su_propio_canonico_y_la_estrella_se_carga(contrato):
    """CU-06 · 1a. No se reconcilia nada, se dice por qué, y la estrella no se pierde."""
    roto = {**contrato, "reconciliacion": {"reglas": "contracts/no-esta.yaml"}}
    con, cuentas = _estrella(roto, [{}, LETRAS])
    assert cuentas["hechos_precio"] == 2
    assert con.execute("SELECT bool_and(articulo_canonico_key = articulo_key) "
                       "FROM dim_articulo").fetchone()[0]
    r = rec.resumen(con)
    assert r["estado"] == rec.NO_CORRIO and "no-esta.yaml" in r["motivo"]

    sin_campo = {k: v for k, v in contrato.items() if k != "reconciliacion"}
    con, _ = _estrella(sin_campo, [{}, LETRAS])
    assert "reconciliacion.reglas" in rec.resumen(con)["motivo"]


def test_un_umbral_flojo_es_una_regla_rota(contrato, reglas):
    """Si el umbral uniera `congelado` con `descongelado`, no se reconcilia nada."""
    flojas = dataclasses.replace(reglas, umbral=0.80)
    con, _ = _estrella(contrato, [{}, LETRAS], reglas=flojas)
    r = rec.resumen(con)
    assert r["estado"] == rec.NO_CORRIO
    assert "congelado" in r["motivo"] and "flojo" in r["motivo"]


def test_el_resumen_cuenta_lo_que_hizo(contrato):
    """CU-06 paso 5: cuántos reconcilió y cuántos quedaron solos."""
    con, _ = _estrella(contrato, [
        {}, LETRAS,
        {"clave_presentacion": "paquete 200 gr lengua", "presentacion": "Paquete 200 Gr. Lengua"},
        {"clave_presentacion": "paquete 200 gr lenguita",
         "presentacion": "Paquete 200 Gr. Lenguita"},
        {"clave_presentacion": "paquete 200 gr fideo 2", "presentacion": "Paquete 200 Gr. Fideo 2"}])
    r = rec.resumen(con)
    assert r["estado"] == rec.APLICADA and r["version"] == "1.0.0"
    assert (r["articulos"], r["grupos"], r["reconciliados"], r["solos"], r["variantes"],
            r["por_llave"], r["por_difusa"]) == (5, 2, 4, 1, 2, 1, 1)


# ── H3 ─────────────────────────────────────────────────────────────────────

def _filas_de_la_muestra(muestra):
    """Una fila de la capa intermedia por cada artículo de la muestra."""
    articulos = sorted({p.a for p in muestra} | {p.b for p in muestra})
    return [{"clave_producto": producto, "producto": producto,
             "clave_presentacion": presentacion, "presentacion": presentacion}
            for producto, presentacion in articulos]


def test_la_muestra_trae_los_200_pares_del_recuento(muestra):
    assert len(muestra) == h3.PARES
    for mitad, si in (("parecido", 30), ("azar", 3)):
        de_la_mitad = [p for p in muestra if p.mitad == mitad]
        assert len(de_la_mitad) == h3.POR_MITAD
        assert sum(p.si for p in de_la_mitad) == si, "el conteo vigente del ADR 014"
    assert all(p.producto_a == p.producto_b for p in muestra), "el universo es el mismo producto"
    assert not any(p.a == p.b for p in muestra), "sólo marca: cero por construcción (ADR 004 §2)"


def test_h3_dentro_de_la_muestra(contrato, reglas, muestra):
    """La estrella con los 322 artículos de la muestra, medida como se mide la real.
    Con todos los artículos en el catálogo, las dos cifras son la misma.

    Las cifras van fijas a propósito: si una entrada de la lista o el umbral cambia,
    esta prueba cambia con ellos y el cambio de H3 se ve en la revisión."""
    con, _ = _estrella(contrato, _filas_de_la_muestra(muestra))
    articulos = con.execute("SELECT articulo_key, producto_c, presentacion_c, "
                            "articulo_canonico_key FROM dim_articulo ORDER BY 1").fetchall()
    r = h3.medir(muestra, {(p, q): c for _, p, q, c in articulos})

    assert r["total"]["fp"] == 0, "ningún «no» quedó unido"
    assert r["total"]["sin_medir"] == r["total"]["solo_marca"] == 0
    assert (r["cobertura"]["numerador"], r["cobertura"]["denominador"]) == (26, 30)
    assert (r["precision"]["numerador"], r["precision"]["denominador"]) == (3, 3)
    assert (r["precision_200"]["numerador"], r["precision_200"]["denominador"]) == (29, 29)
    assert all(r["cumple"].values())
    separados = sorted(f"{p.n:03d}" for p, res in r["pares"] if res == "fn")
    assert separados == sorted(par for _, _, par, _ in reglas.sin_clasificar), (
        "los únicos «sí» separados son los que la lista deja fuera a propósito")

    texto = h3.informe(muestra, articulos, reglas, con, "prueba", hoy="2026-11-23")
    for linea in ("✓ la estrella cargada tiene los grupos que dan estas reglas",
                  "1 · SOBRE LOS 200 PARES", "H3 SE CUMPLE sobre los 200 pares.",
                  "2 · DENTRO DEL ALCANCE DE LA PLATAFORMA · los 200 pares",
                  "DENTRO DEL ALCANCE: SE CUMPLE.",
                  "PRECISIÓN · mitad al azar · 3 / 3 = 100.0 %",
                  "sólo difieren en marca", "LAS DOS SON DENTRO DE LA MUESTRA",
                  "LOS «NO» UNIDOS · 0 de 167", "TODAS LAS UNIONES DEL CATÁLOGO"):
        assert linea in texto, linea
    assert texto.count("COBERTURA · mitad por parecido · 26 / 30 = 86.7 %") == 2
    assert "difusa · viena / vienesa 0.943 ≥ 0.93" in texto
    assert "no están en dim_articulo" not in texto and "FUERA DEL ALCANCE" not in texto


def test_h3_con_articulos_fuera_del_alcance(contrato, reglas, muestra):
    """La muestra salió del corpus sin el recorte de entidades: algunos de sus artículos
    no llegan a la plataforma. La cifra de H3 los mide igual, con la misma
    reconciliación, y la del alcance los deja fuera y lo dice."""
    afuera = {("salchicha", "1 kg granel viena"),                 # 011, unido por la difusa
              ("arroz", "bolsa 900 gr extra grano largo")}        # 055, unido por el orden
    filas = [f for f in _filas_de_la_muestra(muestra)
             if (f["clave_producto"], f["clave_presentacion"]) not in afuera]
    con, _ = _estrella(contrato, filas)
    articulos = con.execute("SELECT articulo_key, producto_c, presentacion_c, "
                            "articulo_canonico_key FROM dim_articulo ORDER BY 1").fetchall()

    grupo, faltan = h3.con_la_muestra(muestra, articulos, reglas, con)
    assert set(faltan) == afuera
    assert grupo[("salchicha", "1 kg granel viena")] == grupo[("salchicha", "1 kg granel vienesa")]

    texto = h3.informe(muestra, articulos, reglas, con, "prueba", hoy="2026-11-23")
    for linea in ("2 artículos de la muestra no están en dim_articulo, y 2 pares",
                  "H3 SE CUMPLE sobre los 200 pares.",
                  "COBERTURA · mitad por parecido · 26 / 30 = 86.7 %",
                  "2 · DENTRO DEL ALCANCE DE LA PLATAFORMA · los 198 pares",
                  "COBERTURA · mitad por parecido · 24 / 28 = 85.7 %",
                  "FUERA DEL ALCANCE · 2 pares, 2 artículos", "pares: 011 055",
                  "1 kg granel viena  ||  1 kg granel vienesa  · fuera del alcance"):
        assert linea in texto, linea
    assert "sumar esos artículos cambia de grupo" not in texto


def test_si_la_meta_no_se_alcanza_se_reporta_la_cifra(reglas, con, muestra):
    """Sin lista y sin difusa, sólo P1 une: 12 de 30. Y una estrella cargada sin
    reconciliar no une ninguno: 0 de 30, con la precisión sin población. El informe da
    las dos cifras con sus números, y avisa que la estrella no tiene estos grupos."""
    debiles = dataclasses.replace(reglas, lista={}, umbral=1.0)
    articulos = sorted({p.a for p in muestra} | {p.b for p in muestra})
    filas = [(i, p, q, i) for i, (p, q) in enumerate(articulos, start=1)]
    r = h3.medir(muestra, {(p, q): c for _, p, q, c in filas})
    assert r["cobertura"]["valor"] == 0 and r["precision"]["valor"] is None
    assert not any(r["cumple"].values())

    texto = h3.informe(muestra, filas, debiles, con, "prueba", hoy="2026-11-23")
    for linea in ("COBERTURA · mitad por parecido · 12 / 30 = 40.0 %",
                  "H3 NO SE CUMPLE sobre los 200 pares.",
                  "COBERTURA · mitad por parecido · 0 / 30 = 0.0 %", "0 / 0 = sin población",
                  "DENTRO DEL ALCANCE: NO SE CUMPLE.", "NO se cumple",
                  "están en otro grupo que el que dan estas reglas"):
        assert linea in texto, linea


def test_un_par_sin_calificar_detiene_la_medicion(tmp_path):
    texto = h3.MUESTRA.read_text(encoding="utf-8").replace(
        "¿son el MISMO artículo?  [x] sí   [ ] no", "¿son el MISMO artículo?  [ ] sí   [ ] no", 1)
    ruta = tmp_path / "muestra.txt"
    ruta.write_text(texto, encoding="utf-8")
    with pytest.raises(ValueError, match="par 001"):
        h3.leer_muestra(ruta)
