const assert = require('node:assert/strict');
const test = require('node:test');
const { verificarDirecciones } = require('../scripts/verificar-build.cjs');
const buenas = { EXPO_PUBLIC_API_URL: 'https://dominio.canastamx.mx', EXPO_PUBLIC_ANALITICA_URL: 'https://analitica.canastamx.mx' };
test('la entrega exige ambas direcciones públicas y rechaza simuladores, secretos y ejemplos', () => {
  assert.doesNotThrow(() => verificarDirecciones(buenas));
  for (const nombre of Object.keys(buenas)) {
    for (const valor of [undefined, '', 'http://api.canastamx.mx', 'https://localhost', 'https://127.0.0.1:4011', 'https://192.168.1.4', 'https://[::1]', 'https://api.invalid', 'https://api.example.com', 'https://usuario:clave@api.canastamx.mx', 'https://api.canastamx.mx?token=secreto']) {
      assert.throws(() => verificarDirecciones({ ...buenas, [nombre]: valor }), new RegExp(nombre));
    }
  }
});
