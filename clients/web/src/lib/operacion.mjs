// Lo que la consola de observabilidad le pide a la interfaz analítica, según
// analitica.yaml 0.2.1: las seis rutas con `x-rol: OPERADOR` (CU-04 y CU-05). Se piden
// desde el servidor de la web con el token de la sesión, como el tablero. Reciben
// `fetch` como argumento para que `npm test` las pruebe sin servidor.

import { conteo } from './analitica.mjs'

/** Cuántos renglones pide la consola de cada lista (P-05: máximo 100). */
export const LIMITES = { corridas: 10, historial: 20, abiertos: 100, cuarentena: 10 }

/** El nombre de un lote, como lo valida `operacion.corrida`: 07-2026_Q2 o 01-2025_01. */
export const LOTE = /^(0[1-9]|1[0-2])-\d{4}_(Q[12]|0[12])$/

/** Las cuatro causas de cierre del contrato (CU-04), con su nombre en pantalla. */
export const CAUSAS = {
  ARCHIVO_DE_LA_FUENTE: 'El archivo de la fuente',
  REGLA_DEL_CONTRATO: 'Una regla del contrato',
  DATO_REAL_ATIPICO: 'Un dato real atípico',
  INFRAESTRUCTURA: 'La infraestructura',
}

/** La decisión es «qué se hizo, en una o dos frases» (analitica.yaml). */
export const LARGO_DE_LA_DECISION = 500

/**
 * Las formas de analitica.yaml 0.2.1 que pinta la consola.
 * @typedef {'CORRECTA' | 'CON_AVISOS' | 'RECHAZADA' | 'FALLIDA'} Resultado
 * @typedef {{ lote: string, fecha: string, resultado: Resultado, filasLeidas: number,
 *             filasAceptadas: number, filasEnCuarentena: number,
 *             duracionSegundos?: number | null }} Corrida
 * @typedef {{ ultimoDato?: string | null,
 *             frescura: { estado: 'OK' | 'AVISA' | 'BLOQUEA' | 'NO_APLICA', dias?: number | null },
 *             ultimaCorrida: Corrida, filasProcesadas: number,
 *             cuarentena: { filas: number, porcentaje: number, poblacion: string },
 *             avisosDeEsquema: number, incidentesAbiertos: number }} Indicadores
 * @typedef {{ id: string, severidad: 'AVISO' | 'INCIDENTE', lote: string, compuerta: string,
 *             motivo: string, filas: number, estado: 'ABIERTO' | 'CERRADO' | 'INFORMATIVO',
 *             abiertoEn: string, cerradoEn?: string | null, cerradoPor?: string | null,
 *             causa?: string | null, decision?: string | null,
 *             reprocesarLote?: boolean }} Incidente
 * @typedef {{ lote: string, motivo: string, compuerta?: string | null,
 *             fila: Record<string, unknown> }} FilaEnCuarentena
 * @typedef {{ estado: 'error', motivo: string }} Falla
 * @typedef {{ analiticaUrl: string, fetch: typeof fetch }} Dependencias
 */

const RESULTADOS = {
  CORRECTA: 'Correcta', CON_AVISOS: 'Con avisos', RECHAZADA: 'Rechazada', FALLIDA: 'Fallida',
}
// Nunca «al día»: la fuente no publica desde julio de 2026 (diseno.md §6, regla 3).
const FRESCURAS = { OK: 'Dentro del umbral', AVISA: 'Avisa', BLOQUEA: 'Bloquea', NO_APLICA: 'No aplica' }
const SEVERIDADES = ['AVISO', 'INCIDENTE']
const ESTADOS_DE_INCIDENTE = ['ABIERTO', 'CERRADO', 'INFORMATIVO']

// ── Las llamadas ─────────────────────────────────────────────────────────────

