# CanastaMX · Cliente móvil

Base de T014 con TypeScript y Expo Router. Tiene dos pantallas: **Búsqueda** (`/`) y **Mi canasta** (`/canasta`). El enlace abre la canasta; el botón de regreso y la navegación de Android permiten volver.

## Requisitos

- Node **20.20.2**, fijado en `.nvmrc` (el SDK admite Node 20 desde 20.19.4).
- npm y las versiones del archivo `package-lock.json`.
- Android con [Expo Go para SDK 55](https://expo.dev/go?sdkVersion=55&platform=android&device=true).
- Computadora y teléfono en la misma red Wi-Fi.

Se usa Expo SDK 55 para cumplir Node 20. SDK 57 requiere Node 22.13 o superior, según la [tabla de compatibilidad](https://docs.expo.dev/versions/latest/). La configuración de Router sigue la [instalación oficial](https://docs.expo.dev/router/installation/).

## Instalar y arrancar

Desde `clients/mobile/`, con Node 20 activo:

```powershell
node --version
npm.cmd ci
npm.cmd start
```

En Expo Go, pulsa **Scan QR code** y escanea el QR de la terminal. Mantén la terminal abierta. Si aparece incompatibilidad de SDK, comprueba que Expo Go sea la versión para SDK 55 enlazada arriba.

Si ambas máquinas no pueden comunicarse por Wi-Fi:

```powershell
npm.cmd start -- --tunnel
```

El modo túnel requiere internet y puede solicitar instalar `@expo/ngrok`. En Windows se usan `npm.cmd` y `npx.cmd` para evitar depender de la política de ejecución de scripts de PowerShell.

## Verificar

```powershell
npm.cmd run typecheck
npx.cmd expo install --check
npx.cmd expo-doctor
```

Prueba manual requerida en Android:

1. Al abrir, se muestra **Búsqueda**.
2. Pulsa **Ir a mi canasta**: se muestra **Mi canasta**.
3. Pulsa **Volver a búsqueda**: regresa a **Búsqueda**.
4. Vuelve a entrar a la canasta y comprueba el botón o gesto Atrás de Android.
5. Graba unos diez segundos de la ida y vuelta y adjunta el video o las capturas al issue real de T014.

La comprobación de TypeScript y el empaquetado no sustituyen la prueba en el teléfono. El issue se cierra después de adjuntar evidencia y de que el Pull Request esté aprobado e incorporado a `main`.

## Estructura

```text
app/
├── _layout.tsx   # Navegación de pila y títulos
├── index.tsx     # Búsqueda
└── canasta.tsx   # Mi canasta
```

`package.json` utiliza `expo-router/entry` como punto de entrada. Detalle de producto y Alertas se implementarán en sus tareas correspondientes. Esta base no incluye consultas de precios ni persistencia de la canasta.

`node_modules/`, `.expo/`, archivos de entorno y salidas de compilación están ignorados. Se versionan el código, la configuración y `package-lock.json`.
