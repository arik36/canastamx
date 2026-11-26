// Lo que el tablero y el detalle de artículo le piden a la interfaz analítica, según
// analitica.yaml 0.2.1: GET /api/v1/anomalias, /articulos/serie y /articulos/establecimientos
// (x-rol: ANALISTA), desde el servidor de la web y con el token de la sesión, como las
// llamadas al dominio. Recibe `fetch` como argumento para que `npm test` la pruebe sin servidor.

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

// ── El detalle de artículo (vista 3): serieDeArticulo y desgloseDeArticulo ─────────
// Las dos con `x-rol: ANALISTA`, como las anomalías. El catálogo, para el ícono, sale de
// buscarArticulos, que es la única ruta que lo trae.

/**
 * @typedef {{ monto: string, moneda: 'MXN' }} Dinero
 * @typedef {{ quincena: string, entidad: string, mediana: Dinero, p25?: Dinero, p75?: Dinero,
 *             minimo?: Dinero, maximo?: Dinero, observaciones: number }} PuntoDeSerie
 * @typedef {{ nombre: string, cadena: string, maximo: Dinero, minimo: Dinero, promedio: Dinero,
 *             observaciones: number }} Establecimiento
 */

const QUINCENA = /^(\d{4})-(0[1-9]|1[0-2])-Q([12])$/
export const esQuincena = (valor) => esTexto(valor) && QUINCENA.test(valor)
const esDinero = (d) => esTexto(d?.monto) && /^\d+\.\d{2}$/.test(d.monto) && d?.moneda === 'MXN'
const puedeFaltar = (prueba) => (valor) => valor === undefined || valor === null || prueba(valor)
const esPositivo = (valor) => Number.isInteger(valor) && valor >= 1

function esPunto(p) {
  return esQuincena(p?.quincena) && esTexto(p?.entidad) && esDinero(p?.mediana) && esPositivo(p?.observaciones)
    && ['p25', 'p75', 'minimo', 'maximo'].every((campo) => puedeFaltar(esDinero)(p?.[campo]))
}

function esEstablecimiento(e) {
  return esTexto(e?.nombre) && esTexto(e?.cadena) && esDinero(e?.maximo) && esDinero(e?.minimo)
    && esDinero(e?.promedio) && esPositivo(e?.observaciones)
}

const esPoblacion = (p) => Array.isArray(p?.entidades) && p.entidades.every(esTexto)
  && esTexto(p?.desde) && esTexto(p?.hasta) && esConteo(p?.observaciones)

function consulta(parametros) {
  return new URLSearchParams(Object.entries(parametros)
    .filter(([, valor]) => valor !== undefined && valor !== null && valor !== '')
    .map(([clave, valor]) => [clave, String(valor)])).toString()
}

// Como leerAnomalias: el `detail` del problema, sin su punto final, y nunca el token.
async function pedir(ruta, token, { analiticaUrl, fetch }) {
  let respuesta
  try {
    respuesta = await fetch(`${analiticaUrl}${ruta}`, {
      headers: { Authorization: `Bearer ${token}`, Accept: 'application/json' },
      cache: 'no-store',
    })
  } catch {
    return { estado: 'error', motivo: 'no contestó' }
  }
  const cuerpo = await respuesta.json().catch(() => null)
  if (!respuesta.ok) {
    const detalle = typeof cuerpo?.detail === 'string' ? cuerpo.detail.trim().replace(/\.+$/, '') : ''
    return { estado: 'error', motivo: `respondió ${respuesta.status}${detalle ? `: ${detalle}` : ''}` }
  }
  return { estado: 'ok', status: respuesta.status, cuerpo }
}

/**
 * La serie del artículo en todas las entidades y quincenas del alcance (serieDeArticulo):
 * la gráfica por entidad y los cuatro indicadores salen de aquí.
 * @returns {Promise<{ estado: 'ok', articulo: Articulo, puntos: PuntoDeSerie[] }
 *                  | { estado: 'error', motivo: string }>}
 */
export async function leerSerie(token, { producto, presentacion }, dependencias) {
  const r = await pedir(`/api/v1/articulos/serie?${consulta({ producto, presentacion })}`, token, dependencias)
  if (r.estado === 'error') return r
  const { articulo, puntos } = r.cuerpo ?? {}
  return esTexto(articulo?.producto) && esTexto(articulo?.presentacion) && Array.isArray(puntos)
    && puntos.every(esPunto)
    ? { estado: 'ok', articulo, puntos }
    : { estado: 'error', motivo: `respondió ${r.status} sin la forma de serieDeArticulo` }
}

/**
 * El precio por establecimiento en una entidad y una quincena (desgloseDeArticulo), con
 * la población de las filas que entraron.
 * @returns {Promise<{ estado: 'ok', establecimientos: Establecimiento[], poblacion: Poblacion }
 *                  | { estado: 'error', motivo: string }>}
 */
