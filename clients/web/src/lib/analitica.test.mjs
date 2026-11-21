// npm test · lo que el tablero le pide a la analítica y lo que hace con la respuesta
// (analitica.yaml 0.2.1: articulosAnomalos). Un fetch falso guarda cada petición.
import assert from 'node:assert/strict'
import { test } from 'node:test'

import {
  SIMULADOR,
  conteo,
  esSimulador,
  leerAnomalias,
  nombreDelArticulo,
  textoDePoblacion,
  urlDeAnalitica,
  variacionEnPorcentaje,
} from './analitica.mjs'

const ANALITICA = 'http://analitica.prueba'

function fetchFalso(estado, cuerpo) {
  const peticiones = []
  const fetch = async (url, opciones = {}) => {
    peticiones.push({ url, ...opciones })
    return new Response(cuerpo === undefined ? null : JSON.stringify(cuerpo), { status: estado })
  }
  return { fetch, peticiones }
}

const fetchCaido = async () => { throw new TypeError('fetch failed') }

// La forma de articulosAnomalos: un objeto con la lista y la población, no una lista.
const RESPUESTA = {
  articulos: [
    {
      articulo: { producto: 'huevo', presentacion: 'paquete c 30 blanco' },
      entidad: 'Guanajuato', quincena: '2026-07-Q2', variacion: 0.2734, observaciones: 12,
    },
    {
      articulo: { producto: 'frijol', presentacion: 'bolsa 1 kg negro' },
      entidad: 'Jalisco', quincena: '2026-07-Q1', variacion: -0.3125, observaciones: 7,
    },
  ],
  poblacion: { entidades: ['Guanajuato', 'Jalisco'], desde: '2026-06-Q2', hasta: '2026-07-Q2', observaciones: 1540 },
}

test('sin ANALITICA_URL va al simulador y lo reconoce; con ella, a la analítica que se dé', () => {
  assert.equal(SIMULADOR, 'http://localhost:4011')
  assert.equal(urlDeAnalitica({}), SIMULADOR)
  assert.equal(esSimulador({}), true)
  assert.equal(esSimulador({ ANALITICA_URL: 'http://localhost:4011/' }), true)
  assert.equal(urlDeAnalitica({ ANALITICA_URL: 'http://analytics-api:8000/' }), 'http://analytics-api:8000')
  assert.equal(esSimulador({ ANALITICA_URL: 'http://localhost:8000' }), false)
})

test('pide GET /api/v1/anomalias con el token de la sesión y sin umbral ni mínimo (P-15)', async () => {
  const { fetch, peticiones } = fetchFalso(200, RESPUESTA)
  await leerAnomalias('token-del-analista', { analiticaUrl: ANALITICA, fetch })

  assert.equal(peticiones.length, 1)
  assert.equal(peticiones[0].url, `${ANALITICA}/api/v1/anomalias`)
  assert.equal(peticiones[0].method, undefined)          // GET
  assert.equal(peticiones[0].headers.Authorization, 'Bearer token-del-analista')
})

test('con la respuesta del contrato devuelve los artículos y su población', async () => {
  const { fetch } = fetchFalso(200, RESPUESTA)
  const r = await leerAnomalias('t', { analiticaUrl: ANALITICA, fetch })
  assert.deepEqual(r, { estado: 'ok', articulos: RESPUESTA.articulos, poblacion: RESPUESTA.poblacion })
})

test('sin anomalías también es una respuesta: la lista vacía, con su población', async () => {
  const vacia = { articulos: [], poblacion: RESPUESTA.poblacion }
  const r = await leerAnomalias('t', { analiticaUrl: ANALITICA, fetch: fetchFalso(200, vacia).fetch })
  assert.deepEqual(r, { estado: 'ok', articulos: [], poblacion: RESPUESTA.poblacion })
})

test('una respuesta sin la forma de articulosAnomalos es un aviso, no una vista rota', async () => {
  const [fila] = RESPUESTA.articulos
  const casos = [
    RESPUESTA.articulos,                                                  // una lista sola
    { articulos: RESPUESTA.articulos },                                   // sin población (RNF-16)
    { ...RESPUESTA, articulos: [{ ...fila, articulo: 'huevo' }] },        // el artículo como texto
    { ...RESPUESTA, articulos: [{ ...fila, variacion: '27%' }] },
    { ...RESPUESTA, articulos: [{ ...fila, precio: 64, variacion: undefined }] },
    { ...RESPUESTA, poblacion: { ...RESPUESTA.poblacion, desde: undefined } },
    { ...RESPUESTA, poblacion: { ...RESPUESTA.poblacion, hasta: undefined } },
    { ...RESPUESTA, poblacion: { ...RESPUESTA.poblacion, entidades: 'Guanajuato' } },
    { ...RESPUESTA, poblacion: { ...RESPUESTA.poblacion, observaciones: '1540' } },
    null,
  ]
  for (const cuerpo of casos) {
    const r = await leerAnomalias('t', { analiticaUrl: ANALITICA, fetch: fetchFalso(200, cuerpo).fetch })
    assert.deepEqual(r, { estado: 'error', motivo: 'respondió 200 sin la forma de articulosAnomalos' },
      JSON.stringify(cuerpo))
  }
})

test('cada falla de la analítica da su motivo, y ninguno lleva el token', async () => {
  const problema = (status, detail) => ({ type: 'about:blank', title: 'Problema', status, detail })
  const casos = [
    [fetchFalso(401, problema(401, 'Esta ruta pide una sesión con el rol ANALISTA.')).fetch,
      'respondió 401: Esta ruta pide una sesión con el rol ANALISTA'],
    [fetchFalso(404, problema(404, 'La capa de consumo todavía no tiene datos.')).fetch,
      'respondió 404: La capa de consumo todavía no tiene datos'],
    [fetchFalso(500).fetch, 'respondió 500'],
    [fetchCaido, 'no contestó'],
  ]
  for (const [fetch, motivo] of casos) {
    const r = await leerAnomalias('token-secreto', { analiticaUrl: ANALITICA, fetch })
    assert.deepEqual(r, { estado: 'error', motivo })
    assert.doesNotMatch(r.motivo, /token-secreto/)
  }
})

test('las cifras se leen como en el contrato: proporción en por ciento, con signo', () => {
  assert.equal(variacionEnPorcentaje(0.2734), '+27.3%')
  assert.equal(variacionEnPorcentaje(-0.3125), '-31.3%')
  assert.equal(variacionEnPorcentaje(0.2), '+20%')
  assert.equal(conteo(2585186), '2,585,186')
  assert.equal(nombreDelArticulo(RESPUESTA.articulos[0].articulo), 'huevo · paquete c 30 blanco')
})

test('la población dice cuántas observaciones, de qué entidades y de qué quincenas (RNF-16)', () => {
  assert.equal(textoDePoblacion(RESPUESTA.poblacion),
    '1,540 observaciones de Guanajuato y Jalisco, de 2026-06-Q2 a 2026-07-Q2')
  assert.equal(textoDePoblacion({ entidades: ['Colima'], desde: '2026-07-Q2', hasta: '2026-07-Q2', observaciones: 1 }),
    '1 observación de Colima, en 2026-07-Q2')
  assert.equal(textoDePoblacion({ entidades: [], desde: '2026-07-Q1', hasta: '2026-07-Q2', observaciones: 0 }),
    'ninguna observación, de 2026-07-Q1 a 2026-07-Q2')
})
