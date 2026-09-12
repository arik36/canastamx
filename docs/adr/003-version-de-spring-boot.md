# ADR 003 · Versión de Spring Boot


- **Fecha:** 11 Septiembre 2026
- **Estado:** aceptada
- **Participantes:** Lisseth Lara

## Contexto

Spring Initializr ofrece versiones 3.x y 4.x de Spring Boot. Para el servicio de dominio se utiliza Spring Boot 4.1.1 con Java 21.

## Decisión
Se utilizará Spring Boot 4.1.1 con Java 21 para `domain-service`.

## Alternativas descartadas



| Alternativa | Por qué no |
|---|---|
| Boot 3.x | Más tutoriales disponibles, pero soporte más corto. |

## Consecuencias
Los ejemplos de internet escritos para 3.x no aplican tal cual; las rutas de paquete de autoconfiguración cambiaron.


