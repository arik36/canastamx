const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const ts = require('typescript');
require.extensions['.ts'] = (mod, filename) => mod._compile(ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText, filename);
const { clasificarImagen: imagen } = require('../components/clasificarImagen.ts');

test('rostizado, consomé y sopa sabor pollo nunca reutilizan pechuga cruda', () => {
  const tipos = [imagen('Pollo Rostizado. Tradicional'), imagen('Concentrado de Pollo', 'caja 12 cubos de 10 g'), imagen('alimentos preparados', 'vaso 64 gr sopa instantanea sabor a pollo')];
  assert.equal(new Set(tipos.map(t => JSON.stringify(t))).size, 3);
  for (const tipo of tipos) assert.notEqual(tipo?.foto, 'pechuga');
});
test('la presentación distingue entero, pechuga y pierna del mismo producto', () => {
  const tipos = ['1 kg granel entero', '1 kg pechuga', '1 kg pierna'].map(p => imagen('carne pollo', p));
  assert.ok(tipos.every(Boolean));
  assert.equal(new Set(tipos.map(t => JSON.stringify(t))).size, 3);
});
test('leche líquida, evaporada, condensada y polvo tienen recursos distintos', () => {
  const tipos = ['ultrapasteurizada', 'evaporada', 'condensada', 'en polvo'].map(t => imagen(`Leche ${t}`));
  assert.ok(tipos.every(Boolean));
  assert.equal(new Set(tipos.map(t => JSON.stringify(t))).size, 4);
});
test('un ingrediente o sabor no convierte otro producto en leche, pollo o fruta', () => {
  assert.deepEqual(imagen('gelatina en polvo', 'bolsa 120 gr leche fresa'), { atlas: 'complementos', celda: 5 });
  assert.equal(imagen('producto desconocido', 'sabor pollo'), undefined);
  assert.equal(imagen('artículo sin identificar', 'manzana'), undefined);
  assert.equal(imagen('crema dental'), undefined);
});
test('no se asigna una foto incompatible cuando falta una variante', () => {
  for (const [p, presentacion] of [['manzana', 'golden'], ['frijol', 'cocido'], ['queso', 'azul'], ['atun', 'empanizado'], ['leche', 'sabor chocolate']]) {
    assert.equal(imagen(p, presentacion), undefined);
  }
});
test('cubre mojarra y Blanco del Nilo de las últimas capturas sin confundir filetes', () => {
  for (const presentacion of ['1 kg granel tilapia grande fresco', '1 kg granel tilapia chica fresco']) {
    assert.deepEqual(imagen('Mojarra', presentacion), { atlas: 'frescos', celda: 0 });
  }
  assert.deepEqual(imagen('Blanco del Nilo', 'bolsa 1 kg filete o filete de tilapia natural'), { atlas: 'frescos', celda: 1 });
  assert.deepEqual(imagen('Mojarra', 'filete fresco'), { atlas: 'frescos', celda: 1 });
});
test('el ahumado se reconoce antes que lomo o fresco y nunca muestra atún crudo', () => {
  for (const presentacion of ['1 kg granel ahumado lomo', '1 kg ahumado tipo marlin o tipo marlin al natural', 'lomo fresco ahumado']) {
    assert.deepEqual(imagen('Atún', presentacion), { foto: 'atunAhumado' });
    assert.notDeepEqual(imagen('Atún', presentacion), imagen('Atún', 'lomo fresco'));
  }
});
test('normaliza mayúsculas y acentos conservando la presentación', () => {
  assert.deepEqual(imagen('PLÁTANO'), imagen('platano'));
  assert.deepEqual(imagen('LECHE EN POLVO'), imagen('leche', 'en polvo'));
  assert.deepEqual(imagen('yogurt'), { atlas: 'despensa', celda: 2 });
  assert.deepEqual(imagen('yoghurt'), imagen('yogur'));
  assert.deepEqual(imagen('arroz', 'integral'), { atlas: 'complementos', celda: 1 });
});
test('cubre todos los faltantes de las ocho capturas del responsable', () => {
  const casos = [
    ['Atún', 'bolsa 78 gr aleta amarilla en trozos en agua', 0],
    ['atun', 'bolsa 110 gr ensalada', 0],
    ['atun', 'bolsa 74 gr aleta amarilla en trozos en agua', 0],
    ['atun', 'bolsa 100 gr lomo en agua', 0],
    ['Arroz', 'bolsa 750 gr integral', 1],
    ['arroz', 'bolsa 1 kg super extra integral', 1],
    ['Shampoo', 'botella 760 ml aceite herbal', 2],
    ['shampoo', 'botella 650 ml aceite de oliva', 2],
    ['Acondicionador y Enjuague', 'botella 600 ml lavanda aceite de almendras', 3],
    ['shampoo', 'botella 600 ml lavanda aceite de almendras', 2],
    ['Cajeta', 'botella 333 gr de leche quemada', 4],
    ['cajeta', 'botella 594 gr de leche quemada', 4],
    ['Gelatina en Polvo', 'bolsa 120 gr leche fresa', 5],
  ];
  for (const [producto, presentacion, celda] of casos) assert.deepEqual(imagen(producto, presentacion), { atlas: 'complementos', celda }, `${producto}: ${presentacion}`);
});
test('distingue las nuevas variantes y conserva las imágenes ya asignadas', () => {
  assert.notDeepEqual(imagen('atun', 'bolsa 78 gr'), imagen('atun', 'lata 130 gr'));
  assert.notDeepEqual(imagen('arroz', 'integral'), imagen('arroz', 'super extra'));
  assert.notDeepEqual(imagen('shampoo', 'aceite oliva'), imagen('aceite', 'oliva'));
  assert.notDeepEqual(imagen('cajeta', 'leche quemada'), imagen('leche', 'entera'));
  assert.notDeepEqual(imagen('acondicionador y enjuague'), imagen('shampoo'));
});
test('harina de arroz usa harina blanca y no arroz cocido ni el respaldo neutro', () => {
  assert.deepEqual(imagen('Harina de Arroz', 'caja 200 gr'), { atlas: 'frescos', celda: 10 });
  assert.deepEqual(imagen('harina', 'bolsa 1 kg arroz'), imagen('harina de arroz'));
  assert.notDeepEqual(imagen('harina de arroz'), imagen('arroz'));
  assert.equal(imagen('harina de arroz', 'integral'), undefined);
});
