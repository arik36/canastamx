# Manual técnico del servicio de dominio

T078 · C1 · #220. Revisión documental del 26 de noviembre de 2026, sobre la base
`7c9414160cbc110d72763f3ae87915b4d98d81d2`. Su operación se describe en el
[manual de operación](manual-de-operacion.md).

## Alcance y fuentes

El servicio Java mantiene cuentas, emite sesiones y guarda canastas en PostgreSQL.
El costo de una canasta lo calcula la interfaz analítica; no se almacena en dominio.
El código implementa CU-08 y las ocho operaciones de canasta de CU-09.

Fuentes para continuar el trabajo:

- [README del servicio](../../services/domain-service/README.md).
- [Contrato OpenAPI de dominio 0.2.2](../analisis/openapi/dominio.yaml) y
  [convenciones del contrato](../analisis/openapi/README.md).
- [CU-08](../analisis/casos-uso/CU-08-registrar-cuenta.md),
  [CU-09](../analisis/casos-uso/CU-09-crear-canasta.md),
  [modelo de dominio](../analisis/modelo-dominio.md) y [modelo ER](../analisis/modelo-er.md).
- [ADR 020](../adr/020-token-de-sesion.md),
  [decisiones del equipo](../equipo/decisiones-pendientes.md) y
  [recorte del producto](../equipo/cronograma.md).
- [Código y pruebas](../../services/domain-service/src).

Las rutas de alertas y notificaciones aún aparecen en OpenAPI y en CU-10/CU-11,
pero no están implementadas: salieron del producto con el recorte del 5 de noviembre.
No deben presentarse como funciones disponibles ni como trabajo de T078.

Este manual y el de operación atienden la documentación de continuidad indicada
en la ficha de T078. La correspondencia con el texto completo del protocolo de
investigación queda pendiente de cotejo cuando esté disponible. No son el
documento de traspaso de T083 ni dependen de las corridas del experimento.

## Organización del código

Paquete base: `mx.tecnm.canastamx.domain_service`, bajo
`services/domain-service/src/main/java/`.

| Paquete o lugar | Responsabilidad |
|---|---|
| `DomainServiceApplication` | Punto de arranque de Spring Boot. |
| `domain.canasta` | `Canasta`, `LineaDeCanasta`, `Cantidad` y `ReferenciaDeArticulo`; reglas de artículos y cantidades sin HTTP ni acceso a base. |
| `domain.usuario` | `Usuario`, `CorreoElectronico` y los tres valores de `Rol`. |
| `application.service` | Registro, inicio de sesión, resolución de cuenta y operaciones transaccionales de canastas. |
| `infrastructure.persistence` | Repositorios con `JdbcTemplate` para PostgreSQL; no se delega la persistencia a entidades JPA. |
| `infrastructure.web` | Controladores, DTO, validación de entrada, resolución de `@CuentaDeLaSesion` y errores `ProblemDetail`. |
| `infrastructure.security` | `JwtService`: firma y verificación de sesiones según ADR 020. |
| `infrastructure.config` | `WebConfig` registra el resolutor de cuenta; `SeguridadConfig` proporciona BCrypt. |
| `src/main/resources/db/migration` | Migraciones Flyway V1 a V3. |
| `src/test/java` | Pruebas de entidades, aplicación, contrato, seguridad y operaciones HTTP con PostgreSQL. |

Una petición protegida pasa por `CuentaDeLaSesionResolver`: extrae Bearer,
`CuentaDeLaSesionService` verifica el token y busca la cuenta actual.
Sólo entonces se invoca el controlador. No basta con que el token esté bien firmado:
la cuenta debe seguir existiendo.

## Reglas de canasta y pruebas que las cuidan

Los métodos de la tabla pertenecen a
[`CanastaTest`](../../services/domain-service/src/test/java/mx/tecnm/canastamx/domain_service/domain/canasta/CanastaTest.java).

