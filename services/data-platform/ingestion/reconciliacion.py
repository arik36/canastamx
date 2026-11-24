"""CanastaMX · T053 (#206) · la reconciliación de productos, versión uno (CU-06).

QUÉ HACE
--------
Reescribe `articulo_canonico_key` en `dim_articulo`. Las presentaciones de un mismo
producto que son el mismo artículo escrito de otra forma —`Paquete 200 Gr. Letra` y
`Paquete 200 Gr. Letras`— quedan apuntando a una sola, y `estrella.agregados()`
calcula sobre ella: sus precios se vuelven una sola serie. Los hechos no se tocan;
cada observación conserva su `articulo_key` (CU-06, paso 4).

Las reglas no están aquí. Están en `contracts/reconciliacion-v1.yaml`, que el
contrato declara en `reconciliacion.reglas`, cada una con el par de la muestra que
la justifica.

CÓMO DECIDE
-----------
1. A cada presentación le saca su LLAVE (`llave()`). Sobre la forma canónica aplica
   las formas de P1 que se deciden palabra por palabra —separa números de letras,
   quita `c u` y el `no` de `no 2`, deja una sola forma por unidad, pasa a
   singular—, luego lo que `no_identifican` dice para SU producto, y al final quita
   conectores y preposiciones. La llave son los números, en su orden, y las
   palabras, ordenadas.
2. Dos presentaciones del mismo producto con la misma llave son el mismo artículo.
3. Lo que no unió la llave lo puede unir la comparación difusa: dos llaves con los
   mismos números y una sola palabra distinta se unen si esa palabra se parece a la
   otra al menos `difusa.umbral`, medido con `jaro_winkler_similarity` de DuckDB,
   la misma función con que se armó la muestra.
4. Los grupos son las componentes conexas de esas uniones, así que no dependen del
   orden en que se compara (RF-25). El canónico de cada grupo es el artículo con
   más hechos —la escritura más común— y el empate lo decide la presentación misma.

SI LAS REGLAS NO SE PUEDEN LEER (CU-06 · 1a)
-------------------------------------------
No se reconcilia nada: cada artículo queda como su propio canónico y la estrella se
carga igual. `resumen()` dice `no corrió` y por qué; `estrella.cargar()` lo
devuelve y el activo `capa_consumo` lo pone en su metadata con un aviso. Pasa lo
mismo si el umbral une alguno de `no_se_unen`: un umbral flojo es una regla rota,
no una regla.

LO QUE DEJA
-----------
En la conexión, dos tablas locales: `reconciliacion`, una fila por artículo con su
canónico, su llave y cómo llegó a su grupo, y `reconciliacion_estado`, si corrió y
con qué versión de las reglas. No van al destino: `dim_articulo` ya lleva el
canónico, y `h3.py` recalcula las llaves para explicar cada unión.

No importa Dagster (ADR 016).
"""

import dataclasses
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ingesta import CONTRATO

VOCALES = frozenset("aeiou")
# La forma canónica del contrato: minúsculas sin acentos, letras, números y un
# espacio entre palabras. Lo que la lista dice tiene que estar escrito así para
# poder compararse con `producto_c` y `presentacion_c`.
CANONICA = re.compile(r"[a-z0-9]+( [a-z0-9]+)*")
FRONTERA = re.compile(r"(?<=[0-9])(?=[a-z])|(?<=[a-z])(?=[0-9])")
METRICA = "jaro_winkler_similarity"
APLICADA, NO_CORRIO = "aplicada", "no corrió"


class ReglasIlegibles(ValueError):
    """Las reglas no se pueden leer o no se sostienen: no se reconcilia (CU-06 · 1a)."""


@dataclasses.dataclass(frozen=True)
class Frase:
    """Una entrada de `no_identifican`, ya en palabras normalizadas."""
    palabras: tuple
    por: tuple
    par: str
    clase: str


@dataclasses.dataclass(frozen=True)
class Reglas:
    version: str
    ruta: str
    separar: bool
    secuencias: tuple
    antes_de_numero: frozenset
    unidad: dict
    plural: bool
    conectores: frozenset
    preposiciones: frozenset
    nunca: frozenset
    umbral: float
    minimo_de_letras: int
    no_se_unen: tuple
    lista: dict = dataclasses.field(default_factory=dict)      # producto_c → (Frase, …)
    sin_clasificar: tuple = ()      # ((producto_c, palabra, par, por qué), …)


