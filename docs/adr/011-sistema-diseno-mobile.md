# ADR 011 · Aplicación del sistema de diseño al móvil

- **Fecha:** 25 de septiembre de 2026
- **Estado:** propuesta, pendiente de revisión del equipo
- **Participantes:** Oscar (C2); revisión pendiente

## Contexto

T028 requiere aplicar a las cuatro pantallas vacías el sistema de diseño de D,
documentado en [diseño.md](../entregas/diseño.md). Se conserva la navegación de
T023, el vocabulario del ADR 002 y Expo Go para SDK 55.

## Decisión

Se centralizan colores, tipografía, tamaños, radios y espaciados en
`clients/mobile/theme/design-system.ts`. Las cuatro pantallas comparten
`PantallaVacia`, con fondo crema, texto tinta, título de 24 y márgenes de 24.
El botón de prueba y la pestaña seleccionada usan turquesa con texto tinta.
El botón tiene radio de 12 y los espaciados son múltiplos de cuatro.

Inter Regular y SemiBold se incluyen mediante `@expo-google-fonts/inter` y
se cargan con `useFonts` de `expo-font` antes de mostrar la navegación.
Se utilizan archivos estáticos incluidos en el paquete, sin descargar fuentes
desde Google durante el uso de la app. Regular y SemiBold son pesos elegidos
para esta implementación; D especifica la familia, pero no los pesos.

Los valores de tamaño se expresan en unidades lógicas de React Native,
con escalado de texto del sistema habilitado. No se agregan contenidos,
servicios ni operaciones de negocio.

## Alternativas descartadas

- Declarar únicamente `fontFamily: "Inter"`: no instala la fuente en Android.
- Integrar fuentes solo mediante un plugin nativo: requeriría una compilación
  propia; la entrega se prueba en Expo Go.
- Copiar estilos independientes en cada pantalla: facilitaría diferencias
  accidentales respecto a la especificación común.

## Consecuencias

Se añade una dependencia de fuentes y se actualiza su archivo de bloqueo.
Las pantallas esperan a que cargue Inter. Se conserva la lógica de navegación.

Verde queda reservado para éxito. No se usan rojo ni naranja porque no hay
estados de fallo ni anomalías de mercado; sus códigos no están definidos
en la especificación. Tampoco se agregan tarjetas ni modales para demostrar
radios que esta tarea no necesita.

La aceptación exige revisar la apariencia y grabar el recorrido en teléfono real.

Referencias: [ADR 007](007-navegacion-mobile.md),
[fuentes en Expo](https://docs.expo.dev/develop/user-interface/fonts/).