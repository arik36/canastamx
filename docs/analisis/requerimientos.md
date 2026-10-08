# Requerimientos · CanastaMX

**Entrega 2 · documento de análisis · 9 de octubre de 2026 · Responsable: A**

> **Cómo se lee.** Cada requerimiento tiene un identificador que no cambia (RF-07,
> RNF-12, SLA-D-03, R-02) y dice cómo se verifica. Los identificadores nuevos se
> agregan al final de la numeración, nunca en medio.
>
> Casi nada es nuevo. Sale de:
> - los 14 casos de uso;
> - el contrato de datos 1.3.4;
> - el modelo dimensional (T031);
> - los ADR;
> - las decisiones del equipo (`docs/equipo/decisiones-pendientes.md` y `docs/analisis/openapi/README.md`);
> - el protocolo.
>
> Cada fila dice de dónde sale. La columna **Protocolo** dice a qué requerimiento del
> protocolo de investigación corresponde (RF-D y RNF-D). Cualquier cambio entra por
> solicitud, como el resto del repositorio.
>
> **Población de las cifras:** el alcance del contrato, 2,658,906 filas (7 entidades,
> 5 catálogos, del 2025-01-01 al 2026-07-31), salvo que la fila diga otra cosa.

## 1 · Actores

| Actor | Quién es | Dónde trabaja |
|---|---|---|
| Persona consumidora | Quien compara precios y arma su canasta | App móvil (vistas 6 a 8) |
| Operador de datos | Quien vigila la calidad, atiende incidentes y revisa variantes. Entra con sesión de rol `OPERADOR` | Consola web (vistas 4 y 5) |
| Analista | Quien estudia la evolución de precios contra la inflación. Entra con sesión de rol `ANALISTA` | Consola web (vistas 2 y 3) |
| Procesos automáticos | Orquestador, ingesta, validación, transformación y alertas | Plataforma de datos y servicio de dominio |
| PROFECO (externo) | Publica «Quién es Quién en los Precios», la única fuente de precios | Datos abiertos |
| INEGI (externo) | Publica el INPC, contra el que se contrasta el índice | Datos abiertos |

## 2 · Requerimientos funcionales

### Plataforma de datos

| ID | El sistema debe… | Viene de | Protocolo | Se verifica con |
|---|---|---|---|---|
| RF-01 | Ingerir cada lote de la fuente a la capa cruda completo o nada, sin duplicar filas al volver a ingerirlo | CU-01 | RF-D01 | El consolidado: bucket = filas leídas (hoy 2,658,906 = 2,658,906) |
| RF-02 | Detener el lote, y levantar un incidente, cuando trae controles C1, un `?` en `estado` o `catalogo`, o filas de otra quincena | CU-01 · 3a, 4a, 6a | RF-D02 | Las 8 pruebas de `services/data-platform/tests/` |
| RF-03 | Leer cada archivo con la codificación y el formato de fecha que declara el contrato, y validarlo contra el contrato vigente: 15 columnas, tipos, las 13 con valor requerido, rango y techo de precio por catálogo | CU-02 | RF-D04 · RF-D06 | Lotes de prueba con cada violación |
| RF-04 | No ingerir columnas que el contrato no declara, con un aviso de deriva de esquema, y rechazar el lote si le falta una requerida | CU-02 · 2a, 2b | RF-D03 | Los archivos de junio de 2026 (18 columnas): entran con aviso |
| RF-05 | Reparar el `?` con el diccionario versionado y la regla por frecuencia, contada en el corpus completo, y mandar a cuarentena, con su motivo, lo que no se puede reparar | CU-03 · contrato 1.3.4 (D-03) | RF-D05 | Ningún `?` en la capa de consumo |
| RF-06 | Resolver la clave de fila: de una captura doble (menos de $1) se queda una fila; de $1 a $50, todas; con más de $50, el grupo completo va a cuarentena | CU-02 · 5a · voto unánime del equipo, 2 de octubre de 2026 | RF-D06 | T031: 72,621 capturas dobles; 512 filas (256 pares) a cuarentena |
| RF-07 | Medir la frescura contra la fecha de referencia de la corrida: avisar a los 20 días y dejar de publicar la capa de consumo como vigente a los 45 | CU-02 · 7a | RNF-D03 | Corridas con la fecha de referencia fijada (10, 25 y 51 días) |
| RF-08 | Registrar cada corrida: archivo, huella, filas leídas, aceptadas y en cuarentena por motivo, y duración | CU-01, CU-02 | RF-D02 | Un registro por corrida en `corridas/` |
| RF-09 | Cargar la capa de consumo en esquema estrella, con una observación de precio por fila, y sus agregados | T031 | RF-D08 | `probar-modelo-dimensional.py`: las tres consultas responden |
| RF-10 | Reconciliar las variantes de escritura de un artículo y mandar las dudosas a la cola de revisión | CU-06 | RF-D10 | H3 sobre la muestra de 200 pares |
| RF-11 | Calcular el índice de la canasta por quincena y entidad, con la canasta del ADR 015, y su correlación con el INPC | CU-07 · ADR 015 (D-02) | RF-D11 | H4 |
| RF-24 | Detener la promoción de un lote cuando más del 5% de sus filas va a cuarentena, y levantar un incidente | CU-02 · 5b · contrato 1.3.4 (D-07) | RF-D07 | Un lote de prueba con 6% de filas defectuosas no se promueve; uno con 4% sí |
| RF-25 | Conservar la capa cruda sin alterar, y poder reprocesar cualquier lote desde ella con el mismo resultado | CU-01 · CU-04 · ADR 009 | RF-D12 | Reprocesar `07-2026_Q2` da las mismas filas y la misma huella |

