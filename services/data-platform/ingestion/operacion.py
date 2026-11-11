#!/usr/bin/env python3
"""CanastaMX · T064 · las compuertas dejan su rastro en el esquema de operación.

QUÉ ES
------
Lo que le pasa a cada lote, en las tablas de `docs/datos/esquema-de-operacion.md`.
Viven en `postgres-analytics`, esquema `operacion`, aparte de la capa de consumo
(P-08):

  · **`corrida`**, una fila por corrida: qué archivo, con qué contrato, cuántas
    filas leyó, aceptó y apartó, y el resultado.
  · **`paso`**, cada etapa por la que pasó, con sus filas de entrada y de salida y
    su hora. Lo que sale de un paso es lo que entra al siguiente.
  · **`cuarentena`**, cada fila apartada, con su motivo, su compuerta y la fila tal
    como llegó. Una fila apartada no llega a la capa intermedia, y por eso tampoco
    a `hechos_precio`.
  · **`incidente`**, el incidente abierto de un lote detenido (CU-04) y el aviso de
    las columnas que el contrato no declara (CU-02 · 2a).

Sólo la plataforma crea filas aquí (P-08). La interfaz analítica sólo cierra
incidentes y resuelve variantes.

EL ESQUEMA NO ESTÁ ESCRITO AQUÍ
-------------------------------
Es `docs/datos/esquema-de-operacion.sql`, que se puede aplicar las veces que sea.
Contra `postgres-analytics` se manda tal cual. DuckDB, el de la simulación, no
entiende siete cosas de PostgreSQL, y `A_DUCKDB` las traduce. Si el SQL cambia y
una de ellas ya no se encuentra, la traducción se detiene: así la simulación no
crea en silencio otras tablas que las de la base de verdad.

DÓNDE ESCRIBE
-------------
En la misma base que la capa intermedia (`intermedia.adjuntar_destino()`): con
`CANASTAMX_SIMULAR`, el DuckDB de la carpeta de corridas; sin simular,
`postgres-analytics`, con las `ANALYTICS_*` del `.env`. La contraseña nunca va en
una cadena de SQL. Lo de una corrida se escribe en una transacción: queda completo
o no queda nada.

No importa Dagster (ADR 016): si la orquestación se va, esto sigue corriendo.

USO
---
    # crear o poner al día el esquema, sin Dagster
    python services/data-platform/ingestion/operacion.py --aplicar
    # cuántas filas tiene cada tabla, los indicadores de la consola y si las cuentas
    # cuadran: la evidencia de #210
    python services/data-platform/ingestion/operacion.py --contar
    # lo mismo, contra el DuckDB de la simulación
    python services/data-platform/ingestion/operacion.py --contar --simular
"""

import datetime as dt
import json
import numbers
import re
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import compuerta
import intermedia
from ingesta import RAIZ, columnas_del_contrato, leer_contrato
from salida_segura import preparar_salida

ESQUEMA = "operacion"
SQL = RAIZ / "docs" / "datos" / "esquema-de-operacion.sql"
TABLAS = ("motivo", "corrida", "paso", "cuarentena", "incidente", "variante", "equivalencia")

# El paso que aplica el umbral de D-07 (`compuerta.decidir_promocion()`). Se llama
# como la sección del contrato que lo define.
PROMOCION = "promocion_del_lote"
# CU-02 · 2a: las columnas extra levantan «un aviso de tipo deriva_de_esquema».
DERIVA = "deriva_de_esquema"
# Qué compuerta detiene el lote con cada motivo de nivel LOTE que llega hasta aquí.
# Los de la ingesta (archivo ilegible, controles C1, `?` en un filtro, filas de otra
# quincena) no llegan: la capa cruda falla antes de que haya corrida.
QUIEN_DETIENE = {"rechazo_mayor_al_umbral": PROMOCION,
                 "columna_requerida_faltante": compuerta.NOMBRE_COMPUERTA}

