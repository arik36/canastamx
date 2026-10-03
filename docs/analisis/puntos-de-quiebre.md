# Prototipo y Puntos de Quiebre

- **Archivo de Figma:** https://www.figma.com/make/yUK7s2m2NoGCHGk6vAkSTZ/CanastaMX-3.0

## Puntos de quiebre definidos

1. **Móvil (hasta 768px):** Diseño a una sola columna o cuadrículas de dos columnas pequeñas. Uso intensivo de barra de navegación inferior con acceso directo a "Inicio", "Descubrir", "Canasta" y "Cuenta". Implementación de menús modales que emergen desde la parte inferior de la pantalla. Aplica exclusivamente para la App Consumidor.
2. **Tableta (769px a 1024px):** Transición a diseños expandidos. Los elementos de listas pasan a organizarse en cuadrículas de tres o más columnas. Aplica para la App Consumidor.
3. **Web / Escritorio (1025px en adelante):** Uso de múltiples columnas, paneles laterales de navegación y tablas de datos complejas a lo ancho de la pantalla. Orientación completamente horizontal. Punto de quiebre obligatorio y exclusivo para las consolas internas de Operador y Analista.

## Comportamiento y navegación por vista

### 1. Acceso
- **Relación:** Pantalla raíz que permite seleccionar el perfil (Acceso, Operador, Analista o App consumidor) mediante la navegación superior.
- **Móvil / Tableta:** El formulario de inicio de sesión se adapta al ancho del dispositivo en una sola columna.
- **Web:** Diseño de pantalla dividida a dos columnas. Una fotografía de mercado abarca toda la mitad izquierda, mientras que el formulario de inicio de sesión se alinea a la derecha con un fondo claro.

### 2. Consola de Operador - Observabilidad
- **Relación:** Vista inicial del operador para monitorear el estado operativo y los incidentes activos. Conecta directamente con la Cola de Reconciliación a través de un menú lateral izquierdo.
- **Móvil / Tableta:** No aplica (Uso exclusivo web).
- **Web:** Tablero "dashboard" de múltiples columnas que presenta indicadores de estado, linaje entre activos y volumen en cuarentena en formato de tarjetas.

### 3. Consola de Operador - Cola de Reconciliación
- **Relación:** Accesible desde el menú lateral de la consola del operador. Sirve para realizar la asignación manual de variantes de artículos no resueltas.
- **Móvil / Tableta:** No aplica (Uso exclusivo web).
- **Web:** Se presenta como una tabla de revisión de diccionario a ancho completo. Muestra la cadena original contra la sugerida, una barra de progreso visual para el porcentaje de similitud, y botones alineados a la derecha para "Aprobar", "Rechazar" o seleccionar de forma "Manual".

### 4. Consola de Analista - Tablero Analítico
- **Relación:** Vista principal para el rol de analista. Permite contrastar la macroeconomía y detectar desviaciones, funcionando como puente hacia el detalle específico de cada artículo.
- **Móvil / Tableta:** No aplica (Uso exclusivo web).
- **Web:** Cuenta con un panel superior de filtros interactivos (fecha, catálogo, entidad, cadena comercial). El cuerpo se divide en dos secciones principales: gráficas comparativas del Índice vs INPC y variaciones extremas, y una tabla inferior listando artículos con comportamiento anómalo.

### 5. Consola de Analista - Detalle de Artículo
- **Relación:** Se despliega al seleccionar un artículo anómalo específico desde el tablero analítico.
- **Móvil / Tableta:** No aplica (Uso exclusivo web).
- **Web:** Presenta una cabecera con el artículo canónico y botones de exportación a CSV. La sección central incluye tarjetas de métricas, una gráfica de serie histórica multilínea interactiva comparando entidades, y finalmente una tabla desglosando el precio por establecimiento.

### 6. App Consumidor - Inicio y Descubrir
- **Relación:** Pantallas de navegación principal accesibles desde la barra inferior de la aplicación. Permiten buscar productos o consultar medias de costo.
- **Móvil:** La vista "Inicio" agrupa un buscador, filtros horizontales y presenta los artículos en una cuadrícula de dos columnas. La vista "Descubrir" apila tarjetas resúmenes organizadas por catálogos y costo por tienda en una lista vertical continua.
- **Tableta:** La cuadrícula de la vista de "Inicio" se adapta para mostrar tres o cuatro columnas de productos.
- **Web:** La cuadrícula aprovecha todo el espacio horizontal y los filtros pueden anclarse lateralmente.

### 7. App Consumidor - Detalle de Artículo
- **Relación:** Accesible al seleccionar la tarjeta de un producto. Contiene un botón superior de retroceso y facilita la inserción del ítem a una lista con el botón "Agregar a mi canasta".
- **Móvil:** Una imagen representativa del artículo encabeza la pantalla a ancho completo. Debajo, en una sola columna, se organiza el precio, un interruptor para activar el monitoreo de caída de precios y los controles de incremento de unidades.
- **Tableta / Web:** La vista se divide, posicionando la fotografía a la izquierda y el panel de interacción (monitoreo y agregar a canasta) a la derecha.

### 8. App Consumidor - Canastas y Cuenta
- **Relación:** Vistas de control de usuario localizadas en los últimos dos iconos de la barra de navegación inferior.
- **Móvil:** La vista "Canasta" presenta los productos enlistados y segmentados por tienda, cerrando con un panel oscuro anclado al inferior que muestra el costo total estimado. Cuenta con modales emergentes para gestionar múltiples canastas. La vista "Mi cuenta" despliega la información del perfil y botones directos hacia las alertas de precio mediante tarjetas horizontales.
- **Tableta / Web:** Las listas de canasta y configuración de cuenta se centran en el dispositivo o implementan navegación lateral para aprovechar resoluciones amplias.