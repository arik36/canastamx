# Guion de grabación · una tarea completa, de la tarjeta a `main`

**Un video de unos 16 minutos, con capítulos.** Lo graba A. Se ve una vez completo en la reunión de arranque y después queda como referencia: cuando alguien pregunte «¿qué pongo en la descripción?» en la semana 6, la respuesta es un minuto de video, no una explicación repetida.

> **Por qué grabado y no solo en vivo.** En vivo se explica una vez y para cinco personas a la vez, tres de las cuales están tecleando y no escuchando. Grabado se ve otra vez, se pausa, y sirve en noviembre igual que en septiembre. La sesión en vivo *(ver [`reunion-de-arranque.md`](./reunion-de-arranque.md))* sigue siendo necesaria: el video explica, la sesión verifica que cada quien lo logró en su máquina.

---

# Antes de grabar

## La tarea que vas a usar

**Tu propia ficha de entorno**: `[S1][Datos] Ficha de entorno de A`.

No sirve ninguna otra. Tu issue #7 —cerrar la estructura del repositorio— ya está hecho, y los otros cinco de tu semana son trabajo real que no conviene adelantar. La ficha de entorno es perfecta porque es chica, es de verdad, y **es exactamente la tarea que los cuatro van a hacer después de ver el video**. Van a poder seguirlo copiando.

Siémbrala junto con las otras cuatro, con el comando de [`reunion-de-arranque.md`](./reunion-de-arranque.md), y llénale los campos con `llenar-tablero.py`. **Esto se hace antes de grabar**, porque en el video la tarjeta ya tiene que existir.

## El estado de partida

```bash
cd ~/projects/canastamx
git switch main && git pull
git status                    # tiene que decir: nothing to commit, working tree clean
git branch                    # solo main
ls docs/equipo/entorno/       # solo PLANTILLA.md
```

Si `git status` no está limpio, resuélvelo antes. Una rama a medias o un archivo sin confirmar aparece en pantalla y confunde.

## El ensayo, que no es opcional

**Solo puedes incorporar esta tarea una vez.** Después de la fusión, la demostración se acabó. Así que primero se ensaya completo, con un archivo desechable, y **la solicitud del ensayo se cierra sin incorporar**:

```bash
git switch -c docs/alm-ensayo
mkdir -p docs/equipo/entorno && echo "# ensayo" > docs/equipo/entorno/_ensayo.md
git add -A && git commit -m "chore: ensayo"
git push -u origin docs/alm-ensayo
```

Abre la solicitud, recorre la página entera, mira dónde queda cada botón. Y al final, **Close pull request**, *no* «Merge»:

```bash
git switch main
git branch -D docs/alm-ensayo
git push origin --delete docs/alm-ensayo
```

`main` queda intacto y ya sabes dónde está todo.

## La preparación técnica

| | Por qué |
|---|---|
| **Letra de la terminal grande** (Ctrl + `+` varias veces) | Lo van a ver en el teléfono. Si no se lee, el video no sirve |
| **Zoom del navegador al 125–150 %** | Lo mismo |
| **Notificaciones apagadas** | WhatsApp de escritorio, correo, todo |
| **Ventana de incógnito para GitHub** | Sin marcadores ni pestañas personales a la vista |
| **Terminal y navegador en la misma pantalla** | Alternar con Alt+Tab marea; lado a lado se entiende |
| **La descripción de la solicitud, ya escrita en un bloc** | Para pegarla y no teclear tres párrafos en cámara |
| **Grabar la pantalla completa, no una ventana** | Si cambias de ventana con «solo esta ventana», se ve negro |

**Si te equivocas, no cortes: dilo.** «Ay, me faltó el pull — miren lo que pasa» enseña más que la toma perfecta. Los errores en cámara son la parte que más se agradece.

## Los capítulos, para pegar en la descripción del video