# Lo que DuckDB no entiende del SQL de PostgreSQL. Cada una tiene que encontrarse.
A_DUCKDB = (
    # 1 y 2 · el esquema va en la base adjunta, no en la de la conexión.
    (r"^CREATE SCHEMA IF NOT EXISTS operacion;", "CREATE SCHEMA IF NOT EXISTS destino.operacion;"),
    (r"^SET search_path = operacion;", "USE destino.operacion;"),
    # 3 · no tiene columnas de identidad: una secuencia por tabla.
    (r"^CREATE TABLE IF NOT EXISTS (\w+) \((\s+)id(\s+)bigint GENERATED ALWAYS AS IDENTITY",
     (r"CREATE SEQUENCE IF NOT EXISTS \1_id;\n"
     r"CREATE TABLE IF NOT EXISTS \1 (\2id\3bigint DEFAULT nextval('\1_id')")),
    # 4 · calcula las columnas generadas al leerlas, no las guarda.
    (r"\) STORED,", ") VIRTUAL,"),
    # 5 · su JSON se llama JSON.
    (r"\bjsonb\b", "JSON"),
    # 6 · no borra en cascada. La simulación nunca borra una corrida.
    (r" ON DELETE CASCADE", ""),
    # 7 · los índices sobran, y estorban: con un índice sobre `iniciada_en`, DuckDB
    #     vuelve borrado e inserción la actualización de `terminada_en`, y sus llaves
    #     foráneas ya no dejan tocar una corrida que tiene pasos. Tampoco tiene
    #     índices parciales.
    (r"^CREATE INDEX IF NOT EXISTS [^;]*;\n?", ""),
)

# Las columnas que escribe la plataforma. Las demás tienen valor por omisión o son
# de la interfaz analítica (el cierre de un incidente).
COLUMNAS = {
    "corrida": ("lote", "archivo", "sha256_entrada", "version_contrato", "fecha_de_referencia",
                "iniciada_en", "terminada_en", "filas_del_archivo", "filas_leidas",
                "filas_aceptadas", "filas_en_cuarentena", "resultado", "frescura_estado",
                "frescura_dias", "detalle"),
    "paso": ("corrida_id", "orden", "capa", "nombre", "filas_entrada", "filas_salida",
             "filas_en_cuarentena", "iniciado_en", "terminado_en", "resultado"),
    "cuarentena": ("corrida_id", "motivo", "nivel", "compuerta", "huella_fila", "ocurrencia",
                   "grupo", "fila"),
    "incidente": ("severidad", "corrida_id", "compuerta", "motivo", "filas_afectadas", "estado"),
}
FILAS_POR_SENTENCIA = 500


def ahora():
    return dt.datetime.now(dt.UTC).isoformat()


# ── El esquema ──────────────────────────────────────────────────────────────

def ddl(motor):
    """El SQL del esquema, para PostgreSQL tal cual o traducido a DuckDB."""
    texto = SQL.read_text(encoding="utf-8")
    if motor == "postgres":
        # Dos corridas que empiezan a la vez aplican el esquema a la vez: el candado
        # las forma y dura lo que su transacción. El catálogo, además, sólo reescribe
        # un motivo si cambió. Sin eso, en REPEATABLE READ —el aislamiento con que
        # la extensión postgres de DuckDB abre sus transacciones— tres de seis
        # aplicaciones simultáneas fallaban con «could not serialize access».
        # `RESET` deja la conexión como estaba.
        return ("SELECT pg_advisory_xact_lock(hashtext('canastamx.operacion'));\n"
                + texto + "\nRESET search_path;\n")
    for patron, reemplazo in A_DUCKDB:
        texto, n = re.subn(patron, reemplazo, texto, flags=re.MULTILINE)
        if not n:
            raise RuntimeError(
                f"la traducción a DuckDB ya no encuentra «{patron}» en {SQL.name}: el SQL "
                "cambió, y la simulación crearía otras tablas que la base. Ajusta A_DUCKDB.")
    return texto


