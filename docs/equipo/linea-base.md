# La línea base: qué existe en `main` antes de ramificar

Cinco personas van a crear ramas por área. Si cada quien ramifica desde un `main` distinto —uno con `.gitignore` y otro sin él, uno con la estructura de carpetas y otro sin ella— las ramas divergen desde el primer día y el conflicto llega al primer intento de incorporar.

Este documento delimita qué tiene que existir antes de que **nadie** cree una rama.

---

## La regla

**Nadie crea una rama hasta que `main` contenga la línea base v0 y su clon la tenga.**

Se comprueba con un comando, no con un mensaje en el chat:

```bash
bash infra/scripts/verificar-base.sh A     # cambia por tu clave: A, B, C1, C2 o D
```

Si el script dice **PUEDES CREAR TU RAMA**, ramificas. Si dice que no, arregla lo que te señale o avisa en el chat. No ramifiques «de mientras».

---

## Por qué esto importa más de lo que parece

El caso que se va a dar si no se respeta:

> Liseth clona el repositorio a las diez de la noche del miércoles, antes de que A haya subido el `.gitignore`. Crea `feat/lyl-esqueleto-spring`, genera el proyecto de Maven, compila, y hace `git add .`. Maven ya creó `target/` con cientos de archivos compilados. Todos entran al commit. El jueves abre la solicitud y trae mil doscientos archivos, la revisión es imposible, y `main` queda con basura que hay que limpiar del historial.

Lo mismo con `node_modules/` en el caso de Oscar y Karen, y con `.venv/` en el de Ariadne.

**El `.gitignore` es el archivo más urgente del repositorio**, más que el README y más que el `docker-compose.yml`. Tiene que existir antes de que alguien escriba su primera línea de código.

---

## Nivel 0 · antes de la primera rama de cualquiera

Lo sube **A**, en un solo commit, **antes del arranque del lunes 7**. Sin excepciones y sin ramas de nadie más en paralelo.

| Qué | Por qué es bloqueante |
|---|---|
| **`.gitignore`** | Sin él entran `target/`, `node_modules/`, `.venv/` y archivos de datos. Es el más urgente de todos |
| **Estructura de carpetas** con `.gitkeep` | Sin ella, cada quien inventa dónde va lo suyo y hay que reorganizar en octubre |
| **`.env.example`** | Define qué variables existen. Sin él, cada quien inventa nombres distintos |
| **`README.md` inicial** | Punto de entrada. Aunque esté a medias |
| **`docs/equipo/`** completo | El manual, las fichas y el mapa de dependencias. Es lo que la gente lee antes de trabajar |
| **Las 14 plantillas-esqueleto** | Para que nadie parta de un archivo vacío |
| **`.github/`** | Plantillas de issue y de solicitud, y el flujo de integración continua |
| **`infra/scripts/`** | Los guiones de estructura, siembra y verificación |
| **`main` protegida, etapa 1** | Requerir solicitud y una aprobación. Las verificaciones vienen en la etapa 2, ver abajo |
| **Los cuatro colaboradores aceptaron** | Una invitación sin aceptar se ve igual que un repositorio que no existe |

Cuando esos diez puntos están, A marca el punto con una etiqueta:

```bash
git switch main && git pull
git tag -a base-v0 -m "Línea base: estructura, gitignore, manual y plantillas"
git push origin base-v0
```

**La etiqueta es la señal de arranque.** El script de verificación la busca; si no está, nadie ramifica.

---

## Lo que NO va en la línea base todavía

Esto importa igual que la lista anterior, y es menos obvio. Meterlas en la línea base hace más daño que dejarlas fuera.

| Qué | Por qué se espera | Cuándo entra |
|---|---|---|
| **Verificaciones obligatorias en `main`** | GitHub solo deja seleccionar canalizaciones **que ya corrieron alguna vez**. Al cerrar la línea base no ha corrido ninguna: la lista está vacía y no hay nada que marcar | Etapa 2, miércoles 9, cuando B cierre T009 |
| **`docker-compose.yml` con Traefik activo** | Traefik es T008, del martes. La plantilla lo trae comentado a propósito | Martes 8, por rama de B |
| **Código de cualquier servicio** | Cada quien lo sube en su rama. Es justamente el punto de tener línea base | Del lunes 7 en adelante |

**Sí va el archivo `ci.yml`**, pero ojo con cómo: cada trabajo revisa primero si el proyecto que le toca ya existe, y si no, lo dice y se salta **en verde**. El lunes 7 `services/domain-service/` solo tiene un `.gitkeep`; una canalización que intentara compilarlo saldría **roja en toda solicitud del equipo**, incluidas las de documentación, y nadie entendería por qué su cambio falla. Con la guarda, empieza a compilar sola en cuanto C1 sube su `pom.xml`, sin que nadie edite el archivo.

---

## La protección de `main` va en dos etapas

