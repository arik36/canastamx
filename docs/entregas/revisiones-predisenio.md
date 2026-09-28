# Revisión de T024 · inventario de vistas y wireframes

- **Revisa:** A (Ariadne) · **Fecha:** 19 de septiembre de 2026  
- **Revisado:** `docs/analisis/inventario-vistas.md` y el PDF de Figma con 13 pantallas  
- **Tarea:** *«Llenar el inventario de las ocho vistas y hacer sus wireframes. El sistema de diseño, si sobra tiempo. Empezar por la consola de observabilidad, que ya tiene sus seis indicadores definidos.»*

## Diseño Seleccionado
- Paleta de colores
turquesa #23BBB7, 
crema #F0EADF,
tinta #2F2F2F, 
verde éxito #00A859, 

tipografía Inter, y  rojo sólo para incidentes del sistema, 
naranja para anomalías de mercado. 
Estan declarados en index.css.

## Veredicto

| Parte | Estado |
| :---- | :---- |
| Inventario de las ocho vistas | **completo**, con las tres secciones de cada una |
| Wireframes de las ocho | **correcto** y de sobra: hay 13 pantallas |
| Empezar por la consola de observabilidad | **correcto** y  los seis indicadores están |
| Sistema de diseño | ⚠ hay identidad visual, no hay documento |

&nbsp;

**Y algo más que hay que decir antes que nada: ya no son wireframes.** La tarea pedía baja fidelidad y lo que llegó es alta fidelidad, con paleta, tipografía, fotografía y estados. Eso está por encima de lo pedido y ahorra trabajo de T029.

&nbsp;

---

## Lo que se corrigió, y era lo que bloqueaba

**Resolvió la suplantación de PROFECO.** La revisión anterior marcó como bloqueante que el diseño se presentara como sistema oficial. Ahora:

&nbsp;

- El logotipo dice *«Fuente: datos abiertos de PROFECO · Quién es Quién en los Precios»*, que es exactamente lo que somos.  
- El correo de ejemplo es `nombre@ejemplo.com`, no uno de dominio oficial.  
- Y en **Mi cuenta · Sobre nosotros** lo dice con todas sus letras: *«**No somos PROFECO**; usamos su información pública para ayudarte a decidir dónde comprar más barato.»*

&nbsp;

Eso era el único bloqueo real que tenía el frente web. Está cerrado.

&nbsp;

**Declara la cobertura en cada pantalla.** El encabezado del móvil trae permanentemente *«Estado: Guanajuato · Mostrando solo artículos registrados en Guanajuato»*, y el filtro de la web anota que Colima y Nayarit no tienen datos en la fuente. Es el ADR 001 aplicado en la interfaz, y con más insistencia de la que se le pidió.

&nbsp;

**Los catálogos son los correctos.** Los chips de búsqueda y la sección Descubrir usan **exactamente los cinco del ADR 005**: Básicos, PACIC, Frutas y Legumbres, Mercados, Pescados y Mariscos. No inventó categorías ni dejó las del protocolo viejo.

&nbsp;

**La cola de reconciliación entendió la regla difícil.** La nota *«Nunca se combinan gramajes distintos»* es literalmente la regla que salió de mirar una muestra mala: en esta fuente el número define el artículo y las letras son las que varían. Y usó `Mazatún`, que es un caso real de la muestra de H3. Eso no se adivina, se lee.

&nbsp;

---

## Lo que hay que corregir antes de enseñarlo

### 1 · La frase del acceso web es incorrecta en sus tres afirmaciones

> *«Datos en tiempo real de más de 80,000 artículos en toda la República.»*

&nbsp;

| Dice | Lo medido |
| :---- | :---- |
| «en tiempo real» | QQP se publica **por quincena**. El contrato declara frescura quincenal y hoy arrastra 48 días de retraso |
| «más de 80,000 artículos» | **1,597** en el alcance del contrato. Ni el corpus completo llega: son 5,015 |
| «en toda la República» | **Siete entidades**, fijadas por el ADR 001 |

&nbsp;

Lo delicado es que **la app móvil de ella misma dice la verdad** en su encabezado. Es una frase de mercadotecnia que contradice al resto del diseño, y es justo la primera que ve quien abre el sistema.

&nbsp;

Propuesta: *«Precios quincenales de 1,597 artículos en siete entidades del centro-occidente.»* Menos vistosa y verificable, que es lo que le conviene a un proyecto sobre calidad de datos.

&nbsp;

Por lo mismo, **«Acceso institucional»** vuelve a sugerir respaldo de una institución. Mejor *«Acceso para analistas y operadores del equipo»*.