### Operación y análisis (consola web)

| ID | El sistema debe… | Viene de | Protocolo | Se verifica con |
|---|---|---|---|---|
| RF-12 | Mostrar el estado de la plataforma con los seis indicadores de CU-05, el historial de avisos e incidentes y el linaje de cada lote | CU-05 · vista 4 | RF-D09 | Recorrido de la consola |
| RF-13 | Registrar cada incidente y cada aviso (como la deriva de esquema, que no detiene el lote) con su lote, compuerta, motivo y filas, y permitir cerrar los incidentes con causa, decisión y fecha. Los avisos no se cierran | CU-04 · BPMN de incidentes | RF-D06 · RNF-D02 | Un incidente de punta a punta, y un aviso |
| RF-14 | Permitir al operador aprobar, rechazar o asignar a mano una variante de la cola de reconciliación sin mezclar gramajes distintos, y mostrar la cobertura y la precisión de la normalización con su población | CU-14 · vista 5 | RF-D10 · RNF-D08 | Recorrido de la cola |
| RF-15 | Filtrar la evolución de precios por fecha, catálogo, entidad y cadena, compararla con el INPC y señalar las variaciones extremas: más del 20% contra la quincena anterior (P-15) | CU-13 · vista 2 | RF-D11 | Recorrido del tablero |
| RF-16 | Mostrar el detalle de un artículo (el ícono de su catálogo, su precio típico en la entidad, su serie histórica y su precio por establecimiento) y exportarlo a CSV. El precio típico es la **mediana**, no un promedio ni una cifra nacional | CU-13 · vista 3 · ADR 010 · 6 · T031 | RF-D11 | Un CSV exportado que abre en una hoja de cálculo |

### App de la persona consumidora (móvil y dominio)

| ID | El sistema debe… | Viene de | Protocolo | Se verifica con |
|---|---|---|---|---|
| RF-17 | Registrar una cuenta con correo y contraseña, e iniciar sesión. La contraseña tiene mínimo 8 caracteres, una mayúscula y un número, y se guarda cifrada. La cuenta no guarda nombre | CU-08 · P-13 | — | Pruebas del servicio de dominio |
| RF-18 | Buscar un artículo y comparar su precio entre los establecimientos de la entidad, y decir cuando la entidad no tiene cobertura, distinto de «no hay resultados» | CU-12 · vista 6 · P-06 | RF-D11 | 30 búsquedas, incluida una de una entidad fuera del alcance |
| RF-19 | Crear y editar canastas, y mostrar su costo estimado por cadena comercial. El precio de una cadena es la mediana de sus tiendas en la entidad, en la quincena más reciente; sin dato, dice «sin precio», nunca un monto. El costo lo calcula la interfaz analítica a partir de las líneas | CU-09 · vista 7 · T031 · P-10 | RF-D11 | Una canasta con un artículo sin precio en una cadena |
| RF-20 | Configurar una alerta, en la entidad que la persona tiene elegida en la app, con un umbral dentro del rango histórico del artículo en esa entidad: el mínimo y el máximo de sus medianas quincenales | CU-10 · T031 · P-14 | — | Un umbral fuera del rango se rechaza |
| RF-21 | Notificar por correo cuando el precio cruza el umbral hacia abajo (menor o igual), sin repetir mientras siga abajo, y volver a armar la alerta cuando sube. Registrar cada intento (pendiente, enviada o fallida), reintentar los fallidos y mostrar en la app los precios que bajaron | CU-11 · D-05 · `navegacion.md` §3 | — | Una alerta que cruza, una que sigue abajo y no repite, y una con envío fallido |
| RF-22 | Dejar explorar artículos sin iniciar sesión. Guardar la canasta del invitado en el teléfono, y pedir el registro al guardarla o al vigilar un precio | Inventario de vistas · vista 1 · CU-09 · 1a · D-04 | — | Recorrido como invitado: la canasta se sube al iniciar sesión |
| RF-23 | Mostrar «No somos PROFECO» en el acceso, y la quincena de los precios en las vistas de consumo | Inventario · vista 1 · R-03 | — | Revisión de las pantallas |

