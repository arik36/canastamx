// Prism produce y valida las respuestas; este adaptador sólo elige un ejemplo por consulta.
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const http = require('node:http');
const { spawn } = require('node:child_process');
const YAML = require('yaml');
const { ejemplos, elegirEjemplo, entidadesCubiertas, quincena } = require('./escenarios.cjs');

async function iniciarSimulador({ puerto = 4011, puertoPrism = 4012, host = '0.0.0.0', silencioso = false } = {}) {
  const contrato = path.resolve(__dirname, '../../../docs/analisis/openapi/analitica.yaml');
  const spec = YAML.parse(fs.readFileSync(contrato, 'utf8'));
  if (spec.info.version !== '0.2.1') throw new Error('Revisa los ejemplos: el contrato analítico cambió de versión.');
  spec.paths['/api/v1/articulos'].get.responses['200'].content['application/json'].examples = ejemplos();
  spec.components.responses.DatosInvalidos.content['application/problem+json'].examples = {
    entidadInvalida: { value: { type: 'urn:canastamx:simulador:entidad-invalida', title: 'Entidad no reconocida', status: 400, detail: 'Escribe el nombre completo de una entidad federativa de México.' } },
    consultaInvalida: { value: { type: 'urn:canastamx:simulador:consulta-invalida', title: 'Consulta inválida', status: 400, detail: 'El simulador rechazó esta consulta de prueba. Cambia el término e intenta de nuevo.' } },
  };
  spec.paths['/api/v1/entidades'].get.responses['200'].content['application/json'].example = {
    entidades: entidadesCubiertas.map(entidad => ({ entidad, ultimaQuincena: quincena })),
  };
  const carpeta = fs.mkdtempSync(path.join(os.tmpdir(), 'canastamx-prism-'));
  const archivo = path.join(carpeta, 'analitica-con-ejemplos.json');
  fs.writeFileSync(archivo, JSON.stringify(spec));
  const paquete = require.resolve('@stoplight/prism-cli/package.json');
  const bin = require(paquete).bin.prism;
  const proceso = spawn(process.execPath, [path.resolve(path.dirname(paquete), bin), 'mock', '-h', '127.0.0.1', '-p', String(puertoPrism), archivo], {
    windowsHide: true, stdio: silencioso ? 'ignore' : 'inherit',
  });
  let fallo;
  proceso.once('error', error => { fallo = error; });
  proceso.once('exit', codigo => { fallo = new Error(`Prism terminó (${codigo}). Comprueba que ${puertoPrism} esté libre.`); });
  const limpiar = () => {
    if (fs.existsSync(archivo)) fs.unlinkSync(archivo);
    if (fs.existsSync(carpeta)) fs.rmdirSync(carpeta);
  };
  const servidor = http.createServer(async (req, res) => {
    const url = new URL(req.url, 'http://simulador.local');
    if (req.method !== 'GET' || !['/health', '/api/v1/entidades', '/api/v1/articulos'].includes(url.pathname)) {
      res.writeHead(404, { 'content-type': 'application/problem+json', 'x-canastamx-fuente': 'simulador' });
      res.end(JSON.stringify({ type: 'urn:canastamx:simulador:ruta', title: 'Ruta fuera del simulador de búsqueda', status: 404 })); return;
    }
    const elegido = elegirEjemplo(url);
    const headers = { Accept: req.headers.accept ?? '*/*' };
    if (elegido) {
      headers.Prefer = `code=${elegido.code}, example=${elegido.example}`;
      if (elegido.code >= 400) headers.Accept = 'application/problem+json';
    }
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 7000);
    try {
      const respuesta = await fetch(`http://127.0.0.1:${puertoPrism}${url.pathname}${url.search}`, {
        method: req.method, headers, signal: controller.signal,
      });
      const cuerpo = await respuesta.text();
      res.writeHead(respuesta.status, { 'content-type': respuesta.headers.get('content-type') ?? 'application/json', 'x-canastamx-fuente': 'simulador', 'cache-control': 'no-store' });
      res.end(cuerpo);
    } catch {
      res.writeHead(503, { 'content-type': 'application/problem+json', 'x-canastamx-fuente': 'simulador' });
      res.end(JSON.stringify({ type: 'urn:canastamx:simulador:no-disponible', title: 'Simulador no disponible', status: 503, detail: 'Prism no respondió. Reinicia el simulador y vuelve a intentar.' }));
    } finally { clearTimeout(timer); }
  });
  try {
    let preparado = false;
    for (let i = 0; i < 100; i++) {
      if (fallo) throw fallo;
      try { if ((await fetch(`http://127.0.0.1:${puertoPrism}/health`)).ok) { preparado = true; break; } } catch {}
      await new Promise(resolve => setTimeout(resolve, 150));
    }
    if (!preparado) throw new Error('Prism no arrancó a tiempo.');
    await new Promise((resolve, reject) => { servidor.once('error', reject); servidor.listen(puerto, host, resolve); });
  } catch (error) { proceso.kill(); limpiar(); throw error; }
  if (!silencioso) console.log(`\nSimulador analítico: http://TU-IP:${puerto}\nPrism 5.14.2 interno: 127.0.0.1:${puertoPrism}\nleche + Guanajuato: resultados | inexistente + Guanajuato: vacío | leche + Colima: cobertura\nproblema + Guanajuato: problem+json | Ctrl+C: apagar ambos procesos\n`);
  return {
    puerto: servidor.address().port,
    async cerrar() {
      await new Promise(resolve => { servidor.close(resolve); servidor.closeIdleConnections(); });
      proceso.kill(); limpiar();
    },
  };
}
if (require.main === module) iniciarSimulador().then(simulador => {
  let cerrando = false;
  const cerrar = () => { if (!cerrando) { cerrando = true; void simulador.cerrar().then(() => process.exit(0)); } };
  process.on('SIGINT', cerrar); process.on('SIGTERM', cerrar);
}).catch(error => { console.error(error.message); process.exitCode = 1; });
module.exports = { iniciarSimulador };