def aplicar(con, motor):
    """Crea o pone al día el esquema en `destino`. No borra nada."""
    if motor == "postgres":
        con.execute(f"CALL postgres_execute('destino', '{intermedia._texto_sql(ddl(motor))}')")
        # Lo creado con postgres_execute no está en la caché de DuckDB hasta limpiarla.
        con.execute("CALL pg_clear_cache()")
        return
    antes = con.execute("SELECT current_database()").fetchone()[0]
    try:
        con.execute(ddl(motor))
    finally:
        con.execute(f'USE "{antes}"')


def columnas_extra(contrato, columnas_del_archivo):
    """Las columnas del archivo que el contrato no declara (CU-02 · 2a)."""
    politica = contrato["columnas_extra"]["politica"]
    if politica != "no_ingerir_con_aviso":
        raise ValueError(f"`columnas_extra.politica` dice «{politica}»; esta compuerta "
                         "sólo sabe no ingerirlas y avisar")
    declaradas = set(columnas_del_contrato(contrato))
    return [c for c in columnas_del_archivo if c not in declaradas]


# ── Los pasos ───────────────────────────────────────────────────────────────

def paso(capa, nombre, ejecucion, iniciado_en, terminado_en,
         entrada=None, salida=None, en_cuarentena=0, resultado="PASO"):
    return {"capa": capa, "nombre": nombre, "ejecucion": ejecucion,
            "iniciado_en": iniciado_en, "terminado_en": terminado_en,
            "filas_entrada": entrada, "filas_salida": salida,
            "filas_en_cuarentena": en_cuarentena, "resultado": resultado}


def paso_de_compuerta(nombre, resumen, ejecucion, iniciado_en, terminado_en):
    """Una compuerta, con las cifras de su resumen: AVISO si apartó filas y siguió,
    DETENIDO si detuvo el lote."""
    apartadas = resumen.get("filas_en_cuarentena", 0)
    resultado = ("DETENIDO" if resumen.get("resultado") == "DETENIDO"
                 else "AVISO" if apartadas else "PASO")
    return paso("COMPUERTA", nombre, ejecucion, iniciado_en, terminado_en,
                entrada=resumen["filas_entrada"], salida=resumen.get("filas_salida", 0),
                en_cuarentena=apartadas, resultado=resultado)


def paso_de_promocion(resumen, entrada, ejecucion, iniciado_en, terminado_en):
    """El umbral de D-07: no aparta filas; deja salir todas o ninguna."""
    detenido = resumen["resultado"] == "DETENIDO"
    return paso("COMPUERTA", PROMOCION, ejecucion, iniciado_en, terminado_en,
                entrada=entrada, salida=resumen["filas_salida"],
                resultado="DETENIDO" if detenido else "PASO")


# ── La corrida de un lote ──────────────────────────────────────────────────

def _filas_del_archivo(registro_de_la_ingesta):
    recorte = (registro_de_la_ingesta or {}).get("recorte")
    return recorte.get("filas_del_archivo") if isinstance(recorte, dict) else None