```
00:00  Qué vamos a ver
00:30  1 · Tomar la tarjeta del tablero
01:30  2 · Crear la rama
03:00  3 · Hacer el trabajo
04:00  4 · El commit, y el gancho que te frena
06:00  5 · Subir la rama
07:00  6 · Llenar la solicitud
10:00  7 · Las verificaciones de integración continua
12:00  8 · La revisión
13:30  9 · Squash and merge
15:00  10 · De vuelta a la terminal
16:00  11 · Lo que NO se hace
18:00  12 · Quién aprueba, si main no está protegida
```

Los minutos son estimados; ajústalos con los reales al subirlo.

---

# El guion

> **Cómo leer las escenas.** «Qué dices» no es para leerlo palabra por palabra: es la idea y el orden. Dilo con tus palabras. «Qué tecleas» sí es literal.

---

## 0 · Qué vamos a ver · 30 s

**En pantalla:** el tablero de GitHub.

**Qué dices:**

> Este video es una tarea completa de CanastaMX, de principio a fin: desde que agarras una tarjeta del tablero hasta que tu cambio está en `main` y la tarjeta se movió sola a Hecho. Son unos quince minutos y tiene capítulos, así que cuando en octubre no te acuerdes de qué poner en la descripción, vienes al minuto siete y ya.
>
> La tarea que voy a hacer es la que ustedes van a hacer hoy: su ficha de entorno. Así que esto no es un ejemplo inventado; es literalmente lo que sigue.

---

## 1 · Tomar la tarjeta · 1 min

**En pantalla:** el tablero, vista *Tablero*, columna `Esta semana`.

**Qué haces:** abres tu tarjeta `[S1][Datos] Ficha de entorno de A`, la lees en voz alta, y la arrastras de `Esta semana` a `En curso`.

**Qué dices:**

> Primero se lee la tarjeta completa, sobre todo el apartado **cómo saber que quedó**. Ese es el criterio con el que otro te va a revisar. Si no lo entiendes, se pregunta ahora, no cuando ya escribiste todo.
>
> Y se mueve a `En curso` **antes** de empezar, no al terminar. Esta columna es lo único que le dice al resto en qué andas. Si la mueves al final, nadie supo en toda la tarde que estabas en eso, y dos personas pueden haber tocado el mismo archivo.
>
> Máximo dos tarjetas en `En curso` por persona. Si necesitas una tercera, primero cierras una. Es lo único que impide tener siete cosas empezadas y ninguna terminada.

---

## 2 · Crear la rama · 1.5 min

**En pantalla:** terminal.

**Qué tecleas:**

```bash
cd ~/projects/canastamx
git switch main
git pull
git switch -c docs/alm-entorno-a
git branch --show-current
```

**Qué dices, mientras cada comando corre:**

> `git switch main` — vuelvo a la rama principal, porque toda rama nueva sale de ahí.
>
> `git pull` — y esta es la que se olvida siempre. Trae lo que subieron los demás. Si te la saltas, tu rama nace vieja: trabajas encima de un `main` de hace tres días y el conflicto te aparece al final, cuando ya no tienes tiempo. Tres segundos ahora, o media hora el viernes.
>
> `git switch -c` crea la rama y me cambia a ella. El nombre lleva formato: **tipo, diagonal, iniciales, guion, descripción**. Tipo `docs` porque es documentación —hay `feat`, `fix`, `docs`, `test` y `chore`—, `alm` que son mis iniciales, y qué estoy haciendo. Sin acentos, sin eñes, sin espacios, minúsculas.
>
> Y siempre comprobar dónde estás antes de escribir nada. Se ha ido más de una tarde por trabajar creyendo estar en otra rama.

---

## 3 · Hacer el trabajo · 1 min

**En pantalla:** terminal, y el editor.

**Qué tecleas:**

```bash
cp docs/equipo/entorno/PLANTILLA.md docs/equipo/entorno/a.md
git --version
gh --version
python3 --version
nano docs/equipo/entorno/a.md
```

**Qué dices:**

> Nadie parte de un archivo vacío: hay plantilla. La copio con **mi clave** de nombre.
>
> Corro los comandos de mis herramientas y **copio la salida real**. Nada de poner «la última versión». Este documento existe para que en noviembre, cuando alguien diga «en mi máquina sí funciona», se pueda comparar contra algo cierto. Una versión inventada aquí hace que el documento sea peor que no tenerlo.
>
> Si un comando dice *command not found*, se escribe «pendiente» y una nota de para cuándo lo necesito. Eso no es una falta: es saber hoy que hay algo que instalar antes de la semana en que hace falta.

