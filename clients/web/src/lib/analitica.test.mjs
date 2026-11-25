// npm test · lo que el tablero y el detalle le piden a la analítica y lo que hacen con la
// respuesta (analitica.yaml 0.2.1: articulosAnomalos, serieDeArticulo, desgloseDeArticulo y
// buscarArticulos). Un fetch falso guarda cada petición.
import assert from 'node:assert/strict'
import { test } from 'node:test'

import {
  SIMULADOR,
  centavos,
  conteo,
  dinero,
  entidadesDeLaSerie,
  esSimulador,
  leerAnomalias,
  leerCatalogo,
  leerDesglose,
  leerSerie,
  nombreDelArticulo,
  quincenaAnterior,
  resumenDeSerie,
  textoDePoblacion,
  urlDeAnalitica,
  urlDelDetalle,
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

// ── El detalle de artículo (vista 3) ─────────────────────────────────────────

const PESOS = (monto) => ({ monto, moneda: 'MXN' })
const punto = (quincena, entidad, mediana, observaciones, extra = {}) =>
  ({ quincena, entidad, mediana: PESOS(mediana), p25: PESOS(mediana), p75: PESOS(mediana),
     minimo: PESOS(mediana), maximo: PESOS(mediana), observaciones, ...extra })
const SERIE = {
  articulo: { producto: 'huevo', presentacion: 'paquete c 30 blanco' },
  puntos: [
    punto('2026-06-Q2', 'Guanajuato', '60.00', 40),
    punto('2026-06-Q2', 'Jalisco', '62.50', 30),
    punto('2026-07-Q1', 'Guanajuato', '61.00', 44),
    punto('2026-07-Q2', 'Guanajuato', '78.00', 47, { minimo: PESOS('64.90'), maximo: PESOS('92.00') }),
    punto('2026-07-Q2', 'Jalisco', '63.00', 4),
  ],
}
const DESGLOSE = {
  establecimientos: [
    { nombre: 'Soriana Hiper León', cadena: 'Soriana', maximo: PESOS('92.00'), minimo: PESOS('70.00'),
      promedio: PESOS('81.25'), observaciones: 4 },
  ],
  poblacion: { entidades: ['Guanajuato'], desde: '2026-07-Q2', hasta: '2026-07-Q2', observaciones: 4 },
}

test('el detalle pide la serie y el desglose con el par canónico, el token y la quincena', async () => {
  const serie = fetchFalso(200, SERIE)
  await leerSerie('token-del-analista', SERIE.articulo, { analiticaUrl: ANALITICA, fetch: serie.fetch })
  assert.equal(serie.peticiones[0].url,
    `${ANALITICA}/api/v1/articulos/serie?producto=huevo&presentacion=paquete+c+30+blanco`)
  assert.equal(serie.peticiones[0].headers.Authorization, 'Bearer token-del-analista')
  assert.equal(serie.peticiones[0].cache, 'no-store')

  const desglose = fetchFalso(200, DESGLOSE)
  await leerDesglose('t', { ...SERIE.articulo, entidad: 'Guanajuato', quincena: '2026-07-Q2' },
    { analiticaUrl: ANALITICA, fetch: desglose.fetch })
  assert.equal(desglose.peticiones[0].url, `${ANALITICA}/api/v1/articulos/establecimientos?producto=huevo`
    + '&presentacion=paquete+c+30+blanco&entidad=Guanajuato&desde=2026-07-Q2&hasta=2026-07-Q2')
})

test('con las respuestas del contrato devuelve la serie y el desglose tal cual', async () => {
  const deps = (cuerpo) => ({ analiticaUrl: ANALITICA, fetch: fetchFalso(200, cuerpo).fetch })
  assert.deepEqual(await leerSerie('t', SERIE.articulo, deps(SERIE)), { estado: 'ok', ...SERIE })
  assert.deepEqual(await leerDesglose('t', { ...SERIE.articulo, entidad: 'Guanajuato' }, deps(DESGLOSE)),
    { estado: 'ok', ...DESGLOSE })
})

test('una serie o un desglose sin la forma del contrato es un aviso, no una vista rota', async () => {
  const [p] = SERIE.puntos
  const series = [
    { puntos: SERIE.puntos },                                           // sin artículo
    { ...SERIE, puntos: [{ ...p, mediana: 60 }] },                      // dinero como número
    { ...SERIE, puntos: [{ ...p, mediana: PESOS('60') }] },             // sin dos decimales (P-02)
    { ...SERIE, puntos: [{ ...p, quincena: '2026-13-Q1' }] },
    { ...SERIE, puntos: [{ ...p, observaciones: 0 }] },
    { ...SERIE, puntos: [{ ...p, maximo: '92.00' }] },
  ]
  for (const cuerpo of series) {
    const r = await leerSerie('t', SERIE.articulo, { analiticaUrl: ANALITICA, fetch: fetchFalso(200, cuerpo).fetch })
    assert.deepEqual(r, { estado: 'error', motivo: 'respondió 200 sin la forma de serieDeArticulo' }, JSON.stringify(cuerpo))
  }
  const [e] = DESGLOSE.establecimientos
  const desgloses = [
    { establecimientos: DESGLOSE.establecimientos },                    // sin población (RNF-16)
    { ...DESGLOSE, establecimientos: [{ ...e, promedio: PESOS('81.2') }] },
    { ...DESGLOSE, establecimientos: [{ ...e, cadena: undefined }] },
  ]
  for (const cuerpo of desgloses) {
    const r = await leerDesglose('t', { ...SERIE.articulo, entidad: 'Guanajuato' },
      { analiticaUrl: ANALITICA, fetch: fetchFalso(200, cuerpo).fetch })
    assert.deepEqual(r, { estado: 'error', motivo: 'respondió 200 sin la forma de desgloseDeArticulo' }, JSON.stringify(cuerpo))
  }
})

test('las fallas del detalle dan su motivo sin el token', async () => {
  const sinDatos = { type: 'about:blank', title: 'Sin datos', status: 404,
    detail: 'No hay observaciones de ese artículo en esa entidad y periodo.' }
  const r = await leerSerie('token-secreto', SERIE.articulo, { analiticaUrl: ANALITICA, fetch: fetchFalso(404, sinDatos).fetch })
  assert.deepEqual(r, { estado: 'error', motivo: 'respondió 404: No hay observaciones de ese artículo en esa entidad y periodo' })
  const caida = await leerDesglose('token-secreto', { ...SERIE.articulo, entidad: 'Guanajuato' }, { analiticaUrl: ANALITICA, fetch: fetchCaido })
  assert.deepEqual(caida, { estado: 'error', motivo: 'no contestó' })
})

test('el catálogo sale del resultado de la búsqueda con el mismo par canónico', async () => {
  const busqueda = { cobertura: true, entidad: 'Guanajuato', quincena: '2026-07-Q2', total: 2, resultados: [
    { articulo: { producto: 'huevo', presentacion: 'paquete c 18 blanco' }, nombre: 'Huevo', catalogo: 'PACIC',
      precioTipico: PESOS('40.00'), observaciones: 9 },
    { articulo: SERIE.articulo, nombre: 'Huevo', catalogo: 'BASICOS', precioTipico: PESOS('78.00'), observaciones: 47 },
  ] }
  const { fetch, peticiones } = fetchFalso(200, busqueda)
  const r = await leerCatalogo('t', { ...SERIE.articulo, entidad: 'Guanajuato' }, { analiticaUrl: ANALITICA, fetch })
  assert.deepEqual(r, { estado: 'ok', catalogo: 'BASICOS' })
  assert.equal(peticiones[0].url, `${ANALITICA}/api/v1/articulos?q=huevo&entidad=Guanajuato&limit=100`)
  const otro = await leerCatalogo('t', { producto: 'atun', presentacion: 'lata 140 gr', entidad: 'Guanajuato' },
    { analiticaUrl: ANALITICA, fetch: fetchFalso(200, busqueda).fetch })
  assert.deepEqual(otro, { estado: 'ok', catalogo: null })
})

test('del tablero al detalle: la dirección lleva el par canónico, la entidad y la quincena', () => {
  assert.equal(urlDelDetalle(RESPUESTA.articulos[0]),
    '/detalle?producto=huevo&presentacion=paquete+c+30+blanco&entidad=Guanajuato&quincena=2026-07-Q2')
})

test('la quincena anterior es la de calendario, también al cruzar el año (P-15)', () => {
  assert.equal(quincenaAnterior('2026-07-Q2'), '2026-07-Q1')
  assert.equal(quincenaAnterior('2026-07-Q1'), '2026-06-Q2')
  assert.equal(quincenaAnterior('2026-01-Q1'), '2025-12-Q2')
  assert.equal(quincenaAnterior('2025-10-Q1'), '2025-09-Q2')
})

test('el dinero se compara en centavos y se lee con separador de miles', () => {
  assert.equal(centavos(PESOS('65.00')), 6500)
  assert.equal(centavos(PESOS('0.07')), 7)
  assert.equal(dinero(PESOS('65.00')), '$65.00')
  assert.equal(dinero(PESOS('1234.50')), '$1,234.50')
})

test('los cuatro indicadores: el punto elegido, la quincena anterior y su variación', () => {
  const r = resumenDeSerie(SERIE.puntos, 'Guanajuato', '2026-07-Q2')
  assert.equal(r.quincena, '2026-07-Q2')
  assert.equal(r.punto.mediana.monto, '78.00')
  assert.equal(r.anterior.quincena, '2026-07-Q1')
  assert.equal(variacionEnPorcentaje(r.variacion), '+27.9%')        // (78 − 61) / 61
  assert.equal(r.atipica, true)                                      // > 20% y 47 y 44 observaciones
  assert.equal(r.previa, '2026-07-Q1')
  assert.equal(r.siguiente, null)

  // Sin quincena, la más reciente de la entidad; con pocas observaciones no es atípica.
  const jalisco = resumenDeSerie(SERIE.puntos, 'Jalisco')
  assert.equal(jalisco.quincena, '2026-07-Q2')
  assert.equal(jalisco.anterior, null)                               // 2026-07-Q1 no se observó
  assert.equal(jalisco.variacion, null)
  assert.equal(jalisco.atipica, false)

  // Una quincena que la entidad no tiene: la más reciente. Una entidad sin datos: nada.
  assert.equal(resumenDeSerie(SERIE.puntos, 'Guanajuato', '2026-01-Q1').quincena, '2026-07-Q2')
  assert.equal(resumenDeSerie(SERIE.puntos, 'Colima').punto, null)
  assert.deepEqual(entidadesDeLaSerie(SERIE.puntos), ['Guanajuato', 'Jalisco'])
})
