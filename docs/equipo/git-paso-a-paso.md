# Git paso a paso en CanastaMX

Manual de operación del repositorio. Todo procedimiento aparece dos veces: **por terminal** y **por GitHub Desktop**. Elige una vía y quédate en ella; mezclarlas a media tarea es la fuente número uno de confusión.

Nadie tiene que memorizar nada. Este archivo se abre mientras se trabaja.

> **¿Es tu primera vez con ramas?** Empieza por [`ciclo-de-trabajo.md`](./ciclo-de-trabajo.md): cuenta el ciclo completo de principio a fin y explica el porqué de cada paso. Este de aquí es el manual de consulta, para buscar un comando concreto.

> **Repositorio:** `github.com/arik36/canastamx` · **Rama principal:** `main`, protegida · **Regla que no se rompe:** nadie escribe directo en `main`.

---

## Índice

| # | Sección | Cuándo la lees |
|---|---|---|
| 0 | [Instalación y configuración](#0-instalación-y-configuración-una-sola-vez-en-tu-vida) | Una sola vez, hoy |
| 1 | [El ciclo completo](#1-el-ciclo-completo-en-ocho-pasos) | Una vez, para entender el mapa |
| 2 | [Empezar una tarea](#2-empezar-una-tarea) | Cada vez que tomas un issue |
| 3 | [Guardar y subir tu avance](#3-guardar-y-subir-tu-avance) | Varias veces al día |
| 4 | [Abrir la solicitud de incorporación](#4-abrir-la-solicitud-de-incorporación-pull-request) | Cuando terminas la tarea |
| 5 | [Revisar la solicitud de otro](#5-revisar-la-solicitud-de-otro-integrante) | Cuando te etiquetan |
| 6 | [Incorporar y limpiar](#6-incorporar-y-limpiar) | Cuando te aprueban |
| 7 | [Mi rama quedó vieja](#7-mi-rama-quedó-vieja) | Cuando GitHub dice que hay conflictos |
| 8 | [Resolver un conflicto](#8-resolver-un-conflicto) | Cuando aparece `<<<<<<<` |
| 9 | [La regué: cómo deshacer](#9-la-regué-cómo-deshacer) | Cuando entra el pánico |
| 10 | [Qué nunca sube al repositorio](#10-qué-nunca-sube-al-repositorio) | Antes de cada `git add` |
| 11 | [Catálogo de errores](#11-catálogo-de-errores-frecuentes) | Cuando la terminal te grita |
| 12 | [Tarjeta de referencia](#12-tarjeta-de-referencia-rápida) | Siempre |

---

## 0. Instalación y configuración (una sola vez en tu vida)

### 0.1 Instala lo que te toca

| Quién | Necesita sí o sí |
|---|---|
| Todos | Git, cuenta de GitHub, VS Code |
| A (Ariadne) | Python 3.12, Docker Desktop |
| B (Ari Adair) | Docker Desktop, terminal cómoda (WSL2 si es Windows) |
| C1 (Liseth) | JDK 21, Maven |
| C2 (Oscar) | Node.js 20, Expo CLI |
| D (Karen) | Node.js 20, Figma |

**Git en Windows:** descarga de `git-scm.com`, siguiente-siguiente-siguiente, y en la pantalla que pregunta por el editor elige *Visual Studio Code*.
**Git en Mac:** abre la Terminal y escribe `git --version`. Si no lo tienes, macOS te ofrece instalarlo solo. Acepta.
**GitHub Desktop:** `desktop.github.com`. Instálalo aunque uses terminal; sirve para ver los cambios de un vistazo.

### 0.2 Dile a Git quién eres

Esto queda grabado en cada commit que hagas en tu vida. Escríbelo bien.

```bash
git config --global user.name "Karen Alejandra Herrera Villalpando"
git config --global user.email "el-correo-de-tu-cuenta-github@ejemplo.com"
git config --global init.defaultBranch main
git config --global pull.rebase false
```

El correo **tiene que ser el mismo** de tu cuenta de GitHub. Si no, tus commits aparecen como de un fantasma y no cuentan como tu contribución.

Verifica:

```bash
git config --global --list
```

### 0.3 Clona el repositorio

**Por terminal**

```bash
cd ~/Documentos          # o donde guardes tus proyectos. En Windows: cd ~/Documents
git clone https://github.com/arik36/canastamx.git
cd canastamx
ls
```

La primera vez te va a pedir usuario y contraseña. **La contraseña de GitHub ya no funciona ahí.** Necesitas un token:

1. GitHub → tu foto arriba a la derecha → *Settings*
2. Hasta abajo: *Developer settings* → *Personal access tokens* → *Tokens (classic)*
3. *Generate new token (classic)*. Nota: `canastamx laptop`. Vencimiento: 90 días. Marca la casilla **repo**.
4. *Generate token*. **Cópialo ahora**, no lo vuelves a ver.
5. Cuando la terminal pida *Password*, pega el token.

Para no repetirlo cada vez:

```bash
git config --global credential.helper store    # Linux
git config --global credential.helper osxkeychain   # Mac
git config --global credential.helper manager       # Windows
```

**Por GitHub Desktop**

1. Abre GitHub Desktop → *Sign in to GitHub.com* → autoriza en el navegador.
2. *File* → *Clone repository* → pestaña *GitHub.com* → busca `arik36/canastamx`.
3. En *Local path* elige dónde guardarlo. **Que no sea una carpeta sincronizada con OneDrive, iCloud o Google Drive.** Esos servicios corrompen carpetas de Git.
4. *Clone*.

### 0.4 Comprueba que quedó

```bash
cd canastamx
git status
```

Debe decir `On branch main` y `nothing to commit, working tree clean`. Si dice eso, ya estás dentro.

---

## 1. El ciclo completo en ocho pasos

Este es el mapa. Todo lo demás son detalles de estos ocho pasos.

```
  1. Tomo un issue del tablero            →  me asigno en GitHub
  2. Actualizo main                       →  git switch main && git pull
  3. Verifico que puedo ramificar         →  bash infra/scripts/verificar-base.sh D
  4. Creo mi rama                         →  git switch -c feat/kah-tablero
  5. Trabajo y voy guardando              →  git add . && git commit -m "..."
  6. Subo mi rama                         →  git push
  7. Abro solicitud de incorporación      →  en la web de GitHub
  8. Otro me revisa y se incorpora        →  el issue se cierra solo
```

**Una rama por tarea.** No una rama por semana, ni una rama por persona. Una por tarea. Ramas cortas que viven dos o tres días se incorporan sin dolor; ramas de dos semanas se convierten en un conflicto gigante que nadie quiere revisar.

---

## 2. Empezar una tarea

### 2.1 Toma el issue

En `github.com/arik36/canastamx/issues` busca el que te toca. Ábrelo y en la barra derecha, en *Assignees*, haz clic en *assign yourself*. Mueve la tarjeta a **En curso** en el tablero.

Si no está asignada a nadie en el tablero, **no la empieces**. Escríbelo en el chat primero. Dos personas trabajando lo mismo sin saberlo es tiempo perdido dos veces.

### 2.2 Actualiza `main` antes de ramificar

Esto no es opcional. Si ramificas desde un `main` viejo, te ganas un conflicto gratis.

**Por terminal**

```bash
git switch main
git pull
```

**Por GitHub Desktop**

1. *Current Branch* (arriba, en medio) → elige `main`.
2. Botón *Fetch origin* → si aparece *Pull origin*, haz clic.

### 2.3 Verifica que ya puedes ramificar

Un comando, y te dice sí o no:

```bash
bash infra/scripts/verificar-base.sh C1     # tu clave: A, B, C1, C2 o D
```

Comprueba siete cosas: que estás en un clon al día, que `main` ya tiene la **línea base v0**, que existe el `.gitignore` con lo que tu frente genera, que están las carpetas de tu área, que tu Git tiene nombre y correo, y que tus herramientas están instaladas.

- Si dice **PUEDES CREAR TU RAMA**, sigue.
- Si dice que no, arregla lo que marque con ✗. Si lo que falta es algo del repositorio, **no lo subas por tu cuenta**: avisa en el chat, porque la línea base la sube A en un solo commit.

**Por qué existe este paso.** Si ramificas antes de que exista el `.gitignore`, tu primer `git add .` se lleva `target/`, `node_modules/` o `.venv/` —cientos de archivos generados— y la solicitud queda imposible de revisar. El detalle está en [`linea-base.md`](./linea-base.md).

### 2.4 Crea tu rama

El nombre lleva formato. `tipo/iniciales-descripcion-corta`, todo en minúsculas, sin acentos, palabras separadas por guiones.

| Tipo | Cuándo |
|---|---|
| `feat` | Funcionalidad nueva |
| `fix` | Corriges algo roto |
| `docs` | Solo documentación |
| `test` | Solo pruebas |
| `chore` | Configuración, dependencias, limpieza |
| `refactor` | Reacomodas código sin cambiar lo que hace |

| Integrante | Iniciales |
|---|---|
| Ariadne Lizett Macías Campos (A) | `alm` |
| Ari Adair Soto Garnica (B) | `aas` |
| Liseth Yareth Lara López (C1) | `lyl` |
| Oscar Renato Fonseca Ríos (C2) | `orf` |
| Karen Alejandra Herrera Villalpando (D) | `kah` |

Ejemplos reales de este proyecto:

```
feat/alm-contrato-datos-qqp
feat/aas-docker-compose-base
feat/lyl-entidad-canasta
feat/orf-pantalla-busqueda
docs/kah-inventario-vistas
fix/aas-traefik-tls
```

**Por terminal**

```bash
git switch -c feat/kah-inventario-vistas
```

**Por GitHub Desktop**

*Current Branch* → *New Branch* → escribe el nombre → *Create Branch* → *Publish branch*.

### 2.5 Confirma en qué rama estás

```bash
git branch --show-current
```

Adquiere el hábito de correr esto antes de escribir la primera línea. El error más común del semestre va a ser trabajar dos horas creyendo que estás en tu rama cuando estás en `main`.

---

## 3. Guardar y subir tu avance

### 3.1 Mira qué cambiaste

```bash
git status
```

Rojo = cambios que Git todavía no está siguiendo. Verde = listos para el commit.

```bash
git diff        # te muestra línea por línea qué cambió
```

En GitHub Desktop esto se ve solo, en el panel izquierdo, con el detalle a la derecha. Es la razón principal para tenerlo instalado aunque uses terminal.

### 3.2 Selecciona y confirma

**Por terminal**

```bash
git add .                                    # todo lo que cambiaste
git add docs/analisis/vistas.md              # o solo un archivo
git commit -m "docs(analisis): agrega inventario de las ocho vistas"
```

**Por GitHub Desktop**

Palomea los archivos en el panel izquierdo, escribe el resumen en el recuadro de abajo, *Commit to feat/...*.

### 3.3 El formato del mensaje de commit

```
tipo(ámbito): descripción en presente y en minúscula
```

Los ámbitos de este proyecto: `data`, `infra`, `domain`, `mobile`, `web`, `docs`, `ci`.

| Bien | Mal |
|---|---|
| `feat(data): agrega contrato de datos para QQP` | `cambios` |
| `fix(infra): corrige puerto de MinIO en compose` | `ya quedó` |
| `docs(analisis): escribe CU-08 y CU-09` | `Avance del martes` |
| `test(domain): prueba de cálculo de costo de canasta` | `asdasd` |

No es capricho de estilo. En diciembre alguien va a leer el historial para escribir el documento de traspaso, y `ya quedó` no le va a decir nada.

**Commitea seguido.** Terminaste una sección: commit. Funcionó algo: commit. Un commit gigante al final del día es imposible de revisar y, si algo se rompe, imposible de deshacer parcialmente.

### 3.4 Sube

**Por terminal**

```bash
git push -u origin feat/kah-inventario-vistas   # la primera vez de esa rama
git push                                        # las siguientes
```

El `-u` solo se usa la primera vez. Después basta `git push`.

**Por GitHub Desktop**

*Push origin*, arriba a la derecha.

---

## 4. Abrir la solicitud de incorporación (pull request)

La solicitud es donde tu trabajo se vuelve del equipo. Sin solicitud, tu rama no existe para nadie más.

### 4.1 Ábrela

Después de un `push`, la terminal imprime una URL que termina en `/pull/new/tu-rama`. Ábrela. Si ya la cerraste: entra a `github.com/arik36/canastamx` y verás una barra amarilla con *Compare & pull request*.

En GitHub Desktop el botón azul dice *Create Pull Request* y te lleva al mismo lugar.

### 4.2 Llénala

El título es el mismo formato del commit: `feat(web): inventario de las ocho vistas`.

El cuerpo ya viene con plantilla. Tres preguntas, tres respuestas honestas:

```markdown
## Qué cambia
Agrego el inventario de las ocho vistas con una línea de contenido por vista
y el enlace al archivo de Figma.

## Cómo se probó
Abrí el archivo en la vista previa de GitHub y verifiqué que los ocho enlaces
a Figma abren. Karen y Ariadne revisaron la lista en la reunión del jueves.

## Qué podría romper
Nada de código. Si cambia el nombre de alguna vista en Figma, este archivo
queda desactualizado.

Closes #14
```

**`Closes #14` es la línea importante.** Con ella, al incorporarse la solicitud, el issue 14 se cierra solo y la tarjeta se mueve sola en el tablero. Sin ella, tienes que cerrar todo a mano y siempre se olvida.

### 4.3 Pide revisión

En la barra derecha, *Reviewers*, elige a **una** persona. Quién revisa a quién, por defecto:

| Autor | Revisa |
|---|---|
| A (Ariadne) | B |
| B (Ari Adair) | A |
| C1 (Liseth) | C2 |
| C2 (Oscar) | C1 |
| D (Karen) | C2, o A si toca la consola de observabilidad |

Avisa en el chat con el enlace. Una solicitud que nadie sabe que existe se queda abierta cuatro días.

### 4.4 Espera el verde

Abajo aparecen las verificaciones de integración continua. Si sale una tacha roja, **es tuya**. Haz clic en *Details*, lee el error, arréglalo en tu rama, haz commit y push. La solicitud se actualiza sola; no abras otra.

---

## 5. Revisar la solicitud de otro integrante

Revisar no es aprobar por compromiso. Toma diez minutos y le ahorra al equipo una semana.

1. Entra a la pestaña *Files changed*.
2. Lee el diff. Verde = agregado, rojo = eliminado.
3. Pregunta lo que no entiendas. Haz clic en el número de línea y escribe. No es agresión, es cómo funciona.
4. Contrasta contra el criterio del issue: la columna **cómo saber que quedó**. Si el issue decía *"existe `docs/datos/diccionario-qqp.md` con la lista de columnas"* y el archivo tiene tres columnas de veinte, todavía no queda.
5. *Review changes* → elige:
   - **Approve** — se puede incorporar.
   - **Request changes** — falta algo concreto. Di qué.
   - **Comment** — dudas sin bloquear.

Tres cosas que siempre se revisan en este proyecto:

- [ ] ¿Hay contraseñas, tokens o cadenas de conexión en el diff? Si sí, **Request changes** de inmediato.
- [ ] ¿Hay archivos pesados que no deberían estar? (`node_modules/`, `.venv/`, `target/`, `.parquet` grandes, capturas sin comprimir)
- [ ] ¿El criterio de aceptación del issue se cumple de verdad?

---

## 6. Incorporar y limpiar

Cuando tengas la aprobación y el verde de integración continua:

1. Botón *Squash and merge*. Siempre *squash*: convierte tus quince commits en uno solo y deja el historial de `main` legible.
2. *Confirm squash and merge*.
3. Botón *Delete branch*. La rama ya cumplió; dejarla ahí solo estorba.

Y en tu máquina, después:

**Por terminal**

```bash
git switch main
git pull
git branch -d feat/kah-inventario-vistas
```

**Por GitHub Desktop**

*Current Branch* → `main` → *Fetch origin* / *Pull origin*. GitHub Desktop te ofrece borrar la rama local; acepta.

---

## 7. Mi rama quedó vieja

Pasa cuando otro incorporó algo a `main` mientras tú trabajabas. GitHub te lo dice: *"This branch is out-of-date with the base branch"*.

**Por terminal**

```bash
git switch main
git pull
git switch feat/kah-inventario-vistas
git merge main
git push
```

**Por GitHub Desktop**

*Current Branch* → *Choose a branch to merge into feat/...* → elige `main` → *Merge*. Luego *Push origin*.

Si el merge sale limpio, terminaste. Si aparece la palabra *conflict*, sigue a la sección 8.

**Costumbre que evita el 90% de los conflictos:** haz esto cada mañana antes de trabajar, aunque no lo necesites.

---

## 8. Resolver un conflicto

Un conflicto no es un error. Es Git diciendo "dos personas cambiaron las mismas líneas y no me corresponde a mí decidir cuál vale".

Se ve así dentro del archivo:

```
<<<<<<< HEAD
El tablero muestra seis indicadores.
=======
El tablero muestra los seis indicadores de calidad.
>>>>>>> main
```

- Entre `<<<<<<< HEAD` y `=======` está **lo tuyo**.
- Entre `=======` y `>>>>>>> main` está **lo que ya estaba en main**.

### Cómo se arregla, en VS Code

VS Code pinta el bloque de colores y pone cuatro botones arriba: *Accept Current Change*, *Accept Incoming Change*, *Accept Both Changes*, *Compare Changes*.

1. Lee las dos versiones. Decide cuál queda, o escribe una tercera que combine ambas.
2. **Borra las tres líneas de marcadores** (`<<<<<<<`, `=======`, `>>>>>>>`). Los botones lo hacen por ti; si editas a mano, no se te olviden.
3. Repite en cada bloque. VS Code lista abajo cuántos quedan.
4. Cierra:

```bash
git add .
git commit -m "merge: resuelve conflicto con main"
git push
```

**Si no entiendes el conflicto, no adivines.** Habla con quien escribió la otra versión. Borrar el trabajo de otro por resolver rápido es peor que dejar el conflicto abierto una hora.

**Salida de emergencia**, si todo se enredó y quieres volver al estado anterior al merge:

```bash
git merge --abort
```

---

## 9. La regué: cómo deshacer

Ordenadas de menos a más grave. Busca tu caso.

### Cambié cosas y quiero tirarlas (sin commit todavía)

```bash
git restore archivo.md      # un archivo
git restore .               # todo
```

Irreversible. Lo que no tenía commit se pierde.

### Hice `git add` pero todavía no commit y me arrepentí

```bash
git restore --staged archivo.md
```

El cambio sigue ahí, solo sale de la lista del commit.

### Hice commit pero no push, y el mensaje quedó mal

```bash
git commit --amend -m "feat(web): mensaje correcto"
```

### Hice commit pero no push, y quiero deshacerlo conservando los cambios

```bash
git reset --soft HEAD~1
```

### Ya hice push y el commit está mal

No borres historia de una rama compartida. Haz un commit nuevo que corrija:

```bash
git revert <hash-del-commit-malo>
git push
```

El hash lo sacas de `git log --oneline` (los siete caracteres del inicio).

### Trabajé dos horas en `main` por error

Muy común. Tiene arreglo limpio y no pierdes nada.

```bash
git switch -c feat/kah-lo-que-hice   # se lleva tus cambios a una rama nueva
git add .
git commit -m "feat(web): lo que hiciste"
git push -u origin feat/kah-lo-que-hice
```

Si ya habías hecho commit en `main` local pero **no** push:

```bash
git switch -c feat/kah-lo-que-hice   # la rama nueva ya tiene tu commit
git switch main
git reset --hard origin/main         # main vuelve a como está en GitHub
git switch feat/kah-lo-que-hice
```

### Subí un archivo con contraseñas

**Detente y avisa a B ahora mismo, por chat, no por correo.** Borrar el archivo en un commit nuevo no sirve: la contraseña sigue en el historial. Hay que reescribir historia y rotar la credencial. B lo coordina.

### Todo está tan roto que ya no sé

Sin vergüenza y sin drama:

```bash
cd ..
mv canastamx canastamx-roto
git clone https://github.com/arik36/canastamx.git
```

Tienes una copia limpia y tu carpeta anterior sigue ahí por si rescatas algo. Perder media hora es más barato que perder una tarde peleando.

---

## 10. Qué nunca sube al repositorio

| Qué | Dónde va |
|---|---|
| Contraseñas, tokens, cadenas de conexión | Tu `.env` local, que está en `.gitignore`. Al repo solo sube `.env.example` con las llaves y valores vacíos |
| Archivos crudos de PROFECO | MinIO. Al repo solo una muestra de mil filas en `services/data-platform/tests/fixtures/` |
| `node_modules/`, `.venv/`, `target/`, `__pycache__/` | A ningún lado. Están en `.gitignore` desde el día uno |
| Bases de datos y volúmenes de contenedor | A ningún lado |
| Documentos de Word y presentaciones | Google Drive. En `docs/entregas/` queda solo un archivo de texto con el enlace y la fecha |
| Capturas pesadas | Solo las del README, comprimidas. Las demás en Drive |

**Antes de cada `git add .`, corre `git status` y lee la lista.** Si aparece algo que no reconoces, no lo agregues: pregunta.

Regla de oro: si al abrir un archivo ves algo que no le enseñarías a un desconocido, no va al repositorio.

---

## 11. Catálogo de errores frecuentes

### `fatal: not a git repository`

No estás dentro de la carpeta del proyecto.

```bash
cd ruta/donde/lo/clonaste/canastamx
```

### `Updates were rejected because the remote contains work that you do not have locally`

Alguien subió algo antes que tú.

```bash
git pull
# resuelve conflictos si aparecen
git push
```

### `Authentication failed` / `Support for password authentication was removed`

Estás usando tu contraseña de GitHub. Necesitas un token: sección 0.3.

### `Your branch is ahead of 'origin/main' by 3 commits`

Hiciste commits en `main` local. Ve a la sección 9, caso *"Trabajé dos horas en main"*.

### `error: Your local changes would be overwritten by merge`

Tienes cambios sin commit y Git no quiere pisarlos.

```bash
git stash        # los guarda aparte
git pull
git stash pop    # los devuelve
```

### `Permission to arik36/canastamx.git denied`

No estás invitada como colaboradora, o entraste con otra cuenta. Avisa a Ariadne.

### `CONFLICT (content): Merge conflict in archivo.md`

Sección 8. No es grave.

### La verificación de integración continua sale roja

Haz clic en *Details* en la solicitud, lee la línea que dice `Error:` y arregla en tu rama. Push y se vuelve a correr sola. Si el error no habla de tu código sino de la configuración, es de B.

### `refusing to merge unrelated histories`

Clonaste mal o creaste un repo local aparte. Habla con B antes de forzar nada.

---

## 12. Tarjeta de referencia rápida

```bash
# ¿Dónde estoy y qué tengo?
git status
git branch --show-current

# Empezar tarea
git switch main && git pull
git switch -c feat/inic-descripcion

# Guardar
git add .
git commit -m "tipo(ámbito): descripción"
git push -u origin feat/inic-descripcion     # primera vez
git push                                     # después

# Traer lo nuevo de main a mi rama
git switch main && git pull
git switch mi-rama && git merge main

# Ver historial
git log --oneline -10

# Cambiar de rama
git switch nombre-de-la-rama

# Guardar cambios temporalmente
git stash / git stash pop
```

---

## Las cinco reglas

1. **Nunca trabajes en `main`.** Rama por tarea, siempre.
2. **`git pull` antes de ramificar.** Cada mañana.
3. **Commits chicos y frecuentes**, con mensaje en formato.
4. **Toda rama entra por solicitud** con una aprobación y la integración continua en verde.
5. **Si no sabes, pregunta antes de forzar.** Un `--force` a destiempo borra el trabajo de alguien más.

---

*Si algo de este manual no funcionó como dice, es un defecto del manual, no tuyo. Abre un issue con la etiqueta `docs` y se corrige.*
