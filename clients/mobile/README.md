# CanastaMX · Cliente móvil

Prototipo de T028 con el sistema de diseño de D sobre la navegación de T023: **Inicio**,
**Detalle de artículo**, **Mi canasta** y **Alertas**. Se usa el vocabulario del
[ADR 002](../../docs/adr/002-identidad-del-articulo.md).

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

Recorrido manual requerido en un **teléfono real**:

1. Al abrir, se muestra **Inicio** y tres pestañas.
2. Pulsa **Probar detalle de artículo**: se muestra **Detalle de artículo**.
3. Usa la flecha superior: vuelve a Inicio.
4. Entra otra vez al detalle y comprueba también Atrás de Android.
5. Pulsa la pestaña **Mi canasta** y después **Alertas**.
6. Vuelve a la pestaña **Inicio** y comprueba que puedes abrir el detalle de nuevo.
7. Graba unos quince segundos del recorrido Inicio → detalle → regresar →
   Mi canasta → Alertas, mostrando la paleta y tipografía, y adjunta el video al
   issue de T028 (sistema de diseño móvil).

BlueStacks sirve como comprobación adicional. El criterio de esta tarea pide
evidencia en teléfono real. El video se adjunta al issue, no al repositorio.
La prueba debe mostrar las cuatro pantallas con el sistema de diseño aplicado.

La comprobación de TypeScript y el empaquetado no sustituyen la prueba en el
teléfono. El cierre requiere evidencia, revisión e incorporación a `main`.

## Estructura

```text
app/
├── _layout.tsx
├── (tabs)/
│   ├── _layout.tsx
│   ├── index.tsx          # Inicio
│   ├── canasta.tsx        # MiCanasta
│   └── alertas.tsx        # Alertas
└── articulo/
    └── [id].tsx           # DetalleDeArticulo
```

Las pestañas conservan las rutas `/` y `/canasta`, y añaden `/alertas`.
El detalle usa `/articulo/[id]` en la pila raíz. El botón temporal navega a
`/articulo/prueba`: ese identificador no representa un artículo real ni fija
el contrato de datos futuro. El detalle contiene únicamente su título.

La organización se documenta en el
[ADR 007](../../docs/adr/007-navegacion-mobile.md).
No hay datos de ejemplo, consultas de precios, filtros ni persistencia. T039 añade la consulta real a `/health` en Inicio.

`node_modules/`, `.expo/`, archivos de entorno y salidas de compilación están
ignorados. Se versionan el código, la configuración y `package-lock.json`.

## Sistema de diseño de D (T028)

Fuente: [especificación del equipo](../../docs/entregas/diseno.md).
La integración se documenta en el [ADR 011](../../docs/adr/011-sistema-diseno-mobile.md).

- `theme/design-system.ts`: valores compartidos de color, fuente, tamaño, radio y espaciado.
- `components/PantallaVacia.tsx`: presentación común de las cuatro pantallas.
- Fondo crema `#F0EADF`, texto tinta `#2F2F2F` y turquesa `#23BBB7` en el botón y la pestaña activa.
- Inter Regular y SemiBold incluidas como archivos estáticos por `@expo-google-fonts/inter`, cargadas con `expo-font` antes de mostrar las pantallas; funcionan en Expo Go.
- Títulos de 24, etiquetas de navegación y botón de 14, botón con radio de 12 y espaciados en múltiplos de cuatro. Se conserva el escalado de texto del sistema.
- Verde reservado para éxito. No se usan rojo ni naranja en pantallas vacías.

Al revisar en el teléfono, comprueba los cuatro títulos con Inter, el fondo crema,
la pestaña activa turquesa y el botón redondeado. Verifica que la barra de pestañas
no se superponga con la navegación de Android y que el texto siga legible al
ampliar el tamaño de fuente del sistema. Recorre búsqueda, detalle, regreso,
canasta y alertas antes de grabar la evidencia. Estas verificaciones visuales
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
No necesita base de datos para `/health`. Mantén esa terminal abierta.
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
