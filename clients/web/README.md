# Cliente web de CanastaMX

Las cinco vistas web (`docs/analisis/inventario-vistas.md`): acceso, tablero y detalle
para el analista; consola y cola para el operador. Next.js 16, React 19 y Tailwind 4
(ADR 021). Hace falta Node.js 20.9 o superior.

## Cómo se corre

```bash
cd clients/web
npm ci
cp .env.example .env.local      # DOMINIO_URL vacía = http://localhost:8081
npm run dev
```

Ábrela en **http://localhost:3000**, no en `127.0.0.1:3000`: Next 16 bloquea sus
recursos de desarrollo desde otro origen y la página queda sin JavaScript.

El acceso necesita el servicio de dominio corriendo (`services/domain-service`, desde
`main`) y una cuenta **ANALISTA** u **OPERADOR**. El registro sólo crea cuentas
`CONSUMIDOR`, que no entran a la web; las otras dos se crean por configuración (T045), y
todavía no hay un guion que lo haga.

## Cómo funciona la sesión

- `/api/login` llama a `POST /api/v1/sesiones` y guarda el token y el rol en cookies
  httpOnly que vencen con el token. El navegador nunca ve el token.
- `src/proxy.ts` manda cada rol a sus vistas: sin sesión, al acceso; el analista que
  escribe `/consola` vuelve al tablero. Es la regla de `src/lib/rutas.mjs`.
- Cada vista pide la cuenta a `GET /api/v1/cuentas/yo` (D-10) con `exigirCuenta()`:
  de ahí salen el correo y el rol de la barra lateral, nunca un nombre (P-13). Si el
  dominio no reconoce el token, o el rol no es el de la vista, la sesión se cierra.
- Ocultar una vista no es autorizar: las rutas de la analítica tienen que exigir su
  `x-rol` (`analitica.yaml`).

## Cómo se comprueba

```bash
npm test          # reglas de rol, llamadas al dominio y revisión de las vistas
npm run lint
```

A mano, con el dominio corriendo:

1. Entra como analista: abre el tablero y la barra muestra el correo y `ANALISTA`.
   Escribe `/consola` en la barra de direcciones: vuelves al tablero.
2. Entra como operador: abre la consola; `/tablero` escrito a mano no se abre.
3. En las herramientas de desarrollo, a 1024 px de ancho la consola avisa del ancho
   mínimo y se desplaza de lado; a 1025 px el aviso no aparece (D-08).
4. El acceso se ve completo a 360, 768 y 1280 px (`puntos-de-quiebre.md`).
5. Ninguna cifra en pantalla sin su población y su fecha (RNF-16). Hoy las vistas no
   muestran cifras; las del tablero llegan con T052 y, sin dato, dicen «se mide en T058».
6. «Salir», al pie de la barra lateral, te regresa al acceso sin cookies `token` ni `rol`;
   después, `/tablero` escrito a mano tampoco abre.
