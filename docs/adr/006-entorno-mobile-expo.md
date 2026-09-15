# ADR 006 · Entorno móvil de T014

- **Fecha:** 8 de septiembre de 2026
- **Estado:** propuesta, pendiente de revisión del equipo
- **Participantes:** Oscar (C2), autor de T014; revisión pendiente

## Contexto

T014 exige Node 20, TypeScript, Expo y navegación entre dos pantallas. La computadora de desarrollo tiene Node 24.14.0. SDK 55 admite Node 20, mientras SDK 57 requiere Node 22.13.x. El diagnóstico oficial detectó en SDK 56 una regresión de memoria de Hermes V1 cuya corrección se distribuye con SDK 57.

## Decisión

La implementación propuesta utiliza Node 20.20.2, Expo SDK 55 y Expo Router. Se fija Node en `.nvmrc`, se declara su intervalo en `package.json` y se conservan las dependencias resueltas en `package-lock.json`. En Android se usa Expo Go compatible con SDK 55.

Se crean las rutas `/` (Búsqueda) y `/canasta` (Mi canasta), siguiendo el alcance de T014. Las otras pantallas se incorporarán en las tareas posteriores.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Usar la plantilla más reciente sin fijar SDK | SDK 57 requiere una versión de Node distinta de la exigida en T014. |
| Usar SDK 56 | El diagnóstico oficial señala una regresión de Hermes V1. SDK 55 permite cumplir Node 20 sin utilizar esa versión de Hermes. |
| Usar Node 24 para esta entrega | No cumple el criterio explícito `node -v` igual a `v20.x`; cambiarlo requiere acuerdo del equipo. |
| Configurar React Native sin Expo | La ficha ya establece Expo y Router como base del cliente móvil. |

## Consecuencias

Oscar debe usar Node 20 en la sesión de desarrollo y una versión compatible de Expo Go en Android. La instalación portable local permite mantener la versión de Node que ya tenía la computadora. El equipo deberá revisar este ADR y acordar futuras actualizaciones del entorno. La ejecución en teléfono y la evidencia del issue siguen siendo necesarias para cerrar T014.

Fuentes: [compatibilidad de SDK](https://docs.expo.dev/versions/latest/), [Expo Go para SDK 55](https://expo.dev/go?sdkVersion=55&platform=android&device=true), [dependencias de SDK 55](https://github.com/expo/expo/blob/sdk-55/packages/expo/bundledNativeModules.json), [regresiones de Hermes](https://expo.dev/changelog/sdk-57#known-regressions).
