const fs = require('node:fs');
const path = require('node:path');
// React Native 0.83.10 incluye Foojay 0.5.0, incompatible con su Gradle 9.
// Corrección upstream: https://github.com/reactwg/react-native-releases/issues/1349
// Foojay 1.0.0 elimina IBM_SEMERU, retirado en Gradle 9.
const paquete = require.resolve('@react-native/gradle-plugin/package.json');
const { version } = JSON.parse(fs.readFileSync(paquete, 'utf8'));
if (version === '0.83.10') {
  const archivo = path.join(path.dirname(paquete), 'settings.gradle.kts');
  const original = fs.readFileSync(archivo, 'utf8');
  const anterior = 'id("org.gradle.toolchains.foojay-resolver-convention").version("0.5.0")';
  const corregido = 'id("org.gradle.toolchains.foojay-resolver-convention").version("1.0.0")';
  if (original.includes(anterior)) {
    fs.writeFileSync(archivo, original.replace(anterior, corregido));
    console.log('Compatibilidad Android: Foojay 1.0.0 para Gradle 9 / RN 0.83.10.');
  } else if (!original.includes(corregido)) {
    throw new Error('Cambió la configuración de React Native; revisa la corrección de Foojay antes de compilar.');
  }
}