*(Llenas el archivo en cámara, rápido. No hace falta que lo vean teclear todo.)*

---

## 4 · El commit, y el gancho que te frena · 2 min

**En pantalla:** terminal.

**Qué tecleas:**

```bash
git status
git add docs/equipo/entorno/a.md
git status
git commit -m "docs(equipo): ficha de entorno de trabajo de A"
```

**Qué dices:**

> `git status` antes de nada. Dice *Untracked files*: Git ve el archivo pero todavía no lo va a guardar.
>
> `git add` y otra vez `status`. Ahora dice *Changes to be committed*. Eso de en medio se llama **área de preparación**: el montón de lo que va a entrar en el próximo commit. Existe para que puedas confirmar tres archivos de cinco cuando los otros dos no están listos.
>
> Y el mensaje del commit lleva formato igual que la rama: **tipo, ámbito entre paréntesis, dos puntos, descripción en presente**. «Agrega», no «agregué» ni «agregando». Suena raro al principio y es lo que hace legible el historial cuando tenga doscientos commits.

### 🎬 La demostración del gancho

**Qué tecleas:**

```bash
echo "POSTGRES_PASSWORD=esto-es-de-mentiras" > .env
git add -f .env
git commit -m "prueba"
```

**Qué dices, señalando el mensaje rojo:**

> Miren esto, porque les va a pasar. Acabo de intentar subir un archivo `.env`, que es donde van las contraseñas, y algo me lo bloqueó antes de guardar nada.
>
> Eso es un **gancho de Git**: un programa que corre solo antes de cada commit. Revisa tres cosas: que no vaya un `.env`, que no vayan carpetas de dependencias como `node_modules` o `target`, y que no vaya nada de más de diez megas.
>
> ¿Por qué esas tres? Porque son **las que no se arreglan borrando el archivo después**. Una vez que algo entra al historial de Git, ahí se queda aunque lo borres en el commit siguiente. Una contraseña subida es una contraseña quemada: hay que cambiarla, no borrarla.
>
> Y por eso el paso de `instalar-hooks.sh` no es opcional. Los ganchos **no vienen con el clon**: Git obliga a que cada quien los active a mano, porque si no, clonar cualquier repositorio de internet ejecutaría código de un desconocido en tu computadora. Son cinco activaciones distintas. Si uno se lo salta, no tiene ninguna de estas protecciones y nadie se entera hasta que rompe algo.

**Qué tecleas para deshacerlo:**

```bash
git restore --staged .env && rm .env
git log --oneline -1
```

> Lo saco, y compruebo que mi commit bueno sigue ahí.

---

## 5 · Subir la rama · 1 min

**Qué tecleas:**

```bash
git push -u origin docs/alm-entorno-a
```

**Qué dices:**

> El `-u` es solo la primera vez de cada rama: la ata a la del servidor, y de ahí en adelante `git push` a secas basta.
>
> Y fíjense en lo que imprime: **una dirección**. Esa es la solicitud, ya lista para abrirse. No hay que buscarla en GitHub, se copia de aquí.

**Menciónalo sin demostrarlo:**

> Hay un segundo gancho, el de `push`. Si alguna vez están parados en `main` y hacen `git push`, sale **ENVÍO BLOQUEADO** y no pasa nada. Es a propósito: escribir directo en `main` se salta la revisión y se salta las verificaciones, y los otros cuatro se enteran cuando su `pull` les trae algo que no esperaban.

---

## 6 · Llenar la solicitud · 3 min

**En pantalla:** el navegador, en la página de la solicitud nueva.

**Qué dices, recorriendo la página:**

> El título viene puesto con mi mensaje de commit, y así está bien. Si hubiera hecho varios commits, GitHub pone cualquiera y hay que corregirlo al formato.
>
> Y la descripción viene **con plantilla**. No hay que inventar qué escribir: son tres preguntas.

