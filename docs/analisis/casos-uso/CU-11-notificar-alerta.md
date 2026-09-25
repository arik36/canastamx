# CU-11 · Notificar cuando la alerta se dispara

- **Actor primario:** Proceso automático de alertas
- **Interesados:**
  - Persona consumidora — quiere recibir una notificación cuando el precio de un artículo alcance el umbral configurado.
  - Sistema — debe detectar las alertas disparadas y gestionar el envío de las notificaciones.
- **Precondiciones:**
  1. Existe una alerta configurada y activa.
  2. La alerta está asociada a una persona consumidora y a un artículo.
  3. Existe un precio observado del artículo para realizar la comparación.
- **Disparador:** El proceso automático de alertas revisa el precio observado de un artículo asociado a una alerta activa.

## Flujo principal

1. El proceso automático de alertas obtiene las alertas activas que deben ser revisadas.
2. El proceso obtiene el precio observado de cada artículo asociado a una alerta.
3. El proceso compara el precio observado con el umbral configurado.
4. El proceso identifica que el precio observado es menor o igual al umbral.
5. El proceso obtiene los datos necesarios para enviar la notificación a la persona consumidora.
6. El proceso envía la notificación por correo electrónico.
7. El proceso registra que la notificación fue enviada correctamente.

## Flujos alternos

**2a · No se puede obtener el precio observado**
1. El proceso no puede obtener un precio válido para el artículo.
2. El proceso no evalúa la alerta con información incompleta.
3. La alerta permanece disponible para una revisión posterior.
4. El proceso continúa con la siguiente alerta.

**4a · El precio observado es mayor al umbral**
1. El proceso determina que la condición de la alerta no se cumple.
2. El proceso no envía ninguna notificación.
3. La alerta permanece disponible para una revisión posterior.

**6a · El correo electrónico no puede enviarse**
1. El proceso detecta que el envío del correo electrónico falló.
2. El proceso conserva la alerta como pendiente de notificación.
3. El proceso registra el fallo para permitir un nuevo intento de envío.
4. El proceso continúa con la siguiente alerta.

## Postcondiciones

- **De éxito:** La persona consumidora recibe una notificación por correo electrónico y el sistema registra que la notificación fue enviada correctamente.
- **De fallo:** Si la notificación no puede enviarse, la alerta permanece pendiente de notificación y el fallo queda registrado para permitir un nuevo intento.

## Requisito no funcional asociado

- El proceso automático de alertas debe completar la evaluación y registrar el resultado de cada alerta en un tiempo máximo de **5 segundos** por alerta bajo condiciones normales de operación.

## Notas

- La persona consumidora es interesada en el caso de uso, pero no es el actor primario.
- La alerta se dispara cuando el precio observado es menor o igual al umbral configurado.
- Si el precio no cumple la condición, no se envía una notificación.
- Si el envío falla, la alerta no se pierde y queda pendiente para un nuevo intento.
