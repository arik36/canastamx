# Inventario de vistas

<!-- Lo llena D (Karen) en T015 · lunes 7 de septiembre.

     LAS OCHO VISTAS YA ESTÁN DEFINIDAS EN EL PROTOCOLO. No las inventes: si propones otras, el prototipo del 18 de septiembre no va a corresponder al documento entregado el mismo día.

     Tu trabajo es decidir QUÉ CONTIENE CADA UNA Y EN QUÉ ORDEN, que es donde está el diseño de verdad. -->

**Archivo de Figma:**  https://www.figma.com/make/4IwoeyKda0fkYkNxCIWKjT/CanastaMX?t=AqPXIKml2qEO3lOL-1 <!-- compartido con permiso de lectura para cualquiera con el enlace; pruébalo en incógnito -->
**Autora:** D · **Fecha:** 11 de septiembre de 2026

---

| # | Vista | Cliente | Dueño del dato | A quién le pregunto |
|---|---|---|---|---|
| 1 | Acceso | Web y móvil | Servicio de dominio | C1 |
| 2 | Tablero analítico | Web | Interfaz analítica | A |
| 3 | Detalle de producto | Web | Interfaz analítica | A |
| 4 | Consola de observabilidad | Web | Interfaz analítica | A |
| 5 | Cola de reconciliación | Web | Interfaz analítica | A |
| 6 | Búsqueda | Móvil | Interfaz analítica | A |
| 7 | Mi canasta | Móvil | Dominio y analítica | C1 y A |
| 8 | Alertas | Móvil | Servicio de dominio | C1 |

---

## 1 · Acceso

- **Qué contiene:** Carrusel dinámico de imágenes con frase reflexiva. Botón primario de "Explorar productos" (modo invitado) y formulario/botón secundario de "Iniciar sesión" integrado en la misma pantalla.
- **Qué puede hacer el usuario:** Decidir si entra a navegar directamente el catálogo o iniciar sesión para funciones guardadas y vistas de analista/operador.
- **Qué necesita del sistema:** Conexión a la base transaccional para validación de credenciales.

## 2 · Tablero analítico

<!-- Del protocolo: evolución de precios por categoría, entidad y cadena;
     dispersión; productos con comportamiento anómalo; contraste contra el INPC.
     Usuario: el ANALISTA, no el consumidor. -->

- **Qué contiene:** Filtros superiores por fecha, entidad y cadena. Gráfico principal comparativo contra el INPC, gráfico de dispersión de precios y tabla de productos anómalos.
- **Qué puede hacer el usuario:** Contrastar el impacto de la inflación oficial con la canasta local y detectar variaciones extremas por cadena en Guanajuato.
- **Qué necesita del sistema:** Métricas pre-agregadas desde la capa de consumo en esquema estrella.

## 3 · Detalle de producto

- **Qué contiene:** Foto referencial y nombre canónico. Gráfico histórico de la evolución del precio a 12 meses y tabla de precios por supermercado para ese artículo puntual.
- **Qué puede hacer el usuario:** Inspeccionar a detalle el comportamiento en el tiempo de un producto y exportar esos datos a CSV/Excel.
- **Qué necesita del sistema:** Extracción de la serie histórica del almacén analítico para un SKU específico.

## 4 · Consola de observabilidad

<!-- LOS SEIS INDICADORES, del protocolo. No son negociables ni ampliables:
     1. Estado de la última ejecución
     2. Frescura por fuente
     3. Resultado de las validaciones
     4. Linaje entre activos
     5. Historial de incidentes
     6. Volumen en cuarentena

     Usuario: el OPERADOR DE DATOS. Abre la pantalla para responder una sola
     pregunta: ¿está todo bien? Si un incidente no salta a la vista en tres
     segundos, el mecanismo de detección no sirve de nada. -->

- **Qué contiene:** Los seis indicadores en tarjetas amplias. Destaca el volumen en cuarentena (0.36%) y la lista de incidentes reales (ej. "Corrupción de codificación: 753,054 filas afectadas").
- **Qué puede hacer el usuario:** Confirmar en 3 segundos si el flujo está sano o localizar inmediatamente dónde se rompió la ingesta.
- **Qué necesita del sistema:** Logs del orquestador, metadatos y registros directos de la tabla de cuarentena.

## 5 · Cola de reconciliación

- **Qué contiene:** Indicadores de cobertura (>85%) y precisión. Tabla con nombres originales de la fuente, su cadena, sugerencia de diccionario y porcentaje de similitud.
- **Qué puede hacer el usuario:** Aprobar manualmente una sugerencia del comparador difuso o forzar el vínculo de un producto no reconocido hacia el diccionario canónico.
- **Qué necesita del sistema:** Vocabulario canónico y los algoritmos de comparación del proceso de transformación.

## 6 · Búsqueda

- **Qué contiene:** Barra de búsqueda, filtros horizontales activables por categoría (ej. Lácteos) resaltados en color, banner de destacados ("Los que más bajaron") y cuadrícula de tarjetas de productos.
- **Qué puede hacer el usuario:** Buscar artículos rápido viendo fotos reales y el precio más bajo resaltado en verde junto al nombre del supermercado.
- **Qué necesita del sistema:** Catálogo limpio unificado y consulta ágil a los últimos precios de la capa oro.

## 7 · Mi canasta

- **Qué contiene:** Lista de artículos seleccionados con controles para ajustar cantidades (+/-) y un panel flotante inferior con el desglose total estimado.
- **Qué puede hacer el usuario:** Sumar los costos de su súper, ver qué establecimiento le da la cuenta más baja y guardar la canasta final.
- **Qué necesita del sistema:** Cruce del carrito de compras transaccional con la tabla de hechos (precios vigentes).

## 8 · Alertas

- **Qué contiene:** Tarjetas descriptivas de las reglas de precios que vigila el usuario, botones flotantes para alta de nuevas alertas e interruptores on/off.
- **Qué puede hacer el usuario:** Configurar que el sistema le avise cuando el "Aceite marca X" baje de cierto precio.
- **Qué necesita del sistema:** Servicio de dominio para cruzar la regla guardada del usuario con la última corrida de datos.

---

## Dudas para la reunión del lunes

1. Puesto que vamos a mostrar fotos en los resultados de búsqueda (Vista 6), ¿cómo se manejará si en los datos abiertos de Profeco algún producto no trae fotografía oficial asociada? ¿Tendremos algún icono por defecto o conectaremos un banco de imágenes externo?

2. Al integrar el modo "Explorar productos" sin inicio de sesión en la vista de Acceso, ¿en qué momento exacto le pediremos al usuario que se registre? ¿Al darle "+ Agregar" a la canasta, o al intentar "Guardar canasta"?
