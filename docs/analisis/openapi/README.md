# Contratos OpenAPI · T037

| Archivo | Servicio | Versión | Lo publica | Lo consumen |
|---|---|---|---|---|
| `dominio.yaml` | `services/domain-service` | 0.2.0 | C1, con B | C2 (app) y D (acceso web) |
| `analitica.yaml` | `services/analytics-api` | 0.2.1 | A, con B | C2 (app), D (web) y C1 (alertas) |

**La versión 0.2 es la revisada por el equipo el 7 de octubre de 2026.** Cada ruta dice
de qué caso de uso sale. Ya no quedan marcas `x-pendiente`. En la analítica, cada ruta
protegida dice en `x-rol` qué rol pide.

## Cómo se revisan

```bash
# 1 · Que son OpenAPI válidos (lee solo el redocly.yaml de la raíz)
npx @redocly/cli lint docs/analisis/openapi/*.yaml

# 2 · Que la app y la web ya pueden construir contra ellos
npx @stoplight/prism-cli mock docs/analisis/openapi/dominio.yaml -p 4010
curl http://127.0.0.1:4010/health
```

Hoy el validador da **0 errores y 5 avisos esperados**:
- **2 avisos:** los servidores apuntan a `localhost` porque son de desarrollo;
- **3 avisos:** `/health` (en los dos contratos) y `/entidades` no tienen respuestas 4XX, porque no reciben datos.

---

## Decidido antes de la revisión