def armar_corrida(contrato, lote, traza, resumen, fecha_de_referencia):
    """La fila de `corrida`, sus pasos y sus incidentes, desde lo que decidieron las
    compuertas. No escribe nada.

    `traza` es lo que viaja con el lote desde la capa cruda: el archivo y su sha256,
    el registro de la ingesta, las columnas del archivo, los pasos con su hora, la
    corrida de Dagster y el disparo del sensor. Entran los pasos de ESTA corrida:
    si alguien vuelve a materializar sólo la compuerta de lote, la capa cruda no
    corrió otra vez y no es un paso de la corrida nueva.
    """
    marca = traza.get("ejecucion") or str(uuid.uuid4())
    pasos = [p for p in traza.get("pasos", []) if p.get("ejecucion") == marca]
    terminada_en = ahora()
    # H2 cuenta desde el disparo del sensor (SLA-D-05). Si nadie la disparó, desde
    # el primer paso.
    iniciada_en = traza.get("disparo") or min(
        (p["iniciado_en"] for p in pasos), key=dt.datetime.fromisoformat, default=terminada_en)

    incidentes = []
    detenido = resumen.get("resultado") == "DETENIDO"
    if detenido:
        motivo = resumen["motivo_lote"]
        incidentes.append({
            "severidad": "INCIDENTE", "estado": "ABIERTO", "compuerta": QUIEN_DETIENE[motivo],
            "motivo": motivo,
            # Con el umbral, las que se apartaron; si al archivo le falta una columna,
            # el lote entero.
            "filas_afectadas": resumen.get("filas_en_cuarentena") or resumen["filas_entrada"]})
    extra = columnas_extra(contrato, traza.get("columnas_del_archivo") or [])
    if extra:
        incidentes.append({"severidad": "AVISO", "estado": "INFORMATIVO", "compuerta": DERIVA,
                           "motivo": "columnas_extra", "filas_afectadas": 0})

    # Filas en cuarentena por debajo del umbral no hacen una corrida «con avisos»: es
    # el flujo normal de CU-02 (3a, 4a y 5a siguen, y el paso 9 la muestra
    # correcta). Con avisos es la que levantó un aviso.
    if detenido:
        resultado = "RECHAZADA"
    elif any(i["severidad"] == "AVISO" for i in incidentes):
        resultado = "CON_AVISOS"
    else:
        resultado = "CORRECTA"

    frescura = resumen.get("frescura") or {}
    if frescura.get("estado") is None:
        frescura_estado = None          # no hubo fecha que medir
    else:
        frescura_estado = frescura["estado"] if frescura.get("aplica") else "NO_APLICA"

    corrida = {
        "lote": lote, "archivo": traza.get("archivo"),
        "sha256_entrada": traza.get("sha256_entrada"),
        "version_contrato": contrato["version"], "fecha_de_referencia": fecha_de_referencia,
        "iniciada_en": iniciada_en, "terminada_en": terminada_en,
        "filas_del_archivo": _filas_del_archivo(traza.get("ingesta")),
        # Leídas es el alcance, la población de D-07 y de la consola.
        "filas_leidas": resumen["filas_entrada"],
        "filas_aceptadas": 0 if detenido else resumen["filas_salida"],
        "filas_en_cuarentena": resumen.get("filas_en_cuarentena", 0),
        "resultado": resultado, "frescura_estado": frescura_estado,
        "frescura_dias": frescura.get("dias"),
        "detalle": {"ejecucion": marca, "disparo": traza.get("disparo"),
                    "columnas_extra": extra, "ingesta": traza.get("ingesta"),
                    "compuertas": resumen},
    }
    return corrida, pasos, incidentes


def registrar_lote(contrato, lote, traza, resumen, cuarentena, fecha_de_referencia,
                   simular=False, carpeta=None):
    """Arma la corrida del lote y la escribe con sus pasos, su cuarentena y sus
    incidentes. Devuelve su id."""
    corrida, pasos, incidentes = armar_corrida(contrato, lote, traza, resumen,
                                               fecha_de_referencia)
    return registrar_corrida(corrida, pasos, cuarentena, incidentes, contrato, simular, carpeta)


# ── La escritura ───────────────────────────────────────────────────────────

def _sql(valor):
    """Un valor como literal de SQL, que PostgreSQL y DuckDB leen igual."""
    if valor is None:
        return "NULL"
    if isinstance(valor, bool):
        return "true" if valor else "false"
    if isinstance(valor, numbers.Integral):
        return str(int(valor))
    if isinstance(valor, dict | list):
        valor = json.dumps(valor, ensure_ascii=False, default=str)
    return "'" + str(valor).replace("'", "''") + "'"


def _insertar(tabla, prefijo, filas):
    """INSERT de `filas` (listas de literales ya escritos), de 500 en 500."""
    columnas = ", ".join(COLUMNAS[tabla])
    for i in range(0, len(filas), FILAS_POR_SENTENCIA):
        valores = ",\n  ".join(f"({', '.join(f)})" for f in filas[i:i + FILAS_POR_SENTENCIA])
        yield f"INSERT INTO {prefijo}{tabla} ({columnas}) VALUES\n  {valores};"