# ── Leer las reglas ─────────────────────────────────────────────────────────

def ruta_de(contrato):
    """Dónde están las reglas, según `reconciliacion.reglas` del contrato."""
    relativa = (contrato.get("reconciliacion") or {}).get("reglas")
    if not relativa:
        raise ReglasIlegibles("el contrato no declara `reconciliacion.reglas`")
    return CONTRATO.parent.parent / relativa


def leer_reglas(contrato=None, ruta=None):
    """Las reglas de `contracts/reconciliacion-v1.yaml`, comprobadas al leerlas.

    Se comprueba lo que el archivo afirma de sí mismo, porque una lista que no
    cumple su propia definición une mal sin dar ningún error: todo está en forma
    canónica, cada entrada es de una clase de P3 que dice «sí» y cita su par, ninguna
    quita un número ni la palabra `sin`, y nada de `sin_clasificar` está también en
    la lista."""
    import yaml

    if ruta is None:
        if contrato is None:
            from ingesta import leer_contrato
            contrato = leer_contrato()
        ruta = ruta_de(contrato)
    ruta = Path(ruta)
    try:
        crudo = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as e:
        raise ReglasIlegibles(f"no se pudieron leer las reglas de {ruta}: {e}") from None
    try:
        return _reglas(crudo, ruta)
    except ReglasIlegibles:
        raise
    except (KeyError, TypeError, ValueError, AttributeError) as e:
        raise ReglasIlegibles(f"{ruta.name} no tiene la forma que se espera: {e!r}") from None


def _canonico(valor, que):
    if not isinstance(valor, str) or not CANONICA.fullmatch(valor):
        raise ReglasIlegibles(f"{que} tiene que estar en forma canónica (minúsculas, sin "
                              f"acentos ni puntuación, un espacio entre palabras): {valor!r}")
    return valor


def _conjunto(valores, que):
    return frozenset(_canonico(v, que) for v in valores)


