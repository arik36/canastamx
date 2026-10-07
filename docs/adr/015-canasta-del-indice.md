# ADR 015 · La canasta del índice (H4)

- **Fecha:** 6 de octubre de 2026
- **Estado:** aceptada el 6 de octubre de 2026 (D-02 de `docs/equipo/decisiones-pendientes.md`)
- **Participantes:** A, con el equipo

## Contexto

H4 contrasta un índice de canasta propio con el INPC de INEGI (CU-07, RF-11). Para
calcularlo hay que decir qué artículos forman la canasta, cuánto pesa cada uno y
contra qué quincena se compara. Sin eso, T069 no tiene qué calcular.

## Decisión

1. **Qué artículos entran:** los que tienen precio en **las 38 quincenas** de la
   ventana y en **las 7 entidades** del alcance.
2. **Cuáles quedan fuera:** cerveza, vinos y licores, y cigarrillos, igual que en la
   canasta básica por omisión (ADR 010 · 7).
3. **Peso:** **el mismo para todos.**
4. **Base:** **100 en la primera quincena de enero de 2025** (`2025-01-Q1`).
5. **El precio de cada artículo,** en cada entidad y quincena, es su **precio
   típico**: la mediana de `agg_articulo_entidad_quincena` (T031).

## Cómo se calcula

El índice de una quincena es la **media geométrica** de los precios relativos de los
artículos de la canasta (precio de la quincena entre precio de la base), por 100.
Es la misma fórmula del índice por cadena que ya se midió en T031. Se calcula por
entidad y para el alcance completo.

*La fórmula se confirma al implementarla en T069. Si el equipo prefiere media
aritmética, se cambia aquí, antes de esa tarea.*

## Alternativas descartadas

- **Ponderar con los pesos del INPC por categoría.** Se parece más a INEGI, pero
  obliga a relacionar las categorías de PROFECO con las del INPC, y esa relación no
  existe. Queda como trabajo futuro.
- **Todos los artículos, aunque les falten quincenas.** El índice cambiaría de un mes
  a otro sólo porque entran y salen artículos, no porque cambien los precios.

## Consecuencias

- **Por construcción, ningún artículo de la canasta tiene huecos en la ventana.** El
  alterno 1a de CU-07, un artículo sin precio en una quincena, sólo puede pasar con
  datos nuevos, después de julio de 2026.
- **Hay que medir cuántos artículos cumplen** antes de T069. Si son muy pocos, la
  canasta no representa nada y este ADR se revisa. Lo mide el guion del modelo
  dimensional sobre el alcance.
- **El tablero dice siempre la base, la fórmula y cuántos artículos tiene la canasta.**
