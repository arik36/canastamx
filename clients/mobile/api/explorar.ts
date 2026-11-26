import { ArticuloEncontrado, buscarArticulos, ErrorAnalitica, ResultadoDeBusqueda } from "./analitica";

// Selección editorial de términos, nunca de precios o resultados ficticios.
// El contrato exige q de dos caracteres; no existe una ruta de catálogo vacío.
export async function explorarArticulos(entidad: string, catalogo?: string, signal?: AbortSignal): Promise<{ datos: ResultadoDeBusqueda; simulador: boolean }> {
  const terminos = catalogo === "FRUTAS Y LEGUMBRES" ? ["jitomate", "chile", "limón", "cebolla"]
    : catalogo === "MERCADOS" ? ["papa", "jitomate", "pollo", "huevo"]
    : catalogo === "PESCADOS Y MARISCOS" ? ["atún", "sardina", "tilapia"]
    : ["pollo", "huevo", "atún", "arroz", "aceite", "leche"];
  const respuestas = await Promise.all(terminos.map(q => buscarArticulos({ q, entidad, catalogo }, signal)));
  const sinCobertura = respuestas.find(r => !r.datos.cobertura);
  if (sinCobertura) return sinCobertura;
  const resultados = new Map<string, ArticuloEncontrado>();
  let quincena = "";
  for (const { datos } of respuestas) {
    if (!datos.cobertura) continue;
    if (quincena && quincena !== datos.quincena) throw new ErrorAnalitica("Los precios se están actualizando. Vuelve a cargar los artículos.");
    quincena = datos.quincena;
    for (const articulo of datos.resultados) resultados.set(JSON.stringify([articulo.articulo.producto, articulo.articulo.presentacion]), articulo);
  }
  return { datos: { cobertura: true, entidad, quincena, total: resultados.size, resultados: [...resultados.values()] },
    simulador: respuestas.some(r => r.simulador) };
}