### 2 · El «artículo canónico» de la web lleva marca; el del móvil no

- **Web:** «Huevo Blanco **Bachoco** 30 piezas», rotulado `ARTÍCULO CANÓNICO`.  
- **Móvil:** «Huevo blanco» como título y «Bachoco · 16 pzas» debajo.

&nbsp;

**El móvil está bien y la web contradice al ADR 002**: el artículo es `producto` \+ `presentacion`, y la marca es atributo, no identidad. Si la marca entra al nombre canónico, Lala y Alpura de un litro son dos artículos y la app deja de poder comparar precios, que es para lo que existe.

&nbsp;

Hay que unificar hacia el criterio del móvil: título «Huevo Blanco · 30 piezas», marca como dato de la ficha.

### 3 · Tres cifras de la consola de observabilidad no corresponden a los datos

**Volumen en cuarentena: «3.61% del corpus · 770,273 registros retenidos».** Esa cifra es real, pero es **el bug del `?`**, y el contrato decidió **repararlo**, no ponerlo en cuarentena: el 96.63% es reparable por gemelo de longitud. Mostrarlo como cuarentena dice lo contrario de lo que se decidió.

&nbsp;

**INC-2030 · «Valores nulos fuera de umbral · Campo `precio_unitario` · 2.1% nulos».** Dos errores en un renglón: la columna se llama `precio`, y **el precio llegó íntegro — cero nulos, cero en cero, cero negativos** (ADR 001). Ese incidente no puede existir con estos datos.

&nbsp;

**«24,918 reglas».** El contrato tiene 15 columnas con un puñado de reglas cada una. Probablemente quiso decir validaciones ejecutadas.

&nbsp;

> En cambio **INC-2031 · «Deriva de esquema · 18 columnas detectadas vs 15 esperadas» está exacto**: son las 15 del contrato más `folio`, `cv_producto` y `cv_marca`. Ése se queda tal cual.

&nbsp;

Y una sugerencia de fondo: la consola se ve con todo en verde y «al día». **Para la demostración conviene mostrarla con el incidente encendido**, porque la tesis del proyecto no es que el flujo funcione, es que el sistema se da cuenta cuando no funciona. Una pantalla perfecta no demuestra nada.

### 4 · Métodos de pago y direcciones no deberían existir

En **Mi cuenta** hay *«Métodos de pago · Tarjetas y efectivo»* y *«Direcciones · Casa · Trabajo»*. CanastaMX no vende nada: no hay transacción en ningún caso de uso. Tenerlos implica que la app procesa pagos, mete alcance que nadie pidió y —en un repositorio que se hace público al final— crea un riesgo de datos personales que no hay por qué correr. **Quitar los dos.**

### 5 · Los nombres abreviados de la cola no existen en la fuente

`FRIJOL NGR MZTN 1KG`, `TRT MAIZ BL 1KG`, `AZ EST ZULKA 1KG`. QQP no escribe así: escribe `Frijol Bayo`, `Tortilla de Maíz`, completos.

&nbsp;

La variación real es **mucho más sutil**, y por eso importa:

&nbsp;

| Caso real | Qué lo separa |
| :---- | :---- |
| `Mazatán` / `Mazatún` | una letra en medio |
| `1 L` / `1 Lt` | abreviatura de unidad |
| `Whirlpool` / `Whirpool` | una letra faltante |
| `S/m` / `S/M` | mayúscula |
| `Camar?n` | el carácter que la codificación se comió |

&nbsp;

**Y eso cambia el diseño de la pantalla**: si las diferencias son de una letra, el revisor no puede decidir mirando sólo los literales — necesita ver **las dos claves ya normalizadas**, una debajo de otra. Es exactamente lo que se aprendió calificando la muestra de H3 a mano.

### 6 · «CATEGORÍA: Básicos» confunde dos columnas distintas

`Básicos` es un **catálogo**, no una categoría, y no es un detalle de palabras. El ADR 005 destapó que `catalogo` y `categoria` son clasificaciones **independientes y no anidadas**: excluir el catálogo `Medicamentos` no excluyó las 8,212 filas de `categoria = medicamentos` que viven dentro de `Basicos`.

&nbsp;

Si el filtro los mezcla, va a devolver resultados que el usuario no espera. Etiquetarlo **CATÁLOGO**, y si más adelante quieren filtrar por categoría, que sea un segundo filtro.

### 7 · Hay cifras inventadas donde las reales ya existen