## 3 · Requerimientos no funcionales

| ID | Atributo | Requerimiento | Viene de | Protocolo |
|---|---|---|---|---|
| RNF-01 | Rendimiento | Registro o inicio de sesión en 2 s o menos | CU-08 | — |
| RNF-02 | Rendimiento | Crear o modificar una canasta en 2 s o menos | CU-09 | — |
| RNF-03 | Rendimiento | Validar y registrar una alerta en 2 s o menos | CU-10 | — |
| RNF-04 | Rendimiento | Evaluar una alerta en 5 s o menos | CU-11 | — |
| RNF-05 | Rendimiento | Resultados de búsqueda en 2 s o menos, medido en 30 búsquedas consecutivas | CU-12 | — |
| RNF-06 | Rendimiento | Primeros resultados del tablero en menos de 3 s, sobre los agregados y no sobre los hechos | CU-13 · T031 | RNF-D07 |
| RNF-07 | Rendimiento | Estado de la plataforma confirmado en menos de 3 s al abrir la consola | CU-05 | — |
| RNF-08 | Operación | Un operador resuelve al menos 120 variantes por hora en la cola | CU-14 | RNF-D08 |
| RNF-09 | Integridad | Volver a ingerir no duplica: el bucket guarda exactamente las filas leídas | CU-01 | RNF-D04 · RNF-D06 |
| RNF-10 | Integridad | 0 lotes a medias: un lote entra completo o no entra | CU-01 | RNF-D06 |
| RNF-11 | Seguridad | Las contraseñas nunca se guardan en texto plano | CU-08 | — |
| RNF-12 | Seguridad | Todo el tráfico externo entra por una sola puerta de enlace con HTTPS y certificados automáticos | Protocolo §10.4 | — |
| RNF-13 | Seguridad | Ningún secreto ni dato crudo en el repositorio: el `.env` fuera de Git, el gancho pre-commit y un historial sin credenciales | `ciclo-de-trabajo.md` · #129 | RNF-D09 |
| RNF-14 | Seguridad | La interfaz analítica no escribe en la capa de consumo; sólo la plataforma de datos lo hace. Las acciones del operador (cerrar un incidente, resolver una variante) van a un esquema de operación aparte | Protocolo §10.4 · P-08 | RF-D11 |
| RNF-15 | Usabilidad | Tres puntos de quiebre: hasta 768, de 769 a 1024 y desde 1025 px. La app es de teléfono; el acceso web se adapta a los tres; las consolas son de escritorio y, debajo de 1025 px, avisan del ancho mínimo | `puntos-de-quiebre.md` (#125) · D-08 | — |
| RNF-16 | Usabilidad | El 100% de las cifras visibles lleva su población y su fecha | Convenio del equipo | — |
| RNF-17 | Mantenibilidad | El 100% de las solicitudes integradas pasa los 3 trabajos de la integración continua: Dominio (Java), Datos (Python) e Higiene | `estrategia-de-ramas.md` | RNF-D10 |
| RNF-18 | Portabilidad | Despliegue en contenedores, con entornos de desarrollo y pruebas aislados que no repiten nombres, puertos, volúmenes ni redes | #129 | — |
| RNF-19 | Arquitectura | Cuatro componentes desplegables por separado, comunicados por HTTP tras la puerta de enlace. El dominio consulta a la interfaz analítica para las alertas, con dos rutas de sólo lectura | Protocolo §10.7 · P-09 | — |
| RNF-20 | Arquitectura | Al menos dos plataformas de desarrollo: Java, Python y TypeScript | Protocolo §10.7 | — |
| RNF-21 | Seguridad | Las consolas exigen sesión con rol: analista para el tablero y el detalle, y operador para la consola y la cola. La app sólo crea cuentas de consumidor | P-07 | — |

## 4 · Acuerdos de nivel de servicio de datos

| ID | Dimensión | Acuerdo | Hoy | Viene de | Protocolo |
|---|---|---|---|---|---|
| SLA-D-01 | Frescura | Avisa a los 20 días y bloquea a los 45, contra la fecha de referencia de la corrida | No aplica: la fuente no publica desde 2026-07-Q2 | Contrato 1.3.4 · ADR 010 · 9 | RNF-D03 |
| SLA-D-02 | Completitud de valores | 0 vacíos en las 13 columnas con valor requerido | 0 (T031) | Contrato · columnas | — |
| SLA-D-03 | Cobertura | 266 de 266 particiones de entidad × quincena (7 × 38) | 266 (T031) | Ingesta T020 | — |
| SLA-D-04 | Contención · H1 | 95% o más de las filas defectuosas inyectadas quedan en cuarentena y no llegan a la capa de consumo | Se mide en el experimento | Protocolo · H1 | RNF-D01 |
| SLA-D-05 | Detección · H2 | Menos de 15 minutos entre la ingesta de un lote defectuoso y el incidente | Se mide en el experimento | Protocolo · H2 | RNF-D02 |
| SLA-D-06 | Texto | 96.63% de las filas afectadas por `?` reparadas, y 0 `?` en la capa de consumo | Como máximo 5,480 filas sin reparar con sólo el diccionario (T031) | Contrato · CU-03 | RF-D05 |
| SLA-D-07 | Reconciliación · H3 | Cobertura ≥ 85% y precisión ≥ 90% sobre la muestra calificada de 200 pares | Se mide en T058 (4 de noviembre) | Protocolo · H3 · ADR 004 y 014 | RNF-D08 |
| SLA-D-08 | Validez del índice · H4 | Correlación positiva y significativa con el INPC, con las divergencias documentadas | Se mide en T069 | Protocolo · H4 · ADR 015 | — |
| SLA-D-09 | Trazabilidad de la cuarentena | 100% de las filas en cuarentena con su motivo, y 100% de los incidentes cerrados con su causa | — | CU-02 · CU-04 | RF-D06 |
| SLA-D-10 | Trazabilidad del consumo | 100% de las filas de la capa de consumo conserva su lote, su fuente y su hora de ingesta | El modelo dimensional las lleva (`lote` e `ingerido_en`) | T031 | RNF-D05 |

*Referencia, no acuerdo:* hoy la cuarentena del alcance es como máximo de 5,992 filas,
el 0.225% (T031). Es una cota superior, porque la regla por frecuencia del `?` todavía
no corre.

## 5 · Restricciones

| ID | Restricción | Viene de |
|---|---|---|
| R-01 | La única fuente de precios es «Quién es Quién en los Precios» de PROFECO; la inflación oficial es el INPC de INEGI | Protocolo · ADR 001 |
| R-02 | Alcance: 7 entidades (Aguascalientes, Guanajuato, Jalisco, Michoacán, Querétaro, San Luis Potosí y Zacatecas), 5 catálogos (Básicos, PACIC, Frutas y Legumbres, Mercados, y Pescados y Mariscos) y la ventana del 2025-01-01 al 2026-07-31 | Contrato · ADR 001 y 005 |
| R-03 | La app no se presenta como fuente oficial: «No somos PROFECO» | Inventario de vistas · vista 1 |
| R-04 | La fuente no trae imágenes: cada artículo se muestra con el ícono de su catálogo | ADR 010 · 6 |
| R-05 | Cerveza, vinos y licores, y cigarrillos se ocultan por omisión en la canasta básica | ADR 010 · 7 |
| R-06 | Congelamiento de funcionalidad el 18 de noviembre. El experimento corre en las semanas 12 y 13 | Cronograma |
| R-07 | Tecnología: web en Next.js, móvil en Expo, dominio en Spring Boot con arquitectura hexagonal, plataforma de datos en Python (Dagster, dbt, Pandera), interfaz analítica en FastAPI, dos PostgreSQL, MinIO, Traefik y Docker Compose en una máquina de Oracle | Protocolo §10.7 · README · ADR 003, 008 y 009 |

## 6 · Supuestos y dependencias

- **S-01 · La fuente está congelada.** PROFECO no publica desde la segunda quincena
  de julio de 2026 (consultado el 30 de septiembre). Si vuelve a publicar, entra como
  lote nuevo y SLA-D-01 empieza a aplicar.
- **S-02 · INEGI publica el INPC con su propio calendario.** Si falta un periodo, el
  índice se publica sin comparación (CU-07 · 3a).
- **S-03 · La máquina de Oracle alcanza.** La tabla de hechos pesa unos 206 MB sin
  índices, y alrededor de medio GB con índices y agregados (estimado, T031). Hace
  falta que B lo confirme contra el presupuesto de memoria del ADR 008.

## 7 · Trazabilidad

Objetivos específicos del protocolo:
1. Ingeniería de requerimientos.
2. Caracterizar la fuente.
3. Especificar el contrato.
4. Capas y modelo estrella.
5. Compuertas, cuarentena y observabilidad.
6. Reconciliación.
7. Evaluar con inyección de fallas.
8. Contrastar el índice con el INPC.

| Requerimientos | Casos de uso | Objetivo | Hipótesis | Decisiones |
|---|---|---|---|---|
| RF-01, RF-02, RF-08, RF-25 · RNF-09, RNF-10 · SLA-D-10 | CU-01 | 2, 4, 5 | H2 | Contrato 1.3.4 · #126 · ADR 009 |
| RF-03 a RF-07, RF-24 · SLA-D-01 a 03 y 06 | CU-02, CU-03 | 3, 5 | H1, H2 | Contrato 1.3.4 (D-03, D-07) · ADR 010 · 9 |
| RF-09 · RNF-06 | CU-12, CU-13 | 4 | — | T031 |
| RF-10, RF-14 · RNF-08 · SLA-D-07 | CU-06, CU-14 | 6 | H3 | ADR 002, 004 y 014 |
| RF-11, RF-15, RF-16 · SLA-D-08 | CU-07, CU-13 | 8 | H4 | ADR 015 · P-15 |
| RF-12, RF-13 · RNF-07 · SLA-D-09 | CU-04, CU-05 | 5 | H1, H2 | BPMN de incidentes · P-08 |
| SLA-D-04, SLA-D-05 | CU-02, CU-04 | 7 | H1, H2 | ADR 010 · 9 |
| RF-17 a RF-23 · RNF-01 a 05, RNF-11, RNF-21 | CU-08 a CU-12 | Proyecto integrador (§10.7) | — | Modelo de dominio · ADR 003, 006, 007 y 011 · D-01, D-04, D-05 · P-07, P-10, P-13, P-14 |
| RNF-12 a RNF-20 · R-07 | — | Proyecto integrador (§10.7) | — | ADR 008, 009 y 012 · #129 · D-08 · P-08, P-09 |

El objetivo 1 es este documento.

## 8 · Lo que sigue abierto

| Qué falta | Afecta | Quién · cuándo |
|---|---|---|
| Los ADR del orquestador (Dagster), la interfaz analítica (FastAPI) y la validación (Pandera) | R-07 | A |
| El ADR del cliente web (Next.js) | R-07 | D |
| Medir el rechazo de cada uno de los 38 lotes, para confirmar el 5% | RF-24 | A · antes del 1 de noviembre |
| Contar cuántos artículos cumplen la canasta del ADR 015 | RF-11 · SLA-D-08 | A · antes de T069 |
| Calibrar el 20% de los anómalos y su mínimo de observaciones | RF-15 | A y D · antes de construir el tablero |

## Historial

- **7 de octubre de 2026.** El equipo revisó el documento.
  - **D ajustó RF-12, RF-13, RF-14 y RF-16.** Al integrarlos se recuperó el linaje de RF-12 y se corrigió el precio de RF-16: es la mediana, no un promedio.
  - **Entraron las decisiones D-02 a D-08 y P-01 a P-15.**
  - **Se agregó la columna del protocolo.** Con ella entraron RF-24 (RF-D07), RF-25 (RF-D12), RNF-21 (P-07) y SLA-D-10 (RNF-D05).
