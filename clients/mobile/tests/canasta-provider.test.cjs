const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const ts = require('typescript');
const Module = require('node:module');
for (const extension of ['.ts', '.tsx']) require.extensions[extension] = (mod, filename) => mod._compile(ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX },
}).outputText, filename);
const React = require('react');
const { create, act } = require('react-test-renderer');
global.IS_REACT_ACT_ENVIRONMENT = true;
let sesion;
const cargar = Module._load;
Module._load = function(nombre, parent, ...args) {
  if (nombre === '../session/SesionProvider') return { useSesion: () => sesion };
  return cargar.call(this, nombre, parent, ...args);
};
const { CanastaProvider, useCanasta } = require('../canasta/CanastaProvider.tsx');
Module._load = cargar;
const api = require('../api/canastas.ts');
const { ErrorServicio } = require('../api/solicitud.ts');
let contexto;
function Hijo() { contexto = useCanasta(); return null; }
const vista = () => React.createElement(CanastaProvider, null, React.createElement(Hijo));
const cuenta = id => ({ estado: 'conSesion', cuenta: { id }, tokenDeSesion: () => `token-${id}`, reintentar: async () => {} });
const diferir = () => { let resolve; const promise = new Promise(r => { resolve = r; }); return { promise, resolve }; };
const canasta = id => ({ id, nombre: `Canasta ${id}`, lineas: [] });
test('una respuesta tardía de otra cuenta no reaparece; salir vacía la canasta', async t => {
  const antigua = diferir();
  t.mock.method(api, 'listarCanastas', token => token === 'token-A' ? antigua.promise : Promise.resolve([canasta('B')]));
  sesion = cuenta('A'); let root;
  await act(async () => { root = create(vista()); });
  sesion = cuenta('B'); await act(async () => { root.update(vista()); });
  assert.equal(contexto.actual.id, 'B');
  await act(async () => antigua.resolve([canasta('A')]));
  assert.equal(contexto.actual.id, 'B');
  sesion = { ...sesion, estado: 'invitado', cuenta: undefined };
  await act(async () => { root.update(vista()); });
  assert.deepEqual(contexto.canastas, []); assert.equal(contexto.actual, undefined);
  await act(async () => root.unmount());
});
test('dos pulsaciones no duplican una escritura y fijar usa PUT; recargar recupera del dominio', async t => {
  sesion = cuenta('A');
  let persistida = canasta('A');
  t.mock.method(api, 'listarCanastas', async () => [persistida]);
  const pendiente = diferir();
  const guardar = t.mock.method(api, 'guardarLinea', () => pendiente.promise);
  let root; await act(async () => { root = create(vista()); });
  const articulo = { producto: 'leche', presentacion: '1 l' };
  let primera, segunda;
  await act(async () => { primera = contexto.agregar(articulo, 2); segunda = contexto.agregar(articulo, 2); });
  assert.equal(await segunda, false); assert.equal(guardar.mock.callCount(), 1);
  persistida = { ...persistida, lineas: [{ articulo, cantidad: 2 }] };
  await act(async () => { pendiente.resolve(persistida); await primera; });
  guardar.mock.mockImplementation(async (...args) => {
    assert.equal(args[3], true); persistida = { ...persistida, lineas: [args[2]] }; return persistida;
  });
  await act(async () => { await contexto.fijar({ articulo, cantidad: 3 }); });
  assert.equal(contexto.actual.lineas[0].cantidad, 3);
  await act(async () => root.unmount());
  await act(async () => { root = create(vista()); });
  assert.equal(contexto.actual.lineas[0].cantidad, 3);
  await act(async () => root.unmount());
});
test('un 401 descarta datos y solicita restaurar sesión; no reintenta escrituras automáticamente', async t => {
  sesion = cuenta('A'); let restauraciones = 0;
  sesion.reintentar = async () => { restauraciones++; };
  t.mock.method(api, 'listarCanastas', async () => [canasta('A')]);
  const guardar = t.mock.method(api, 'guardarLinea', async () => { throw new ErrorServicio('Sesión vencida', 401); });
  let root; await act(async () => { root = create(vista()); });
  await act(async () => { await contexto.agregar({ producto: 'leche', presentacion: '1 l' }, 1); });
  assert.equal(restauraciones, 1); assert.equal(guardar.mock.callCount(), 1);
  assert.deepEqual(contexto.canastas, []); assert.match(contexto.error, /Sesión vencida/);
  await act(async () => root.unmount());
});
test('una escritura de resultado incierto bloquea nuevos envíos hasta recuperar el estado del dominio', async t => {
  sesion = cuenta('A');
  const articulo = { producto: 'leche', presentacion: '1 l' };
  let persistida = canasta('A');
  t.mock.method(api, 'listarCanastas', async () => [persistida]);
  const guardar = t.mock.method(api, 'guardarLinea', async () => {
    persistida = { ...persistida, lineas: [{ articulo, cantidad: 1 }] };
    throw new ErrorServicio('Se perdió la conexión después de guardar.');
  });
  let root; await act(async () => { root = create(vista()); });
  await act(async () => { await contexto.agregar(articulo, 1); });
  assert.equal(contexto.requiereRecarga, true);
  await act(async () => { assert.equal(await contexto.agregar(articulo, 1), false); });
  assert.equal(guardar.mock.callCount(), 1);
  await act(async () => { await contexto.recargar(); });
  assert.equal(contexto.requiereRecarga, false);
  assert.equal(contexto.actual.lineas[0].cantidad, 1);
  await act(async () => root.unmount());
});

test('renombrar persiste y eliminar la última canasta deja un estado vacío utilizable', async t => {
  sesion = cuenta('A');
  t.mock.method(api, 'listarCanastas', async () => [canasta('A')]);
  const renombrar = t.mock.method(api, 'renombrarCanasta', async (token, id, nombre) => ({ ...canasta(id), nombre }));
  const borrar = t.mock.method(api, 'borrarCanasta', async () => {});
  let root; await act(async () => { root = create(vista()); });
  await act(async () => { assert.equal(await contexto.renombrar('Mi compra'), true); });
  assert.equal(contexto.actual.nombre, 'Mi compra');
  assert.equal(renombrar.mock.calls[0].arguments[0], 'token-A');
  await act(async () => { assert.equal(await contexto.borrar(), true); });
  assert.equal(borrar.mock.calls[0].arguments[1], 'A');
  assert.equal(contexto.actual, undefined);
  assert.deepEqual(contexto.canastas, []);
  assert.equal(contexto.listaCargada, true);
  assert.equal(await contexto.borrar(), false);
  await act(async () => root.unmount());
});

test('agregar desde una tarjeta usa la canasta elegida aunque otra esté activa', async t => {
  sesion = cuenta('A');
  t.mock.method(api, 'listarCanastas', async () => [canasta('uno'), canasta('dos')]);
  const articulo = { producto: 'arroz', presentacion: '1 kg' };
  const guardar = t.mock.method(api, 'guardarLinea', async (_, id, linea) => ({ ...canasta(id), lineas: [linea] }));
  let root; await act(async () => { root = create(vista()); });
  assert.equal(contexto.actual.id, 'uno');
  await act(async () => { assert.equal(await contexto.agregarEn('dos', articulo, 1), true); });
  assert.equal(guardar.mock.calls[0].arguments[1], 'dos');
  assert.equal(contexto.actual.id, 'dos');
  assert.equal(await contexto.agregarEn('ajena', articulo, 1), false);
  assert.equal(guardar.mock.callCount(), 1);
  await act(async () => root.unmount());
});
