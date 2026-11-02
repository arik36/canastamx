# T051 · Búsqueda de Inicio contra el simulador (#189)

## Preparar

Usa Node 20.20.2. Desde `clients/mobile/`:

```bash
npm ci
npm run simulador
```

La versión fijada es `@stoplight/prism-cli@5.14.2`. `mocks/servidor.cjs` lee el
contrato compartido `docs/analisis/openapi/analitica.yaml` 0.2.1 y genera una copia
JSON temporal con ejemplos. Prism escucha internamente en `127.0.0.1:4012`; un
adaptador de ejemplos recibe las consultas Android en `0.0.0.0:4011`, selecciona
el ejemplo mediante `Prefer` y devuelve la respuesta de Prism. Sólo admite GET
en `/health`, `/api/v1/entidades` y `/api/v1/articulos`. No modifica el contrato
compartido ni contiene un servicio analítico real.

El comando de la ficha también arranca Prism directamente sobre el contrato:

```bash
npx @stoplight/prism-cli@5.14.2 mock -h 0.0.0.0 -p 4011 docs/analisis/openapi/analitica.yaml
```

Ese comando se ejecuta desde la raíz y produce respuestas desde los esquemas,
pero el contrato no define ejemplos completos para los alternos. Para las cuatro
capturas usa `npm run simulador`, que permite reproducirlos por término y entidad.
No ejecutes ambas opciones a la vez en 4011.

## Configurar la app

Conserva `EXPO_PUBLIC_API_URL`, que utiliza el dominio y la sesión. Agrega a
`clients/mobile/.env`, ignorado por Git:

```dotenv
EXPO_PUBLIC_ANALITICA_URL=http://TU-IP:4011
```

`TU-IP` es la IPv4 de la computadora accesible desde Android. No es `localhost`
del teléfono. En otra terminal, desde `clients/mobile/`:

```bash
npx expo start --go --port 8082 -c
```

Usa Expo Go para SDK 55. El simulador no necesita Docker, base de datos, dominio,
cuenta ni token. La sección plegable de Inicio conserva la comprobación `/health`
del dominio para cuando ese servicio esté encendido.

## Escenarios reproducibles

| Artículo | Entidad | Respuesta esperada |
|---|---|---|
| `leche` | `Guanajuato` | Dos resultados, con precio típico, presentación, quincena 2026-07-Q2 y 12 u 8 observaciones |
| `inexistente` | `Guanajuato` | 200, cobertura true, total 0 y lista vacía: alterno 2a |
| `leche` | `Colima` | 200, cobertura false y las siete entidades: alterno 2b |
| `problema` | `Guanajuato` | 400, application/problem+json: título y detalle del problema |
| `leche` | `Guanajuato`, con el simulador detenido | Error de conexión, termina la carga y permite reintentar |

El corpus de prueba está en `mocks/escenarios.cjs`: dos leches y un arroz. Es
sintético y sólo existe en el proceso de desarrollo, no dentro del paquete de
la app. Escribir otros términos sin coincidencias devuelve la lista vacía.
La falta de cobertura precede a la búsqueda, como pide CU-12. Se puede consultar
cualquiera de las 32 entidades; siete tienen cobertura en los ejemplos. Una
entidad no reconocida devuelve un problema 400.

Para apagar ambos procesos pulsa Ctrl+C en la terminal de `npm run simulador`.
Vuelve a iniciarlo y pulsa Reintentar para comprobar recuperación. Los puertos
4011 y 4012 son propios de este simulador; 8081 sigue siendo del dominio.

## Comportamiento del cliente

- Búsqueda pública: no usa el token ni la URL del dominio.
- Valida al menos dos caracteres y una entidad; codifica los parámetros.
- Cada precio típico conserva el monto de texto y MXN. Muestra entidad,
  quincena y observaciones; no inventa marca ni variación.
- Distingue vacío y falta de cobertura; conserva los criterios editables.
- Al editar criterios cancela la solicitud anterior y retira los resultados
  anteriores. Una respuesta tardía no reemplaza la búsqueda nueva.
- Límite de ocho segundos, cancelación al desmontar y reintento ante error.
- Muestra `title`, `detail` y el estado HTTP de los problemas válidos del servicio.
- Solicita páginas de 20 con `limit` y `offset`; la población de cada precio
  corresponde a su artículo, no al total de resultados.
- La etiqueta de origen queda fija al desplazarse. El simulador se identifica
  por el encabezado `X-CanastaMX-Fuente: simulador`; antes de la primera respuesta
  o sin conexión, el puerto 4011 lo identifica como el puerto reservado de T051.

Para apuntar a T058 cambia sólo `EXPO_PUBLIC_ANALITICA_URL` a la dirección de la
analítica real y reinicia Expo. No se cambian las rutas ni se añaden cabeceras
`Prefer` al cliente; la selección de ejemplos pertenece al simulador. Usa otro
puerto para el servicio real; 4011 queda reservado a simulación.

## Validación y evidencia

```bash
npm test
npm run typecheck
```

La suite incluye una instancia real de Prism en el puerto interno 14012, con
puerto público temporal, y comprueba resultados, vacío, cobertura y problem+json.
Las pruebas de sesión anteriores siguen ejecutándose. El empaquetado y estas
pruebas no sustituyen las capturas de la interfaz Android.

Adjunta cuatro capturas: resultados, vacío, falta de cobertura y conexión fallida.
En todas debe ser visible «Simulador · datos de prueba». Indica si se hicieron en
un teléfono físico o en BlueStacks; no presentes el emulador como teléfono real.
La evidencia queda en `docs/evidencia/t051/` dentro del cliente.

Prism está fijado a la versión de la ficha. Sus dependencias de desarrollo tienen
avisos de npm audit; no se hizo una actualización forzada de Prism ni de Expo.
Prism y los ejemplos no se importan desde el código ejecutado en Android.
