# Servicio de dominio

Cuentas, sesiones y, después, canastas y alertas. El contrato es
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
env -i PATH="$PATH" HOME="$HOME" ./mvnw -B test
```

```powershell
# Windows, PowerShell: primero, que no haya variables viejas en la sesión
Get-ChildItem Env: | Where-Object Name -Match '^(OLTP_|JWT_)'
#   si sale alguna: Remove-Item Env:NOMBRE   (y quítala de las variables de usuario)
cd services\domain-service
.\mvnw.cmd -B test
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

## Rutas protegidas

Una ruta pide sesión recibiendo `@CuentaDeLaSesion Usuario cuenta`. Sin un token
Bearer válido de una cuenta que existe, el método no se llama y la respuesta es el 401
`problem+json` con `WWW-Authenticate` (`SinSesionHandler`). `RutasProtegidasTests`
falla si una ruta que `dominio.yaml` no declara pública (`security: []`) no lo recibe.
