# CU-12 · Buscar un artículo y comparar su precio entre establecimientos

- **Actor primario:** La persona consumidora.
- **Interesados:**
  - **Persona consumidora** — quiere comparar precios del mismo artículo en
    establecimientos de la entidad consultada, conocer la fecha de los datos
    y entender cuándo no existe información suficiente para comparar.
  - **Responsable de datos (A)** — necesita que la consulta respete el catálogo,
    la cobertura y los registros habilitados para consumo.
  - **Responsables de los clientes móvil y web (C2 y D)** — necesitan comunicar
    de forma consistente la identidad del artículo y las limitaciones de cobertura.
- **Precondiciones:**
  1. El sistema dispone de una versión del catálogo y de registros de precios
     habilitados para consulta conforme al contrato de datos vigente.
  2. La consulta de artículos está disponible para la persona consumidora,
     incluso en modo invitado; no se exige iniciar sesión para buscar y comparar.
  3. La cobertura declarada del sistema está disponible para su consulta.
     No se presupone que la entidad solicitada esté cubierta ni que existan
     coincidencias para la búsqueda.
- **Disparador:** La persona consumidora envía una solicitud de búsqueda de
  artículos e indica la entidad federativa que desea consultar.

## Flujo principal

1. La persona consumidora proporciona el término de búsqueda y la entidad
   federativa de interés.
2. El sistema comprueba la cobertura de la entidad y presenta los artículos
   coincidentes del catálogo incluido en el alcance, acotados a esa entidad.
   Cada artículo se distingue por su denominación y presentación.
3. La persona consumidora elige un artículo y solicita comparar sus precios
   entre establecimientos de la entidad consultada.
4. El sistema presenta los precios disponibles del mismo artículo en al menos
   dos establecimientos distintos, ordenados de menor a mayor conforme al
   criterio por omisión. Cada registro identifica el establecimiento y su
   sucursal o dirección disponible, la marca o categoría genérica, el precio
   en pesos mexicanos y la fecha del registro. La persona dispone de la
   información para comparar sin confundir presentaciones diferentes.

## Flujos alternos

**2a · La búsqueda no devuelve coincidencias**
1. La entidad está cubierta, pero no hay artículos que coincidan con los
   criterios solicitados dentro del catálogo disponible.
2. El sistema informa que no se encontraron resultados para esa búsqueda,
   conservando el término y la entidad consultada para que puedan corregirse.
3. La persona consumidora puede reformular los criterios y volver al paso 1,
   o terminar la consulta sin resultados. No se presentan precios inventados
   ni resultados anteriores como si correspondieran a la nueva búsqueda.

**2b · La entidad de la persona consumidora no está cubierta**
1. Al comprobar la entidad solicitada, el sistema identifica que está fuera
   de la cobertura declarada. Esta comprobación precede a la búsqueda de
   coincidencias, para no confundir falta de cobertura con falta de resultados.
2. El sistema informa que no ofrece datos para esa entidad y declara las siete
   entidades del alcance: **Aguascalientes, Guanajuato, Jalisco, Michoacán,
   Querétaro, San Luis Potosí y Zacatecas**. Colima y Nayarit quedan fuera,
   conforme al ADR 001.
3. El sistema presenta esta situación como una limitación de cobertura,
   no como un error ni un incidente del sistema. No cambia la entidad
   consultada automáticamente.
4. La persona consumidora puede elegir otra entidad de la cobertura disponible
   y volver al paso 1, o terminar sin resultados para su entidad original.

**4a · El artículo tiene dato en un solo establecimiento**
1. El sistema encuentra registros del artículo en un único establecimiento
   dentro de la entidad y los criterios consultados. Varias marcas o fechas
   de ese mismo establecimiento no cuentan como establecimientos distintos.
2. El sistema muestra la información disponible, incluida su fecha, e informa:
   «Solo hay datos de un establecimiento; no es posible comparar entre
   establecimientos».
3. El sistema no calcula diferencias entre establecimientos ni declara cuál
   es el más barato a partir de ese único establecimiento.
4. La persona consumidora puede volver al paso 1 para realizar otra búsqueda,
   o finalizar con la consulta del dato disponible, sin comparación.
   Esta insuficiencia de datos no se trata como un fallo técnico.

