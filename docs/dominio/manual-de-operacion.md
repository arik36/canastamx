# Manual de operación del servicio de dominio

T078 · C1 · #220. Revisado contra el repositorio el 26 de noviembre de 2026.
Complementa el [manual técnico](manual-tecnico.md). Describe procedimientos;
no acredita una nueva ejecución del despliegue ni del experimento.

## Alcance y requisitos

El servicio atiende cuentas, sesiones y canastas. Necesita Java 21 y PostgreSQL 16.
Para desarrollo: Git, Docker con Compose y Maven (o el wrapper del servicio).
Los ejemplos siguientes usan Bash/Git Bash desde la raíz, salvo indicación.

Fuentes: [README del servicio](../../services/domain-service/README.md),
[guía de arranque](../infra/arranque.md),
[entorno de pruebas](../../infra/envs/test/README.md) y
[guía de producción](../../infra/envs/prod/README.md).

La ficha menciona `infra/despliegue/README.md`; en la versión revisada no existe.
La guía vigente de T054 (#201) está en `infra/envs/prod/README.md`.
Los pasos del sistema completo, DNS, certificados y administración de la VM
corresponden a esa guía y al frente de infraestructura.

## Variables y secretos

Esta tabla enumera nombres y propósito, sin valores de configuración ni secretos.

| Variable | Uso |
|---|---|
| `OLTP_DB` | Base transaccional. |
| `OLTP_USER` | Usuario de PostgreSQL. |
| `OLTP_PASSWORD` | Contraseña de PostgreSQL. |
| `OLTP_PORT` | Puerto publicado de PostgreSQL para ejecutar Java en la máquina local. |
| `JWT_SECRET` | Clave compartida con analítica: Base64 estándar de exactamente 32 bytes aleatorios. |
| `JWT_EXPIRATION_MINUTES` | Duración positiva de las sesiones. |
| `SEMILLA_CONTRASENA` | Contraseña que usa el script al crear las cuentas semilla. |
| `SPRING_DATASOURCE_URL` | Compose de producción sustituye la URL local por la de PostgreSQL en la red interna. |
| `JAVA_TOOL_OPTIONS` | Compose limita la memoria de la JVM según el contenedor. |
| `DIRECCION_PUBLICA` | Nombre público del despliegue usado por Traefik. |
| `ACME_CORREO`, `ACME_SERVIDOR` | Configuración de certificados gestionada por infraestructura. |

Las demás variables del sistema completo están descritas en la guía de producción.
No se copian aquí valores de `.env`, contraseñas, tokens ni cadenas de conexión reales.

En desarrollo, `application.properties` importa el `.env` de la raíz mediante
`../../.env`, relativo al directorio de trabajo. En producción, Compose lee
`infra/envs/prod/.env` e inyecta las variables al contenedor; no se copia el secreto
a la imagen. Un valor exportado en la terminal tiene precedencia: no mezcles
variables cargadas de otro entorno.

Los archivos `.env` son locales y no se versionan. Usa el formato
`CLAVE=valor`, sin comillas, sin `export` y sin comentarios al final de línea.
Genera `JWT_SECRET` según el [README del servicio](../../services/domain-service/README.md);
no pegues su salida en evidencias. Rotarla invalida las sesiones anteriores y
requiere coordinar el mismo cambio con analítica.

## Desarrollo: levantar y comprobar

1. Comprueba Docker:

   ```bash
   docker compose version
   docker info
   ```

2. Sólo si todavía no existe el `.env` de la raíz, copia su ejemplo y complétalo
   localmente. No sobrescribas una configuración existente:

   ```bash
   cp -n .env.example .env
   python infra/scripts/revisar-env.py --entorno
   ```

   El validador informa de nombres y problemas sin mostrar valores.
   Si detecta una variable de terminal que tapa el archivo, elimina esa variable
   de la sesión o abre una terminal limpia; no imprimas el entorno completo.

3. Desde la raíz, levanta la base usada por el servicio:

   ```bash
   docker compose config --quiet
   docker compose up -d postgres-oltp
   docker compose ps postgres-oltp
   ```

   La base debe quedar sana. Este procedimiento usa el entorno de desarrollo de
   la raíz; no debe confundirse con el entorno aislado de pruebas.

4. En otra terminal limpia, ejecuta el servicio desde su carpeta:

   ```bash
   cd services/domain-service
   ./mvnw spring-boot:run
   ```

   En PowerShell: `cd services\domain-service` y
   `.\mvnw.cmd spring-boot:run`. También puede usarse Maven instalado.
   En un IDE, configura ese mismo directorio de trabajo. Flyway aplica las
   migraciones al arrancar; espera el mensaje `Started`.

5. Comprueba desde una tercera terminal:

   ```bash
   curl --fail --show-error http://localhost:8081/health
   ```

   Debe responder HTTP 200 y JSON con `status` igual a `UP`,
   `service` igual a `domain-service` y `time`.
   Esta ruta pública comprueba que el controlador responde: no hace una consulta
   de disponibilidad de PostgreSQL en cada petición. No sustituye una prueba de
   operación de cuenta/canasta.

Para detener Java en primer plano, usa Ctrl+C. La detención de la base se puede
hacer desde la raíz con `docker compose stop postgres-oltp`; conserva el volumen.

## Pruebas y cobertura

Usa preferentemente la base del [entorno de pruebas](../../infra/envs/test/README.md),
en un puerto distinto al desarrollo. El servicio Java local sigue leyendo el
`.env` de la raíz: levantar Compose con `--env-file infra/envs/test/.env` no cambia
por sí solo lo que Maven lee. Configura localmente los nombres `OLTP_*` para esa
base, sin publicar valores, y mantén terminales de desarrollo y pruebas separadas.

Desde la raíz, con el archivo de pruebas ya preparado según su guía:

```bash
docker compose -f infra/envs/test/docker-compose.yml --env-file infra/envs/test/.env up -d postgres-oltp
```

Desde `services/domain-service`, en una terminal sin variables antiguas que tapen
el archivo:

```bash
./mvnw -B clean test -DfailIfNoTests=true
python scripts/resumir_cobertura.py
python -m unittest discover -s scripts -p 'test_*.py' -v
```

En PowerShell, usa `.\mvnw.cmd` en lugar de `./mvnw`.
Se espera `BUILD SUCCESS` y un total `Tests run` mayor que cero.
El informe queda en `target/site/jacoco/index.html` y
`target/cobertura-dominio.md`. Registra el SHA y si el árbol tiene cambios;
no atribuyas cifras de una corrida anterior a una nueva.

Desde la raíz, valida el contrato si se modifica:

```bash
npx --yes @redocly/cli@2.71.0 lint docs/analisis/openapi/dominio.yaml
```

La referencia de dominio es 0 errores y dos avisos existentes: servidor localhost
y falta de 4XX en `/health`. Las pruebas Java que escriben datos usan rollback;
no borran cuentas de corridas antiguas.

Antes de cada corrida del experimento se usa la comprobación de aislamiento de
T049 descrita en su guía. T078 documenta dominio: no ejecuta ni acredita T076.

## Cuentas semilla

Desde la raíz, con PostgreSQL sano y la tabla `usuario` ya creada por Flyway:

```bash
bash infra/scripts/sembrar-cuentas.sh
```

Para el entorno de pruebas o producción, respectivamente:

```bash
bash infra/scripts/sembrar-cuentas.sh --test
bash infra/scripts/sembrar-cuentas.sh --prod
```

Ejecuta sólo la variante del entorno que deseas modificar. El script lee su
`SEMILLA_CONTRASENA`, que debe cumplir las reglas de registro: al menos ocho
caracteres, una mayúscula y un número. No imprime la contraseña.

Crea una cuenta `ANALISTA` y una `OPERADOR`. Si sus correos ya existen, no cambia
nada. Cambiar `SEMILLA_CONTRASENA` y repetir la siembra no actualiza sus contraseñas:
las existentes conservan la anterior. La creación de consumidores se hace mediante
`POST /api/v1/cuentas`.

## Producción: arranque y redespliegue

Estos pasos los ejecuta quien tenga acceso autorizado a la VM, siguiendo la
[guía de producción](../../infra/envs/prod/README.md).
El primer despliegue requiere preparar VM, DNS, puertos y certificados conforme
a esa guía; un manual del dominio no sustituye esa preparación.

Desde la raíz en la VM y en una terminal sin variables de otros entornos,
con `infra/envs/prod/.env` preparado:

```bash
alias prod='docker compose -f infra/envs/prod/docker-compose.yml --env-file infra/envs/prod/.env'
prod config --quiet
prod up -d --build
prod ps
prod logs --tail=100 domain-service
```

Compose construye el [Dockerfile del dominio](../../services/domain-service/Dockerfile)
con JDK 21, genera el JAR y lo ejecuta con JRE 21 y usuario sin privilegios.
La compilación de imagen omite pruebas; éstas se ejecutan por separado en CI.
No se debe presentar una imagen construida como evidencia de pruebas aprobadas.

El contenedor depende de PostgreSQL sano, usa su nombre en la red Docker mediante
`SPRING_DATASOURCE_URL` y escucha internamente en el puerto 8081.
Traefik termina TLS y publica `https://dominio.<DIRECCION_PUBLICA>`.
La base no publica su puerto en producción. El límite del dominio es 1 GiB y
la JVM tiene configurado el 75 % mediante `JAVA_TOOL_OPTIONS`.

Después de `Started`, ejecuta la siembra `--prod` si corresponde. Desde fuera de
la VM, sustituye el marcador por el nombre público configurado:

```bash
curl --fail --show-error 'https://dominio.<DIRECCION_PUBLICA>/health'
bash infra/envs/prod/verificar-desde-fuera.sh '<DIRECCION_PUBLICA>'
```

El segundo comando usa el nombre raíz del despliegue, no el subdominio del dominio.
Comprueba también certificados, servicios y cuentas semilla, y pide la contraseña
sin mostrarla. Guarda la evidencia sin credenciales ni tokens.

Para redesplegar una versión ya integrada, primero verifica que no haya cambios
locales en la VM. Después, como indica la guía:

```bash
git switch main
git pull --ff-only
prod up -d --build
prod ps
```

Repite salud y verificación externa. Conserva los volúmenes: no uses
`docker compose down -v` ni `prod down -v`, porque borran bases y certificados.
Una recuperación de datos o cambio de infraestructura se coordina con B;
no se resuelve eliminando volúmenes ni editando migraciones aplicadas.

## Errores frecuentes

| Síntoma | Comprobación y acción |
|---|---|
| Docker no responde o no encuentra el motor. | Inicia Docker Desktop, espera a que esté listo y comprueba `docker info`. |
| Aparece `${OLTP_USER}` literal o falla la conexión. | Ejecuta Java desde `services/domain-service`; verifica que existe el archivo local y valida el formato. Comprueba base sana, puerto y nombres, sin imprimir contraseñas. |
| `ConfiguracionLocalTest` señala variables distintas. | Quita sólo las variables señaladas de la terminal o abre una limpia. No cambies valores del archivo para ocultar el conflicto. |
| `JWT_SECRET` vacía, Base64 inválido o longitud incorrecta. | Genera una clave conforme al ADR 020 y configúrala localmente. Coordina el cambio con analítica; no publiques su valor. |
| Duración de sesión no positiva. | Revisa `JWT_EXPIRATION_MINUTES`; debe ser mayor que cero. |
| 401 al iniciar sesión. | Verifica las credenciales. D-12 establece que no lleva `WWW-Authenticate`; no es un fallo de configuración por sí mismo. |
| 401 en una ruta protegida. | Envía Bearer válido y comprueba vencimiento, clave compartida y existencia de la cuenta. Vuelve a iniciar sesión si la clave cambió. |
| 400, 409 o 404 en operaciones. | 400: entrada inválida; 409 de registro: correo ya usado; 404 de canasta: ausente o ajena, o artículo ausente. Revisa el contrato sin exponer datos de otra cuenta. |
| La semilla no encuentra `usuario`. | Arranca primero el dominio o sus pruebas para que Flyway cree la tabla. No la crees manualmente con otro esquema. |
| Cambió la contraseña de PostgreSQL y ahora rechaza conexiones. | La del volumen no cambia al editar el `.env`. Coordina la corrección con infraestructura; no borres el volumen. |
| 502 en la dirección pública. | Comprueba `prod ps`, log del dominio, estado de PostgreSQL y log de Traefik. |
| Fallo de certificados o DNS. | Sigue la guía de producción; corresponde a infraestructura. |
| Error de validación de Flyway. | Conserva los datos y registra el error sin secretos. Revisa versiones y checksums con infraestructura; no edites una migración aplicada ni ejecutes reparaciones a ciegas. |

## Continuidad y evidencia

Al entregar una versión, registra commit, comandos, resultado real, entorno y
fecha. Conserva el conteo de pruebas y los informes de cobertura; no copies
`.env`, tokens ni salidas que contengan credenciales. Las verificaciones locales
no sustituyen la CI ni acreditan por sí solas el estado de producción.

Los dos manuales son entradas para el traspaso T083. Su elaboración no incluye
crear ese documento, ejecutar el experimento ni desplegar una versión nueva.
El cotejo con el protocolo completo de investigación queda pendiente de disponer
de él, como se indica en el manual técnico.
