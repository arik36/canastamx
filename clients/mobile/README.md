# CanastaMX · Cliente móvil

Navegación de la semana 2 sobre la base de T014: **Búsqueda de artículos**,
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
   Mi canasta → Alertas, o toma cuatro capturas, y adjunta la evidencia al
   issue de navegación de la semana 2.

BlueStacks sirve como comprobación adicional. El criterio de esta tarea pide
evidencia en teléfono real. El video se adjunta al issue, no al repositorio.
Al terminar, avisa al equipo: «Navegación lista, cuatro pantallas.»

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
llamadas al servicio. El sistema de diseño corresponde a T028.

`node_modules/`, `.expo/`, archivos de entorno y salidas de compilación están
ignorados. Se versionan el código, la configuración y `package-lock.json`.