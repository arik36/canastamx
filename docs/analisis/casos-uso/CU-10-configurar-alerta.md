# CU-10 · Configurar una alerta de precio

- **Actor primario:** Persona consumidora
- **Interesados:**
  - Persona consumidora — quiere recibir una alerta cuando el precio de un artículo alcance o sea menor al umbral establecido.
  - Sistema — debe validar que la alerta sea consistente con el historial de precios del artículo y conservar su configuración correctamente.
- **Precondiciones:**
  1. La persona consumidora tiene una cuenta registrada e inició sesión.
  2. Existe un artículo con un historial de precios disponible.
- **Disparador:** La persona consumidora solicita configurar una alerta de precio para un artículo.

## Flujo principal

1. La persona consumidora selecciona un artículo para el que desea configurar una alerta.
2. El sistema obtiene el historial de precios del artículo.
3. El sistema determina el rango histórico de precios del artículo.
4. La persona consumidora proporciona un umbral de precio.
5. El sistema valida que el umbral se encuentre dentro del rango histórico del artículo.
6. El sistema crea la alerta asociándola con el artículo, el usuario y el umbral indicado.
7. El sistema registra la alerta como activa.
8. El sistema confirma que la alerta quedó configurada correctamente.

## Flujos alternos

**2a · El historial de precios no está disponible**
1. El sistema informa que no existe información histórica suficiente para configurar la alerta.
2. El sistema no crea la alerta.
3. El caso de uso termina sin éxito.

**5a · El umbral está fuera del rango histórico**
1. El sistema rechaza el umbral proporcionado porque está fuera del rango histórico de precios del artículo.
2. El sistema informa el rango histórico permitido.
3. La persona consumidora proporciona un nuevo umbral.
4. Vuelve al paso 5 del flujo principal.

**6a · No es posible registrar la alerta**
1. El sistema informa que la alerta no pudo ser registrada.
2. El sistema no deja la alerta en estado activo.
3. El caso de uso termina sin éxito.

## Postcondiciones

- **De éxito:** La alerta queda registrada y activa, asociada al artículo, al usuario y al umbral configurado. La alerta se considera disparada cuando el precio observado sea menor o igual al umbral.
- **De fallo:** No se registra una alerta activa con un umbral inválido o cuando no existen datos históricos suficientes. Si ocurre un error al registrar la alerta, la configuración no queda parcialmente guardada.

## Requisito no funcional asociado

- El sistema debe validar y registrar una alerta en un tiempo máximo de **2 segundos** bajo condiciones normales de operación.

## Notas

- El umbral de precio debe encontrarse dentro del rango histórico del artículo.
- La alerta se dispara cuando el precio observado es menor o igual al umbral configurado.
- La alerta pertenece a un único usuario y referencia un artículo específico.
- La identidad del artículo se determina mediante producto + presentación.
