# Auditoría del sistema de trabajo

**2 de septiembre de 2026** · Revisión del panel, la bitácora y el cronograma antes de que arranquen las actividades del jueves 3.

Ocho hallazgos. Los dos primeros los detectó A; los seis restantes salieron al contrastar las tareas contra el protocolo de investigación.

---

## Resumen

| # | Hallazgo | Severidad | Estado |
|---|---|---|---|
| 1 | El panel enlaza a archivos que no existen en el repositorio | **Crítica** | Resuelto |
| 2 | Las tareas dicen qué lograr, no cómo ni con qué insumo | **Crítica** | Resuelto |
| 3 | Siete tareas tienen insumos que existen y nadie señaló | **Alta** | Resuelto |
| 4 | Ninguna tarea dice cómo se ve el archivo terminado | **Alta** | Resuelto |
| 5 | El recorte geográfico ya está semidecidido en el protocolo | Media | Resuelto |
| 6 | El jueves 3 concentra tres tareas secuenciales de A | Media | Mitigado |
| 7 | Referencia cruzada rota en el protocolo | Baja | **Pendiente** |
| 8 | El manual original se contradice sobre quién crea la estructura | Baja | Resuelto |

---

## 1 · El panel enlaza a archivos que no existen — **crítica**

**Qué pasa.** La sección «Las guías, en el repositorio» del panel apunta a `docs/equipo/git-paso-a-paso.md`, `cronograma.md`, `como-trabajamos.md`, `tablero-github.md` y `entregas/`. Ninguno está en el repositorio todavía. Los cuatro integrantes que reciban el enlace verán un 404 en cada guía.

**Por qué importa más de lo que parece.** El panel es el enlace único que se les iba a mandar. Un recurso de arranque que falla en su primer clic destruye la confianza en el sistema completo: la siguiente vez que se les pida abrir algo, no lo abren.

**Agravante.** El repositorio es privado durante el semestre. Aunque los archivos existieran, un integrante que no haya aceptado la invitación de colaborador vería 404 igual, y no sabría distinguir entre «no existe» y «no tengo acceso».

**Solución aplicada.** Se rompe la dependencia en dos frentes:

- **El panel se vuelve autosuficiente.** Cada tarea de la semana 1 se despliega dentro del panel con su ficha completa. Nadie necesita entrar al repositorio para saber qué hacer el jueves.
- **Los enlaces se marcan por estado.** Cada guía indica si ya está en el repositorio o si llega cuando A suba el paquete, y se advierte que el repositorio es privado.

**Orden correcto de arranque**, que antes estaba invertido:

1. A sube el paquete al repositorio *(hoy, miércoles 2)*
2. A invita a los cuatro colaboradores y confirma que los cuatro aceptaron
3. A manda el enlace del panel

---

## 2 · Las tareas dicen qué lograr, no cómo ni con qué — **crítica**

**Qué pasa.** «Instalar JDK 21 y Maven. Esqueleto de Spring Boot con las tres capas separadas y endpoint de salud» declara un resultado, no un procedimiento. No dice cuáles son las tres capas, dónde se leen, qué se necesita antes ni cómo se ve terminado.

**Por qué importa.** Cinco estudiantes de especialidades distintas, con horarios distintos y sin oficina compartida. Cuando una tarea es ambigua y no hay nadie al lado a quien preguntar, pasa una de tres cosas, y las tres cuestan: se detiene y espera respuesta en el chat, la interpreta a su manera y hay que rehacerla, o la pospone.

**Solución aplicada.** Las 18 tareas de la semana 1 tienen ficha con siete apartados:

| Apartado | Qué responde |
|---|---|
| Qué entregas | El artefacto concreto, con su ruta |
| Antes de empezar, verifica | Lista de comprobación de insumos, con quién los produce |
| Depende de · Bloquea a | La cadena, para saber a quién avisar al terminar |
| Lo que necesitas saber | Los conceptos explicados aquí mismo, no en un enlace |
| Paso a paso | Comandos y acciones reales, copiables |
| Cómo se ve terminado | El esqueleto del archivo, o la señal de que quedó |
| Errores frecuentes | Los que se van a encontrar, con su solución |

Las semanas 2 en adelante se escriben en la reunión semanal con `docs/equipo/fichas/PLANTILLA-ficha.md`. Escribirlas es parte de cerrar la reunión, no una tarea aparte.

---

## 3 · Siete tareas tienen insumos que existen y nadie señaló — **alta**

