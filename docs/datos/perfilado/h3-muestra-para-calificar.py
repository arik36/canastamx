"""
H3 · la muestra de 200 pares que el protocolo pide de verdad · QQP

Por qué hace falta OTRO guión de H3
----------------------------------
`h3-entre-cadenas.py` contestó la primera pregunta —¿existen pares?— y dijo
**1,712,984**, contra los 200 que H3 pide. Pero ese número engaña por dos
razones, y las dos importan.

**Primera: está inflado por las cadenas.** Aquel guión multiplica cada par de
escrituras por cada par de cadenas donde aparecen. El mismo `S/m` contra `S/M`
de la tortilla, presente en 73 cadenas, cuenta 2,628 veces. **Las formas
distintas de escribir son 1,730**, no 1.7 millones. Sigue siendo más que 200,
pero es otra escala.

**Segunda, y es la de fondo: ninguno de esos 1,730 es difícil.** Los pares se
arman uniendo literales que comparten la misma **clave normalizada**, y la
normalización es justamente lo que quita mayúsculas, acentos y puntuación.
Entonces dos literales que comparten clave sólo pueden diferir en eso. Medido:

    sólo marca           1,098 pares   (1,040 son puro cambio de mayúscula)
    sólo presentacion      531
    más de una columna      96
    sólo producto            5

Y tras aplicar la normalización de `marca` que decidió el ADR 002, **sobreviven
687**: el contrato borra los de `S/m` antes de que la reconciliación los vea.

Eso deja a H3 en una posición incómoda: mediría una normalización determinista
usando exclusivamente los casos que una normalización determinista resuelve al
100%. La cobertura saldría 100% y la precisión 100%, siempre, sin importar qué
tan buena o mala sea la normalización. **Una hipótesis que no puede fallar no
es una hipótesis.**

Y hay un tercer problema, del mismo origen: esos pares sólo contienen casos
donde la normalización **ya acertó**. Los casos donde **falla** —dos escrituras
del mismo artículo que caen en claves distintas— son invisibles ahí, porque si
cayeron en claves distintas, el join nunca las junta. Medir cobertura sobre
aciertos garantizados no mide nada.

Qué hace este guión
-------------------
1. **Clasifica los pares que ya existen**: ¿en qué columna está la diferencia?
   ¿y cuántos sobreviven después de la normalización de `marca` que decidió el
   ADR 002? (Adelanto: los de `S/m` desaparecen solos.)

2. **Arma la muestra que H3 necesita**: pares de artículos que la normalización
   **NO** unió —claves distintas—, dentro del mismo producto, que se parecen lo
   bastante como para que valga la pena que una persona decida si son el mismo
   artículo o no.

   Ésos son los casos difíciles. Son los únicos con los que se puede medir
   cobertura de verdad, porque son los únicos donde la normalización se puede
   equivocar.

Uso
---
    python docs/datos/perfilado/h3-muestra-para-calificar.py
    CANASTAMX_DATOS=/otra/ruta python docs/datos/perfilado/h3-muestra-para-calificar.py

Salidas
-------
    docs/datos/perfilado/salidas/h3-diferencias-por-columna.csv
    docs/datos/perfilado/salidas/h3-muestra-para-calificar.csv
    docs/datos/perfilado/h3-muestra-para-calificar.txt   ← se marca a mano
"""
import os
from pathlib import Path

import duckdb

RAIZ = Path(os.environ.get("CANASTAMX_DATOS", Path.home() / "canastamx-datos"))
PARQUETS = RAIZ / "procesado" / "por_archivo"
SALIDA = Path("docs/datos/perfilado/salidas")
PARA_MARCAR = Path("docs/datos/perfilado")

# Los que pide el protocolo: «muestra aleatoria de 200 pares».
PARES_QUE_PIDE_H3 = 200

# Qué tan parecidos tienen que ser dos artículos para que valga la pena
# preguntarle a una persona. Por debajo de esto son obviamente distintos y
# preguntarlo sólo gasta el tiempo de quien califica.
PARECIDO_MINIMO = 0.82

