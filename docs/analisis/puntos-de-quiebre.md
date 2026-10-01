# Prototipo y Puntos de Quiebre

- **Archivo de Figma:** [https://www.figma.com/make/yUK7s2m2NoGCHGk6vAkSTZ/CanastaMX-3.0?t=0uPnGylxUSXFBGoy-1]

## Puntos de quiebre definidos

1. **Móvil (hasta 768px):** Diseño a una sola columna o cuadrículas de dos columnas pequeñas[cite: 13]. Uso intensivo de barra de navegación inferior con acceso directo a "Inicio", "Descubrir", "Canasta" y "Cuenta"[cite: 13, 14, 15, 16]. Implementación de menús modales que emergen desde la parte inferior de la pantalla[cite: 13, 15]. Aplica exclusivamente para la App Consumidor[cite: 13, 14, 15, 16].
2. **Tableta (769px a 1024px):** Transición a diseños expandidos. Los elementos de listas pasan a organizarse en cuadrículas de tres o más columnas. Aplica para la App Consumidor.
3. **Web / Escritorio (1025px en adelante):** Uso de múltiples columnas, paneles laterales de navegación y tablas de datos complejas a lo ancho de la pantalla[cite: 10, 11, 12]. Orientación completamente horizontal[cite: 10, 11, 12]. Punto de quiebre obligatorio y exclusivo para las consolas internas de Operador y Analista[cite: 10, 11, 12].

## Comportamiento y navegación por vista

### 1. Acceso
- **Relación:** Pantalla raíz que permite seleccionar el perfil (Acceso, Operador, Analista o App consumidor) mediante la navegación superior[cite: 10].
- **Móvil / Tableta:** El formulario de inicio de sesión se adapta al ancho del dispositivo en una sola columna.
- **Web:** Diseño de pantalla dividida a dos columnas[cite: 10]. Una fotografía de mercado abarca toda la mitad izquierda, mientras que el formulario de inicio de sesión se alinea a la derecha con un fondo claro[cite: 10].

### 2. Consola de Operador - Observabilidad
- **Relación:** Vista inicial del operador para monitorear el estado operativo y los incidentes activos[cite: 10, 11]. Conecta directamente con la Cola de Reconciliación a través de un menú lateral izquierdo[cite: 10, 11].
- **Móvil / Tableta:** No aplica (Uso exclusivo web).
- **Web:** Tablero "dashboard" de múltiples columnas que presenta indicadores de estado, linaje entre activos y volumen en cuarentena en formato de tarjetas[cite: 10, 11].

### 3. Consola de Operador - Cola de Reconciliación
- **Relación:** Accesible desde el menú lateral de la consola del operador[cite: 11]. Sirve para realizar la asignación manual de variantes de artículos no resueltas[cite: 11].
- **Móvil / Tableta:** No aplica (Uso exclusivo web).
- **Web:** Se presenta como una tabla de revisión de diccionario a ancho completo[cite: 11]. Muestra la cadena original contra la sugerida, una barra de progreso visual para el porcentaje de similitud, y botones alineados a la derecha para "Aprobar", "Rechazar" o seleccionar de forma "Manual"[cite: 11].

### 4. Consola de Analista - Tablero Analítico
- **Relación:** Vista principal para el rol de analista[cite: 12]. Permite contrastar la macroeconomía y detectar desviaciones, funcionando como puente hacia el detalle específico de cada artículo[cite: 12].
- **Móvil / Tableta:** No aplica (Uso exclusivo web).
- **Web:** Cuenta con un panel superior de filtros interactivos (fecha, catálogo, entidad, cadena comercial)[cite: 12]. El cuerpo se divide en dos secciones principales: gráficas comparativas del Índice vs INPC y variaciones extremas, y una tabla inferior listando artículos con comportamiento anómalo[cite: 12].

### 5. Consola de Analista - Detalle de Artículo
- **Relación:** Se despliega al seleccionar un artículo anómalo específico desde el tablero analítico[cite: 12].
- **Móvil / Tableta:** No aplica (Uso exclusivo web).
- **Web:** Presenta una cabecera con el artículo canónico y botones de exportación a CSV[cite: 12]. La sección central incluye tarjetas de métricas, una gráfica de serie histórica multilínea interactiva comparando entidades, y finalmente una tabla desglosando el precio por establecimiento[cite: 12].

### 6. App Consumidor - Inicio y Descubrir
- **Relación:** Pantallas de navegación principal accesibles desde la barra inferior de la aplicación[cite: 13, 14]. Permiten buscar productos o consultar medias de costo[cite: 13, 14].
- **Móvil:** La vista "Inicio" agrupa un buscador, filtros horizontales y presenta los artículos en una cuadrícula de dos columnas[cite: 13]. La vista "Descubrir" apila tarjetas resúmenes organizadas por catálogos y costo por tienda en una lista vertical continua[cite: 14].
- **Tableta:** La cuadrícula de la vista de "Inicio" se adapta para mostrar tres o cuatro columnas de productos.
- **Web:** La cuadrícula aprovecha todo el espacio horizontal y los filtros pueden anclarse lateralmente.

### 7. App Consumidor - Detalle de Artículo
- **Relación:** Accesible al seleccionar la tarjeta de un producto[cite: 13, 14]. Contiene un botón superior de retroceso y facilita la inserción del ítem a una lista con el botón "Agregar a mi canasta"[cite: 14].
- **Móvil:** Una imagen representativa del artículo encabeza la pantalla a ancho completo[cite: 14]. Debajo, en una sola columna, se organiza el precio, un interruptor para activar el monitoreo de caída de precios y los controles de incremento de unidades[cite: 14].
- **Tableta / Web:** La vista se divide, posicionando la fotografía a la izquierda y el panel de interacción (monitoreo y agregar a canasta) a la derecha.

### 8. App Consumidor - Canastas y Cuenta
- **Relación:** Vistas de control de usuario localizadas en los últimos dos iconos de la barra de navegación inferior[cite: 15, 16].
- **Móvil:** La vista "Canasta" presenta los productos enlistados y segmentados por tienda, cerrando con un panel oscuro anclado al inferior que muestra el costo total estimado[cite: 15]. Cuenta con modales emergentes para gestionar múltiples canastas[cite: 15]. La vista "Mi cuenta" despliega la información del perfil y botones directos hacia las alertas de precio mediante tarjetas horizontales[cite: 16].
- **Tableta / Web:** Las listas de canasta y configuración de cuenta se centran en el dispositivo o implementan navegación lateral para aprovechar resoluciones amplias.