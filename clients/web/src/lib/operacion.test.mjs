// npm test · lo que la consola le pide a la analítica y lo que hace con la respuesta
// (analitica.yaml 0.2.1: las seis rutas con x-rol OPERADOR). Un fetch falso guarda cada
// petición.
import assert from 'node:assert/strict'
import { test } from 'node:test'

import {
  CAUSAS,
  LARGO_DE_LA_DECISION,
  LOTE,
  cerrarIncidente,
  duracion,
  estadoGeneral,
  fechaYHora,
  leerCierre,
  leerCorridas,
  leerCuarentena,
  leerEstado,
  leerIncidentes,
  leerLinaje,
  nivelDeCorrida,
  nivelDeFrescura,
  porCerrar,
  porcentaje,
  textoDeFila,
  textoDeFrescura,
} from './operacion.mjs'

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
const con = (fetch) => ({ analiticaUrl: ANALITICA, fetch })

// Como responde la interfaz de T069 con los datos de A (t069, 13 de noviembre).
const CORRIDA = {
  lote: '07-2026_Q2', fecha: '2026-11-10T18:04:11.520000Z', resultado: 'CORRECTA',
  filasLeidas: 70412, filasAceptadas: 70385, filasEnCuarentena: 27, duracionSegundos: 41.8,
}
const ESTADO = {
  ultimoDato: '2026-07-Q2',
  frescura: { estado: 'NO_APLICA', dias: 10 },
  ultimaCorrida: CORRIDA,
  filasProcesadas: 2658906,
  cuarentena: { filas: 1089, porcentaje: 0.041, poblacion: 'lotes vigentes del alcance' },
  avisosDeEsquema: 2,
  incidentesAbiertos: 0,
}
const AVISO = {
  id: '2', severidad: 'AVISO', lote: '03-2026_Q1', compuerta: 'columnas_extra', motivo: 'columnas_extra',
  filas: 0, estado: 'INFORMATIVO', abiertoEn: '2026-11-09T17:00:00Z', cerradoEn: null, cerradoPor: null,
  causa: null, decision: null, reprocesarLote: false,
}
const ABIERTO = {
  ...AVISO, id: '7', severidad: 'INCIDENTE', lote: '07-2026_Q2', compuerta: 'promocion_del_lote',
  motivo: 'rechazo_mayor_al_umbral', filas: 4120, estado: 'ABIERTO',
}
const CERRADO = {
  ...ABIERTO, id: '5', estado: 'CERRADO', cerradoEn: '2026-11-13T19:10:00Z', cerradoPor: 'operador@canastamx.mx',
  causa: 'ARCHIVO_DE_LA_FUENTE', decision: 'Se reprocesa cuando PROFECO corrija el archivo.', reprocesarLote: true,
}
const FILA = {
  lote: '07-2026_Q2', motivo: 'precio_fuera_de_rango', compuerta: 'columnas',
  fila: { producto: 'HUEVO', presentacion: 'PAQUETE C/30', precio: '9999', estado: 'GUANAJUATO' },
}

test('cada lectura pide su ruta con GET y el token de la sesión', async () => {
  const casos = [
    [(d) => leerEstado('tk', d), '/api/v1/operacion/estado', ESTADO],
    [(d) => leerCorridas('tk', { limit: 10 }, d), '/api/v1/operacion/corridas?limit=10', { corridas: [], total: 0 }],
    [(d) => leerLinaje('tk', '07-2026_Q2', d), '/api/v1/operacion/corridas/07-2026_Q2', { lote: '07-2026_Q2', corridas: [CORRIDA] }],
    [(d) => leerCuarentena('tk', { lote: '07-2026_Q2', limit: 10 }, d),
      '/api/v1/operacion/cuarentena?lote=07-2026_Q2&limit=10', { filas: [], total: 0 }],
    [(d) => leerCuarentena('tk', {}, d), '/api/v1/operacion/cuarentena?limit=10', { filas: [], total: 0 }],
    [(d) => leerIncidentes('tk', { estado: 'ABIERTO', severidad: 'INCIDENTE', limit: 100 }, d),
      '/api/v1/operacion/incidentes?estado=ABIERTO&severidad=INCIDENTE&limit=100', { incidentes: [], total: 0 }],
    [(d) => leerIncidentes('tk', {}, d), '/api/v1/operacion/incidentes?limit=20', { incidentes: [], total: 0 }],
  ]
  for (const [leer, ruta, cuerpo] of casos) {
    const { fetch, peticiones } = fetchFalso(200, cuerpo)
    const r = await leer(con(fetch))
    assert.equal(r.estado, 'ok', ruta)
    assert.equal(peticiones.length, 1)
    assert.equal(peticiones[0].url, `${ANALITICA}${ruta}`)
    assert.equal(peticiones[0].method, 'GET')
    assert.equal(peticiones[0].headers.Authorization, 'Bearer tk')
    assert.equal(peticiones[0].body, undefined)
  }
})