# Los catálogos sobre los que se mide H3. Vacío = todos.
#
# Conviene llenarlo con lo que decida el ADR 005, porque el problema de
# reconciliación NO se parece entre catálogos: en `Electrodomesticos` la
# diferencia entre dos artículos es un carácter del número de modelo
# —`Gt 32 Bdc` contra `Gt 32 Wdc`—, mientras que en `Basicos` es cómo se
# escribe una cantidad —`1 L` contra `1 Lt`—. Medir H3 sobre refrigeradores
# que el producto no va a vender infla o desinfla el resultado sin que
# corresponda a nada.
CATALOGOS = ["Basicos", "Pacic", "Frutas y Legumbres", "Mercados", "Pescados y Mariscos"]

# Cuántos pares de un mismo producto pueden entrar a la mitad «más parecidos».
# Sin esto, cinco playeras de la misma marca que sólo cambian de talla se
# comen la muestra y quedan fuera patrones que aparecen una sola vez.
MAX_POR_PRODUCTO = 3

# La misma normalización de perfilado_nivel3.py y h3-entre-cadenas.py.
NORM = ("trim(regexp_replace(regexp_replace(lower(strip_accents({0})), "
        "'[^a-z0-9 ]', ' ', 'g'), '\\s+', ' ', 'g'))")


def conectar():
    con = duckdb.connect()
    con.sql("SET memory_limit='4GB'")
    tmp = RAIZ / "tmp-duckdb"
    tmp.mkdir(parents=True, exist_ok=True)
    con.sql(f"SET temp_directory='{tmp}'")
    fuente = f"read_parquet('{PARQUETS}/*.parquet', union_by_name=true)"
    # Se comparan sin acentos ni mayúsculas: la fuente escribe cuatro catálogos
    # de dos maneras (`Basicos`/`Básicos`, `Pacic`/`PACIC`, …).
    filtro_catalogo = ""
    if CATALOGOS:
        lista = ", ".join("'" + c.upper() + "'" for c in
                          [__import__("unicodedata").normalize("NFKD", c)
                           .encode("ascii", "ignore").decode() for c in CATALOGOS])
        filtro_catalogo = f"AND upper(strip_accents(trim(catalogo))) IN ({lista})"
    con.sql(f"""
        CREATE VIEW q AS
        SELECT producto, presentacion, marca, cadena_comercial, catalogo,
               {NORM.format('producto')}     AS prod_n,
               {NORM.format('presentacion')} AS pres_n,
               {NORM.format('marca')}        AS marca_n
        FROM {fuente}
        WHERE producto     NOT LIKE '%?%'
          AND presentacion NOT LIKE '%?%'
          AND marca        NOT LIKE '%?%'
          {filtro_catalogo}
    """)
    # Una fila por (clave normalizada, escritura literal), con las cadenas
    # donde aparece. Son unos miles de filas: todo lo demás sale de aquí.
    con.sql("""
        CREATE TABLE art AS
        SELECT prod_n, pres_n, marca_n,
               prod_n || '§' || pres_n || '§' || marca_n          AS clave,
               producto || ' · ' || presentacion || ' · ' || marca AS literal,
               producto, presentacion, marca,
               -- Los NÚMEROS aparte de las LETRAS. Ver `candidatos_para_calificar`:
               -- en esta fuente los números son los que cambian el artículo.
               regexp_replace(prod_n || pres_n || marca_n, '[^0-9]', '', 'g') AS digitos,
               trim(regexp_replace(regexp_replace(
                    prod_n || ' ' || pres_n || ' ' || marca_n,
                    '[0-9]', ' ', 'g'), '\\s+', ' ', 'g'))         AS letras,
               count(*)                            AS filas,
               list(DISTINCT cadena_comercial)     AS cadenas
        FROM q
        GROUP BY ALL
    """)
    # UNA fila por clave normalizada, con una escritura representativa.
    #
    # Los candidatos se buscan aquí y no en `art` porque `art` tiene una fila
    # por cada FORMA DE ESCRIBIR: la misma diferencia de presentación aparecería
    # repetida una vez por cada variante de marca, y se comería la muestra con
    # duplicados disfrazados.
    #
    # Se agrupa por la clave que ya trae `art` —la normalización completa del
    # flujo— y no por una derivada aquí. La primera versión de este guión
    # reconstruía la clave con `upper(strip_accents(trim(marca)))`, que quita
    # acentos y mayúsculas pero NO la puntuación, y eso hacía que
    # `Kellogg's` y `Kellogg´s` parecieran artículos distintos: salían de
    # candidatos con parecido 1.000 cuando la normalización real ya los une en
    # `kellogg s`. Ofrecer como «casos difíciles» cosas que el sistema ya
    # resuelve es justo el error que este guión existe para no cometer.
    con.sql("""
        CREATE TABLE art_contrato AS
        SELECT prod_n, clave,
               arg_max(literal, filas)               AS literal,
               any_value(digitos)                    AS digitos,
               any_value(letras)                     AS letras,
               sum(filas)                            AS filas,
               list_distinct(flatten(list(cadenas))) AS cadenas
        FROM art
        GROUP BY prod_n, clave
    """)
    return con