| Regla | Prueba |
|---|---|
| Dos escrituras normalizadas de producto y presentación identifican el mismo artículo. | `dos_escrituras_del_mismo_articulo_son_el_mismo_articulo` |
| Agregar un artículo existente suma cantidades y conserva una línea. | `agregar_dos_veces_el_mismo_articulo_suma_cantidades` |
| Quien consulta las líneas no puede modificar la colección. | `desde_afuera_no_se_modifican_las_lineas` |
| La cantidad es un entero mayor que cero. | `la_cantidad_tiene_que_ser_mayor_que_cero` |
| Fijar reemplaza la cantidad; no agrega un artículo ausente. | `fijar_cantidad_reemplaza_y_no_agrega_articulos_inexistentes` |
| Quitar un artículo ausente avisa y no cambia la canasta. | `quitar_articulo_inexistente_no_modifica_la_canasta` |
| Normalizar antes de validar rechaza textos que quedan vacíos, como sólo signos. | `referencia_rechaza_texto_que_queda_vacio_al_normalizar` |
| Una cantidad nula se rechaza con o sin línea previa. | `agregar_rechaza_cantidad_nula_con_y_sin_linea_previa` |
| La suma no desborda el entero ni deja la línea modificada si falla. | `suma_no_desborda_la_cantidad_ni_modifica_la_linea` |

`ReferenciaDeArticulo` usa producto y presentación, no marca: elimina acentos y
signos, convierte a minúsculas y compacta espacios antes de exigir contenido.
`Canasta` exige identificador, dueño y nombre no vacíos; renombrar recorta el nombre.
No se atribuye cobertura total a estas validaciones: T055 registra ramas sin cubrir.

En integración, [`CanastasTests`](../../services/domain-service/src/test/java/mx/tecnm/canastamx/domain_service/CanastasTests.java)
comprueba las ocho operaciones, el dueño, las cantidades, los errores y el borrado:

- `ochoOperacionesPersistenYRespetanElContrato`.
- `canastaAjenaONoExistenteEs404EnLasSeisOperaciones`.
- `fijarOQuitarArticuloAusenteNoCambiaLaCanasta`.
- `ochoOperacionesSinSesionSonProblem401`.
- `validaEntradasYPaginacionSinModificarDatos`.
- `borrarCanastaEliminaSusLineas`.

El dueño siempre sale de la sesión. Una canasta ajena se trata como inexistente,
con 404. Las modificaciones bloquean su fila mediante `SELECT … FOR UPDATE`
dentro de la transacción del servicio para serializar los cambios.

## Reglas de cuenta y pruebas que las cuidan

| Regla | Prueba existente |
|---|---|
| El correo se recorta y se guarda en minúsculas; se rechaza formato inválido. | `UsuarioTest.el_correo_se_guarda_normalizado` y `no_acepta_correos_con_formato_invalido`. |
| `Usuario` exige un hash con prefijo BCrypt, no una contraseña en texto plano. | `UsuarioTest.no_acepta_contrasena_en_texto_plano`. |
| La cuenta tiene rol y no tiene campo ni métodos de nombre. | `UsuarioTest.el_usuario_tiene_rol`, `el_usuario_no_tiene_atributo_nombre` y `el_usuario_no_expone_metodos_nombre_ni_renombrar`. |
| El registro valida el correo y la contraseña; el correo repetido responde 409. | `ErroresDelContratoTests.registrarConCorreoInvalidoDevuelve400`, `registrarConContrasenaQueNoCumpleLaReglaDevuelve400` y `registrarDosVecesElMismoCorreoDevuelve409`. |
| La respuesta no expone la contraseña y el token incluye el rol. | `AutenticacionTests.respuestaDeCuentaNoExponeLaContrasena` y `tokenIncluyeElRolDelUsuario`. |
| Cuenta y sesión conservan los campos y tipos del contrato. | `ContratoOpenApiEsquemasTest`: esquemas `Registro`, `Credenciales`, `Cuenta`, `Sesion` y `Rol`. |

La API de registro admite contraseñas de 8 a 72 caracteres con al menos una
mayúscula y un número. `RegistroCuentaService` cifra con BCrypt y crea siempre
`CONSUMIDOR`; `ANALISTA` y `OPERADOR` se crean por la semilla, no eligiendo rol
desde la app. La respuesta de cuenta sólo contiene `id`, `correo`, `rol` y
`fechaDeRegistro`.

## Rutas implementadas y contrato

La tabla resume [`dominio.yaml`](../analisis/openapi/dominio.yaml); allí están
los esquemas de cuerpos y parámetros. Las respuestas exitosas con cuerpo son
`application/json`; los errores descritos por estas operaciones usan
`application/problem+json`, con `type`, `title` y `status`.

