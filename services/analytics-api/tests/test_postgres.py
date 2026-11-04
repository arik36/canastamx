"""Las cuatro rutas contra `postgres-analytics` de verdad, con lo que tenga cargado.

Sólo corre si se pide, con las `ANALYTICS_*` y `JWT_SECRET` del `.env`:

    CANASTAMX_PRUEBA_POSTGRES=1 python -m pytest services/analytics-api/tests/test_postgres.py -v -s
"""

import os

import pytest
from conftest import token
from contrato import errores, esquema

pytestmark = pytest.mark.skipif(os.environ.get("CANASTAMX_PRUEBA_POSTGRES") != "1",
                                reason="contra postgres-analytics: CANASTAMX_PRUEBA_POSTGRES=1")


def test_las_cuatro_rutas_responden_con_el_contrato_y_datos_reales():
    from analitica.datos import TABLA, Almacen
    from analitica.main import app
    from fastapi.testclient import TestClient

    fila = Almacen().consulta(f"SELECT clave_producto, clave_presentacion, entidad, count(*) "
                              f"FROM {TABLA} GROUP BY 1, 2, 3 ORDER BY 4 DESC LIMIT 1")
    if not fila:
        pytest.skip("la capa intermedia está vacía")
    articulo = dict(zip(("producto", "presentacion", "entidad"), fila[0][:3], strict=True))
    cliente = TestClient(app)
    for ruta, params, cabeceras in [
            ("/api/v1/entidades", {}, {}),
            ("/api/v1/articulos", {"q": articulo["producto"], "entidad": articulo["entidad"]}, {}),
            ("/api/v1/precios", articulo, {}),
            ("/api/v1/articulos/establecimientos", articulo,
             {"Authorization": f"Bearer {token()}"})]:
        r = cliente.get(ruta, params=params, headers=cabeceras)
        assert r.status_code == 200, (ruta, r.text)
        assert not errores(r.json(), esquema(ruta, "get", 200)), (ruta, r.json())
        cuerpo = r.json()
        resumen = {k: (len(v) if isinstance(v, list) else v) for k, v in cuerpo.items()
                   if k != "articulo"}
        print(f"{ruta} → 200 · {resumen}")