**Pega esto, apartado por apartado, leyéndolo:**

```markdown
## Qué cambia

Agrega docs/equipo/entorno/a.md con mi sistema operativo, la ruta donde vive
el repositorio y las versiones de git, gh y python3 de mi máquina.

## Cómo se probó

Cada versión de la tabla es la salida literal de su comando, corrida hoy.
Docker aparece como pendiente porque no lo tengo instalado todavía; lo
necesito hasta la semana 7.

## Qué podría romper

Nada. Es un archivo nuevo de documentación y ningún otro archivo lo lee.

---

Closes #37
```

**Qué dices:**

> **Qué cambia** es en dos o tres líneas, y es *qué hace*, no *cómo lo hiciste*.
>
> **Cómo se probó** tiene que ser concreto y repetible. «Se probó y funciona» no sirve: no dice qué se probó ni cómo, así que el revisor no lo puede repetir. Y «no se probó» es una respuesta válida cuando aplica. Inventar que se probó, no.
>
> **Qué podría romper** es la que más se salta y la más útil. Si de verdad crees que nada, escribe **por qué** nada. Aquí es «es un archivo nuevo y nadie lo lee», que es una razón. «Nada» a secas no lo es.
>
> Y esta línea de abajo, `Closes` y el número de su issue, es la que más trabajo ahorra de todo el video: **cuando esto se incorpore, el issue se cierra solo y la tarjeta se mueve sola a Hecho.** Sin ella hay que ir a cerrarlo a mano y alguien se va a olvidar. El número está en su tarjeta, en el tablero.

**En pantalla:** la barra derecha. Llénala en cámara.

| Campo | Qué pones | Qué dices |
|---|---|---|
| **Reviewers** | `Wolff06` | «Sin revisor, la solicitud no está lista. Quién les toca está en la tabla: es su **segundo**, el mismo de las reglas de suplencia. No es al azar — revisar es cómo su segundo se entera de lo que pasa en su frente, y es quien tendría que sostener su demostración si faltan el día de la presentación» |
| **Assignees** | tú | «Ustedes. Para que se vea de quién es» |
| **Labels** | la del frente: `datos` | «La misma etiqueta de frente que trae su issue. Sirve para filtrar después» |
| **Projects** | `CanastaMX — Semestre 2026-2` | «Para que aparezca en el tablero junto al issue» |

> Y avisen en el chat. GitHub manda correo, y el correo no lo lee nadie.

---

## 7 · Las verificaciones · 2 min

**En pantalla:** abajo de la solicitud, el bloque de *checks*. Espera a que corran.

**Qué dices:**

> Esto de aquí abajo corre solo cada vez que suben algo. Son tres.
>
> **Higiene** revisa que no haya un `.env` versionado, ni carpetas de dependencias, ni archivos de más de diez megas. Es lo mismo que el gancho, pero del lado del servidor. **Esa es la que verifica de verdad desde hoy.**
>
> **Dominio (Java)** compila el servicio de Liseth y **Datos (Python)** revisa el código de Python. Y ahora viene lo que los va a confundir: **las dos van a salir verdes sin haber hecho nada.**
>
> No están rotas. Cada una empieza preguntando si el proyecto que le toca ya existe. Hoy la carpeta del dominio solo tiene un archivo vacío y no hay ni un `.py`, así que dejan una nota que dice «todavía no hay `pom.xml`, se omite» y terminan en verde.
>
> Está hecho así a propósito. Si intentaran compilar un proyecto que no existe, saldrían **rojas en todas las solicitudes del equipo**, incluidas las de documentación como esta, y en dos días nadie miraría el color. Con la guarda, empiezan a verificar solas: en cuanto Liseth suba su `pom.xml`, la de Java compila sin que nadie toque nada.

**Muestra los símbolos:**

> Punto amarillo girando: está corriendo, espérense uno o dos minutos. Palomita verde: pasó. Tache rojo: falló, y ahí le dan a **Details** y leen el registro; el error casi siempre está al final.
>
> Y si sale rojo: lo arreglan **en su máquina**, hacen `add`, `commit` y `push` **a la misma rama**, y la solicitud se actualiza sola. **No abran una solicitud nueva.** Una rama recibe todos los commits que haga falta y la conversación se conserva.