async function pedir(ruta, token, { analiticaUrl, fetch }, { metodo = 'GET', cuerpo } = {}) {
  let respuesta
  try {
    respuesta = await fetch(`${analiticaUrl}${ruta}`, {
      method: metodo,
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: 'application/json',
        ...(cuerpo === undefined ? {} : { 'Content-Type': 'application/json' }),
      },
      ...(cuerpo === undefined ? {} : { body: JSON.stringify(cuerpo) }),
      cache: 'no-store',
    })
  } catch {
    return { estado: 'error', motivo: 'no contestó' }
  }
  const json = await respuesta.json().catch(() => null)
  if (!respuesta.ok) {
    // Como en el tablero: el `detail` del problema dice más que el número, sin su punto
    // final, porque quien muestra el motivo cierra la frase. Nunca lleva el token.
    const detalle = typeof json?.detail === 'string' ? json.detail.trim().replace(/\.+$/, '') : ''
    return {
      estado: 'error',
      status: respuesta.status,
      motivo: `respondió ${respuesta.status}${detalle ? `: ${detalle}` : ''}`,
    }
  }
  return { estado: 'ok', status: respuesta.status, json }
}

const sinForma = (status, operacion) =>
  ({ estado: 'error', motivo: `respondió ${status} sin la forma de ${operacion}` })

function consulta(parametros) {
  const texto = new URLSearchParams(
    Object.entries(parametros).filter(([, valor]) => valor !== undefined && valor !== null)
      .map(([clave, valor]) => [clave, String(valor)]),
  ).toString()
  return texto ? `?${texto}` : ''
}

/**
 * Los seis indicadores de CU-05 (estadoDeLaPlataforma). Sin corridas, la analítica
 * responde 404 (CU-05 · 2b) y la consola lo dice en lugar de mostrar ceros.
 * @param {string} token
 * @param {Dependencias} dependencias
 * @returns {Promise<{ estado: 'ok', indicadores: Indicadores } | { estado: 'sin-corridas', motivo: string }
 *                  | Falla>}
 */
export async function leerEstado(token, dependencias) {
  const r = await pedir('/api/v1/operacion/estado', token, dependencias)
  if (r.estado === 'error') {
    return r.status === 404 ? { estado: 'sin-corridas', motivo: r.motivo } : sinStatus(r)
  }
  return esEstado(r.json) ? { estado: 'ok', indicadores: r.json } : sinForma(r.status, 'estadoDeLaPlataforma')
}

/**
 * Las corridas, de la más reciente a la más antigua (listarCorridas).
 * @param {string} token
 * @param {{ limit?: number }} filtro
 * @param {Dependencias} dependencias
 * @returns {Promise<{ estado: 'ok', corridas: Corrida[], total: number } | Falla>}
 */
export async function leerCorridas(token, { limit = LIMITES.corridas } = {}, dependencias) {
  const r = await pedir(`/api/v1/operacion/corridas${consulta({ limit })}`, token, dependencias)
  if (r.estado === 'error') return sinStatus(r)
  const { corridas, total } = r.json ?? {}
  return Array.isArray(corridas) && corridas.every(esCorrida) && esConteo(total)
    ? { estado: 'ok', corridas, total }
    : sinForma(r.status, 'listarCorridas')
}

/**
 * Todas las corridas de un lote, de la más antigua a la vigente (linajeDeLote, CU-05 · 5a).
 * @param {string} token
 * @param {string} lote
 * @param {Dependencias} dependencias
 * @returns {Promise<{ estado: 'ok', lote: string, corridas: Corrida[] } | Falla>}
 */
export async function leerLinaje(token, lote, dependencias) {
  const r = await pedir(`/api/v1/operacion/corridas/${encodeURIComponent(lote)}`, token, dependencias)
  if (r.estado === 'error') return sinStatus(r)
  const { corridas } = r.json ?? {}
  return esTexto(r.json?.lote) && Array.isArray(corridas) && corridas.length > 0 && corridas.every(esCorrida)
    ? { estado: 'ok', lote: r.json.lote, corridas }
    : sinForma(r.status, 'linajeDeLote')
}

/**
 * Las filas en cuarentena, con su motivo; las de un lote si se da (listarCuarentena). Son
 * las que apartó la corrida vigente de cada lote: las mismas que cuenta el indicador.
 * @param {string} token
 * @param {{ lote?: string, limit?: number }} filtro
 * @param {Dependencias} dependencias
 * @returns {Promise<{ estado: 'ok', filas: FilaEnCuarentena[], total: number } | Falla>}
 */