| Método y ruta | Sesión | Éxito | Errores declarados |
|---|---|---|---|
| `GET /health` | Pública | 200 | No declara 4XX. |
| `POST /api/v1/cuentas` | Pública | 201 | 400, 409 |
| `POST /api/v1/sesiones` | Pública | 200 | 401 |
| `GET /api/v1/cuentas/yo` | Bearer | 200 | 401 |
| `GET /api/v1/canastas` | Bearer | 200 | 400, 401 |
| `POST /api/v1/canastas` | Bearer | 201 | 400, 401 |
| `GET /api/v1/canastas/{canastaId}` | Bearer | 200 | 401, 404 |
| `PATCH /api/v1/canastas/{canastaId}` | Bearer | 200 | 400, 401, 404 |
| `DELETE /api/v1/canastas/{canastaId}` | Bearer | 204, sin cuerpo | 401, 404 |
| `POST /api/v1/canastas/{canastaId}/lineas` | Bearer | 200 | 400, 401, 404 |
| `PUT /api/v1/canastas/{canastaId}/lineas` | Bearer | 200 | 400, 401, 404 |
| `DELETE /api/v1/canastas/{canastaId}/lineas` | Bearer | 200 | 400, 401, 404 |

Crear y renombrar reciben `nombre`. Agregar y fijar reciben
`articulo: {producto, presentacion}` y `cantidad` entera; quitar recibe
`producto` y `presentacion` como parámetros de consulta.
La respuesta de canasta tiene `id`, `nombre` y `lineas`, sin dueño ni costo.
Listar devuelve `canastas` y `total`, con paginación `limit` y `offset`.

`RutasProtegidasTests` compara la seguridad declarada con los parámetros
`@CuentaDeLaSesion` de las rutas realmente implementadas. No convierte las rutas
de alertas del contrato en funcionalidad disponible.

## D-12 y ADR 020

**D-12, opción B**, votada por C1, C2 y D el 2 de noviembre de 2026:
el 401 de `POST /api/v1/sesiones` queda sin `WWW-Authenticate` como excepción
explícita. Recibe correo y contraseña en el cuerpo y no acepta Bearer; anunciarlo
nombraría un mecanismo que esa ruta no acepta. Credenciales inexistentes,
incorrectas o ilegibles producen el mismo tipo de error, sin revelar cuál falló.

Los 401 de las rutas protegidas sí llevan `WWW-Authenticate: Bearer`;
si llegó un token que no sirve, agregan `error="invalid_token"`.
Las pruebas `ErroresDelContratoTests`, `SesionControllerTest`,
`CuentaDeLaSesionTests` y `ExpiracionDeSesionTests` cuidan estos casos.

**ADR 020**, aceptado el 7 de noviembre de 2026:

- Sólo HS256 al emitir y verificar.
- `JWT_SECRET` contiene Base64 estándar de exactamente 32 bytes aleatorios;
  la clave son los bytes decodificados, no el texto Base64.
- Claims obligatorios: `sub` (id de cuenta), `rol`, `iat` y `exp`.
  No hay tolerancia de reloj.
- `JWT_EXPIRATION_MINUTES` debe ser mayor que cero. Rotar la clave invalida las
  sesiones anteriores y requiere iniciar sesión otra vez.
