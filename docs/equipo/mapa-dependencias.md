# Mapa de dependencias

Qué tarea bloquea a cuál. En un equipo con horarios distintos y sin oficina compartida, la causa más común de una semana perdida no es que alguien no trabaje: es que alguien trabaje **sobre un insumo que todavía no existe**, o que espere en silencio algo que ya estaba listo.

Este documento resuelve las dos cosas.

---

## La dependencia raíz: la línea base

Antes de la primera flecha de este mapa hay una que no aparece dibujada, porque no es de una tarea a otra sino de **todas** a un punto de partida.

**Nadie crea una rama hasta que `main` tenga la línea base completo.** Qué es exactamente y cómo se verifica está en [`linea-base.md`](./linea-base.md). En corto: `.gitignore`, la estructura de carpetas, las guías, las plantillas y las plantillas de issue y solicitud, más los cinco colaboradores con la invitación **aceptada**.

Lo deja listo A el miércoles 2. Cada quien lo comprueba antes de ramificar:

```bash
git switch main && git pull
bash infra/scripts/verificar-base.sh
```

Si sale algo en rojo, no se ramifica: se avisa. Una rama creada antes dla línea base no tiene `.gitignore`, y la primera instalación de dependencias mete `node_modules/` al repositorio.

---

## La regla, en una línea

**Cuando termines una tarea que bloquea a otra persona, se lo dices en el chat. Con su nombre.**

No basta con cerrar el issue. Cerrar un issue es un evento que nadie está mirando; un mensaje con el nombre de alguien, sí.

```
@Oscar ya está el enlace del diccionario de QQP:
datos.profeco.gob.mx/diccionarioDatosQQP.php
Ya puedes arrancar T013.
```

Y del otro lado: **si estás esperando algo, dilo el mismo día**. No a las 48 horas, no en la reunión del lunes.

---

## Semana 1 · el grafo completo

```
                          ┌──────────────────────────────────┐
                          │  T001 · A                        │
                          │  Estructura del repositorio      │  jue 3 · prioridad 1
                          └───────────────┬──────────────────┘
                                          │  desbloquea a los cuatro
        ┌──────────────┬──────────────────┼──────────────────┬──────────────┐
        ▼              ▼                  ▼                  ▼              ▼
   ┌─────────┐   ┌──────────┐      ┌───────────┐      ┌──────────┐   ┌──────────┐
   │ T007 B  │   │ T011 C1  │      │  T014 C2  │      │ T015 D   │   │ T002 A   │
   │ compose │   │ Spring   │      │  Expo     │      │inventario│   │ descarga │
   └────┬────┘   └────┬─────┘      └───────────┘      └────┬─────┘   └────┬─────┘
        │             │                                    │              │
        ▼             ▼                                    ▼              ├──────────┐
   ┌─────────┐   ┌──────────┐                   ┌──────────┴───────┐      ▼          ▼
   │ T008 B  │   │ T012 C1  │                   ▼                  ▼   ┌──────┐ ┌─────────┐
   │ Traefik │   │ dominio  │              ┌────────┐        ┌─────────┐│T003 A│ │ T013 C2 │
   └─────────┘   └──────────┘              │T016 D  │        │ T017 D  ││perf 1│ │diccion. │
        ▲                                  │tablero │        │ consola │└──┬───┘ └─────────┘
        │                                  └────────┘        └────┬────┘   │
   ┌────┴─────┐                                                   │        ▼
   │ T011 C1  │───────────────────┐                    visto bueno│    ┌────────┐
   └──────────┘                   ▼                        de A ──┘    │T004 A  │
                            ┌──────────┐                               │perf 2  │
                            │ T009 B   │                               └───┬────┘
                            │ CI       │                                   ▼
                            └──────────┘                               ┌────────┐
                                                                       │T005 A  │
   T010 B (Oracle + Student Pack) ── no depende de nada ──┐            │perf 3  │
                                                          │            └───┬────┘
                                                          │                ▼
                                                          │           ┌─────────┐
                                                          │           │ T006 A  │ dom 6
                                                          │           │ informe │
                                                          │           └────┬────┘
                                                          │                ▼
                                                          └──────►  ┌─────────────┐
                                                                    │  T018 EQUIPO│ lun 7
                                                                    │  Reunión    │
                                                                    └─────────────┘
```

---

## Las tres cadenas críticas

Una cadena crítica es una secuencia donde cada eslabón espera al anterior. Si un eslabón se atrasa un día, todo lo que sigue se atrasa un día.

### 1 · La cadena de datos — la que decide el semestre

```
T002 descarga → T003 perfilado 1 → T004 perfilado 2 → T005 perfilado 3 → T006 informe → T018 reunión
```

**Cinco tareas seguidas, todas de A, en tres días.** Es la cadena más larga y la más frágil del semestre, y termina en la reunión que decide si el proyecto sigue con esta fuente.