export async function leerCuarentena(token, { lote, limit = LIMITES.cuarentena } = {}, dependencias) {
  const r = await pedir(`/api/v1/operacion/cuarentena${consulta({ lote, limit })}`, token, dependencias)
  if (r.estado === 'error') return sinStatus(r)
  const { filas, total } = r.json ?? {}
  return Array.isArray(filas) && filas.every(esFilaEnCuarentena) && esConteo(total)
    ? { estado: 'ok', filas, total }
    : sinForma(r.status, 'listarCuarentena')
}

/**
 * Incidentes y avisos, del más reciente al más antiguo (listarIncidentes, RF-13).
 * @param {string} token
 * @param {{ estado?: 'ABIERTO' | 'CERRADO', severidad?: 'AVISO' | 'INCIDENTE', limit?: number }} filtro
 * @param {Dependencias} dependencias
 * @returns {Promise<{ estado: 'ok', incidentes: Incidente[], total: number } | Falla>}
 */
export async function leerIncidentes(token, { estado, severidad, limit = LIMITES.historial } = {},
  dependencias) {
  const ruta = `/api/v1/operacion/incidentes${consulta({ estado, severidad, limit })}`
  const r = await pedir(ruta, token, dependencias)
  if (r.estado === 'error') return sinStatus(r)
  const { incidentes, total } = r.json ?? {}
  return Array.isArray(incidentes) && incidentes.every(esIncidente) && esConteo(total)
    ? { estado: 'ok', incidentes, total }
    : sinForma(r.status, 'listarIncidentes')
}

/**
 * Cierra un incidente con su causa y su decisión (cerrarIncidente, CU-04 pasos 5 y 6).
 * Quién cierra y cuándo no van en el cuerpo: los pone la analítica, con el correo que le
 * da el dominio para este token (D-11).
 * @param {string} token
 * @param {string} id
 * @param {{ causa: string, decision: string, reprocesarLote: boolean }} cierre
 * @param {Dependencias} dependencias
 * @returns {Promise<{ estado: 'ok', incidente: Incidente } | Falla>}
 */
export async function cerrarIncidente(token, id, cierre, dependencias) {
  const { causa, decision, reprocesarLote } = cierre
  const r = await pedir(`/api/v1/operacion/incidentes/${encodeURIComponent(id)}/cierre`, token,
    dependencias, { metodo: 'POST', cuerpo: { causa, decision, reprocesarLote } })
  if (r.estado === 'error') return sinStatus(r)
  return esIncidente(r.json) ? { estado: 'ok', incidente: r.json } : sinForma(r.status, 'cerrarIncidente')
}

// La página sólo necesita el motivo; el número ya va dentro de él.
const sinStatus = ({ estado, motivo }) => ({ estado, motivo })

/**
 * Lo que llega del formulario de cierre, revisado antes de mandarlo: un FormData es
 * texto que cualquiera puede armar a mano.
 * @param {FormData} datos
 * @returns {{ estado: 'ok', id: string, cierre: { causa: string, decision: string, reprocesarLote: boolean } }
 *          | { estado: 'error', motivo: string }}
 */
export function leerCierre(datos) {
  const id = String(datos.get('incidenteId') ?? '').trim()
  const causa = String(datos.get('causa') ?? '')
  const decision = String(datos.get('decision') ?? '').trim()
  if (!/^[\w-]{1,40}$/.test(id)) {
    return { estado: 'error', motivo: 'El formulario no dice qué incidente cerrar.' }
  }
  if (!Object.hasOwn(CAUSAS, causa)) {
    return { estado: 'error', motivo: 'Elige la causa del incidente.' }
  }
  if (!decision) {
    return { estado: 'error', motivo: 'Escribe qué se hizo: un cierre sin decisión no se acepta (SLA-D-09).' }
  }
  if (decision.length > LARGO_DE_LA_DECISION) {
    return { estado: 'error', motivo: `La decisión pasa de ${LARGO_DE_LA_DECISION} caracteres: resúmela en una o dos frases.` }
  }
  return { estado: 'ok', id, cierre: { causa, decision, reprocesarLote: datos.get('reprocesarLote') === 'si' } }
}

// ── Lo que se revisa de cada respuesta ──────────────────────────────────────
// Lo que la consola pinta tiene que venir completo: un campo a medias tumbaría la vista.
// Lo opcional del contrato (o lo que la analítica omite cuando es null) puede faltar.

