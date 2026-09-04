# Manual del equipo — CanastaMX

Todo lo que necesitas para trabajar en este proyecto sin preguntar. Se actualiza al cierre de cada iteración y vive en el repositorio, no en el correo.

---

## Antes de crear tu primera rama

```bash
git switch main && git pull
bash infra/scripts/verificar-base.sh
```

Si sale algo en rojo, **no ramifiques: avísalo en el chat.** Qué tiene que existir y por qué está en [`linea-base.md`](./linea-base.md).

---

## Empieza aquí

| Si eres… | Lee, en este orden |
|---|---|
| **Alguien a punto de crear su primera rama** | **[La línea base](./linea-base.md).** Y corre `bash infra/scripts/verificar-base.sh <tu clave>` |
| **Alguien a punto de crear su primera rama** | [Línea base](./linea-base.md), y corre `verificar-base.sh` |
| **Alguien que va a trabajar hoy** | **[La ficha de tu tarea](./fichas/semana-01.md).** Completa, antes de empezar. No a media tarea |
| **Nuevo en el equipo** | [Cómo trabajamos](./como-trabajamos.md) → [Git paso a paso](./git-paso-a-paso.md) → [tu ficha de hoy](./fichas/semana-01.md) |
| **El que monta el tablero (A)** | [El tablero](./tablero-github.md), parte 1 |
| **Alguien que va a subir código hoy** | [Git paso a paso](./git-paso-a-paso.md), secciones 2, 3 y 4 |
| **Alguien atorado** | [Git paso a paso](./git-paso-a-paso.md), secciones 9 y 11 |
| **Alguien que espera algo de otro** | [Mapa de dependencias](./mapa-dependencias.md) |
| **Alguien preparando una entrega** | La [ficha de esa fecha](#las-cinco-entregas) |

---

## Qué es cada cosa

Cinco piezas con nombres parecidos. Esto las distingue.

| | Qué es | Dónde vive | Quién lo abre | Para qué |
|---|---|---|---|---|
| **El panel** | Página web con enlace | Fuera del repositorio | Los cinco, a diario | Qué toca hoy, y la ficha de cada tarea desplegada |
| **Las fichas** | Cómo se hace cada tarea | [`fichas/semana-01.md`](./fichas/semana-01.md) | Quien va a trabajar | Insumos, conceptos, paso a paso, errores frecuentes |
| **El cronograma** | Las 14 semanas del semestre | [`cronograma.md`](./cronograma.md) | Quien planea | Qué pasa cuándo, de septiembre a diciembre |
| **La bitácora** | El reporte con semáforo | `CanastaMX_Bitacora.xlsx`, en Drive | A, y el asesor | Evidencia de cumplimiento por integrante y por semana |
| **El tablero** | Los issues | GitHub Projects | Los cinco | **La fuente de verdad del avance.** Si no está aquí, no existe |

El cronograma y la bitácora contienen las mismas 85 tareas, pero no son lo mismo: **el cronograma se lee, la bitácora se llena.** El cronograma vive en el repositorio y no cambia salvo que se replanee; la bitácora vive en Drive, se colorea en la reunión semanal y se entrega al asesor en cada entrega institucional.

Y el orden de uso, en un día normal: abres **el panel**, encuentras tu tarea, despliegas **la ficha**, trabajas, y mueves la tarjeta en **el tablero**.

---

## Los documentos

| Archivo | Qué contiene |
|---|---|
| [`fusion-con-el-repo.md`](./fusion-con-el-repo.md) | Qué diferencia hay entre el paquete y el repositorio que ya existía, y cómo se fusionan sin perder nada |
| [`linea-base.md`](./linea-base.md) | **Qué debe existir en `main` antes de que nadie cree una rama.** Tres niveles y la etiqueta `base-v0` como señal de arranque |
| [`fichas/semana-01.md`](./fichas/semana-01.md) | **Las 18 tareas de la semana 1, una ficha cada una**: qué entregas, qué verificar antes, de quién dependes, los conceptos explicados, paso a paso, cómo se ve terminado y errores frecuentes |
| [`fichas/PLANTILLA-ficha.md`](./fichas/PLANTILLA-ficha.md) | Para escribir las fichas de la semana siguiente. Se llenan en la reunión, con todos presentes |
| [`linea-base.md`](./linea-base.md) | Qué debe existir en `main` **antes de que alguien ramifique**, qué NO debe estar todavía, y las dos etapas de la protección de `main` |
| [`mapa-dependencias.md`](./mapa-dependencias.md) | Qué tarea bloquea a cuál, las tres cadenas críticas y a quién avisarle al terminar |
| [`como-trabajamos.md`](./como-trabajamos.md) | El ritmo del equipo: reporte diario, reunión semanal, la regla de las 24 horas, qué significa "terminado", el semáforo y dónde se dice qué |
| [`git-paso-a-paso.md`](./git-paso-a-paso.md) | Cada operación de Git en dos vías, terminal y GitHub Desktop. Incluye cómo deshacer errores y un catálogo de mensajes de error |
| [`cronograma.md`](./cronograma.md) | Las 14 semanas rebaseadas al 3 de septiembre, con actividades y criterios de cierre por integrante |
| [`tablero-github.md`](./tablero-github.md) | Cómo se monta el tablero (una vez) y cómo se opera (todos los días) |
| [`entregas/`](./entregas/) | Una ficha por entrega institucional |
| [`AUDITORIA-2026-09-02.md`](./AUDITORIA-2026-09-02.md) | Los ocho problemas detectados en la revisión del sistema de trabajo, y qué se hizo con cada uno |

### Las plantillas-esqueleto

Nadie parte de un archivo vacío. Estos ya traen la estructura puesta; se llenan, no se diseñan.

| Plantilla | Quién la llena | Cuándo |
|---|---|---|
| [`docs/datos/fuente-qqp.md`](../datos/fuente-qqp.md) | A | jue 3 |
| [`docs/datos/perfilado.md`](../datos/perfilado.md) | A | jue 3 y vie 4 |
| [`docs/datos/informe-perfilado-v0.md`](../datos/informe-perfilado-v0.md) | A | dom 6 |
| [`docs/datos/diccionario-qqp.md`](../datos/diccionario-qqp.md) | C2 | jue 3 |
| [`docs/analisis/inventario-vistas.md`](../analisis/inventario-vistas.md) | D | jue 3 |
| [`docs/analisis/modelo-dominio.md`](../analisis/modelo-dominio.md) | C1 | vie 4 |
| [`docs/adr/001-fuente-de-datos.md`](../adr/001-fuente-de-datos.md) | Equipo | lun 7 |
| [`docs/adr/000-plantilla.md`](../adr/000-plantilla.md) | Quien decida algo | siempre |
| `docker-compose.yml` · `.env.example` · `.gitignore` | B | jue 3 y vie 4 |
| `.github/workflows/ci.yml` | B | vie 4 |
| `contracts/qqp.contrato.yml` | A | semana 2 |
| `README.md` | A, y lo verifica B | semana 3 |

---

## Qué es cada cosa, y quién la toca

Hay cinco artefactos con nombres parecidos. Se confunden, y conviene tenerlos claros desde hoy.

| Artefacto | Qué es | Se llena o se lee | Quién lo toca | Cada cuánto |
|---|---|---|---|---|
| **Tablero de GitHub** (Projects e Issues) | **La fuente de verdad del avance.** Si una tarea no está aquí, no existe | Se llena | Los cinco | Todos los días |
| **[`cronograma.md`](./cronograma.md)** | El **plan** de las 14 semanas: qué toca cada semana y a quién | Se lee | A lo edita si el plan cambia | Cuando algo se recorre |
| **[`fichas/semana-01.md`](./fichas/semana-01.md)** | **Cómo se hace** cada tarea de la semana en curso | Se lee | Quien ejecuta la tarea | Se escribe una vez por semana, en la reunión |
| **`CanastaMX_Bitacora.xlsx`** | El **reporte para el asesor**, con el semáforo por integrante y por semana | Se llena, exportando del tablero | A | Una vez por entrega institucional |
| **El panel** (la página con enlace) | La **vista de consulta** desde el celular. No guarda nada del equipo | Se lee | Nadie lo edita a mano | Se republica si el plan cambia |

Dicho de otro modo: **el cronograma dice qué**, **la ficha dice cómo**, **el tablero dice cómo va**, **el Excel se lo enseña al asesor** y **el panel es para consultarlo desde el teléfono**.

El cronograma y el Excel se parecen porque cubren las mismas 85 tareas, pero uno es el plan narrado y el otro es el registro con estados y colores. Salen de la misma fuente, así que no se contradicen.

---

## Los cinco frentes

| | Quién | Iniciales | Frente | Etiqueta | Suplente |
|---|---|---|---|---|---|
| **A** | Ariadne Lizett Macías Campos | `alm` | Datos y plataforma | `datos` | B |
| **B** | Ari Adair Soto Garnica | `aas` | Infraestructura, CI y calidad | `infra` | A |
| **C1** | Liseth Yareth Lara López | `lyl` | Servicio de dominio (Java) | `dominio` | C2 |
| **C2** | Oscar Renato Fonseca Ríos | `orf` | Cliente móvil (Expo) | `movil` | C1 y D |
| **D** | Karen Alejandra Herrera Villalpando | `kah` | Cliente web y maquetación | `web` | C2 |

---

## Las cinco entregas

| Fecha | Qué | Ficha |
|---|---|---|
| **18 de septiembre** | Definición del proyecto y responsabilidades | [ficha](./entregas/2026-09-18-definicion.md) |
| **9 de octubre** | Documento de análisis: 14 casos de uso, BPMN, prototipo | [ficha](./entregas/2026-10-09-analisis.md) |
| **4 de noviembre** | Avance de construcción: cuatro suites de pruebas | [ficha](./entregas/2026-11-04-construccion.md) |
| **18 de noviembre** | Versión final desplegada · congelamiento | [ficha](./entregas/2026-11-18-version-desplegada.md) |
| **2, 7 y 9 de diciembre** | Experimento, cierre y presentaciones | [ficha](./entregas/2026-12-presentaciones.md) |

---

## Las reglas, en una pantalla

1. **Si no está en el tablero, no existe.** No se evalúa y no se reclama.
2. **Nadie escribe directo en `main`.** Rama por tarea, solicitud con una aprobación y la integración continua en verde.
3. **Ninguna tarea dura más de una semana.** Si dura más, son dos tareas.
4. **24 horas atorado = pides ayuda.** No es opcional.
5. **Terminado significa incorporado a `main` y aprobado por otro.** "Está en mi máquina" no es un estado.
6. **Cada decisión técnica va a un ADR.** Media cuartilla, en `docs/adr/`.
7. **Contraseñas y datos crudos nunca entran al repositorio.**

---

## Enlaces

| Qué | Dónde |
|---|---|
| Repositorio | `github.com/arik36/canastamx` |
| Tablero | Pestaña **Projects** del repositorio |
| Figma | *(D lo agrega aquí)* |
| Drive del equipo | *(A lo agrega aquí)* |
| Bitácora en Excel | *(A lo agrega aquí)* |
| Panel del equipo | *(A lo agrega aquí)* |

---

*¿Algo de este manual no funcionó como dice? Es un defecto del manual, no tuyo. Abre un issue con la etiqueta `docs`.*
