"""Las rutas contra `postgres-analytics` de verdad, con lo que tenga cargado: la capa
intermedia (T058), la estrella y el esquema de operación (T069).

Sólo corre si se pide, con las `ANALYTICS_*` y `JWT_SECRET` del `.env`:

    CANASTAMX_PRUEBA_POSTGRES=1 python -m pytest services/analytics-api/tests/test_postgres.py -v -s

Estas pruebas sólo leen. La que escribe, el cierre de un incidente, se pide aparte
y contra una base de pruebas, porque mientras corre mete en el esquema de operación
una corrida y un incidente de mentira, y al terminar los borra:

    CANASTAMX_PRUEBA_CIERRE=1 python -m pytest services/analytics-api/tests/test_postgres.py -v -s
"""

import os
from decimal import Decimal

import pytest
from conftest import CORREO, DominioDePrueba, token
from contrato import errores, esquema

LEE = pytest.mark.skipif(os.environ.get("CANASTAMX_PRUEBA_POSTGRES") != "1",
                         reason="contra postgres-analytics: CANASTAMX_PRUEBA_POSTGRES=1")
ESCRIBE = pytest.mark.skipif(os.environ.get("CANASTAMX_PRUEBA_CIERRE") != "1",
                             reason="escribe en el esquema de operación: CANASTAMX_PRUEBA_CIERRE=1")
CIERRE = "/api/v1/operacion/incidentes/{incidenteId}/cierre"
ARCHIVO = "prueba-de-t069-cerrar-incidente.csv"
CUERPO = {"causa": "DATO_REAL_ATIPICO", "decision": "Prueba de T069: se borra al terminar."}


def _cliente():
    from analitica.main import app
    from fastapi.testclient import TestClient

    return TestClient(app)


def _cabeceras(rol):
    return {"Authorization": f"Bearer {token(rol=rol)}"}


def _pedir(cliente, ruta, metodo="get", plantilla=None, estado=200, **pedido):
    """Pide, comprueba el estado y el esquema del contrato, y devuelve el cuerpo."""
    r = cliente.request(metodo, ruta, **pedido)
    assert r.status_code == estado, (ruta, r.text)
    medio = "application/json" if estado == 200 else "application/problem+json"
    assert not errores(r.json(), esquema(plantilla or ruta, metodo, estado, medio)), (ruta, r.json())
    return r.json()


def _resumen(cuerpo):
    return {k: (len(v) if isinstance(v, list) else v) for k, v in cuerpo.items()
            if k != "articulo"}


@LEE
def test_las_cuatro_rutas_responden_con_el_contrato_y_datos_reales():
    from analitica.datos import TABLA, Almacen

    fila = Almacen().consulta(f"SELECT clave_producto, clave_presentacion, entidad, count(*) "
                              f"FROM {TABLA} GROUP BY 1, 2, 3 ORDER BY 4 DESC LIMIT 1")
    if not fila:
        pytest.skip("la capa intermedia está vacía")
    articulo = dict(zip(("producto", "presentacion", "entidad"), fila[0][:3], strict=True))
    cliente = _cliente()
    for ruta, params, cabeceras in [
            ("/api/v1/entidades", {}, {}),
            ("/api/v1/articulos", {"q": articulo["producto"], "entidad": articulo["entidad"]}, {}),
            ("/api/v1/precios", articulo, {}),
            ("/api/v1/articulos/establecimientos", articulo, _cabeceras("ANALISTA"))]:
        cuerpo = _pedir(cliente, ruta, params=params, headers=cabeceras)
        print(f"{ruta} → 200 · {_resumen(cuerpo)}")