export async function leerDesglose(token, { producto, presentacion, entidad, quincena }, dependencias) {
  const ruta = `/api/v1/articulos/establecimientos?${consulta({
    producto, presentacion, entidad, desde: quincena, hasta: quincena })}`
  const r = await pedir(ruta, token, dependencias)
  if (r.estado === 'error') return r
  const { establecimientos, poblacion } = r.cuerpo ?? {}
  return Array.isArray(establecimientos) && establecimientos.every(esEstablecimiento) && esPoblacion(poblacion)
    ? { estado: 'ok', establecimientos, poblacion }
    : { estado: 'error', motivo: `respondió ${r.status} sin la forma de desgloseDeArticulo` }
}

/**
 * El catálogo del artículo, para su ícono. Sólo buscarArticulos lo trae: se busca el
 * producto en la entidad y se toma el resultado con el mismo par canónico. Sin él, `null`.
 * @returns {Promise<{ estado: 'ok', catalogo: string | null } | { estado: 'error', motivo: string }>}
 */
export async function leerCatalogo(token, { producto, presentacion, entidad }, dependencias) {
  const r = await pedir(`/api/v1/articulos?${consulta({ q: producto, entidad, limit: 100 })}`, token, dependencias)
  if (r.estado === 'error') return r
  const resultados = r.cuerpo?.resultados ?? []
  if (!Array.isArray(resultados)) {
    return { estado: 'error', motivo: `respondió ${r.status} sin la forma de buscarArticulos` }
  }
  const suyo = resultados.find((x) => x?.articulo?.producto === producto && x?.articulo?.presentacion === presentacion)
  return { estado: 'ok', catalogo: esTexto(suyo?.catalogo) ? suyo.catalogo : null }
}

/** La dirección del detalle de un artículo anómalo del tablero. */
export function urlDelDetalle({ articulo, entidad, quincena }) {
  return `/detalle?${consulta({ producto: articulo.producto, presentacion: articulo.presentacion, entidad, quincena })}`
}

/** La quincena de calendario anterior, con la que compara P-15: 2026-07-Q1 → 2026-06-Q2. */
export function quincenaAnterior(quincena) {
  const [, anio, mes, mitad] = quincena.match(QUINCENA)
  if (mitad === '2') return `${anio}-${mes}-Q1`
  return mes === '01' ? `${Number(anio) - 1}-12-Q2` : `${anio}-${String(Number(mes) - 1).padStart(2, '0')}-Q2`
}

/** Centavos enteros, para comparar dinero sin punto flotante (P-02). */
export function centavos({ monto }) {
  const [enteros, fraccion] = monto.split('.')
  return Number(enteros) * 100 + Number(fraccion)
}

/** «$1,234.50»: el monto tal como llega, con separador de miles. */
export function dinero({ monto }) {
  const [enteros, fraccion] = monto.split('.')
  return `$${CONTEO.format(Number(enteros))}.${fraccion}`
}

/** Las entidades de la serie, en orden alfabético. */
export function entidadesDeLaSerie(puntos) {
  return [...new Set(puntos.map((p) => p.entidad))].sort((a, b) => a.localeCompare(b, 'es'))
}

/**
 * Lo que dicen los cuatro indicadores de una entidad en una quincena: su punto, el de la
 * quincena de calendario anterior y la variación entre sus medianas, en proporción. Sin
 * quincena, o con una en que la entidad no tiene dato, la más reciente de la entidad.
 * `atipica` aplica P-15: más de 20% y al menos 5 observaciones en cada quincena.
 * @param {PuntoDeSerie[]} puntos
 */
export function resumenDeSerie(puntos, entidad, quincena) {
  const suyos = puntos.filter((p) => p.entidad === entidad)
    .sort((a, b) => a.quincena.localeCompare(b.quincena))
  const elegida = suyos.some((p) => p.quincena === quincena) ? quincena : suyos.at(-1)?.quincena ?? null
  const punto = suyos.find((p) => p.quincena === elegida) ?? null
  const anterior = elegida ? suyos.find((p) => p.quincena === quincenaAnterior(elegida)) ?? null : null
  const base = anterior ? centavos(anterior.mediana) : 0
  const variacion = punto && base > 0 ? (centavos(punto.mediana) - base) / base : null
  const atipica = variacion !== null && Math.abs(variacion) > 0.2
    && Math.min(punto.observaciones, anterior.observaciones) >= 5
  const i = suyos.indexOf(punto)
  return {
    quincena: elegida, punto, anterior, variacion, atipica,
    previa: i > 0 ? suyos[i - 1].quincena : null,
    siguiente: i >= 0 && i < suyos.length - 1 ? suyos[i + 1].quincena : null,
  }
}