| # | Pregunta | Respuesta | Dónde se decidió |
|---|---|---|---|
| R-01 | ¿Cuántos contratos? | **Dos.** La plataforma de datos no expone API; el estado de las corridas lo sirve la interfaz analítica | Propuesta entregada (E1), §5 |
| R-02 | ¿Cómo viaja un artículo? | **Por su par canónico**, en dos campos: `producto` y `presentacion`. Nunca por `articulo_key` | `ReferenciaDeArticulo.java` · modelo ER · T031 §9 |
| R-03 | ¿Fechas? | ISO 8601. La quincena, como `2026-07-Q2` | Ingesta · T031 |
| R-04 | ¿Población en las cifras? | Toda cifra agregada dice entidades, periodo y observaciones | Convenio del equipo · T031 |
| R-05 | ¿Autenticación? | Token JWT portador | `JWT_SECRET` en `.env.example` |
| R-06 | ¿Qué pide sesión en la app? | Buscar y ver precios, no (modo invitado). Canastas y alertas, sí | Inventario de vistas · duda 2 |
| R-07 | ¿Contraseña? | Mínimo 8 caracteres, una mayúscula y un número; se guarda con BCrypt | CU-08 · `Usuario.java` |
| R-08 | ¿Canasta? | Un solo dueño. Una línea por artículo: agregar uno repetido **suma** la cantidad. Cantidad entera mayor que cero. El costo no se guarda | Modelo ER · `Canasta.java` · CU-09 6b |
| R-09 | ¿Precio por cadena en Mi canasta? | Mediana de sus tiendas en la entidad, en la quincena más reciente. Sin dato, `null`, y el total dice cuántos faltan | T031 |
| R-10 | ¿Alertas? | Umbral dentro del rango histórico (mínimo y máximo de las medianas quincenales). Se dispara con «menor o igual», sólo al cruzar el umbral hacia abajo (D-05). Sigue activa después de avisar | T031 · modelo ER (#137) |
| R-11 | ¿Notificaciones? | Cada intento se registra con `ENVIADA` o `FALLIDA`, y su fecha y hora | CU-11 · modelo ER |
| R-12 | ¿Entidades y catálogos? | Las 7 entidades y los 5 catálogos del contrato | Contrato 1.3.3 |
| R-13 | ¿Salud del dominio? | `GET /health` en el 8081, fuera de `/api/v1` | `HealthController.java` |
| R-14 | ¿La interfaz analítica escribe en la capa de consumo? | No | Protocolo §10.4 · propuesta |
| R-15 | ¿Dónde vive la canasta del invitado? | En el teléfono, hasta que inicia sesión. No hay rutas anónimas en el dominio; su costo lo calcula `POST /api/v1/canastas/costo` | D-04 · CU-09, alterno 1a |
| R-16 | ¿La alerta vuelve a avisar mientras el precio siga abajo? | No. Avisa al cruzar el umbral hacia abajo y se vuelve a armar cuando sube; la alerta guarda su `posicion` (`ARRIBA` o `DEBAJO`) | D-05 · CU-11 · `navegacion.md` §3 |

## Decidido en la revisión del 7 de octubre

| # | Pregunta | Decisión | Quién |
|---|---|---|---|
| P-01 | ¿Cómo se escriben los campos? | **`camelCase`** | Todo el equipo, por unanimidad |
| P-02 | ¿Cómo viaja el dinero? | **Texto con moneda:** `{"monto": "24.50", "moneda": "MXN"}`. Para sumar o comparar se pasa a centavos enteros o a decimal exacto, **nunca a punto flotante** | Todo el equipo, por unanimidad |
| P-03 | ¿Formato de error? | **`application/problem+json`** (RFC 9457) | B |
| P-04 | ¿Versión en la ruta? | **`/api/v1/…`**, con `/health` fuera | B |
| P-05 | ¿Paginación? | **`limit` y `offset`**; máximo 100 y 20 por omisión | B |
| P-06 | ¿Entidad sin cobertura? | **200 con `cobertura: false`** y las 7 entidades cubiertas | Todo el equipo, por unanimidad |
| P-07 | ¿Cómo entran el analista y el operador? | **Sesión con rol** (`CONSUMIDOR`, `ANALISTA` u `OPERADOR`), emitida por el dominio. La app sólo crea consumidores | A, C1 y D |
| P-08 | ¿Quién escribe las acciones de la consola? | **La analítica, en un esquema de operación** aparte de la capa de consumo. Siguen siendo dos contratos | A, C1 y D |
| P-09 | ¿El dominio consulta a la analítica? | **Sí,** con dos rutas de sólo lectura: el rango histórico y los precios vigentes | A, C1, C2 y D |
| P-10 | ¿Quién calcula el costo de la canasta? | **La analítica,** con `POST /api/v1/canastas/costo` | A, C1 y D |
| P-13 | ¿El usuario tiene nombre? | **No:** se quita del modelo ER, y la cuenta se identifica con su correo | C1 |
| P-14 | ¿De qué entidad es el precio de una alerta? | **La alerta guarda su entidad:** la elegida en la app al crearla | C1 |
| P-15 | ¿Qué es un artículo «anómalo»? | **Variación quincenal del precio típico mayor al 20%**, en valor absoluto. Se calibra con el volumen real | A y D |

## Correcciones que salieron de la revisión

| Observación | De quién | Qué cambió |
|---|---|---|
| CU-11 tiene tres estados de notificación y el contrato dos | C1 | `Notificacion.estado`: `PENDIENTE`, `ENVIADA` o `FALLIDA` |
| La notificación no trae la alerta | C1 | `Notificacion.alertaId` |
| CU-10 no dice en qué posición nace la alerta | C1 | `posicion` es null mientras no se revisa; la primera revisión cuenta como si estuviera arriba |
| La cola no trae la cobertura del diccionario | D | La cola trae `cobertura` **y `precision`**, cada una con su población, como pide el prototipo |
| El aviso de Inicio no sabía qué cruces eran nuevos | Revisión de A | `Alerta.ultimoCruce` |
| RF-13 registra también los avisos | Requerimientos | `Incidente.severidad` (`AVISO` o `INCIDENTE`). Los avisos no se cierran (409) |
| ADR 015 pide que el índice diga cómo se calculó | ADR 015 | `IndiceContraInpc.canasta`: artículos, base y fórmula |
| El esquema de operación fija los motivos, el cierre y la cola | `docs/datos/esquema-de-operacion.md` | **0.2.1:** los 8 motivos de fila del catálogo; los avisos son `INFORMATIVO`; el cierre guarda quién y si se reprocesa el lote; la variante trae su cadena y su resolución |

## Nuevo, a confirmar por A y D

**Mínimo de observaciones en los anómalos.** Un artículo con dos observaciones puede
«subir 50%» sólo porque cambió una tienda. Por eso cuenta como anómalo sólo si tiene al
menos 5 observaciones en cada una de las dos quincenas (`minimoDeObservaciones`). El
número se calibra junto con el 20%.

## Lo que estos contratos piden a otros documentos

| Qué | Dónde | Quién |
|---|---|---|
| `rol` en `USUARIO`, sin `nombre`. En `ALERTA`: `entidad`, `posicion`, `ultima_revision` y `ultimo_cruce`. `motivo` y tres estados en `NOTIFICACION` | Modelo ER, modelo de dominio y CU-09 a CU-11 | C1 |
| La compuerta del cruce: «¿estaba arriba o es su primera revisión?» | `bpmn/alertas.bpmn` | C1 |
| La propuesta dice que el dominio y la analítica «no se llaman entre sí» y que la analítica tiene «cuatro endpoints de sólo lectura» | Documento de la entrega 2 | A |
| Cuenta muestra el correo, no un nombre. La cola muestra cobertura y precisión con su población, o «se mide en T058» | Prototipo | D y C2 |
