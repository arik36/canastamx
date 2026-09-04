# Entrega 3 — Avance de construcción y pruebas

**Miércoles 4 de noviembre de 2026** · Hito `E3 — Construcción`

Aquí se demuestra que el sistema existe y que se prueba solo. El protocolo compromete cuatro niveles de prueba para esta fecha, y esa tabla es la que hay que poder mostrar en verde.

---

## Los cuatro niveles de prueba que se demuestran

| Nivel | Qué verifica | Herramienta | Quién |
|---|---|---|---|
| **Unitarias de servicios** | Lógica de dominio aislada: costo de canasta, disparo de alerta, validación de credenciales | JUnit 5 | C1 |
| **Unitarias de datos** | Funciones de transformación: parseo de unidades, normalización de cadenas, comparación difusa | pytest | A |
| **De datos** | El contenido de las tablas: unicidad, obligatoriedad, rangos, integridad referencial, frescura | Pandera y pruebas de dbt | A |
| **De front** | Responsivo en tres puntos de quiebre, manejo de sesión, navegabilidad | Playwright en web, pruebas de Expo en móvil | D y C2 |

Las de integración (B) van hasta el 18 de noviembre. No se prometen para esta fecha.

---

## Qué se demuestra, no qué se dice

Esta entrega se defiende con la pantalla compartida, no con el documento.

| Quién | Qué demuestra en vivo |
|---|---|
| A | El flujo corre de la fuente a la capa de consumo. El esquema estrella tiene datos. La interfaz analítica responde a cuatro endpoints. Cobertura y precisión de la reconciliación medidas sobre 200 pares. |
| B | La canalización de integración continua corriendo en una solicitud real, con las suites en verde. El sistema desplegado en la nube, accesible por HTTPS. |
| C1 | Autenticación con token: entrar, operar, expirar, cerrar sesión. Cobertura de pruebas del dominio. |
| C2 | La app en un teléfono real: acceso, búsqueda y canasta con datos del sistema, no simulados. |
| D | Tablero analítico con datos reales. Los tres puntos de quiebre en vivo, redimensionando la ventana. Rutas protegidas que redirigen al acceso. |

---

## Las tres evidencias que exige el protocolo para el front

Se verifican en esta fecha y conviene tenerlas grabadas, no solo demostrables:

1. **Comportamiento responsivo.** Cada vista web en escritorio, tableta y teléfono. Ninguna tabla ni gráfica produce desplazamiento horizontal en el punto más estrecho. *Evidencia: capturas de las cuatro vistas en los tres anchos, doce imágenes.*

2. **Manejo de sesión.** El token tiene vigencia acotada. El cierre de sesión lo invalida. Las rutas protegidas redirigen al acceso cuando no hay sesión válida. La expiración se maneja sin perder la vista en curso. *Evidencia: prueba de Playwright que recorre los cuatro escenarios, en verde.*

3. **Navegabilidad.** Toda vista es alcanzable en un máximo de tres interacciones desde el punto de entrada. Existe retorno explícito. La ruta activa se refleja en la barra de navegación. *Evidencia: tabla de las ocho vistas con el conteo de interacciones desde el inicio.*

---

## La medición de H3, que es investigación y no ingeniería

En la semana 10, A mide **cobertura y precisión de la reconciliación sobre una muestra aleatoria de 200 pares**. Es la primera cifra experimental del trabajo y se reporta aquí aunque no sea favorable.

Si la cobertura sale en 71% y la meta era 85%, se reporta 71% y se explica por qué, con el dato del perfilado nivel 3 de septiembre. Ajustar la meta después de medir es lo contrario de lo que se hace en investigación; explicar por qué la meta no se alcanzó es exactamente lo que se hace.

---

## Checklist de cierre — lunes 2 de noviembre

- [ ] Las cuatro suites de prueba corren y están en verde en la canalización
- [ ] Sistema accesible por HTTPS desde fuera de la red del equipo
- [ ] Capturas de responsivo: cuatro vistas × tres puntos de quiebre
- [ ] Prueba de sesión automatizada, en verde
- [ ] Tabla de navegabilidad de las ocho vistas
- [ ] Medición de cobertura y precisión de la reconciliación, con su muestra documentada
- [ ] Build de la app móvil instalable, probado en un teléfono que no sea el de C2
- [ ] Guión de demostración escrito y cronometrado
- [ ] `docs/entregas/2026-11-04/` con enlaces y fecha
- [ ] Bitácora exportada, semanas 7 a 10

---

## El error clásico de esta entrega

Demostrar con datos simulados y esperar que no pregunten. Preguntan. Si un número viene de un `mock`, se dice que viene de un `mock` y se explica qué falta para que venga del flujo real. La honestidad técnica se califica mejor que la demostración maquillada, y además es más fácil de defender.

---

## Antes de que empiece el congelamiento

Después del 18 de noviembre no se agrega funcionalidad. Lo que no esté construido para entonces, no va a existir. Esta entrega es el último momento razonable para decir en voz alta *"esto no va a estar"* y recortar el alcance de forma ordenada, en lugar de descubrirlo el 17 de noviembre a medianoche.
