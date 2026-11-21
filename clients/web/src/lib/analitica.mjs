// Lo que el tablero le pide a la interfaz analítica, según analitica.yaml 0.2.1:
// GET /api/v1/anomalias (articulosAnomalos, x-rol: ANALISTA), desde el servidor de la
// web y con el token de la sesión, como las llamadas al dominio. Recibe `fetch` como
// argumento para que `npm test` la pruebe sin servidor.

/** El simulador del contrato (Prism), en el puerto del README. */
export const SIMULADOR = 'http://localhost:4011'

/** Sin ANALITICA_URL, el simulador. Con ella, la analítica a la que apunte. */
export function urlDeAnalitica(entorno = process.env) {
  return (entorno.ANALITICA_URL || SIMULADOR).replace(/\/+$/, '')
}

/** Si la web le habla al simulador: el tablero lo dice, porque sus cifras son ejemplos. */
export function esSimulador(entorno = process.env) {
  return urlDeAnalitica(entorno) === SIMULADOR
}

/**
 * @typedef {{ producto: string, presentacion: string }} Articulo
 * @typedef {{ articulo: Articulo, entidad: string, quincena: string, variacion: number,
 *             observaciones: number }} ArticuloAnomalo
 * @typedef {{ entidades: string[], desde: string, hasta: string, observaciones: number }} Poblacion
 */

/**
 * Los artículos anómalos y la población que se examinó (P-15, RNF-16). La respuesta es
 * un objeto con las dos cosas, no una lista. No manda umbral ni mínimo de
 * observaciones: los pone la analítica (P-15). En un error, `motivo` dice qué pasó,
 * nunca con el token.
 * @param {string} token
 * @returns {Promise<{ estado: 'ok', articulos: ArticuloAnomalo[], poblacion: Poblacion }
 *                  | { estado: 'error', motivo: string }>}
 */
export async function leerAnomalias(token, { analiticaUrl, fetch }) {
  let respuesta
  try {
    respuesta = await fetch(`${analiticaUrl}/api/v1/anomalias`, {
      headers: { Authorization: `Bearer ${token}`, Accept: 'application/json' },
      cache: 'no-store',
    })
  } catch {
    return { estado: 'error', motivo: 'no contestó' }
  }
  const cuerpo = await respuesta.json().catch(() => null)
  if (!respuesta.ok) {
    // Los problemas de analitica.yaml traen `detail`: dice más que el número solo. Sin
    // su punto final, porque quien muestra el motivo cierra la frase.
    const detalle = typeof cuerpo?.detail === 'string' ? cuerpo.detail.trim().replace(/\.+$/, '') : ''
    return { estado: 'error', motivo: `respondió ${respuesta.status}${detalle ? `: ${detalle}` : ''}` }
  }
  if (!esRespuestaDeAnomalias(cuerpo)) {
    return { estado: 'error', motivo: `respondió ${respuesta.status} sin la forma de articulosAnomalos` }
  }
  return { estado: 'ok', articulos: cuerpo.articulos, poblacion: cuerpo.poblacion }
}

const esTexto = (valor) => typeof valor === 'string'
const esConteo = (valor) => Number.isInteger(valor) && valor >= 0

function esArticuloAnomalo(fila) {
  return esTexto(fila?.articulo?.producto) && esTexto(fila?.articulo?.presentacion)
    && esTexto(fila?.entidad) && esTexto(fila?.quincena)
    && Number.isFinite(fila?.variacion) && esConteo(fila?.observaciones)
}

// Lo que el tablero pinta tiene que venir completo: una fila a medias tumbaría la vista.
function esRespuestaDeAnomalias(cuerpo) {
  const poblacion = cuerpo?.poblacion
  return Array.isArray(cuerpo?.articulos) && cuerpo.articulos.every(esArticuloAnomalo)
    && Array.isArray(poblacion?.entidades) && poblacion.entidades.every(esTexto)
    && esTexto(poblacion?.desde) && esTexto(poblacion?.hasta) && esConteo(poblacion?.observaciones)
}

const POR_CIENTO = new Intl.NumberFormat('es-MX', {
  style: 'percent', maximumFractionDigits: 1, signDisplay: 'exceptZero',
})
const CONTEO = new Intl.NumberFormat('es-MX')
const LISTA = new Intl.ListFormat('es-MX', { type: 'conjunction' })

/** La variación de analitica.yaml es una proporción: 0.2734 se lee «+27.3%». */
export function variacionEnPorcentaje(variacion) {
  return POR_CIENTO.format(variacion)
}

/** Un conteo con separador de miles: 2585186 se lee «2,585,186». */
export function conteo(numero) {
  return CONTEO.format(numero)
}

/** El artículo por su par canónico (ADR 002): «huevo · paquete c 30 blanco». */
export function nombreDelArticulo({ producto, presentacion }) {
  return `${producto} · ${presentacion}`
}

/**
 * La población de la respuesta en una frase (RNF-16): cuántas observaciones, de qué
 * entidades y de qué quincenas.
 * @param {Poblacion} poblacion
 */
export function textoDePoblacion({ entidades, desde, hasta, observaciones }) {
  const cuantas = observaciones === 0 ? 'ninguna observación'
    : observaciones === 1 ? '1 observación' : `${conteo(observaciones)} observaciones`
  const deDonde = entidades.length ? ` de ${LISTA.format(entidades)}` : ''
  const cuando = desde === hasta ? `en ${desde}` : `de ${desde} a ${hasta}`
  return `${cuantas}${deDonde}, ${cuando}`
}
