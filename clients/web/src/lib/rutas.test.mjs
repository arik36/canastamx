// npm test · el rol decide la vista, y la URL escrita a mano no la salta (T047, P-07).
import assert from 'node:assert/strict'
import { test } from 'node:test'

import { decidir, destinoPorRol, rolQuePide } from './rutas.mjs'

test('el analista abre el tablero y el operador la consola', () => {
  assert.equal(destinoPorRol('ANALISTA'), '/tablero')
  assert.equal(destinoPorRol('OPERADOR'), '/consola')
})

test('una cuenta de la app, o un rol que no existe, no tiene vista en la web', () => {
  for (const rol of ['CONSUMIDOR', 'ADMIN', '', undefined, '__proto__', 'constructor']) {
    assert.equal(destinoPorRol(rol), null, String(rol))
  }
})

test('cada una de las cuatro vistas con sesión pide su rol', () => {
  assert.equal(rolQuePide('/tablero'), 'ANALISTA')
  assert.equal(rolQuePide('/detalle'), 'ANALISTA')
  assert.equal(rolQuePide('/consola'), 'OPERADOR')
  assert.equal(rolQuePide('/cola'), 'OPERADOR')
  assert.equal(rolQuePide('/acceso'), null)
  assert.equal(rolQuePide('/tableros'), null)
})

test('sin sesión, toda vista manda al acceso', () => {
  for (const ruta of ['/tablero', '/detalle', '/consola', '/cola', '/']) {
    assert.deepEqual(decidir(ruta, undefined), { redirigeA: '/acceso' }, ruta)
  }
  assert.deepEqual(decidir('/acceso', undefined), { pasa: true })
})

test('el analista que escribe a mano una vista del operador vuelve al tablero', () => {
  assert.deepEqual(decidir('/consola', 'ANALISTA'), { redirigeA: '/tablero' })
  assert.deepEqual(decidir('/cola', 'ANALISTA'), { redirigeA: '/tablero' })
  assert.deepEqual(decidir('/tablero', 'ANALISTA'), { pasa: true })
  assert.deepEqual(decidir('/detalle', 'ANALISTA'), { pasa: true })
})

test('el operador que escribe a mano una vista del analista vuelve a la consola', () => {
  assert.deepEqual(decidir('/tablero', 'OPERADOR'), { redirigeA: '/consola' })
  assert.deepEqual(decidir('/detalle', 'OPERADOR'), { redirigeA: '/consola' })
  assert.deepEqual(decidir('/consola', 'OPERADOR'), { pasa: true })
  assert.deepEqual(decidir('/cola', 'OPERADOR'), { pasa: true })
})

test('con sesión, el acceso manda a la vista del rol', () => {
  assert.deepEqual(decidir('/acceso', 'ANALISTA'), { redirigeA: '/tablero' })
  assert.deepEqual(decidir('/acceso', 'OPERADOR'), { redirigeA: '/consola' })
})

test('una cookie de rol desconocido cuenta como sin sesión', () => {
  assert.deepEqual(decidir('/consola', 'CONSUMIDOR'), { redirigeA: '/acceso' })
  assert.deepEqual(decidir('/acceso', 'CONSUMIDOR'), { pasa: true })
})

test('las rutas internas y de la API pasan sin revisar', () => {
  for (const ruta of ['/api/login', '/api/salir', '/_next/static/x.js', '/favicon.ico']) {
    assert.deepEqual(decidir(ruta, undefined), { pasa: true }, ruta)
  }
})
