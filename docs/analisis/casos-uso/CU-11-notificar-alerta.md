# CU-11 · Notificar cuando la alerta se dispara

* **Actor primario:** Proceso automático de alertas

* **Interesados:**

  * Persona consumidora — quiere recibir una notificación cuando el precio de un artículo alcance el umbral configurado.
  * Sistema — debe detectar las alertas disparadas y gestionar el envío y registro de las notificaciones.

* **Precondiciones:**

  1. Existe una alerta configurada y activa.
  2. La alerta está asociada a una persona consumidora y a un artículo.
  3. Existe un precio observado del artículo para realizar la comparación.

* **Disparador:** El proceso automático de alertas revisa el precio observado de un artículo asociado a una alerta activa.

## Flujo principal

1. El proceso automático de alertas obtiene las alertas activas que deben ser revisadas.
2. El proceso obtiene el precio observado de cada artículo asociado a una alerta.
3. El proceso compara el precio observado con el umbral configurado.
4. El proceso evalúa si el precio observado es menor o igual al umbral configurado.
5. Si el precio observado es menor o igual al umbral **y en la revisión anterior estaba por encima, o es su primera revisión**, el proceso obtiene los datos necesarios para enviar la notificación a la persona consumidora.
6. El proceso envía la notificación por correo electrónico.
7. El proceso registra la notificación con estado **ENVIADA**.
8. El proceso registra que la alerta quedó **debajo** del umbral, la quincena de la revisión y la del cruce, y la mantiene activa para que pueda ser evaluada nuevamente en la siguiente revisión quincenal.

## Flujos alternos

**2a · No se puede obtener el precio observado**

1. El proceso no puede obtener un precio válido para el artículo.
2. El proceso no evalúa la alerta con información incompleta.
3. La alerta permanece disponible para una revisión posterior.
4. El proceso continúa con la siguiente alerta.

**4a · El precio observado es mayor al umbral**

1. El proceso determina que la condición de la alerta no se cumple.
2. El proceso no envía ninguna notificación.
3. El proceso registra que la alerta quedó **arriba** del umbral: si en una revisión posterior vuelve a bajar, avisa otra vez.
4. La alerta permanece activa para una revisión posterior.
5. El proceso continúa con la siguiente alerta.

**5a · El precio ya estaba debajo del umbral en la revisión anterior**

1. El proceso no envía una notificación nueva: ya avisó cuando el precio cruzó.
2. Si la notificación de ese cruce quedó **FALLIDA** o **PENDIENTE**, el proceso la reintenta: el reintento no es un aviso nuevo.
3. La alerta sigue activa y debajo del umbral.
4. El proceso continúa con la siguiente alerta.

**6a · El correo electrónico no puede enviarse**

1. El proceso detecta que el envío del correo electrónico falló.
2. El proceso registra la notificación con estado **FALLIDA**.
3. El proceso registra el motivo del fallo para permitir un nuevo intento de envío.
4. El proceso conserva la alerta pendiente de notificación.
5. El proceso continúa con la siguiente alerta.

## Postcondiciones

* **De éxito:** La persona consumidora recibe una notificación por correo electrónico, la notificación queda registrada con estado **ENVIADA** y la alerta permanece activa: volverá a avisar sólo si el precio sube por encima del umbral y vuelve a cruzarlo hacia abajo.

* **De fallo:** La notificación queda registrada con estado **FALLIDA**, el fallo queda registrado y la alerta permanece pendiente de notificación para permitir un nuevo intento de envío.

## Requisito no funcional asociado

* El proceso automático de alertas debe completar la evaluación y registrar el resultado de cada alerta en un tiempo máximo de **5 segundos** por alerta bajo condiciones normales de operación.

## Registro de notificaciones

Cada intento de envío debe generar un registro de notificación asociado a la alerta correspondiente. El registro debe permitir conocer el resultado del intento mediante un estado.

Estados considerados:

* **PENDIENTE** — notificación pendiente de envío o reintento.
* **ENVIADA** — notificación enviada correctamente.
* **FALLIDA** — el intento de envío no fue exitoso.

El registro debe conservar, como mínimo, el identificador de la alerta, la fecha y hora del intento, el estado de la notificación y, cuando corresponda, el motivo del fallo.

## Decisión sobre el ciclo de vida de la alerta

Una alerta que genera una notificación **no se desactiva ni se marca como disparada de forma permanente**. La alerta permanece **activa**, recuerda si quedó arriba o debajo del umbral, y vuelve a generar una notificación sólo cuando el precio cruza el umbral hacia abajo otra vez (D-05, 6 de octubre de 2026).

## Notas

* La persona consumidora es interesada en el caso de uso, pero no es el actor primario.
* La alerta se dispara cuando el precio observado es menor o igual al umbral configurado, **y sólo al cruzarlo**: no repite mientras el precio siga abajo, y se vuelve a armar cuando sube (D-05, 6 de octubre de 2026).
* Además del correo, la app muestra los precios que bajaron. Está en `docs/analisis/navegacion.md` §3.
* Si el precio no cumple la condición, no se envía una notificación y la alerta permanece activa para una revisión posterior.
* Una notificación exitosa se registra con estado **ENVIADA**.
* Si el envío falla, la notificación se registra con estado **FALLIDA** y la alerta permanece pendiente de notificación para un nuevo intento.
* Después de una notificación exitosa, la alerta permanece activa y no vuelve a notificar mientras el precio siga debajo del umbral.
