# ADR 007 · Navegación móvil con cuatro pestañas y pila

- **Fecha:** 15 de septiembre de 2026
- **Ratificación:** 15 de octubre de 2026
- **Estado:** aceptada
- **Participantes:** Oscar (C2); decisión D-01 acordada por C2 y D el 6 de octubre de 2026

## Contexto

T014 dejó la base de Expo SDK 55 y T023 incorporó la navegación inicial. El
6 de octubre de 2026, C2 y D acordaron en D-01 utilizar las cuatro pestañas del
prototipo: Inicio, Descubrir, Canasta y Cuenta. Esta decisión sustituye la
propuesta de tres pestañas de este ADR y se describe en
[navegacion.md](../analisis/navegacion.md). El ADR 002 establece el término
«artículo» para la combinación de producto y presentación.

## Decisión

Se utiliza Expo Router con cuatro pestañas hermanas, en este orden: **Inicio,
Descubrir, Canasta y Cuenta**. Las rutas del grupo `(tabs)` son `index`,
`descubrir`, `canasta` y `cuenta`. Inicio contiene la búsqueda de artículos;
Descubrir corresponde al panorama y a la sección «Precios que bajaron»;
Canasta reúne las canastas de la persona; Cuenta reúne el acceso a la sesión,
el perfil y las opciones de la cuenta, según `navegacion.md`.

Una pila raíz contiene el grupo de pestañas, el detalle de artículo
`/articulo/[id]` y **Mis alertas** en `/alertas`. El detalle se abre desde
Inicio o Descubrir y se cierra mediante la flecha del encabezado o el
botón/gesto Atrás de Android. No ocupa una pestaña propia.

Mis alertas se abre desde la campana de la barra superior o desde Cuenta y
permite regresar mediante la pila. Su archivo queda fuera de `(tabs)`;
la URL `/alertas` se conserva porque los grupos entre paréntesis no forman
parte de la URL. El título de regreso a Inicio sustituye a «Búsqueda».

Esta decisión fija la navegación. La incorporación de la pantalla de acceso,
los datos y las llamadas a servicios se realiza en sus tareas correspondientes.
El identificador temporal `prueba` del botón de detalle sólo permite recorrer
la ruta; no representa un artículo del catálogo ni define su identidad futura.

## Alternativas descartadas

- Mantener Búsqueda, Mi canasta y Alertas como tres pestañas: contradice D-01,
  omite Descubrir y Cuenta y deja la sesión sin su sección de destino.
- Usar el detalle de artículo como una cuarta pestaña: depende de un artículo
  seleccionado y pertenece a la pila, no a una sección hermana.
- Mantener Mis alertas en la barra inferior: D-01 establece su acceso desde
  la campana y Cuenta, y reserva la barra para las cuatro secciones acordadas.
- Sustituir las pestañas por enlaces desde Inicio: dificultaría el acceso
  directo y persistente a Descubrir, Canasta y Cuenta.

## Consecuencias

La implementación debe declarar cuatro `Tabs.Screen`, renombrar Búsqueda como
Inicio, crear Descubrir y Cuenta y mover Mis alertas a la pila raíz. Las rutas
`/`, `/canasta` y `/alertas` conservan su URL; se incorporan `/descubrir` y
`/cuenta`. Deben actualizarse las importaciones al mover el archivo de alertas.

Se conservan Node 20, Expo SDK 55 y el sistema de diseño del ADR 011. Las
pantallas mantienen el alcance de cada tarea; esta ratificación no introduce
operaciones de negocio ni una implementación de sesión.

La verificación en Android debe recorrer las cuatro pestañas, abrir y cerrar
el detalle, y entrar y regresar de Mis alertas desde la campana y Cuenta.
Cuenta queda disponible antes de implementar el acceso; la primera llamada
real de T039 se muestra en Inicio.

Referencias: [ADR 002](002-identidad-del-articulo.md),
[ADR 006](006-entorno-mobile-expo.md),
[ADR 011](011-sistema-diseno-mobile.md),
[D-01](../equipo/decisiones-pendientes.md),
[navegación acordada](../analisis/navegacion.md).