def _reglas(c, ruta):
    if not isinstance(c, dict) or c.get("contrato") != "reconciliacion":
        raise ReglasIlegibles(f"{ruta.name} no es el archivo de reglas de la reconciliación")
    f = c["formas_ortograficas"]
    if f.get("orden") != "palabras":
        raise ReglasIlegibles("`formas_ortograficas.orden` sólo puede ser `palabras`: los "
                              "números conservan su orden (ADR 004 §1)")
    unidad = {}
    for forma_canonica, formas in f["unidades"].items():
        for forma in formas:
            _canonico(forma, "una unidad")
            if unidad.setdefault(forma, forma_canonica) != forma_canonica:
                raise ReglasIlegibles(f"`{forma}` está en dos unidades")
    nunca = _conjunto(f["nunca_se_quitan"], "`nunca_se_quitan`")
    conectores = _conjunto(f["conectores"], "un conector")
    preposiciones = _conjunto(f["preposiciones"], "una preposición")
    if nunca & (conectores | preposiciones):
        raise ReglasIlegibles(f"{sorted(nunca & (conectores | preposiciones))} está en "
                              "`nunca_se_quitan` y también se quita")
    d = c["difusa"]
    if d.get("metrica") != METRICA:
        raise ReglasIlegibles(f"la comparación difusa sólo sabe medir con {METRICA}")
    umbral, minimo = float(d["umbral"]), int(d["minimo_de_letras"])
    if not 0 < umbral <= 1 or minimo < 1:
        raise ReglasIlegibles(f"umbral {umbral} o mínimo de letras {minimo} fuera de rango")
    reglas = Reglas(
        version=str(c["version"]), ruta=str(ruta),
        separar=bool(f["separar_numeros_de_letras"]),
        secuencias=tuple(tuple(_canonico(p, "una secuencia") for p in s)
                         for s in f["quitar_secuencias"]),
        antes_de_numero=_conjunto(f["quitar_antes_de_un_numero"], "`quitar_antes_de_un_numero`"),
        unidad=unidad, plural=bool(f["plural"]), conectores=conectores,
        preposiciones=preposiciones, nunca=nunca, umbral=umbral, minimo_de_letras=minimo,
        no_se_unen=tuple(tuple(_canonico(p, "`no_se_unen`") for p in par)
                         for par in c["no_se_unen"]))

    # La lista se normaliza con las mismas formas que las presentaciones: así
    # `rosas` en una presentación es `rosa` en la lista.
    clases = set(c["clases_que_no_identifican"])
    lista = {}
    for producto, entradas in (c.get("no_identifican") or {}).items():
        _canonico(producto, "un producto de `no_identifican`")
        frases = []
        for e in entradas:
            que = f"la entrada de `{producto}` del par {e.get('par')}"
            if e.get("clase") not in clases:
                raise ReglasIlegibles(f"{que} es de la clase {e.get('clase')!r}, que no está en "
                                      "`clases_que_no_identifican`: sólo entra lo clasificado")
            if not str(e.get("par") or "").strip() or not str(e.get("clasifico") or "").strip():
                raise ReglasIlegibles(f"{que} no dice su par o quién la clasificó")
            if ("quitar" in e) == ("cambiar" in e) or (("cambiar" in e) != ("por" in e)):
                raise ReglasIlegibles(f"{que} tiene que decir `quitar`, o `cambiar` y `por`")
            palabras = tuple(_por_palabra(_canonico(e.get("quitar") or e["cambiar"], que), reglas))
            por = tuple(_por_palabra(_canonico(e["por"], que), reglas)) if "por" in e else ()
            if [p for p in palabras if p.isdigit()] != [p for p in por if p.isdigit()]:
                raise ReglasIlegibles(f"{que} quita o cambia un número: el número define el "
                                      "artículo (ADR 004 §1)")
            if nunca & set(palabras):
                raise ReglasIlegibles(f"{que} quita {sorted(nunca & set(palabras))}, que "
                                      "nunca se quita")
            frases.append(Frase(palabras, por, str(e["par"]), e["clase"]))
        # La frase más larga primero, para que `congelado o descongelado` gane a
        # una entrada que quitara sólo `congelado`; el resto, por orden de texto.
        lista[producto] = tuple(sorted(frases, key=lambda x: (-len(x.palabras), x.palabras)))

    sin_clasificar = []
    for s in c.get("sin_clasificar") or ():
        producto = _canonico(s["producto"], "un producto de `sin_clasificar`")
        palabras = tuple(_por_palabra(_canonico(s["palabra"], "una palabra de `sin_clasificar`"),
                                      reglas))
        if any(fr.palabras == palabras for fr in lista.get(producto, ())):
            raise ReglasIlegibles(f"`{s['palabra']}` de `{producto}` está en `sin_clasificar` y "
                                  "también en `no_identifican`")
        sin_clasificar.append((producto, s["palabra"], str(s["par"]), " ".join(s["por_que"].split())))
    return dataclasses.replace(reglas, lista=lista, sin_clasificar=tuple(sin_clasificar))


# ── La llave de una presentación ───────────────────────────────────────────

def singular(palabra):
    """`letras` → `letra`, `limones` → `limon`, `nueces` → `nuez`, `dobles` → `doble`.

    Sin diccionario: cada palabra se decide sola, y la llave de un artículo no
    depende de qué otros artículos haya. Cuando se equivoca es casi siempre hacia
    separar —`chiles` queda en `chil` y no se une con `chile`—, que cuesta
    cobertura y no junta dos artículos distintos. Las de menos de cuatro letras no
    se tocan: `res`, `gas`, `dos`."""
    p = palabra
    if len(p) < 4 or not p.isalpha() or not p.endswith("s") or p[-2] not in VOCALES:
        return p
    if p.endswith("ces") and p[-4] in VOCALES:
        return p[:-3] + "z"
    if p.endswith("es") and p[-3] in "lnrdj" and p[-4] in VOCALES:
        return p[:-2]
    return p[:-1]


