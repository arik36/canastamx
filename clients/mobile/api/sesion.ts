export type Rol = "CONSUMIDOR" | "ANALISTA" | "OPERADOR";
export type Cuenta = { id: string; correo: string; rol: Rol; fechaDeRegistro: string };
export type Sesion = { token: string; expiraEn: string; rol: Rol };

export class ErrorDeAcceso extends Error {
  constructor(message: string, public readonly status?: number) { super(message); }
}
const esObjeto = (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null;
const esRol = (v: unknown): v is Rol => ["CONSUMIDOR", "ANALISTA", "OPERADOR"].includes(String(v));

async function solicitar(ruta: string, opciones: RequestInit): Promise<unknown> {
  const base = process.env.EXPO_PUBLIC_API_URL?.trim().replace(/\/+$/, "");
  if (!base || !/^https?:\/\//i.test(base)) throw new ErrorDeAcceso("Configura la dirección del servicio y reinicia Expo.");
  const controller = new AbortController();
  let vencio = false;
  const timer = setTimeout(() => { vencio = true; controller.abort(); }, 8000);
  try {
    const respuesta = await fetch(`${base}${ruta}`, { ...opciones, signal: controller.signal });
    if (!respuesta.ok) {
      if (ruta === "/api/v1/cuentas" && respuesta.status === 409) throw new ErrorDeAcceso("Ya existe una cuenta con ese correo. Inicia sesión para continuar.", 409);
      if (ruta === "/api/v1/cuentas" && respuesta.status === 400) throw new ErrorDeAcceso("Revisa el correo y la contraseña: usa entre 8 y 72 caracteres, una mayúscula y un número.", 400);
      if (respuesta.status === 401) throw new ErrorDeAcceso(ruta.endsWith("/sesiones")
        ? "El correo o la contraseña no son válidos." : "Tu sesión venció. Vuelve a iniciar sesión.", 401);
      throw new ErrorDeAcceso("No pudimos completar el acceso. Intenta de nuevo más tarde.", respuesta.status);
    }
    return await respuesta.json();
  } catch (error) {
    if (vencio) throw new ErrorDeAcceso("El servicio no respondió en 8 segundos. Intenta de nuevo.");
    if (error instanceof TypeError) throw new ErrorDeAcceso("No hay conexión con el servicio. Revisa tu conexión e intenta de nuevo.");
    if (error instanceof SyntaxError) throw new ErrorDeAcceso("El servicio devolvió una respuesta que no podemos leer.");
    throw error;
  } finally { clearTimeout(timer); }
}

export async function iniciarSesion(correo: string, contrasena: string): Promise<Sesion> {
  const data = await solicitar("/api/v1/sesiones", { method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({ correo: correo.trim(), contrasena }) });
  if (!esObjeto(data) || typeof data.token !== "string" || !data.token.trim() || !esRol(data.rol)
    || typeof data.expiraEn !== "string" || !Number.isFinite(Date.parse(data.expiraEn)) || Date.parse(data.expiraEn) <= Date.now()) {
    throw new ErrorDeAcceso("La respuesta de sesión no cumple el contrato del servicio.");
  }
  return data as Sesion;
}

function validarCuenta(data: unknown): Cuenta {
  if (!esObjeto(data) || typeof data.id !== "string" || !data.id || typeof data.correo !== "string"
    || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.correo) || !esRol(data.rol)
    || typeof data.fechaDeRegistro !== "string" || !Number.isFinite(Date.parse(data.fechaDeRegistro))) {
    throw new ErrorDeAcceso("La respuesta de la cuenta no cumple el contrato del servicio.");
  }
  return data as Cuenta;
}

export async function consultarMiCuenta(token: string): Promise<Cuenta> {
  return validarCuenta(await solicitar("/api/v1/cuentas/yo", { headers: { Accept: "application/json", Authorization: `Bearer ${token}` } }));
}

export function validarRegistro(correo: string, contrasena: string, confirmacion: string): string {
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(correo.trim())) return "Escribe un correo electrónico válido.";
  if (contrasena.length < 8 || contrasena.length > 72 || !/[A-Z]/.test(contrasena) || !/[0-9]/.test(contrasena)) {
    return "La contraseña debe tener entre 8 y 72 caracteres, una mayúscula y un número.";
  }
  if (contrasena !== confirmacion) return "Las contraseñas no coinciden.";
  return "";
}

export async function registrarCuenta(correo: string, contrasena: string): Promise<Cuenta> {
  const error = validarRegistro(correo, contrasena, contrasena);
  if (error) throw new ErrorDeAcceso(error);
  const cuenta = validarCuenta(await solicitar("/api/v1/cuentas", { method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({ correo: correo.trim(), contrasena }) }));
  if (cuenta.rol !== "CONSUMIDOR") throw new ErrorDeAcceso("El servicio no devolvió una cuenta de consumidor.");
  return cuenta;
}
