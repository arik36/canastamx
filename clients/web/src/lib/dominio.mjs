/**
 * La cuenta del token, según el dominio (D-10). Sólo se toman el correo y el rol: la
 * cuenta no tiene nombre (P-13). En un error, `motivo` dice qué pasó, para que el
 * mensaje no culpe al dominio de no responder cuando sí respondió (un 404, por ejemplo).
 * @returns {Promise<{ estado: 'ok', cuenta: { correo: string, rol: string } }
 *                  | { estado: 'sin-sesion' } | { estado: 'error', motivo: string }>}
 */
export async function leerCuenta(token, { dominioUrl, fetch }) {
  let respuesta
  try {
    respuesta = await fetch(`${dominioUrl}/api/v1/cuentas/yo`, {
      headers: { Authorization: `Bearer ${token}`, Accept: 'application/json' },
    })
  } catch {
    return { estado: 'error', motivo: 'no contestó' }
  }
  if (respuesta.status === 401) {
    return { estado: 'sin-sesion' }
  }
  if (!respuesta.ok) {
    return { estado: 'error', motivo: `respondió ${respuesta.status}` }
  }
  const cuenta = await respuesta.json().catch(() => null)
  if (typeof cuenta?.correo !== 'string' || !ROLES_WEB.includes(cuenta?.rol)) {
    return cuenta?.rol === 'CONSUMIDOR'
      ? { estado: 'sin-sesion' }
      : { estado: 'error', motivo: `respondió ${respuesta.status} sin una cuenta de la web` }
  }
  return { estado: 'ok', cuenta: { correo: cuenta.correo, rol: cuenta.rol } }
}