const esTexto = (valor) => typeof valor === 'string'
const esConteo = (valor) => Number.isInteger(valor) && valor >= 0
const esNumero = (valor) => typeof valor === 'number' && Number.isFinite(valor)
const esFecha = (valor) => esTexto(valor) && !Number.isNaN(Date.parse(valor))
const esQuincena = (valor) => esTexto(valor) && /^\d{4}-(0[1-9]|1[0-2])-Q[12]$/.test(valor)
const puedeFaltar = (prueba) => (valor) => valor === undefined || valor === null || prueba(valor)

function esCorrida(c) {
  return esTexto(c?.lote) && esFecha(c?.fecha) && Object.hasOwn(RESULTADOS, c?.resultado ?? '')
    && esConteo(c?.filasLeidas) && esConteo(c?.filasAceptadas) && esConteo(c?.filasEnCuarentena)
    && puedeFaltar(esNumero)(c?.duracionSegundos)
}

function esEstado(e) {
  // `ultimoDato` falta mientras ningún lote haya pasado: es uno de los huecos del
  // contrato 0.2.1 que anota docs/analisis/openapi/README.md.
  return puedeFaltar(esQuincena)(e?.ultimoDato)
    && Object.hasOwn(FRESCURAS, e?.frescura?.estado ?? '') && puedeFaltar(Number.isInteger)(e?.frescura?.dias)
    && esCorrida(e?.ultimaCorrida) && esConteo(e?.filasProcesadas)
    && esConteo(e?.cuarentena?.filas) && esNumero(e?.cuarentena?.porcentaje) && esTexto(e?.cuarentena?.poblacion)
    && esConteo(e?.avisosDeEsquema) && esConteo(e?.incidentesAbiertos)
}

function esIncidente(i) {
  return esTexto(i?.id) && SEVERIDADES.includes(i?.severidad) && esTexto(i?.lote)
    && esTexto(i?.compuerta) && esTexto(i?.motivo) && esConteo(i?.filas)
    && ESTADOS_DE_INCIDENTE.includes(i?.estado) && esFecha(i?.abiertoEn)
    && puedeFaltar(esFecha)(i?.cerradoEn) && puedeFaltar(esTexto)(i?.cerradoPor)
    && puedeFaltar(esTexto)(i?.causa) && puedeFaltar(esTexto)(i?.decision)
    && puedeFaltar((v) => typeof v === 'boolean')(i?.reprocesarLote)
}

function esFilaEnCuarentena(f) {
  return esTexto(f?.lote) && esTexto(f?.motivo) && puedeFaltar(esTexto)(f?.compuerta)
    && typeof f?.fila === 'object' && f.fila !== null && !Array.isArray(f.fila)
}

// ── Cómo se lee en pantalla ─────────────────────────────────────────────────

/**
 * El semáforo (diseno.md §5): verde OK, azul aviso, rojo incidente y gris «no aplica».
 * Nunca naranja, que es del mercado.
 * @typedef {'ok' | 'aviso' | 'incidente' | 'no-aplica'} Nivel
 */

/** @returns {Nivel} */
export function nivelDeCorrida(resultado) {
  return { CORRECTA: 'ok', CON_AVISOS: 'aviso', RECHAZADA: 'incidente', FALLIDA: 'incidente' }[resultado]
}

/** @returns {Nivel} */
export function nivelDeFrescura(estado) {
  return { OK: 'ok', AVISA: 'aviso', BLOQUEA: 'incidente', NO_APLICA: 'no-aplica' }[estado]
}

/**
 * Los que llevan «Cerrar con causa»: sólo los incidentes abiertos. Un aviso nunca, aunque
 * la lista lo traiga como abierto (el simulador lo hace): los avisos no se cierran (RF-13).
 * @param {Incidente[]} incidentes
 */
export function porCerrar(incidentes) {
  return incidentes.filter((i) => i.severidad === 'INCIDENTE' && i.estado === 'ABIERTO')
}

export const nombreDelResultado = (resultado) => RESULTADOS[resultado]
export const nombreDeLaFrescura = (estado) => FRESCURAS[estado]
export const nombreDeLaCausa = (causa) => CAUSAS[causa] ?? causa

