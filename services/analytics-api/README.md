# Interfaz analítica · `analytics-api`

FastAPI (ADR 017). Lee la capa intermedia de T048 en `postgres-analytics` y verifica
el token que emite el dominio (ADR 020). Contrato: `docs/analisis/openapi/analitica.yaml` 0.2.1.

| Ruta | `operationId` | Sesión |
|---|---|---|
| `GET /api/v1/entidades` | `listarEntidades` | no |
| `GET /api/v1/articulos` | `buscarArticulos` | no |
| `GET /api/v1/precios` | `compararPrecios` | no |
| `GET /api/v1/articulos/establecimientos` | `desgloseDeArticulo` | `x-rol: ANALISTA` |

Mientras no exista la estrella de T053, el artículo se busca por `clave_producto` y
`clave_presentacion` de la capa intermedia, en la forma canónica del contrato.

## Correrla

Desde la raíz, con el `.env` cargado. Usa `JWT_SECRET` y las `ANALYTICS_*`;
`ANALYTICS_HOST` es opcional, y por omisión es `localhost`.

```bash
set -a; source .env; set +a
pip install -r services/analytics-api/requirements.txt
cd services/analytics-api && uvicorn analitica.main:app --port 8000
```

Si `JWT_SECRET` no es Base64 de 32 bytes, no arranca, igual que el dominio.

## Pruebas

```bash
python -m pytest services/analytics-api/tests/ -v      # las de la CI: sin base ni dominio
```

Dos más corren sólo si se piden, con el `.env` cargado:

- **Contra `postgres-analytics`, con lo que tenga cargado:**
  `CANASTAMX_PRUEBA_POSTGRES=1 python -m pytest services/analytics-api/tests/test_postgres.py -v -s`
- **De punta a punta contra el dominio**, que tiene que estar corriendo, con las cuentas de
  `infra/scripts/sembrar-cuentas.sh`:
  `CANASTAMX_PRUEBA_DOMINIO=1 python -m pytest services/analytics-api/tests/test_dominio.py -v -s`

Ninguna imprime tokens ni contraseñas.
