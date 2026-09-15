# ADR 007 · Navegación móvil con pestañas y pila

- **Fecha:** 15 de septiembre de 2026
- **Estado:** propuesta, pendiente de revisión del equipo
- **Participantes:** Oscar (C2); revisión pendiente

## Contexto

T014 dejó la base de Expo SDK 55 y dos pantallas. La tarea de navegación de
la semana 2 requiere cuatro pantallas vacías. El ADR 002 establece el término
«artículo» para la combinación de producto y presentación.

## Decisión

Se utiliza Expo Router, ya instalado, con tres pestañas: Búsqueda, Mi canasta
y Alertas. Una pila raíz contiene esas pestañas y la ruta dinámica
`/articulo/[id]`. El detalle se abre desde Búsqueda y permite regresar mediante
la flecha del encabezado o el botón/gesto Atrás de Android.

Los componentes se llaman `BusquedaDeArticulos`, `DetalleDeArticulo`,
`MiCanasta` y `Alertas`. Cada pantalla contiene su título; Búsqueda incluye
además el botón temporal requerido para probar el detalle. Su identificador
`prueba` sirve únicamente para recorrer la ruta, no representa datos del catálogo
ni define la futura clave de artículo del servicio.

## Alternativas descartadas

- Cuatro pestañas: el detalle depende de la selección en Búsqueda, no es
  una sección hermana.
- Enlaces desde Búsqueda hacia Canasta y Alertas: la ficha exige acceso por
  pestañas.
- Incorporar datos, filtros o llamadas al servicio: pertenecen a tareas futuras.

## Consecuencias

Se conservan Node 20, Expo SDK 55 y las dependencias de T014. Las rutas previas
`/` y `/canasta` conservan su URL al moverse al grupo `(tabs)`.
El sistema de diseño se aplicará en T028. La evidencia de cierre debe recorrer
las cuatro pantallas en un teléfono real y adjuntarse al issue de esta tarea.

Referencias: [ADR 002](002-identidad-del-articulo.md),
[ADR 006](006-entorno-mobile-expo.md),
[pestañas de Expo Router](https://docs.expo.dev/router/advanced/tabs/).