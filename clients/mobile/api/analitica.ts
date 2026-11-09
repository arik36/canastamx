// Contrato analitica.yaml 0.2.1. Las rutas de consumo no requieren sesión.
export type Dinero = { monto: string; moneda: "MXN" };
export type ArticuloEncontrado = {
  articulo: { producto: string; presentacion: string };
  nombre: string;
  catalogo: string;
  precioTipico: Dinero;
  observaciones: number;
};
export type BusquedaConDatos = {
  cobertura: true; entidad: string; quincena: string; total: number;
  resultados: ArticuloEncontrado[];
};
export type BusquedaSinCobertura = {
  cobertura: false; entidad: string; entidadesCubiertas: string[];
};
export type ResultadoDeBusqueda = BusquedaConDatos | BusquedaSinCobertura;
export type CriteriosBusqueda = { q: string; entidad: string; offset?: number };
export type Problema = { type: string; title: string; status: number; detail?: string; instance?: string };

export class ErrorAnalitica extends Error {
  constructor(message: string, public readonly problema?: Problema) { super(message); }
}

const catalogos = ["BASICOS", "PACIC", "FRUTAS Y LEGUMBRES", "MERCADOS", "PESCADOS Y MARISCOS"];
const objeto = (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null;
const texto = (v: unknown): v is string => typeof v === "string" && v.trim().length > 0;
const entero = (v: unknown, minimo: number): v is number => Number.isSafeInteger(v) && Number(v) >= minimo;
const quincena = (v: unknown): v is string => typeof v === "string" && /^\d{4}-(0[1-9]|1[0-2])-Q[12]$/.test(v);

function esArticulo(v: unknown): v is ArticuloEncontrado {
  return objeto(v) && objeto(v.articulo) && texto(v.articulo.producto) && texto(v.articulo.presentacion)
    && texto(v.nombre) && catalogos.includes(String(v.catalogo)) && entero(v.observaciones, 1)
    && objeto(v.precioTipico) && v.precioTipico.moneda === "MXN"
    && typeof v.precioTipico.monto === "string" && /^\d+\.\d{2}$/.test(v.precioTipico.monto);
}

export function validarBusqueda(v: unknown): ResultadoDeBusqueda {
  if (!objeto(v) || !texto(v.entidad)) throw new ErrorAnalitica("La analítica devolvió una búsqueda incompleta.");
  // Se comprueba cobertura antes de resultados: su ausencia no significa «sin coincidencias».
  if (v.cobertura === false && Array.isArray(v.entidadesCubiertas)
    && v.entidadesCubiertas.length > 0 && v.entidadesCubiertas.every(texto)) return v as BusquedaSinCobertura;
  if (v.cobertura === true && quincena(v.quincena) && entero(v.total, 0)
    && Array.isArray(v.resultados) && v.resultados.every(esArticulo) && v.total >= v.resultados.length) {
    return v as BusquedaConDatos;
  }
  throw new ErrorAnalitica("La respuesta no incluye los resultados, la quincena o la población que necesitamos mostrar.");
}

export function esUrlDeSimulador(): boolean {
  try {
    // 4011 es el puerto reservado al simulador por T051; también cubre el estado sin conexión.
    return new URL(process.env.EXPO_PUBLIC_ANALITICA_URL ?? "").port === "4011";
  } catch { return false; }
}

export async function buscarArticulos(criterios: CriteriosBusqueda, signal?: AbortSignal): Promise<{
  datos: ResultadoDeBusqueda; simulador: boolean;
}> {
  if (criterios.q.trim().length < 2 || !criterios.entidad.trim()) {
    throw new ErrorAnalitica("Escribe al menos dos caracteres y selecciona una entidad.");
  }
  const base = process.env.EXPO_PUBLIC_ANALITICA_URL?.trim().replace(/\/+$/, "");
  if (!base || !/^https?:\/\//i.test(base)) throw new ErrorAnalitica("Falta configurar la dirección de la analítica.");
  const controller = new AbortController();
  const cancelar = () => controller.abort();
  signal?.addEventListener("abort", cancelar);
  if (signal?.aborted) controller.abort();
  let agotado = false;
  const timer = setTimeout(() => { agotado = true; controller.abort(); }, 8000);
  const offset = criterios.offset ?? 0;
  if (!entero(offset, 0)) { clearTimeout(timer); signal?.removeEventListener("abort", cancelar); throw new ErrorAnalitica("La página solicitada no es válida."); }
  const query = `q=${encodeURIComponent(criterios.q.trim())}&entidad=${encodeURIComponent(criterios.entidad.trim())}&limit=20&offset=${offset}`;
  try {
    const respuesta = await fetch(`${base}/api/v1/articulos?${query}`, {
      signal: controller.signal,
      headers: { Accept: "application/json, application/problem+json" },
    });
    if (!respuesta.ok) {
      if (respuesta.headers.get("content-type")?.toLowerCase().includes("application/problem+json")) {
        const p: unknown = await respuesta.json();
        if (objeto(p) && typeof p.type === "string" && texto(p.title) && entero(p.status, 100)
          && p.status === respuesta.status && (p.detail === undefined || typeof p.detail === "string")) {
          throw new ErrorAnalitica(p.title, p as Problema);
        }
      }
      throw new ErrorAnalitica(`La analítica respondió HTTP ${respuesta.status}. Intenta de nuevo.`);
    }
    return {
      datos: validarBusqueda(await respuesta.json()),
      simulador: respuesta.headers.get("x-canastamx-fuente") === "simulador" || esUrlDeSimulador(),
    };
  } catch (error) {
    if (signal?.aborted) throw error;
    if (agotado) throw new ErrorAnalitica("La analítica no respondió en 8 segundos. Vuelve a intentar.");
    if (error instanceof TypeError) throw new ErrorAnalitica("No hay conexión con la analítica. Revisa la red y que el servicio esté encendido.");
    if (error instanceof SyntaxError) throw new ErrorAnalitica("La analítica devolvió una respuesta que no podemos leer.");
    throw error;
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", cancelar);
  }
}