---

## 8 · La revisión · 1.5 min

**En pantalla:** la pestaña *Files changed*.

**Qué dices:**

> Esto es lo que ve quien los revisa. Verde es lo que se agregó, rojo lo que se quitó.
>
> Revisar no es aprobar por compromiso. Son diez minutos y le ahorran una semana al equipo. Se hace así: se lee el diff, se hace clic en el número de línea para preguntar ahí mismo lo que no se entienda —**preguntar no es agredir**, es cómo funciona esto— y se contrasta contra el criterio del issue. Si el issue pedía las versiones reales y la tabla dice «la última», todavía no queda.
>
> Y luego **Review changes**, con tres opciones: **Approve** si se puede incorporar. **Request changes** si falta algo concreto, y ahí hay que decir **qué** falta, no «no me convence». Y **Comment** para dudas que no bloquean.
>
> Aprobar sin leer no es amabilidad. Es pasarle el problema al que venga después.

---

## 9 · Squash and merge · 1.5 min

**En pantalla:** el botón verde, con su flechita desplegada mostrando las tres opciones.

**Qué dices:**

> Con la verificación en verde y una aprobación, se incorpora. Hay tres botones y **siempre usamos el mismo: Squash and merge.**
>
> *Squash* aplasta todos los commits de su rama en **uno solo** sobre `main`. Si trabajaron cuatro horas e hicieron ocho commits —incluidos el «arreglo el typo» y el «ahora sí»—, en `main` queda una sola línea limpia. Así el historial de `main` se vuelve la lista de tareas terminadas, legible de corrido.

**Haces:** *Squash and merge* → *Confirm squash and merge* → *Delete branch*.

> Confirmar, y **borrar la rama**. Ya está incorporada; dejarla ahí solo llena la lista de basura. Y si se arrepienten, mientras GitHub siga mostrando *Restore branch* se puede recuperar.

---

## 10 · De vuelta a la terminal · 1.5 min

**Qué tecleas:**

```bash
git switch main
git pull
git branch -D docs/alm-entorno-a
git log --oneline -3
```

**Qué dices:**

> Esto se les va a olvidar y es el que más problemas causa. Su `main` local **no se enteró** de nada: la fusión pasó en el servidor. Sin este `pull`, la próxima rama que hagan nace vieja.
>
> Y ahora una cosa rara que van a ver siempre. Al borrar la rama con `-d` minúscula, Git avisa que «no está fusionada». Es mentira, pero tiene su lógica: *squash* creó en `main` un commit **nuevo**, distinto del suyo. Git compara identidades, no contenidos, y no lo reconoce. Por eso se usa `-D` mayúscula, que fuerza el borrado.
>
> **Va a pasar en todas las solicitudes del semestre.** No es señal de nada malo. Pero úsenla solo después de confirmar que su cambio ya está en `main`, que es justo lo que muestra este `git log`.

---

## 11 · La tarjeta se movió sola · 30 s

**En pantalla:** el tablero.

**Qué dices:**

> Y miren: la tarjeta está en **Hecho** y el issue cerrado, sin que nadie los tocara. Eso lo hizo la línea `Closes` de la descripción. Ese es todo el ciclo.

---

## 12 · Lo que NO se hace · 2 min

**En pantalla:** tú hablando, o la terminal quieta.

**Qué dices:**

