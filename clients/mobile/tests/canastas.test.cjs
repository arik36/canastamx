const assert = require('node:assert/strict');
const test = require('node:test');
const ts = require('typescript');
const fs = require('node:fs');
require.extensions['.ts'] = (mod, filename) => mod._compile(ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText, filename);
const api = require('../api/canastas.ts');
const precios = require('../api/precios.ts');
const { comparacion, costo } = require('../mocks/canasta.cjs');
const articulo = { producto: 'leche & arroz', presentacion: '1 l / bolsa' };
const linea = { articulo, cantidad: 2 };
const canasta = { id: 'canasta/1', nombre: 'Mi canasta', lineas: [linea] };
function configurar(t) {
  for (const [k, v] of Object.entries({ EXPO_PUBLIC_API_URL: 'http://dominio.invalid', EXPO_PUBLIC_ANALITICA_URL: 'http://analitica.invalid' })) {
    const previo = process.env[k]; process.env[k] = v;
    t.after(() => { if (previo === undefined) delete process.env[k]; else process.env[k] = previo; });
  }
}
test('las ocho operaciones usan dominio y Bearer; POST suma, PUT fija y DELETE codifica la identidad', async t => {
  configurar(t); const llamadas = [];
  t.mock.method(global, 'fetch', async (url, opciones) => {
    llamadas.push({ url: new URL(url), opciones });
    if (opciones.method === 'DELETE' && !url.includes('/lineas')) return new Response(null, { status: 204 });
    return Response.json(url.includes('?limit=') ? { canastas: [canasta], total: 1 } : canasta);
  });
  await api.listarCanastas('token-prueba'); await api.crearCanasta('token-prueba', ' Mi canasta ');
  await api.obtenerCanasta('token-prueba', canasta.id); await api.renombrarCanasta('token-prueba', canasta.id, ' Otra ');
  await api.guardarLinea('token-prueba', canasta.id, linea); await api.guardarLinea('token-prueba', canasta.id, linea, true);
  await api.quitarArticulo('token-prueba', canasta.id, articulo); await api.borrarCanasta('token-prueba', canasta.id);
  assert.deepEqual(llamadas.map(l => l.opciones.method), ['GET', 'POST', 'GET', 'PATCH', 'POST', 'PUT', 'DELETE', 'DELETE']);
  assert.ok(llamadas.every(l => l.url.origin === 'http://dominio.invalid' && l.opciones.headers.Authorization === 'Bearer token-prueba'));
  assert.equal(llamadas[6].url.pathname, '/api/v1/canastas/canasta%2F1/lineas');
  assert.equal(llamadas[6].url.searchParams.get('producto'), articulo.producto);
  assert.equal(llamadas[6].url.searchParams.get('presentacion'), articulo.presentacion);
  assert.deepEqual(JSON.parse(llamadas[5].opciones.body), linea);
});
test('restaura todas las páginas de canastas, no sólo las primeras cien', async t => {
  configurar(t); let paginas = 0;
  t.mock.method(global, 'fetch', async url => {
    paginas++; const offset = Number(new URL(url).searchParams.get('offset'));
    return Response.json({ total: 101, canastas: Array.from({ length: offset === 0 ? 100 : 1 }, (_, i) => ({ ...canasta, id: String(offset + i) })) });
  });
  assert.equal((await api.listarCanastas('t')).length, 101); assert.equal(paginas, 2);
});
test('cantidades inválidas, nombres vacíos y sesión ausente no hacen escrituras', async t => {
  configurar(t); const mock = t.mock.method(global, 'fetch', () => { throw new Error('No debía llamarse'); });
  for (const cantidad of [0, -1, 1.5, null, NaN, Infinity, Number.MAX_SAFE_INTEGER + 1])
    await assert.rejects(api.guardarLinea('t', 'id', { articulo, cantidad }), /entero/);
  await assert.rejects(api.crearCanasta('t', '  '), /nombre/);
  await assert.rejects(api.listarCanastas(''), /Inicia sesión/);
  assert.equal(mock.mock.callCount(), 0);
});
test('rechaza respuestas incompletas y líneas duplicadas sin tratarlas como canasta vacía', () => {
  for (const v of [{ id: 'x' }, { ...canasta, lineas: [{ ...linea, cantidad: 0 }] }, { ...canasta, lineas: [linea, linea] }])
    assert.throws(() => api.validarCanasta(v), /contrato/);
});
test('comparación y costo van a la analítica sin token y conservan dinero exacto, fecha, quincena y faltantes', async t => {
  configurar(t); const llamadas = [];
  t.mock.method(global, 'fetch', async (url, opciones) => {
    llamadas.push({ url: new URL(url), opciones });
    return Response.json(url.includes('/precios') ? comparacion(articulo, 'Guanajuato') : costo({ entidad: 'Guanajuato', lineas: [linea] }));
  });
  const p = await precios.compararPrecios(articulo, 'Guanajuato');
  const c = await precios.costearCanasta([linea], 'Guanajuato');
  assert.ok(llamadas.every(l => l.url.origin === 'http://analitica.invalid' && l.opciones.headers.Authorization === undefined));
  assert.equal(llamadas[0].url.searchParams.get('producto'), articulo.producto);
  assert.deepEqual(JSON.parse(llamadas[1].opciones.body), { entidad: 'Guanajuato', lineas: [linea] });
  assert.equal(p.datos.establecimientos[0].precio.monto, '28.50');
  assert.equal(p.datos.establecimientos[0].fechaRegistro, '2026-07-24');
  assert.equal(c.datos.quincena, '2026-07-Q2');
  assert.equal(c.datos.cadenas[1].lineas[0].precio, null); assert.equal(c.datos.cadenas[1].faltan, 1);
  assert.equal(c.datos.cadenas[0].total.monto, '57.00'); assert.equal(c.simulador, false);
});
test('no muestra precio flotante, fecha imposible ni faltantes incongruentes', () => {
  const p = comparacion(articulo, 'Guanajuato');
  assert.throws(() => precios.validarComparacion({ ...p, establecimientos: [{ ...p.establecimientos[0], fechaRegistro: '2026-02-30' }] }));
  assert.throws(() => precios.validarComparacion({ ...p, establecimientos: [{ ...p.establecimientos[0], precio: { monto: 28.5, moneda: 'MXN' } }] }));
  const c = costo({ entidad: 'Guanajuato', lineas: [linea] }); c.cadenas[1].faltan = 0;
  assert.throws(() => precios.validarCosto(c));
});
test('rechaza costos calculados para otras cantidades aunque su esquema sea válido', async t => {
  configurar(t); t.mock.method(global, 'fetch', async () => Response.json(costo({ entidad: 'Guanajuato', lineas: [{ ...linea, cantidad: 99 }] })));
  await assert.rejects(precios.costearCanasta([linea], 'Guanajuato'), /otra lista/);
});
test('401 y 404 conservan problem+json y un error HTML conserva su HTTP', async t => {
  configurar(t);
  for (const status of [401, 404]) {
    const p = { type: '/problemas/no-existe', title: 'No existe', status, detail: 'No existe esa canasta.' };
    const mock = t.mock.method(global, 'fetch', async () => Response.json(p, { status, headers: { 'content-type': 'application/problem+json' } }));
    await assert.rejects(api.obtenerCanasta('t', 'ajena'), e => e.status === status && e.problema.detail === p.detail);
    mock.mock.restore();
  }
  t.mock.method(global, 'fetch', async () => new Response('error', { status: 503 }));
  await assert.rejects(api.listarCanastas('t'), /HTTP 503/);
});
test('cancela peticiones desmontadas y corta la espera del dominio y la analítica a ocho segundos', async t => {
  configurar(t); t.mock.timers.enable({ apis: ['setTimeout'] });
  t.mock.method(global, 'fetch', (_, o) => new Promise((_, reject) => {
    if (o.signal.aborted) reject(new Error('Cancelada'));
    else o.signal.addEventListener('abort', () => reject(new Error('Cancelada')));
  }));
  for (const llamada of [() => api.listarCanastas('t'), () => precios.costearCanasta([linea], 'Guanajuato')]) {
    const pendiente = llamada(); t.mock.timers.tick(8000); await assert.rejects(pendiente, /8 segundos/);
  }
  const controller = new AbortController(); const pendiente = api.listarCanastas('t', controller.signal);
  controller.abort(); await assert.rejects(pendiente, /Cancelada/);
});
test('simulador declara su origen y sirve precios y costos con las cantidades enviadas', { timeout: 90000 }, async t => {
  configurar(t);
  const { iniciarSimulador } = require('../mocks/servidor.cjs');
  const sim = await iniciarSimulador({ puerto: 0, puertoPrism: 4014, host: '127.0.0.1', silencioso: true });
  t.after(() => sim.cerrar()); process.env.EXPO_PUBLIC_ANALITICA_URL = `http://127.0.0.1:${sim.puerto}`;
  const p = await precios.compararPrecios(articulo, 'Guanajuato');
  const c = await precios.costearCanasta([linea], 'Guanajuato');
  assert.equal(p.simulador, true); assert.equal(c.simulador, true);
  assert.equal(c.datos.cadenas[0].lineas[0].cantidad, 2);
});
