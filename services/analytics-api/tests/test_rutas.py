"""Las rutas de la interfaz contra analitica.yaml 0.2.1, con la base simulada: las
cuatro de T058, y las seis de la consola y las tres de los clientes de T069.

Lo que se comprueba es la forma: cada respuesta contra su esquema del contrato, y
que la ruta, su `operationId` y su `x-rol` sean los del contrato. Quién puede pedir
cada una está en test_sesion.py, y las consultas de verdad, contra
`postgres-analytics`, en test_postgres.py.
"""

import typing

import pytest
from analitica import modelos as m
from analitica.main import app
from conftest import CORREO, CUENTA, AlmacenDePrueba, DominioDePrueba, token
from contrato import CONTRATO, errores, esquema, operaciones

HUEVO = {"producto": "Huevo", "presentacion": "PAQUETE C/30 blanco", "entidad": "guanajuato"}
OPERADOR = {"Authorization": f"Bearer {token(rol='OPERADOR')}"}
ANALISTA = {"Authorization": f"Bearer {token(rol='ANALISTA')}"}
CIERRE = "/api/v1/operacion/incidentes/{incidenteId}/cierre"
# Lo que el contrato declara y esta interfaz todavía no sirve. Las dos del dominio
# y las dos de la cola salieron con el recorte del 5 de noviembre (alertas y
# reconciliación); el índice salió del producto y la exportación, con el detalle.
SIN_IMPLEMENTAR = {"rangoHistorico", "preciosVigentes", "indiceContraInpc", "exportarArticulo",
                   "colaDeVariantes", "resolverVariante"}
IMPLEMENTADAS = [(ruta, metodo, o["operationId"], o.get("x-rol"))
                 for ruta, metodo, o in operaciones()
                 if o["operationId"] not in SIN_IMPLEMENTAR]


def test_son_la_salud_y_las_trece_del_contrato():
    assert len(IMPLEMENTADAS) == 14
    generadas = {o["operationId"] for metodos in app.openapi()["paths"].values()
                 for o in metodos.values()}
    assert generadas == {operacion for _, _, operacion, _ in IMPLEMENTADAS}


@pytest.mark.parametrize(("ruta", "metodo", "operacion", "rol"), IMPLEMENTADAS)
def test_la_ruta_es_la_del_contrato(ruta, metodo, operacion, rol):
    generada = app.openapi()["paths"][ruta][metodo]
    assert generada["operationId"] == operacion
    assert generada.get("x-rol") == rol


def test_los_motivos_y_las_causas_son_los_del_contrato():
    motivos = CONTRATO["components"]["schemas"]["MotivoDeCuarentena"]["enum"]
    assert list(typing.get_args(m.MotivoDeCuarentena)) == motivos
    cuerpo = CONTRATO["paths"][CIERRE]["post"]["requestBody"]["content"]["application/json"]
    assert list(typing.get_args(m.Causa)) == cuerpo["schema"]["properties"]["causa"]["enum"]


def _cumple(r, ruta, estado=200, medio="application/json", metodo="get"):
    assert r.status_code == estado, r.text
    assert r.headers["content-type"].startswith(medio)
    assert not errores(r.json(), esquema(ruta, metodo, estado, medio)), r.json()
    return r.json()


def _problema(r, ruta, estado, metodo="get"):
    return _cumple(r, ruta, estado, "application/problem+json", metodo)


def test_entidades(cliente):
    cuerpo = _cumple(cliente.get("/api/v1/entidades"), "/api/v1/entidades")
    assert cuerpo["entidades"][0] == {"entidad": "Guanajuato", "ultimaQuincena": "2026-07-Q2"}


def test_buscar_en_una_entidad_cubierta(cliente):
    r = cliente.get("/api/v1/articulos", params={"q": "huevo", "entidad": "GUANAJUATO"})
    cuerpo = _cumple(r, "/api/v1/articulos")
    assert cuerpo["cobertura"] and cuerpo["entidad"] == "Guanajuato" and cuerpo["total"] == 1
    assert cuerpo["resultados"][0]["precioTipico"] == {"monto": "65.00", "moneda": "MXN"}


def test_buscar_fuera_del_alcance_es_200_con_cobertura_false(cliente):
    r = cliente.get("/api/v1/articulos", params={"q": "huevo", "entidad": "Yucatán"})
    cuerpo = _cumple(r, "/api/v1/articulos")
    assert cuerpo == {"cobertura": False, "entidad": "Yucatán",
                      "entidadesCubiertas": ["Guanajuato", "Querétaro"]}


