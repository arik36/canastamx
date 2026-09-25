# CanastaMX · Cliente móvil

Prototipo de T028 con el sistema de diseño de D sobre la navegación de T023: **Búsqueda de artículos**,
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
necesario arrancar ese servicio para probar estas pantallas.

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

1. Al abrir, se muestra **Búsqueda de artículos** y tres pestañas.
2. Pulsa **Probar detalle de artículo**: se muestra **Detalle de artículo**.
3. Usa la flecha superior: vuelve a Búsqueda.
4. Entra otra vez al detalle y comprueba también Atrás de Android.
5. Pulsa la pestaña **Mi canasta** y después **Alertas**.
6. Vuelve a la pestaña **Búsqueda** y comprueba que puedes abrir el detalle de nuevo.
7. Graba unos quince segundos del recorrido Búsqueda → detalle → regresar →
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
│   ├── index.tsx          # BusquedaDeArticulos
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
No hay datos de ejemplo, consultas de precios, filtros, persistencia ni
llamadas al servicio. T028 aplica únicamente estilos y carga de fuentes.

`node_modules/`, `.expo/`, archivos de entorno y salidas de compilación están
ignorados. Se versionan el código, la configuración y `package-lock.json`.

## Sistema de diseño de D (T028)

Fuente: [especificación del equipo](../../docs/entregas/diseño.md).
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