def donde_esta_la_diferencia(con):
    """De los pares que YA existen, ¿en qué columna está la diferencia?

    La pregunta importa porque el ADR 002 decidió normalizar `marca` a un solo
    literal. Si la mayoría de los pares difieren sólo en `marca`, el contrato
    los va a borrar antes de que el subsistema de reconciliación los vea, y H3
    se quedaría midiendo sobre lo que sobra.
    """
    return con.sql("""
        WITH pares AS (
            SELECT a.producto <> b.producto         AS dif_prod,
                   a.presentacion <> b.presentacion AS dif_pres,
                   a.marca <> b.marca               AS dif_marca,
                   upper(trim(a.marca)) = upper(trim(b.marca)) AS marca_solo_mayusculas,
                   a.filas + b.filas                AS peso
            FROM art a JOIN art b
              ON a.clave = b.clave
             AND a.literal < b.literal
        )
        SELECT CASE
                 WHEN dif_prod AND NOT dif_pres AND NOT dif_marca THEN 'sólo producto'
                 WHEN dif_pres AND NOT dif_prod AND NOT dif_marca THEN 'sólo presentacion'
                 WHEN dif_marca AND NOT dif_prod AND NOT dif_pres THEN 'sólo marca'
                 ELSE 'más de una columna'
               END                                        AS donde,
               count(*)                                   AS pares,
               sum(peso)                                  AS filas_implicadas,
               count(*) FILTER (WHERE dif_marca AND marca_solo_mayusculas)
                                                          AS de_esos_marca_solo_mayusculas
        FROM pares
        GROUP BY 1
        ORDER BY pares DESC
    """).df()


def sobreviven_a_la_normalizacion_de_marca(con):
    """¿Cuántos pares quedan una vez que el contrato normaliza `marca`?

    El ADR 002 decidió que `S/m` y `S/M` colapsan a un solo literal. Aquí se
    simula esa regla sobre TODA la columna `marca` —no sólo sobre `S/m`— y se
    cuenta qué queda. Lo que quede es el material real de H3.
    """
    return con.sql("""
        WITH pares AS (
            SELECT a.literal AS la, b.literal AS lb,
                   a.producto || '·' || a.presentacion || '·' || upper(strip_accents(trim(a.marca))) AS na,
                   b.producto || '·' || b.presentacion || '·' || upper(strip_accents(trim(b.marca))) AS nb
            FROM art a JOIN art b
              ON a.clave = b.clave
             AND a.literal < b.literal
        )
        SELECT count(*)                          AS pares_hoy,
               count(*) FILTER (WHERE na <> nb)  AS pares_despues_de_normalizar_marca
        FROM pares
    """).fetchone()