@LEE
def test_las_seis_de_la_consola_con_las_corridas_reales():
    """El criterio de #211: con una corrida real, `estadoDeLaPlataforma` trae los
    seis indicadores de CU-05 con su población."""
    from analitica.datos import OPERACION, Almacen

    if not Almacen().consulta(f"SELECT 1 FROM {OPERACION}.corrida LIMIT 1"):
        pytest.skip("el esquema de operación no tiene corridas")
    cliente, operador = _cliente(), _cabeceras("OPERADOR")

    estado = _pedir(cliente, "/api/v1/operacion/estado", headers=operador)
    assert set(estado) >= {"frescura", "ultimaCorrida", "filasProcesadas", "cuarentena",
                           "avisosDeEsquema", "incidentesAbiertos"}
    assert estado["cuarentena"]["poblacion"]
    print("\n/api/v1/operacion/estado → 200 · los seis indicadores de CU-05")
    ultima, cuarentena, frescura = estado["ultimaCorrida"], estado["cuarentena"], estado["frescura"]
    dato = f"{estado.get('ultimoDato')} · frescura {frescura['estado']} ({frescura.get('dias')} días)"
    apartado = (f"{cuarentena['filas']:,} · {cuarentena['porcentaje']}% · "
                f"población: {cuarentena['poblacion']}")
    for nombre, valor in [
            ("1 · dato más reciente", dato),
            ("2 · última corrida", f"{ultima['lote']} · {ultima['resultado']}"),
            ("3 · filas procesadas", f"{estado['filasProcesadas']:,}"),
            ("4 · en cuarentena", apartado),
            ("5 · avisos de esquema", estado["avisosDeEsquema"]),
            ("6 · incidentes abiertos", estado["incidentesAbiertos"])]:
        print(f"  {nombre:<24}{valor}")

    corridas = _pedir(cliente, "/api/v1/operacion/corridas", headers=operador)
    print(f"/api/v1/operacion/corridas → 200 · {_resumen(corridas)}")
    lote = corridas["corridas"][0]["lote"]
    linaje = _pedir(cliente, f"/api/v1/operacion/corridas/{lote}",
                    plantilla="/api/v1/operacion/corridas/{lote}", headers=operador)
    print(f"/api/v1/operacion/corridas/{lote} → 200 · {_resumen(linaje)}")
    apartadas = _pedir(cliente, "/api/v1/operacion/cuarentena", headers=operador)
    # Lo que se lista es lo que cuenta el indicador: la misma población.
    assert apartadas["total"] == cuarentena["filas"]
    print(f"/api/v1/operacion/cuarentena → 200 · {_resumen(apartadas)}")
    incidentes = _pedir(cliente, "/api/v1/operacion/incidentes", headers=operador,
                        params={"limit": 100})
    print(f"/api/v1/operacion/incidentes → 200 · {_resumen(incidentes)}")
    abiertos = _pedir(cliente, "/api/v1/operacion/incidentes", headers=operador,
                      params={"estado": "ABIERTO"})
    assert abiertos["total"] == estado["incidentesAbiertos"]

    # Con ANALISTA o sin token, 401. Y un aviso no se puede cerrar: ninguna de estas escribe.
    for cabeceras in ({}, _cabeceras("ANALISTA")):
        _pedir(cliente, "/api/v1/operacion/estado", estado=401, headers=cabeceras)
    aviso = next((i for i in incidentes["incidentes"] if i["severidad"] == "AVISO"), None)
    if aviso:
        _pedir(cliente, CIERRE.format(incidenteId=aviso["id"]), "post", CIERRE, 409,
               headers=operador, json=CUERPO)
        print(f"POST …/incidentes/{aviso['id']}/cierre (un aviso) → 409")
    _pedir(cliente, CIERRE.format(incidenteId="0"), "post", CIERRE, 404, headers=operador,
           json=CUERPO)


@LEE
def test_las_tres_de_los_clientes_con_la_estrella_real():
    from analitica.datos import CONSUMO, Almacen

    datos = Almacen()
    fila = datos.consulta(f"""
        SELECT a.producto_c, a.presentacion_c, g.entidad
        FROM {CONSUMO}.agg_articulo_cadena_entidad_quincena g
        JOIN {CONSUMO}.dim_articulo a ON a.articulo_key = g.articulo_canonico_key
        WHERE g.quincena = (SELECT max(quincena) FROM {CONSUMO}.agg_articulo_cadena_entidad_quincena)
        GROUP BY 1, 2, 3 ORDER BY count(*) DESC, 1, 2, 3 LIMIT 1""")
    if not fila:
        pytest.skip("la estrella está vacía: python services/data-platform/ingestion/estrella.py --cargar")
    producto, presentacion, entidad = fila[0]
    articulo = {"producto": producto, "presentacion": presentacion}
    cliente, analista = _cliente(), _cabeceras("ANALISTA")

    costo = _pedir(cliente, "/api/v1/canastas/costo", "post", json={
        "entidad": entidad, "lineas": [{"articulo": articulo, "cantidad": 2},
                                       {"articulo": {"producto": "no existe", "presentacion": "x"},
                                        "cantidad": 1}]})
    assert costo["cadenas"] and all(c["faltan"] == 1 for c in costo["cadenas"])
    barata = costo["cadenas"][0]
    print(f"\n/api/v1/canastas/costo → 200 · {entidad} · {costo['quincena']} · "
          f"{len(costo['cadenas'])} cadenas · la más barata: {barata['cadena']}, "
          f"${barata['total']['monto']}, faltan {barata['faltan']}")

    serie = _pedir(cliente, "/api/v1/articulos/serie", headers=analista,
                   params={**articulo, "entidad": entidad})
    print(f"/api/v1/articulos/serie → 200 · {producto} · {presentacion} · {entidad} · "
          f"{len(serie['puntos'])} quincenas, de {serie['puntos'][0]['quincena']} a "
          f"{serie['puntos'][-1]['quincena']}")

    anomalos = _pedir(cliente, "/api/v1/anomalias", headers=analista, params={"limit": 100})
    print(f"/api/v1/anomalias → 200 · {len(anomalos['articulos'])} en la primera página · "
          f"población: {anomalos['poblacion']}")
    for cabeceras in ({}, _cabeceras("OPERADOR")):
        _pedir(cliente, "/api/v1/anomalias", estado=401, headers=cabeceras)

    # P-15, con el volumen real: cuántos marca cada par de valores, de cuántos comparados.
    print("P-15 · artículos anómalos por umbral y mínimo de observaciones, en todo el periodo:")
    for umbral, minimo in [("0.2", 5), ("0.2", 10), ("0.3", 5), ("0.5", 5)]:
        filas, poblacion = datos.anomalos(None, None, None, None, Decimal(umbral), minimo, None)
        comparados = datos.comparaciones(minimo)
        ultima = sum(1 for f in filas if f[3] == poblacion[2])
        print(f"  umbral {float(umbral):.0%}, mínimo {minimo:>2}: {len(filas):>7,} de "
              f"{comparados:,} comparaciones ({len(filas) / max(comparados, 1):.2%}) · "
              f"{ultima:,} en {poblacion[2]}")


