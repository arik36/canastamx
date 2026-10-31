# CanastaMX · Cliente móvil

La navegación sigue D-01 y el ADR 007 ratificado: **Inicio, Descubrir, Canasta
y Cuenta** son las cuatro pestañas. **Detalle de artículo** y **Mis alertas**
se abren en la pila raíz. Se conserva la consulta real a `/health` de T039 y
el sistema de diseño de D. Se utiliza «artículo», conforme al ADR 002.

El acceso de #159 se abre desde Cuenta. Usa el dominio real para iniciar sesión y
obtener el correo mediante D-10; no se muestran datos ficticios de una cuenta.

## Requisitos

- Node **20.20.2**, fijado en `.nvmrc`.
- npm y las versiones del archivo `package-lock.json`.
- Android con [Expo Go para SDK 55](https://expo.dev/go?sdkVersion=55&platform=android&device=true).
- Computadora y teléfono en la misma red Wi-Fi.

Se conserva Expo SDK 55 y el entorno de T014 documentado en el
[ADR 006](../../docs/adr/006-entorno-mobile-expo.md).

## Instalar y arrancar

Desde `clients/mobile/`, con Node 20 activo:

```powershell
node --version
npm.cmd ci
npm.cmd start -- --port 8082
```

El puerto 8082 evita competir con el 8081 del servicio de dominio. No es
necesario arrancar ese servicio para recorrer la navegación; la consulta de T039 sí lo requiere.

En Expo Go, escanea el QR de la terminal. Mantén la terminal abierta.
Si aparece incompatibilidad de SDK, utiliza la versión para SDK 55 enlazada arriba.

Si no hay comunicación por la red local:

```powershell
npm.cmd start -- --port 8082 --tunnel
```

El túnel requiere internet y puede solicitar instalar `@expo/ngrok`.
En Windows se usan `npm.cmd` y `npx.cmd` para evitar depender de la política
de ejecución de scripts de PowerShell.

## Verificar

```powershell
npm.cmd run typecheck
npx.cmd expo install --check
```

Si acabas de cambiar las rutas, arranca Expo para que regenere los tipos de
`.expo/types/` antes de comprobar TypeScript.

Recorrido manual de navegación en Android con Expo Go:

1. Al abrir, comprueba las cuatro pestañas, en este orden: **Inicio**, **Descubrir**,
   **Canasta** y **Cuenta**. Alertas no debe aparecer en la barra inferior.
2. Desde Inicio, pulsa **Probar detalle de artículo** y regresa con la flecha.
3. Abre el detalle otra vez y regresa con Atrás de Android.
4. Desde la campana del encabezado abre **Mis alertas**. La barra de pestañas
   debe ocultarse; regresa con la flecha a la pestaña desde la que entraste.
5. Cambia a Descubrir y Canasta; comprueba también la campana desde ellas.
6. En **Cuenta**, pulsa **Mis alertas**, regresa y verifica que sigues en Cuenta.
7. Comprueba que Inicio conserva la consulta y el refresco de T039. «Estado: UP»
   usa verde oscuro `#007A44` sobre crema, conforme a `diseno.md`.
8. La campana y «Mis alertas» deben tener fondo turquesa, relleno y un área
   táctil mínima de 48 × 48. Ábrelos y regresa a la misma pestaña.
9. Cada pestaña muestra su título una sola vez, en el encabezado. Detalle y
   Mis alertas conservan el título central porque no tienen título de encabezado.

Graba el recorrido o adjunta capturas a la solicitud. Indica si la prueba se
realizó en teléfono físico o en BlueStacks; el empaquetado y TypeScript no
sustituyen la verificación de la navegación en Android.

## Estructura

```text
app/
├── _layout.tsx
├── acceso.tsx            # Iniciar sesión, ruta /acceso
├── alertas.tsx           # MisAlertas, ruta /alertas
├── (tabs)/
│   ├── _layout.tsx
│   ├── index.tsx         # Inicio
│   ├── descubrir.tsx     # Descubrir
│   ├── canasta.tsx       # MiCanasta
│   └── cuenta.tsx        # Cuenta
└── articulo/
    └── [id].tsx          # DetalleDeArticulo
```

Las rutas `/`, `/canasta` y `/alertas` conservan su URL; el grupo `(tabs)` no
forma parte de la dirección. Se incorporan `/descubrir` y `/cuenta`.
`/alertas` está en la pila y es accesible desde la campana y desde Cuenta.
El botón temporal de Inicio abre `/articulo/prueba`; ese identificador no
representa un artículo real ni fija el contrato de datos futuro.

La organización se documenta en el [ADR 007](../../docs/adr/007-navegacion-mobile.md).
Esta corrección no añade catálogos, precios, canastas ni alertas de ejemplo.
La consulta real a `/health` permanece en Inicio.

`node_modules/`, `.expo/`, archivos de entorno y salidas de compilación están
ignorados. Se versionan el código, la configuración y `package-lock.json`.

## Sistema de diseño de D (T028)

Fuente: [especificación del equipo](../../docs/entregas/diseno.md).
La integración se documenta en el [ADR 011](../../docs/adr/011-sistema-diseno-mobile.md).

- `theme/design-system.ts`: valores compartidos de color, fuente, tamaño, radio y espaciado.
- `components/PantallaVacia.tsx`: presentación común; `showTitle={false}` evita
  duplicar el título que ya muestra el encabezado de cada pestaña.
- Fondo crema `#F0EADF`, texto tinta `#2F2F2F` y turquesa `#23BBB7` en el botón y la pestaña activa.
- Inter Regular y SemiBold incluidas como archivos estáticos por `@expo-google-fonts/inter`, cargadas con `expo-font` antes de mostrar las pantallas; funcionan en Expo Go.
- Títulos de 24, etiquetas de navegación y botón de 14, botón con radio de 12 y espaciados en múltiplos de cuatro. Se conserva el escalado de texto del sistema.
- Verde reservado para éxito. No se usan rojo ni naranja en pantallas vacías.

Al revisar en el teléfono, comprueba los cuatro títulos con Inter, el fondo crema,
la pestaña activa turquesa y el botón redondeado. Verifica que la barra de pestañas
no se superponga con la navegación de Android y que el texto siga legible al
ampliar el tamaño de fuente del sistema. Recorre Inicio → detalle → regreso →
Descubrir → Canasta → Cuenta → Mis alertas → regreso antes de grabar la evidencia. Estas verificaciones visuales
requieren ejecución en el dispositivo; compilar no las sustituye.

## Primera llamada real al dominio (T039)

Inicio consulta `GET /health`, fuera de `/api/v1`, según `dominio.yaml`.
La respuesta muestra `status`, `service` y la hora ISO `time` que envía el servidor.
El botón **Refrescar** vuelve a consultar. **Reintentar** aparece si falla la
conexión. Cada consulta tiene un límite de 8 segundos y se cancela al desmontar
el componente; una respuesta inválida o un error HTTP también se muestran.

### Preparar el servicio

Con JDK 21, desde la raíz del repositorio y en Git Bash:

```bash
cd services/domain-service
./mvnw spring-boot:run
```

En PowerShell, el equivalente es `./mvnw.cmd spring-boot:run`.
La versión actual del dominio necesita PostgreSQL y las variables locales de
base de datos y JWT, incluso para arrancar y consultar `/health`. Sigue
[services/domain-service/README.md](../../services/domain-service/README.md) y
mantén esa terminal abierta.
El puerto **8081** es del dominio; si Traefik lo usaba, cambia únicamente su
variable local `TRAEFIK_WEB_PORT` a **8880** y aplica
`docker compose up -d traefik` desde la raíz del repositorio.

En otra terminal comprueba `curl http://localhost:8081/health`.

### Configurar Android

Copia `.env.example` a `.env` dentro de `clients/mobile` sólo si no tienes ya uno.
Completa `EXPO_PUBLIC_API_URL` con la dirección accesible desde Android, sin
agregar `/health`. Usa la IPv4 de tu computadora y el puerto 8081 para un teléfono
en la misma red. Verifica esa dirección con `/health` en el navegador de Android.
El emulador oficial de Android usa `10.0.2.2` para alcanzar la computadora;
en BlueStacks verifica la conexión con la IPv4 de la computadora, pues su red
puede ser diferente. Desde el teléfono, `localhost` es el propio teléfono.

El `.env` local está ignorado; `.env.example` se versiona sin valor. Las variables
`EXPO_PUBLIC_` se incluyen en la app y no deben contener secretos.

Con Node 20, reinicia Expo para cargar la configuración:

```bash
npx expo start -c --port 8082
```

Abre el proyecto con Expo Go para SDK 55 en Android. La prueba se hace en Android,
no en Expo web: el servicio no configura CORS para el navegador.

### Evidencia de aceptación

1. En Inicio verifica **Cargando**, después **Estado: UP**, el servicio y su hora.
2. Pulsa **Refrescar** dos veces: la hora del servidor debe cambiar.
3. Captura la respuesta real de la app.
4. Detén el dominio con `Ctrl+C` en su terminal y pulsa **Refrescar**.
5. En un máximo aproximado de 8 segundos debe aparecer un error y **Reintentar**;
   la conexión puede fallar antes del tiempo límite. Captura ese estado.
6. Arranca el dominio de nuevo y pulsa **Reintentar** para comprobar la recuperación.
7. Ejecuta `npm run typecheck` y adjunta las dos capturas al issue #120 o su PR.

TypeScript y el empaquetado no acreditan estas pruebas de Android: deben
realizarse con el servicio real y las capturas correspondientes.

Evidencia de la prueba realizada en BlueStacks con Android 11: [respuesta, refresco, error y recuperación](docs/evidencia/t039/README.md).

## Acceso conectado al dominio (T046 · #159)

Desde **Cuenta → Iniciar sesión**, escribe el correo y la contraseña de una
cuenta de prueba creada en tu dominio local. La app llama a
`POST /api/v1/sesiones` y después a `GET /api/v1/cuentas/yo` con Bearer.
Muestra el correo y un avatar con su inicial, nunca un nombre. Incluye
«Explorar sin cuenta» y el aviso «No somos PROFECO».

- El rol `CONSUMIDOR` abre Cuenta. `ANALISTA` y `OPERADOR` reciben una indicación
  de usar la plataforma web; no se persiste su token en el móvil.
- Sólo el token se guarda con `expo-secure-store`; correo y contraseña no se
  persisten. La contraseña se limpia del formulario al enviarse. No se guardan
  credenciales en `.env`, en el código ni en capturas.
- Al abrir la app o volver al primer plano se consulta `/cuentas/yo`. Un 401
  elimina la sesión; un fallo de red ofrece reintentar o continuar sin cuenta.
- Cerrar sesión borra el token y el perfil en memoria. Cada solicitud tiene un
  límite de ocho segundos; un error deja un mensaje y termina la carga.
- El cliente no contiene `JWT_SECRET` ni verifica firmas: el dominio valida el
  token. Las variables `EXPO_PUBLIC_` son públicas.
- Esta tarea no implementa registro, datos de canasta ni sincronización. La
  navegación como invitado no envía una canasta al servidor.

La persistencia se explica en el [ADR 021](../../docs/adr/021-persistencia-sesion-mobile.md).
La API y el gestor de sesión se separan del almacenamiento nativo para probar
rechazos, restauración, cierre y respuestas tardías:

```bash
npm test
npm run typecheck
```

### Prueba manual en Android

1. Arranca PostgreSQL y el dominio con su configuración local. En el teléfono o
   BlueStacks comprueba la URL del dominio en `/health` y ajusta la dirección de
   `clients/mobile/.env`; reinicia Expo si cambió la IP.
2. En Cuenta, abre Iniciar sesión. Envía un correo válido con una contraseña
   incorrecta: debe aparecer el aviso y desaparecer el indicador de carga.
3. Usa credenciales válidas de tu base de pruebas: Cuenta muestra el correo y su
   inicial. Captura el resultado sin incluir contraseña ni token.
4. Recarga la app desde Expo: debe recuperar Cuenta consultando `/cuentas/yo`.
5. Cierra sesión, recarga y verifica que continúa como invitado. Desde Acceso,
   «Explorar sin cuenta» debe regresar a Inicio.
6. Con el dominio detenido intenta entrar: debe terminar con un error, como
   máximo al vencer el límite de ocho segundos. Arranca el dominio y reintenta.
7. Recorre las cuatro pestañas, el detalle y ambos accesos a Mis alertas.

El acceso Android se valida en Expo Go, no en Expo web. Usa datos sintéticos en
una base local aislada; no publiques contraseñas ni tokens como evidencia. Las
pruebas automatizadas del gestor y de la API no sustituyen este recorrido.

Registro de comprobaciones de acceso: [T046](docs/evidencia/t046/README.md).
