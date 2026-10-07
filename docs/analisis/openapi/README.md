# Contratos OpenAPI · T037

| Archivo | Servicio | Lo escribe | Lo aprueban en el PR |
|---|---|---|---|
| `dominio.yaml` | `services/domain-service` | C1, con B | C2 y D |
| `analitica.yaml` | `services/analytics-api` | A, con B | D, C2 y C1 |

**Son borradores** (versión `0.1.0-borrador`), armados el 6 de octubre de 2026 con
lo que ya está en `main`: los 14 casos de uso, el inventario de vistas, el modelo
ER, el modelo dimensional y el código del dominio. Cada ruta dice de qué caso de
uso sale. Lo que todavía no está decidido va con la opción propuesta, marcado con
`x-pendiente` y con su número de la lista de abajo.

## Cómo se revisan

```bash
# 1 · Que son OpenAPI válidos: 0 errores
npx @redocly/cli lint docs/analisis/openapi/*.yaml

# 2 · Que la app y la web ya pueden construir contra ellos
npx @stoplight/prism-cli mock docs/analisis/openapi/dominio.yaml -p 4010
curl http://127.0.0.1:4010/health
```

Hoy el validador da **0 errores y 5 avisos esperados**: los servidores apuntan a
`localhost` porque son de desarrollo, y `/health` y `/entidades` no tienen
respuestas 4XX porque no reciben datos.

---

## Lo que ya está decidido

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
| R-10 | ¿Alertas? | Umbral dentro del rango histórico (mínimo y máximo de las medianas quincenales). Se dispara con «menor o igual». Sigue activa después de avisar | T031 · modelo ER (#137) |
| R-11 | ¿Notificaciones? | Cada intento se registra con `ENVIADA` o `FALLIDA`, y su fecha y hora | CU-11 · modelo ER |
| R-12 | ¿Entidades y catálogos? | Las 7 entidades y los 5 catálogos del contrato | Contrato 1.3.3 |
| R-13 | ¿Salud del dominio? | `GET /health` en el 8081, fuera de `/api/v1` | `HealthController.java` |
| R-14 | ¿La interfaz analítica escribe en la capa de consumo? | No | Protocolo §10.4 · propuesta |
| R-15 | ¿Dónde vive la canasta del invitado? | En el teléfono, hasta que inicia sesión. No hay rutas anónimas en el dominio; su costo lo calcula `POST /api/v1/canastas/costo` | D-04 · CU-09, alterno 1a |
| R-16 | ¿La alerta vuelve a avisar mientras el precio siga abajo? | No. Avisa al cruzar el umbral hacia abajo y se vuelve a armar cuando sube; la alerta guarda su `posicion` (`ARRIBA` o `DEBAJO`) | D-05 · CU-11 · `navegacion.md` §3 |

## Lo que falta decidir

| # | Pregunta | Opciones | Propuesta | Decide |
|---|---|---|---|---|
| P-01 | ¿Cómo se escriben los campos? | **A** `camelCase` (`precioTipico`): el natural de Java y TypeScript · **B** `snake_case` (`precio_tipico`): el natural de Python | A | Todos |
| P-02 | ¿Cómo viaja el dinero? | **A** Texto con moneda: `{"monto": "24.50", "moneda": "MXN"}` · **B** Número: `24.5` | A, para no perder centavos | Todos |
| P-03 | ¿Formato de error? | **A** `application/problem+json` (RFC 9457), el que trae Spring Boot · **B** Uno propio | A | B |
| P-04 | ¿Versión en la ruta? | **A** `/api/v1/…`, con `/health` fuera · **B** Sin versión | A | B |
| P-05 | ¿Paginación? | **A** `limit` y `offset`; máximo 100 y 20 por omisión · **B** Por cursor | A | B |
| P-06 | ¿Qué responde una entidad sin cobertura? | **A** 200 con `cobertura: false` y las 7 entidades cubiertas, porque es el alterno 2b de CU-12 · **B** Un error 404 | A | C2 y A |
| P-07 | ¿Cómo entran el analista y el operador a la web? | **A** El dominio les da sesión con un rol (consumidor, analista u operador): cambia `USUARIO` · **B** Cuentas fijas por configuración · **C** Sin sesión, sólo para la demostración | A | C1, D y B |
| P-08 | ¿Quién escribe las acciones de la consola (cerrar un incidente, resolver una variante)? | **A** La interfaz analítica, en un esquema de operación aparte de la capa de consumo: siguen siendo dos contratos · **B** Una API de operación en la plataforma de datos: tres contratos | A | A y B |
| P-09 | ¿El dominio consulta a la interfaz analítica para las alertas? | **A** Sí, para el rango histórico y los precios vigentes: es lectura de servicio a servicio, y se corrige la propuesta, que dice que no se llaman · **B** Las alertas se evalúan en la plataforma de datos, que llama al dominio para notificar | A | C1 y A |
| P-10 | ¿Quién calcula el costo de la canasta? | **A** La interfaz analítica: recibe las líneas y no guarda nada, así que sirve también para la canasta del invitado · **B** El dominio, llamando a la analítica · **C** La app, con los precios | A, para que la regla de «sin precio» viva en un solo lugar | A, C1 y C2 |
| P-13 | ¿El usuario tiene nombre? | **A** Sí: se pide al registrarse, y cambian CU-08 y `Usuario.java` · **B** No: se quita del modelo ER | — | C1 |
| P-14 | ¿De qué entidad es el precio que vigila una alerta? | **A** La alerta guarda su entidad: hoy el modelo ER no la tiene · **B** El usuario guarda una entidad | A, porque el rango histórico es por entidad | C1 |
| P-15 | ¿Qué es un artículo «anómalo» en el tablero? | **A** Una variación quincenal de su mediana mayor a un umbral, por ejemplo 20% · **B** Fuera del rango intercuartílico de su historia · **C** Lo que marque la compuerta fina de precio, que está pendiente | — | A y D |

La canasta del índice (D-02) también afecta a `GET /api/v1/indice`.

## Inconsistencias que salieron al armar los contratos

| Qué | Dónde | Quién |
|---|---|---|
| CU-11 pide guardar el **motivo** de una notificación fallida, y la tabla `NOTIFICACION` no tiene esa columna | Modelo ER | C1 |
| `USUARIO.nombre` es obligatorio en el modelo ER, pero CU-08 no lo pide y `Usuario.java` no lo tiene | Modelo ER · CU-08 · código | C1 (P-13) |
| `ALERTA` no guarda entidad, pero el rango y el precio vigente son por entidad | Modelo ER | C1 (P-14) |
| La propuesta dice que la interfaz analítica tiene «cuatro endpoints de sólo lectura»; los casos de uso piden más, y dos escrituras de la consola | Propuesta · CU-04 · CU-14 | A (P-08) |
| La propuesta dice que el dominio y la analítica «no se llaman entre sí»; CU-10 y CU-11 necesitan que el dominio consulte a la analítica | Propuesta · CU-10 · CU-11 | A y C1 (P-09) |