test('un lote raro no se cuela en la ruta del linaje', async () => {
  const { fetch, peticiones } = fetchFalso(404, { status: 404, detail: 'No hay corridas de ese lote.' })
  await leerLinaje('tk', '../estado?x=1', con(fetch))
  assert.equal(peticiones[0].url, `${ANALITICA}/api/v1/operacion/corridas/..%2Festado%3Fx%3D1`)
  assert.ok(LOTE.test('07-2026_Q2') && LOTE.test('01-2025_01'))
  assert.ok(!LOTE.test('../estado') && !LOTE.test('2026-07-Q2'))
})

test('los seis indicadores pasan tal como los da la analítica, aunque omita lo que es null', async () => {
  const r = await leerEstado('tk', con(fetchFalso(200, ESTADO).fetch))
  assert.deepEqual(r, { estado: 'ok', indicadores: ESTADO })

  // Con response_model_exclude_none la interfaz real no manda ultimoDato, dias ni duración.
  const recortado = { ...ESTADO, frescura: { estado: 'NO_APLICA' }, ultimaCorrida: { ...CORRIDA } }
  delete recortado.ultimoDato
  delete recortado.ultimaCorrida.duracionSegundos
  assert.equal((await leerEstado('tk', con(fetchFalso(200, recortado).fetch))).estado, 'ok')
})

test('sin corridas, la consola lo dice en lugar de mostrar ceros (CU-05 · 2b)', async () => {
  const problema = { type: '/problemas/sin-datos', title: 'Sin datos', status: 404,
    detail: 'Todavía no hay ninguna corrida registrada.' }
  const r = await leerEstado('tk', con(fetchFalso(404, problema).fetch))
  assert.deepEqual(r, { estado: 'sin-corridas', motivo: 'respondió 404: Todavía no hay ninguna corrida registrada' })
})

test('un estado sin la forma del contrato es un aviso, no una vista rota', async () => {
  const casos = [
    { ...ESTADO, frescura: undefined },
    { ...ESTADO, frescura: { estado: 'AL_DIA' } },
    { ...ESTADO, ultimaCorrida: { ...CORRIDA, resultado: 'EXITOSA' } },
    { ...ESTADO, ultimaCorrida: { ...CORRIDA, fecha: 'ayer' } },
    { ...ESTADO, ultimaCorrida: { ...CORRIDA, filasLeidas: '70412' } },
    { ...ESTADO, filasProcesadas: -1 },
    { ...ESTADO, cuarentena: { filas: 1089, porcentaje: '0.041', poblacion: 'lotes vigentes del alcance' } },
    { ...ESTADO, cuarentena: { filas: 1089, porcentaje: 0.041 } },                     // sin población (RNF-16)
    { ...ESTADO, avisosDeEsquema: undefined },
    { ...ESTADO, incidentesAbiertos: 1.5 },
    { ...ESTADO, ultimoDato: '07-2026_Q2' },
    null,
  ]
  for (const cuerpo of casos) {
    const r = await leerEstado('tk', con(fetchFalso(200, cuerpo).fetch))
    assert.deepEqual(r, { estado: 'error', motivo: 'respondió 200 sin la forma de estadoDeLaPlataforma' },
      JSON.stringify(cuerpo))
  }
})

