# CU-14 · Revisar y resolver una variante en la cola de reconciliación

- **Actor primario:** operador de datos
- **Interesados:** 
  - **Operador de datos** — necesita limpiar las variantes ambiguas eficientemente sin alterar registros válidos.
  - **Analista** — necesita un catálogo de artículos normalizado para evitar duplicados en sus gráficas.
- **Precondiciones:** 
  1. El proceso de ingesta ha depositado variantes de artículos no reconocidas en la cola.
  2. El comparador automático calculó un porcentaje de similitud para cada variante.
- **Disparador:** El operador de datos accede a la cola de reconciliación para limpiar las retenciones del último lote.

## Flujo principal

1. El operador solicita abrir la cola de reconciliación.
2. El sistema presenta una lista de variantes de artículos originales junto con su porcentaje de similitud frente a una opción sugerida.
3. El operador evalúa la coincidencia sugerida basándose en la escritura y el gramaje.
4. El operador aprueba la coincidencia.
5. El sistema actualiza el diccionario vinculando la variante original al artículo canónico sugerido de forma permanente.

## Flujos alternos

**4a · El operador rechaza la coincidencia**
1. El operador determina que la sugerencia del sistema es incorrecta y la rechaza.
2. El sistema marca la variante como rechazada en el diccionario.
3. El caso de uso termina con éxito (resolución negativa).

**4b · El operador asigna la variante manualmente**
1. El operador indica que requiere realizar una asignación manual.
2. El sistema solicita la búsqueda del artículo en el catálogo.
3. El operador busca y selecciona el artículo canónico correcto.
4. El sistema actualiza el diccionario vinculando la variante al artículo seleccionado manualmente.
5. El caso de uso termina con éxito (resolución manual).

## Postcondiciones

- **De éxito:** La variante de artículo queda registrada en el diccionario, ya sea aprobada, asignada manualmente o rechazada definitivamente.
- **De fallo:** La variante permanece en estado pendiente dentro de la cola de reconciliación y no se actualiza el diccionario.

## Requisito no funcional asociado

- Un operador debe poder resolver y clasificar al menos 120 variantes por hora en la herramienta.

## Notas

- Este flujo se detona cuando el comparador automático no está seguro si dos escrituras distintas pertenecen al mismo artículo.
- Nunca se deben combinar gramajes distintos al resolver una variante.