@pytest.mark.parametrize("params", [{"q": "h", "entidad": "Guanajuato"},
                                    {"q": "huevo", "entidad": "Guanajuato", "limit": 101},
                                    {"q": "huevo", "entidad": "Guanajuato", "catalogo": "OTRO"}])
def test_datos_invalidos_es_400(cliente, params):
    _cumple(cliente.get("/api/v1/articulos", params=params), "/api/v1/articulos", 400,
            "application/problem+json")


def test_precios_con_la_marca_generica_al_final(cliente):
    cuerpo = _cumple(cliente.get("/api/v1/precios", params=HUEVO), "/api/v1/precios")
    assert cuerpo["articulo"] == {"producto": "huevo", "presentacion": "paquete c 30 blanco"}
    assert [e["precio"]["monto"] for e in cuerpo["establecimientos"]] == ["62.50", "60.00"]


def test_precios_sin_datos_es_404(cliente):
    r = cliente.get("/api/v1/precios", params={**HUEVO, "producto": "caviar"})
    _cumple(r, "/api/v1/precios", 404, "application/problem+json")


def test_desglose_trae_su_poblacion(cliente):
    r = cliente.get("/api/v1/articulos/establecimientos", params=HUEVO,
                    headers={"Authorization": f"Bearer {token()}"})
    cuerpo = _cumple(r, "/api/v1/articulos/establecimientos")
    assert cuerpo["establecimientos"][0]["promedio"]["monto"] == "64.33"
    assert cuerpo["poblacion"] == {"entidades": ["Guanajuato"], "desde": "2026-07-Q1",
                                   "hasta": "2026-07-Q2", "observaciones": 3}


# ── Los clientes, sobre la estrella (T069) ─────────────────────────────────────

COSTO = "/api/v1/canastas/costo"
CANASTA = {"entidad": "GUANAJUATO", "lineas": [
    {"articulo": {"producto": "Huevo", "presentacion": "PAQUETE C/30 blanco"}, "cantidad": 2},
    {"articulo": {"producto": "Leche", "presentacion": "1 L"}, "cantidad": 3},
    {"articulo": {"producto": "Caviar", "presentacion": "Lata"}, "cantidad": 1}]}


def test_costo_de_la_canasta_por_cadena_sin_sesion(cliente):
    cuerpo = _cumple(cliente.post(COSTO, json=CANASTA), COSTO, metodo="post")
    assert (cuerpo["entidad"], cuerpo["quincena"]) == ("Guanajuato", "2026-07-Q2")
    # Primero a las que les faltan menos; con los mismos faltantes, la más barata.
    assert [(c["cadena"], c["faltan"], c["total"]["monto"]) for c in cuerpo["cadenas"]] == [
        ("Bodega Aurrera", 1, "202.00"), ("Soriana", 1, "216.32"), ("Mercado", 2, "116.00")]


def test_sin_precio_es_null_y_no_entra_al_total(cliente):
    cuerpo = _cumple(cliente.post(COSTO, json=CANASTA), COSTO, metodo="post")
    mercado = cuerpo["cadenas"][-1]
    assert [linea["precio"] for linea in mercado["lineas"]] == [
        {"monto": "58.00", "moneda": "MXN"}, None, None]
    assert mercado["lineas"][2]["articulo"] == {"producto": "caviar", "presentacion": "lata"}
    # 2 × 66.90 + 3 × 27.505 = 216.315: se suma exacto y se redondea al final (P-02).
    assert cuerpo["cadenas"][1]["total"] == {"monto": "216.32", "moneda": "MXN"}


def test_una_canasta_vacia_cuesta_cero_cadenas(cliente):
    r = cliente.post(COSTO, json={"entidad": "Guanajuato", "lineas": []})
    assert _cumple(r, COSTO, metodo="post")["cadenas"] == []


@pytest.mark.parametrize("pedido", [
    {"entidad": "Yucatán", "lineas": []},
    {"lineas": []},
    {"entidad": "Guanajuato", "lineas": [{"articulo": CANASTA["lineas"][0]["articulo"],
                                          "cantidad": 0}]},
    {"entidad": "Guanajuato", "lineas": [CANASTA["lineas"][0]] * 201}])
def test_un_pedido_de_costo_invalido_es_400(cliente, pedido):
    _problema(cliente.post(COSTO, json=pedido), COSTO, 400, "post")


