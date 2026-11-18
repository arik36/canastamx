import { Dinero } from "./analitica";
import { Articulo, claveArticulo, esArticulo, esLinea, Linea } from "./canastas";
import { entero, ErrorServicio, objeto, solicitar, texto } from "./solicitud";

export type Establecimiento = { nombre: string; cadena: string; marca: string; precio: Dinero; fechaRegistro: string; direccion?: string; municipio?: string };
export type Comparacion = { articulo: Articulo; entidad: string; quincena: string; establecimientos: Establecimiento[] };
export type Costo = { entidad: string; quincena: string; cadenas: { cadena: string; total: Dinero; faltan: number; lineas: (Linea & { precio: Dinero | null })[] }[] };
const esDinero = (v: unknown): v is Dinero => objeto(v) && v.moneda === "MXN" && typeof v.monto === "string" && /^\d+\.\d{2}$/.test(v.monto);
const esQuincena = (v: unknown) => typeof v === "string" && /^\d{4}-(0[1-9]|1[0-2])-Q[12]$/.test(v);
const esFecha = (v: unknown) => typeof v === "string" && /^\d{4}-\d{2}-\d{2}$/.test(v)
  && Number.isFinite(Date.parse(v)) && new Date(v).toISOString().slice(0, 10) === v;
export function validarComparacion(v: unknown): Comparacion {
  if (!objeto(v) || !esArticulo(v.articulo) || !texto(v.entidad) || !esQuincena(v.quincena)
    || !Array.isArray(v.establecimientos) || !v.establecimientos.every(e => objeto(e) && texto(e.nombre)
      && typeof e.cadena === "string" && typeof e.marca === "string" && esDinero(e.precio) && esFecha(e.fechaRegistro)
      && (e.direccion === undefined || e.direccion === null || typeof e.direccion === "string")
      && (e.municipio === undefined || e.municipio === null || typeof e.municipio === "string"))) {
    throw new ErrorServicio("La comparación no incluye precios, fechas o población válidos.");
  }
  return v as Comparacion;
}
export function validarCosto(v: unknown): Costo {
  if (!objeto(v) || !texto(v.entidad) || !esQuincena(v.quincena) || !Array.isArray(v.cadenas)
    || !v.cadenas.every(c => objeto(c) && texto(c.cadena) && esDinero(c.total) && entero(c.faltan, 0)
      && Array.isArray(c.lineas) && c.lineas.every(l => esLinea(l) && "precio" in l && (l.precio === null || esDinero(l.precio)))
      && c.faltan === c.lineas.filter(l => l.precio === null).length)) {
    throw new ErrorServicio("El costo no incluye importes, faltantes o población válidos.");
  }
  return v as Costo;
}
export async function compararPrecios(articulo: Articulo, entidad: string, signal?: AbortSignal) {
  if (!esArticulo(articulo) || !entidad.trim()) throw new ErrorServicio("Selecciona un artículo y una entidad.");
  const query = `producto=${encodeURIComponent(articulo.producto)}&presentacion=${encodeURIComponent(articulo.presentacion)}&entidad=${encodeURIComponent(entidad.trim())}`;
  const r = await solicitar(process.env.EXPO_PUBLIC_ANALITICA_URL, `/api/v1/precios?${query}`, {}, signal);
  const datos = validarComparacion(r.datos);
  if (claveArticulo(datos.articulo) !== claveArticulo(articulo)) throw new ErrorServicio("La comparación corresponde a otro artículo.");
  return { datos, simulador: r.simulador };
}
export async function costearCanasta(lineas: Linea[], entidad: string, signal?: AbortSignal) {
  if (!entidad.trim() || lineas.length > 200 || !lineas.every(esLinea)) throw new ErrorServicio("Selecciona una entidad y hasta 200 artículos con cantidades enteras positivas.");
  const r = await solicitar(process.env.EXPO_PUBLIC_ANALITICA_URL, "/api/v1/canastas/costo", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ entidad: entidad.trim(), lineas }),
  }, signal);
  const datos = validarCosto(r.datos);
  if (datos.cadenas.some(c => c.lineas.length !== lineas.length || new Set(c.lineas.map(l => claveArticulo(l.articulo))).size !== lineas.length
    || c.lineas.some(l => !lineas.some(p => claveArticulo(p.articulo) === claveArticulo(l.articulo) && p.cantidad === l.cantidad)))) {
    throw new ErrorServicio("El costo corresponde a otra lista de artículos o cantidades.");
  }
  return { datos, simulador: r.simulador };
}
