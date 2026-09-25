# CU-08 · Registrar cuenta e iniciar sesión

- **Actor primario:** Persona consumidora
- **Interesados:**
  - Persona consumidora — quiere crear una cuenta y acceder de forma segura al sistema.
  - Sistema — debe validar los datos de la cuenta y proteger la contraseña de la persona consumidora.
- **Precondiciones:**
  1. La persona consumidora no tiene una cuenta registrada con el correo electrónico que desea utilizar para registrarse.
  2. El sistema está disponible para registrar cuentas e iniciar sesiones.
- **Disparador:** La persona consumidora solicita registrar una cuenta nueva o iniciar sesión.

## Flujo principal

1. La persona consumidora proporciona un correo electrónico y una contraseña para registrar una cuenta.
2. El sistema valida que el correo electrónico tenga un formato válido.
3. El sistema valida que la contraseña tenga mínimo 8 caracteres, una mayúscula y un número.
4. El sistema cifra la contraseña antes de almacenarla y nunca guarda la contraseña en texto plano.
5. El sistema registra la cuenta asociando el correo electrónico con la contraseña cifrada.
6. La persona consumidora proporciona sus credenciales para iniciar sesión.
7. El sistema valida las credenciales proporcionadas contra los datos registrados.
8. El sistema permite el inicio de sesión de la persona consumidora.

## Flujos alternos

**2a · El correo electrónico no tiene un formato válido**
1. El sistema rechaza el correo electrónico proporcionado.
2. El sistema solicita un correo electrónico con formato válido.
3. La persona consumidora proporciona otro correo electrónico.
4. Vuelve al paso 2 del flujo principal.

**3a · La contraseña no cumple las reglas establecidas**
1. El sistema rechaza la contraseña.
2. El sistema informa que debe tener mínimo 8 caracteres, una mayúscula y un número.
3. La persona consumidora proporciona una nueva contraseña.
4. Vuelve al paso 3 del flujo principal.

**5a · El correo electrónico ya está registrado**
1. El sistema rechaza el registro de la nueva cuenta.
2. El sistema informa que el correo electrónico ya está asociado a una cuenta.
3. El caso de uso termina sin crear una cuenta duplicada.

**7a · Las credenciales no son válidas**
1. El sistema rechaza el inicio de sesión.
2. El sistema informa que las credenciales proporcionadas no son válidas.
3. La persona consumidora puede proporcionar nuevamente sus credenciales.
4. Vuelve al paso 6 del flujo principal.

## Postcondiciones

- **De éxito:** La cuenta queda registrada con un correo electrónico válido y una contraseña cifrada, sin almacenar la contraseña en texto plano. La persona consumidora puede iniciar sesión con sus credenciales válidas.
- **De fallo:** No se crea una cuenta con datos inválidos o duplicados y no se permite iniciar sesión con credenciales no válidas.

## Requisito no funcional asociado

- El sistema debe completar el registro o responder al intento de inicio de sesión en un tiempo máximo de **2 segundos** bajo condiciones normales de operación.

## Notas

- La contraseña debe cumplir las reglas establecidas en ADR 010: mínimo 8 caracteres, una mayúscula y un número.
- El sistema maneja la contraseña mediante `ContraseñaCifrada`.
- La contraseña nunca debe almacenarse en texto plano.
- El correo electrónico se representa mediante el objeto de valor `CorreoElectronico`.