test('los incidentes y los avisos se aceptan con sus campos nulos, y no sin los obligatorios', async () => {
  const lista = { incidentes: [CERRADO, ABIERTO, AVISO], total: 3 }
  assert.deepEqual(await leerIncidentes('tk', {}, con(fetchFalso(200, lista).fetch)),
    { estado: 'ok', incidentes: lista.incidentes, total: 3 })

  const malos = [
    { ...ABIERTO, id: 7 },
    { ...ABIERTO, severidad: 'CRITICO' },
    { ...ABIERTO, estado: 'RESUELTO' },
    { ...ABIERTO, filas: undefined },
    { ...ABIERTO, abiertoEn: undefined },
    { ...ABIERTO, compuerta: null },
    { ...CERRADO, cerradoEn: 'el martes' },
    { ...CERRADO, reprocesarLote: 'si' },
  ]
  for (const incidente of malos) {
    const r = await leerIncidentes('tk', {}, con(fetchFalso(200, { incidentes: [incidente], total: 1 }).fetch))
    assert.deepEqual(r, { estado: 'error', motivo: 'respondió 200 sin la forma de listarIncidentes' },
      JSON.stringify(incidente))
  }
  const sinTotal = await leerIncidentes('tk', {}, con(fetchFalso(200, { incidentes: [] }).fetch))
  assert.equal(sinTotal.estado, 'error')
})

test('las corridas, el linaje y la cuarentena revisan su forma', async () => {
  const corridas = await leerCorridas('tk', { limit: 10 }, con(fetchFalso(200, { corridas: [CORRIDA], total: 38 }).fetch))
  assert.deepEqual(corridas, { estado: 'ok', corridas: [CORRIDA], total: 38 })

  const reprocesado = [{ ...CORRIDA, resultado: 'RECHAZADA', filasAceptadas: 0 }, CORRIDA]
  const linaje = await leerLinaje('tk', '07-2026_Q2', con(fetchFalso(200, { lote: '07-2026_Q2', corridas: reprocesado }).fetch))
  assert.deepEqual(linaje, { estado: 'ok', lote: '07-2026_Q2', corridas: reprocesado })

  const cuarentena = await leerCuarentena('tk', {}, con(fetchFalso(200, { filas: [FILA], total: 1089 }).fetch))
  assert.deepEqual(cuarentena, { estado: 'ok', filas: [FILA], total: 1089 })

  const malos = [
    [(d) => leerCorridas('tk', {}, d), { corridas: [{ ...CORRIDA, lote: undefined }], total: 1 }, 'listarCorridas'],
    [(d) => leerCorridas('tk', {}, d), { corridas: [CORRIDA] }, 'listarCorridas'],
    [(d) => leerLinaje('tk', '07-2026_Q2', d), { lote: '07-2026_Q2', corridas: [] }, 'linajeDeLote'],
    [(d) => leerLinaje('tk', '07-2026_Q2', d), { corridas: [CORRIDA] }, 'linajeDeLote'],
    [(d) => leerCuarentena('tk', {}, d), { filas: [{ ...FILA, fila: 'HUEVO,9999' }], total: 1 }, 'listarCuarentena'],
    [(d) => leerCuarentena('tk', {}, d), { filas: [{ ...FILA, fila: null }], total: 1 }, 'listarCuarentena'],
    [(d) => leerCuarentena('tk', {}, d), { filas: [{ ...FILA, motivo: undefined }], total: 1 }, 'listarCuarentena'],
  ]
  for (const [leer, cuerpo, operacion] of malos) {
    const r = await leer(con(fetchFalso(200, cuerpo).fetch))
    assert.deepEqual(r, { estado: 'error', motivo: `respondió 200 sin la forma de ${operacion}` }, JSON.stringify(cuerpo))
  }
})

test('el cierre hace POST con la causa, la decisión y el reproceso, y nada de quién ni cuándo', async () => {
  const cerrado = { ...ABIERTO, estado: 'CERRADO', cerradoEn: '2026-11-22T20:00:00Z',
    cerradoPor: 'operador@canastamx.mx', causa: 'DATO_REAL_ATIPICO', decision: 'Se acepta.' }
  const { fetch, peticiones } = fetchFalso(200, cerrado)
  const cierre = { causa: 'DATO_REAL_ATIPICO', decision: 'Se acepta.', reprocesarLote: false }
  const r = await cerrarIncidente('token-del-operador', '7', cierre, con(fetch))

  assert.deepEqual(r, { estado: 'ok', incidente: cerrado })
  assert.equal(peticiones.length, 1)
  assert.equal(peticiones[0].url, `${ANALITICA}/api/v1/operacion/incidentes/7/cierre`)
  assert.equal(peticiones[0].method, 'POST')
  assert.equal(peticiones[0].headers.Authorization, 'Bearer token-del-operador')
  assert.equal(peticiones[0].headers['Content-Type'], 'application/json')
  assert.deepEqual(JSON.parse(peticiones[0].body), cierre)     // ni cerradoPor ni cerradoEn (D-11)
})

