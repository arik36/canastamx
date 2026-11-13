# Interfaz analítica · `analytics-api`

FastAPI (ADR 017). Lee `postgres-analytics` y verifica el token que emite el dominio
(ADR 020). Contrato: `docs/analisis/openapi/analitica.yaml` 0.2.1.

| Ruta | `operationId` | Sesión | Lee |
|---|---|---|---|
| `GET /api/v1/entidades` | `listarEntidades` | no | capa intermedia |
| `GET /api/v1/articulos` | `buscarArticulos` | no | capa intermedia |
| `GET /api/v1/precios` | `compararPrecios` | no | capa intermedia |
| `GET /api/v1/articulos/establecimientos` | `desgloseDeArticulo` | `x-rol: ANALISTA` | capa intermedia |
| `POST /api/v1/canastas/costo` | `costearCanasta` | no | estrella |
| `GET /api/v1/anomalias` | `articulosAnomalos` | `x-rol: ANALISTA` | estrella |
| `GET /api/v1/articulos/serie` | `serieDeArticulo` | `x-rol: ANALISTA` | estrella |
| `GET /api/v1/operacion/estado` | `estadoDeLaPlataforma` | `x-rol: OPERADOR` | operación |
| `GET /api/v1/operacion/corridas` | `listarCorridas` | `x-rol: OPERADOR` | operación |
| `GET /api/v1/operacion/corridas/{lote}` | `linajeDeLote` | `x-rol: OPERADOR` | operación |
| `GET /api/v1/operacion/cuarentena` | `listarCuarentena` | `x-rol: OPERADOR` | operación |
| `GET /api/v1/operacion/incidentes` | `listarIncidentes` | `x-rol: OPERADOR` | operación |
| `POST /api/v1/operacion/incidentes/{incidenteId}/cierre` | `cerrarIncidente` | `x-rol: OPERADOR` | **escribe** en operación |

Las cuatro primeras son de T058 y buscan el artículo por `clave_producto` y
`clave_presentacion` de la capa intermedia (T048). Las nueve de T069 leen la estrella
de T053 (esquema `consumo`) y el esquema de operación de T064 (esquema `operacion`).
Con otro rol o sin token, una ruta con `x-rol` responde 401 `SinSesion`.

## Lo que hay que saber de las nueve de T069

- **`cerrarIncidente` es la única escritura** (P-08), y va al esquema de operación.
  Guarda la causa, la decisión, la fecha, que pone la base, y el correo de quien
  cerró (D-11, RNF-22). El correo no viene en el token ni se acepta en el cuerpo: se
  le pregunta al dominio con el mismo token, en `GET /api/v1/cuentas/yo` (D-10). Si el
  dominio no contesta, responde 503 y no cierra nada. Un aviso, o un incidente ya
  cerrado, responde 409.
- **Sin corridas, `estadoDeLaPlataforma` responde 404** `SinDatos`, en lugar de cifras
  en cero (CU-05 · 2b). Sus indicadores salen de la vista
  `operacion.estado_de_la_plataforma`.
- **`listarCuarentena` trae lo que apartó la corrida vigente de cada lote**: su total
  es el del indicador de la consola.
- **`linajeDeLote` trae las corridas del lote en orden**, y la última es la vigente
  (CU-05 · 5a).
- **`costearCanasta`**: cantidad por la mediana de las tiendas de la cadena, en la
  quincena más reciente de la entidad (R-09). Sin precio es `null`, no entra al total
  y se cuenta en `faltan`. Primero van las cadenas a las que les faltan menos
  artículos y, entre ellas, la más barata.
- **`articulosAnomalos`** compara la mediana de cada artículo en cada entidad con la
  de la quincena de calendario anterior (P-15). Van de la quincena más reciente a la
  más antigua y, en cada una, la mayor variación primero. Fuera del alcance responde
  200 con la lista vacía y la población en cero.
- **`serieDeArticulo`**: cada punto lleva su quincena, su entidad y sus observaciones.

## Correrla

Desde la raíz, con el `.env` cargado. Usa `JWT_SECRET` y las `ANALYTICS_*`. Dos son
opcionales: `ANALYTICS_HOST`, que por omisión es `localhost`, y `DOMINIO_URL`, dónde
corre el dominio para `cerrarIncidente`, que por omisión es `http://localhost:8081`.

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

Las demás corren sólo si se piden, con el `.env` cargado:

- **Contra `postgres-analytics`, con lo que tenga cargado.** Sólo lee. Imprime los seis
  indicadores de CU-05, y cuántos artículos marca P-15 con el volumen real:
  `CANASTAMX_PRUEBA_POSTGRES=1 python -m pytest services/analytics-api/tests/test_postgres.py -v -s`
- **El cierre de un incidente, contra la base.** Escribe: mete una corrida y un
  incidente de prueba en el esquema de operación, lo cierra y los borra. Mientras
  corre, la consola los vería: va contra una base de pruebas, no la del despliegue.
  `CANASTAMX_PRUEBA_CIERRE=1 python -m pytest services/analytics-api/tests/test_postgres.py -v -s`
- **De punta a punta contra el dominio**, que tiene que estar corriendo, con las cuentas de
  `infra/scripts/sembrar-cuentas.sh`:
  `CANASTAMX_PRUEBA_DOMINIO=1 python -m pytest services/analytics-api/tests/test_dominio.py -v -s`

Ninguna imprime tokens ni contraseñas.