def sentencias_de_la_corrida(motor, corrida, pasos, cuarentena, incidentes):
    """El SQL que escribe una corrida completa. La corrida se inserta primero, y lo
    demás la toma de su secuencia en la misma transacción."""
    if motor == "postgres":
        prefijo = f"{ESQUEMA}."
        esta = f"currval(pg_get_serial_sequence('{ESQUEMA}.corrida', 'id'))"
    else:
        prefijo = f"destino.{ESQUEMA}."
        esta = f"currval('destino.{ESQUEMA}.corrida_id')"

    sentencias = list(_insertar("corrida", prefijo,
                                [[_sql(corrida.get(c)) for c in COLUMNAS["corrida"]]]))
    sentencias += _insertar("paso", prefijo, [
        [esta, _sql(orden)] + [_sql(p[c]) for c in COLUMNAS["paso"][2:]]
        for orden, p in enumerate(pasos, start=1)])

    # La misma fila puede llegar dos veces idéntica: misma huella. Cada copia es una
    # fila apartada, y `ocurrencia` las distingue, como en la capa intermedia.
    copias, filas = {}, []
    for r in cuarentena:
        llave = (r["huella_fila"], r["motivo"])
        copias[llave] = copias.get(llave, 0) + 1
        filas.append([esta, _sql(r["motivo"]), _sql(r.get("nivel", "FILA")),
                      _sql(r["compuerta"]), _sql(r["huella_fila"]), _sql(copias[llave]),
                      _sql(r.get("grupo")), _sql(r["fila"])])
    sentencias += _insertar("cuarentena", prefijo, filas)
    sentencias += _insertar("incidente", prefijo, [
        [_sql(i["severidad"]), esta] + [_sql(i[c]) for c in COLUMNAS["incidente"][2:]]
        for i in incidentes])
    return sentencias


def _escribir(con, motor, sentencias):
    """Todo o nada. En PostgreSQL va en una sola llamada, que es una transacción."""
    if motor == "postgres":
        con.execute("CALL postgres_execute('destino', "
                    f"'{intermedia._texto_sql(chr(10).join(sentencias))}')")
        return
    con.execute("BEGIN TRANSACTION")
    try:
        for s in sentencias:
            con.execute(s)
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise


def _consulta(con, motor, sql):
    """Un SELECT sobre el esquema, escrito con `{e}`. En PostgreSQL lo corre la base."""
    if motor == "postgres":
        sql = sql.format(e=ESQUEMA)
        return con.execute("SELECT * FROM postgres_query('destino', "
                           f"'{intermedia._texto_sql(sql)}')").fetchall()
    return con.execute(sql.format(e=f"destino.{ESQUEMA}")).fetchall()


def registrar_corrida(corrida, pasos, cuarentena, incidentes, contrato=None, simular=False,
                      carpeta=None):
    """Escribe la corrida, sus pasos, sus filas en cuarentena y sus incidentes.

    Si algo falla, no queda nada: ni la corrida sin su cuarentena ni la cuarentena
    sin su corrida. Devuelve el id de la corrida y a dónde se escribió."""
    contrato = contrato or leer_contrato()
    con = intermedia._con()
    destino = intermedia.adjuntar_destino(con, contrato, simular, carpeta)
    motor = destino["motor"]
    try:
        aplicar(con, motor)
        _escribir(con, motor, sentencias_de_la_corrida(motor, corrida, pasos, cuarentena,
                                                       incidentes))
        # La corrida que se acaba de escribir es la de su marca: la corrida de Dagster.
        marca = corrida["detalle"]["ejecucion"]
        corrida_id = _consulta(
            con, motor,
            f"SELECT max(id) FROM {{e}}.corrida WHERE lote = {_sql(corrida['lote'])} "
            # Entre paréntesis: en DuckDB `->>` pesa menos que `=`.
            f"AND (detalle->>'ejecucion') = {_sql(marca)}")[0][0]
    finally:
        con.execute("DETACH destino")
    return {"id": int(corrida_id), "motor": motor, "donde": destino["donde"],
            "pasos": len(pasos), "cuarentena": len(cuarentena),
            "incidentes": [i["motivo"] for i in incidentes]}


