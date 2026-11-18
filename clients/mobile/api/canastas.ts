import { entero, ErrorServicio, objeto, solicitar, texto } from "./solicitud";

export type Articulo = { producto: string; presentacion: string };
export type Linea = { articulo: Articulo; cantidad: number };
export type Canasta = { id: string; nombre: string; lineas: Linea[] };
export const esArticulo = (v: unknown): v is Articulo => objeto(v) && texto(v.producto) && texto(v.presentacion);
export const esLinea = (v: unknown): v is Linea => objeto(v) && esArticulo(v.articulo) && entero(v.cantidad);
export const claveArticulo = (a: Articulo) => JSON.stringify([a.producto, a.presentacion]);
export function validarCanasta(v: unknown): Canasta {
  if (!objeto(v) || !texto(v.id) || !texto(v.nombre) || !Array.isArray(v.lineas) || !v.lineas.every(esLinea)
    || new Set(v.lineas.map(l => claveArticulo(l.articulo))).size !== v.lineas.length) {
    throw new ErrorServicio("La respuesta de canasta no cumple el contrato del dominio.");
  }
  return v as Canasta;
}
const ruta = (id: string) => `/api/v1/canastas/${encodeURIComponent(id)}`;
async function dominio(token: string, path: string, method = "GET", body?: unknown, signal?: AbortSignal) {
  if (!token.trim()) throw new ErrorServicio("Inicia sesión para guardar tu canasta.", 401);
  return (await solicitar(process.env.EXPO_PUBLIC_API_URL, path, { method,
    headers: { Authorization: `Bearer ${token}`, ...(body === undefined ? {} : { "Content-Type": "application/json" }) },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }) }, signal)).datos;
}
export async function listarCanastas(token: string, signal?: AbortSignal): Promise<Canasta[]> {
  const canastas: Canasta[] = [];
  let total = 0;
  do {
    const v = await dominio(token, `/api/v1/canastas?limit=100&offset=${canastas.length}`, "GET", undefined, signal);
    if (!objeto(v) || !entero(v.total, 0) || !Array.isArray(v.canastas) || (v.canastas.length === 0 && canastas.length < v.total)) {
      throw new ErrorServicio("La lista de canastas no cumple el contrato del dominio.");
    }
    total = v.total;
    canastas.push(...v.canastas.map(validarCanasta));
  } while (canastas.length < total);
  return canastas;
}
export async function obtenerCanasta(token: string, id: string, signal?: AbortSignal) {
  return validarCanasta(await dominio(token, ruta(id), "GET", undefined, signal));
}
export async function crearCanasta(token: string, nombre: string, signal?: AbortSignal) {
  if (!nombre.trim()) throw new ErrorServicio("Escribe un nombre para la canasta.");
  return validarCanasta(await dominio(token, "/api/v1/canastas", "POST", { nombre: nombre.trim() }, signal));
}
export async function renombrarCanasta(token: string, id: string, nombre: string, signal?: AbortSignal) {
  if (!nombre.trim()) throw new ErrorServicio("Escribe un nombre para la canasta.");
  return validarCanasta(await dominio(token, ruta(id), "PATCH", { nombre: nombre.trim() }, signal));
}
export async function borrarCanasta(token: string, id: string, signal?: AbortSignal) {
  await dominio(token, ruta(id), "DELETE", undefined, signal);
}
export async function guardarLinea(token: string, id: string, linea: Linea, fijar = false, signal?: AbortSignal) {
  if (!esLinea(linea)) throw new ErrorServicio("La cantidad debe ser un entero mayor que cero.");
  return validarCanasta(await dominio(token, `${ruta(id)}/lineas`, fijar ? "PUT" : "POST", linea, signal));
}
export async function quitarArticulo(token: string, id: string, articulo: Articulo, signal?: AbortSignal) {
  const query = `producto=${encodeURIComponent(articulo.producto)}&presentacion=${encodeURIComponent(articulo.presentacion)}`;
  return validarCanasta(await dominio(token, `${ruta(id)}/lineas?${query}`, "DELETE", undefined, signal));
}