## Postcondiciones

- **De éxito:** La persona consumidora dispone de precios identificados y
  fechados del mismo artículo en al menos dos establecimientos de la entidad
  consultada y puede compararlos. No se modificaron el catálogo, los registros
  de precios, las canastas ni las alertas.
- **De fallo:** Cuando no se logra el objetivo de comparar, el sistema explica
  la causa: sin coincidencias, entidad fuera de cobertura o un único
  establecimiento con datos. En este último caso solo se muestra el dato
  disponible, sin afirmar que existe una comparación. La consulta no modifica
  información persistente ni presenta resultados ajenos a los criterios.
  No lograr el objetivo no convierte los tres alternos en incidentes del sistema.

## Requisito no funcional asociado

- **RNF-CU12-01 · Tiempo de respuesta de búsqueda:** Se propone un máximo de
  **2 segundos** desde que la persona envía la búsqueda hasta que recibe
  los resultados o el aviso de ausencia de resultados/cobertura. Para verificarlo
  se realizarán **30 búsquedas consecutivas con una persona activa**, sobre
  el catálogo del alcance en el entorno de pruebas, registrando la duración
  de cada solicitud; cada una deberá cumplir el límite. Es un objetivo de
  aceptación propuesto para revisión, **no una medición ya realizada**.
  Las condiciones del dispositivo, red y versión de datos se registrarán
  junto con los resultados de la prueba.

## Notas

- **Identidad y orden (ADR 002):** Un artículo se identifica por
  `producto` + `presentacion`; la marca pertenece al registro de precio
  y no forma parte de esa identidad. `S/m` representa la categoría genérica.
  Los registros genéricos quedan al final en el orden por omisión; los demás
  se ordenan por precio ascendente. La persona puede ordenar y filtrar por
  marca y por precio, ascendente o descendente, sin alterar la identidad
  del artículo. Cambiar los criterios da lugar a una nueva consulta.
- **Catálogo (ADR 005):** La búsqueda se limita a Básicos, PACIC,
  Frutas y Legumbres, Mercados y Pescados y Mariscos.
- **Cobertura (ADR 001):** Las siete entidades son el alcance declarado.
  El despliegue comienza con Guanajuato y se amplía por etapas; debe
  distinguirse una entidad del alcance aún no habilitada de una entidad
  fuera de cobertura. Nunca se promete disponibilidad de las siete por el
  solo hecho de enumerar el alcance.
- **Procedencia y vigencia:** Los precios son registros observados de QQP,
  no una garantía de precio actual en caja ni de existencia del artículo.
  La consulta utiliza los datos habilitados por la política de frescura del
  contrato vigente, y conserva la fecha del registro para su interpretación.
- **Límites:** Este caso describe buscar y comparar. Guardar una canasta y
  configurar o enviar alertas corresponden a CU-09, CU-10 y CU-11.
- **Referencia visual:** Se revisó CanastaMX 3.0, versión 18 de Figma Make,
  el 25 de septiembre de 2026. Se observaron búsqueda, filtros, orden por
  marca/precio y un detalle con sucursal y fecha. En el recorrido probado,
  la búsqueda sin coincidencias dejó la lista vacía sin explicación, el
  selector de entidad no desplegó opciones y el detalle mostró una sucursal.
  Esas observaciones no acreditan los alternos como implementados: este
  documento especifica el comportamiento requerido.
- **Fuentes:**
  - [Plantilla de T095](PLANTILLA.md).
  - [Ficha T034 de la semana 3](../../equipo/fichas/planeacion-semana-03.md#t034--c2--caso-de-uso-cu-12).
  - [Inventario de vistas](../inventario-vistas.md).
  - [ADR 001 · Fuente y cobertura](../../adr/001-fuente-de-datos.md).
  - [ADR 002 · Identidad del artículo](../../adr/002-identidad-del-articulo.md).
  - [ADR 005 · Recorte de catálogos](../../adr/005-recorte-de-catalogos.md).
  - [Contrato QQP vigente](../../../contracts/qqp-v1.yaml).
  - [CanastaMX 3.0 · Figma Make](https://www.figma.com/make/yUK7s2m2NoGCHGk6vAkSTZ/CanastaMX-3.0).