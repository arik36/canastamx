# Entrega 5 — Experimento, cierre y presentaciones

**2, 7 y 9 de diciembre de 2026** · Hito `E5 — Presentación`

Dos semanas: la 13 es el experimento, la 14 es la presentación. **Ninguna de las dos lleva desarrollo de funcionalidad nueva.** Los proyectos escolares no se caen construyendo, se caen presentando.

---

# Semana 13 · 23 al 29 de noviembre — el experimento

Es la parte que convierte esto en investigación y no en un proyecto de programación. Todo lo construido en catorce semanas existe para poder llenar una tabla de resultados.

## El diseño, según el protocolo

Cuasiexperimento de inyección controlada de fallas. Se toma un lote verificado como correcto, se generan copias con defectos deliberados, se procesan por el flujo y se registra el comportamiento.

**Cinco tipologías de falla**, mínimo treinta corridas en total:

| # | Tipología |
|---|---|
| 1 | Valores numéricos fuera de rango admisible |
| 2 | Valores ausentes en campos obligatorios |
| 3 | Modificación del esquema en origen: columna renombrada, eliminada o con tipo alterado |
| 4 | Duplicación de registros |
| 5 | Ausencia de actualización que rompe el umbral de frescura |

**Tres variables por corrida:**

1. ¿Se detectó la falla? (sí / no)
2. ¿Los registros defectuosos quedaron contenidos en cuarentena sin alcanzar la capa de consumo? (sí / no)
3. Tiempo entre la ingesta y la señalización del incidente (minutos)

**Corridas de control:** las mismas mediciones con las validaciones **desactivadas**. Sin control no hay forma de atribuir el resultado al subsistema de calidad en lugar de al azar, y esa es la primera pregunta que hace un asesor con formación en método.

## Reparto de la semana 13

| Quién | Qué | Queda en |
|---|---|---|
| A | Especifica las cinco tipologías y el procedimiento de cada corrida, **antes** de que B ejecute nada | `docs/experimento/protocolo.md` |
| B | **Ejecuta las 30 corridas** sobre el entorno aislado, más las de control. Registra las tres variables por corrida | `docs/experimento/bitacora.csv` |
| A | Calcula tasa de detección, tasa de contención y latencia media. Contrasta las cuatro hipótesis | `docs/experimento/resultados.md` |
| A | Redacta el reporte de hallazgos económicos: índice de canasta, dispersión y correlación contra el INPC | `docs/experimento/hallazgos.md` |
| C1 | Documentación técnica del dominio y manual de operación | `docs/` |
| C2 | Documentación de la app móvil y capturas para la presentación | `docs/` |
| D | Documentación de la interfaz web y capturas para la presentación | `docs/` |

## La tabla de resultados

Es la lámina que decide la calificación. Se llena con lo que salió, no con lo que se esperaba.

| Hipótesis | Criterio comprometido | Resultado obtenido | ¿Se cumple? |
|---|---|---|---|
| H1 Contención | ≥ 95% de filas defectuosas en cuarentena | | |
| H2 Detección | < 15 min entre ingesta y señalización | | |
| H3 Reconciliación | Cobertura ≥ 85%, precisión ≥ 90% | | |
| H4 Validez del índice | Correlación positiva y significativa con el INPC | | |

**Una hipótesis que no se cumple no es un fracaso: es un resultado.** Lo que sí es un fracaso es no poder explicar por qué. Si H2 sale en 22 minutos, se dice 22 minutos y se explica dónde está el cuello de botella. Un equipo que reporta un resultado adverso con su explicación demuestra más dominio que uno cuyos cuatro números salen redondos.

---

# Semana 14 · 30 de noviembre al 6 de diciembre — el cierre

