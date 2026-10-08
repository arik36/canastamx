# Sistema de diseño · CanastaMX

**Dueña:** D (Karen) · **La app la implementa:** C2 (Renato) · **Fecha:** 6 de octubre de 2026

**De dónde sale.** De lo que ya está construido en el prototipo, el proyecto de
Figma Make **CanastaMX 3.0**:
[Prototipo en Figma](https://www.figma.com/make/yUK7s2m2NoGCHGk6vAkSTZ/CanastaMX-3.0).
Los colores son las variables de su `src/index.css`. Las tipografías, radios y
componentes son los que usan sus tres apps: consumidor, analista y operador.

Integra dos decisiones del 6 de octubre (`docs/equipo/decisiones-pendientes.md`):
- **D-01:** cuatro pestañas en la app;
- **D-06:** los tonos son los de Figma, y el aviso es azul.

> **Esta versión reemplaza la tabla «Semántica de colores» anterior,** que pintaba
> el aviso de naranja (`#F59E0B`) y usaba otros tonos de verde y de rojo. El naranja
> se reserva para el mercado, y los tonos válidos son los de Figma.

---

## 1 · Colores

### Marca y superficie

| Token (`index.css`) | Tono | Para qué |
|---|---|---|
| `--color-turquoise` | `#23bbb7` | Marca: encabezado de la app, pestaña activa, chips activos, íconos |
| `--color-turquoise-600` | `#1aa5a1` | Hover de lo turquesa |
| `--color-turquoise-700` | `#158683` | Cifras y enlaces destacados sobre blanco |
| `--color-turquoise-boton` *(nuevo)* | `#137a77` | **Botones con texto blanco.** Con `#23bbb7` el texto blanco no se lee (2.37:1) |
| `--color-cream` | `#f0eadf` | Fondo de toda la app y de las consolas |
| `--color-cream-200` | `#e7dfd0` | Bordes, divisiones y campos de captura |
| `--color-ink` | `#2f2f2f` | Texto principal |
| `--color-ink-soft` | `#5b5b5b` | Texto secundario y metadatos |
| — | `#ffffff` | Tarjetas, sobre el fondo crema |

### Semántica · un color, un significado

| Significado | Relleno | Texto, ícono y borde | Cuándo |
|---|---|---|---|
| **OK** | `#00a859` (`--color-success`) | `#007a44` *(nuevo)* | El lote pasó, el precio bajó, la acción salió bien |
| **Aviso** *(D-06)* | `#89ccff` *(nuevo)* | `#0b5394` *(nuevo)* | El contrato dice «avisa»: deriva de esquema, frescura de 20 a 45 días, lote con avisos |
| **Incidente** | `#d32f2f` (`--color-danger`) | `#d32f2f` sobre blanco; `#c62828` *(nuevo)* sobre crema | El contrato dice «bloquea»: lote rechazado, compuerta caída, cuarentena que exige intervención |
| **Anomalía de mercado** | `#f2a900` (`--color-market`) | `#8a6100` (ya está en el prototipo) | El precio es raro, pero el dato está bien: «el huevo subió 27% en Jalisco» |
| **No aplica** | `#e7dfd0` (`--color-cream-200`) | `#5b5b5b` (`--color-ink-soft`) | La regla no corre: la frescura mientras la fuente no publique, que es el estado de hoy (`NO_APLICA`) |

**Reglas que no se rompen:**
1. **El rojo es sólo para lo que el sistema bloquea.** Un precio máximo, una
   subida o un duplicado resuelto no son incidentes.
2. **El naranja es sólo para el mercado.** Nunca para un estado del sistema.
3. **El azul de aviso no es «información» genérica:** es el nivel «avisa» del
   contrato.
4. **Los tonos claros (`#89ccff`, `#f2a900`) nunca son texto.** Van de fondo, con
   texto tinta encima, o se usa su variante oscura.

### Series de las gráficas

Sin significado de estado. Se usan cuando hay que distinguir líneas:

| Tono | En el prototipo |
|---|---|
| `#23bbb7` | Índice propio |
| `#4c6ef5` | INPC |
| `#7048e8` | Tercera serie |
| `#495057` | Referencias y ejes |

### Contraste medido (WCAG 2.1)

Para texto normal hace falta 4.5:1; para texto grande y componentes, 3:1.

| Par | Contraste | Resultado |
|---|---|---|
| Tinta sobre crema | 11.18 | Pasa |
| Blanco sobre `#137a77` (botón) | 5.15 | Pasa |
| Blanco sobre `#23bbb7` | 2.37 | **No pasa**: por eso existe el turquesa de botón |
| `#d32f2f` sobre blanco · sobre crema | 4.98 · 4.16 | Pasa · sólo texto grande |
| `#c62828` sobre crema | 4.70 | Pasa |
| `#8a6100` sobre blanco · sobre crema | 5.54 · 4.63 | Pasa |
| Tinta sobre `#f2a900` | 6.66 | Pasa |
| `#f2a900` como texto sobre blanco | 2.01 | **No pasa** |
| Tinta sobre `#89ccff` | 7.74 | Pasa |
| `#0b5394` sobre crema · sobre `#89ccff` | 6.55 · 4.53 | Pasa |
| `#89ccff` como texto sobre blanco | 1.73 | **No pasa** |
| `#00a859` como texto sobre crema | 2.60 | **No pasa**: por eso existe `#007a44` |
| `#007a44` sobre crema | 4.54 | Pasa |

### Para copiar

**`index.css` (web):**
```css
@theme {
  --color-turquoise-boton: #137a77;
  --color-success-text: #007a44;
  --color-aviso: #89ccff;
  --color-aviso-text: #0b5394;
  --color-danger-text: #c62828;
  --color-market-text: #8a6100;
}
```

**`clients/mobile/theme/design-system.ts` (app), los mismos valores:**
```ts
export const colores = {
  turquesa: '#23bbb7', turquesaBoton: '#137a77', turquesa700: '#158683',
  crema: '#f0eadf', crema200: '#e7dfd0', tinta: '#2f2f2f', tintaSuave: '#5b5b5b',
  ok: '#00a859', okTexto: '#007a44',
  aviso: '#89ccff', avisoTexto: '#0b5394',
  incidente: '#d32f2f', incidenteTexto: '#c62828',
  mercado: '#f2a900', mercadoTexto: '#8a6100',
} as const
```

---

## 2 · Tipografía

**Inter**, pesos 400 a 800, con `ui-sans-serif` y `system-ui` de respaldo.

| Uso | Tamaño | Peso |
|---|---|---|
| Título de pantalla | 24 px | 800 |
| Título de tarjeta | 18 px | 700 |
| Cuerpo | 14 px | 400 o 600 |
| Etiquetas y botones | 13 a 14 px | 700 |
| Metadatos: fecha, población, «S/m» | **11 px como mínimo** | 600 |

**En el prototipo hay 17 textos de 9 y 10 px.** Bajan a 11 px: con menos no se lee
en un teléfono.

## 3 · Forma

| Elemento | Radio |
|---|---|
| Tarjeta | 16 px |
| Modal y hoja inferior | 24 px |
| Botón | 12 px, o píldora completa |
| Chip de catálogo | Píldora |

- **Espaciado:** múltiplos de 4 px. Lo más común es 16 o 20 px de relleno y 8 o 12 px de separación.
- **Sombra:** una sola, suave, en las tarjetas sobre crema.
- **Área táctil:** 44 × 44 px como mínimo (los botones − y + del prototipo ya miden eso).

## 4 · Puntos de quiebre

| Nombre | Ancho | Dónde se usa |
|---|---|---|
| Teléfono | hasta 768 px | La app, y el acceso web |
| Tableta | de 769 a 1024 px | El acceso web. Las consolas muestran el aviso de ancho mínimo |
| Escritorio | desde 1025 px | Las consolas del analista y del operador |

**Implementación.** Los valores por omisión de Tailwind son 768 y 1024, un píxel
distintos de la tabla. Para que el código diga lo mismo que este documento:

```css
@theme {
  --breakpoint-md: 769px;
  --breakpoint-lg: 1025px;
}
```

**D-08 (7 de octubre): las consolas son sólo de escritorio,** como define
`puntos-de-quiebre.md` (#125). Por su densidad de datos, una consola en una columna
dejaría de servir. Debajo de 1025 px muestran un aviso de ancho mínimo y permiten
desplazarse de lado. **El acceso web sí se adapta a los tres anchos.**

La propuesta entregada (E1) prometía una «aplicación web responsiva en tres puntos
de quiebre». El cambio de alcance se le explica al asesor en el documento de la
entrega 2.

---

## 5 · Componentes

### App · lo que se repite en todas las pestañas

| Componente | Qué es | Reglas |
|---|---|---|
| **Barra superior** | Selector de estado, campana de alertas y avatar | Debajo dice «Mostrando sólo artículos registrados en {estado} · {mes y año del dato}». **Siempre con la fecha del dato**, hoy julio de 2026 |
| **Barra inferior** *(D-01)* | Cuatro pestañas: **Inicio, Descubrir, Canasta y Cuenta** | La pestaña activa, en turquesa con una barra arriba. Canasta lleva un globo con el número de artículos |
| **Aviso de precios que bajaron** *(D-05)* | Una franja sobre la barra inferior: «Bajaron {n} precios que vigilas» | Sólo con sesión y con n > 0. Fondo turquesa con texto blanco. **No es rojo:** una baja de precio no es un incidente. Ver `navegacion.md` §3 |
| **Notificación breve** | Mensaje que aparece y se va | Verde si salió bien, rojo si falló |

### App · artículos y canasta

| Componente | Qué es | Reglas |
|---|---|---|
| **Tarjeta de artículo** | Ícono, nombre, marca · presentación, precio típico, variación y botón + | **Ícono de su catálogo** (ADR 010 · 6). Si se usa foto, lleva «Imagen ilustrativa». La variación se pinta verde si baja y naranja si sube. «S/m» va al final de la lista |
| **Chips de catálogo** | Los 5 catálogos oficiales | Uno activo a la vez, en turquesa |
| **Detalle de artículo** | Hoja que sube sobre la pestaña | Precio típico **con su población**: estado, quincena y observaciones. Cantidad con − y +. «Agregar a mi canasta». Alerta con umbral **que elige la persona** dentro del rango histórico (CU-10) |
| **Grupo de cadena** | Una tarjeta por cadena comercial, con sus artículos y su total | Agrupa por **cadena**, no por sucursal. Si a una cadena le falta un artículo, ese renglón dice «sin precio» y el total dice «falta 1 precio» |
| **Total de la canasta** | Panel oscuro fijo abajo | El total de cada cadena, uno por renglón. Nunca un monto inventado |
| **Modales de canasta** | Elegir, crear, renombrar y borrar | Antes de borrar, confirmar |

### Web

| Componente | Qué es | Reglas |
|---|---|---|
| **Barra lateral** | Navegación de cada consola | El analista: Tablero y Detalle. El operador: Consola y Cola |
| **Tarjeta de indicador** | Una cifra grande con su rótulo | **Siempre con su población**, por ejemplo «del alcance · julio de 2026» |
| **Semáforo** | Estado de la última corrida y de la frescura | Verde OK, azul aviso, rojo incidente, gris «no aplica». Nunca naranja |
| **Historial** | Avisos e incidentes de la consola (RF-13) | Los avisos en azul, sin botón de cerrar; los incidentes en rojo, con «Cerrar con causa» |
| **Dona** | Una proporción | Con su número al centro y su población debajo |
| **Linaje** | Archivo → cruda → compuerta → intermedia → consumo | Cada nodo con sus filas |
| **Barra de parecido** | El parecido de una variante en la cola | Del 0 al 100%, en turquesa |
| **Métricas de la cola** | Cobertura de normalización, precisión y variantes en cola | Cada porcentaje con su población («412 de 506 variantes»). Hasta medirse, «se mide en T058» |
| **Tabla** | Cola, cuarentena, precios por establecimiento | Encabezado fijo; desplazamiento lateral dentro de su tarjeta |

---

## 6 · Reglas de contenido

Vienen de los datos y del contrato:

1. **Toda cifra visible dice su población y su fecha** (RNF-16): de qué estado, de qué quincena y cuántas observaciones.
2. **«Precio típico» es la mediana** de las observaciones (T031). No se escribe «promedio» si no es promedio, ni «media ponderada».
3. **Los datos llegan hasta julio de 2026.** La fuente no publica desde entonces. Ningún texto dice «al día» ni pone fechas posteriores.
4. **«No somos PROFECO»** aparece en Acceso y en Cuenta.
5. **Fuera de las 7 entidades,** el mensaje es de cobertura y nombra las siete; no es un error.
6. **Sin dato no hay monto:** se escribe «sin precio».

## 7 · Lo que el prototipo todavía no cumple

| # | Dónde | Qué hay | Qué debe haber | Quién |
|---|---|---|---|---|
| 1 | Consola | INC-2831 «18 columnas vs 15» en rojo, con el lote «rechazado» | Aviso en azul; el lote entra completo | D |
| 2 | Consola | INC-2829 «duplicados» en naranja | Una captura doble no es incidente: se resuelve sola | D |
| 3 | Consola | Frescura «2ª de septiembre · al día», lote «L-2026-Q18» | `07-2026_Q2`; frescura «no aplica: la fuente no publica desde julio» | D |
| 4 | Consola | «1,896 registros retenidos» | Como máximo 5,992, el 0.23% del alcance | D |
| 5 | App · Descubrir | «Media de costo por tienda» (Walmart $44.80), sin población | El índice por cadena de T031 (1.000 = precio típico), con mes y número de artículos | D y C2 |
| 6 | App · Canasta | Grupos por sucursal («Walmart · Plaza Mayor») y «Sucursal no verificada» | Por cadena, con «sin precio» | D y C2 |
| 7 | App · Detalle | Umbral fijo en el 95% del precio | Lo elige la persona, dentro del rango histórico | D y C2 |
| 8 | App · Tarjetas | Fotos sin marcar | Ícono de catálogo, o «Imagen ilustrativa» como ya hace el detalle | D |
| 9 | Web · Detalle | «Precio promedio regional · media ponderada»; el máximo en rojo | «Precio típico (mediana)»; el máximo en tinta | D |
| 10 | Datos de ejemplo | Fechas «11 sep 2026» | Fechas hasta julio de 2026 | D |
| 11 | App · Descubrir | Listas «Despensa Quincenal», «Fiesta Navidad» y «Desayunos» | No las pide ningún caso de uso ni requerimiento. Se definen o se quitan | D y C2 |
| 12 | App · Cuenta | El nombre «Karen Alejandra» y una foto de perfil | El correo de la cuenta y un avatar con su inicial: la cuenta no tiene nombre ni foto (P-13) | D y C2 |
| 13 | Web · Barra lateral | «Analista Ruiz» | El correo y el rol de la sesión (P-07 y P-13) | D |
| 14 | Web · Cola | Cobertura 81.4% y precisión 97.3% | Son inventadas, y la cobertura queda por debajo de la meta de H3 (85%). «Se mide en T058», o la cifra real con su población | D |
