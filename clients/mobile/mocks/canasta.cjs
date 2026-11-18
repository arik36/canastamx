// Datos sintéticos de desarrollo. La app nunca importa este módulo ni calcula totales.
const { quincena } = require('./escenarios.cjs');
function comparacion(articulo, entidad) {
  return { articulo, entidad, quincena, establecimientos: [
    { nombre: 'Tienda de prueba Centro', cadena: 'Cadena de prueba A', marca: 'Marca de prueba',
      precio: { monto: '28.50', moneda: 'MXN' }, fechaRegistro: '2026-07-24', municipio: 'León', direccion: 'Dirección ficticia 1' },
    { nombre: 'Tienda de prueba Norte', cadena: 'Cadena de prueba B', marca: 'Marca de prueba',
      precio: { monto: '30.00', moneda: 'MXN' }, fechaRegistro: '2026-07-25', municipio: 'León' },
  ] };
}
function costo({ entidad, lineas }) {
  return { entidad, quincena, cadenas: [2850n, 3000n].map((centavos, i) => {
    // La segunda cadena omite el último artículo para probar el total parcial.
    let total = 0n;
    const resultado = lineas.map((l, n) => {
      const falta = i === 1 && n === lineas.length - 1;
      if (!falta) total += BigInt(l.cantidad) * centavos;
      return { ...l, precio: falta ? null : { monto: `${centavos / 100n}.${String(centavos % 100n).padStart(2, '0')}`, moneda: 'MXN' } };
    });
    return { cadena: `Cadena de prueba ${i ? 'B' : 'A'}`, total: { monto: `${total / 100n}.${String(total % 100n).padStart(2, '0')}`, moneda: 'MXN' },
      faltan: resultado.filter(l => l.precio === null).length, lineas: resultado };
  }) };
}
async function responderCanasta(req, res, url) {
  if (!['/api/v1/precios', '/api/v1/canastas/costo'].includes(url.pathname)) return false;
  const enviar = (status, datos) => {
    res.writeHead(status, { 'content-type': status === 200 ? 'application/json' : 'application/problem+json',
      'x-canastamx-fuente': 'simulador', 'cache-control': 'no-store' }); res.end(JSON.stringify(datos));
  };
  try {
    if (url.pathname === '/api/v1/precios' && req.method === 'GET') {
      const producto = url.searchParams.get('producto'), presentacion = url.searchParams.get('presentacion'), entidad = url.searchParams.get('entidad');
      if (!producto || !presentacion || !entidad) throw new Error('Faltan criterios.');
      enviar(200, comparacion({ producto, presentacion }, entidad));
    } else if (url.pathname === '/api/v1/canastas/costo' && req.method === 'POST') {
      let body = '';
      for await (const parte of req) { body += parte; if (body.length > 100000) throw new Error('Pedido demasiado grande.'); }
      const pedido = JSON.parse(body);
      if (typeof pedido.entidad !== 'string' || !pedido.entidad.trim() || !Array.isArray(pedido.lineas) || pedido.lineas.length > 200
        || !pedido.lineas.every(l => l?.articulo && typeof l.articulo.producto === 'string' && typeof l.articulo.presentacion === 'string'
          && Number.isSafeInteger(l.cantidad) && l.cantidad > 0)) throw new Error('Pedido inválido.');
      enviar(200, costo(pedido));
    } else enviar(405, { type: 'urn:canastamx:simulador:metodo', title: 'Método no permitido', status: 405 });
  } catch {
    enviar(400, { type: 'urn:canastamx:simulador:pedido', title: 'Pedido inválido', status: 400 });
  }
  return true;
}
module.exports = { responderCanasta, comparacion, costo };