/**
 * La respuesta de los tres segundos (CU-05 · 3): ¿la última corrida fue correcta y no
 * hay incidentes abiertos? Lo rojo gana a lo azul. Los avisos de esquema no la cambian:
 * informan y no se cierran (RF-13), así que con ellos la consola no volvería al verde.
 * @param {Indicadores} indicadores
 * @returns {{ nivel: Nivel, titulo: string }}
 */
export function estadoGeneral({ incidentesAbiertos, ultimaCorrida, frescura }) {
  if (incidentesAbiertos > 0) {
    return {
      nivel: 'incidente',
      titulo: incidentesAbiertos === 1 ? 'Hay 1 incidente abierto'
        : `Hay ${conteo(incidentesAbiertos)} incidentes abiertos`,
    }
  }
  const corrida = nivelDeCorrida(ultimaCorrida.resultado)
  const resultado = nombreDelResultado(ultimaCorrida.resultado).toLowerCase()
  if (corrida === 'incidente') {
    return { nivel: 'incidente', titulo: `La última corrida terminó ${resultado}` }
  }
  if (frescura.estado === 'BLOQUEA') {
    return { nivel: 'incidente', titulo: 'La frescura bloquea la publicación del dato' }
  }
  if (corrida === 'aviso') {
    return { nivel: 'aviso', titulo: 'La última corrida terminó con avisos y no hay incidentes abiertos' }
  }
  if (frescura.estado === 'AVISA') {
    return { nivel: 'aviso', titulo: 'La frescura avisa y no hay incidentes abiertos' }
  }
  return { nivel: 'ok', titulo: 'La última corrida fue correcta y no hay incidentes abiertos' }
}

/**
 * La frescura en una frase (CU-05 · 2a): sin alarma mientras la fuente no publique.
 * @param {Indicadores['frescura']} frescura
 * @param {string | null | undefined} ultimoDato
 */
export function textoDeFrescura({ estado, dias }, ultimoDato) {
  // No dice «desde cuándo»: si el último lote se rechazó, el dato más reciente que pasó
  // es más viejo que lo último que publicó la fuente. Esa fecha va en su propia línea.
  if (estado === 'NO_APLICA') {
    return ultimoDato ? 'La regla no corre mientras la fuente no publique: el corpus está congelado.'
      : 'Todavía no hay dato que medir.'
  }
  const cuantos = Number.isInteger(dias) ? `${conteo(dias)} ${dias === 1 ? 'día' : 'días'}` : 'Sin días'
  return `${cuantos} del último registro a la última corrida.`
}

// La hora del equipo, en León, aunque el servidor corra en UTC (la VM).
const FECHA_Y_HORA = new Intl.DateTimeFormat('es-MX', {
  day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  hourCycle: 'h23', timeZone: 'America/Mexico_City',
})
const POR_CIENTO = new Intl.NumberFormat('es-MX', { maximumFractionDigits: 3 })

/** «12 nov 2026, 10:32», en la hora del centro de México. */
export function fechaYHora(fecha) {
  return FECHA_Y_HORA.format(new Date(fecha))
}

/**
 * El porcentaje de la cuarentena ya viene en por ciento: 0.041 se lee «0.041%», como lo
 * calcula la vista `estado_de_la_plataforma` (100 × apartadas ÷ leídas). No es una
 * proporción, como la `variacion` de las anomalías.
 */
export function porcentaje(valor) {
  return `${POR_CIENTO.format(valor)}%`
}

/** «45 s», «1 min» o «3 min 5 s». Sin dato, «—». */
export function duracion(segundos) {
  if (!esNumero(segundos)) return '—'
  const total = Math.round(segundos)
  if (total < 60) return `${total} s`
  return total % 60 === 0 ? `${total / 60} min` : `${Math.floor(total / 60)} min ${total % 60} s`
}

/** «1 fila» o «1,089 filas». */
export function filas(numero) {
  return `${conteo(numero)} ${numero === 1 ? 'fila' : 'filas'}`
}

/** La fila apartada tal como llegó, en una línea: «producto: huevo · precio: 9999». */
export function textoDeFila(fila) {
  const texto = (valor) => valor === null || valor === undefined || valor === '' ? '(vacío)'
    : typeof valor === 'object' ? JSON.stringify(valor) : String(valor)
  return Object.entries(fila).map(([clave, valor]) => `${clave}: ${texto(valor)}`).join(' · ')
}
