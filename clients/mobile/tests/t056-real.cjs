// Prueba optativa contra servicios reales y la semilla aislada t056-analitica.sql.
// No se incluye en npm test: crea y borra exclusivamente su propia canasta.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const ts = require('typescript');
require.extensions['.ts'] = (mod, filename) => mod._compile(ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText, filename);
const api = require('../api/canastas.ts');
const { iniciarSesion } = require('../api/sesion.ts');
const { buscarArticulos } = require('../api/analitica.ts');
const { compararPrecios, costearCanasta } = require('../api/precios.ts');
async function probar() {
  if (process.env.CANASTAMX_PRUEBA_MOVIL_REAL !== '1') throw new Error('Activa CANASTAMX_PRUEBA_MOVIL_REAL=1 sólo con la base y semilla aisladas.');
  for (const nombre of ['EXPO_PUBLIC_API_URL', 'EXPO_PUBLIC_ANALITICA_URL']) {
    if (!['127.0.0.1', 'localhost', '[::1]'].includes(new URL(process.env[nombre]).hostname)) throw new Error('Esta prueba sólo admite servicios locales.');
  }
  if (!process.env.T056_EMAIL || !process.env.T056_PASSWORD) throw new Error('Faltan las credenciales de la cuenta sintética.');
  const entrar = () => iniciarSesion(process.env.T056_EMAIL, process.env.T056_PASSWORD);
  let sesion = await entrar();
  const busqueda = await buscarArticulos({ q: 'leche', entidad: 'Guanajuato' });
  assert.equal(busqueda.simulador, false); assert.equal(busqueda.datos.cobertura, true);
  assert.equal(busqueda.datos.resultados.length, 2);
  const entera = busqueda.datos.resultados.find(a => a.articulo.producto === 'leche entera').articulo;
  const descremada = busqueda.datos.resultados.find(a => a.articulo.producto === 'leche descremada').articulo;
  const precios = await compararPrecios(entera, 'Guanajuato');
  assert.equal(precios.simulador, false); assert.equal(precios.datos.establecimientos.length, 2);
  assert.equal(precios.datos.quincena, '2026-07-Q2');
  assert.equal(precios.datos.establecimientos[0].fechaRegistro, '2026-07-24');
  console.log('OK búsqueda y precios: API real, dos establecimientos, fecha y quincena de la semilla.');
  const creada = await api.crearCanasta(sesion.token, `Prueba HTTP T056 ${Date.now()}`);
  try {
    assert.equal((await api.renombrarCanasta(sesion.token, creada.id, 'Prueba HTTP T056 renombrada')).nombre, 'Prueba HTTP T056 renombrada');
    await api.guardarLinea(sesion.token, creada.id, { articulo: entera, cantidad: 1 });
    let c = await api.guardarLinea(sesion.token, creada.id, { articulo: entera, cantidad: 1 });
    assert.equal(c.lineas[0].cantidad, 2); assert.equal(c.lineas.length, 1);
    c = await api.guardarLinea(sesion.token, creada.id, { articulo: entera, cantidad: 3 }, true);
    c = await api.guardarLinea(sesion.token, creada.id, { articulo: descremada, cantidad: 1 });
    const costo = await costearCanasta(c.lineas, 'Guanajuato');
    assert.equal(costo.simulador, false);
    assert.deepEqual(costo.datos.cadenas.map(c => [c.cadena, c.total.monto, c.faltan]), [
      ['Cadena de prueba A', '117.90', 0], ['Cadena de prueba B', '90.00', 1],
    ]);
    console.log('OK costo real: 117.90 MXN completo y 90.00 MXN parcial con un faltante.');
    await api.quitarArticulo(sesion.token, creada.id, descremada);
    await assert.rejects(api.quitarArticulo(sesion.token, creada.id, descremada), e => e.status === 404);
    sesion = await entrar();
    const recuperada = await api.obtenerCanasta(sesion.token, creada.id);
    assert.deepEqual(recuperada.lineas, [{ articulo: entera, cantidad: 3 }]);
    assert.ok((await api.listarCanastas(sesion.token)).some(c => c.id === creada.id));
    await assert.rejects(api.obtenerCanasta('token-invalido', creada.id), e => e.status === 401);
    console.log('OK crear, sumar, fijar, quitar, recuperar con sesión nueva, 404 y 401.');
  } finally { await api.borrarCanasta(sesion.token, creada.id); }
  console.log('OK canasta propia de la prueba eliminada.');
}
probar().catch(error => { console.error(error.message); process.exitCode = 1; });