def _por_palabra(texto, reglas, pasos=None):
    """Las formas de P1 que se deciden palabra por palabra, en este orden: números y
    letras, abreviaturas, unidades y plural."""
    anotar = pasos.add if pasos is not None else (lambda _: None)
    if reglas.separar:
        for junto in texto.split():
            if FRONTERA.search(junto):
                anotar(("números y letras", junto))
        texto = FRONTERA.sub(" ", texto)
    ps, salida, i = texto.split(), [], 0
    while i < len(ps):
        secuencia = next((s for s in reglas.secuencias if tuple(ps[i:i + len(s)]) == s), None)
        if secuencia:
            anotar(("abreviatura", " ".join(secuencia)))
            i += len(secuencia)
            continue
        if ps[i] in reglas.antes_de_numero and i + 1 < len(ps) and ps[i + 1].isdigit():
            anotar(("abreviatura", ps[i]))
            i += 1
            continue
        p = ps[i]
        if p in reglas.unidad:
            if reglas.unidad[p] != p:
                anotar(("unidad", f"{p}→{reglas.unidad[p]}"))
            p = reglas.unidad[p]
        elif reglas.plural and singular(p) != p:
            anotar(("plural", f"{p}→{singular(p)}"))
            p = singular(p)
        salida.append(p)
        i += 1
    return salida


def palabras(producto_c, presentacion_c, reglas, pasos=None):
    """La presentación con las formas de P1, la lista de su producto y sin conectores
    ni preposiciones, todavía en su orden. `pasos`, un `set`, anota qué la cambió:
    (forma, qué palabra)."""
    anotar = pasos.add if pasos is not None else (lambda _: None)
    ps = _por_palabra(presentacion_c, reglas, pasos)
    salida, i = [], 0
    frases = reglas.lista.get(producto_c, ())
    while i < len(ps):
        f = next((f for f in frases if tuple(ps[i:i + len(f.palabras)]) == f.palabras), None)
        if f is None:
            salida.append(ps[i])
            i += 1
        else:
            anotar(("lista", f"{' '.join(f.palabras)} ({f.par})"))
            salida.extend(f.por)
            i += len(f.palabras)
    ultimo, quedan = len(salida) - 1, []
    for i, p in enumerate(salida):
        if p in reglas.nunca:
            quedan.append(p)
        elif p in reglas.preposiciones:
            anotar(("preposición", p))
        elif p in reglas.conectores and 0 < i < ultimo:
            anotar(("conector", p))
        else:
            quedan.append(p)
    return quedan


def llave(producto_c, presentacion_c, reglas, pasos=None):
    """(números en su orden, palabras ordenadas): dos presentaciones del mismo
    producto con la misma llave son el mismo artículo."""
    ps = palabras(producto_c, presentacion_c, reglas, pasos)
    return (tuple(p for p in ps if p.isdigit()), tuple(sorted(p for p in ps if not p.isdigit())))


def texto_de(llave_):
    numeros, palabras_ = llave_
    return f"{' '.join(numeros)} | {' '.join(palabras_)}"


# ── La comparación difusa ──────────────────────────────────────────────────

def una_palabra_distinta(a, b):
    """Si dos llaves tienen los mismos números y cambian en una sola palabra, esas
    dos palabras; si no, None."""
    (numeros_a, palabras_a), (numeros_b, palabras_b) = a, b
    if numeros_a != numeros_b or len(palabras_a) != len(palabras_b):
        return None
    resto, solo_a = list(palabras_b), []
    for p in palabras_a:
        if p in resto:
            resto.remove(p)
        else:
            solo_a.append(p)
    return (solo_a[0], resto[0]) if len(solo_a) == 1 and len(resto) == 1 else None


def parecido(con, a, b):
    return con.execute(f"SELECT {METRICA}(?, ?)", [a, b]).fetchone()[0]


def _la_difusa_une(con, reglas, a, b, cache=None):
    if not all(p.isalpha() and len(p) >= reglas.minimo_de_letras for p in (a, b)):
        return False
    clave = (a, b) if a <= b else (b, a)
    if cache is None or clave not in cache:
        valor = parecido(con, *clave)
        if cache is None:
            return valor >= reglas.umbral
        cache[clave] = valor
    return cache[clave] >= reglas.umbral


