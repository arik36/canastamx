# Servicio de dominio

Cuentas, sesiones y las ocho operaciones de canastas. Las rutas de alertas todavía
no están implementadas. El contrato es
`docs/analisis/openapi/dominio.yaml`; el token, el ADR 020.

## Configuración: el `.env` de la raíz

`application.properties` importa `../../.env`. La ruta es relativa al **directorio de
trabajo**, así que el servicio y sus pruebas se corren desde `services/domain-service`.
En un IDE, la configuración de ejecución tiene que usar esa misma carpeta como
directorio de trabajo; si no, el `.env` no se encuentra, se omite sin avisar y aparece
`${OLTP_USER}` literal.

- **Las variables del entorno ganan sobre el archivo.** Si en una terminal quedó
  exportada `JWT_SECRET` u `OLTP_DB` con otro valor —o, en Windows, como variable de
  usuario—, se usa ésa. `ConfiguracionLocalTest` hace fallar la suite cuando pasa,
  y dice cuál, sin mostrar el valor. Sin `.env`, como en la CI, no aplica.
- **El formato tiene que ser el que leen igual Compose y Spring:** `CLAVE=valor`, sin
  comillas, sin `export` y sin comentarios al final de la línea. Desde la raíz:
  `python3 infra/scripts/revisar-env.py --entorno`, que tampoco muestra valores.
- **`JWT_SECRET`** es Base64 de 32 bytes aleatorios (ADR 020). En Linux, WSL o Git
  Bash: `openssl rand -base64 32`. En PowerShell:

  ```powershell
  $b = New-Object byte[] 32
  [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b)
  [Convert]::ToBase64String($b)
  ```

  Con otra cosa, el servicio no arranca, y el mensaje dice por qué. Al cambiar de
  clave, los tokens emitidos con la anterior dejan de valer: hay que volver a entrar.

## Pruebas

Necesitan PostgreSQL, la base que nombran las `OLTP_*` del `.env`. Lo recomendado es
la de `infra/envs/test`.

```bash
# Linux o WSL, sin heredar variables de la terminal
cd services/domain-service
env -i PATH="$PATH" HOME="$HOME" ./mvnw -B test -DfailIfNoTests=true
```

```powershell
# Windows, PowerShell: primero, que no haya variables viejas en la sesión
Get-ChildItem Env: | Where-Object Name -Match '^(OLTP_|JWT_)'
#   si sale alguna: Remove-Item Env:NOMBRE   (y quítala de las variables de usuario)
cd services\domain-service
.\mvnw.cmd -B test -DfailIfNoTests=true
```

Ya no hace falta pasar `JWT_SECRET` en la orden: sale del `.env`. Si se pasa y el
`.env` trae otra, `ConfiguracionLocalTest` falla a propósito.

**Las pruebas no dejan datos.** Las que escriben en la base corren dentro de una
transacción que se revierte al terminar cada prueba (`@Transactional` en la clase).
Las cuentas que dejaron las corridas de antes siguen ahí y no se borran solas. Todas
las pruebas las crean con la forma `prueba-<UUID>@canastamx.mx`, así que se pueden
contar sin tocar nada más:

```sql
select count(*) from usuario
where correo_electronico ~ '^prueba-[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}@canastamx\.mx$';
```

Borrarlas es decisión de quien administra esa base.

## Cobertura del dominio (T055, #202)

