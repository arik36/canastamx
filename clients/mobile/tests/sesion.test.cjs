const assert = require('node:assert/strict');
const test = require('node:test');
const ts = require('typescript');
const fs = require('node:fs');
// Node 20 no ejecuta TypeScript; esta carga usa el compilador ya instalado.
require.extensions['.ts'] = (mod, filename) => mod._compile(ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText, filename);
const api = require('../api/sesion.ts');
const { GestorSesion } = require('../session/gestor-sesion.ts');
const cuenta = { id: 'prueba', correo: 'consumidor@example.invalid', rol: 'CONSUMIDOR', fechaDeRegistro: '2026-10-28T12:00:00Z' };
const sesion = { token: 'token-de-prueba', rol: 'CONSUMIDOR', expiraEn: '2099-01-01T00:00:00Z' };
function escenario(cambios = {}, tokenInicial = null) {
  const estados = [];
  let almacenado = tokenInicial;
  const escritos = [];
  const deps = {
    leerToken: async () => almacenado,
    guardarToken: async token => { escritos.push(token); almacenado = token; },
    borrarToken: async () => { almacenado = null; },
    iniciar: async () => sesion,
    consultar: async token => { assert.equal(token, sesion.token); return cuenta; },
    ...cambios,
  };
  const gestor = new GestorSesion(deps, estado => estados.push(estado));
  return { gestor, estados, escritos, token: () => almacenado };
}
test('entrar obtiene el correo de /yo y persiste sólo el token', async () => {
  const e = escenario();
  assert.equal(await e.gestor.entrar('otro@example.invalid', 'NoPersistir123'), true);
  assert.deepEqual(e.escritos, [sesion.token]);
  assert.equal(e.estados.at(-1).cuenta.correo, cuenta.correo);
});
test('credenciales incorrectas terminan la carga sin persistir sesión', async () => {
  const e = escenario({ iniciar: async () => { throw new api.ErrorDeAcceso('Credenciales inválidas', 401); } });
  assert.equal(await e.gestor.entrar('a@b.mx', 'incorrecta'), false);
  assert.equal(e.estados.at(-1).estado, 'invitado');
  assert.equal(e.token(), null);
});
test('restaurar vuelve a consultar /yo usando el token guardado', async () => {
  const e = escenario({}, sesion.token);
  await e.gestor.restaurar();
  assert.equal(e.estados.at(-1).cuenta.correo, cuenta.correo);
  assert.deepEqual(e.escritos, []);
});
test('un 401 al restaurar borra el token y el perfil', async () => {
  const e = escenario({ consultar: async () => { throw new api.ErrorDeAcceso('Sesión vencida', 401); } }, sesion.token);
  await e.gestor.restaurar();
  assert.equal(e.token(), null);
  assert.equal(e.estados.at(-1).estado, 'invitado');
  assert.equal(e.estados.at(-1).cuenta, undefined);
});
test('una falla de red al restaurar permite reintentar sin borrar el token', async () => {
  let falla = true;
  const e = escenario({ consultar: async () => { if (falla) throw new Error('Sin red'); return cuenta; } }, sesion.token);
  await e.gestor.restaurar();
  assert.equal(e.estados.at(-1).estado, 'error');
  assert.equal(e.token(), sesion.token);
  falla = false;
  await e.gestor.restaurar();
  assert.equal(e.estados.at(-1).estado, 'conSesion');
});
for (const rol of ['ANALISTA', 'OPERADOR']) test(`el rol ${rol} no abre una sesión de consumidor ni se guarda`, async () => {
  const e = escenario({ iniciar: async () => ({ ...sesion, rol }), consultar: async () => ({ ...cuenta, rol }) });
  assert.equal(await e.gestor.entrar('a@b.mx', 'clave'), false);
  assert.match(e.estados.at(-1).mensaje, /plataforma web/);
  assert.equal(e.token(), null);
});
test('roles contradictorios entre token y /yo se rechazan', async () => {
  const e = escenario({ iniciar: async () => ({ ...sesion, rol: 'ANALISTA' }) });
  assert.equal(await e.gestor.entrar('a@b.mx', 'clave'), false);
  assert.equal(e.token(), null);
});
test('cerrar sesión borra la persistencia y el correo en memoria', async () => {
  const e = escenario();
  await e.gestor.entrar('a@b.mx', 'clave');
  assert.equal(await e.gestor.salir(), true);
  assert.equal(e.token(), null);
  assert.deepEqual(e.estados.at(-1), { estado: 'invitado' });
});
test('un fallo del almacenamiento no se presenta como sesión iniciada', async () => {
  const e = escenario({ guardarToken: async () => { throw new Error('Almacenamiento no disponible'); } });
  assert.equal(await e.gestor.entrar('a@b.mx', 'clave'), false);
  assert.equal(e.estados.at(-1).cuenta, undefined);
});
test('una respuesta tardía de restauración no revive una sesión cerrada', async () => {
  let resolver;
  const e = escenario({ consultar: () => new Promise(resolve => { resolver = resolve; }) }, sesion.token);
  const restauracion = e.gestor.restaurar();
  await new Promise(resolve => setImmediate(resolve));
  await e.gestor.salir();
  resolver(cuenta);
  await restauracion;
  assert.deepEqual(e.estados.at(-1), { estado: 'invitado' });
});
test('cerrar durante una escritura pendiente termina borrando el token', async () => {
  let liberar;
  let almacenado;
  const e = escenario({
    guardarToken: token => new Promise(resolve => { liberar = () => { almacenado = token; resolve(); }; }),
    borrarToken: async () => { almacenado = null; },
  });
  const entrada = e.gestor.entrar('a@b.mx', 'clave');
  await new Promise(resolve => setImmediate(resolve));
  const salida = e.gestor.salir();
  liberar();
  assert.equal(await entrada, false);
  assert.equal(await salida, true);
  assert.equal(almacenado, null);
  assert.deepEqual(e.estados.at(-1), { estado: 'invitado' });
});
test('la API envía credenciales por POST y Bearer sólo a /yo', async t => {
  process.env.EXPO_PUBLIC_API_URL = 'http://dominio.invalid:8081/';
  const llamadas = [];
  t.mock.method(global, 'fetch', async (url, opciones) => {
    llamadas.push({ url, opciones });
    return new Response(JSON.stringify(url.endsWith('/sesiones') ? sesion : cuenta));
  });
  await api.iniciarSesion(' a@b.mx ', 'ClaveConEspacio ');
  await api.consultarMiCuenta(sesion.token);
  assert.equal(llamadas[0].opciones.method, 'POST');
  assert.deepEqual(JSON.parse(llamadas[0].opciones.body), { correo: 'a@b.mx', contrasena: 'ClaveConEspacio ' });
  assert.equal(llamadas[0].opciones.headers.Authorization, undefined);
  assert.equal(llamadas[1].opciones.headers.Authorization, `Bearer ${sesion.token}`);
});
test('el 401 del acceso se muestra como credenciales inválidas', async t => {
  t.mock.method(global, 'fetch', async () => new Response('', { status: 401 }));
  await assert.rejects(api.iniciarSesion('a@b.mx', 'clave'), /correo o la contraseña no son válidos/);
});
test('respuestas incompletas nunca se aceptan como sesión o cuenta', async t => {
  t.mock.method(global, 'fetch', async () => new Response('{}'));
  await assert.rejects(api.iniciarSesion('a@b.mx', 'clave'), /no cumple/);
  await assert.rejects(api.consultarMiCuenta('token'), /no cumple/);
});
test('la espera se corta a los ocho segundos', async t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  t.mock.method(global, 'fetch', async (_, opciones) => new Promise((_, reject) => {
    opciones.signal.addEventListener('abort', () => reject(new Error('Abortado')));
  }));
  const consulta = api.iniciarSesion('a@b.mx', 'clave');
  t.mock.timers.tick(8000);
  await assert.rejects(consulta, /8 segundos/);
});
