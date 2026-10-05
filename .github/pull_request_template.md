<!--
Título de la solicitud, mismo formato que el commit:
  tipo(ámbito): descripción en presente

El título dice TODO lo que trae. Si trae dos temas, son dos solicitudes.

Tipos: feat · fix · docs · test · chore · refactor
Ámbitos en uso: datos · contrato · dominio · infra · mobile · web · analisis · equipo · adr · ci · repo
-->

## Qué cambia

<!-- En dos o tres líneas. Qué hace este cambio, no cómo lo hiciste. -->


## Cómo se probó

<!--
Concreto y verificable. Ejemplos:
  - Levanté docker compose up y entré a MinIO en localhost:9001
  - Corrí python -m pytest services/data-platform/tests -q, 8 pruebas en verde
  - Abrí el prototipo en Figma y verifiqué los tres puntos de quiebre
"No se probó" es una respuesta válida si aplica. Inventar que se probó, no.
-->


## Qué podría romper

<!--
Qué otro frente puede verse afectado. Si crees que nada, escribe por qué.
Ejemplo: cambia el nombre de la columna precio_unitario, así que la consulta
de la interfaz analítica deja de funcionar hasta que A la actualice.
-->


## Qué tiene que revisar quien revise

<!--
Lo mínimo que la otra persona tiene que mirar o correr para revisar con
confianza. Si no lo dices, revisa lo que alcance, y eso no es revisión.
Ejemplos:
  - Que cada par corregido cite su cláusula del ADR 004
  - Correr docker compose config con infra/envs/test/.env: nada repetido
  - Abrir docs/analisis/bpmn/ingesta.svg y que se lea completo
-->


---

Closes #

<!--
El número del issue arriba. Con esa línea, el issue se cierra solo al
incorporarse y la tarjeta se mueve sola en el tablero.
-->

### Antes de pedir revisión

- [ ] No hay contraseñas, tokens ni cadenas de conexión en el diff
- [ ] No hay archivos pesados (`node_modules/`, `.venv/`, `target/`, datos crudos)
- [ ] El criterio de aceptación del issue se cumple
- [ ] El título dice todo lo que trae la solicitud
- [ ] La integración continua está en verde
- [ ] Asigné un revisor y avisé en el chat

<!--
Al integrar: Squash and merge, conservando el (#N) que GitHub agrega al
título, y luego Delete branch. Si la revisión no llegó a tiempo, antes de
integrar deja un comentario con qué se comprobó y a quién se le pidió revisión
(docs/equipo/estrategia-de-ramas.md §5).
-->
