import { Problema } from "./analitica";

export class ErrorServicio extends Error {
  constructor(message: string, public readonly status?: number, public readonly problema?: Problema) { super(message); }
}

// Compartida por las rutas nuevas: plazo, cancelación y errores RFC 9457.
export async function solicitar(base: string | undefined, ruta: string, opciones: RequestInit = {}, signal?: AbortSignal) {
  base = base?.trim().replace(/\/+$/, "");
  if (!base || !/^https?:\/\//i.test(base)) throw new ErrorServicio("Falta configurar la dirección del servicio. Reinicia Expo después de configurarla.");
  const controller = new AbortController();
  const cancelar = () => controller.abort();
  signal?.addEventListener("abort", cancelar);
  if (signal?.aborted) controller.abort();
  let vencio = false;
  const timer = setTimeout(() => { vencio = true; controller.abort(); }, 8000);
  try {
    const respuesta = await fetch(`${base}${ruta}`, { ...opciones, signal: controller.signal,
      headers: { Accept: "application/json, application/problem+json", ...opciones.headers } });
    if (!respuesta.ok) {
      let problema: Problema | undefined;
      if (respuesta.headers.get("content-type")?.includes("application/problem+json")) {
        try {
          const p = await respuesta.json();
          if (p && typeof p.type === "string" && typeof p.title === "string" && p.status === respuesta.status
            && (p.detail === undefined || typeof p.detail === "string")) problema = p;
        } catch { /* Conserva el código HTTP aunque el cuerpo de error sea ilegible. */ }
      }
      throw new ErrorServicio(respuesta.status === 401 ? "Tu sesión venció. Vuelve a iniciar sesión."
        : problema?.detail ?? problema?.title ?? `El servicio respondió HTTP ${respuesta.status}. Vuelve a intentar.`, respuesta.status, problema);
    }
    return { datos: respuesta.status === 204 ? undefined : await respuesta.json() as unknown,
      simulador: respuesta.headers.get("x-canastamx-fuente") === "simulador" || new URL(base).port === "4011" };
  } catch (error) {
    if (signal?.aborted) throw error;
    if (vencio) throw new ErrorServicio("El servicio no respondió en 8 segundos. Vuelve a intentar.");
    if (error instanceof TypeError) throw new ErrorServicio("No hay conexión con el servicio. Revisa la red y vuelve a intentar.");
    if (error instanceof SyntaxError) throw new ErrorServicio("El servicio devolvió una respuesta que no podemos leer.");
    throw error;
  } finally { clearTimeout(timer); signal?.removeEventListener("abort", cancelar); }
}

export const objeto = (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null;
export const texto = (v: unknown): v is string => typeof v === "string" && v.trim().length > 0;
export const entero = (v: unknown, minimo = 1): v is number => Number.isSafeInteger(v) && Number(v) >= minimo;