test('cada falla del cierre da su motivo, y ninguno lleva el token', async () => {
  const problema = (status, detail) => ({ type: 'about:blank', title: 'Problema', status, detail })
  const cierre = { causa: 'INFRAESTRUCTURA', decision: 'Se asignó a B.', reprocesarLote: false }
  const casos = [
    [fetchFalso(409, problema(409, 'Es un aviso: los avisos informan y no se cierran (RF-13).')).fetch,
      'respondió 409: Es un aviso: los avisos informan y no se cierran (RF-13)'],
    [fetchFalso(409, problema(409, 'El incidente ya estaba cerrado.')).fetch,
      'respondió 409: El incidente ya estaba cerrado'],
    [fetchFalso(503, problema(503, 'No se pudo preguntar al dominio de quién es la sesión. El incidente no se cerró.')).fetch,
      'respondió 503: No se pudo preguntar al dominio de quién es la sesión. El incidente no se cerró'],
    [fetchFalso(401, problema(401, 'Esta ruta pide una sesión con el rol OPERADOR.')).fetch,
      'respondió 401: Esta ruta pide una sesión con el rol OPERADOR'],
    [fetchFalso(500).fetch, 'respondió 500'],
    [fetchFalso(200, { id: '7' }).fetch, 'respondió 200 sin la forma de cerrarIncidente'],
    [fetchCaido, 'no contestó'],
  ]
  for (const [fetch, motivo] of casos) {
    const r = await cerrarIncidente('token-secreto', '7', cierre, con(fetch))
    assert.deepEqual(r, { estado: 'error', motivo })
    assert.doesNotMatch(r.motivo, /token-secreto/)
  }
})

test('cada falla de una lectura da su motivo, y ninguno lleva el token', async () => {
  const casos = [
    [fetchFalso(401, { status: 401, detail: 'La sesión no es válida o ya venció.' }).fetch,
      'respondió 401: La sesión no es válida o ya venció'],
    [fetchFalso(500).fetch, 'respondió 500'],
    [fetchCaido, 'no contestó'],
  ]
  for (const [fetch, motivo] of casos) {
    for (const leer of [leerEstado, (t, d) => leerCorridas(t, {}, d), (t, d) => leerIncidentes(t, {}, d),
      (t, d) => leerCuarentena(t, {}, d), (t, d) => leerLinaje(t, '07-2026_Q2', d)]) {
      const r = await leer('token-secreto', con(fetch))
      assert.deepEqual(r, { estado: 'error', motivo })
    }
  }
})

test('el formulario de cierre se revisa antes de mandarlo', () => {
  const formulario = (campos) => {
    const datos = new FormData()
    for (const [clave, valor] of Object.entries(campos)) datos.append(clave, valor)
    return datos
  }
  const bueno = { incidenteId: '7', causa: 'ARCHIVO_DE_LA_FUENTE', decision: '  Se reprocesa.  ', reprocesarLote: 'si' }

  assert.deepEqual(leerCierre(formulario(bueno)), {
    estado: 'ok', id: '7', cierre: { causa: 'ARCHIVO_DE_LA_FUENTE', decision: 'Se reprocesa.', reprocesarLote: true },
  })
  const sinReproceso = { ...bueno }
  delete sinReproceso.reprocesarLote
  assert.equal(leerCierre(formulario(sinReproceso)).cierre.reprocesarLote, false)

  for (const malo of [
    { ...bueno, incidenteId: '' },
    { ...bueno, incidenteId: '7/../../estado' },
    { ...bueno, causa: '' },
    { ...bueno, causa: 'CULPA_DE_ALGUIEN' },
    { ...bueno, causa: 'toString' },
    { ...bueno, decision: '   ' },
    { ...bueno, decision: 'x'.repeat(LARGO_DE_LA_DECISION + 1) },
  ]) {
    assert.equal(leerCierre(formulario(malo)).estado, 'error', JSON.stringify(malo).slice(0, 80))
  }
  assert.deepEqual(Object.keys(CAUSAS),
    ['ARCHIVO_DE_LA_FUENTE', 'REGLA_DEL_CONTRATO', 'DATO_REAL_ATIPICO', 'INFRAESTRUCTURA'])
})