| Quién | Qué | Queda en |
|---|---|---|
| Equipo | Guión de demostración escrito y **ensayado dos veces completas** | `docs/entregas/final/` |
| Equipo | **Video de respaldo grabado.** Si la red falla, el video salva la calificación | Drive, enlace en el README |
| Equipo | README final con diagrama de arquitectura | `README.md` |
| Equipo | Documento de traspaso: deuda técnica conocida y líneas de continuación | `docs/traspaso.md` |
| Equipo | Lámina de métricas: filas procesadas, validaciones activas, incidentes detectados, resultado de las hipótesis | `docs/entregas/final/` |

---

# Las presentaciones

**2, 7 y 9 de diciembre.** Presenta el responsable de cada parte; no hay un vocero único. Un equipo donde solo una persona sabe explicar el proyecto levanta la sospecha de que solo una persona lo hizo.

## Estructura de 15 minutos

| Min | Quién | Qué |
|---|---|---|
| 0–2 | A | El problema, con los datos duros. Los flujos fallan en silencio y tardan horas en detectarse |
| 2–3 | A | Qué se construyó, en un diagrama de arquitectura |
| 3–5 | B | Cómo se levanta y dónde está desplegado |
| 5–7 | C1 y C2 | Dominio y app móvil, en un teléfono real |
| 7–9 | D | Tablero analítico y consola de observabilidad |
| 9–13 | A y B | **La demostración de inyección de fallas, en vivo.** Los cinco pasos |
| 13–15 | A | La tabla de resultados de las cuatro hipótesis. Conclusiones y líneas de continuación |

## La demostración, paso a paso

1. Consola en verde: última corrida exitosa, seis indicadores sanos, cero incidentes.
2. B inyecta un lote con precios negativos y una columna renombrada.
3. La consola cambia de estado. Aparece el incidente. **Se muestra el reloj.**
4. Se abre la tabla de cuarentena: filas rechazadas con su motivo y su regla violada.
5. Se muestra que la capa de consumo no las tiene y que el tablero sigue correcto.

Seis minutos. Ensayada dos veces. Grabada.

---

## Preguntas que van a hacer, y quién las contesta

| Pregunta | Quién responde |
|---|---|
| ¿Por qué Dagster y no Airflow? | A — está en `docs/adr/` |
| ¿Cómo saben que el dato es correcto y no solo que el proceso corrió? | A — es la tesis entera del trabajo |
| ¿Qué pasa si PROFECO cambia el formato del archivo? | A — flujo alterno B de CU-02: el esquema no coincide y el proceso se detiene |
| ¿Esto corre en otra máquina? | B — `docker compose up`, y la guía la verificó alguien más |
| ¿Por qué el índice no coincide exactamente con el INPC? | A — metodologías distintas; las divergencias están documentadas |
| ¿Quién hizo qué? | Cada quien la suya. La bitácora lo respalda |
| ¿Qué harían distinto? | Cualquiera — está en el documento de traspaso |

**Si nadie sabe contestar una pregunta, se dice que no se sabe.** Inventar en una presentación técnica se nota, y cuesta más caro que el hueco.

---

## Checklist final — lunes 30 de noviembre

- [ ] Tabla de resultados de las cuatro hipótesis, llena con datos reales
- [ ] `docs/experimento/bitacora.csv` con las 30 corridas más las de control
- [ ] Reporte de hallazgos económicos escrito
- [ ] README final con diagrama de arquitectura
- [ ] Documento de traspaso con deuda técnica y líneas de continuación
- [ ] Presentación armada, con la lámina de métricas
- [ ] Guión escrito: quién dice qué, en qué minuto
- [ ] **Dos ensayos completos cronometrados**
- [ ] **Video de respaldo grabado y subido a Drive**
- [ ] Sistema desplegado y funcionando, verificado el mismo día de cada presentación
- [ ] Repositorio hecho público después de la última presentación
- [ ] Bitácora completa exportada, las 14 semanas

---

## Lo último

El repositorio se vuelve público después del 9 de diciembre. A partir de ahí deja de ser una tarea escolar y se convierte en lo que cinco personas pueden enseñar en una entrevista de trabajo. Vale la pena que el README final esté bien escrito: es lo primero que va a ver alguien que no los conoce.