- La analítica verifica el token para `x-rol` desde T058 (#199).

`JwtServiceTest` comprueba algoritmo, clave, claims, expiración y rechazo uniforme.
`CuentaDeLaSesionServiceTest` comprueba además la existencia actual de la cuenta.
El ADR conserva párrafos históricos de propuesta; su estado aceptado, el contrato
0.2.2 y la implementación son las referencias para el funcionamiento actual.

## Persistencia y migraciones

Flyway aplica al arrancar las migraciones de
[`db/migration`](../../services/domain-service/src/main/resources/db/migration):

- V1 crea `usuario`: identificador, correo único, hash, rol y fecha.
- V2 crea `canasta` y `linea_canasta`. La llave de línea es
  `(canasta_id, producto, presentacion)`; `cantidad` es `NOT NULL` y positiva.
  Borrar la canasta elimina sus líneas por cascada.
- V3 amplía los campos según el contrato y agrega el índice por dueño.

No se edita una migración ya aplicada: cualquier evolución exige otra migración.
Las consultas filtran por dueño; el bloqueo y la transacción preceden a la
reescritura de líneas. Las pruebas de integración que escriben datos usan
`@Transactional` y rollback; no son un procedimiento para limpiar datos antiguos.

## Cobertura medida: T055 (#202)

[La solicitud #231](https://github.com/arik36/canastamx/pull/231) registra esta
**medición histórica local**, sobre el commit base
`cd9ff7b4e93da41a14d20248dab3f23e91513c65` con los cambios de T055 aplicados:

| Indicador | Resultado |
|---|---|
| Suite completa | 76 pruebas, 0 fallos, 0 errores, 0 omitidas. |
| Líneas | 91/101: 90.10 %. |
| Ramas | 37/54: 68.52 %. |
| Clases sin líneas ejecutadas | Ninguna. |

Población: ocho clases compiladas de `domain.canasta` y `domain.usuario`:
`Canasta`, `Canasta.ArticuloNoExisteException`, `Cantidad`, `LineaDeCanasta`,
`ReferenciaDeArticulo`, `CorreoElectronico`, `Rol` y `Usuario`.
La ejecución medida es la suite completa, incluidas pruebas de integración.
No entran controladores, aplicación, persistencia ni seguridad al porcentaje;
no es la cobertura de todo el servicio. No hay umbral mínimo configurado.

`Canasta`, `LineaDeCanasta`, `ReferenciaDeArticulo`, `CorreoElectronico` y
`Usuario` tienen cobertura parcial. Estas cifras no certifican el checkout actual
ni son una medición nueva de T078. La descripción de #231 dejó la cifra de CI
pendiente; no se presenta como medición remota.

Para volver a medir con PostgreSQL configurado, desde `services/domain-service`:

```bash
mvn -B clean test -DfailIfNoTests=true
python scripts/resumir_cobertura.py
```

JaCoCo 0.8.16 genera `target/site/jacoco/index.html` y `jacoco.csv`.
El script cruza los contadores con Surefire, escribe
`target/cobertura-dominio.md`, informa el SHA y avisa si hay cambios sin commit.
El trabajo «Dominio (Java)» de
[CI](../../.github/workflows/ci.yml) también publica el resumen y el artefacto
`cobertura-dominio-<SHA>`. Una evidencia nueva debe incluir el SHA,
la población y el total de pruebas de esa corrida.

## Seguimiento del README y Javadoc de #185

T050 (#188) se integró mediante [#226](https://github.com/arik36/canastamx/pull/226).
La comprobación de T078 sobre los archivos actuales deja este resultado:

| Archivo, relativo al servicio salvo indicación | Qué quedó |
|---|---|
| `README.md` | Alcance de cuentas, sesiones y canastas, pruebas con conteo, configuración local, cobertura y listado explícito del seguimiento de #185. |
| `docs/analisis/openapi/README.md`, desde la raíz | Distingue rutas contratadas e implementadas, sumar frente a fijar, sesión y errores. |
| `domain/canasta/ReferenciaDeArticulo.java` | Javadoc: identidad producto/presentación, normalización antes de validar. |
| `domain/canasta/Canasta.java` | Javadoc: agregar suma, fijar reemplaza sin crear ausentes y quitar avisa si no existe. |
| `infrastructure/web/CuentaDeLaSesion.java` | Explica la cuenta resuelta de la sesión y el error uniforme. |
| `RutasProtegidasTests.java`, bajo `src/test/java` | Documenta el cotejo del contrato con las rutas implementadas; alertas siguen fuera. |
| `infrastructure/security/JwtService.java` | Describe la clave decodificada y HS256; T055 (#231) alineó el Javadoc con el ADR aceptado. |
| `infrastructure/web/SinSesionHandler.java` | T071 (#236) declaró la excepción D-12. |
| `docs/analisis/openapi/dominio.yaml`, desde la raíz | T071 (#236) declaró D-12 y actualizó las dos referencias al ADR 020 aceptado. |

Las rutas `domain/` e `infrastructure/` de esta tabla parten de
`src/main/java/mx/tecnm/canastamx/domain_service/`.
El README conserva la frase histórica «queda para T071»: al cotejarla con #236
y los archivos actuales se comprueba que ese pendiente ya se atendió.
T078 deja constancia; no reabre ni cambia la implementación de aquellas tareas.
