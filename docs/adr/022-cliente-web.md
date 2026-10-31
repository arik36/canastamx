# ADR 022 · El framework del cliente web: Next.js

- **Fecha:** 15 de octubre de 2026
- **Estado:** aceptada el 15 de octubre de 2026
- **Participantes:** D, dueña del cliente web
- **Número:** se escribió como 020 el 15 de octubre, en el PR #176. Pasó a 021 porque el
  ADR 020, el del token de sesión, entró antes a `main` (#185), y a 022 porque el ADR 021,
  el de la persistencia de la sesión en el cliente móvil, también entró antes (#195).

## Contexto

La tarjeta T047 exige estructurar el cliente web con acceso y navegación para las consolas de Analista y Operador. Para lograrlo, hay necesidades específicas:

1. **Ruteo seguro y roles:** El acceso debe validarse contra `POST /api/v1/sesiones` de C1. Dependiendo del rol en el token, se debe mandar al usuario al tablero (analista) o a la consola (operador).
2. **Control responsivo (D-08):** La consola no debe deformarse en pantallas menores a 1025 px, sino mostrar un aviso programado de ancho mínimo.
3. **El diseño ya existe:** El prototipo visual ya está terminado en Figma y herramientas automatizadas permiten exportarlo directamente.

## Decisión

Se decide construir el cliente web utilizando **Next.js (v16.4.2), React (v19.3) y Tailwind CSS (v4)** (alineado a la restricción R-07 del protocolo), programando los componentes y la navegación a mano. `next` 16.4.2 pide **Node.js 20.9
o superior**, en las máquinas del equipo y en la del despliegue.

## Alternativas descartadas

| Alternativa | Por qué no |
| :--- | :--- |
| **Vite exportado directo de Figma** | Aunque acelera la maquetación copiando el diseño exacto, el código generado carece de una arquitectura robusta. Es muy rígido para manejar el estado global, la seguridad de rutas por roles y la lógica de redirección que exige el sistema. |

## Consecuencias

- **Mayor esfuerzo inicial de maquetación:** Habrá que traducir el sistema de diseño (colores, componentes, tipografías) de Figma a código en Next.js paso a paso.
- **Se cumple R-07:** El protocolo y el README ya nombran a Next.js como la tecnología oficial de esta capa.
- **La sesión la decide el dominio, no la web:** la web guarda el token de
  `POST /api/v1/sesiones` en una cookie httpOnly que vence con él, y en cada vista
  pregunta la cuenta a `GET /api/v1/cuentas/yo` (D-10): de ahí salen el correo y el
  rol que se muestran y que deciden la vista. La web no verifica la firma (ADR 020) y
  ocultar una vista no sustituye la autorización: la analítica tiene que exigir el
  rol de `x-rol` en sus rutas (`analitica.yaml`).
- **Control total de D-08 mediante CSS:** Aunque el middleware de Next.js protege las rutas, este corre en el servidor y no conoce el ancho de la ventana. La responsividad y el aviso se controlarán estrictamente mediante CSS.
- **Impacto en infraestructura:** Correr el servidor de Node.js para Next consumirá recursos en la máquina definida en el ADR 008, lo que incrementa ligeramente el costo computacional frente a servir puros archivos estáticos.