def comprobar(con, reglas):
    """Que ningún par de `no_se_unen` quede unido: ni con la misma llave en algún
    producto de la lista, ni por la difusa. Si uno se une, las reglas están rotas."""
    productos = ("",) + tuple(sorted(reglas.lista))
    for a, b in reglas.no_se_unen:
        for producto in productos:
            if llave(producto, a, reglas) == llave(producto, b, reglas):
                raise ReglasIlegibles(f"`{a}` y `{b}` quedan con la misma llave"
                                      + (f" en `{producto}`" if producto else ""))
        if _la_difusa_une(con, reglas, a, b):
            raise ReglasIlegibles(
                f"la comparación difusa une `{a}` con `{b}` ({parecido(con, a, b):.3f} contra "
                f"un umbral de {reglas.umbral}): el umbral está flojo (ADR 004)")


# ── Los grupos ─────────────────────────────────────────────────────────────

def _raiz(padre, x):
    """La raíz de `x` en el bosque de uniones, acortando el camino de paso."""
    while padre[x] != x:
        padre[x] = padre[padre[x]]
        x = padre[x]
    return x


def agrupar(articulos, reglas, con):
    """`articulos` son (articulo_key, producto_c, presentacion_c, hechos). Devuelve
    {articulo_key: (canónico, llave, cómo)}, donde cómo es `solo`, `canonico`,
    `llave` (comparte la llave del canónico) o `difusa`.

    `con` es cualquier conexión de DuckDB: sólo mide el parecido."""
    por_producto = {}
    for articulo, producto, presentacion, hechos in articulos:
        ll = llave(producto, presentacion, reglas)
        por_producto.setdefault(producto, {}).setdefault(ll, []).append(
            (articulo, presentacion, hechos))

    salida, cache = {}, {}
    for producto in sorted(por_producto):
        grupos = por_producto[producto]
        llaves = sorted(grupos)
        padre = {ll: ll for ll in llaves}
        for i, a in enumerate(llaves):
            for b in llaves[i + 1:]:
                distintas = una_palabra_distinta(a, b)
                if distintas and _la_difusa_une(con, reglas, *distintas, cache=cache):
                    ra, rb = _raiz(padre, a), _raiz(padre, b)
                    if ra != rb:
                        padre[max(ra, rb)] = min(ra, rb)

        componentes = {}
        for ll in llaves:
            componentes.setdefault(_raiz(padre, ll), []).append(ll)
        for del_grupo in componentes.values():
            miembros = [(articulo, presentacion, hechos, ll) for ll in del_grupo
                        for articulo, presentacion, hechos in grupos[ll]]
            # El de más hechos; el empate, por la presentación misma (RF-25).
            canonico = min(miembros, key=lambda m: (-m[2], m[1]))
            for articulo, _, _, ll in miembros:
                como = ("solo" if len(miembros) == 1 else "canonico" if articulo == canonico[0]
                        else "llave" if ll == canonico[3] else "difusa")
                salida[articulo] = (canonico[0], ll, como)
    return salida


def explicar(producto_c, presentacion_a, presentacion_b, reglas, con):
    """Por qué dos presentaciones quedan juntas o separadas, en una línea. Es para el
    informe de H3: no decide nada."""
    pa, pb = set(), set()
    la, lb = (llave(producto_c, presentacion_a, reglas, pa),
              llave(producto_c, presentacion_b, reglas, pb))
    if la == lb:
        # Lo que se le hizo a una sola de las dos, o de otra forma: `gr→g` contra
        # `ml→g` es la unidad que las une; `gr→g` en las dos no explica nada.
        por_forma = {}
        for forma, que in sorted(pa ^ pb):
            por_forma.setdefault(forma, []).append(que)
        pasos = [f"{forma} ({', '.join(ques)})" for forma, ques in por_forma.items()]
        orden = [p for p in palabras(producto_c, presentacion_a, reglas) if not p.isdigit()]
        otro = [p for p in palabras(producto_c, presentacion_b, reglas) if not p.isdigit()]
        if orden != otro:
            pasos.append("orden")
        return "misma llave · " + ("; ".join(pasos) if pasos else "escritas igual")
    distintas = una_palabra_distinta(la, lb)
    if distintas and all(p.isalpha() for p in distintas):
        a, b = distintas
        valor = parecido(con, a, b)
        if min(len(a), len(b)) < reglas.minimo_de_letras:
            return (f"difusa · {a} / {b} no se comparan: menos de {reglas.minimo_de_letras} "
                    f"letras ({valor:.3f})")
        return f"difusa · {a} / {b} {valor:.3f} {'≥' if valor >= reglas.umbral else '<'} {reglas.umbral}"
    return f"llaves distintas · {texto_de(la)}  ≠  {texto_de(lb)}"


