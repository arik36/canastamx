# T046 · Verificación del acceso móvil (#159)

Fecha: 28 de octubre de 2026. Entorno: Node 20.20.2, Expo SDK 55,
BlueStacks con Expo Go y dominio local con PostgreSQL aislado para pruebas.

## Comprobaciones automatizadas

- `npm test`: 16 pruebas aprobadas del gestor y de la API. Cubren credenciales
  inválidas, roles, restauración, vencimiento, cierre, almacenamiento, respuestas
  tardías y límite de ocho segundos. El almacenamiento se sustituye por una
  dependencia de prueba: estas pruebas no acreditan por sí solas SecureStore.
- `npm run typecheck`: aprobado después de regenerar las rutas con Expo.
- Exportación Android: aprobada. La salida de compilación queda fuera del repositorio.
- Cliente real contra el dominio local: acceso válido, correo desde `/cuentas/yo`,
  rechazo de contraseña incorrecta, restauración con un gestor nuevo, cierre y
  error cuando la dirección del servicio es inaccesible. No se imprimieron tokens.

## Comprobación manual del autor

Renato confirmó en BlueStacks:

- Las cuatro pestañas, los accesos a Mis alertas y su regreso funcionan.
- La campana y Mis alertas mantienen el fondo y relleno; no hay títulos duplicados.
- Inicio muestra Estado: UP con el verde oscuro del sistema de diseño.
- Una contraseña incorrecta muestra el aviso y termina la carga.
- Un acceso válido muestra el correo y el avatar con su inicial.
- Después de recargar, Cuenta se recupera sin pedir contraseña.
- Con el dominio apagado, el acceso muestra error de conexión y termina la carga.

Durante la revisión se detectó que Acceso seguía visible aunque el gestor ya
había restaurado la sesión. Un diagnóstico temporal confirmó la lectura del
almacenamiento y el estado autenticado sin imprimir credenciales. Se corrigió la
redirección a Cuenta y el autor confirmó el resultado. El diagnóstico fue retirado.

No se incluyen capturas nuevas: el control de Windows del asistente no estuvo
disponible durante esta prueba. Las confirmaciones anteriores son manuales del
autor, no una inspección visual automatizada.