def test_anomalos_con_su_variacion_y_su_poblacion(cliente):
    cuerpo = _cumple(cliente.get("/api/v1/anomalias", headers=ANALISTA), "/api/v1/anomalias")
    assert [(a["articulo"]["producto"], a["quincena"], a["variacion"], a["observaciones"])
            for a in cuerpo["articulos"]] == [("jitomate saladette", "2026-07-Q1", 0.4426, 9),
                                              ("limon", "2026-06-Q2", -0.2511, 6)]
    assert cuerpo["poblacion"] == {"entidades": ["Guanajuato", "Querétaro"],
                                   "desde": "2025-01-Q1", "hasta": "2026-07-Q2",
                                   "observaciones": 286489}


def test_anomalos_con_otro_umbral_y_otro_minimo(cliente):
    r = cliente.get("/api/v1/anomalias", headers=ANALISTA,
                    params={"umbral": 0.3, "minimoDeObservaciones": 7, "entidad": "guanajuato",
                            "catalogo": "FRUTAS Y LEGUMBRES", "desde": "2026-06-Q1", "limit": 5})
    cuerpo = _cumple(r, "/api/v1/anomalias")
    assert [a["articulo"]["producto"] for a in cuerpo["articulos"]] == ["jitomate saladette"]


def test_anomalos_fuera_del_alcance_no_es_un_error(cliente):
    r = cliente.get("/api/v1/anomalias", headers=ANALISTA, params={"entidad": "Yucatán"})
    cuerpo = _cumple(r, "/api/v1/anomalias")
    assert cuerpo["articulos"] == [] and cuerpo["poblacion"]["entidades"] == []
    assert cuerpo["poblacion"]["observaciones"] == 0


@pytest.mark.parametrize("params", [{"umbral": -0.1}, {"minimoDeObservaciones": 0},
                                    {"desde": "julio"}, {"catalogo": "OTRO"}, {"limit": 0}])
def test_anomalos_con_un_parametro_invalido_es_400(cliente, params):
    r = cliente.get("/api/v1/anomalias", headers=ANALISTA, params=params)
    assert r.status_code == 400 and r.json()["type"] == "/problemas/datos-invalidos"


SERIE = "/api/v1/articulos/serie"


def test_la_serie_trae_un_punto_por_quincena_y_entidad(cliente):
    cuerpo = _cumple(cliente.get(SERIE, params=HUEVO, headers=ANALISTA), SERIE)
    assert cuerpo["articulo"] == {"producto": "huevo", "presentacion": "paquete c 30 blanco"}
    assert cuerpo["puntos"][0] == {
        "quincena": "2026-07-Q1", "entidad": "Guanajuato", "observaciones": 47,
        "mediana": {"monto": "65.00", "moneda": "MXN"}, "p25": {"monto": "62.00", "moneda": "MXN"},
        "p75": {"monto": "68.50", "moneda": "MXN"}, "minimo": {"monto": "59.00", "moneda": "MXN"},
        "maximo": {"monto": "91.00", "moneda": "MXN"}}


def test_la_serie_sin_entidad_son_todas_las_del_alcance(cliente):
    sin_entidad = {k: v for k, v in HUEVO.items() if k != "entidad"}
    assert len(_cumple(cliente.get(SERIE, params=sin_entidad, headers=ANALISTA),
                       SERIE)["puntos"]) == 2


@pytest.mark.parametrize("params", [{**HUEVO, "producto": "caviar"},
                                    {**HUEVO, "entidad": "Yucatán"}])
def test_la_serie_sin_datos_es_404(cliente, params):
    _problema(cliente.get(SERIE, params=params, headers=ANALISTA), SERIE, 404)


# ── La consola, sobre el esquema de operación (T069) ───────────────────────────

ESTADO = "/api/v1/operacion/estado"
CORRIDAS = "/api/v1/operacion/corridas"
LINAJE = "/api/v1/operacion/corridas/{lote}"
CUARENTENA = "/api/v1/operacion/cuarentena"
INCIDENTES = "/api/v1/operacion/incidentes"
CUERPO = {"causa": "ARCHIVO_DE_LA_FUENTE", "reprocesarLote": True,
          "decision": "  La fuente repitió filas; se reprocesa cuando corrija.  "}


