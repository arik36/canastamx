# ADR 020 · El token de sesión entre el dominio y la analítica

- **Fecha:** 23 de octubre de 2026
- **Estado:** propuesta. El dominio ya lo aplica; falta que A lo ratifique para la
  analítica (ADR 017), que todavía no verifica tokens.
- **Participantes:** C1, que emite el token; A, que lo verifica para `x-rol`; B, por
  la integración continua y el `.env`

## Contexto

- `JwtService` firmaba con `signWith(clave)`, y JJWT elige el algoritmo por el largo
  de la clave. Medido el 23 de octubre con JJWT 0.13.0: un `JWT_SECRET` de 32 a 47
  bytes firmaba HS256; de 48 a 63, HS384; de 64 o más, HS512. El verificador aceptaba
  cualquiera de los tres.
- La clave eran los bytes del **texto** de `JWT_SECRET`, no lo que ese texto codifica:
  `openssl rand -base64 32` daba una clave de 44 bytes, y `openssl rand -hex 32`, una
  de 64, que firmaba HS512.
- El ADR 017 dice que `x-rol` «lee el token que emite el dominio», pero ningún
  documento fijaba algoritmo, clave ni claims. PyJWT exige declarar el algoritmo al
  verificar: con HS256 fijo en la analítica y una clave larga en el dominio, toda ruta
  protegida respondería 401 en esa máquina, y en la CI, que usa 44 bytes, no.

## Decisión (propuesta)

- **Algoritmo:** HS256, y sólo HS256, al firmar y al verificar.
- **Clave:** `JWT_SECRET` es Base64 estándar (RFC 4648 §4) de 32 bytes aleatorios, y la
  clave son esos 32 bytes decodificados. El dominio no arranca con otra cosa, y el
  mensaje de error no muestra el valor.
- **Claims obligatorios:** `sub` (el `id` de la cuenta), `rol` (P-07), `iat` y `exp`,
  sin tolerancia de reloj. Un token al que le falte uno se rechaza.
- **Dónde queda:** `dominio.yaml` 0.2.2, `components.securitySchemes.sesion`, y este
  ADR. La analítica lo cita en el suyo.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| **Que el largo de la clave elija el algoritmo** | Es lo que había: dos máquinas con el mismo código firman distinto, y la analítica tendría que aceptar tres algoritmos para no fallar |
| **Usar el texto de `JWT_SECRET` como clave** | Confunde el texto con la clave: su fuerza depende de cómo se escribió, no de cuántos bytes aleatorios tiene |
| **RS256 o EdDSA, con clave pública para la analítica** | La analítica no podría firmar tokens, y eso es mejor. Pero son dos claves que generar, guardar y rotar, y otra dependencia en Python. Se reconsidera si la analítica deja de vivir junto al dominio (ADR 008) |

## Consecuencias

- **Transición:** los tokens emitidos antes del cambio dejan de valer, porque se
  firmaron con otra clave, y quien tenga sesión abierta vuelve a entrar. Duran 60
  minutos (`JWT_EXPIRATION_MINUTES`), así que el efecto dura una hora.
- Un `JWT_SECRET` que no sea Base64 de 32 bytes detiene el arranque con un mensaje que
  dice cómo generarlo. `openssl rand -base64 32`, que es lo que ya usa la CI, cumple.
- Con HS256 la analítica guarda la misma clave que el dominio: puede verificar tokens,
  y también podría firmarlos. Se acepta mientras las dos vivan en la misma máquina y
  la misma CI.
- **Falta:** que A lo ratifique, y que la analítica (T058) verifique con
  `algorithms=["HS256"]`, la misma clave decodificada y los mismos claims.