Este es el hallazgo que más tiempo iba a costar. En cada caso el insumo ya existe —casi siempre dentro del protocolo de investigación— pero la persona que hace la tarea no sabe que existe, y va a producir algo desde cero que no va a coincidir.

| Tarea | Insumo que ya existe | Qué pasaba si no se dice |
|---|---|---|
| **D · Wireframe de la consola** | Los seis indicadores están definidos en el objetivo específico 4 del protocolo | Karen dibuja los indicadores que se imagine. Ninguno coincide con lo que A va a construir, y el wireframe se rehace |
| **D · Inventario de las ocho vistas** | Las ocho vistas están en la tabla de la sección 10.7, con su cliente y su origen de dato | Se inventan ocho vistas distintas y el prototipo del 18 de septiembre no corresponde al protocolo entregado |
| **C1 · Esqueleto de Spring con «tres capas»** | El protocolo compromete **arquitectura hexagonal**, que no es lo mismo que el patrón clásico de tres capas | Liseth arma controlador–servicio–repositorio, que es lo que se enseña, y en octubre hay que reescribirlo |
| **C1 · Borrador del modelo de dominio** | Los tres agregados ya están nombrados —Usuario, Canasta, Alerta— y CU-08 a CU-11 describen su comportamiento | Se modela desde cero un dominio que no cubre los casos de uso comprometidos |
| **C2 · Diccionario de datos QQP** | Depende de que A localice primero el portal y el archivo. Ambas tareas caen el mismo jueves | Oscar busca por su cuenta, encuentra otra versión del conjunto y documenta columnas que no son las que A descargó |
| **B · Traefik** | Necesita el `docker-compose.yml` que B mismo hace el jueves | Sin riesgo real, pero conviene declararlo |
| **B · Integración continua mínima** | Necesita algo que compilar: el esqueleto de C1, del jueves | Si C1 se atrasa, la canalización no tiene qué construir y B queda bloqueado sin saber por qué |

**Los seis indicadores de la consola**, para que dejen de estar enterrados en un párrafo:

1. Estado de la última ejecución
2. Frescura por fuente
3. Resultado de las validaciones
4. Linaje entre activos
5. Historial de incidentes
6. Volumen en cuarentena

**Las ocho vistas**, igual:

| Vista | Cliente | Origen del dato |
|---|---|---|
| Acceso | Web y móvil | Servicio de dominio |
| Tablero analítico | Web | Interfaz analítica |
| Detalle de producto | Web | Interfaz analítica |
| Consola de observabilidad | Web | Interfaz analítica |
| Cola de reconciliación | Web | Interfaz analítica |
| Búsqueda | Móvil | Interfaz analítica |
| Mi canasta | Móvil | Dominio y analítica |
| Alertas | Móvil | Servicio de dominio |

**Solución aplicada.** Cada ficha abre con «Antes de empezar, verifica», y los insumos que viven en el protocolo se transcriben dentro de la ficha en lugar de citarse. Además se publicó `docs/equipo/mapa-dependencias.md` con las cadenas explícitas.

---

## 4 · Ninguna tarea dice cómo se ve el archivo terminado — **alta**

**Qué pasa.** Cinco personas van a crear archivos Markdown en `docs/` durante catorce semanas, cada una partiendo de un archivo vacío. El resultado previsible es cinco formatos distintos, y un documento de análisis que en octubre hay que homogeneizar a mano.

**Por qué importa en un equipo remoto.** Un archivo vacío es donde se atora la gente que no quiere preguntar. Media hora mirando la pantalla sin escribir nada no aparece en ningún tablero, pero se acumula.

**Solución aplicada.** Catorce plantillas-esqueleto en el repositorio, con encabezados, tablas vacías y comentarios `<!-- -->` que explican qué va en cada sección. Se llenan, no se diseñan.

`fuente-qqp.md` · `perfilado.md` · `informe-perfilado-v0.md` · `diccionario-qqp.md` · `modelo-dominio.md` · `inventario-vistas.md` · `diagrama-clases.md` · ADR 000 plantilla y 001 fuente de datos · `docker-compose.yml` comentado · `.env.example` · `.gitignore` · contrato de datos en YAML · `README.md` · `ci.yml`

---

## 5 · El recorte geográfico ya está semidecidido — media

**Qué pasa.** La reunión del lunes 7 se planteó como «se fija el recorte geográfico definitivo». Pero el protocolo ya declara en Alcances: **centro-occidente, ventana temporal 2024 a 2026, entre dos y cuatro millones de registros.**

