# Entrega 4 — Versión final desplegada

**Miércoles 18 de noviembre de 2026** · Hito `E4 — Versión desplegada`

**Esta fecha marca el congelamiento de funcionalidad.** Después del 18 de noviembre no se construye nada nuevo: se experimenta, se documenta y se ensaya.

> ⚠️ **El lunes 16 de noviembre es festivo.** Esa semana tiene tres días hábiles, no cinco, y son los dos anteriores a la entrega. Todo lo que se pueda cerrar el **viernes 13** se cierra el viernes 13.

---

## Qué tiene que estar operando

| Componente | Quién | Criterio |
|---|---|---|
| Flujo bronze–silver–gold completo | A | Un lote entra crudo y sale como indicador consultable |
| **Compuertas de calidad y cuarentena** | A | Un registro defectuoso **no llega** a la capa de consumo; queda en `quarantine_registro` con su motivo |
| Consola de observabilidad con los seis indicadores | A y D | Los seis leen datos reales |
| Índice de canasta y dispersión, contrastados contra el INPC | A | El cálculo existe y la correlación está medida |
| Despliegue continuo y HTTPS | B | Un merge a `main` despliega solo. Certificado válido |
| Suite de pruebas de integración front-back | B | En verde en la canalización |
| Arnés de inyección de fallas | B | Construido y probado con una corrida piloto |
| Servicio de dominio completo | C1 | Autenticación, canastas, alertas, notificaciones por correo |
| App móvil instalable | C2 | Build probado en dos teléfonos distintos |
| Cliente web con las cuatro vistas | D | Tablero, detalle de producto, consola, cola de reconciliación |

---

## La demostración que define la calificación

Es el momento en que el objeto de investigación se vuelve visible. Se ensaya, se cronometra y se graba.

**El guión, en cinco pasos:**

1. **El sistema funcionando en verde.** Consola de observabilidad: última corrida exitosa, seis indicadores en buen estado, cero incidentes abiertos.
2. **Se inyecta una falla en vivo.** B lanza un lote con precios negativos y una columna renombrada.
3. **El sistema la atrapa.** La consola cambia de estado. Aparece el incidente. Se muestra el reloj: **cuánto tardó en señalizarlo**.
4. **Se abre la tabla de cuarentena.** Ahí están las filas rechazadas, con el motivo y la regla violada. Se muestra que la capa de consumo **no las tiene**.
5. **El tablero analítico sigue mostrando datos correctos.** Ese es el punto entero del trabajo: el dato malo no llegó a la pantalla de nadie.

Los cinco pasos, seis minutos. Ensayado dos veces antes del día. Grabado como respaldo.

---

## La semana 12 en tres días

Con el 16 festivo, la semana de la entrega es martes 17 y miércoles 18. Planeación realista:

| Cuándo | Qué |
|---|---|
| **Viernes 13** | Congelamiento técnico interno. Todo lo que va a la entrega tiene que estar incorporado a `main` este día |
| **Lunes 16** | Festivo. Descanso real, no "avanzo tantito" |
| **Martes 17** | Ensayo completo de la demostración, dos veces. Grabación del video de respaldo. Corrección de lo que salga mal en el ensayo |
| **Miércoles 18** | Entrega y presentación |

Si algo no está el viernes 13, no entra. Es más barato entregar con una funcionalidad menos y una demostración impecable, que con todo a medias y una demostración que se cae.

---

## Checklist de cierre — viernes 13 de noviembre

- [ ] `main` congelado: solo entran correcciones, no funcionalidad
- [ ] Sistema desplegado y accesible por HTTPS, probado desde una red que no sea la de nadie del equipo
- [ ] La demostración de inyección de fallas corre de principio a fin sin intervención manual
- [ ] Tabla de cuarentena poblada con casos reales
- [ ] Consola de observabilidad con los seis indicadores leyendo datos reales
- [ ] Build móvil instalable, probado en dos teléfonos
- [ ] Suite de integración en verde
- [ ] **Video de respaldo grabado.** Si la red falla el 18, el video salva la entrega
- [ ] Guión de demostración escrito, con quién dice qué y en qué minuto
- [ ] `docs/entregas/2026-11-18/` con enlaces, fecha y capturas
- [ ] Bitácora exportada, semanas 11 y 12

---

## El error clásico de esta entrega

Dejar la demostración para el día. Un sistema distribuido con cinco contenedores, una puerta de enlace y un certificado tiene diez formas de fallar en vivo, y todas se manifiestan cuando hay público. Ensayar dos veces no es exceso de cuidado: es lo que convierte una demostración en algo que se puede repetir.

Y el video de respaldo no es pesimismo. Es que la red del plantel falla y no está bajo su control.