*Si se rompe:* la reunión del lunes se queda sin insumo y hay que reagendarla, lo que empuja el arranque de la semana 2.

*Cómo se protege:* si el jueves solo alcanza para descargar el archivo, se descarga y el perfilado 1 se recorre al viernes. La descarga es lo que no puede fallar, porque además desbloquea a C2.

### 2 · La cadena de arranque — la que desbloquea a todos

```
T001 estructura → T007 compose, T011 Spring, T014 Expo, T015 inventario
```

**Una tarea que desbloquea cuatro.** Es la única del semestre con esa forma.

*Si se rompe:* cuatro personas sin poder empezar. El costo es cuatro veces el retraso.

*Cómo se protege:* es la prioridad 1 del jueves de A, por encima incluso de la descarga de datos. Y el insumo que puede atrasarla —los usuarios de GitHub de los otros cuatro— se pide **hoy, miércoles 2**, no el jueves.

### 3 · La cadena silenciosa — la que se rompía sin que nadie lo notara

```
T011 Spring (C1) → T009 CI (B)
```

B necesita algo que compilar. Si C1 se atrasaba y no le avisaba, **B iba a pensar que su configuración estaba mal** y a perder horas depurando una canalización correcta. Peor: la canalización habría salido **roja en toda solicitud del equipo**, incluidas las de documentación, y nadie habría entendido por qué.

*Cómo se protege ahora:* la canalización ya no lo necesita. Cada trabajo revisa si el proyecto que le toca existe; si no, lo dice y se salta, en verde. Empieza a compilar sola en cuanto aparece el `pom.xml`. La dependencia sigue ahí, pero dejó de ser bloqueante.

*Lo que sí queda:* C1 le avisa a B al terminar, para que B vea el trabajo compilando de verdad antes de encender la etapa 2 de la protección de `main`.

---

## Las dependencias entre personas, resumidas

| Quien espera | Espera de | Qué | Cuándo se libera |
|---|---|---|---|
| **B, C1, C2, D** | A | La estructura del repositorio | jue 3, temprano |
| **C2** | A | El enlace del diccionario de QQP | jue 3, en cuanto lo tenga |
| **B** | C1 | El esqueleto de Spring, para tener qué compilar | jue 3, fin del día |
| **D** | A | Visto bueno del wireframe de la consola | vie 4 |
| **A** | C2 | El nombre real de las columnas de precio y categoría | vie 4, temprano |
| **C2** | C1 | Qué reglas tiene la canasta, para la pantalla | antes del lun 7 |
| **Los cinco** | A | El informe de perfilado | dom 6, para leerlo antes de la reunión |

---

## Cómo se ve esto en el tablero

Cada issue lleva su campo **Depende de** con el número de los issues que lo bloquean. En GitHub Projects:

1. Abre el issue que está bloqueado.
2. En el cuerpo, escribe `Bloqueado por #12`.
3. En el issue que bloquea, escribe `Bloquea a #17`.

GitHub no impone la dependencia —no impide que empieces— pero deja el rastro, y en la reunión semanal se ve de un vistazo qué está detenido y por culpa de qué.

**Si algo lleva más de 24 horas esperando a otra persona**, deja de ser una dependencia y se convierte en un bloqueo: se abre un issue con etiqueta `bloqueo`, se asigna a quien lo puede resolver y se dice en el chat.

---

## Semanas 2 en adelante

El mapa de cada semana se traza en la reunión, junto con las fichas. Son tres preguntas por tarea, y toman un minuto:

1. **¿Qué necesito que exista para empezar esto?**
2. **¿Quién lo produce y para cuándo?**
3. **¿A quién dejo detenido si no termino?**

Las dependencias que ya se ven venir en las próximas semanas, para tenerlas presentes:

| Semana | Dependencia | Por qué importa |
|---|---|---|
| 2 | El contrato de datos de A depende del diccionario de C2 | A declara tipos y rangos por columna; el diccionario dice qué significa cada una |
| 2 | Todo lo de A depende del compose de B | Sin base de datos no hay dónde escribir |
| 3 | La guía de arranque de B la verifica **otra persona** | Una guía que solo funciona en la máquina de quien la escribió no sirve |
| 5 | Los tres OpenAPI se acuerdan entre C1, D y A, coordinados por B | Si no se acuerdan aquí, en noviembre el front y el back no se hablan |
| 8 | El tablero de D consume la interfaz analítica de A | D puede avanzar con datos simulados, pero necesita la forma de la respuesta |
| 11 | La consola de D lee los seis indicadores reales de A | La pantalla más importante del proyecto depende de que A los exponga |
| 13 | B ejecuta las 30 corridas sobre el protocolo que A especifica | A especifica **antes** de que B ejecute, o las corridas no son comparables |
