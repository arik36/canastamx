# Inventario de vistas

**Prototipo:** [CanastaMX 3.0 en Figma](https://www.figma.com/make/yUK7s2m2NoGCHGk6vAkSTZ/CanastaMX-3.0) ·
**Autora:** D, con C2 para la app · **Actualizado:** 6 de octubre de 2026

Las ocho vistas son las del protocolo. Este documento dice qué contiene cada una,
qué puede hacer quien la usa y qué datos pide.
- **Cómo se pasa de una a otra, y sus estados:** [`navegacion.md`](./navegacion.md).
- **Cómo se ve:** [`docs/entregas/diseno.md`](../entregas/diseno.md).
- **De qué ruta sale cada dato:** los contratos de `docs/analisis/openapi/`, que siguen en borrador.

| # | Vista | Cliente | Dónde vive | Dueño del dato |
|---|---|---|---|---|
| 1 | Acceso | Web y app | Primera pantalla | Dominio |
| 2 | Tablero analítico | Web | Barra lateral del analista | Analítica |
| 3 | Detalle de artículo | Web | Desde el tablero | Analítica |
| 4 | Consola de observabilidad | Web | Barra lateral del operador | Analítica |
| 5 | Cola de reconciliación | Web | Barra lateral del operador | Analítica |
| 6 | Búsqueda y catálogos | App | Pestañas **Inicio** y **Descubrir** (D-01) | Analítica |
| 7 | Mi canasta | App | Pestaña **Canasta** | Dominio y analítica |
| 8 | Cuenta y alertas | App | Pestaña **Cuenta** y la campana | Dominio y analítica |

---

## 1 · Acceso

- **Qué contiene:**
  - en la web, pantalla dividida con carrusel de mercado; en la app, capas sobre un fondo de mercado;
  - formulario de correo y contraseña;
  - en la app, el botón «Explorar artículos», que entra sin sesión;
  - **«No somos PROFECO»** y la fuente: datos abiertos de PROFECO.
- **Qué puede hacer:** entrar sin sesión (sólo la app), iniciar sesión o crear una cuenta.
- **Qué pide del sistema:** dominio · `POST /api/v1/cuentas` y `POST /api/v1/sesiones`.
- **Nota:** la barra de módulos de arriba del prototipo sólo sirve para recorrerlo.

## 2 · Tablero analítico

- **Qué contiene:**
  - filtros: desde, hasta, catálogo, entidad y cadena. En entidad, Colima y Nayarit aparecen como «sin datos en la fuente»;
  - el índice de la canasta contra el INPC, con base 100 en la primera quincena de enero de 2025 (ADR 015);
  - la dispersión de precio contra variación;
  - las variaciones extremas por cadena;
  - la tabla de artículos anómalos.
- **Qué puede hacer:** contrastar el índice con el INPC y abrir el detalle de un artículo anómalo.
- **Qué pide del sistema:** analítica · `GET /api/v1/indice` y `GET /api/v1/anomalias`. Qué cuenta como «anómalo» está pendiente (P-15).

## 3 · Detalle de artículo (web)

- **Qué contiene:**
  - el ícono del catálogo y la llave canónica del artículo;
  - cuatro indicadores: **precio típico** en el estado (la mediana), variación contra la quincena anterior, mínimo y máximo, todos con su población;
  - la serie histórica por entidad;
  - el precio por establecimiento.
- **Qué puede hacer:** recorrer la serie y exportar las observaciones a CSV.
- **Qué pide del sistema:** analítica · `GET /api/v1/articulos/serie`, `/establecimientos` y `/exportacion`.

## 4 · Consola de observabilidad

- **Qué contiene:** los seis indicadores (CU-05):
  1. última corrida;
  2. frescura, en «no aplica» mientras la fuente no publique;
  3. filas procesadas;
  4. volumen en cuarentena del alcance, con su porcentaje;
  5. avisos de esquema;
  6. incidentes abiertos.

  Además, el linaje entre capas y el historial, donde los avisos van en azul y los incidentes en rojo.
- **Qué puede hacer:** confirmar el estado en menos de 3 segundos, abrir un incidente y cerrarlo con su causa (CU-04).
- **Qué pide del sistema:** analítica · `GET /api/v1/operacion/estado`, `/corridas`, `/cuarentena` e `/incidentes`, y `POST …/incidentes/{id}/cierre`. Quién guarda el cierre está pendiente (P-08).
- **Cifras de hoy:** la cuarentena del alcance es como máximo de 5,992 filas, el 0.23%, en julio de 2026 (T031).

## 5 · Cola de reconciliación

- **Qué contiene:** el título «Revisión de diccionario»; la tabla con la variante, la cadena, la sugerencia y su parecido; la cobertura de normalización.
- **Qué puede hacer:** aprobar, rechazar o asignar a mano, sin mezclar gramajes distintos (CU-14).
- **Qué pide del sistema:** analítica · `GET /api/v1/reconciliacion/cola` y `POST …/resolucion`. Quién guarda la decisión está pendiente (P-08).

## 6 · Búsqueda y catálogos · pestañas Inicio y Descubrir

**Inicio**
- **Qué contiene:**
  - el buscador, sin escáner de código de barras;
  - los chips de los 5 catálogos;
  - ordenar por precio o por marca;
  - la cuadrícula de tarjetas, con el **ícono de su catálogo** (ADR 010 · 6) o foto marcada como ilustrativa;
  - el aviso «Bajaron {n} precios que vigilas» (D-05), sólo con sesión.
- **Qué puede hacer:** buscar, filtrar, ordenar, abrir el detalle y agregar a la canasta con el botón +. Los artículos «S/m» van al final por omisión.
- **Qué pide del sistema:** analítica · `GET /api/v1/entidades` y `GET /api/v1/articulos`.

**Descubrir**
- **Qué contiene:**
  - el panorama del estado: el índice por cadena del mes (1.000 es el precio típico) y la media por catálogo, cada uno con su población;
  - hasta abajo, **«Precios que bajaron»** (D-05).
- **Qué puede hacer:** ver cómo se comparan las cadenas, y desplegar la tabla por quincena de cada alerta que bajó.
- **Qué pide del sistema:** analítica (panorama y serie) y dominio · `GET /api/v1/alertas`.

**Detalle de artículo (app).** Es una hoja sobre la pestaña.
- **Qué contiene:** el precio típico con estado, quincena y observaciones, y los precios por establecimiento.
- **Qué puede hacer:**
  - elegir la cantidad y agregar a la canasta;
  - «Vigilar este precio», que pide un umbral **dentro del rango histórico** (CU-10).
- **Qué pide del sistema:** analítica · `GET /api/v1/precios` y `/rango-historico`; dominio · `POST /api/v1/alertas`.

## 7 · Mi canasta · pestaña Canasta

- **Qué contiene:** el selector de «Mis canastas»; los artículos **agrupados por cadena comercial**, con el subtotal de cada una; y un panel fijo con el costo estimado por cadena.
- **Qué puede hacer:**
  - cambiar cantidades (si una llega a 0, pide confirmación) y quitar artículos;
  - crear, renombrar y borrar canastas;
  - guardar. Sin sesión, la canasta vive en el teléfono hasta que inicia sesión (D-04).
- **Qué pide del sistema:**
  - dominio · `/api/v1/canastas` y sus líneas;
  - analítica · `POST /api/v1/canastas/costo`: precio por cadena como mediana de sus tiendas, «sin precio» cuando no hay dato, y cuántos faltan.

## 8 · Cuenta y alertas · pestaña Cuenta y la campana

- **Qué contiene:** el perfil; **Mis alertas** (cada una con su umbral y si está arriba o debajo); «Sobre nosotros», con «No somos PROFECO»; y cerrar sesión.
- **Qué puede hacer:** cambiar o borrar alertas y cerrar sesión. Una alerta avisa por correo cuando el precio cruza el umbral hacia abajo, y no repite mientras siga abajo (D-05).
- **Qué pide del sistema:** dominio · `/api/v1/alertas` y sus notificaciones; analítica · `/rango-historico` para cambiar el umbral.

---

## Dudas resueltas

1. **¿Fotos de los artículos?** Ícono genérico por catálogo (ADR 010 · 6). La fuente no trae foto de ningún artículo.
2. **¿Cuándo se pide el registro al invitado?** Al guardar la canasta o al vigilar un precio. Mientras tanto, la canasta vive en el teléfono (D-04).
