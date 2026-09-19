# Inventario de vistas

<!-- Lo llena D (Karen) en T015 · lunes 7 de septiembre.
     LAS OCHO VISTAS YA ESTÁN DEFINIDAS EN EL PROTOCOLO. No las inventes: si propones otras, el prototipo del 18 de septiembre no va a corresponder al documento entregado el mismo día.
     Tu trabajo es decidir QUÉ CONTIENE CADA UNA Y EN QUÉ ORDEN, que es donde está el diseño de verdad. -->

**Archivo de Figma:**  [Inserta aquí tu enlace actualizado de Figma] <!-- compartido con permiso de lectura para cualquiera con el enlace; pruébalo en incógnito --> 
https://www.figma.com/make/yUK7s2m2NoGCHGk6vAkSTZ/CanastaMX-3.0?t=683ef0vKAnPmN7j4-1
**Autora:** D · **Fecha:** 18 de septiembre de 2026

---

| # | Vista | Cliente | Dueño del dato | A quién le pregunto |
|---|---|---|---|---|
| 1 | Acceso | Web y móvil | Servicio de dominio | C1 |
| 2 | Tablero analítico | Web | Interfaz analítica | A |
| 3 | Detalle de artículo | Web | Interfaz analítica | A |
| 4 | Consola de observabilidad | Web | Interfaz analítica | A |
| 5 | Cola de reconciliación | Web | Interfaz analítica | A |
| 6 | Búsqueda y Catálogos | Móvil | Interfaz analítica | A |
| 7 | Mi canasta | Móvil | Dominio y analítica | C1 y A |
| 8 | Cuenta y Alertas | Móvil | Servicio de dominio | C1 |

---

## 1 · Acceso
- **Qué contiene:** Versión Web dividida con carrusel fotográfico. Versión Móvil en capas con fondo de mercado. Ambos utilizan la paleta Turquesa/Crema. Botones de "Explorar artículos" (modo invitado) e "Iniciar sesión".
- **Qué puede hacer el usuario:** Entrar a navegar directamente o iniciar sesión. NO hay selectores de rol de usuario visibles.
- **Qué necesita del sistema:** Conexión a la base transaccional para validación de credenciales.

## 2 · Tablero analítico
- **Qué contiene:** Filtros superiores separados (Desde/Hasta, Categoría por 5 catálogos oficiales, Entidad Federativa indicando que Colima/Nayarit no tienen datos en fuente, y Cadena). Gráficos de líneas y dispersión.
- **Qué puede hacer el usuario:** Contrastar evolución vs INPC y detectar variaciones extremas. Al hacer clic en la tabla de artículos anómalos, navega directo al detalle.
- **Qué necesita del sistema:** Métricas pre-agregadas desde la capa de consumo en esquema estrella.

## 3 · Detalle de artículo
- **Qué contiene:** Foto representativa, ID Canónico y precio promedio regional (NO nacional). Gráfico histórico a 12 meses y tabla comparativa de precios exactos desglosados por establecimientos.
- **Qué puede hacer el usuario:** Inspeccionar el comportamiento en el tiempo de un artículo puntual y exportar datos a CSV.
- **Qué necesita del sistema:** Extracción de la serie histórica del almacén analítico para un SKU específico.

## 4 · Consola de observabilidad
- **Qué contiene:** Los seis indicadores clave. Destaca el volumen en cuarentena con el dato real (3.61% del corpus · 770,273 registros retenidos)[cite: 5] y el historial de incidentes (INC-2831 · Deriva de esquema · 18 columnas detectadas vs. 15 esperadas)[cite: 5].
- **Qué puede hacer el usuario:** Confirmar en 3 segundos el estado de la ingesta (frescura por lote, no por cadena)[cite: 5].
- **Qué necesita del sistema:** Logs del orquestador, metadatos y registros directos de la tabla de cuarentena.

## 5 · Cola de reconciliación
- **Qué contiene:** Título estricto "Revisión de Diccionario" (Se descarta el término "comparación difusa")[cite: 2, 5]. Tabla con nombres originales, cadena y coincidencia sugerida. La tarjeta de cobertura muestra el porcentaje sin una meta estática grabada[cite: 5].
- **Qué puede hacer el usuario:** Aprobar, rechazar o asignar manualmente sin mezclar gramajes distintos[cite: 5].
- **Qué necesita del sistema:** Vocabulario canónico y los algoritmos de normalización del proceso de transformación.

## 6 · Búsqueda y Catálogos (Inicio / Descubrir)
- **Qué contiene:** Barra de búsqueda sin escáner de código de barras[cite: 5]. Filtros deslizables para los 5 catálogos oficiales (Básicos, PACIC, Frutas y Legumbres, Mercados, Pescados y Mariscos)[cite: 4, 5]. Cuadrícula de resultados.
- **Qué puede hacer el usuario:** Buscar artículos, ordenar por precio/marca. Los artículos "S/m" (Sin marca) se envían al final de la lista por omisión[cite: 5].
- **Qué necesita del sistema:** Catálogo limpio unificado y consulta ágil a los últimos precios de la capa oro.

## 7 · Mi canasta
- **Qué contiene:** Selector de "Mis Canastas". Lista de artículos dividida ESTRICTAMENTE por sucursal (ej. Sección Walmart, Sección Soriana) para el cálculo de subtotales[cite: 5].
- **Qué puede hacer el usuario:** Sumar los costos, ver cuánto cuesta el súper en cada establecimiento y gestionar cantidades. Si reduce un artículo a 0, recibe alerta de confirmación[cite: 6].
- **Qué necesita del sistema:** Cruce del carrito de compras transaccional con la tabla de hechos (precios vigentes).

## 8 · Cuenta y Alertas
- **Qué contiene:** Perfil de usuario, información sobre el uso de datos abiertos PROFECO y un menú/resumen independiente de alertas activas.
- **Qué puede hacer el usuario:** Administrar su sesión y configurar notificaciones (ej. "Avisarme si la pechuga baja de $85.00").
- **Qué necesita del sistema:** Servicio de dominio para cruzar las reglas guardadas con la última corrida de datos.

---

## Dudas para la reunión del lunes

1. Puesto que vamos a mostrar fotos en los resultados de búsqueda (Vista 6), ¿cómo se manejará si en los datos abiertos de la fuente algún artículo no trae fotografía oficial asociada? ¿Tendremos algún icono por defecto o conectaremos un banco de imágenes externo?

NA para productos que no tienen foto oficial

2. Al integrar el modo "Explorar artículos" sin inicio de sesión en la vista de Acceso, ¿en qué momento exacto le pediremos al usuario que se registre? ¿Al darle "+ Agregar" a la canasta, o al intentar "Guardar canasta"?

Al guardar canasta 