def candidatos_para_calificar(con, exigir_mismos_digitos=True):
    """Los casos difíciles: artículos que la normalización NO unió.

    Se buscan dentro del mismo `producto` normalizado, porque dos artículos de
    productos distintos no se confunden nunca y preguntarlo no aporta.

    Se exige que el par cubra dos cadenas o más, porque H3 es «entre cadenas».

    **Y se exige que los NÚMEROS coincidan.** Ésta es la parte que la primera
    versión de este guión no tenía, y por eso producía una muestra inservible.
    El parecido de Jaro-Winkler cuenta caracteres, no significado, así que
    estos dos salían con 0.985 de parecido:

        Bencilpenicilina ... Inyectable 400 000 Ui
        Bencilpenicilina ... Inyectable 800 000 Ui

    Cambia un dígito de 60 caracteres, así que «se parecen mucho». Pero son
    dosis distintas: **no son el mismo artículo y nunca lo van a ser.** Lo
    mismo con `Paquete 25 Piezas` contra `Paquete 5 Piezas`.

    En esta fuente **el número es el que define el artículo**: la dosis, el
    gramaje, el litraje, el conteo de piezas, el modelo. Las letras son las que
    se escriben de maneras distintas. Entonces la regla es:

        mismos números + letras distintas  →  candidato de verdad
        números distintos                  →  artículos distintos, no preguntar

    Con eso, `1 L` contra `1 Lt` sí entra (mismo número, letra de más), y
    `400 000 Ui` contra `800 000 Ui` no.

    El parecido se calcula sólo sobre las LETRAS, por la misma razón: si se
    calculara sobre la cadena completa, los números —que ya sabemos que son
    iguales— inflarían el parecido de todos los pares por igual.
    """
    filtro_digitos = "AND a.digitos = b.digitos" if exigir_mismos_digitos else ""
    return con.sql(f"""
        WITH c AS (
            SELECT a.prod_n,
                   a.literal AS literal_a, a.filas AS filas_a, a.cadenas AS cadenas_a,
                   b.literal AS literal_b, b.filas AS filas_b, b.cadenas AS cadenas_b,
                   replace(a.clave, '§', ' · ') AS clave_a,
                   replace(b.clave, '§', ' · ') AS clave_b,
                   jaro_winkler_similarity(a.letras, b.letras) AS parecido,
                   (a.digitos = b.digitos)                     AS mismos_digitos,
                   len(list_distinct(list_concat(a.cadenas, b.cadenas))) AS cadenas_del_par
            FROM art_contrato a JOIN art_contrato b
              ON a.prod_n = b.prod_n
             AND a.clave < b.clave          -- claves DISTINTAS, cada par una vez
             {filtro_digitos}
        )
        SELECT * FROM c
        WHERE parecido >= {PARECIDO_MINIMO}
          AND cadenas_del_par >= 2
        ORDER BY parecido DESC, filas_a + filas_b DESC
    """).df()