# ── En la estrella ─────────────────────────────────────────────────────────

def _guardar(con, filas, estado, version, motivo):
    con.execute("""CREATE OR REPLACE TABLE reconciliacion (
        articulo_key INTEGER, articulo_canonico_key INTEGER, llave VARCHAR, como VARCHAR)""")
    if filas:
        con.executemany("INSERT INTO reconciliacion VALUES (?, ?, ?, ?)", filas)
    con.execute("CREATE OR REPLACE TABLE reconciliacion_estado "
                "(estado VARCHAR, version VARCHAR, motivo VARCHAR)")
    con.execute("INSERT INTO reconciliacion_estado VALUES (?, ?, ?)", [estado, version, motivo])


def aplicar(con, reglas):
    """Reescribe `articulo_canonico_key` en la tabla local `dim_articulo` de `con`.

    Lee `dim_articulo` y, para escoger el canónico, cuántos hechos tiene cada
    artículo en `hechos_precio`. No toca `hechos_precio`."""
    articulos = con.execute("""
        SELECT a.articulo_key, a.producto_c, a.presentacion_c, count(h.articulo_key)
        FROM dim_articulo a LEFT JOIN hechos_precio h USING (articulo_key)
        GROUP BY ALL ORDER BY a.articulo_key""").fetchall()
    grupos = agrupar(articulos, reglas, con)
    _guardar(con, [(k, canonico, texto_de(ll), como)
                   for k, (canonico, ll, como) in sorted(grupos.items())],
             APLICADA, reglas.version, None)
    con.execute("""UPDATE dim_articulo SET articulo_canonico_key = r.articulo_canonico_key
                   FROM reconciliacion r WHERE dim_articulo.articulo_key = r.articulo_key""")
    return resumen(con)


def sin_reconciliar(con, motivo):
    """CU-06 · 1a: cada artículo es su propio canónico, y queda dicho por qué."""
    con.execute("UPDATE dim_articulo SET articulo_canonico_key = articulo_key")
    filas = con.execute("SELECT articulo_key, articulo_key, NULL, 'solo' FROM dim_articulo "
                        "ORDER BY 1").fetchall()
    _guardar(con, filas, NO_CORRIO, None, motivo)
    return resumen(con)


def reconciliar(con, contrato, reglas=None):
    """CU-06 en la carga de la estrella. Lee las reglas que declara el contrato,
    salvo que se le pasen, y reconcilia; si no se puede, no reconcilia nada."""
    try:
        reglas = reglas or leer_reglas(contrato)
        comprobar(con, reglas)
    except ReglasIlegibles as e:
        return sin_reconciliar(con, str(e))
    return aplicar(con, reglas)


def resumen(con):
    """Cuántos artículos reconcilió y cuántos quedaron solos (CU-06, paso 5)."""
    estado, version, motivo = con.execute("SELECT * FROM reconciliacion_estado").fetchone()
    articulos, grupos, solos, variantes, por_llave, por_difusa = con.execute("""
        SELECT count(*),
               count(DISTINCT articulo_canonico_key) FILTER (WHERE como <> 'solo'),
               count(*) FILTER (WHERE como = 'solo'),
               count(*) FILTER (WHERE articulo_key <> articulo_canonico_key),
               count(*) FILTER (WHERE como = 'llave'),
               count(*) FILTER (WHERE como = 'difusa')
        FROM reconciliacion""").fetchone()
    r = {"estado": estado, "version": version, "articulos": articulos, "grupos": grupos,
         "reconciliados": articulos - solos, "solos": solos, "variantes": variantes,
         "por_llave": por_llave, "por_difusa": por_difusa}
    if motivo:
        r["motivo"] = motivo
    return r