Es la parte que más confunde, y por eso va aparte.

### Etapa 1 · antes del arranque, la hace A

Settings → Branches → Add branch protection rule

- Branch name pattern: `main`
- ☑ Require a pull request before merging
- ☑ Require approvals: **1**
- ☐ Require status checks — **apagada.** No hay ninguna que seleccionar todavía
- ☑ Do not allow bypassing the above settings

Con esto ya nadie escribe directo en `main`, que es el 90% del valor.

### Etapa 2 · miércoles 9, la hace B al cerrar T009

Después de que su solicitud de prueba salga verde, los trabajos ya aparecen en la lista de GitHub:

- Misma regla → ☑ **Require status checks to pass before merging**
- Selecciona **Dominio (Java)**, **Datos (Python)** e **Higiene**

Sin este segundo paso la canalización corre y reporta, pero no impide nada: es un reporte, no una compuerta.

---

## Nivel 1 · lo que cada frente necesita, además

Estos no bloquean a todos: bloquean a una persona.

| Quién quiere ramificar | Necesita que ya esté en `main` | Quién lo sube | Cuándo |
|---|---|---|---|
| **A** — perfilado y datos | Solo el nivel 0 | — | lun 7 |
| **B** — compose | Solo el nivel 0 | — | lun 7 |
| **C1** — Spring | Solo el nivel 0 | — | lun 7 |
| **C2** — Expo | Solo el nivel 0 | — | lun 7 |
| **D** — inventario y wireframes | Solo el nivel 0 | — | lun 7 |
| **B** — Traefik y `.env.example` con valores | `docker-compose.yml` | B, en su propia rama anterior | mar 8 |
| **B** — integración continua | `services/domain-service/` con `pom.xml` | C1 | mié 9 |
| **A** — contrato de datos (semana 2) | `docs/datos/diccionario-qqp.md` lleno | C2 | lun 7 |
| **A** — ingesta (semana 4) | `docker-compose.yml` funcionando | B | lun 7 |
| **D** — sistema de diseño (semana 2) | `docs/analisis/inventario-vistas.md` lleno | D, tarea anterior | lun 7 |

El lunes 7, con el nivel 0 listo, **los cinco pueden ramificar en paralelo desde la mañana**. Ese es el punto de haber cerrado el nivel 0 antes del arranque.

---

## Nivel 2 · lo que se acuerda antes de construir contra ello

No son archivos: son acuerdos. Ramificar antes de que existan produce trabajo que hay que rehacer.

| Acuerdo | Antes de que alguien construya | Cuándo se cierra |
|---|---|---|
| ¿La fuente sirve? ¿Con qué recorte? | La ingesta de A | ADR 001, viernes 11 |
| ¿H3 se sostiene al 85%? | La reconciliación de A | ADR 001, viernes 11 |
| Los seis indicadores de la consola | La consola de D | Ya están: objetivo específico 4 del protocolo |
| Las ocho vistas | Los wireframes de D | Ya están: sección 10.7 del protocolo |
| Los tres contratos OpenAPI | El cliente web y el móvil contra el dominio | Semana 5, coordina B |

---

## Cómo se ve en la práctica, el lunes 7

```bash
# 1. Traes lo último
git switch main
git pull

# 2. Verificas que puedes ramificar
bash infra/scripts/verificar-base.sh C1

#    → si dice PUEDES CREAR TU RAMA, sigue.
#    → si no, arregla lo que señale o avísalo en el chat.

# 3. Ahora sí
git switch -c feat/lyl-esqueleto-spring
```

Tres comandos. El de en medio es el que evita el problema.

---

## Qué hacer si ya ramificaste antes de tiempo

Pasa, y tiene arreglo. No tires tu trabajo.

```bash
# 1. Guarda lo que llevas
git add .
git commit -m "wip: avance antes de la línea base"

# 2. Trae la línea base a tu rama
git switch main
git pull
git switch tu-rama
git merge main

# 3. Si entraron archivos que no debían (target/, node_modules/, .venv/)
git rm -r --cached target/          # o node_modules/, .venv/
git commit -m "chore: saca del control de versiones lo que ignora .gitignore"
```

El paso 3 saca los archivos del repositorio pero **los conserva en tu disco**. Si ya habías hecho `push` con ellos, siguen en el historial: dilo en el chat y B decide si vale la pena limpiarlo.

---

## Después de la semana 1

La línea base no es solo del arranque. Cada vez que algo se vuelve **base compartida** —el contrato de datos, el paquete de tipos de TypeScript, los tres OpenAPI— se marca con una etiqueta y se anuncia en el chat:

```bash
git tag -a base-contratos-v1 -m "Contratos OpenAPI acordados entre los tres servicios"
git push origin base-contratos-v1
```

Así, cuando alguien pregunte «¿desde dónde ramifico?», la respuesta es un nombre concreto y no «desde lo último, creo».