def escribir_para_marcar(muestra, destino):
    """El archivo que se marca a mano, con el mismo formato que ya conoces.

    OJO con la polaridad, que es AL REVÉS de `variantes-para-revisar.txt`:
    allá «sí» confirmaba que el script acertó al juntar. Aquí estos pares el
    script NO los juntó, así que un «sí» es un FALLO de la normalización.
    """
    lineas = [
        "MUESTRA PARA CALIFICAR H3 · pares que la normalización NO unió",
        "",
        "Cada par son dos artículos que quedaron en claves distintas, o sea que el",
        "sistema los trata hoy como dos cosas diferentes.",
        "",
        "  [x] sí  →  son el MISMO artículo. El sistema NO lo detectó.",
        "             Esto es un FALLO de cobertura y cuenta EN CONTRA.",
        "",
        "  [x] no  →  son artículos DISTINTOS. El sistema hizo bien en separarlos.",
        "             Esto cuenta A FAVOR.",
        "",
        "CUIDADO: la polaridad es al revés que en `variantes-para-revisar.txt`.",
        "Allá «sí» era bueno. Aquí «sí» significa que se nos escapó uno.",
        "",
        "Bajo cada par vienen las dos escrituras YA NORMALIZADAS. Compara ésas:",
        "en los literales de arriba puede haber diferencias que el sistema ya",
        "resuelve —un apóstrofo, una mayúscula— y que no son la que importa.",
        "",
        "Cobertura = (pares que son el mismo y el sistema SÍ unió)",
        "            ────────────────────────────────────────────",
        "            (todos los pares que son el mismo)",
        "",
        "Los «sí» de este archivo son el denominador que faltaba: los que son el",
        "mismo artículo y NO se unieron. Sin ellos la cobertura sale 100% siempre.",
        "",
        "=" * 70,
        "",
    ]
    for i, f in enumerate(muestra.itertuples(), 1):
        ca = ", ".join(list(f.cadenas_a)[:3])
        cb = ", ".join(list(f.cadenas_b)[:3])
        lineas += [
            f"par {i:03d} · parecido {f.parecido:.3f}",
            f"   A  {f.literal_a}",
            f"      {int(f.filas_a):>9,} filas · {ca}",
            f"   B  {f.literal_b}",
            f"      {int(f.filas_b):>9,} filas · {cb}",
            f"   ·  ya normalizados, la diferencia está aquí:",
            f"      A: {f.clave_a}",
            f"      B: {f.clave_b}",
            f"   ¿son el MISMO artículo?  [ ] sí   [ ] no",
            "",
        ]
    destino.write_text("\n".join(lineas), encoding="utf-8")


