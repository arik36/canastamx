// Contrato: docs/analisis/openapi/dominio.yaml, GET /health (Salud).
export type Salud = {
  status: "UP";
  service: string;
  time: string;
};

const TIEMPO_LIMITE_MS = 8000;

function esSalud(valor: unknown): valor is Salud {
  if (typeof valor !== "object" || valor === null) return false;
  const salud = valor as Record<string, unknown>;
  return (
    salud.status === "UP" &&
    typeof salud.service === "string" &&
    typeof salud.time === "string" &&
    Number.isFinite(Date.parse(salud.time))
  );
}

export async function consultarSalud(signal?: AbortSignal): Promise<Salud> {
  const baseUrl = process.env.EXPO_PUBLIC_API_URL?.trim().replace(/\/+$/, "");
  if (!baseUrl) {
    throw new Error("Falta configurar EXPO_PUBLIC_API_URL. Guarda la dirección del dominio y reinicia Expo.");
  }
  if (!/^https?:\/\//i.test(baseUrl)) {
    throw new Error("EXPO_PUBLIC_API_URL debe comenzar con http:// o https://.");
  }

  const controller = new AbortController();
  const cancelar = () => controller.abort();
  signal?.addEventListener("abort", cancelar);
  if (signal?.aborted) controller.abort();
  let tiempoAgotado = false;
  const timer = setTimeout(() => {
    tiempoAgotado = true;
    controller.abort();
  }, TIEMPO_LIMITE_MS);

  try {
    const response = await fetch(`${baseUrl}/health`, {
      headers: { Accept: "application/json" },
      signal: controller.signal,
    });
    if (!response.ok) {
      throw new Error(`El servicio respondió con un error HTTP ${response.status}.`);
    }
    const data: unknown = await response.json();
    if (!esSalud(data)) {
      throw new Error("La respuesta del servicio no cumple el contrato de /health.");
    }
    return data;
  } catch (error) {
    if (tiempoAgotado) {
      throw new Error("El servicio no respondió en 8 segundos. Revisa la conexión y vuelve a intentar.");
    }
    if (error instanceof TypeError) {
      throw new Error("No se pudo conectar con el dominio. Comprueba que esté encendido y revisa la dirección de red.");
    }
    if (error instanceof SyntaxError) {
      throw new Error("El servicio no devolvió una respuesta JSON válida.");
    }
    throw error;
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", cancelar);
  }
}
