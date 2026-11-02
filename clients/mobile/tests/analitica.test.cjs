const assert = require('node:assert/strict');
const test = require('node:test');
const ts = require('typescript');
const fs = require('node:fs');
require.extensions['.ts'] = (mod, filename) => mod._compile(ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText, filename);
const { buscarArticulos, validarBusqueda, ErrorAnalitica } = require('../api/analitica.ts');
const { articulos, entidadesCubiertas } = require('../mocks/escenarios.cjs');
const datos = { cobertura: true, entidad: 'Guanajuato', quincena: '2026-07-Q2', total: 1, resultados: [articulos[0]] };
const criterios = { q: 'leche', entidad: 'Guanajuato' };
function configurar(t) {
  const anterior = process.env.EXPO_PUBLIC_ANALITICA_URL;
  process.env.EXPO_PUBLIC_ANALITICA_URL = 'http://analitica.invalid:4011/';
  t.after(() => { if (anterior === undefined) delete process.env.EXPO_PUBLIC_ANALITICA_URL; else process.env.EXPO_PUBLIC_ANALITICA_URL = anterior; });
}
test('usa la URL analítica, codifica criterios y no envía el token del dominio', async t => {
  configurar(t);
  let llamada;
  t.mock.method(global, 'fetch', async (url, opciones) => { llamada = { url, opciones }; return Response.json(datos); });
  const resultado = await buscarArticulos({ q: ' leche & arroz ', entidad: 'San Luis Potosí', offset: 20 });
  const url = new URL(llamada.url);
  assert.equal(url.origin, 'http://analitica.invalid:4011');
  assert.equal(url.pathname, '/api/v1/articulos');
  assert.equal(url.searchParams.get('q'), 'leche & arroz');
  assert.equal(url.searchParams.get('entidad'), 'San Luis Potosí');
  assert.equal(url.searchParams.get('limit'), '20');
  assert.equal(url.searchParams.get('offset'), '20');
  assert.equal(llamada.opciones.headers.Authorization, undefined);
  assert.equal(resultado.simulador, true);
  assert.equal(resultado.datos.resultados[0].precioTipico.monto, '28.50');
});
test('200 con lista vacía es el alterno 2a y conserva quincena', async t => {
  configurar(t);
  t.mock.method(global, 'fetch', async () => Response.json({ ...datos, total: 0, resultados: [] }));
  const respuesta = await buscarArticulos(criterios);
  assert.equal(respuesta.datos.cobertura, true);
  assert.equal(respuesta.datos.total, 0);
  assert.equal(respuesta.datos.quincena, '2026-07-Q2');
});
test('200 sin cobertura es el alterno 2b aunque no tenga resultados ni quincena', async t => {
  configurar(t);
  t.mock.method(global, 'fetch', async () => Response.json({ cobertura: false, entidad: 'Colima', entidadesCubiertas }));
  const respuesta = await buscarArticulos({ ...criterios, entidad: 'Colima' });
  assert.equal(respuesta.datos.cobertura, false);
  assert.equal(respuesta.datos.entidadesCubiertas.length, 7);
});
test('una respuesta incompleta no se confunde con ausencia de resultados', () => {
  for (const invalido of [
    { cobertura: true, entidad: 'Guanajuato' },
    { ...datos, quincena: '2026-13-Q3' },
    { ...datos, resultados: [{ ...articulos[0], observaciones: undefined }] },
    { ...datos, resultados: [{ ...articulos[0], observaciones: 0 }] },
    { cobertura: false, entidad: 'Colima' },
  ]) assert.throws(() => validarBusqueda(invalido), ErrorAnalitica);
});
test('rechaza dinero flotante, moneda ajena y artículo sin presentación', () => {
  for (const item of [
    { ...articulos[0], precioTipico: { monto: 28.5, moneda: 'MXN' } },
    { ...articulos[0], precioTipico: { monto: '28.50', moneda: 'USD' } },
    { ...articulos[0], articulo: { producto: 'leche' } },
  ]) assert.throws(() => validarBusqueda({ ...datos, resultados: [item] }), ErrorAnalitica);
});
test('preserva title, detail, type, instance y status de problem+json', async t => {
  configurar(t);
  const problema = { type: 'urn:prueba:invalido', title: 'Consulta inválida', detail: 'La entidad no es válida.', status: 400, instance: '/api/v1/articulos' };
  t.mock.method(global, 'fetch', async () => Response.json(problema, { status: 400, headers: { 'content-type': 'application/problem+json; charset=utf-8' } }));
  await assert.rejects(buscarArticulos(criterios), error => { assert.deepEqual(error.problema, problema); return true; });
});
test('un error no JSON se muestra como error HTTP', async t => {
  configurar(t);
  t.mock.method(global, 'fetch', async () => new Response('<html>fallo</html>', { status: 502, headers: { 'content-type': 'text/html' } }));
  await assert.rejects(buscarArticulos(criterios), /HTTP 502/);
});
test('JSON ilegible y red caída terminan con errores explicados', async t => {
  configurar(t);
  const reemplazo = t.mock.method(global, 'fetch', async () => new Response('no es JSON'));
  await assert.rejects(buscarArticulos(criterios), /no podemos leer/);
  reemplazo.mock.mockImplementation(async () => { throw new TypeError('Network request failed'); });
  await assert.rejects(buscarArticulos(criterios), /No hay conexión/);
});
test('corta la espera a los ocho segundos', async t => {
  configurar(t);
  t.mock.timers.enable({ apis: ['setTimeout'] });
  t.mock.method(global, 'fetch', async (_, opciones) => new Promise((_, reject) => { opciones.signal.addEventListener('abort', () => reject(new Error('Abortado'))); }));
  const pendiente = buscarArticulos(criterios);
  t.mock.timers.tick(8000);
  await assert.rejects(pendiente, /8 segundos/);
});
test('propaga la cancelación al editar criterios o desmontar la pantalla', async t => {
  configurar(t);
  const controller = new AbortController();
  t.mock.method(global, 'fetch', async (_, opciones) => new Promise((_, reject) => { opciones.signal.addEventListener('abort', () => reject(new Error('Cancelación externa'))); }));
  const pendiente = buscarArticulos(criterios, controller.signal);
  controller.abort();
  await assert.rejects(pendiente, /Cancelación externa/);
});
test('criterios o URL inválidos no hacen solicitudes', async t => {
  configurar(t);
  const fetch = t.mock.method(global, 'fetch', async () => { throw new Error('No se debía llamar'); });
  await assert.rejects(buscarArticulos({ q: 'a', entidad: 'Guanajuato' }), /dos caracteres/);
  await assert.rejects(buscarArticulos({ ...criterios, entidad: '' }), /selecciona una entidad/);
  await assert.rejects(buscarArticulos({ ...criterios, offset: -1 }), /página/);
  delete process.env.EXPO_PUBLIC_ANALITICA_URL;
  await assert.rejects(buscarArticulos(criterios), /configurar/);
  assert.equal(fetch.mock.callCount(), 0);
});
test('apuntar a la analítica real requiere sólo cambiar su URL', async t => {
  configurar(t);
  process.env.EXPO_PUBLIC_ANALITICA_URL = 'http://analitica-real.invalid:8000';
  t.mock.method(global, 'fetch', async url => { assert.match(url, /^http:\/\/analitica-real.invalid:8000\//); return Response.json(datos); });
  assert.equal((await buscarArticulos(criterios)).simulador, false);
});
test('los ejemplos salen de Prism y cubren resultados, vacío, cobertura y problema', { timeout: 30000 }, async t => {
  configurar(t);
  const { iniciarSimulador } = require('../mocks/servidor.cjs');
  const simulador = await iniciarSimulador({ puerto: 0, puertoPrism: 14012, host: '127.0.0.1', silencioso: true });
  t.after(() => simulador.cerrar());
  process.env.EXPO_PUBLIC_ANALITICA_URL = `http://127.0.0.1:${simulador.puerto}`;
  const respuesta = await buscarArticulos(criterios);
  assert.equal(respuesta.simulador, true); // Lo identifica el encabezado, incluso con otro puerto.
  assert.equal(respuesta.datos.resultados.length, 2);
  assert.equal(respuesta.datos.resultados[0].observaciones, 12);
  const vacio = await buscarArticulos({ ...criterios, q: 'inexistente' });
  assert.equal(vacio.datos.total, 0);
  const cobertura = await buscarArticulos({ ...criterios, entidad: 'Colima' });
  assert.equal(cobertura.datos.cobertura, false);
  assert.equal(cobertura.datos.entidadesCubiertas.length, 7);
  await assert.rejects(buscarArticulos({ ...criterios, q: 'problema' }), error => {
    assert.equal(error.problema.status, 400);
    assert.equal(error.problema.title, 'Consulta inválida');
    assert.match(error.problema.detail, /simulador/); return true;
  });
});