def test_el_estado_trae_los_seis_indicadores_de_cu05(cliente):
    cuerpo = _cumple(cliente.get(ESTADO, headers=OPERADOR), ESTADO)
    assert cuerpo == {
        "ultimoDato": "2026-07-Q2", "frescura": {"estado": "NO_APLICA", "dias": 102},
        "ultimaCorrida": {"lote": "07-2026_Q2", "fecha": "2026-11-10T18:00:00Z",
                          "resultado": "CORRECTA", "filasLeidas": 70120,
                          "filasAceptadas": 69980, "filasEnCuarentena": 140,
                          "duracionSegundos": 42.5},
        "filasProcesadas": 139220,
        "cuarentena": {"filas": 240, "porcentaje": 0.172,
                       "poblacion": "lotes vigentes del alcance"},
        "avisosDeEsquema": 1, "incidentesAbiertos": 1}


def test_sin_corridas_el_estado_lo_dice_en_lugar_de_dar_ceros(cliente):
    AlmacenDePrueba.sin_corridas = True       # CU-05 · 2b
    cuerpo = cliente.get(ESTADO, headers=OPERADOR)
    assert cuerpo.status_code == 404 and cuerpo.json()["type"] == "/problemas/sin-datos"


def test_las_corridas_de_la_mas_reciente_a_la_mas_antigua(cliente):
    cuerpo = _cumple(cliente.get(CORRIDAS, headers=OPERADOR, params={"limit": 2}), CORRIDAS)
    assert cuerpo["total"] == 4
    assert [c["lote"] for c in cuerpo["corridas"]] == ["07-2026_Q2", "06-2026_Q2"]


def test_el_linaje_trae_todas_las_corridas_del_lote_y_la_ultima_es_la_vigente(cliente):
    r = cliente.get(LINAJE.format(lote="04-2026_Q2"), headers=OPERADOR)
    cuerpo = _cumple(r, LINAJE)
    assert cuerpo["lote"] == "04-2026_Q2"
    assert [c["resultado"] for c in cuerpo["corridas"]] == ["RECHAZADA", "CORRECTA"]   # 5a


def test_el_linaje_de_un_lote_sin_corridas_es_404(cliente):
    _problema(cliente.get(LINAJE.format(lote="01-2020_Q1"), headers=OPERADOR), LINAJE, 404)


def test_la_cuarentena_con_su_motivo_y_la_fila_tal_como_llego(cliente):
    cuerpo = _cumple(cliente.get(CUARENTENA, headers=OPERADOR), CUARENTENA)
    assert cuerpo["total"] == 3
    assert cuerpo["filas"][0] == {
        "lote": "07-2026_Q2", "motivo": "revision_humana", "compuerta": "contrato_por_fila",
        "fila": {"producto": "HUEVO", "marca": "BACH?CO", "precio": "65.00"}}


def test_la_cuarentena_se_filtra_por_lote_y_por_motivo(cliente):
    r = cliente.get(CUARENTENA, headers=OPERADOR,
                    params={"lote": "07-2026_Q2", "motivo": "colision_precio_alta"})
    cuerpo = _cumple(r, CUARENTENA)
    assert cuerpo["total"] == 1 and cuerpo["filas"][0]["fila"]["producto"] == "LECHE"


def test_un_motivo_que_no_es_de_fila_es_400(cliente):
    r = cliente.get(CUARENTENA, headers=OPERADOR, params={"motivo": "columnas_extra"})
    assert r.status_code == 400 and r.json()["type"] == "/problemas/datos-invalidos"


def test_los_incidentes_y_los_avisos_con_su_lote_compuerta_y_motivo(cliente):
    cuerpo = _cumple(cliente.get(INCIDENTES, headers=OPERADOR), INCIDENTES)
    assert cuerpo["total"] == 3
    assert [(i["id"], i["severidad"], i["estado"]) for i in cuerpo["incidentes"]] == [
        ("1", "AVISO", "INFORMATIVO"), ("2", "INCIDENTE", "ABIERTO"),
        ("3", "INCIDENTE", "CERRADO")]
    assert cuerpo["incidentes"][2]["cerradoPor"] == "otra@canastamx.mx"


@pytest.mark.parametrize(("params", "ids"), [({"estado": "ABIERTO"}, ["2"]),
                                             ({"estado": "CERRADO"}, ["3"]),
                                             ({"severidad": "AVISO"}, ["1"]),
                                             ({"severidad": "INCIDENTE"}, ["2", "3"])])
def test_los_incidentes_se_filtran_por_estado_y_severidad(cliente, params, ids):
    cuerpo = _cumple(cliente.get(INCIDENTES, headers=OPERADOR, params=params), INCIDENTES)
    assert [i["id"] for i in cuerpo["incidentes"]] == ids


