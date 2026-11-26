# CanastaMX · Aplicación Android

Cliente Expo SDK 55 / React Native. La versión T072 (#215) adapta el diseño de
Karen a pantallas nativas: portada, acceso y registro, catálogo de artículos,
comparación, canastas y cuenta. La carpeta `App_Karen` permanece intacta.

La barra conserva **Inicio, Descubrir, Canasta y Cuenta** (D-01). Descubrir indica
«No está disponible en esta versión». Las alertas salen del alcance aprobado;
la ruta antigua `/alertas` redirige a Cuenta. No se ofrecen funciones de alertas,
favoritos, recuperación de contraseña ni datos de perfil ficticios.

## Desarrollo

Requisitos: Node **20.20.2** (`.nvmrc`), npm y Android con
[Expo Go SDK 55](https://expo.dev/go?sdkVersion=55&platform=android&device=true).
Desde `clients/mobile/`:

```powershell
npm.cmd ci
# Copia .env.example a .env sólo si no tienes configuración local.
npm.cmd start -- --port 8082
```

Configura dos direcciones independientes, sin rutas `/api/v1`:

- `EXPO_PUBLIC_API_URL`: servicio de dominio, por ejemplo el puerto local 8081.
- `EXPO_PUBLIC_ANALITICA_URL`: interfaz analítica, por ejemplo el puerto local 8000.

En un teléfono, `localhost` es el propio teléfono. Para desarrollo usa una
dirección alcanzable por él; también puedes usar USB y `adb reverse` para enlazar
únicamente los puertos locales necesarios. Expo Go necesita su servidor de
desarrollo activo. **El APK de entrega funciona sin Expo Go ni ese servidor.**

Las variables `EXPO_PUBLIC_` quedan dentro del instalable: nunca llevan secretos.
El dominio requiere PostgreSQL y su configuración JWT, incluso para `/health`;
consulta [su README](../../services/domain-service/README.md).

## Generar el APK de entrega (#215)

`app.json` fija la identidad `mx.tecnm.canastamx`, versión `1.0.0`, código Android
`1`. Conserva esa identidad y la misma clave de firma para las actualizaciones;
incrementa `android.versionCode` antes de distribuir una actualización.

La entrega validada es el APK v10 conectado a los servidores públicos. Su
SHA-256, firma, pruebas y capturas están en [T072](docs/t072-version-final.md).
Puedes generarlo localmente con `npm.cmd run build:android -- -ServidoresPublicos`,
siguiendo la sección de Windows de abajo. EAS es una opción adicional; #215
no exige usar ese proveedor ni publicar en una tienda.

### Opción de compilación con EAS

El perfil **preview** de `eas.json` genera un **APK firmado para distribución
interna**; **production** genera AAB para una tienda. No se necesita publicar en
una tienda para instalar el APK en los dos teléfonos.

1. Consigue las dos direcciones HTTPS reales de #201. Configura en tu entorno
   local ambas variables anteriores y comprueba:

   ```powershell
   npm.cmd run build:verificar
   ```

   Esta comprobación revisa la configuración, no acredita que el servidor esté
   accesible. Rechaza direcciones de ejemplo, HTTP, direcciones IP y credenciales
   incrustadas. La compilación EAS repite el control automáticamente.

2. Con la cuenta Expo del equipo, vincula el proyecto **una sola vez**:

   ```powershell
   npx.cmd eas-cli login
   npx.cmd eas-cli init
   ```

   Conserva el `extra.eas.projectId` que genere y la firma administrada por EAS.
   No crees otra identidad ni regeneres la firma al actualizar la app.

3. Configura las mismas dos variables públicas en el entorno EAS `preview`
   mediante su panel (visibilidad de texto público). No basta con tenerlas en
   una terminal local: el servidor de compilación también debe recibirlas.

4. Genera y descarga el APK:

   ```powershell
   npx.cmd eas-cli build --platform android --profile preview
   ```

   Guarda el identificador del build, commit de origen, SHA-256 y certificado de
   firma junto con las capturas. El enlace que entrega EAS permite descargar el
   mismo APK en ambos teléfonos. Instálalo autorizando esa fuente de instalación
   en cada dispositivo. Desactiva esa autorización después si ya no la necesitas.

Las direcciones se incorporan al compilar: cambiarlas requiere generar otro APK.
El build de entrega desactiva HTTP sin cifrar y bloquea los permisos de micrófono
y superposición que no usa el producto.

### APK conectado a los servidores públicos en Windows

Las direcciones de #201 están en `servidores-publicos.json`: Dominio en
`https://dominio.canastamx.duckdns.org` y Analítica en
`https://analitica.canastamx.duckdns.org`. El responsable comprobó ambos estados
`UP` desde un teléfono el 25 de noviembre de 2026.

Con Node 20, SDK Android y JDK 21 configurados, ejecutar:

```powershell
npm.cmd run build:android -- -ServidoresPublicos
```

Resultado: `artifacts/canastamx-servidores.apk`. Lleva JavaScript y recursos
incluidos, exige HTTPS y desactiva HTTP sin cifrar. No necesita Docker, Expo,
servicios locales ni `adb reverse` para funcionar: requiere internet y los
servidores públicos disponibles. Este modo local conserva la firma de desarrollo
del proyecto nativo; todavía queda pendiente la firma final de distribución.
Para actualizar la validación instalada, utilizar la misma clave que en el APK
anterior; no desinstalar la app para resolver una firma diferente.

Verificar búsqueda, detalle, registro/sesión y canastas con los servicios locales
apagados. El estado `UP` comprueba disponibilidad, pero no acredita este recorrido.

### APK de validación local en Windows

Para revisar la app antes de contar con #201, se incluye un guion separado.
Requiere Android Studio con SDK/NDK y sus licencias aceptadas, JDK y Node 20 en
PATH. La primera compilación descarga componentes de Gradle y Android.
Usa JDK 17 o 21 en `JAVA_HOME`. `postinstall` aplica a React Native 0.83.10 la
[corrección de Foojay para Gradle 9](https://github.com/reactwg/react-native-releases/issues/1349).
Si la ruta del proyecto es larga, el guion compila una copia nueva bajo la
carpeta temporal, sin `.env`, y copia el APK de vuelta a `artifacts/`. Conserva
esa copia temporal para diagnosticar la compilación.

```powershell
npm.cmd run build:android -- -ValidacionLocal
```

Resultado: `artifacts/canastamx-validacion.apk`, generado con `expo prebuild` y
`gradlew assembleRelease`, con JavaScript y recursos empaquetados. Incluye ARM64
y x86_64 y usa **la firma de desarrollo del proyecto nativo generado**: es para
validar localmente, no es el APK firmado final de EAS. No intercambies ambas
firmas en una instalación que contenga información que quieras conservar.

Este APK se llama **CanastaMX · Validación** y consulta sólo
`127.0.0.1:8084` (dominio) y `127.0.0.1:8004` (analítica). Para usar servicios locales
necesita los correspondientes enlaces USB `adb reverse`. Es el único modo que
permite HTTP. No escribe `.env` ni contiene cuentas de prueba.

El guion genera `android/` a partir de la configuración Expo. Esa carpeta y los
APK, claves y artefactos están ignorados. No ejecutes prebuild sobre una carpeta
nativa editada a mano sin respaldar sus cambios.

## Comportamiento y datos

- **Registro:** `POST /api/v1/cuentas`, sin Bearer ni rol enviado. Correo válido,
  contraseña de 8–72 caracteres con mayúscula y número y confirmación. Un 409
  explica que la cuenta existe. Al terminar se solicita iniciar sesión; no se
  interpreta la creación de cuenta como una sesión iniciada. Las contraseñas se
  limpian al enviar y no se persisten. Si una petición de registro pierde la
  conexión, el aviso permite intentar entrar si la cuenta alcanzó a crearse.
- **Sesión:** `POST /sesiones` y `GET /cuentas/yo`. Sólo el token se conserva con
  SecureStore; el correo viene del servidor. Sólo entra el rol CONSUMIDOR. Al
  abrir o volver al primer plano se restaura la sesión; salir elimina sus datos.
- **Inicio:** búsqueda paginada real por artículo y entidad. La entidad elegida
  en el encabezado también se usa para el costo de canasta. Cambiarla descarta
  resultados antiguos. El catálogo se envía al servicio. El orden y el rango de precios filtran **sólo la página
  consultada**, como indica la pantalla; no representan todo el catálogo. Al abrir se ofrece una selección de artículos mediante búsquedas de productos habituales, sin inventar precios ni devolver todo el catálogo.
- **Detalle:** identidad canónica `producto` + `presentacion`; muestra precios
  por establecimiento, marca, fecha, entidad, quincena y población recibidos.
- **Canastas:** crear, seleccionar, renombrar, eliminar con confirmación, sumar,
  fijar cantidades y quitar artículos con confirmación; todo persiste mediante
  el dominio. Si una escritura pierde la respuesta, hay que recuperar el estado
  antes de enviar otra. Eliminar la última canasta deja disponible la creación.
- **Costo:** lo calcula la analítica. Se muestran estimaciones independientes
  por cadena y sus faltantes. No se suman cadenas para inventar un total de
  compra; un artículo sin precio no equivale a cero. Las fotografías son
  ilustrativas de categoría, porque el contrato no entrega fotografías de cada
  producto. No se inventan descuentos, precios anteriores ni marcas.

Conserva los avisos de precios observados QQP y «No somos PROFECO». El simulador
se identifica como datos de prueba. Fuentes de recursos: [assets/README.md](assets/README.md).

## Verificar

```powershell
npm.cmd test
npm.cmd run typecheck
```

La suite cubre acceso, registro, sesión, cancelación, contratos, simulador,
canastas y configuración de compilación. El simulador abre puertos temporales.
Guías anteriores: [T039](docs/evidencia/t039/README.md),
[T046](docs/evidencia/t046/README.md), [T051](docs/t051-busqueda-analitica.md) y
[T056](docs/t056-detalle-canasta.md).

### Aceptación pendiente en dos teléfonos distintos

Usar **el mismo APK de entrega** conectado a las direcciones públicas y repetir
en cada teléfono, con una cuenta nueva diferente:

1. Crear cuenta desde la app, comprobar confirmación e iniciar sesión.
2. Buscar un artículo y comparar precios en su detalle.
3. Crear canasta y agregar el artículo; aumentar/reducir cantidad.
4. Cerrar y reabrir: recuperar cuenta y canasta.
5. Comprobar el aviso de Descubrir, cambiar entidad y cerrar sesión.

Tomar capturas del registro completado, Cuenta, búsqueda, detalle, canasta y
Descubrir. No capturar contraseñas ni tokens. Anotar modelo/Android de cada
**teléfono físico**, fecha, red usada y build probado; adjuntar capturas al PR.
Un emulador, dos ejecuciones en un teléfono o las pruebas automáticas no cumplen
este criterio. Estado y evidencias: [T072](docs/t072-version-final.md).
