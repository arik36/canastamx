export type ImagenProducto = { atlas: "alimentos" | "frescos" | "despensa" | "complementos"; celda: number } | { foto: "pechuga" | "huevo" | "aceite" | "chile" | "atunAhumado" };
const normalizar = (s: string) => s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/\s+/g, " ").trim();
const a = (celda: number): ImagenProducto => ({ atlas: "alimentos", celda });
const f = (celda: number): ImagenProducto => ({ atlas: "frescos", celda });
const d = (celda: number): ImagenProducto => ({ atlas: "despensa", celda });
const c = (celda: number): ImagenProducto => ({ atlas: "complementos", celda });

// La presentación distingue variantes del mismo producto canónico. Nunca se
// deduce el producto de un ingrediente aislado (p. ej. gelatina sabor leche).
export function clasificarImagen(producto: string, presentacion = ""): ImagenProducto | undefined {
  const p = normalizar(producto), t = `${p} ${normalizar(presentacion)}`;
  if (/^(shampoo|champu)\b/.test(p)) return c(2);
  if (/^(acondicionador|enjuague capilar|enjuague para cabello)\b/.test(p)) return c(3);
  if (/^cajeta\b/.test(p)) return c(4);
  if (/^gelatina\b/.test(p)) return /polvo/.test(t) ? c(5) : undefined;
  if (/^(concentrado|consome|caldo)\b/.test(p)) return /pollo/.test(t) && /cubo|concentrado|consome/.test(t) ? a(3) : undefined;
  if (/^(alimentos preparados|sopa)\b/.test(p)) return /sopa|fideo|instantanea/.test(t) ? a(4) : undefined;
  if (/^(salchicha|embutido)/.test(p)) return d(6);
  if (/^jamon\b/.test(p)) return d(5);
  if (/^(pollo|carne (de )?pollo|pechuga|pierna (de )?pollo|muslo (de )?pollo)\b/.test(p)) {
    if (/rostizado|asado|cocido/.test(t)) return /rostizado|asado/.test(t) ? a(0) : undefined;
    if (/pechuga/.test(t)) return { foto: "pechuga" };
    if (/pierna|muslo/.test(t)) return a(2);
    return /entero/.test(t) ? a(1) : undefined;
  }
  if (/^leche\b|^alimento lacteo\b/.test(p)) {
    if (/polvo/.test(t)) return a(8);
    if (/condensad/.test(t)) return a(7);
    if (/evaporad/.test(t)) return a(6);
    if (/chocolate|fresa|sabor/.test(t)) return undefined;
    return a(5);
  }
  if (/^yogh?urt\b|^yogur\b/.test(p)) return d(2);
  if (/^queso\b/.test(p)) return /amarillo|cheddar/.test(t) ? c(8) : /panela|fresco/.test(t) ? d(1) : undefined;
  if (/^mantequilla\b/.test(p)) return d(3);
  if (/^crema\b/.test(p)) return /corporal|facial|afeitar|dental|cacahuate/.test(t) ? undefined : d(4);
  if (/^huevo\b/.test(p)) return { foto: "huevo" };
  if (/^aceite\b/.test(p)) return /motor|cuerpo|bebe/.test(t) ? undefined : { foto: "aceite" };
  if (/^atun\b/.test(p)) return /ahumad/.test(t) ? { foto: "atunAhumado" } : /fresco|crudo|congelado/.test(t) ? c(9) : /bolsa|sobre|pouch/.test(t) ? c(0) : /lata|conserva/.test(t) ? f(4) : /filete|medallon|bistec|lomo/.test(t) ? c(9) : undefined;
  if (/^sardina/.test(p)) return /lata|tomate/.test(t) ? f(3) : undefined;
  if (/^camaron/.test(p)) return f(2);
  if (/^mojarra\b/.test(p)) return /filete/.test(t) ? f(1) : f(0);
  if (/^(pescado|tilapia|blanco del nilo|filete de pescado|basa)\b/.test(p)) return /filete/.test(t) ? f(1) : /entero/.test(t) ? f(0) : undefined;
  if (/^carne (de )?res\b|^bistec/.test(p)) return /molida/.test(t) ? f(6) : /bistec|filete/.test(t) ? f(5) : undefined;
  if (/^carne (de )?(cerdo|puerco)\b|^chuleta/.test(p)) return /chuleta/.test(t) ? f(7) : undefined;
  if (/^arroz\b/.test(p)) return /integral/.test(t) ? c(1) : a(9);
  if (/^frijol/.test(p)) return /refrito/.test(t) ? c(7) : /cocido/.test(t) ? undefined : a(10);
  if (/^pasta\b|^espagueti|^spaghetti|^fideo/.test(p)) return /dental/.test(t) ? undefined : a(11);
  if (/^azucar\b/.test(p)) return /mascabado|morena/.test(t) ? c(6) : f(8);
  if (/^sal\b/.test(p)) return f(9);
  if (/^harina\b/.test(p)) return /integral/.test(t) ? (/trigo/.test(t) ? c(13) : undefined) : /maiz/.test(t) ? c(14) : /trigo|arroz/.test(t) ? f(10) : undefined;
  if (/^pan\b/.test(p)) return /caja|rebanad/.test(t) ? f(11) : undefined;
  if (/^tortilla/.test(p)) return /harina|trigo/.test(t) ? undefined : d(0);
  if (/^lenteja/.test(p)) return d(7);
  if (/^avena\b/.test(p)) return d(8);
  if (/^cereal\b|^hojuelas de maiz/.test(p)) return /maiz|corn/.test(t) ? d(9) : undefined;
  if (/^cafe\b/.test(p)) return d(10);
  if (/^chocolate\b/.test(p)) return /barra|tablilla/.test(t) ? d(11) : undefined;
  if (/^agua\b/.test(p)) return /natural|purificada|potable/.test(t) ? d(12) : undefined;
  if (/^detergente\b/.test(p)) return /polvo/.test(t) ? d(13) : undefined;
  if (/^jabon\b/.test(p)) return /tocador|bano|barra/.test(t) ? d(14) : undefined;
  if (/^papel higienico\b/.test(p)) return d(15);
  if (/^(jitomate|tomate rojo)\b/.test(p)) return a(12);
  if (/^papa\b/.test(p)) return /frita/.test(t) ? undefined : a(13);
  if (/^cebolla\b/.test(p)) return /morada/.test(t) ? c(11) : a(14);
  if (/^aguacate\b/.test(p)) return a(15);
  if (/^manzana\b/.test(p)) return /verde|granny/.test(t) ? c(10) : /golden|amarilla/.test(t) ? undefined : f(12);
  if (/^platano\b|^banana\b/.test(p)) return f(13);
  if (/^limon\b/.test(p)) return f(14);
  if (/^zanahoria\b/.test(p)) return f(15);
  if (/^lechuga\b/.test(p)) return c(15);
  if (/^chile\b/.test(p)) return /lata|vinagre/.test(t) ? undefined : /seco|ancho|guajillo|pasilla/.test(t) ? c(12) : { foto: "chile" };
  return undefined;
}