test('la respuesta de los tres segundos: lo rojo gana, y los avisos de esquema no la pintan de azul', () => {
  const conCambios = (cambios) => ({ ...ESTADO, ...cambios })   // ESTADO ya trae 2 avisos de esquema
  assert.deepEqual(estadoGeneral(ESTADO),
    { nivel: 'ok', titulo: 'La última corrida fue correcta y no hay incidentes abiertos' })
  assert.deepEqual(estadoGeneral(conCambios({ incidentesAbiertos: 1 })), { nivel: 'incidente', titulo: 'Hay 1 incidente abierto' })
  assert.deepEqual(estadoGeneral(conCambios({ incidentesAbiertos: 3 })), { nivel: 'incidente', titulo: 'Hay 3 incidentes abiertos' })
  assert.equal(estadoGeneral(conCambios({ ultimaCorrida: { ...CORRIDA, resultado: 'RECHAZADA' } })).nivel, 'incidente')
  assert.equal(estadoGeneral(conCambios({ ultimaCorrida: { ...CORRIDA, resultado: 'FALLIDA' } })).nivel, 'incidente')
  assert.equal(estadoGeneral(conCambios({ frescura: { estado: 'BLOQUEA', dias: 50 } })).nivel, 'incidente')
  assert.equal(estadoGeneral(conCambios({ ultimaCorrida: { ...CORRIDA, resultado: 'CON_AVISOS' } })).nivel, 'aviso')
  assert.equal(estadoGeneral(conCambios({ frescura: { estado: 'AVISA', dias: 25 } })).nivel, 'aviso')
  assert.equal(estadoGeneral(conCambios({ incidentesAbiertos: 1, ultimaCorrida: { ...CORRIDA, resultado: 'CON_AVISOS' } })).nivel,
    'incidente')
})

test('sólo un incidente abierto se puede cerrar; un aviso nunca, aunque venga abierto', () => {
  const avisoAbierto = { ...AVISO, estado: 'ABIERTO' }        // así lo devuelve el simulador
  assert.deepEqual(porCerrar([ABIERTO, AVISO, avisoAbierto, CERRADO]), [ABIERTO])
  assert.deepEqual(porCerrar([]), [])
})

test('el semáforo: verde, azul, rojo y gris; nunca otro color', () => {
  assert.deepEqual(['CORRECTA', 'CON_AVISOS', 'RECHAZADA', 'FALLIDA'].map(nivelDeCorrida),
    ['ok', 'aviso', 'incidente', 'incidente'])
  assert.deepEqual(['OK', 'AVISA', 'BLOQUEA', 'NO_APLICA'].map(nivelDeFrescura),
    ['ok', 'aviso', 'incidente', 'no-aplica'])
})

test('las cifras se leen como las calcula la analítica', () => {
  // La cuarentena ya viene en por ciento: 0.041 es 0.041%, no 4.1%.
  assert.equal(porcentaje(0.041), '0.041%')
  assert.equal(porcentaje(0.23), '0.23%')
  assert.equal(porcentaje(0), '0%')
  // En la hora del centro de México, aunque el servidor esté en UTC.
  assert.equal(fechaYHora('2026-11-12T16:32:05Z'), '12 nov 2026, 10:32')
  assert.equal(duracion(41.8), '42 s')
  assert.equal(duracion(185), '3 min 5 s')
  assert.equal(duracion(60.2), '1 min')
  assert.equal(duracion(undefined), '—')
  assert.equal(textoDeFrescura({ estado: 'NO_APLICA', dias: 10 }, '2026-07-Q2'),
    'La regla no corre mientras la fuente no publique: el corpus está congelado.')
  assert.equal(textoDeFrescura({ estado: 'AVISA', dias: 25 }, '2026-07-Q2'),
    '25 días del último registro a la última corrida.')
  assert.equal(textoDeFila({ producto: 'HUEVO', precio: '9999', marca: null }),
    'producto: HUEVO · precio: 9999 · marca: (vacío)')
})