**Por qué importa.** El equipo va a llegar a la reunión creyendo que decide desde cero, cuando lo que corresponde es **confirmar o ajustar** un recorte ya comprometido por escrito. Si se decide algo distinto sin notarlo, el protocolo entregado el 18 de septiembre contradice al sistema que se está construyendo.

**Solución aplicada.** La ficha de la reunión (T018) plantea la decisión en su forma correcta: *«el protocolo compromete centro-occidente y 2024–2026; con el perfilado en mano, ¿se sostiene, se acota o se amplía?»*, y exige que el ADR 001 registre explícitamente si se confirma o se cambia, para poder corregir el protocolo si hace falta.

---

## 6 · El jueves 3 concentra tres tareas secuenciales de A — media

**Qué pasa.** A tiene cuatro cosas ese día: subir el paquete, cerrar la estructura del repositorio, localizar y descargar el archivo de PROFECO, y hacer el perfilado nivel 1. Las dos últimas son estrictamente secuenciales —no se perfila lo que no se ha descargado— y las dos primeras bloquean a los otros cuatro.

**Riesgo concreto.** Si la descarga tarda o el archivo resulta ser más pesado de lo esperado, el perfilado nivel 1 se recorre al viernes, y el viernes ya tiene los niveles 2 y 3. La cadena termina empujando el informe al domingo y la reunión del lunes queda sin insumo.

**Mitigación aplicada.** Se declara un orden de prioridad para el jueves, porque cuando algo tenga que caerse conviene saber qué:

1. **Subir el paquete y cerrar la estructura** — desbloquea a los otros cuatro. No se negocia.
2. **Localizar y descargar el archivo** — desbloquea a C2. Pasar el enlace por el chat en cuanto se tenga, sin esperar a terminar la descarga.
3. **Perfilado nivel 1** — si se cae al viernes, no bloquea a nadie más.

Si el jueves solo alcanza para los puntos 1 y 2, la semana sigue viva. Si solo alcanza para el 3, cuatro personas están detenidas.

---

## 7 · Referencia cruzada rota en el protocolo — baja, **pendiente**

**Qué pasa.** El protocolo cita en dos lugares «los seis indicadores de la sección 7.5». La sección 7 es *Objetivos específicos* y no tiene subsecciones. Los seis indicadores están en el cuarto objetivo específico.

**Por qué corregirlo.** Un asesor que siga la referencia y no la encuentre lo va a marcar, y una referencia rota en la primera entrega abre la sospecha de que el documento no fue releído.

**Qué hacer.** Antes del 18 de septiembre, en el mismo pase donde se corrige lo que ya se había detectado:

- Sección 10.3: dice «se trabaja en equipo de tres personas». Son cinco.
- Tabla de integrantes: tres celdas dicen «(por definir)». Ya están definidos.
- Secciones 10.4 y 10.7: la referencia «sección 7.5» debe apuntar al cuarto objetivo específico.

---

## 8 · El manual original se contradice sobre quién crea la estructura — baja

**Qué pasa.** El manual dice en 2.2 que «esta es la estructura que **B** crea el lunes», y en 2.5 que «**B** escribe el README el lunes». Pero la tabla de actividades del lunes 31 asigna a **A** crear el repositorio, subir el README, el `.gitignore` y la estructura.

**Resolución.** Se asigna a **A**, porque es quien ya creó el repositorio y quien tiene los permisos de administración. B conserva `docker-compose.yml`, `.env.example`, la integración continua y todo `infra/`.

Queda por confirmar en la reunión del lunes 7. Es un detalle menor, pero dos personas creyendo que la otra hace el README es exactamente el tipo de hueco que aparece el día de la entrega.

---

## Lo que no cambió, y por qué

**El semáforo de la bitácora se queda como está.** Se propuso agregar un estado «bloqueada». No se hizo: un bloqueo ya tiene su propio issue con etiqueta `bloqueo` y su renglón en la hoja *Bloqueos*. Duplicar el estado en dos lugares lleva a que se actualice en uno solo.

**Las fichas cubren la semana 1 y no las catorce.** Una ficha de la semana 9 escrita hoy sería especulativa: depende de decisiones que no se han tomado. Se escriben en la reunión semanal, cuando ya se sabe qué se recorrió. La plantilla está en el repositorio y escribirlas es parte de cerrar la reunión.

**El panel sigue sin estado compartido.** Las palomitas viven en el navegador de cada quien. Hacer que el panel escriba el avance real duplicaría al tablero de GitHub, que ya es la fuente de verdad, y dos fuentes de verdad no son dos: son ninguna.
