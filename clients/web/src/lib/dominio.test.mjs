// npm test · lo que la web le pide al dominio y lo que hace con la respuesta
// (dominio.yaml 0.2.2: Credenciales, Sesion y Cuenta). Un fetch falso guarda cada petición.
import assert from 'node:assert/strict'
import { test } from 'node:test'

import { iniciarSesion, leerCuenta, urlDelDominio } from './dominio.mjs'

const DOMINIO = 'http://dominio.prueba'

function fetchFalso(estado, cuerpo) {
  const peticiones = []
  const fetch = async (url, opciones = {}) => {
    peticiones.push({ url, ...opciones })
    return new Response(cuerpo === undefined ? null : JSON.stringify(cuerpo), { status: estado })
  }
  return { fetch, peticiones }
}

const fetchCaido = async () => { throw new TypeError('fetch failed') }

const enUnaHora = () => new Date(Date.now() + 3600e3).toISOString()

test('el acceso hace POST /api/v1/sesiones con correo y contrasena, nada más', async () => {
  const { fetch, peticiones } = fetchFalso(200, { token: 't', expiraEn: enUnaHora(), rol: 'ANALISTA' })
  await iniciarSesion({ correo: 'a@b.mx', contrasena: 'Secreta123' }, { dominioUrl: DOMINIO, fetch })

  assert.equal(peticiones.length, 1)
  assert.equal(peticiones[0].url, `${DOMINIO}/api/v1/sesiones`)
  assert.equal(peticiones[0].method, 'POST')
  assert.equal(peticiones[0].headers['Content-Type'], 'application/json')
  assert.deepEqual(JSON.parse(peticiones[0].body), { correo: 'a@b.mx', contrasena: 'Secreta123' })
})

test('con la sesión del analista o del operador entra, y conserva el vencimiento', async () => {
  for (const rol of ['ANALISTA', 'OPERADOR']) {
    const expiraEn = enUnaHora()
    const { fetch } = fetchFalso(200, { token: 'token-' + rol, expiraEn, rol })
    const r = await iniciarSesion({ correo: 'a@b.mx', contrasena: 'x' }, { dominioUrl: DOMINIO, fetch })
    assert.equal(r.estado, 200, rol)
    assert.deepEqual(r.sesion, { token: 'token-' + rol, expiraEn: new Date(expiraEn), rol })
  }
})

test('una cuenta CONSUMIDOR no entra a la web', async () => {
  const { fetch } = fetchFalso(200, { token: 't', expiraEn: enUnaHora(), rol: 'CONSUMIDOR' })
  const r = await iniciarSesion({ correo: 'a@b.mx', contrasena: 'x' }, { dominioUrl: DOMINIO, fetch })
  assert.equal(r.estado, 403)
  assert.equal(r.sesion, undefined)
})

test('cada falla del dominio da su propio mensaje', async () => {
  const casos = [
    [fetchFalso(401, { title: 'Credenciales inválidas', status: 401 }).fetch, 401],
    [fetchFalso(500, { title: 'Error', status: 500 }).fetch, 502],
    [fetchFalso(200, { token: 't', rol: 'ANALISTA' }).fetch, 502],                          // sin expiraEn
    [fetchFalso(200, { expiraEn: enUnaHora(), rol: 'ANALISTA' }).fetch, 502],                // sin token
    [fetchFalso(200, { token: 't', expiraEn: enUnaHora(), rol: 'ADMIN' }).fetch, 502],       // rol que no existe
    [fetchCaido, 503],
  ]
  for (const [fetch, esperado] of casos) {
    const r = await iniciarSesion({ correo: 'a@b.mx', contrasena: 'x' }, { dominioUrl: DOMINIO, fetch })
    assert.equal(r.estado, esperado)
    assert.equal(typeof r.error, 'string')
    assert.equal(r.sesion, undefined)
  }
})

test('la cuenta se pide a GET /api/v1/cuentas/yo con el token Bearer (D-10)', async () => {
  const { fetch, peticiones } = fetchFalso(200, {
    id: 'u1', correo: 'analista@canastamx.mx', rol: 'ANALISTA', fechaDeRegistro: '2026-10-23T12:00:00Z',
  })
  const r = await leerCuenta('token-1', { dominioUrl: DOMINIO, fetch })

  assert.equal(peticiones[0].url, `${DOMINIO}/api/v1/cuentas/yo`)
  assert.equal(peticiones[0].method, undefined)   // GET
  assert.equal(peticiones[0].headers.Authorization, 'Bearer token-1')
  // Sólo correo y rol: la barra lateral nunca muestra un nombre (P-13).
  assert.deepEqual(r, { estado: 'ok', cuenta: { correo: 'analista@canastamx.mx', rol: 'ANALISTA' } })
})

test('un token que el dominio rechaza, o de una cuenta de la app, es «sin sesión»', async () => {
  assert.deepEqual(await leerCuenta('t', { dominioUrl: DOMINIO, fetch: fetchFalso(401, { status: 401 }).fetch }),
    { estado: 'sin-sesion' })
  assert.deepEqual(await leerCuenta('t', { dominioUrl: DOMINIO,
    fetch: fetchFalso(200, { id: 'u', correo: 'c@b.mx', rol: 'CONSUMIDOR', fechaDeRegistro: 'x' }).fetch }),
  { estado: 'sin-sesion' })
})

test('si el dominio no responde bien, no se inventa una cuenta', async () => {
  for (const fetch of [fetchFalso(503, { status: 503 }).fetch, fetchFalso(200, { id: 'u' }).fetch, fetchCaido]) {
    assert.deepEqual(await leerCuenta('t', { dominioUrl: DOMINIO, fetch }), { estado: 'error' })
  }
})

test('sin DOMINIO_URL se usa el dominio de desarrollo, y la diagonal final no estorba', () => {
  assert.equal(urlDelDominio({}), 'http://localhost:8081')
  assert.equal(urlDelDominio({ DOMINIO_URL: 'http://127.0.0.1:4010/' }), 'http://127.0.0.1:4010')
})
