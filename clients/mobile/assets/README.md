# Recursos visuales

## Diferenciación por producto y presentación

Se añade [atún ahumado: imagen y prompt](productos/ATUN-AHUMADO.md), generado con
la herramienta integrada. Tiene prioridad sobre «lomo»/«fresco» para evitar
mostrar pescado crudo en una presentación ahumada. Mojarra entera y filetes de
Blanco del Nilo utilizan las ilustraciones de pescado entero y filete existentes.

`productos/alimentos-v1.png`, `productos/frescos-v1.png` y
`productos/despensa-v1.png`, junto con `productos/complementos-v1.png`, reúnen
64 ilustraciones generadas con la herramienta integrada, en cuatro láminas
de 4 × 4. [Prompts iniciales](productos/PROMPTS.md) y
[complementos: imagen y prompt](productos/COMPLEMENTOS.md).
Se muestran sus celdas con un recorte de la vista nativa, sin modificar los PNG.
Se inspeccionaron visualmente las cuatro láminas y el orden de sus 16 celdas.

`components/clasificarImagen.ts` elige según producto y presentación. Distingue,
por ejemplo, pollo rostizado, entero, piezas, consomé y sopa; leche líquida,
evaporada, condensada y en polvo. Las marcas que comparten tipo pueden compartir
ilustración; no se afirma que la imagen sea de su envase exacto. Se conservan las
fotos existentes para pechuga, huevo, aceite y chile fresco.

No se dispone de fotos exactas de todo el catálogo público. Un producto o
variante sin correspondencia segura muestra un recurso neutro con su nombre y
«Sin fotografía asignada», en lugar de una foto incompatible. Un ingrediente
aislado no determina la imagen: una gelatina sabor leche no recibe leche líquida.

## Recursos anteriores y portada

Adaptación nativa de las capturas de Karen, sin modificar sus originales.

- `icon.svg` y `icon.png`: símbolo de canasta del cliente.
- `hero-v2.png`: portada generada a partir de la composición de la referencia,
  con la herramienta integrada de imágenes. [Prompt y origen](hero-v2.md).
- Fotografías ilustrativas de Unsplash, de las mismas direcciones que usa el
  prototipo. Se asignan por tipo de artículo; no acreditan la marca ni el
  producto registrado. Se incluyen localmente para no consultar terceros al
  abrir la app:
  - [mercado.jpg](https://images.unsplash.com/photo-1584208632856-d2af6180f492)
  - [basicos.jpg](https://images.unsplash.com/photo-1555465083-a845797ef750)
  - [pescados.jpg](https://images.unsplash.com/photo-1633442496335-af4d20202da3)
  - [pollo.jpg](https://images.unsplash.com/photo-1604503468506-a8da13d82791)
  - [huevo.jpg](https://images.unsplash.com/photo-1585584563699-0ae01ba660dd)
  - [atun.jpg](https://images.unsplash.com/photo-1590769383363-5681e57ff10f)
  - [aceite.jpg](https://images.unsplash.com/photo-1593759608363-fde2fa65f5d7)
  - [chile.jpg](https://images.unsplash.com/photo-1598536040030-c2a13cf6efd8)

Inicio aclara que las imágenes son ilustrativas; las etiquetas de accesibilidad
lo conservan en cada imagen. Cuando no hay una foto asignada se usa el símbolo
de canasta sobre fondo crema, sin reutilizar una fotografía ajena al tipo.
