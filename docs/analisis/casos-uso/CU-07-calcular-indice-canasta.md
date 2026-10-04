# CU-07 · Calcular el índice de la canasta y contrastarlo con el INPC

- **Actor primario:** el proceso analítico (actor automático)
- **Interesados:**
  - **Analista** — necesita comparar los precios observados con la inflación
    oficial y explicar dónde se separan.
  - **Asesor y jurado** — es la evidencia de la hipótesis H4.
  - **Consumidor de la app** — de forma indirecta: el tablero le da contexto al
    precio que ve.
- **Precondiciones:**
  1. La canasta del índice está definida en un ADR: qué artículos, qué pesos y qué
     quincena es la base.
  2. La serie del INPC de INEGI está integrada (T064).
  3. La capa de consumo está cargada.
- **Disparador:** termina la carga de una quincena en la capa de consumo.

## Flujo principal

1. El proceso toma los artículos de la canasta y su precio típico (la mediana) por
   entidad y quincena, de `agg_articulo_entidad_quincena`.
2. El proceso calcula el índice de cada quincena contra la base, por entidad y para
   todo el alcance.
3. El proceso obtiene el INPC del mismo periodo.
4. El proceso calcula la correlación entre las dos series y señala dónde se
   separan.
5. El proceso publica el índice, el INPC y la correlación para el tablero (CU-13).

## Flujos alternos

**1a · Un artículo de la canasta no tiene precio en una quincena o entidad**
1. El proceso calcula esa quincena con los artículos que sí tienen precio y anota
   cuántos faltaron.
2. Si faltan más de los que permite el ADR de la canasta, la quincena se publica
   marcada como incompleta.
3. Continúa en el paso 2.

**3a · El INPC de ese periodo todavía no se publica**
1. El proceso publica el índice sin comparación y lo avisa.
2. La correlación se calcula cuando INEGI publique.
3. El caso de uso termina con éxito parcial.

**4a · La serie es demasiado corta para concluir**
1. El proceso publica la correlación sin conclusión y explica por qué.
2. Continúa en el paso 5.

## Postcondiciones

- **De éxito:** el índice y la correlación quedaron publicados, con su quincena y
  su cobertura.
- **De fallo:** el tablero sigue mostrando el último índice válido, con su fecha.

## Requisito no funcional asociado

- El tablero muestra el índice en **menos de 3 segundos** (CU-13), porque se
  calcula al cargar los datos y no al consultar.
- **H4:** la correlación con el INPC es positiva y significativa, y las
  divergencias quedan documentadas.

## Notas

- **La canasta todavía no está definida.** La propuesta es: los artículos con
  precio en las 38 quincenas y las 7 entidades, sin alcohol ni tabaco (ADR 010 ·
  7), con el mismo peso y base 100 en 2025-01-Q1. Va en un ADR antes del 25 de
  octubre.
- En el panel, T069 (13-nov) usa el INPC, pero la integración de INEGI está en
  T064 (15-nov). Hay que adelantar la integración o mover T069.
