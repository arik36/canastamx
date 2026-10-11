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

## Por aplicar en la versión 4 · antes del 18 de octubre

> **Esta pasada no se hizo el 9 de octubre.** Se mantiene como una sola pasada, y
> por eso ahora incluye también las decisiones del **7 de octubre** (puntos 20 a 26),
> que el pliego no tenía porque se escribió antes de esa reunión. Hacer dos pasadas
> sobre el mismo Word es hacer el trabajo dos veces: **primero se completa este
> pliego, luego se aplica.**
>
> El punto **17** incluye ahora las tres decisiones abiertas: **D-09, D-10 y D-11**.


| # | Dónde | Dice en la v3 | Debe decir | Por qué |
|---|---|---|---|---|
| 5 | §7.1 y §14.4 · H3 | Que la primera calificación dio 20 y la segunda lectura la «elevó» a 30; y «PENDIENTE · Ratificar el ADR 014» | La primera calificación dio 20; al aplicar la regla escrita a los pares 026 y 029 quedó en 18. Una segunda lectura encontró 12 más y, con la regla aplicada par por par, el conteo vigente es 30. Quitar el PENDIENTE: el ADR 014 se ratificó el 5 de octubre | ADR 014 (#135) |
| 6 | §11.6, Anexo B y referencia [3] | Contrato «versión 1.3.2, 28 de septiembre» | **Versión 1.3.4, 6 de octubre.** Fue 1.3.3 el 30 de septiembre; 1.3.4 agregó la frecuencia del `?` contada en el corpus (D-03) y el umbral de rechazo por lote del 5% (D-07) | #124 · #140 |
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
| 18 | Anexo C · CU-02 | Su versión del 29 de septiembre | La de `docs/analisis/casos-uso/CU-02-validar-lote-contrato.md`: grupo completo (5a), umbral de rechazo del 5% por lote (5b, D-07) y frescura (7a) | CU-02 |
| 19 | Anexo D · matriz | «Completar la matriz…» | Completarla con `requerimientos.md` cuando se suba, con los mismos identificadores RF-D y RNF-D | — |

### Puntos 20 a 26 · las decisiones del 7 de octubre

Ninguna estaba en este pliego. Las tres primeras son las que el documento de la
entrega 2 ya corrigió en su sección «Qué cambió desde la entrega 1»: el protocolo
tiene que decir lo mismo que ese documento, o el asesor encuentra dos versiones del
proyecto.

| # | Dónde | Dice hoy | Debe decir | Por qué |
|---|---|---|---|---|
| 20 | §10.7 | El servicio de dominio y la interfaz analítica **no se llaman entre sí** | El dominio consulta a la analítica, **sólo para leer**, con dos rutas: el rango histórico y los precios vigentes que necesitan las alertas | P-09 · RNF-19 · CU-10 y CU-11 no se pueden resolver sin esos precios |
| 21 | §10.7 | La interfaz analítica tiene **cuatro endpoints** de sólo lectura | **19 rutas.** Sólo lee la capa de consumo; las dos acciones de la consola —cerrar un incidente y resolver una variante— se guardan en un **esquema de operación aparte** | P-08 · RNF-14 · `analitica.yaml` 0.2.1 |
| 22 | Donde describe el cliente web · por localizar al aplicar | «Aplicación web responsiva en tres puntos de quiebre» | Las **consolas** del analista y del operador son **de escritorio** (desde 1025 px) y avisan del ancho mínimo; el **acceso web** sí se adapta a los tres anchos | D-08 · RNF-15 · una consola en una sola columna deja de servir por su densidad de datos |
| 23 | Donde describe la cuenta · por localizar al aplicar | La cuenta con sus datos de registro | **La cuenta no guarda nombre: se identifica con su correo.** Y **nace con un rol** (`CONSUMIDOR`, `ANALISTA` u `OPERADOR`) que viaja en la sesión; desde la app sólo se crean consumidores | P-13 y P-07 · RF-17 · RNF-21 |
| 24 | Donde describe las alertas · por localizar al aplicar | La alerta avisa cuando el precio baja del umbral | La alerta **guarda la entidad** elegida al crearla, y avisa **sólo al cruzar** el umbral hacia abajo: no repite mientras siga abajo y se vuelve a armar cuando sube | P-14 y D-05 · RF-20 y RF-21 |
| 25 | §11.8 o donde liste los casos de uso | La lista anterior a la entrega 2 | Los **14 casos de uso** (CU-01 a CU-14) y los **tres BPMN**: ingesta, incidentes y alertas | #132, #133, #137, #148 y #149 |
| 26 | §12.2 · tecnologías | Dagster, dbt, Pandera y FastAPI, sin más | Dagster (**ADR 016**, con fecha de salida el 25 de octubre), FastAPI (**ADR 017**) y Pandera (**ADR 018**) quedaron con acta. **dbt se pospone** y se revisa el 2 de noviembre (**ADR 019**) | Los tres primeros estaban en el README sin ADR; el cuarto cambió de fecha |

## Lo que se revisó y no necesita corrección

- **H3** se mide como está enunciada: cobertura del 85% y precisión del 90% sobre
  200 pares (ADR 014).
- **H5** quedó sin efecto, y el protocolo ya lo dice.
- **H2** se mide desde el inicio de la ingesta (RNF-D02). El repositorio decía «desde
  que el lote entró a la capa cruda» en CU-02, CU-04 y el BPMN de incidentes, y se
  alineó con el protocolo.
- **Las referencias:** las 58 que lista se citan, y todo lo que se cita está listado.
- **Las tecnologías** de §12.2 eran las mismas del README. Desde el 11 de octubre tienen ADR, y dbt tiene fecha de revisión: ver el punto 26.
