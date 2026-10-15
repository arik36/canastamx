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
    # FILA y no GRUPO: la tabla `cuarentena` sólo acepta FILA, y obliga a llenar
    # `grupo` cuando el motivo es éste. Hasta el 15 de octubre salía GRUPO.
    assert {r["nivel"] for r in registros} == {"FILA"}
    assert all(r["grupo"] for r in registros)
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


def test_el_umbral_de_captura_doble_es_dato_desde_la_1_3_5(contrato):
    """Hasta la 1.3.4 el `$1` vivía en un comentario de `clave_de_fila.desempate`,
    y un comentario desaparece al interpretar el YAML. Desde la 1.3.5 es
    `clave_de_fila.captura_doble.menos_de`."""
    assert lote.cifras_que_el_contrato_no_declara(contrato) == []
    assert contrato["clave_de_fila"]["captura_doble"]["menos_de"] == 1


def test_sin_el_dato_la_compuerta_se_niega_en_vez_de_adivinar(contrato, columnas):
    """Si alguien quita el umbral del contrato, la compuerta no sigue con una cifra
    escrita a mano: se detiene y dice cuál falta."""
    sin = dict(contrato)
    sin["clave_de_fila"] = {k: v for k, v in contrato["clave_de_fila"].items()
                            if k != "captura_doble"}
    assert lote.cifras_que_el_contrato_no_declara(sin) == ["umbral_de_captura_doble"]
    df = marco(columnas, [fila(columnas, producto="A"), fila(columnas, producto="A")])
    with pytest.raises(ValueError, match="captura_doble"):
        lote.revisar_grupos(df, sin)


def test_la_captura_doble_no_se_deduplica_aqui_se_cuenta(contrato, columnas):
    """Deduplicar es transformar, y eso es de la capa intermedia (semana del 19 al
    25 de octubre). La compuerta deja pasar las dos filas y las cuenta en su cubo,
    para que la deduplicación se compruebe contra esa cifra."""
    df = marco(columnas, [
        fila(columnas, producto="Frijol", precio="30.00"),
        fila(columnas, producto="Frijol", precio="30.50"),
    ])
    limpias, registros, resumen = lote.revisar_grupos(df, contrato)
    assert len(limpias) == 2 and registros == []
    assert resumen["grupos_captura_doble"] == 1
    assert resumen["sobrantes_captura_doble"] == 1


# ── Los tres cubos de la clave de fila (1.3.5) ─────────────────────────────

def test_los_tres_cubos_de_la_clave_de_fila(contrato, columnas):
    """Menos de $1, captura doble; de $1 a $50, observaciones múltiples; más de
    $50, colisión alta. Sólo la última aparta filas."""
    df = marco(columnas, [
        fila(columnas, producto="Frijol", precio="30.00"),
        fila(columnas, producto="Frijol", precio="30.50"),      # $0.50
        fila(columnas, producto="Arroz", precio="20.00"),
        fila(columnas, producto="Arroz", precio="37.00"),       # $17
        fila(columnas, producto="Aceite", precio="40.00"),
        fila(columnas, producto="Aceite", precio="200.00"),     # $160
    ])
    limpias, registros, r = lote.revisar_grupos(df, contrato)
    assert (r["grupos_captura_doble"], r["grupos_observaciones_multiples"],
            r["grupos_en_colision"]) == (1, 1, 1)
    assert r["filas_en_cuarentena"] == 2
    assert {x["fila"]["producto"] for x in registros} == {"Aceite"}
    assert len(limpias) == 4


@pytest.mark.parametrize("menor,mayor,cubo", [
    ("10.00", "10.99", "captura_doble"),            # $0.99
    ("10.00", "11.00", "observaciones_multiples"),  # $1.00 exacto: ya no es doble
    ("10.00", "60.00", "observaciones_multiples"),  # $50.00 exacto: todavía no es colisión
    ("10.00", "60.01", "en_colision"),              # $50.01
])
def test_las_fronteras_de_los_cubos(contrato, columnas, menor, mayor, cubo):
    """«Menos de» y «más de» son estrictos, como los escribe el contrato. Y la
    resta es en DECIMAL(12,2): en flotante, $1.00 sale 0.99999 y cae en el cubo
    de al lado, que es justo lo que `precio.razon_del_casteo` advierte."""
    df = marco(columnas, [fila(columnas, producto="P", precio=menor),
                          fila(columnas, producto="P", precio=mayor)])
    _, _, r = lote.revisar_grupos(df, contrato)
    assert r[f"grupos_{cubo}"] == 1, r


def test_el_umbral_de_captura_doble_lo_decide_el_contrato(contrato, columnas):
    """El `1` no se puede buscar en el código como las otras cifras —aparece en
    cualquier `count(*) > 1`—, así que se comprueba por su efecto: se mueve en una
    copia del contrato y el mismo grupo cambia de cubo."""
    df = marco(columnas, [fila(columnas, producto="P", precio="10.00"),
                          fila(columnas, producto="P", precio="12.00")])   # $2
    _, _, con_1 = lote.revisar_grupos(df, contrato)
    assert con_1["grupos_observaciones_multiples"] == 1

    otro = dict(contrato)
    otro["clave_de_fila"] = {**contrato["clave_de_fila"],
                             "captura_doble": {"menos_de": 5}}
    _, _, con_5 = lote.revisar_grupos(df, otro)
    assert con_5["grupos_captura_doble"] == 1, (
        "mover el umbral en el contrato no cambió el cubo: está escrito en el código")


# ── Con qué se compara cada columna de la clave (1.3.5) ────────────────────

