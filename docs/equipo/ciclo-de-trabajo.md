# El ciclo de trabajo, de principio a fin

**Para quien nunca ha trabajado con ramas.** Si hasta ahora hacías `git add`, `git commit` y `git push` sobre `main` y ya, este documento es para ti. Cuenta el ciclo completo una sola vez, en orden, explicando **por qué** existe cada paso.

`git-paso-a-paso.md` es el manual de consulta: se abre para buscar un comando. Este se lee completo, una vez, antes de empezar.

---

## Índice

| # | Sección |
|---|---|
| 1 | [Por qué dejamos de trabajar sobre `main`](#1-por-qué-dejamos-de-trabajar-sobre-main) |
| 2 | [El mapa: dónde vive tu trabajo](#2-el-mapa-dónde-vive-tu-trabajo) |
| 3 | [La primera vez, una sola vez en el semestre](#3-la-primera-vez-una-sola-vez-en-el-semestre) |
| 4 | [El ciclo completo, con un ejemplo real](#4-el-ciclo-completo-con-un-ejemplo-real) |
| 5 | [Cómo se nombran las ramas](#5-cómo-se-nombran-las-ramas) |
| 6 | [Cómo se nombran los commits](#6-cómo-se-nombran-los-commits) |
| 7 | [Las etiquetas: qué son y cuándo NO se usan](#7-las-etiquetas-qué-son-y-cuándo-no-se-usan) |
| 8 | [Preguntas que hizo el equipo](#8-preguntas-que-hizo-el-equipo) |
| 9 | [Cinco situaciones que se van a dar](#9-cinco-situaciones-que-se-van-a-dar) |
| 10 | [La tarjeta de un vistazo](#10-la-tarjeta-de-un-vistazo) |

---

## 1 · Por qué dejamos de trabajar sobre `main`

Trabajar todos sobre `main` funciona mientras son una o dos personas y el proyecto es chico. Con cinco personas y catorce semanas, se rompe de tres maneras concretas:

**Se pisan el trabajo.** Karen sube un cambio a `main`. Oscar, que llevaba dos horas trabajando sin actualizar, hace `push` y Git rechaza el envío. Para desatorarse hace `pull`, aparece un conflicto en un archivo que él no tocó, y lo resuelve borrando lo de Karen sin darse cuenta.

**Nadie revisa nada.** Todo entra directo. Un error de dedo en el `docker-compose.yml` deja al equipo sin base de datos, y el que lo subió ya se fue a dormir.

**`main` deja de servir como referencia.** A media semana `main` tiene el trabajo a medias de cinco personas. Si el asesor pide una demostración el martes, no hay ningún punto del historial que funcione completo.

Con ramas, cada quien trabaja en su propia copia de la línea de tiempo. `main` solo recibe trabajo terminado, revisado y con las verificaciones en verde. **`main` siempre funciona.** Ese es el punto entero.

> No es burocracia: es lo que permite que cinco personas con horarios distintos toquen el mismo repositorio sin coordinarse por chat cada vez.

---

## 2 · El mapa: dónde vive tu trabajo

Tu cambio pasa por cinco lugares. Confundirlos es lo que más desconcierta al principio.

```
┌─────────────────┐  git add     ┌──────────────┐  git commit  ┌──────────────┐
│  Tu carpeta     │ ───────────► │  Área de     │ ───────────► │  Tu rama     │
│  (archivos)     │              │  preparación │              │  LOCAL       │
└─────────────────┘              └──────────────┘              └──────┬───────┘
                                                                      │ git push
                                                                      ▼
                          ┌──────────────┐   incorporar   ┌──────────────────┐
                          │  main en     │ ◄───────────── │  Tu rama en      │
                          │  GitHub      │   (la solicitud)│  GitHub          │
                          └──────────────┘                └──────────────────┘
```

| Dónde | Qué es | Quién lo ve |
|---|---|---|
| **Tu carpeta** | Los archivos como están ahora en tu disco | Solo tú |
| **Área de preparación** | Lo que elegiste para el próximo commit | Solo tú |
| **Tu rama local** | Tus commits, todavía en tu máquina | Solo tú |
| **Tu rama en GitHub** | Lo mismo, ya subido. Aquí se revisa | Todos |
| **`main` en GitHub** | El proyecto oficial. Siempre funciona | Todos |

**Un commit no publica nada.** Hasta que no haces `push`, tu trabajo solo existe en tu computadora. Si se te descompone la laptop, se pierde.

---

## 3 · La primera vez, una sola vez en el semestre

Esto lo hace cada integrante **una vez**, no cada día.

### 3.1 Dile a Git quién eres

```bash
git config --global user.name "Tu Nombre Completo"
git config --global user.email "el-correo-de-tu-cuenta-github@ejemplo.com"
```

El correo **tiene que ser el mismo** de tu cuenta de GitHub. Si no, tus commits aparecen como de un desconocido y no cuentan como contribución tuya. Al final del semestre, cuando el asesor mire quién hizo qué, eso importa.

### 3.2 Clona el repositorio

```bash
cd ~/projects
git clone git@github.com:arik36/canastamx.git
cd canastamx
```

### 3.3 Comprueba que puedes empezar

```bash
bash infra/scripts/verificar-base.sh C1   # tu clave: A · B · C1 · C2 · D
```

Revisa que tu copia tenga la línea base y que tus herramientas estén instaladas. Si dice **PUEDES CREAR TU RAMA**, ya estás. Si no, arregla lo que marque o avisa en el chat. Detalle en [`linea-base.md`](./linea-base.md).

---

## 4 · El ciclo completo, con un ejemplo real

Vamos a seguir una tarea de verdad: **T011, Liseth, esqueleto de Spring Boot.**

### Paso 1 · Toma el issue

En `github.com/arik36/canastamx/issues`, abre el tuyo y en la barra derecha haz clic en *assign yourself*. Mueve la tarjeta a **En curso** en el tablero.

> **Por qué:** que dos personas empiecen lo mismo sin saberlo cuesta el doble. Y si no está en el tablero, para el equipo no existe.

### Paso 2 · Actualiza `main`

```bash
git switch main
git pull
```

> **Por qué:** vas a crear tu rama a partir de `main`. Si tu `main` está viejo, tu rama nace vieja y te ganas un conflicto que no tenías por qué tener. **Esto se hace cada vez, sin excepción.**

### Paso 3 · Crea tu rama

```bash
git switch -c feat/lyl-esqueleto-spring
```

`-c` significa *create*. Te crea la rama y te cambia a ella en un solo comando.

```bash
git branch --show-current     # confirma: feat/lyl-esqueleto-spring
```

> **Por qué el nombre así:** al ver la lista de ramas, cualquiera sabe de qué se trata y de quién es, sin abrir nada. Las reglas están en la [sección 5](#5-cómo-se-nombran-las-ramas).

> **Adquiere el hábito de correr `git branch --show-current`** antes de escribir la primera línea. El error más común del semestre va a ser trabajar dos horas creyendo estar en tu rama cuando estás en `main`.

### Paso 4 · Trabaja y ve guardando

Aquí sí trabajas: instalas el JDK, generas el proyecto, escribes el controlador. Y vas guardando conforme avanzas:

```bash
git status                    # ¿qué cambió?
git add .                     # prepara todo lo cambiado
git commit -m "feat(domain): esqueleto de Spring Boot con las tres capas"
```

Más tarde, otra pieza:

```bash
git add .
git commit -m "feat(domain): endpoint de salud en /health"
```

> **Por qué varios commits y no uno solo:** un commit gigante al final del día es imposible de revisar, y si algo se rompe no se puede deshacer por partes. Un commit por cosa que funciona.

> **Cuántos commits van en una rama:** los que necesites. Tres, cinco, diez. **No es un commit por rama.** Al incorporar se van a juntar en uno solo de todas formas (sección 4, paso 8).

### Paso 5 · Sube tu rama

```bash
git push -u origin feat/lyl-esqueleto-spring
```

El `-u` solo se usa **la primera vez de esa rama**. Después basta `git push`.

El `push` imprime algo así:

```
remote: Create a pull request for 'feat/lyl-esqueleto-spring' on GitHub by visiting:
remote:      https://github.com/arik36/canastamx/pull/new/feat/lyl-esqueleto-spring
```

**Esa URL es el enlace del que hablamos.** Cópiala.

> **Por qué:** hasta aquí tu trabajo solo existía en tu máquina. Ahora ya está respaldado y visible.

### Paso 6 · Abre la solicitud de incorporación

Pega la URL en el navegador. Se abre la página de la solicitud. Esto es lo que hay ahí y qué haces con cada cosa:

| Campo | Qué haces |
|---|---|
| **base: main ← compare: tu-rama** | Ya viene bien. No lo toques |
| **Título** | Viene lleno con tu último commit. Déjalo o mejóralo, mismo formato |
| **Cuerpo** | Viene con la plantilla del equipo, con tres preguntas. Contéstalas |
| **Reviewers** (barra derecha) | Elige **una** persona. Quién revisa a quién, más abajo |
| **Assignees** | Ponte tú |
| **Labels** | La etiqueta de tu frente: `dominio`, `datos`, `infra`, `movil`, `web` |
| Botón verde | **Create pull request** |

El cuerpo se llena así:

```markdown
## Qué cambia
Esqueleto de Spring Boot en services/domain-service/, con los paquetes
domain, application e infrastructure separados, y un endpoint GET /health.

## Cómo se probó
mvn spring-boot:run levanta el servicio en el 8081.
curl http://localhost:8081/health devuelve {"status":"UP",...}

## Qué podría romper
Nada del resto del sistema. La conexión a base de datos está desactivada
a propósito hasta la semana 7, porque todavía no hay esquema.

Closes #14
```

**`Closes #14` es la línea que más ahorra.** Con ella, al incorporarse la solicitud, el issue 14 se cierra solo y la tarjeta se mueve sola en el tablero. Sin ella hay que cerrarlo a mano, y se olvida siempre.

> **Qué NO se hace aquí:** no se sube nada por la web, no se editan archivos en GitHub. El código ya viajó con el `push`. La solicitud es solo la conversación sobre ese código.

### Paso 7 · Espera el verde y la revisión

Abajo de la solicitud aparecen dos cosas:

**Las verificaciones automáticas.** Tardan uno o dos minutos. Si sale una tacha roja, haz clic en *Details*, busca la línea que dice `Error:` y arregla en tu rama:

```bash
# corriges el archivo
git add .
git commit -m "fix(domain): corrige lo que marcó la canalización"
git push
```

La solicitud se actualiza sola. **No abras otra.**

**La revisión de tu compañero.** Quién revisa a quién, por defecto:

| Autor | Lo revisa |
|---|---|
| A · Ariadne | B |
| B · Ari Adair | A |
| C1 · Liseth | C2 |
| C2 · Oscar | C1 |
| D · Karen | C2, o A si toca la consola de observabilidad |

El revisor mira la pestaña *Files changed*, comenta lo que no entienda, y al final elige **Approve** o **Request changes**. Si pide cambios, los haces en tu rama, haces `push`, y le avisas.

### Paso 8 · Incorpora

Con la aprobación y el verde, aparece habilitado el botón de incorporar. Elige **Squash and merge**.

> **Por qué squash:** junta tus cinco commits en uno solo dentro de `main`. El historial de `main` queda con un commit por tarea, legible. Sin squash, `main` acumula commits como "arregla typo" y "ahora sí" que no le dicen nada a nadie en diciembre.

Luego **Confirm squash and merge**, y aparece un botón **Delete branch**. Haz clic.

> **Por qué borrar la rama:** ya cumplió. Su contenido está en `main`. Un repositorio con cuarenta ramas viejas es imposible de navegar, y nadie sabe cuáles siguen vivas.

### Paso 9 · Vuelve a `main` y limpia

```bash
git switch main
git pull                                    # ahora sí baja tu trabajo, ya incorporado
git branch -d feat/lyl-esqueleto-spring     # borra la copia local
```

> **Por qué el `pull` aquí:** el botón de GitHub incorporó tu rama a `main` **en el servidor**. Tu `main` local todavía no lo sabe. El `pull` lo trae. Si te lo saltas, la próxima rama que crees va a nacer sin tu propio trabajo.

> **Por qué borrar la rama local:** el `Delete branch` de GitHub borró la del servidor. La tuya sigue en tu máquina. `git branch -d` la borra, y solo funciona si ya está incorporada — si te dice que no, es que algo no se incorporó, y eso es información valiosa.

### Y ya. Vuelves al paso 1 con la siguiente tarea.

---

## 5 · Cómo se nombran las ramas

```
tipo/iniciales-descripcion-corta
```

Todo en minúsculas, sin acentos, sin espacios, palabras separadas por guiones.

### Los tipos

| Tipo | Cuándo |
|---|---|
| `feat` | Funcionalidad nueva |
| `fix` | Arreglas algo roto |
| `docs` | Solo documentación |
| `test` | Solo pruebas |
| `chore` | Configuración, dependencias, limpieza |
| `refactor` | Reacomodas código sin cambiar lo que hace |

### Las iniciales

| Integrante | Iniciales |
|---|---|
| Ariadne Lizett Macías Campos | `alm` |
| Ari Adair Soto Garnica | `aas` |
| Liseth Yareth Lara López | `lyl` |
| Oscar Renato Fonseca Ríos | `orf` |
| Karen Alejandra Herrera Villalpando | `kah` |

### Ejemplos reales de este proyecto

```
feat/alm-contrato-datos-qqp
feat/aas-docker-compose-base
feat/lyl-entidad-canasta
feat/orf-pantalla-busqueda
docs/kah-inventario-vistas
fix/aas-traefik-tls
chore/alm-linea-base
```

### Y los que no

| Mal | Por qué |
|---|---|
| `rama-liseth` | ¿De qué? ¿De cuándo? |
| `feature/NuevoServicio` | Mayúsculas y tipo mal escrito |
| `arreglos` | Sin tipo, sin dueño, sin tema |
| `feat/lyl-semana-2` | Una rama es por **tarea**, no por semana |

---

## 6 · Cómo se nombran los commits

```
tipo(ámbito): descripción en presente y en minúscula
```

Los tipos son los mismos de las ramas. Los ámbitos de este proyecto: `data`, `infra`, `domain`, `mobile`, `web`, `docs`, `ci`, `repo`.

| Bien | Mal |
|---|---|
| `feat(data): agrega contrato de datos para QQP` | `cambios` |
| `fix(infra): corrige puerto de MinIO en compose` | `ya quedó` |
| `docs(analisis): escribe CU-08 y CU-09` | `avance del martes` |
| `test(domain): prueba de cálculo de costo de canasta` | `asdasd` |

No es capricho. En diciembre alguien va a leer el historial para escribir el documento de traspaso, y `ya quedó` no le va a decir nada.

---

## 7 · Las etiquetas: qué son y cuándo NO se usan

**Aquí está la confusión más importante que hay que aclarar.**

> ### La etiqueta NO es parte del ciclo de trabajo.
>
> Hiciste `git tag base-v0` **una vez**, para marcar el arranque. No se hace una etiqueta por rama, ni por solicitud, ni por semana. Si etiquetaras cada vez, tendrías 85 etiquetas y ninguna significaría nada.

### Qué es una etiqueta

Un nombre permanente para un punto exacto del historial. Una rama se mueve conforme haces commits; una etiqueta se queda clavada donde la pusiste, para siempre.

Sirve para poder decir «vuelve a **exactamente** ese estado» meses después, sin buscar entre commits.

### Cuándo SÍ se pone una

Solo en dos situaciones, y las dos son excepcionales:

**1 · Cuando algo se vuelve base compartida.** Es decir, cuando varias personas van a construir encima de eso y necesitan referirse al mismo punto:

| Etiqueta | Cuándo | Por qué |
|---|---|---|
| `base-v0` | Ya la pusiste | El punto desde el que los cinco pueden ramificar |
| `base-contratos-v1` | Semana 5, al acordar los tres OpenAPI | C2 y D construyen contra esos contratos |
| `base-tipos-v1` | Cuando el paquete de tipos se estabilice | Web y móvil comparten esas definiciones |

**2 · En cada entrega institucional.** Para poder responder «¿qué exactamente entregamos el 18 de septiembre?» sin adivinar:

```
entrega-2026-09-18
entrega-2026-10-09
entrega-2026-11-04
entrega-2026-11-18
```

Esto vale mucho más de lo que parece. Si en noviembre el asesor pregunta qué se entregó en septiembre, la respuesta es un comando, no una búsqueda arqueológica.

### Cómo se nombran

```
base-<qué>-v<número>      para bases compartidas
entrega-<AAAA-MM-DD>      para entregas institucionales
```

Minúsculas, sin acentos, sin espacios.

### Qué verificar ANTES de poner una etiqueta

Una etiqueta apunta a un commit concreto. Si la pones en el equivocado, dice una mentira que dura todo el semestre.

```bash
# 1. Estar en main
git branch --show-current          # debe decir: main

# 2. Tener lo último
git pull

# 3. Ver QUÉ commit vas a etiquetar
git log -1 --oneline               # ¿es el que crees?

# 4. Que no quede trabajo sin incorporar que debiera estar dentro
#    (revisa que no haya solicitudes abiertas que pertenezcan a esa entrega)

# 5. Que la canalización esté en verde en main
#    (pestaña Actions en GitHub, último trabajo de main)
```

Con los cinco puntos:

```bash
git tag -a entrega-2026-09-18 -m "Entrega institucional: definición del proyecto"
git push origin entrega-2026-09-18
```

- `-a` crea una etiqueta **anotada**: guarda quién, cuándo y por qué. Úsala siempre.
- `-m` es ese porqué.
- **`git push origin <etiqueta>` es obligatorio.** Un `git push` normal **no** sube las etiquetas: se quedan solo en tu máquina y nadie más las ve. Es el error más común con etiquetas.

### Para verlas

```bash
git tag                            # lista todas
git show base-v0                   # qué commit es y qué mensaje tiene
git switch --detach base-v0        # ver el repositorio tal como estaba ahí
git switch main                    # y volver
```

---

## 8 · Preguntas que hizo el equipo

**¿Cuando haga un cambio, hago commit o rama?**
Las dos, en este orden: primero la rama, luego los commits dentro de ella. La rama se crea **antes** de empezar a trabajar, no después.

**¿Se hace una rama por commit?**
No. **Una rama por tarea**, y esa rama lleva los commits que hagan falta. En el semestre habrá unas 85 ramas —una por tarea del tablero—, no una por commit.

**¿Cuánto puede vivir una rama?**
Máximo una semana. Si algo te va a tomar dos semanas, no es una tarea: son dos, y son dos ramas. Las ramas largas producen conflictos gigantes que nadie quiere revisar.

**¿El enlace lo obtengo del `push`?**
Sí. El `push` imprime la URL que termina en `/pull/new/tu-rama`. Si ya cerraste la terminal, entra a `github.com/arik36/canastamx` y verás una barra amarilla con *Compare & pull request*.

**¿Qué agrego o quito en GitHub?**
Nada de código: eso ya viajó con el `push`. En la web solo llenas el cuerpo de la solicitud, eliges revisor, pones la etiqueta de tu frente, y al final haces clic en incorporar y en borrar la rama.

**¿Por qué hago `pull` después de incorporar?**
Porque el botón de GitHub incorporó tu trabajo a `main` **en el servidor**. Tu `main` local sigue igual que antes. El `pull` lo pone al día. Si te lo saltas, tu próxima rama nace sin tu propio trabajo anterior.

**¿Y luego una etiqueta?**
**No.** La etiqueta fue una sola vez, para marcar el arranque. Ver la [sección 7](#7-las-etiquetas-qué-son-y-cuándo-no-se-usan).

**¿Cada rama se elimina después del squash and merge?**
Sí, las dos copias: la del servidor con el botón *Delete branch* de GitHub, y la tuya local con `git branch -d nombre-de-la-rama`.

**¿Y si `git branch -d` se niega?**
Te está diciendo que esa rama tiene commits que no llegaron a `main`. **No uses `-D` mayúscula para forzar**: primero averigua qué se quedó fuera.

**¿Puedo aprobar mi propia solicitud?**
Ahora sí, porque `main` todavía no está protegida. En cuanto A la proteja, GitHub va a exigir la aprobación de otra persona. Ese es el punto.

---

## 9 · Cinco situaciones que se van a dar

### 1 · «`main` avanzó mientras yo trabajaba»

GitHub te lo dice: *This branch is out-of-date with the base branch*.

```bash
git switch main
git pull
git switch mi-rama
git merge main
git push
```

**Costumbre que evita el 90% de los conflictos:** haz esto cada mañana, aunque no te lo pida.

### 2 · «Apareció un conflicto»

No es un error. Es Git diciendo «dos personas cambiaron las mismas líneas, decidan ustedes». Se ve así:

```
<<<<<<< HEAD
lo que tú escribiste
=======
lo que ya estaba en main
>>>>>>> main
```

Eliges cuál queda —o escribes una tercera que combine— **borras las tres líneas de marcadores**, y cierras:

```bash
git add .
git commit -m "merge: resuelve conflicto con main"
git push
```

Si no entiendes el conflicto, no adivines: habla con quien escribió la otra versión. Y si se enredó todo, `git merge --abort` te devuelve al estado anterior.

### 3 · «Trabajé dos horas en `main` por error»

Muy común al principio, y no pierdes nada:

```bash
git switch -c feat/lyl-lo-que-hice    # se lleva tus cambios a una rama nueva
git add .
git commit -m "feat(domain): lo que hiciste"
git push -u origin feat/lyl-lo-que-hice
```

Si ya habías hecho commit en `main` local pero **no** `push`:

```bash
git switch -c feat/lyl-lo-que-hice    # la rama nueva ya tiene tu commit
git switch main
git reset --hard origin/main          # main vuelve a como está en GitHub
git switch feat/lyl-lo-que-hice
```

### 4 · «La canalización sale roja y no entiendo por qué»

*Details* → busca `Error:`. Si habla de tu código, arréglalo en tu rama. Si habla de configuración —rutas, versiones, permisos— es de B: avísale y no lo toques.

### 5 · «Ya no sé en qué estado estoy»

```bash
git status                  # qué tienes sin guardar
git branch --show-current   # en qué rama estás
git log --oneline -5        # tus últimos cinco commits
```

Esos tres comandos contestan casi cualquier duda. Y si de verdad se enredó todo, clonar de nuevo en otra carpeta cuesta cinco minutos y siempre funciona.

---

## 10 · La tarjeta de un vistazo

```bash
# ── CADA TAREA ──────────────────────────────────────────────
git switch main && git pull              # 1. parte de lo último
git switch -c feat/inic-descripcion      # 2. tu rama
                                         # 3. trabajas
git add . && git commit -m "tipo(ámbito): qué hace"
git push -u origin feat/inic-descripcion # 4. subes

# 5. abres la URL que imprimió el push
# 6. llenas la solicitud, pones "Closes #NN", eliges revisor
# 7. esperas verde + aprobación
# 8. Squash and merge → Delete branch

git switch main && git pull              # 9. traes tu trabajo ya incorporado
git branch -d feat/inic-descripcion      # 10. limpias

# ── CADA MAÑANA, si tu rama lleva días abierta ──────────────
git switch main && git pull
git switch mi-rama && git merge main

# ── SOLO EN ENTREGAS O BASES COMPARTIDAS ────────────────────
git switch main && git pull
git log -1 --oneline                     # ¿es el commit correcto?
git tag -a entrega-2026-09-18 -m "Entrega institucional: definición"
git push origin entrega-2026-09-18       # sin esto, la etiqueta no sale de tu máquina
```

---

## Las siete reglas

1. **Nunca trabajes en `main`.** Rama por tarea, siempre.
2. **`git pull` antes de ramificar.** Cada vez.
3. **Una rama por tarea, no por commit ni por semana.** Máximo una semana de vida.
4. **Commits chicos y frecuentes**, con el formato `tipo(ámbito): descripción`.
5. **Toda rama entra por solicitud**, con una aprobación y las verificaciones en verde.
6. **Después de incorporar: `pull` y borrar la rama.** Las dos copias.
7. **Las etiquetas son excepcionales.** Bases compartidas y entregas institucionales. Nada más.

---

*Si algo de este documento no funcionó como dice, es un defecto del documento, no tuyo. Abre un issue con la etiqueta `docs`.*
