// Crea una cuenta sintética únicamente en la base aislada local y reutiliza
// el recorrido HTTP de T056. La cuenta queda allí; la canasta se elimina.
const assert = require('node:assert/strict');
const { randomUUID } = require('node:crypto');
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const ts = require('typescript');
require.extensions['.ts'] = (mod, filename) => mod._compile(ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText, filename);
async function probar() {
  if (process.env.CANASTAMX_PRUEBA_MOVIL_REAL !== '1') throw new Error('Sólo con CANASTAMX_PRUEBA_MOVIL_REAL=1 y la base aislada de T056.');
  for (const nombre of ['EXPO_PUBLIC_API_URL', 'EXPO_PUBLIC_ANALITICA_URL']) {
    if (new URL(process.env[nombre]).hostname !== '127.0.0.1') throw new Error('Esta prueba sólo admite servicios locales aislados.');
  }
  const { registrarCuenta, iniciarSesion, consultarMiCuenta } = require('../api/sesion.ts');
  const correo = `t072-${randomUUID()}@example.invalid`;
  const contrasena = `T072${randomUUID()}`;
  const cuenta = await registrarCuenta(correo, contrasena);
  assert.equal(cuenta.correo, correo); assert.equal(cuenta.rol, 'CONSUMIDOR');
  await assert.rejects(registrarCuenta(correo, contrasena), e => e.status === 409);
  const sesion = await iniciarSesion(correo, contrasena);
  assert.equal((await consultarMiCuenta(sesion.token)).id, cuenta.id);
  console.log('OK registro real, correo duplicado HTTP 409, inicio de sesión y cuenta propia.');
  const recorrido = spawnSync(process.execPath, [require.resolve('./t056-real.cjs')], {
    env: { ...process.env, T056_EMAIL: correo, T056_PASSWORD: contrasena }, encoding: 'utf8',
  });
  process.stdout.write(recorrido.stdout ?? '');
  process.stderr.write(recorrido.stderr ?? '');
  if (recorrido.status !== 0) throw new Error('Falló el recorrido HTTP de búsqueda, precios y canasta con la cuenta recién creada.');
}
probar().catch(e => { console.error(e.message); process.exitCode = 1; });
