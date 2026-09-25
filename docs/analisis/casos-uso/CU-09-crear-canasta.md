# CU-09 · Crear y editar una canasta

- **Actor primario:** Persona consumidora
- **Interesados:**
  - Persona consumidora — quiere organizar artículos de interés en una canasta y mantener actualizadas sus cantidades.
  - Sistema — debe mantener la canasta consistente y evitar cantidades inválidas o artículos duplicados.
- **Precondiciones:**
  1. La persona consumidora tiene una cuenta registrada e inició sesión.
  2. El sistema puede identificar a la persona consumidora mediante su identificador.
- **Disparador:** La persona consumidora solicita crear una canasta nueva o modificar una canasta existente.

## Flujo principal

1. La persona consumidora solicita crear una canasta.
2. El sistema crea una canasta asociada a la persona consumidora.
3. La persona consumidora proporciona el nombre de la canasta.
4. El sistema registra el nombre de la canasta.
5. La persona consumidora selecciona un artículo y proporciona una cantidad para agregarlo a la canasta.
6. El sistema agrega el artículo con la cantidad indicada.
7. La persona consumidora solicita editar la canasta agregando o quitando artículos.
8. El sistema aplica las modificaciones solicitadas.
9. El sistema calcula el costo estimado de la canasta sin almacenarlo.
10. El sistema confirma que la canasta quedó actualizada.

## Flujos alternos

**6a · La cantidad indicada no es válida**
1. El sistema rechaza la cantidad porque no es un número entero mayor que cero.
2. El sistema solicita una cantidad válida.
3. La persona consumidora proporciona una nueva cantidad.
4. Vuelve al paso 6 del flujo principal.

**6b · El artículo ya existe en la canasta**
1. El sistema identifica que ya existe una línea para el artículo.
2. El sistema suma la nueva cantidad a la cantidad existente.
3. El sistema mantiene una sola línea para ese artículo.
4. Continúa en el paso 7 del flujo principal.

**8a · El artículo que se solicita quitar no existe en la canasta**
1. El sistema informa que el artículo no forma parte de la canasta.
2. La canasta permanece sin cambios.
3. Continúa en el paso 9 del flujo principal.

**8b · La modificación solicitada no puede aplicarse**
1. El sistema rechaza la modificación.
2. El sistema conserva la canasta en su último estado válido.
3. El caso de uso termina sin aplicar la modificación solicitada.

## Postcondiciones

- **De éxito:** La canasta queda asociada a su único usuario, contiene cantidades válidas y no presenta artículos duplicados. El costo estimado puede calcularse sin almacenarse.
- **De fallo:** La canasta conserva su último estado válido y no se registran cantidades inválidas ni modificaciones que no hayan podido aplicarse correctamente.

## Requisito no funcional asociado

- El sistema debe confirmar la creación o modificación de una canasta en un tiempo máximo de **2 segundos** bajo condiciones normales de operación.

## Notas

- La canasta pertenece a exactamente un usuario y no puede cambiar de dueño.
- Las líneas de la canasta solo pueden modificarse a través de la raíz `Canasta`.
- Al agregar un artículo que ya existe, se suma la cantidad en lugar de crear una línea duplicada.
- La identidad de un artículo se determina mediante producto + presentación.
- El costo estimado se calcula, pero no se almacena.
