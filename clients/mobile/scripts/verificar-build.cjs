const { isIP } = require('node:net');

function verificarDirecciones(env) {
  for (const nombre of ['EXPO_PUBLIC_API_URL', 'EXPO_PUBLIC_ANALITICA_URL']) {
    let url;
    try { url = new URL(env[nombre]); } catch { throw new Error(`Falta ${nombre}: configura la dirección HTTPS pública del despliegue #201.`); }
    const host = url.hostname.toLowerCase();
    if (url.protocol !== 'https:' || url.username || url.password || url.search || url.hash
      || isIP(host.replace(/^\[|\]$/g, '')) || !host.includes('.')
      || /(^|\.)(localhost|local|internal|invalid|example|test)$/.test(host)
      || /(^|\.)example\.(com|org|net)$/.test(host)) {
      throw new Error(`${nombre} debe ser una dirección HTTPS pública, sin credenciales ni parámetros.`);
    }
  }
}
module.exports = { verificarDirecciones };
if (require.main === module) {
  try { verificarDirecciones(process.env); console.log('Direcciones de entrega configuradas. Falta comprobarlas contra el despliegue real.'); }
  catch (e) { console.error(e.message); process.exitCode = 1; }
}
