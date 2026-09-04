<!--
Título de la solicitud, mismo formato que el commit:
  tipo(ámbito): descripción en presente

Tipos: feat · fix · docs · test · chore · refactor
Ámbitos: data · infra · domain · mobile · web · docs · ci
-->

## Qué cambia

<!-- En dos o tres líneas. Qué hace este cambio, no cómo lo hiciste. -->


## Cómo se probó

<!--
Concreto y verificable. Ejemplos:
  - Levanté docker compose up y entré a MinIO en localhost:9001
  - Corrí pytest services/data-platform/tests/, 14 pruebas en verde
  - Abrí el prototipo en Figma y verifiqué los tres puntos de quiebre
"No se probó" es una respuesta válida si aplica. Inventar que se probó, no.
-->


## Qué podría romper

<!--
Qué otro frente puede verse afectado. Si crees que nada, escribe por qué.
Ejemplo: cambia el nombre de la columna precio_unitario, así que la consulta
de la interfaz analítica deja de funcionar hasta que A la actualice.
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
- [ ] La integración continua está en verde
- [ ] Asigné un revisor y avisé en el chat
