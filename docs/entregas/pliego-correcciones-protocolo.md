# Pliego de correcciones del protocolo

> **Qué es.** Lo que el protocolo dice y ya no es cierto, porque una decisión
> posterior lo cambió. El protocolo vive en Drive, en Word. Las correcciones se
> aplican ahí en una sola pasada por versión, y aquí se marca en qué versión entró
> cada una.
>
> Lo citan `docs/datos/informe-perfilado-v1.md` y el ADR 014.

## Aplicadas en la versión 3 (29 de septiembre)

| # | Dónde | Decía | Dice ahora |
|---|---|---|---|
| 1 | §8.1 · Alcances | «Guanajuato y tres entidades vecinas» | Siete entidades: Aguascalientes, Guanajuato, Jalisco, Michoacán, Querétaro, San Luis Potosí y Zacatecas |
| 2 | §8.1 · Alcances | «ventana temporal de 2024 a 2026» | Del 1 de enero de 2025 al 31 de julio de 2026 |
| 3 | §8.1 · Alcances | «un volumen estimado entre dos y cuatro millones de registros» | 4,384,962 filas del recorte territorial y 2,658,906 del alcance |
| 4 | §4 · tabla, fila «Histórico» | «Serie 2024–2026» | «Serie de enero de 2025 a julio de 2026» |

*Hasta el 5 de octubre este pliego daba las cuatro como pendientes, porque se
comparó contra una copia anterior del protocolo, no contra la versión 3.*

## Por aplicar en la versión 4 · antes del 9 de octubre

| # | Dónde | Dice en la v3 | Debe decir | Por qué |
|---|---|---|---|---|
| 5 | §7.1 y §14.4 · H3 | Que la primera calificación dio 20 y la segunda lectura la «elevó» a 30; y «PENDIENTE · Ratificar el ADR 014» | La primera calificación dio 20; al aplicar la regla escrita a los pares 026 y 029 quedó en 18. Una segunda lectura encontró 12 más y, con la regla aplicada par por par, el conteo vigente es 30. Quitar el PENDIENTE: el ADR 014 se ratificó el 5 de octubre | ADR 014 (#135) |
| 6 | §11.6, Anexo B y referencia [3] | Contrato «versión 1.3.2, 28 de septiembre» | Versión 1.3.3, 30 de septiembre | #124 |
| 7 | Anexo B · frescura | «Suspendida con corpus congelado» | No aplica en operación mientras el corpus esté congelado; en el experimento se fija la fecha de referencia | Contrato 1.3.3 |
| 8 | Anexo B · clave de fila | Sólo «74,992 colisiones en el alcance» | Agregar la regla: con menos de $1 de diferencia se queda una fila; de $1 a $50, todas; con más de $50, el grupo completo va a cuarentena (votado por unanimidad). Medido en T031: 72,621 capturas dobles y 512 filas en colisión alta | Contrato 1.3.3 · T031 |
| 9 | §11.4 · RNF-D03 | «aviso a los 20 días y bloqueo a los 45 días sin fecha de registro nueva» | Agregar «contra la fecha de referencia de la corrida» | Contrato 1.3.3 |
| 10 | §11.7 · grano | «el precio observado de artículo en establecimiento y fecha de captura» | Una observación de precio: un artículo de una marca, en un establecimiento, en una fecha. Esa combinación puede repetirse | T031 (#128) |
| 11 | §11.7 · cifra | «se prevén 2,586,019» filas de hechos | 2,580,293, medidas en T031. Es una cota inferior, porque la regla por frecuencia del `?` todavía no corre | T031 |
| 12 | §11.7 · cambio lento | Dimensiones de «tipo 2» | Tipo 1: con el corpus congelado no hay historia que conservar, y la cadena del día queda en los hechos | T031 |
| 13 | §11.7 · Figura 6 | Diagrama preliminar, con su PENDIENTE | El diagrama de T031, sin el PENDIENTE | T031 |
| 14 | §11.8 · PENDIENTE de T036 | «Especificar CU-01 a CU-07…» | Hecho (#132 y #133): quitar el PENDIENTE | — |
| 15 | §11.12 · PENDIENTE de la CI | «pytest y mvn test están comentados» | `pytest` corre desde el #129; `mvn test` sigue comentado | `ci.yml` |
| 16 | §14 · Avance | «al 29 de septiembre» | Actualizar a la fecha de entrega: bucket que cuadra (2,658,906, 2 de octubre), modelo medido, contrato 1.3.3, ADR 014 ratificado, CU-01 a CU-07 y sus BPMN | — |
| 17 | Anexo A · pendientes | La lista del 29 de septiembre | La de `docs/equipo/decisiones-pendientes.md` | — |
| 18 | Anexo C · CU-02 | Su versión del 29 de septiembre | La de `docs/analisis/casos-uso/CU-02-validar-lote-contrato.md`: grupo completo (5a), umbral de rechazo por decidir (5b) y frescura (7a) | CU-02 |
| 19 | Anexo D · matriz | «Completar la matriz…» | Completarla con `requerimientos.md` cuando se suba, con los mismos identificadores RF-D y RNF-D | — |

## Lo que se revisó y no necesita corrección

- **H3** se mide como está enunciada: cobertura del 85% y precisión del 90% sobre
  200 pares (ADR 014).
- **H5** quedó sin efecto, y el protocolo ya lo dice.
- **H2** se mide desde el inicio de la ingesta (RNF-D02). El repositorio decía «desde
  que el lote entró a la capa cruda» en CU-02, CU-04 y el BPMN de incidentes, y se
  alineó con el protocolo.
- **Las referencias:** las 58 que lista se citan, y todo lo que se cita está listado.
- **Las tecnologías** de §12.2 son las mismas del README.