if __name__ == "__main__":
    if not any(PARQUETS.glob("*.parquet")):
        raise SystemExit(f"No hay parquets en {PARQUETS}. Corre antes perfilado_nivel2.py")
    con = conectar()
    SALIDA.mkdir(parents=True, exist_ok=True)

    print("=" * 78)
    print("H3 · por qué los 1.7 millones de pares no sirven para calificar")
    print("=" * 78)

    # ── 1 · dónde está la diferencia en los pares que ya existen
    d = donde_esta_la_diferencia(con)
    d.to_csv(SALIDA / "h3-diferencias-por-columna.csv", index=False)
    print("\n── En qué columna está la diferencia de cada par\n")
    print(d.to_string(index=False))
    print(f"\n   Total: {int(d.pares.sum()):,} pares DISTINTOS de escritura.")
    print("\n   Ojo con este número: `h3-entre-cadenas.py` reportó 1,712,984, y no")
    print("   se contradicen — cuentan cosas distintas. Aquél multiplica cada par")
    print("   de escrituras por cada par de cadenas donde aparecen: el mismo")
    print("   `S/m` contra `S/M` de la tortilla, presente en 73 cadenas, cuenta")
    print("   2,628 veces. Para calificar a mano, el número que importa es éste:")
    print("   las formas distintas de escribir, no en cuántas tiendas se repiten.")

    hoy, quedan = sobreviven_a_la_normalizacion_de_marca(con)
    print(f"\n── Qué pasa cuando el contrato normaliza `marca` (ADR 002)")
    print(f"   pares hoy                                  : {hoy:,}")
    print(f"   pares que sobreviven                       : {quedan:,} "
          f"({quedan/max(hoy,1):.1%})")
    print(f"   desaparecen                                : {hoy - quedan:,}")
    print("\n   Los que desaparecen no son un problema del guión: son pares que el")
    print("   contrato va a resolver ANTES de que la reconciliación los vea. Medir")
    print("   H3 sobre ellos sería calificar un examen cuyas respuestas ya vienen")
    print("   impresas en la hoja.")

    print("\n   Y aun los que sobreviven comparten clave normalizada, así que sólo")
    print("   difieren en mayúsculas, acentos o puntuación. Ninguno es difícil.")

    # ── 2 · la muestra de verdad
    print("\n" + "=" * 78)
    print(f"La muestra que H3 sí necesita · pares que la normalización NO unió")
    print("=" * 78)
    sin_filtro = candidatos_para_calificar(con, exigir_mismos_digitos=False)
    cand = candidatos_para_calificar(con, exigir_mismos_digitos=True)
    print(f"  Pares parecidos (≥ {PARECIDO_MINIMO}) en dos o más cadenas : {len(sin_filtro):,}")
    print(f"  De ésos, con los MISMOS números                : {len(cand):,}")
    print(f"  Descartados por tener números distintos        : "
          f"{len(sin_filtro) - len(cand):,}")
    print("\n  Los descartados no son candidatos: son artículos distintos. Un par")
    print("  como «400 000 Ui» contra «800 000 Ui» se parece en 60 de 61 caracteres,")
    print("  pero es otra dosis. En esta fuente el número define el artículo y las")
    print("  letras son las que se escriben de maneras distintas.")

    if len(cand) == 0:
        print("\n  No salió ninguno. Baja PARECIDO_MINIMO y vuelve a correr: si de")
        print("  verdad no hay casos dudosos, ése es el resultado y H3 se declara")
        print("  satisfecha con evidencia, no medida.")
        raise SystemExit(0)

    # Muestra estratificada: mitad de los más parecidos (donde estarían los
    # fallos de cobertura) y mitad al azar del resto (para que la precisión
    # también se pueda medir sobre casos que de verdad son distintos).
    mitad = PARES_QUE_PIDE_H3 // 2
    # De la mitad «más parecidos» se toma a lo más MAX_POR_PRODUCTO de cada
    # producto: si no, cinco playeras que sólo cambian de talla ocupan cinco
    # lugares y dejan fuera cinco patrones distintos.
    altos = (cand.groupby("prod_n", sort=False, group_keys=False)
                 .head(MAX_POR_PRODUCTO)
                 .head(mitad))
    resto = cand.drop(altos.index)
    azar = resto.sample(n=min(mitad, len(resto)), random_state=11) if len(resto) else resto
    import pandas as pd
    muestra = pd.concat([altos, azar]).reset_index(drop=True)

    muestra.to_csv(SALIDA / "h3-muestra-para-calificar.csv", index=False)
    destino = PARA_MARCAR / "h3-muestra-para-calificar.txt"
    escribir_para_marcar(muestra, destino)

    print(f"  Muestra escrita: {len(muestra)} pares")
    print(f"    · {len(altos)} de los más parecidos — ahí estarían los fallos de cobertura")
    print(f"    · {len(azar)} al azar del resto — para poder medir precisión también")
    print(f"\n  Para calificar a mano : {destino}")
    print(f"  Para procesar         : {SALIDA / 'h3-muestra-para-calificar.csv'}")

    print("\n  Los diez más parecidos, para ver de qué se trata:\n")
    for f in cand.head(10).itertuples():
        print(f"    {f.parecido:.3f}  {f.literal_a}")
        print(f"           {f.literal_b}")

    print("\n" + "=" * 78)
    print("Qué decide el ADR 004 con esto")
    print("=" * 78)
    print("  · Si al calificar la muestra salen MUCHOS «sí» (pares que son el mismo")
    print("    y no se unieron), H3 tiene material real y se mide como está escrita.")
    print("  · Si salen POCOS «sí», la normalización determinista ya cubre casi todo")
    print("    y H3 al 85% es una meta que no puede fallar. Ahí conviene reenunciarla")
    print("    sobre el eje que sí es difícil: reconciliar PRESENTACIONES dentro de")
    print("    un mismo producto —`Carne Res` tiene 57—, que ninguna normalización")
    print("    resuelve y que sí es investigación.")
    print("\n  En los dos casos el resultado llegó en septiembre, que es cuando")
    print("  todavía se puede cambiar la hipótesis sin costo.")