def sentencias_del_paso(motor, corrida_id, paso_nuevo, fallida=False):
    """El SQL que agrega un paso al final de una corrida y mueve su hora de término."""
    prefijo = f"{ESQUEMA}." if motor == "postgres" else f"destino.{ESQUEMA}."
    cid, p = _sql(corrida_id), paso_nuevo

    def entero(v):
        return f"CAST({_sql(v)} AS INTEGER)"

    def hora(v):
        return f"CAST({_sql(v)} AS TIMESTAMPTZ)"

    return [
        (f"INSERT INTO {prefijo}paso ({', '.join(COLUMNAS['paso'])})\n"
        f"SELECT {cid}, CAST(coalesce(max(orden), 0) + 1 AS SMALLINT), {_sql(p['capa'])}, "
        f"{_sql(p['nombre'])}, {entero(p['filas_entrada'])}, {entero(p['filas_salida'])}, "
        f"{entero(p['filas_en_cuarentena'])}, {hora(p['iniciado_en'])}, "
        f"{hora(p['terminado_en'])}, {_sql(p['resultado'])}\n"
        f"FROM {prefijo}paso WHERE corrida_id = {cid};"),
        f"UPDATE {prefijo}corrida SET terminada_en = {hora(p['terminado_en'])}"
        + (", resultado = 'FALLIDA'" if fallida else "") + f" WHERE id = {cid};",
    ]


def agregar_paso(corrida_id, paso_nuevo, contrato=None, simular=False, carpeta=None,
                 fallida=False):
    """Agrega un paso al final de una corrida que ya existe y mueve su hora de
    término. Con `fallida`, la corrida queda FALLIDA: el lote no llegó a su capa."""
    contrato = contrato or leer_contrato()
    con = intermedia._con()
    destino = intermedia.adjuntar_destino(con, contrato, simular, carpeta)
    try:
        _escribir(con, destino["motor"],
                  sentencias_del_paso(destino["motor"], corrida_id, paso_nuevo, fallida))
    finally:
        con.execute("DETACH destino")


# ── La evidencia ───────────────────────────────────────────────────────────

# Lo que tiene que cuadrar. Cada consulta cuenta lo que NO cuadra: cero es ✓.
COMPROBACIONES = (
    ("cada corrida vigente cuenta en `filas_en_cuarentena` las filas que dejó en cuarentena",
     ("SELECT count(*) FROM {e}.corrida_vigente c WHERE c.filas_en_cuarentena IS DISTINCT FROM "
     "(SELECT count(DISTINCT q.huella_fila || '-' || CAST(q.ocurrencia AS TEXT)) "
     "FROM {e}.cuarentena q WHERE q.corrida_id = c.id)")),
    ("en las corridas que pasaron, aceptadas + en cuarentena = leídas",
     ("SELECT count(*) FROM {e}.corrida_vigente WHERE resultado IN ('CORRECTA', 'CON_AVISOS') "
     "AND filas_aceptadas + filas_en_cuarentena <> filas_leidas")),
    ("lo que sale de cada paso es lo que entra al siguiente",
     ("SELECT count(*) FROM {e}.paso a JOIN {e}.paso b ON b.corrida_id = a.corrida_id "
     "AND b.orden = a.orden + 1 WHERE a.capa <> 'INTERMEDIA' AND a.filas_salida <> b.filas_entrada")),
    ("cada lote detenido tiene su incidente",
     ("SELECT count(*) FROM {e}.corrida_vigente c WHERE c.resultado = 'RECHAZADA' AND NOT EXISTS "
     "(SELECT 1 FROM {e}.incidente i WHERE i.corrida_id = c.id AND i.severidad = 'INCIDENTE')")),
)

INDICADORES = ("ultimo_dato", "frescura_estado", "frescura_dias", "ultima_corrida_lote",
               "ultima_corrida_resultado", "filas_procesadas", "cuarentena_filas",
               "cuarentena_porcentaje", "cuarentena_poblacion", "avisos_de_esquema",
               "incidentes_abiertos")


