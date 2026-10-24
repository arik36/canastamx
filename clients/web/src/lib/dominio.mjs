// Las dos llamadas de la web al servicio de dominio, según dominio.yaml 0.2.2:
// POST /api/v1/sesiones (Credenciales → Sesion) y GET /api/v1/cuentas/yo (→ Cuenta).
// Reciben `fetch` como argumento para que `npm test` las pruebe sin servidor.

import { ROLES_WEB } from './rutas.mjs'

/** Sin DOMINIO_URL, el servicio de dominio en desarrollo (servers de dominio.yaml). */
export function urlDelDominio(entorno = process.env) {
  return (entorno.DOMINIO_URL || 'http://localhost:8081').replace(/\/+$/, '')
}

/**
 * Inicia sesión con el correo y la contraseña. Sólo entran ANALISTA y OPERADOR.
 * @returns {Promise<{ estado: 200, sesion: { token: string, expiraEn: Date, rol: string } }
 *                  | { estado: number, error: string }>}
 */
export async function iniciarSesion({ correo, contrasena }, { dominioUrl, fetch }) {
  let respuesta
  try {
    respuesta = await fetch(`${dominioUrl}/api/v1/sesiones`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ correo, contrasena }),
    })
  } catch {
    return { estado: 503, error: 'No se pudo contactar al servicio de dominio.' }
  }
  if (respuesta.status === 401) {
    return { estado: 401, error: 'Correo o contraseña incorrectos.' }
  }
  if (!respuesta.ok) {
    return { estado: 502, error: 'El servicio de dominio respondió con un error.' }
  }
  const sesion = await respuesta.json().catch(() => null)
  if (sesion?.rol === 'CONSUMIDOR') {
    return { estado: 403, error: 'La web es para analistas y operadores. Usa la app de CanastaMX.' }
  }
  const expiraEn = new Date(sesion?.expiraEn)
  if (typeof sesion?.token !== 'string' || Number.isNaN(expiraEn.getTime())
      || !ROLES_WEB.includes(sesion?.rol)) {
    return { estado: 502, error: 'La sesión no trae token, vencimiento o un rol de la web.' }
  }
  return { estado: 200, sesion: { token: sesion.token, expiraEn, rol: sesion.rol } }
}

/**
 * La cuenta del token, según el dominio (D-10). Sólo se toman el correo y el rol: la
 * cuenta no tiene nombre (P-13).
 * @returns {Promise<{ estado: 'ok', cuenta: { correo: string, rol: string } }
 *                  | { estado: 'sin-sesion' } | { estado: 'error' }>}
 */
export async function leerCuenta(token, { dominioUrl, fetch }) {
  let respuesta
  try {
    respuesta = await fetch(`${dominioUrl}/api/v1/cuentas/yo`, {
      headers: { Authorization: `Bearer ${token}`, Accept: 'application/json' },
    })
  } catch {
    return { estado: 'error' }
  }
  if (respuesta.status === 401) {
    return { estado: 'sin-sesion' }
  }
  if (!respuesta.ok) {
    return { estado: 'error' }
  }
  const cuenta = await respuesta.json().catch(() => null)
  if (typeof cuenta?.correo !== 'string' || !ROLES_WEB.includes(cuenta?.rol)) {
    return cuenta?.rol === 'CONSUMIDOR' ? { estado: 'sin-sesion' } : { estado: 'error' }
  }
  return { estado: 'ok', cuenta: { correo: cuenta.correo, rol: cuenta.rol } }
}
