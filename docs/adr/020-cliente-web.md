# ADR 020 · El framework del cliente web: Next.js

- **Fecha:** 15 de octubre de 2026
- **Estado:** aceptada el 15 de octubre de 2026
- **Participantes:** D, dueña del cliente web

## Contexto

La tarjeta T047 exige estructurar el cliente web con acceso y navegación para las consolas de Analista y Operador. Para lograrlo, hay necesidades específicas:

1. **Ruteo seguro y roles:** El acceso debe validarse contra `POST /api/v1/sesiones` de C1. Dependiendo del rol en el token, se debe mandar al usuario al tablero (analista) o a la consola (operador).
2. **Control responsivo (D-08):** La consola no debe deformarse en pantallas menores a 1025 px, sino mostrar un aviso programado de ancho mínimo.
3. **El diseño ya existe:** El prototipo visual ya está terminado en Figma y herramientas automatizadas permiten exportarlo directamente.

## Decisión

Se decide construir el cliente web utilizando **Next.js** (alineado a la restricción R-07 del protocolo), programando los componentes y la navegación a mano.

## Alternativas descartadas

| Alternativa | Por qué no |
| :--- | :--- |
| **Vite exportado directo de Figma** | Aunque acelera la maquetación copiando el diseño exacto, el código generado carece de una arquitectura robusta. Es muy rígido para manejar el estado global, la seguridad de rutas por roles y la lógica de redirección que exige el sistema. |

## Consecuencias

- **Mayor esfuerzo inicial de maquetación:** Habrá que traducir el sistema de diseño (colores, componentes, tipografías) de Figma a código en Next.js paso a paso.
- **Se cumple R-07:** El protocolo y el README ya nombran a Next.js como la tecnología oficial de esta capa.
- **Control total de D-08:** Podremos programar el middleware o los *layouts* para interceptar los anchos menores a 1025 px y mostrar el aviso correctamente sin que colapse la interfaz.
