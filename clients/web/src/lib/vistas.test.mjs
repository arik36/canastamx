// npm test · revisión estática de las vistas: que existan las cinco rutas, que cada vista
// pida su rol al dominio y que el aviso de ancho mínimo siga en 1025 px (D-08). No
// sustituye abrirlas en el navegador a 1024 y 1025 px (README, «Cómo se comprueba»).
import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import { test } from 'node:test'

const src = new URL('..', import.meta.url)
const leer = (ruta) => readFileSync(new URL(ruta, src), 'utf8')

const VISTAS_CON_SESION = { tablero: 'ANALISTA', detalle: 'ANALISTA', consola: 'OPERADOR', cola: 'OPERADOR' }

test('existen las cinco rutas de la web: acceso, tablero, detalle, consola y cola', () => {
  for (const vista of ['acceso', ...Object.keys(VISTAS_CON_SESION)]) {
    assert.ok(existsSync(new URL(`app/${vista}/page.tsx`, src)), vista)
  }
})

test('cada vista con sesión pide al dominio la cuenta de su rol antes de mostrarse', () => {
  for (const [vista, rol] of Object.entries(VISTAS_CON_SESION)) {
    const pagina = leer(`app/${vista}/page.tsx`)
    assert.match(pagina, new RegExp(`await exigirCuenta\\('${rol}'\\)`), vista)
    assert.match(pagina, /<Sidebar cuenta=\{cuenta\} \/>/, vista)
  }
})

test('las consolas conservan 1025 px y avisan por debajo de ese ancho (D-08)', () => {
  // lg:hidden oculta el aviso desde --breakpoint-lg; Tailwind lo trae en 1024 px, por
  // eso globals.css lo sube a 1025: a 1024 px el aviso aparece y a 1025 no.
  assert.match(leer('app/globals.css'), /--breakpoint-lg:\s*1025px/)
  for (const vista of Object.keys(VISTAS_CON_SESION)) {
    const pagina = leer(`app/${vista}/page.tsx`)
    assert.match(pagina, /overflow-x-auto/, vista)
    assert.match(pagina, /min-w-\[1025px\]/, vista)
    assert.match(pagina, /lg:hidden[^"]*">\s*⚠️ Pantalla pequeña/, vista)
  }
})

test('la barra lateral toma el correo y el rol de la cuenta, no de cookies ni de un nombre', () => {
  const barra = leer('components/Sidebar.tsx')
  assert.doesNotMatch(barra, /cookies\(/)
  assert.doesNotMatch(barra, /Ruiz|\{nombre\}|\.nombre\b/)
  assert.match(barra, /\{correo\}/)
  assert.match(barra, /\{rol\}/)
})