| Dónde | Dice | Lo medido |
| :---- | :---- | :---- |
| Descubrir · artículos por catálogo | suman **570** | **1,597** |
| Media de Mercados | $33.20 | mediana medida **$50.00** |
| Media de Básicos | $46.40 | mediana medida $44.90 · ésa sí anda cerca |
| Cola · «EN COLA» | **3** en la tarjeta, **128** en la insignia | elegir una |

&nbsp;

Ya existen las cifras reales y están en `medir-para-contrato.py` y en el ADR 005\. Poner las verdaderas no cuesta más que poner las inventadas, y una maqueta con números reales es la mitad del trabajo de la presentación.

&nbsp;

> La cobertura de normalización aparece en **81.4%**, por debajo de la meta de 85% de H3. Para una maqueta está bien e incluso es honesto — sólo conviene saber que se está enseñando la hipótesis sin cumplirse.

&nbsp;

---

## Donde el inventario y los wireframes se contradicen

Son dos documentos de la misma persona con datos distintos. Conviene alinearlos antes de T029, porque el prototipo navegable sale de los dos.

&nbsp;

| Tema | Inventario | Wireframe |
| :---- | :---- | :---- |
| Volumen en cuarentena | 0.36% · 753,054 filas | 3.61% · 770,273 |
| Vocabulario | «producto», «Detalle de producto» | «artículo», «Explorar artículos» |
| Filtros de búsqueda | «categoría (ej. Lácteos)» | catálogos del ADR 005 |

&nbsp;

La cifra buena del perfilado es **770,273 (3.61%)**; el 0.36% parece un punto decimal movido de lugar. El vocabulario tiene que ser **artículo** en los dos —el ADR 002 lo fijó y la app móvil ya lo usa bien—. Y el inventario menciona «un SKU específico»: **en QQP no hay SKU**; la identidad es `producto` \+ `presentacion`.

&nbsp;

---

## Las dos dudas que dejó, contestadas

**1 · Las fotos de los productos.** La respuesta es incómoda: **QQP no trae ni una sola fotografía.** No hay columna de imagen en las 15 del contrato. O sea que todas las fotos de los wireframes son de banco de imágenes, y eso hay que decidirlo a propósito, no por omisión:

&nbsp;

- Ícono genérico por catálogo es gratis y no miente.  
- Un banco externo obliga a revisar su licencia **y** a que alguien mantenga el mapeo de 1,597 artículos a imágenes. Eso es una tarea que hoy no está en el cronograma y que nadie tiene asignada.  
- Si se usan fotos, que quede claro que son ilustrativas: una foto de huevo Bachoco junto a un precio que no es de Bachoco confunde.

&nbsp;

**2 · Cuándo pedir el registro.** Esta se contesta sola con el modelo de dominio de C1: *«una canasta pertenece a exactamente un usuario»*. Entonces el registro se pide **al guardar la canasta**, no al agregar un artículo. Agregar puede vivir en memoria del teléfono; guardar necesita dueño.

&nbsp;

---

## El sistema de diseño

Hay una identidad visual consistente —el turquesa, la tipografía, el radio de las tarjetas, el fondo crema— pero no está documentada en ningún lado.

&nbsp;

**Eso bloquea a C2.** T028 pide *«prototipo móvil navegable con el sistema de diseño de D aplicado»*, y Oscar no puede aplicar capturas de pantalla. Necesita valores: los hexadecimales del turquesa y del verde, la familia tipográfica con sus tamaños, el radio de las tarjetas y la escala de espaciado. Media hora de trabajo que desbloquea a otra persona.

&nbsp;

---

## Resumen para el issue

**Se acepta**, con correcciones. Lo esencial está y lo que bloqueaba se resolvió.

&nbsp;

Antes de T029:

&nbsp;

- [ ] Cambiar la frase del acceso web: ni tiempo real, ni 80,000 artículos, ni toda la República  
- [ ] Quitar la marca del nombre canónico en la web, como ya está en el móvil  
- [ ] Corregir cuarentena, `precio_unitario` y «24,918 reglas» en la consola  
- [ ] Quitar métodos de pago y direcciones de Mi cuenta  
- [ ] Mostrar las dos claves normalizadas en la cola de reconciliación, y cambiar los ejemplos por casos reales  
- [ ] Renombrar el filtro «CATEGORÍA» a «CATÁLOGO»  
- [ ] Sustituir las cifras inventadas por las medidas  
- [ ] Alinear inventario y wireframes: cuarentena, «artículo» en vez de «producto», nada de SKU  
- [ ] Documentar el sistema de diseño con valores, para desbloquear T028

&nbsp;