@ESCRIBE
def test_cerrar_un_incidente_de_verdad_guarda_causa_decision_fecha_y_correo():
    """La única escritura de la interfaz, contra la base: mete una corrida detenida
    con su incidente, lo cierra por la ruta, lo comprueba en la tabla y lo borra."""
    from analitica.datos import OPERACION, Almacen
    from analitica.main import app, dominio

    datos = Almacen()

    def borrar():
        suyas = f"(SELECT id FROM {OPERACION}.corrida WHERE archivo = %s)"
        datos.consulta(f"WITH i AS (DELETE FROM {OPERACION}.incidente WHERE corrida_id IN {suyas}) "
                       f"DELETE FROM {OPERACION}.corrida WHERE archivo = %s RETURNING id",
                       (ARCHIVO, ARCHIVO))

    borrar()
    corrida = datos.consulta(f"""
        INSERT INTO {OPERACION}.corrida (lote, archivo, sha256_entrada, version_contrato,
            fecha_de_referencia, iniciada_en, terminada_en, filas_leidas, filas_aceptadas,
            filas_en_cuarentena, resultado, frescura_estado)
        VALUES ('01-2025_01', %s, repeat('0', 64), 'prueba', '2025-01-15',
                '2025-01-15 10:00+00', '2025-01-15 10:04+00', 100, 0, 9, 'RECHAZADA', 'NO_APLICA')
        RETURNING id""", (ARCHIVO,))[0][0]
    try:
        incidente, aviso = (fila[0] for fila in datos.consulta(f"""
            INSERT INTO {OPERACION}.incidente (severidad, corrida_id, compuerta, motivo,
                filas_afectadas, abierto_en, estado)
            VALUES ('INCIDENTE', %(c)s, 'promocion_del_lote', 'rechazo_mayor_al_umbral', 9,
                    '2025-01-15 10:04+00', 'ABIERTO'),
                   ('AVISO', %(c)s, 'deriva_de_esquema', 'columnas_extra', 0,
                    '2025-01-15 10:01+00', 'INFORMATIVO')
            RETURNING id""", {"c": corrida}))
        app.dependency_overrides[dominio] = DominioDePrueba
        cliente, operador = _cliente(), _cabeceras("OPERADOR")

        _pedir(cliente, CIERRE.format(incidenteId=aviso), "post", CIERRE, 409, headers=operador,
               json=CUERPO)
        for cabeceras in ({}, _cabeceras("ANALISTA")):
            _pedir(cliente, CIERRE.format(incidenteId=incidente), "post", CIERRE, 401,
                   headers=cabeceras, json=CUERPO)
        cerrado = _pedir(cliente, CIERRE.format(incidenteId=incidente), "post", CIERRE,
                         headers=operador, json={**CUERPO, "reprocesarLote": True})
        assert (cerrado["estado"], cerrado["cerradoPor"]) == ("CERRADO", CORREO)
        _pedir(cliente, CIERRE.format(incidenteId=incidente), "post", CIERRE, 409,
               headers=operador, json=CUERPO)

        en_la_base = datos.consulta(
            f"SELECT id, estado, causa, decision, cerrado_por, reprocesar_lote, "
            f"cerrado_en IS NOT NULL FROM {OPERACION}.incidente WHERE corrida_id = %s "
            "ORDER BY severidad", (corrida,))
        assert en_la_base == [
            (aviso, "INFORMATIVO", None, None, None, False, False),
            (incidente, "CERRADO", "DATO_REAL_ATIPICO", CUERPO["decision"], CORREO, True, True)]
        print(f"\nPOST …/incidentes/{incidente}/cierre → 200 · en operacion.incidente: "
              f"{en_la_base[1][1:]}")
    finally:
        app.dependency_overrides.clear()
        borrar()
    assert not datos.consulta(f"SELECT 1 FROM {OPERACION}.corrida WHERE archivo = %s", (ARCHIVO,))