[JaCoCo 0.8.16](https://www.jacoco.org/jacoco/trunk/doc/maven.html) mide líneas y
ramas con la misma suite Maven y admite Java 21. El agente se prepara antes de
ejecutar las pruebas y el informe se genera al final de `test`. La población son
las clases compiladas de `mx.tecnm.canastamx.domain_service.domain` (`canasta` y
`usuario`, incluidas clases internas). No entran controladores, persistencia,
seguridad ni servicios de aplicación. Se mide la ejecución de toda la suite,
incluidas las pruebas de integración. No se exige un porcentaje mínimo.

Desde `services/domain-service`, con la base de pruebas encendida:

```bash
mvn -B clean test -DfailIfNoTests=true
python scripts/resumir_cobertura.py
```

Abre `target/site/jacoco/index.html` para ver las líneas y ramas por clase. El
script toma los contadores de `target/site/jacoco/jacoco.csv` y el total `Tests run`
de Surefire. Imprime el resumen, las clases sin líneas ejecutadas y el SHA del
checkout, y escribe `target/cobertura-dominio.md`. Si hay cambios sin commit,
lo indica. Usa `clean` antes de medir para descartar informes de corridas previas.

En **Dominio (Java)**, el paso **Cobertura de líneas y ramas del dominio (T055)**
publica esa misma información en el registro y en el resumen de la ejecución.
El artefacto `cobertura-dominio-<SHA>` contiene el informe navegable y el CSV.
Para la solicitud de cambios y la entrega del 18 (#216), copia las cifras y el
SHA del resumen de esa corrida de CI. En un PR, el SHA puede corresponder al
commit de prueba que GitHub crea al combinar la rama con `main`.

## Rutas protegidas

Una ruta pide sesión recibiendo `@CuentaDeLaSesion Usuario cuenta`. Sin un token
Bearer válido de una cuenta que existe, el método no se llama y la respuesta es el 401
`problem+json` con `WWW-Authenticate` (`SinSesionHandler`). `RutasProtegidasTests`
falla si una ruta que `dominio.yaml` no declara pública (`security: []`) no lo recibe.

## Canastas (T050, #188)

Las ocho operaciones de `dominio.yaml` están implementadas: listar, crear, obtener,
renombrar y borrar canastas; agregar, fijar la cantidad y quitar artículos. Todas
reciben `@CuentaDeLaSesion`: el dueño se toma de la sesión. Una canasta ajena o un
artículo ausente responde 404; los datos inválidos, 400. Los errores siguen P-03
(`application/problem+json`). La respuesta de canasta sólo lleva `id`, `nombre` y
`lineas`; cada línea lleva `articulo` y `cantidad` entera. El costo se consulta a la
analítica, no se guarda aquí.

Flyway aplica `V2__crear_canastas.sql` y `V3__ampliar_campos_canasta.sql`.
V2 se conserva porque puede estar aplicada; V3 amplía los campos sin límite de
longitud en el contrato y agrega el índice por dueño. Los cambios de una misma canasta se serializan
con un bloqueo de fila dentro de la transacción. `CanastasTests` prueba las ocho
operaciones, dueño, paginación, errores y borrado de líneas en PostgreSQL, con rollback.
`CanastaTest` comprueba por separado las reglas de la entidad. La salida de Maven debe
mostrar `Tests run` con un total mayor que cero.

Correcciones de documentación para el seguimiento T078 que dejó #185:

- `services/domain-service/README.md`: alcance actual, pruebas que fallan si no se
  ejecuta ninguna y comportamiento de las rutas de canasta.
- `docs/analisis/openapi/README.md`: distingue el contrato de las rutas implementadas
  y documenta sumar frente a fijar, la sesión y los errores de canastas.
- `domain/canasta/ReferenciaDeArticulo.java`: Javadoc de la identidad canónica y su
  validación, con la regla de normalización expresada en texto.
- `domain/canasta/Canasta.java`: Javadoc de sumar, reemplazar y quitar artículos.
- `infrastructure/web/CuentaDeLaSesion.java` y `RutasProtegidasTests.java`: describen
  la seguridad efectiva y sólo dejan alertas como rutas pendientes de implementar.
- `infrastructure/security/JwtService.java`: aclara cómo se decodifica la clave.
  Su Javadoc se alinea en T055 con la aceptación del ADR 020 del 7 de noviembre;
  la descripción del token en `dominio.yaml` queda para T071 (#214), junto con D-12.

Las rutas Java de esta lista son relativas a
`services/domain-service/src/main/java/mx/tecnm/canastamx/domain_service/`, salvo
`RutasProtegidasTests.java`, que está bajo `src/test/java` con el mismo paquete.
