"""Pruebas de `ingestion/lote.py` · las reglas que necesitan el lote completo.

Lo que estas pruebas tratan de demostrar, y conviene decirlo antes de leerlas:

1. Que la **colisión de precio alta** aparta el GRUPO completo y no la fila
   sobrante, que es lo que dice el contrato 1.3.3.
2. Que el **orden de la normalización importa**: reparar el `?` antes de
   normalizar une dos filas que de otro modo serían artículos distintos, y por
   tanto cambia qué grupos existen. Se demuestra con una colisión que SÓLO se ve
   si la reparación ocurrió.
3. Que la **frescura** reproduce las tres fechas que el propio contrato pone como
   ejemplo. Si alguien cambia los umbrales, estas tres pruebas lo dicen.
4. Que **ninguna cifra del contrato está escrita en el código**, y que la que el
   contrato guarda sólo en un comentario se reporta en vez de adivinarse.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

PLATAFORMA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATAFORMA / "ingestion"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import lote
from codigo import codigo_sin_comentarios
from ingesta import columnas_del_contrato, leer_contrato


@pytest.fixture(scope="module")
def contrato():
    return leer_contrato()


@pytest.fixture(scope="module")
def columnas(contrato):
    return columnas_del_contrato(contrato)


def fila(columnas, **kw):
    """Una fila que cumple el contrato, para que el defecto de cada prueba sea el
    único defecto. La fecha va en el formato que el contrato declara."""
    r = {c: "x" for c in columnas}
    r.update({"estado": "Guanajuato", "catalogo": "Basicos",
              "fecha_registro": "2026/07/20", "precio": "25.00",
              "latitud": "21.12", "longitud": "-101.68"})
    r.update(kw)
    return r


def marco(columnas, filas):
    return pd.DataFrame(filas, columns=columnas, dtype="string")


# ── La colisión de precio alta ─────────────────────────────────────────────

def test_el_grupo_completo_va_a_cuarentena_no_solo_la_sobrante(contrato, columnas):
    """Contrato 1.3.3 · `a_cuarentena: grupo_completo`. Con más de $50 de
    diferencia no se sabe cuál precio es el bueno, así que no se puede quedar
    ninguna de las dos."""
    df = marco(columnas, [
        fila(columnas, producto="Aceite", precio="40.00"),
        fila(columnas, producto="Aceite", precio="200.00"),
    ])
    limpias, registros, resumen = lote.revisar_grupos(df, contrato)
    assert resumen["filas_en_cuarentena"] == 2, "se apartó una fila, no el grupo"
    assert len(limpias) == 0
    assert {r["motivo"] for r in registros} == {"colision_precio_alta"}
    assert {r["nivel"] for r in registros} == {"GRUPO"}
    assert len({r["grupo"] for r in registros}) == 1, "las dos filas, un solo grupo"


def test_la_diferencia_de_mas_de_50_la_decide_el_contrato(contrato, columnas):
    """El umbral sale de `colision_precio_alta.mas_de`. Se comprueba moviéndolo en
    una copia del contrato: si estuviera escrito en el código, esto no cambiaría
    nada."""
    df = marco(columnas, [
        fila(columnas, producto="Arroz", precio="20.00"),
        fila(columnas, producto="Arroz", precio="37.00"),       # $17
    ])
    _, _, con_50 = lote.revisar_grupos(df, contrato)
    assert con_50["filas_en_cuarentena"] == 0, "$17 no es colisión alta con $50"

    bajado = dict(contrato)
    bajado["clave_de_fila"] = dict(contrato["clave_de_fila"])
    bajado["clave_de_fila"]["colision_precio_alta"] = {
        **contrato["clave_de_fila"]["colision_precio_alta"], "mas_de": 10}
    _, _, con_10 = lote.revisar_grupos(df, bajado)
    assert con_10["filas_en_cuarentena"] == 2, (
        "al bajar el umbral del contrato a $10 la compuerta no cambió: "
        "la cifra está escrita en el código")


def test_una_fila_sola_nunca_es_colision(contrato, columnas):
    df = marco(columnas, [fila(columnas, producto="Sal", precio="900.00")])
    limpias, registros, resumen = lote.revisar_grupos(df, contrato)
    assert registros == []
    assert len(limpias) == 1
    assert resumen["grupos"] == 0


def test_el_precio_ilegible_no_inventa_una_colision(contrato, columnas):
    """Una fila con el precio ilegible ya la aparta la compuerta de fila con
    `tipo_invalido`. Aquí no se vuelve a juzgar, y sobre todo no se cuenta como
    precio 0 —que convertiría cualquier grupo en colisión alta—."""
    df = marco(columnas, [
        fila(columnas, producto="Pan", precio="30.00"),
        fila(columnas, producto="Pan", precio="no es un numero"),
    ])
    _, registros, _ = lote.revisar_grupos(df, contrato)
    assert registros == []


def test_la_cuarentena_de_grupo_guarda_la_diferencia_como_evidencia(contrato, columnas):
    df = marco(columnas, [
        fila(columnas, producto="Huevo", precio="30.00"),
        fila(columnas, producto="Huevo", precio="130.00"),
    ])
    _, registros, _r = lote.revisar_grupos(df, contrato)
    assert all(r["diferencia"] == 100.0 for r in registros)
    assert all(r["filas_del_grupo"] == 2 for r in registros)


# ── El orden de la normalización ───────────────────────────────────────────

def test_reparar_el_interrogante_antes_de_normalizar_cambia_que_grupos_existen(
        contrato, columnas):
    """`normalizacion.orden: [reparar_interrogantes, canonica]`.

    `Az?car` y `Azúcar` son el mismo artículo: el diccionario del contrato lo dice.
    Si se normalizara primero, el `?` se habría borrado y el diccionario ya no
    encontraría el valor roto: serían dos artículos y su diferencia de $120 no
    sería colisión de nada. Esta prueba falla si alguien invierte el orden.
    """
    df = marco(columnas, [
        fila(columnas, producto="Az?car", precio="25.00"),
        fila(columnas, producto="Azúcar", precio="145.00"),
    ])
    _, registros, resumen = lote.revisar_grupos(df, contrato)
    assert resumen["grupos_en_colision"] == 1, (
        "no se unieron: la reparación del `?` no se aplicó antes de normalizar")
    assert resumen["filas_en_cuarentena"] == 2
    # Las dos filas caen en el MISMO grupo, que es la prueba de que se unieron.
    assert len({r["grupo"] for r in registros}) == 1


def test_la_normalizacion_canonica_se_lee_del_contrato(contrato):
    """El contrato guarda la expresión completa y dice por qué: «una normalización
    PARECIDA no es la misma normalización»."""
    expresion = lote.expresion_canonica(contrato, "producto")
    assert '"producto"' in expresion
    assert "strip_accents" in expresion and "regexp_replace" in expresion
    assert expresion in " ".join(contrato["normalizacion"]["canonica"].split("\n")) \
        or "strip_accents" in contrato["normalizacion"]["canonica"]


def test_si_el_contrato_cambia_el_orden_la_compuerta_se_niega(contrato, columnas):
    """Negarse es mejor que seguir con el orden viejo: si el contrato cambia el
    orden y el código no, los grupos saldrían mal en silencio."""
    otro = dict(contrato)
    otro["normalizacion"] = {**contrato["normalizacion"],
                             "orden": ["canonica", "reparar_interrogantes"]}
    df = marco(columnas, [fila(columnas, producto="Leche", precio="10.00"),
                          fila(columnas, producto="Leche", precio="99.00")])
    with pytest.raises(ValueError, match="normalizacion.orden"):
        lote.revisar_grupos(df, otro)


def test_el_diccionario_del_contrato_existe_y_tiene_las_entradas(contrato):
    rep = lote.reparaciones(contrato)
    assert len(rep) > 1000, f"el diccionario trae {len(rep)} entradas"
    # El contrato advierte que un valor puede traer MÁS DE UN `?`.
    assert any(k[1].count("?") > 1 for k in rep), (
        "ninguna entrada con dos `?`: el diccionario no es el que declara el contrato")


# ── La frescura ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("referencia,dias,estado", [
    ("2026-08-10", 10, "OK"),
    ("2026-08-25", 25, "AVISA"),
    ("2026-09-20", 51, "BLOQUEA"),
])
def test_la_frescura_reproduce_los_ejemplos_del_contrato(
        contrato, columnas, referencia, dias, estado):
    """Las tres fechas y los tres resultados están escritos en el comentario de
    `frescura.fecha_referencia`, medidos contra el 2026-07-31. Si estas tres no
    dan, o el código está mal o los umbrales del contrato cambiaron."""
    df = marco(columnas, [fila(columnas, fecha_registro="2026/07/31")])
    r = lote.revisar_frescura(df, contrato, referencia)
    assert r["dias"] == dias
    assert r["estado"] == estado


def test_la_frescura_no_aplica_mientras_el_corpus_este_congelado(contrato, columnas):
    """`frescura.no_aplica_mientras: corpus_congelado` (ADR 010). La cifra se
    calcula igual, porque la consola la necesita para escribir «no aplica», que es
    lo que pide `diseno.md` §7 · 3. Lo que no se hace es prender un semáforo."""
    df = marco(columnas, [fila(columnas, fecha_registro="2026/07/31")])
    r = lote.revisar_frescura(df, contrato, "2026-09-20", corpus_congelado=True)
    assert r["aplica"] is False
    assert "corpus_congelado" in r["razon"]
    assert r["estado"] == "BLOQUEA", "la cifra se sigue calculando"

    r2 = lote.revisar_frescura(df, contrato, "2026-09-20", corpus_congelado=False)
    assert r2["aplica"] is True and r2["razon"] is None


def test_la_fecha_de_referencia_es_parametro_y_no_hoy(contrato, columnas):
    """El contrato la pide como parámetro de la corrida y explica por qué: con el
    corpus congelado, `TODAY()` daría «bloquea» siempre y la compuerta nunca
    podría mostrar «ok»."""
    df = marco(columnas, [fila(columnas, fecha_registro="2026/07/31")])
    assert lote.revisar_frescura(df, contrato, "2026-08-10")["estado"] == "OK"
    assert lote.revisar_frescura(df, contrato, "2026-09-20")["estado"] == "BLOQUEA"


def test_un_lote_sin_filas_no_revienta_la_frescura(contrato, columnas):
    """Que no sobreviva ninguna fila es un resultado posible —la compuerta de fila
    apartó todo—, no un error."""
    r = lote.revisar_frescura(marco(columnas, []), contrato, "2026-08-10")
    assert r["aplica"] is False and r["dias"] is None


# ── Ninguna cifra escrita a mano ───────────────────────────────────────────

def test_ninguna_cifra_del_contrato_esta_escrita_en_el_codigo():
    """Las mismas cifras que la compuerta de fila se niega a escribir: el umbral de
    la colisión, los días de la frescura y el 5% de D-07."""
    # Sin comentarios ni textos: ver tests/codigo.py y por qué importa.
    cuerpo = codigo_sin_comentarios(lote.__file__)
    contrato = leer_contrato()
    prohibidas = {
        "el umbral de la colisión":
            contrato["clave_de_fila"]["colision_precio_alta"]["mas_de"],
        "los días del aviso de frescura": contrato["frescura"]["avisa_dias"],
        "los días del bloqueo de frescura": contrato["frescura"]["bloquea_dias"],
    }
    for que, valor in prohibidas.items():
        assert str(valor) not in cuerpo, (
            f"{que} ({valor}) aparece escrito en lote.py; se lee del contrato")


def test_la_cifra_que_el_contrato_tiene_en_prosa_se_reporta_no_se_adivina(contrato):
    """El `$1` que distingue una captura doble de una observación múltiple vive en
    un comentario de `clave_de_fila.desempate`. Un comentario desaparece al
    interpretar el YAML, así que no se puede obedecer: se reporta."""
    faltan = lote.cifras_que_el_contrato_no_declara(contrato)
    assert "umbral_de_captura_doble" in faltan
    assert "umbral_de_captura_doble" in lote.CIFRAS_EN_PROSA


def test_la_captura_doble_no_se_deduplica_y_se_dice(contrato, columnas):
    """Mientras el umbral no esté como dato, las dos filas de una captura doble
    pasan. Es una desviación del contrato y está declarada, no escondida."""
    df = marco(columnas, [
        fila(columnas, producto="Frijol", precio="30.00"),
        fila(columnas, producto="Frijol", precio="30.50"),
    ])
    limpias, _, resumen = lote.revisar_grupos(df, contrato)
    assert len(limpias) == 2
    assert "umbral_de_captura_doble" in resumen["cifras_en_prosa_no_aplicadas"]


def test_los_motivos_de_grupo_apuntan_a_una_regla_del_contrato(contrato):
    for motivo, ruta in lote.MOTIVOS_DE_GRUPO.items():
        nodo = contrato
        for paso in ruta.split("."):
            assert paso in nodo, (
                f"el motivo {motivo} dice venir de `{ruta}` y el contrato no la trae")
            nodo = nodo[paso]
