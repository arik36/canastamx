# Cómo trabajamos

Cinco personas, cinco frentes, ninguna oficina. Lo que sostiene un equipo remoto no es la buena voluntad: es que todos sepan qué se espera de ellos, cuándo, y cómo se ve terminado.

Este archivo es el acuerdo. Se lee una vez completo y después se consulta.

---

## 1. El ritmo

| Cuándo | Qué | Cuánto dura |
|---|---|---|
| **Todos los días, antes de las 21:00** | Reporte asíncrono en el chat | 2 minutos |
| **Una vez por semana, día y hora fijos** | Reunión de equipo | 45 minutos |
| **Viernes** | Cada quien deja su rama incorporada o explica por qué no | — |

El horario fijo de la reunión se acuerda el **viernes 11 de septiembre** y no se mueve el resto del semestre. Un equipo que renegocia el horario cada semana termina reuniéndose cada tres.

### El reporte diario

Tres líneas en el chat del equipo. No es vigilancia; es lo que permite que alguien detecte que estás atorado antes de que pierdas tres días.

```
Ayer: terminé el perfilado nivel 1, 340 mil filas, 12% de nulos en la columna de marca.
Hoy: perfilado nivel 2, distribución de precios por categoría.
Atorada en: nada.
```

Si no trabajaste, se dice:

```
Ayer: nada, tuve examen de Redes.
Hoy: retomo el docker-compose.
Atorado en: nada.
```

**Decir "no avancé" no tiene costo. Desaparecer sí.** El problema nunca es un día perdido; es enterarse el jueves de que llevas una semana sin poder avanzar.

### La reunión semanal

Cuarenta y cinco minutos, cámara encendida, agenda fija:

1. **Cinco minutos** — se abre el tablero y se lee. Qué se cerró, qué sigue en curso, qué se retrasó.
2. **Veinte minutos** — cada quien tres minutos: qué entregó, qué sigue, qué necesita de otro.
3. **Diez minutos** — puntos de acuerdo entre frentes. El contrato OpenAPI entre C1 y C2. Los indicadores que D necesita de A. Los servicios que B tiene que levantar para todos.
4. **Diez minutos** — se cargan al tablero las tareas de la semana siguiente, con dueño y fecha.

Quien no puede asistir deja su parte escrita en el chat **antes** de la reunión. La reunión no se reagenda por una ausencia.

---

### Las iteraciones

El protocolo compromete Scrum adaptado: **iteraciones de dos semanas alineadas con las fechas de entrega institucionales**, reunión semanal breve de sincronización, revisión al cierre de cada iteración y retrospectiva ligera enfocada en redistribuir carga cuando alguien está saturado por evaluaciones de otras materias.

También compromete algo que conviene tener presente porque suena a omisión y no lo es: **no hay reunión diaria.** Es impracticable con horarios escolares heterogéneos, y por eso se sustituye por la actualización asíncrona del párrafo anterior. Si el asesor pregunta por el *daily*, esa es la respuesta y está justificada en el documento.

Las iteraciones caen así:

| Iteración | Semanas | Cierra en |
|---|---|---|
| I1 | 1–3 | Entrega del 18 de septiembre |
| I2 | 4–6 | Entrega del 9 de octubre |
| I3 | 7–8 | Revisión interna |
| I4 | 9–10 | Entrega del 4 de noviembre |
| I5 | 11–12 | Entrega del 18 de noviembre |
| I6 | 13–14 | Presentaciones de diciembre |

**Al cierre de cada iteración**, diez minutos extra en la reunión: qué se comprometió, qué se entregó, y una sola pregunta de retrospectiva — *¿alguien viene sobrecargado y hay que mover algo?* No es ceremonia; es lo que evita que una persona cargue con el proyecto en noviembre.

---

## 2. La regla de las 24 horas

**Si llevas 24 horas atorado en lo mismo, es obligatorio pedir ayuda.** No es una sugerencia amable, es una regla operativa.

Cómo se pide bien:

```
Atorado: el contenedor de Postgres analítico no arranca.
Qué intenté: cambié el puerto a 5433, revisé que no hubiera otro Postgres corriendo,
borré el volumen y volví a levantar.
Error exacto: FATAL: database files are incompatible with server
Enlace: [captura o el log completo en un gist]
```

Cómo **no** se pide:

```
no me sirve docker alguien sabe
```

Un problema bien planteado se resuelve en diez minutos. Uno mal planteado consume media reunión.

**Si el bloqueo depende de otro integrante**, se abre un issue con la etiqueta `bloqueo`, se asigna a quien lo puede resolver y se menciona en el chat. Los bloqueos entre frentes son la causa número uno de que un proyecto de cinco personas se atore.

---

## 3. El ciclo de una tarea

```
issue en el tablero  →  me asigno  →  rama  →  commits  →  push
       →  solicitud de incorporación  →  revisión de otro  →  incorporada  →  issue cerrado
```

Los detalles de Git están en [`git-paso-a-paso.md`](./git-paso-a-paso.md). Aquí van las reglas que lo rodean.

**Si una tarea no está en el tablero, no existe.** No se evalúa, no cuenta como avance y no se le reclama a nadie. Trabajar en algo que no está en el tablero es trabajo que el equipo no puede ver, y por lo tanto no puede aprovechar.

