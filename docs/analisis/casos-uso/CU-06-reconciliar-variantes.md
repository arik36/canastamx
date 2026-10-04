# CU-06 · Reconciliar las variantes de un artículo

- **Actor primario:** el proceso de transformación de la capa de consumo (actor
  automático)
- **Interesados:**
  - **Analista** — necesita la serie histórica completa de un artículo, no partida
    entre sus variantes de escritura.
  - **Consumidor de la app** — al buscar un producto espera una sola entrada, no
    tres casi iguales.
  - **Operador de datos** — los casos dudosos tienen que llegarle a su cola
    (CU-14), no resolverse solos.
- **Precondiciones:**
  1. `dim_articulo` está cargada (T031).
  2. La regla de calificación del ADR 004 (P1, P3 y su default) y la lista de
     palabras que no identifican al artículo están versionadas en `contracts/`.
- **Disparador:** termina la carga de la capa de consumo de un lote.

## Flujo principal

1. El proceso calcula la llave de reconciliación de cada artículo. Parte de su
   forma canónica, aplica P1 (plurales, abreviaturas, conectores y unidades como
   gr/ml) y quita las palabras que no identifican, como los colores de empaque y
   los nombres de línea comercial (P3).
2. El proceso agrupa los artículos que comparten llave.
3. El proceso asigna un artículo canónico a cada grupo y lo escribe en
   `articulo_canonico_key`.
4. El proceso recalcula los agregados. Los hechos no se tocan.
5. El proceso registra cuántos artículos reconcilió y cuántos quedaron solos.

## Flujos alternos

**1a · La lista de palabras no se puede leer**
1. El proceso no reconcilia nada: cada artículo queda como su propio canónico.
2. El proceso levanta un aviso en la consola.
3. El caso de uso termina sin éxito.

**2a · La diferencia es de tamaño, sabor o propiedad nutricional**
1. Los artículos no se agrupan, aunque se parezcan: P3 dice que esas palabras sí
   identifican al artículo.
2. Continúa en el paso 2.

**2b · El proceso no está seguro**
1. Si la palabra que cambia no está clasificada, la pareja va a la cola de
   reconciliación (CU-14).
2. Mientras tanto, cada artículo conserva su propio canónico.
3. Continúa en el paso 2.

**3a · Un operador ya resolvió esa pareja en la cola**
1. Gana la decisión humana sobre la llave calculada.
2. Continúa en el paso 3.

## Postcondiciones

- **De éxito:** cada artículo tiene su canónico; las variantes lo comparten; los
  dudosos están en la cola; los agregados están recalculados.
- **De fallo:** `articulo_canonico_key` no cambió, así que cada artículo es su
  propio canónico; los agregados no se recalcularon; hay un aviso en la consola.

## Requisito no funcional asociado

- **Cobertura ≥ 85% y precisión ≥ 90%**, medidas sobre la muestra calificada de
  200 pares (ADR 004). *(Es la hipótesis H3; se mide en T058, 4 de noviembre.)*

## Notas

- Con la regla escrita aplicada par por par, la muestra tiene 30 pares «sí» en la
  mitad por parecido (ADR 014).
- Doce de esos «sí» son de color de empaque o nombre de línea, y ninguna
  normalización los une. Por eso hace falta la lista de palabras que no
  identifican.
- Nunca se juntan gramajes distintos (CU-14).
- Se implementa en T053 (1 de noviembre).
