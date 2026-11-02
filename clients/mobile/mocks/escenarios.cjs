// Datos sintéticos exclusivos del simulador. Nunca se importan desde la app.
const entidadesCubiertas = ['Aguascalientes', 'Guanajuato', 'Jalisco', 'Michoacán', 'Querétaro', 'San Luis Potosí', 'Zacatecas'];
const entidades = ['Aguascalientes', 'Baja California', 'Baja California Sur', 'Campeche', 'Chiapas', 'Chihuahua', 'Ciudad de México', 'Coahuila', 'Colima', 'Durango', 'Guanajuato', 'Guerrero', 'Hidalgo', 'Jalisco', 'Estado de México', 'Michoacán', 'Morelos', 'Nayarit', 'Nuevo León', 'Oaxaca', 'Puebla', 'Querétaro', 'Quintana Roo', 'San Luis Potosí', 'Sinaloa', 'Sonora', 'Tabasco', 'Tamaulipas', 'Tlaxcala', 'Veracruz', 'Yucatán', 'Zacatecas'];
const quincena = '2026-07-Q2';
const articulos = [
  { articulo: { producto: 'leche entera', presentacion: 'envase de 1 litro' }, nombre: 'Leche entera', catalogo: 'BASICOS', precioTipico: { monto: '28.50', moneda: 'MXN' }, observaciones: 12 },
  { articulo: { producto: 'leche descremada', presentacion: 'envase de 1 litro' }, nombre: 'Leche descremada', catalogo: 'BASICOS', precioTipico: { monto: '30.00', moneda: 'MXN' }, observaciones: 8 },
  { articulo: { producto: 'arroz', presentacion: 'bolsa de 1 kilogramo' }, nombre: 'Arroz', catalogo: 'PACIC', precioTipico: { monto: '32.40', moneda: 'MXN' }, observaciones: 5 },
];
const normalizar = texto => texto.trim().normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
function ejemplos() {
  const casos = {};
  for (let indice = 0; indice < entidades.length; indice++) {
    const entidad = entidades[indice];
    if (!entidadesCubiertas.includes(entidad)) {
      casos[`entidad_${indice}`] = { value: { cobertura: false, entidad, entidadesCubiertas } };
      continue;
    }
    for (let mascara = 0; mascara < 8; mascara++) {
      const resultados = articulos.filter((_, i) => mascara & (1 << i));
      casos[`entidad_${indice}_${mascara}`] = { value: { cobertura: true, entidad, quincena, total: resultados.length, resultados } };
    }
  }
  return casos;
}
function elegirEjemplo(url) {
  if (url.pathname !== '/api/v1/articulos') return undefined;
  const entidad = normalizar(url.searchParams.get('entidad') ?? '');
  const indice = entidades.findIndex(nombre => normalizar(nombre) === entidad);
  if (indice < 0) return { code: 400, example: 'entidadInvalida' };
  if (!entidadesCubiertas.includes(entidades[indice])) return { code: 200, example: `entidad_${indice}` };
  const q = normalizar(url.searchParams.get('q') ?? '');
  // Escenario de problem+json explícito, documentado para comprobar la interfaz.
  if (q === 'problema') return { code: 400, example: 'consultaInvalida' };
  const mascara = articulos.reduce((actual, articulo, i) => normalizar(`${articulo.nombre} ${articulo.articulo.presentacion}`).includes(q) ? actual | (1 << i) : actual, 0);
  return { code: 200, example: `entidad_${indice}_${mascara}` };
}
module.exports = { entidadesCubiertas, entidades, quincena, articulos, ejemplos, elegirEjemplo };