def test_informativo_no_es_un_estado_por_el_que_se_filtre(cliente):
    r = cliente.get(INCIDENTES, headers=OPERADOR, params={"estado": "INFORMATIVO"})
    assert r.status_code == 400


def _cerrar(cliente, incidente_id, cuerpo=CUERPO, cabeceras=OPERADOR):
    return cliente.post(CIERRE.format(incidenteId=incidente_id), json=cuerpo, headers=cabeceras)


def test_cerrar_guarda_la_causa_la_decision_la_fecha_y_el_correo(cliente):
    cuerpo = _cumple(_cerrar(cliente, 2), CIERRE, metodo="post")
    assert (cuerpo["id"], cuerpo["estado"], cuerpo["causa"]) == ("2", "CERRADO",
                                                                 "ARCHIVO_DE_LA_FUENTE")
    assert cuerpo["decision"] == "La fuente repitió filas; se reprocesa cuando corrija."
    assert cuerpo["reprocesarLote"] is True and cuerpo["cerradoEn"] is not None
    assert cuerpo["cerradoPor"] == CORREO                                      # D-11
    # Ya no está entre los abiertos, y quedó en el historial.
    abiertos = cliente.get(INCIDENTES, headers=OPERADOR, params={"estado": "ABIERTO"}).json()
    assert abiertos["total"] == 0


def test_quien_cierra_sale_de_la_cuenta_de_la_sesion_y_no_del_cuerpo(cliente):
    valor = token(rol="OPERADOR")
    r = _cerrar(cliente, 2, {**CUERPO, "cerradoPor": "impostor@canastamx.mx",
                             "cerradoEn": "2020-01-01T00:00:00Z"},
                {"Authorization": f"Bearer {valor}"})
    assert r.json()["cerradoPor"] == CORREO and not r.json()["cerradoEn"].startswith("2020")
    # Al dominio se le pregunta con el mismo token, por la cuenta de su `sub`.
    assert DominioDePrueba.pedidos == [(valor, CUENTA)]


def test_un_aviso_no_se_puede_cerrar(cliente):
    cuerpo = _problema(_cerrar(cliente, 1), CIERRE, 409, "post")
    assert cuerpo["type"] == "/problemas/no-se-cierra" and "aviso" in cuerpo["detail"]
    assert AlmacenDePrueba.incidentes_guardados[1][6] == "INFORMATIVO"
    assert DominioDePrueba.pedidos == []


def test_un_incidente_ya_cerrado_no_se_vuelve_a_cerrar(cliente):
    _problema(_cerrar(cliente, 3), CIERRE, 409, "post")
    assert _cerrar(cliente, 2).status_code == 200
    _problema(_cerrar(cliente, 2), CIERRE, 409, "post")
    assert AlmacenDePrueba.incidentes_guardados[3][9] == "otra@canastamx.mx"


@pytest.mark.parametrize("incidente_id", ["99", "abc", "2.0", "-2", "9" * 30, "٢"])
def test_cerrar_un_incidente_que_no_existe_es_404(cliente, incidente_id):
    _problema(_cerrar(cliente, incidente_id), CIERRE, 404, "post")


@pytest.mark.parametrize("cuerpo", [{"decision": "x"}, {"causa": "INFRAESTRUCTURA"},
                                    {"causa": "OTRA", "decision": "x"},
                                    {"causa": "INFRAESTRUCTURA", "decision": "   "},
                                    {"causa": "INFRAESTRUCTURA", "decision": "x",
                                     "reprocesarLote": "quizá"}])
def test_cerrar_sin_causa_o_sin_decision_es_400_y_no_cierra(cliente, cuerpo):
    r = _cerrar(cliente, 2, cuerpo)
    assert r.status_code == 400 and r.json()["type"] == "/problemas/datos-invalidos"
    assert AlmacenDePrueba.incidentes_guardados[2][6] == "ABIERTO"


def test_si_el_dominio_no_dice_quien_cierra_no_se_cierra(cliente):
    from analitica.main import dominio
    from analitica.problemas import DominioNoDisponible

    class DominioCaido:
        def correo(self, token, cuenta):
            raise DominioNoDisponible("No se pudo preguntar al dominio.")

    app.dependency_overrides[dominio] = DominioCaido
    r = _cerrar(cliente, 2)
    assert r.status_code == 503 and r.json()["type"] == "/problemas/dominio-no-disponible"
    assert r.headers["content-type"].startswith("application/problem+json")
    assert AlmacenDePrueba.incidentes_guardados[2][6] == "ABIERTO"
