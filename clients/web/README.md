# Cliente web de CanastaMX

Las cinco vistas web (`docs/analisis/inventario-vistas.md`): acceso, tablero y detalle
para el analista; consola y cola para el operador. Next.js 16, React 19 y Tailwind 4
(ADR 022). Hace falta Node.js 20.9 o superior.

## Cómo se corre

```bash
cd clients/web
npm ci
cp .env.example .env.local      # DOMINIO_URL vacía = http://localhost:8081
npm run dev                     # ANALITICA_URL vacía = el simulador, abajo
```

Ábrela en **http://localhost:3000**, no en `127.0.0.1:3000`: Next 16 bloquea sus
recursos de desarrollo desde otro origen y la página queda sin JavaScript.

El acceso necesita el servicio de dominio corriendo (`services/domain-service`, desde
`main`) y una cuenta **ANALISTA** u **OPERADOR**. El registro sólo crea cuentas
`CONSUMIDOR`, que no entran a la web. Las otras dos las crea el guion de semilla, desde
la raíz del repositorio y después de arrancar el dominio una vez, para que Flyway cree
la tabla (en Windows, desde Git Bash):

```bash
bash infra/scripts/sembrar-cuentas.sh
```

Crea `analista@canastamx.mx` y `operador@canastamx.mx`, con la `SEMILLA_CONTRASENA`
del `.env` de la raíz.

Si el acceso funciona pero cada vista truena con «GET …/api/v1/cuentas/yo respondió
404», el dominio que corre es anterior a #184: córrelo desde `main`. El simulador del
contrato no sirve para entrar (`.env.example`).

El tablero y la consola leen la interfaz analítica: el tablero, `GET /api/v1/anomalias`;
la consola, las seis rutas de operación (`/operacion/estado`, `/corridas`,
`/corridas/{lote}`, `/cuarentena`, `/incidentes` y el cierre). Con `ANALITICA_URL`
vacía las pide al simulador del contrato, que se levanta desde la raíz:

```bash
npx @stoplight/prism-cli@5.14.2 mock -p 4011 -v debug docs/analisis/openapi/analitica.yaml
```

Con `-v debug`, el registro de Prism muestra el encabezado `authorization: Bearer …` de
cada llamada. El simulador contesta ejemplos: la consola sale en verde, con ceros, y su
único registro es un aviso, que no se cierra. Para cerrar un incidente hace falta la
interfaz de verdad.

Para la interfaz de verdad (`services/analytics-api`, desde `main`),
`ANALITICA_URL=http://localhost:8000`. Necesita el mismo `JWT_SECRET` que el dominio, o
contesta 401. El tablero pide datos en la capa de consumo, y la consola, corridas en el
esquema de operación. Para cerrar un incidente, la analítica le pregunta al dominio
quién cierra (D-11): su `DOMINIO_URL` tiene que alcanzarlo.

### La consola

- Arriba, la respuesta de los tres segundos (CU-05 · 3): verde si la última corrida fue
  correcta y no hay incidentes abiertos; rojo si hay un incidente abierto, si la última
  corrida se rechazó o falló, o si la frescura bloquea; azul si sólo hay avisos. Los
  avisos de esquema no la cambian: informan y no se cierran (RF-13).
- Los seis indicadores de CU-05, cada uno con su población y su fecha (RNF-16).
- Los incidentes abiertos, cada uno con «Cerrar con causa» (CU-04). El cierre corre en
  el servidor de la web (`src/app/consola/acciones.ts`), con el token de la cookie;
  quien autoriza es la analítica. Si falla, el motivo sale junto al formulario y lo
  escrito se queda.
- El historial de avisos e incidentes, las corridas, y el linaje y la cuarentena del
  lote que se elija (por omisión, el de la última corrida).
- Todo lo que pide y revisa está en `src/lib/operacion.mjs`, con sus pruebas.

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
npm test          # reglas de rol, llamadas al dominio y a la analítica, y las vistas
npm run lint
```

A mano, con el dominio y el simulador (o la analítica) corriendo:

1. Entra como analista: abre el tablero y la barra muestra el correo y `ANALISTA`.
   Escribe `/consola` en la barra de direcciones: vuelves al tablero.
2. Entra como operador: abre la consola; `/tablero` escrito a mano no se abre.
3. En las herramientas de desarrollo, a 1024 px de ancho la consola avisa del ancho
   mínimo y se desplaza de lado; a 1025 px el aviso no aparece (D-08).
4. El acceso se ve completo a 360, 768 y 1280 px (`puntos-de-quiebre.md`).
5. Ninguna cifra en pantalla sin su población y su fecha (RNF-16). En el tablero, cada
   variación lleva su entidad, su quincena y sus observaciones, y arriba de la tabla va
   la población de la respuesta: observaciones, entidades y quincenas. En la consola,
   cada indicador dice de qué corridas sale y hasta qué fecha, y cada lista cuántos
   renglones muestra de cuántos hay.
6. Con el simulador, el tablero y la consola avisan que sus cifras son ejemplos; con
   `ANALITICA_URL` en la analítica de verdad, ese aviso no sale. Con la analítica
   apagada, avisan que no la pudieron leer y la vista sigue en pie.
7. Con la analítica de verdad y un incidente abierto, la consola sale en rojo. «Cerrar
   con causa» lo cierra: sale el aviso verde y el historial lo trae con su causa, su
   decisión, quién lo cerró y cuándo. Si alguien lo cerró antes, el formulario dice
   «respondió 409» y conserva lo escrito.
8. «Salir», al pie de la barra lateral, te regresa al acceso sin cookies `token` ni `rol`;
   después, `/tablero` escrito a mano tampoco abre.
