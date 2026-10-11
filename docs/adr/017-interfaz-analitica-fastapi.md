# ADR 017 · La interfaz analítica en FastAPI

- **Fecha:** 11 de octubre de 2026
- **Estado:** aceptada el 11 de octubre de 2026. Documenta una decisión ya tomada, registrada en `docs/equipo/decisiones-pendientes.md` §«Por escribir»
- **Participantes:** A, dueña del frente de datos. B firma la parte de infraestructura

## Contexto

`docs/analisis/openapi/analitica.yaml` 0.2.1 publica **19 rutas** y las deja atadas a
convenciones que se votaron el 7 de octubre: `camelCase` (P-01), dinero como texto
con su moneda y nunca en punto flotante (P-02), `application/problem+json` (P-03),
`/api/v1` (P-04), `limit` y `offset` (P-05), y la entidad sin cobertura como
respuesta normal (P-06). Cada ruta protegida declara en `x-rol` qué rol pide (P-07).

El servicio que las sirve lee la capa de consumo y **nunca escribe en ella**
(RNF-14). Todo lo que la toca ya es Python: la ingesta, las transformaciones y la
reconciliación. El servicio de dominio es Java y, por RNF-14 y P-08, no entra ahí.

Lo que hace falta decidir es con qué se implementan esas 19 rutas sin que las seis
convenciones se vigilen a mano, una por una, en cada respuesta.

## Decisión

**Se usa FastAPI con Pydantic**, en `services/analytics-api/`.

1. **Los modelos de Pydantic son las convenciones.** `camelCase` sale del alias del
   modelo, no de recordar escribirlo; el dinero sale de un modelo `Dinero` con
   `monto` como cadena y `moneda`, que es la única forma de que P-02 no se rompa en
   la primera suma; `problem+json` sale de un manejador de errores, una vez.
2. **El contrato publicado manda.** FastAPI genera su propio OpenAPI; ese documento
   se compara contra `analitica.yaml` y la diferencia es un fallo, no una nota. Es
   la misma idea que el proyecto investiga —un contrato que se verifica solo—
   aplicada a la API en lugar de a los datos.
3. **`x-rol` se implementa como una dependencia** que lee el token que emite el
   dominio (P-07). El rol viaja en el token; la analítica no tiene cuentas.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| **Flask** | No trae modelos ni genera OpenAPI. Las seis convenciones quedarían vigiladas a mano en 19 rutas, que es la forma conocida de que se desincronicen del contrato |
| **Django REST Framework** | Trae ORM, migraciones y panel de administración que este servicio no usa, porque sólo lee. Pesa de más en los 12 GB del ADR 008 |
| **Servir la analítica desde el mismo Spring Boot del dominio** | Rompe RNF-14 y P-08: el dominio escribe en la base transaccional y la analítica sólo lee la de consumo. Además mete Java en la única capa donde todo lo demás es Python |
| **Exponer la base de consumo directamente al cliente web** | Sin capa no hay roles, ni paginación, ni cobertura declarada, ni forma de cambiar el esquema sin romper al consumidor |

## Consecuencias

- **La comparación contra `analitica.yaml` se puede automatizar** en la integración
  continua, junto al `redocly lint` que todavía falta agregar.
- **Es un cuarto contenedor** en la máquina del ADR 008. B lo considera al declarar
  el reparto de memoria.
- **El `x-rol` depende de que el dominio emita el token con el rol** (P-07), que es
  trabajo de C1. Si eso se atrasa, las 19 rutas se pueden construir, pero las
  protegidas no se pueden probar de punta a punta.
- **Las dos rutas que el dominio consulta** (rango histórico y precios vigentes,
  P-09) salen de este mismo servicio: son de sólo lectura y no requieren rol.
