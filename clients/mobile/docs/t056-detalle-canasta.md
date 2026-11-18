# T056 · Detalle y canasta · #203

## Servicios y sesión

Con Node 20.20.2 y Expo Go SDK 55, configura las dos direcciones públicas en
`clients/mobile/.env`, tomando `.env.example` como referencia:

- `EXPO_PUBLIC_API_URL`: dominio, para la cuenta y las canastas; recibe Bearer.
- `EXPO_PUBLIC_ANALITICA_URL`: analítica, para búsqueda, precios y costo; estas
  tres operaciones son públicas y no reciben el token del dominio.

Reinicia Expo al cambiar direcciones. En un teléfono, `localhost` es el teléfono.
Para usar únicamente servicios locales con un emulador conectado por ADB, puedes
redirigir los puertos con `adb reverse tcp:PUERTO tcp:PUERTO`. Arranca Expo con
`--localhost`; si escucha sólo en IPv6 y el puente usa IPv4, utiliza Node con
`NODE_OPTIONS=--dns-result-order=ipv4first`. La depuración debe apagarse al terminar.

Las rutas de canasta de T050 y el costo de T069 ya están en `main`. Sigue los
README de `services/domain-service` y `services/analytics-api` para arrancarlos.
El usuario debe existir como `CONSUMIDOR`: la semilla de roles de infraestructura
sólo crea analista y operador. Para las pruebas, registra el consumidor sintético
con `POST /api/v1/cuentas` en una base aislada, usando credenciales de prueba.

## Comportamiento

Inicio pasa el par canónico del artículo y la entidad al detalle. `compararPrecios`
muestra cada establecimiento, marca, dirección y municipio disponibles, precio MXN
y fecha de registro. Su población es el número de registros por establecimiento
devueltos en esa consulta; no se inventa el total histórico de observaciones.

La canasta se guarda exclusivamente en el dominio. El selector permite recuperar
todas las páginas y trabajar con varias canastas. Agregar usa POST y suma; guardar
cantidad usa PUT y reemplaza. Sólo se permiten enteros positivos. Los cambios se
publican al confirmar la respuesta del dominio, sin persistencia local de líneas.
Cerrar sesión o cambiar de cuenta descarta los datos anteriores. No se reenvían
escrituras automáticamente: si su resultado es incierto, hay que actualizar la
canasta antes de enviar otro cambio.

`costearCanasta` recibe la entidad y las líneas guardadas. El móvil no suma ni
redondea los precios: muestra el dinero textual que devuelve el servicio. Cada
cadena indica su total, número de faltantes y precios unitarios medianos. `null`
significa «sin precio», excluido del total. Un total parcial se identifica como
tal. La población visible son los artículos pedidos y las cadenas devueltas en
esa entidad y quincena. No se atribuye un número de tiendas que el contrato no envía.
El costo se invalida al cambiar canasta, líneas, entidad o sesión.

Las consultas tienen un plazo de ocho segundos y admiten cancelación, reintento y
errores `application/problem+json`. Un 401 de canasta provoca revisar la sesión;
una canasta ajena o una línea ausente conserva el 404 del dominio.

## Simulador de desarrollo

`npm run simulador` conserva la búsqueda y entidades de Prism 5.14.2. Las rutas
`GET /api/v1/precios` y `POST /api/v1/canastas/costo` se amplían con fixtures
sintéticos de `mocks/canasta.cjs`, independientes de Prism. El costo de prueba
respeta las cantidades recibidas e incluye una cadena con un faltante. Esta
aritmética sólo vive en el simulador, nunca en el código del cliente.

El encabezado `x-canastamx-fuente: simulador` identifica las respuestas; el puerto
4011 también se reserva al simulador para mantener el aviso cuando no hay conexión.
No se cambia automáticamente a datos ficticios cuando falla un servicio real.

## Verificaciones reproducibles

Desde `clients/mobile` con Node 20:

```powershell
npm.cmd ci
npm.cmd test
npm.cmd run typecheck
npx.cmd expo export --platform android --output-dir RUTA_FUERA_DEL_REPOSITORIO
```

La suite prueba sesión, formatos de precios y fechas, cantidades, errores, plazo,
cancelación, paginación, doble pulsación, respuestas de otra cuenta y escritura de
resultado incierto. Las pruebas que arrancan Prism corren en serie para evitar
competir por recursos durante su inicio.

La prueba optativa `node tests/t056-real.cjs` necesita servicios reales locales,
una base aislada y `tests/fixtures/t056-analitica.sql` cargado **sólo en esa base**.
La semilla contiene dos artículos, tres registros de precio y sus medianas por
cadena. Es una semilla mínima para el cliente: no acredita la ingesta ni una carga
completa del modelo dimensional. No la apliques sobre datos de desarrollo.

Configura `EXPO_PUBLIC_API_URL`, `EXPO_PUBLIC_ANALITICA_URL`, `T056_EMAIL` y
`T056_PASSWORD` en el proceso y activa `CANASTAMX_PRUEBA_MOVIL_REAL=1`. La prueba
crea una canasta propia, comprueba sumar, fijar, quitar, costo y recuperar con una
sesión nueva; finalmente borra sólo esa canasta. No imprime credenciales.

## Recorrido Android

1. Inicia sesión con el consumidor sintético y busca «leche» en Guanajuato.
2. Toca Leche entera. Verifica dos establecimientos, fechas 2026-07-24 y
   2026-07-25, quincena 2026-07-Q2, población y origen de la interfaz real.
3. Crea «Canasta T056» en el detalle y agrega una unidad.
4. Regresa a Inicio, abre Leche descremada y agrégala a la misma canasta.
5. En Canasta, fija Leche entera en tres. La cantidad guardada debe ser tres.
6. Revisa el costo: A, 117.90 MXN completo; B, 90.00 MXN parcial, un faltante.
7. Quita Leche descremada. Queda Leche entera en tres; A, 85.50 MXN y B, 90.00 MXN.
8. Cierra la app y ábrela de nuevo: recupera la cuenta y la misma canasta desde
   el dominio. Revisa otra vez la cantidad y el costo.
9. Prueba cantidad cero o decimal, actualiza, y verifica recuperación tras un
   fallo de red. Si usas el simulador, comprueba su aviso visible.

El empaquetado y las pruebas HTTP no sustituyen este recorrido Android.
