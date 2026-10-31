// Qué vista abre cada rol y qué rol pide cada vista (P-07, inventario-vistas.md).
// Es JavaScript sin dependencias para que `npm test` lo pruebe con Node, sin Next.

/** Los dos roles que entran a la web. CONSUMIDOR usa la app. */
export const ROLES_WEB = ['ANALISTA', 'OPERADOR']

const INICIO = { ANALISTA: '/tablero', OPERADOR: '/consola' }

const ROL_DE_LA_VISTA = {
  '/tablero': 'ANALISTA',
  '/detalle': 'ANALISTA',
  '/consola': 'OPERADOR',
  '/cola': 'OPERADOR',
}

/**
 * La vista con que abre un rol: el tablero al analista y la consola al operador.
 * @param {string | undefined} rol
 * @returns {string | null} null si el rol no entra a la web
 */
export function destinoPorRol(rol) {
  return typeof rol === 'string' && Object.hasOwn(INICIO, rol) ? INICIO[rol] : null
}

/**
 * El rol que pide una ruta, o null si la ruta no es una de las cuatro vistas con sesión.
 * @param {string} ruta
 */
export function rolQuePide(ruta) {
  const vista = '/' + (ruta.split('/')[1] ?? '')
  return Object.hasOwn(ROL_DE_LA_VISTA, vista) ? ROL_DE_LA_VISTA[vista] : null
}

/**
 * Lo que hace el proxy con una petición, según la ruta y la cookie de rol. Es sólo la
 * primera barrera, para no mostrar la vista equivocada: cada vista vuelve a preguntar
 * la cuenta al dominio (lib/sesion.ts), así que una cookie cambiada a mano no basta.
 * @param {string} ruta
 * @param {string | undefined} rol
 * @returns {{ pasa: true } | { redirigeA: string }}
 */
export function decidir(ruta, rol) {
  if (ruta.startsWith('/_next') || ruta.startsWith('/api') || ruta === '/favicon.ico') {
    return { pasa: true }
  }
  const inicio = destinoPorRol(rol)
  if (!inicio) {
    return ruta === '/acceso' ? { pasa: true } : { redirigeA: '/acceso' }
  }
  if (ruta === '/acceso') {
    return { redirigeA: inicio }
  }
  const pide = rolQuePide(ruta)
  if (pide && pide !== rol) {
    return { redirigeA: inicio }
  }
  return { pasa: true }
}