> Tres cosas que se ven fáciles y cuestan caro.
>
> **La primera: `--no-verify`.** No la voy a escribir en pantalla y no quiero que ustedes la escriban nunca. La menciono porque **el mensaje del gancho se las va a ofrecer solito** —vuelvan al minuto cinco y léanlo: ahí está, al final— y prefiero que sepan por mí qué es, a que la encuentren en el peor momento sin saber qué hace.
>
> Apaga los ganchos. Existe por razones legítimas: un gancho mal escrito que bloquea todo, una emergencia a las tres de la mañana con la herramienta rota. **Ninguna de esas es nuestro caso.**
>
> Aquí `--no-verify` significa una de tres: que el gancho atrapó de verdad un `.env` o un archivo pesado, y entonces **tiene razón**; que el gancho está mal y bloquea algo válido, y entonces **hay que decirlo** para arreglarlo para los cinco; o que traes prisa, y esa prisa la paga otro después.
>
> Y les digo la verdad completa: **`--no-verify` no se puede impedir.** Los ganchos corren en su máquina y ustedes mandan en su máquina. No hay forma de bloquear esa bandera. Lo único que la sostiene es que entiendan de qué los está cuidando. Eso sí: la verificación **Higiene** revisa lo mismo del lado del servidor, así que si se saltan el gancho, la solicitud se pone roja igual — pero ya en público y diez minutos después.
>
> **La segunda: `git add .` sin mirar.** El punto agarra todo lo que haya en la carpeta. Antes de confirmar, siempre `git status` y leerlo.
>
> **La tercera: trabajar sobre `main`.** Si se les olvida crear la rama y ya hicieron el commit, no pasa nada grave: se crea la rama ahí mismo con `git switch -c`, el commit se va con ella, y `main` se devuelve con `git branch -f main origin/main`. Pero avisen, no lo arreglen a escondidas.

---

## 13 · Quién aprueba, si `main` no está protegida · 2 min

**Qué dices:**

> Y termino con lo más importante, que es una pregunta incómoda: **¿qué impide que alguien se salte todo esto?**
>
> Hoy, honestamente: **nada. Solo el acuerdo.**
>
> En un repositorio con protección de ramas, GitHub bloquearía de su lado: no dejaría incorporar sin una aprobación ni con las verificaciones en rojo. Nosotros no la tenemos, y no es por descuido: GitHub no cobra por proteger ramas en repositorios **públicos**, pero sí en los **privados**, y el nuestro es privado. Estamos resolviendo eso.
>
> Mientras tanto tenemos tres capas. Los **ganchos**, que son locales y se pueden saltar. La verificación **Higiene**, que no se puede saltar pero solo reporta. Y el **acuerdo**, que depende de que se vea.
>
> Y para que se vea, cada reunión semanal empieza con dos comandos, en pantalla compartida.

**Qué tecleas, en cámara:**

```bash
git log main --format='%h  %an  %s' | grep -v '(#[0-9]\+)$'
```

> Cada incorporación deja el número de la solicitud al final. Lo que no lo tiene, entró por fuera. Hoy salen dos, de antes de que existiera este acuerdo. **Cualquier tercero es un salto de la regla.**

```bash
gh pr list --state merged --limit 50 --json number,title,author,reviewDecision \
  --jq '.[] | select(.number > 6) | select(.reviewDecision != "APPROVED") | "#\(.number)  \(.author.login)  \(.title)"'
```

> Y este lista lo que se incorporó sin que nadie lo aprobara. De la número siete en adelante, lo ideal es que no imprima nada.
>
> Lo digo claro, incluyéndome: **la que más importa vigilar aquí soy yo.** Soy la dueña del repositorio y la coordinadora; soy la que puede saltarse la regla sin que nadie me diga nada. Si la primera solicitud sin aprobar es mía, la regla se murió para los cinco. Por eso los comandos se corren en pantalla compartida y no en privado, y por eso les pido que si ven mi nombre ahí, lo digan.

---

# Después de grabar

- [ ] Míralo completo una vez. Si algo no se lee en el teléfono, se regraba esa escena.
- [ ] Sube el video a Drive y pon el enlace en `docs/equipo/README.md`, en la tabla de enlaces.
- [ ] Pega los capítulos con los minutos reales en la descripción del video.
- [ ] Compártelo **antes** de la reunión del lunes, no durante. Quien llegue habiéndolo visto avanza al doble.

> **Y si algo del video queda desactualizado** —cambia un guión, se activa la protección de ramas— **no se regraba entero.** Se anota en `docs/equipo/README.md` qué parte ya no aplica, y se regraba solo ese capítulo cuando valga la pena.