def contar(contrato=None, simular=False, carpeta=None):
    """Las filas de cada tabla, el desglose, los indicadores de la consola y las
    comprobaciones, desde el destino."""
    contrato = contrato or leer_contrato()
    con = intermedia._con()
    destino = intermedia.adjuntar_destino(con, contrato, simular, carpeta)
    motor = destino["motor"]
    try:
        aplicar(con, motor)

        def uno(sql):
            return _consulta(con, motor, sql)

        r = {
            "destino": destino,
            "tablas": {t: uno(f"SELECT count(*) FROM {{e}}.{t}")[0][0] for t in TABLAS},
            "por_resultado": uno("SELECT resultado, count(*) FROM {e}.corrida_vigente "
                                 "GROUP BY 1 ORDER BY 1"),
            "por_motivo": uno("SELECT q.motivo, count(*) FROM {e}.cuarentena q JOIN "
                              "{e}.corrida_vigente c ON c.id = q.corrida_id GROUP BY 1 ORDER BY 1"),
            "incidentes": uno("SELECT severidad, estado, motivo, count(*) FROM {e}.incidente "
                              "GROUP BY 1, 2, 3 ORDER BY 1, 2, 3"),
            "vigentes": uno("SELECT count(*) FROM {e}.corrida_vigente")[0][0],
            "indicadores": dict(zip(INDICADORES, uno(
                f"SELECT {', '.join(INDICADORES)} FROM {{e}}.estado_de_la_plataforma")[0])),
            "comprobaciones": [(que, uno(sql)[0][0]) for que, sql in COMPROBACIONES],
        }
    finally:
        con.execute("DETACH destino")
    return r


def _cifra(v):
    return f"{v:,}" if isinstance(v, int) else str(v)


def main():
    preparar_salida()
    import argparse

    ap = argparse.ArgumentParser(description="El esquema de operación: corridas, pasos, "
                                             "cuarentena e incidentes")
    ap.add_argument("--aplicar", action="store_true",
                    help="crea o pone al día el esquema; no borra nada")
    ap.add_argument("--contar", action="store_true",
                    help="cuántas filas tiene cada tabla, y si las cuentas cuadran")
    ap.add_argument("--simular", action="store_true",
                    help="el DuckDB de la carpeta de corridas, no postgres-analytics")
    a = ap.parse_args()
    if not (a.aplicar or a.contar):
        ap.error("di --aplicar, --contar o las dos")

    contrato = leer_contrato()
    if a.aplicar and not a.contar:
        con = intermedia._con()
        destino = intermedia.adjuntar_destino(con, contrato, a.simular)
        try:
            aplicar(con, destino["motor"])
        finally:
            con.execute("DETACH destino")
        print(f"✓ esquema {ESQUEMA} aplicado · {destino['motor']} {destino['donde']}")
        return 0

    r = contar(contrato, simular=a.simular)
    d = r["destino"]
    print(f"\n{d['motor']} {d['donde']} · esquema {ESQUEMA} · contrato {contrato['version']}\n")
    for t, n in r["tablas"].items():
        print(f"  {t:<16}{n:>12,}")
    print(f"\n  corridas vigentes (la última de cada lote): {r['vigentes']:,}")
    for resultado, n in r["por_resultado"]:
        print(f"    {resultado:<46}{n:>10,}")
    print("  su cuarentena, por motivo:")
    for motivo, n in r["por_motivo"]:
        print(f"    {motivo:<46}{n:>10,}")
    print("  incidentes y avisos:")
    for severidad, estado, motivo, n in r["incidentes"] or [("ninguno", "", "", 0)]:
        print(f"    {f'{severidad} {estado} {motivo}':<46}{n:>10,}")
    print("\n  los indicadores de la consola (estado_de_la_plataforma):")
    for k, v in r["indicadores"].items():
        print(f"    {k:<28}{_cifra(v)}")
    print()
    mal = 0
    for que, n in r["comprobaciones"]:
        print(f"  {'✓' if n == 0 else '✗'} {que}" + ("" if n == 0 else f": {n:,} no"))
        mal += n
    return 0 if mal == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