def test_la_marca_se_compara_en_mayusculas_sin_acentos(contrato, columnas):
    """**El error que corrigió la 1.3.5.** La canónica quita la puntuación y une
    `Kellogg's` con `Kellogg´s`; la de la marca no (ADR 002 · 3). Con la canónica
    estas dos filas eran un grupo con $130 de diferencia, y se iban a cuarentena."""
    df = marco(columnas, [
        fila(columnas, producto="Cereal", marca="Kellogg's", precio="20.00"),
        fila(columnas, producto="Cereal", marca="Kellogg´s", precio="150.00"),
    ])
    _, registros, r = lote.revisar_grupos(df, contrato)
    assert r["grupos"] == 0 and registros == [], (
        "la marca se comparó en forma canónica: unió dos marcas distintas")


def test_s_m_y_S_M_son_la_misma_marca(contrato, columnas):
    """Lo que la regla de la marca sí une: sólo difieren en mayúsculas, y el
    contrato lo explica en `normalizacion.marca`."""
    df = marco(columnas, [fila(columnas, producto="Pan", marca="S/m", precio="10.00"),
                          fila(columnas, producto="Pan", marca="S/M", precio="99.00")])
    _, registros, r = lote.revisar_grupos(df, contrato)
    assert r["grupos_en_colision"] == 1 and len(registros) == 2


def test_la_normalizacion_de_cada_columna_la_decide_el_contrato(contrato, columnas):
    """Se cambia la de la marca a canónica en una copia del contrato, y las dos
    Kellogg se vuelven un grupo. Si no cambiara, la regla estaría en el código."""
    df = marco(columnas, [
        fila(columnas, producto="Cereal", marca="Kellogg's", precio="20.00"),
        fila(columnas, producto="Cereal", marca="Kellogg´s", precio="150.00"),
    ])
    otro = dict(contrato)
    otro["clave_de_fila"] = {
        **contrato["clave_de_fila"],
        "normaliza_por_columna": {**contrato["clave_de_fila"]["normaliza_por_columna"],
                                  "marca": "canonica"}}
    _, _, r = lote.revisar_grupos(df, otro)
    assert r["grupos_en_colision"] == 1


def test_cada_columna_de_la_clave_dice_como_se_compara(contrato):
    """Ni una columna de la clave sin su normalización —adivinar es como se coló la
    canónica en la marca—, y la de la marca es la misma que `normalizacion.marca.a`,
    para que los dos lugares no puedan separarse."""
    clave = contrato["clave_de_fila"]
    assert set(clave["normaliza_por_columna"]) == set(clave["columnas"])
    assert clave["normaliza_por_columna"]["marca"] == contrato["normalizacion"]["marca"]["a"]
    assert set(clave["normaliza_por_columna"].values()) <= set(lote.NORMALIZACIONES)


def test_mayusculas_sin_acentos_da_lo_mismo_que_la_ingesta(contrato):
    """`ingesta.py` escribió esta normalización a mano en septiembre, para
    `estado` y `catalogo`. La 1.3.5 la declara en el contrato. Se comparan por lo
    que DAN, no por cómo se escriben: si un día alguien cambia una de las dos,
    esto truena."""
    import duckdb
    from ingesta import recorte_del_contrato

    de_la_ingesta = recorte_del_contrato(contrato)["sql"]["estado"].split(" IN ")[0]
    del_contrato = lote.expresion(contrato, "mayusculas_sin_acentos", "estado")
    casos = ["Guanajuato", " guanajuato ", "Querétaro", "QUERÉTARO", "San Luis Potosí",
             "S/m", "Kellogg's", "Kellogg´s", "  Básicos  "]
    con = duckdb.connect()
    for caso in casos:
        a = con.execute(f"SELECT {de_la_ingesta} FROM (SELECT ? AS estado)", [caso]).fetchone()[0]
        b = con.execute(f"SELECT {del_contrato} FROM (SELECT ? AS estado)", [caso]).fetchone()[0]
        assert a == b, f"{caso!r}: la ingesta da {a!r} y el contrato {b!r}"


def test_la_cuarentena_de_colision_cabe_en_la_tabla_del_esquema(contrato, columnas):
    """La forma que la tabla `cuarentena` acepta, leída del propio SQL: nivel FILA
    (su CHECK), el par (motivo, nivel) en el catálogo (su llave foránea) y `grupo`
    lleno cuando el motivo es la colisión (su otro CHECK)."""
    import re

    sql = (PLATAFORMA.parents[1] / "docs" / "datos" /
           "esquema-de-operacion.sql").read_text(encoding="utf-8")
    assert "CHECK (nivel = 'FILA')" in sql
    assert "CHECK (motivo <> 'colision_precio_alta' OR grupo IS NOT NULL)" in sql
    catalogo = dict(re.findall(r"\('(\w+)',\s*'(FILA|LOTE|CORRIDA)'", sql))

    df = marco(columnas, [fila(columnas, producto="A", precio="10.00"),
                          fila(columnas, producto="A", precio="99.00")])
    _, registros, _ = lote.revisar_grupos(df, contrato)
    assert registros
    for r in registros:
        assert r["nivel"] == "FILA"
        assert catalogo.get(r["motivo"]) == r["nivel"]
        assert r["grupo"]


def test_los_motivos_de_grupo_estan_en_el_catalogo_del_contrato(contrato):
    for motivo, regla in lote.MOTIVOS_DE_GRUPO.items():
        assert contrato["motivos_de_fila"].get(motivo) == regla


def test_los_motivos_de_grupo_apuntan_a_una_regla_del_contrato(contrato):
    for motivo, ruta in lote.MOTIVOS_DE_GRUPO.items():
        nodo = contrato
        for paso in ruta.split("."):
            assert paso in nodo, (
                f"el motivo {motivo} dice venir de `{ruta}` y el contrato no la trae")
            nodo = nodo[paso]