**Ninguna tarea vive más de una semana.** Si algo te va a tomar dos semanas, no es una tarea: son dos. Pártela al crearla.

**Una rama, una solicitud, un revisor.** El revisor por defecto está en la tabla del manual de Git.

---

## 4. Qué significa "terminado"

Una tarea está terminada cuando se cumplen las cuatro:

- [ ] El criterio escrito en el issue —la columna **cómo saber que quedó**— se cumple, verificable por otra persona.
- [ ] El código o documento está incorporado a `main`, no en una rama suelta.
- [ ] La integración continua está en verde.
- [ ] Otro integrante lo aprobó.

"Ya casi" no es un estado. "Está en mi máquina" no es un estado. Si no está en `main`, para el equipo no existe.

---

## 5. El semáforo

Cada tarea del tablero tiene uno de estos estados. El color se asigna en la reunión semanal y se refleja en la bitácora que se entrega al asesor.

| Estado | Significa | Qué se hace |
|---|---|---|
| 🟢 **Aprobada** | Terminada en tiempo y con revisión | Nada, se cierra |
| 🟡 **Parcial** | Se hizo, pero no cumple el criterio completo, o se entregó tarde | Se anota qué falta y se pone fecha nueva **en la misma semana** |
| 🔴 **Retrasada** | No se hizo y no hay fecha nueva | Se replantea en la reunión: ¿se recorta, se reasigna o se descarta? |
| ⚪ **En curso** | Dentro de plazo, avanzando | Se reporta a diario |
| ⬜ **Sin empezar** | Aún no toca, o toca y no ha arrancado | — |

Dos observaciones sobre el rojo, que importan más que el rojo mismo:

- **Un rojo aislado no es un problema.** Todos van a tener rojos. La gente tiene exámenes, se enferma, se le cae el disco duro.
- **Dos rojos seguidos del mismo frente sí lo son**, y se atienden en la reunión hablando con la persona, no acumulando reclamos. Casi siempre la causa real es que la tarea estaba mal dimensionada o que faltaba algo de otro frente.

---

## 6. Dónde se dice qué

| Canal | Para qué | No para |
|---|---|---|
| **Chat del equipo** (WhatsApp o Discord) | Reporte diario, avisos urgentes, "ya subí mi PR" | Decisiones técnicas. Se pierden. |
| **Issues de GitHub** | Todo lo que es una tarea o un bloqueo. Discusión técnica de esa tarea. | Charla |
| **Comentarios en la solicitud** | Revisión de código, dudas sobre líneas concretas | — |
| **`docs/adr/`** | Decisiones de arquitectura: fecha, contexto, decisión, alternativas descartadas | — |
| **Google Drive** | Documentos de Word, presentaciones, videos | Código o documentación técnica |
| **Reunión semanal** | Acuerdos entre frentes, replanteo de lo retrasado | Reportar lo que ya está en el tablero |

**Cuando el equipo elija entre dos opciones técnicas, se escribe un ADR.** Media cuartilla basta. En diciembre nadie recuerda por qué se descartó Airflow, y el asesor lo va a preguntar.

---

## 7. Reglas de suplencia

Cada frente tiene un segundo que puede intervenir si su dueño se cae:

| Frente | Dueño | Segundo |
|---|---|---|
| Datos y plataforma | A · Ariadne | B |
| Infraestructura y CI | B · Ari Adair | A |
| Servicio de dominio | C1 · Liseth | C2 |
| Cliente móvil | C2 · Oscar | C1 y D |
| Cliente web y maquetación | D · Karen | C2 |

El segundo **no hace el trabajo del dueño**. El segundo es quien puede leer ese código y sostener una demostración si el dueño falta el día de la presentación. Para eso, el segundo revisa las solicitudes de su frente: revisar es cómo se entera de lo que pasa ahí.

---

## 8. Reporte al asesor

Cada entrega institucional se acompaña de la bitácora exportada del tablero, con el semáforo por integrante y por semana. El archivo `CanastaMX_Bitacora.xlsx` está en Drive y lo mantiene A.

No es burocracia: es la evidencia de que el trabajo se repartió y se cumplió, y es lo primero que un asesor pide cuando quiere saber quién hizo qué en un equipo de cinco.

---

## 9. Lo que hunde proyectos escolares, y cómo lo evitamos

| Riesgo real | Qué lo evita aquí |
|---|---|
| "En mi máquina sí corre" | Todo levanta con `docker compose up`. Si no levanta en la máquina de otro, no está terminado. |
| Nadie integra hasta la última semana | Toda rama entra por solicitud en menos de una semana. La integración continua corre en cada cambio. |
| Una persona carga con todo | Cada frente tiene un solo dueño y un segundo. El tablero hace visible el desbalance. |
| Se descubre en octubre que la fuente no sirve | El perfilado se hace la primera semana y la decisión se escribe en un ADR el 7 de septiembre. |
| Se llega a diciembre sin poder explicar por qué se eligió algo | Cada decisión técnica queda en `docs/adr/`. |
| El día de la presentación falla la red | Hay video de respaldo grabado desde la semana 14. |
| Nadie sabe qué hizo el otro | Reporte diario, reunión semanal, revisión cruzada de solicitudes. |
