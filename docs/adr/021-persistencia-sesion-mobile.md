# ADR 021 · Persistencia de la sesión en el cliente móvil

- **Fecha:** 28 de octubre de 2026
- **Estado:** propuesta; aplicada en la rama de T046, pendiente de revisión.
- **Participantes:** C2 propone; revisión de C1 pendiente.

## Contexto

T046 (#159) conecta el acceso móvil al dominio. D-10 fija la opción A:
`GET /api/v1/cuentas/yo` obtiene el correo incluso después de restaurar la sesión.
El correo no se guarda en el teléfono. El contrato `dominio.yaml` 0.2.2 entrega
`token`, `expiraEn` y `rol`; el ADR 020 trata la emisión y verificación del token
entre servicios. Hace falta definir cómo conserva el cliente su sesión en Expo.

## Decisión

Se usa `expo-secure-store`, instalado para Expo SDK 55, para persistir únicamente
el token con la clave `canastamx.sesion.token`. El correo vive sólo en memoria y
se obtiene de `/cuentas/yo` al iniciar, abrir la app o volver al primer plano.
La contraseña no se persiste y se limpia del formulario al enviarse.

Sólo se conserva una sesión de `CONSUMIDOR`. Los otros roles reciben la indicación
de usar la plataforma web. Cerrar sesión o recibir 401 al restaurarla elimina el
token y el perfil. Un error de red conserva el token para permitir reintentar.
El cliente no guarda la clave de firma ni obtiene el correo decodificando JWT.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Guardar token y perfil en almacenamiento general | Duplica el correo y utiliza almacenamiento sin la protección nativa elegida para credenciales |
| Guardar correo o contraseña para reconstruir la sesión | Contradice D-10 y obliga a persistir datos que el dominio puede devolver con el token |
| Conservar la sesión sólo en memoria | Obliga a iniciar sesión cada vez que se cierra el proceso |
| Leer el correo del JWT | El contrato no incluye ese claim; D-10 define `/cuentas/yo` |

## Consecuencias

- Se agrega una dependencia nativa compatible con Expo Go SDK 55; se prueba en
  Android. Esta decisión no garantiza persistencia tras desinstalar la app.
- El acceso depende del dominio para recuperar el perfil y debe mostrar carga,
  error y reintento. No hay renovación de tokens: una sesión vencida requiere
  iniciar sesión otra vez.
- El almacenamiento se inyecta en el gestor para probar su comportamiento sin
  simular una validación nativa de SecureStore.
- El entorno local usa la dirección del dominio accesible desde Android. En un
  despliegue se debe proporcionar HTTPS; no se distribuyen claves en Expo.
- Este ADR complementa D-10 y el ADR 020 sin cambiar el contrato, los roles ni
  las decisiones del servidor. La canasta del invitado queda fuera de este cambio.
