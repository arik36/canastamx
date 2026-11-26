const { verificarDirecciones } = require('./scripts/verificar-build.cjs');
module.exports = ({ config }) => {
  if (process.env.CANASTAMX_COMPILACION === 'entrega') verificarDirecciones(process.env);
  return {
    ...config,
    plugins: [...(config.plugins || []), ['expo-build-properties', { android: { usesCleartextTraffic: process.env.CANASTAMX_COMPILACION === 'validacion' } }]],
    ...(process.env.CANASTAMX_COMPILACION === 'validacion' ? { name: 'CanastaMX · Validación' } : {}),
  };
};
