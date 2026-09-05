# Guion de la reunión de arranque

**Lunes 7 de septiembre · 75 minutos · los cinco, cámara encendida y pantalla compartida.**

Esto no es un documento para leer solo: es el guion de una sesión que conduce A. Cada quien trabaja **en su propia máquina al mismo tiempo**, no mirando. Al final de la sesión los cinco han clonado, han instalado los ganchos y **han incorporado un cambio real a `main` por su propia solicitud.**

> **Sobre los 75 minutos.** El cronograma decía 30. Son pocos: alcanzan para clonar, no para que cinco personas entiendan el ciclo. Setenta y cinco minutos el lunes valen más que tres tardes de mensajes en el chat durante la semana. Si de plano no hay 75 seguidos, se parte en dos: **acto 1 el lunes temprano** (nadie puede trabajar sin eso) y **acto 2 el lunes al mediodía**, antes de que alguien tenga algo que subir.

| | Qué | Cuánto |
|---|---|---|
| **Antes** | A sola, sin el equipo | 10 min |
| **Acto 1** | De cero a «puedo trabajar» | 25 min |
| **Acto 2** | Una tarea completa, de la tarjeta a Hecho | 45 min |
| **Cierre** | Acuerdos y horario fijo | 5 min |

---

# Antes de la reunión · A sola, 10 minutos

## Comprueba que el punto de partida está sano

```bash
cd ~/projects/canastamx
git switch main && git pull
git log --oneline -3
git tag
bash infra/scripts/verificar-base.sh A
```

Tiene que aparecer la etiqueta `base-v0` y la verificación en verde. **Si algo sale en rojo, se arregla antes de la reunión, no durante.** Cinco personas esperando mientras se depura es la peor forma de gastar el arranque.

## Siembra las cinco tarjetas de práctica

El acto 2 no puede ser un ejercicio inventado: si el cambio es falso, nadie lo toma en serio y no queda nada. Cada quien va a escribir **la ficha de su entorno de trabajo**, que es un documento que el equipo va a necesitar de verdad en noviembre, la primera vez que alguien diga «en mi máquina sí funciona».

Crea los cinco issues:

```bash
cd ~/projects/canastamx

crear() {  # $1 clave · $2 usuario · $3 etiqueta
  gh issue create --repo arik36/canastamx \
    --title "[S1][Entorno] Ficha de entorno de $1" \
    --label "$3" --assignee "$2" \
    --body "## Qué hay que hacer

Escribir \`docs/equipo/entorno/$1.md\` con el sistema operativo, la ruta donde
vive el repositorio y la versión de cada herramienta instalada. La plantilla
está en \`docs/equipo/reunion-de-arranque.md\`.

## Cómo saber que quedó

El archivo existe, ninguna versión dice «pendiente» sin una nota de por qué,
y otro integrante puede leerlo y saber con qué estás trabajando.

## Dónde queda

\`docs/equipo/entorno/$1.md\`

---

Semana 1 · Tarea de práctica de la reunión de arranque · Fecha límite: 7 sep de 2026"
}

crear A  arik36      datos
crear B  Wolff06     infra
crear C1 lisslar     dominio
crear C2 Renato-Rios movil
crear D  alesitaK    web
```

Agrégalos al tablero, ponles `Semana 1` y su `Frente`, y déjalos en **Esta semana**.

## Ten a la mano, en pestañas abiertas

El repositorio · el tablero · el panel · este guion.

---

# Acto 1 · De cero a «puedo trabajar» · 25 minutos

> **Cómo se conduce:** A comparte pantalla y hace cada paso. Los otros cuatro lo hacen **al mismo tiempo**, no después. Después de cada paso, A pregunta por nombre: «¿Liseth, te salió?». Nadie avanza hasta que los cinco dicen que sí. Es lento a propósito: un rezagado silencioso el lunes es una persona bloqueada el miércoles.

## 1.1 · Git existe y sabe quién eres

```bash
git --version
git config --global user.name  "Nombre Apellido"
git config --global user.email "el-mismo-correo-de-github@ejemplo.com"
```

**Por qué importa el correo:** es lo único que ata un commit a una persona. Si no coincide con el de tu cuenta de GitHub, tus commits aparecen como de un desconocido y **tu trabajo no cuenta como tuyo ante el asesor.** Se arregla ahora en diez segundos; en noviembre, reescribiendo el historial.

Verifica que quedó:

```bash
git config --global --list | grep user
```

## 1.2 · GitHub CLI y la sesión

```bash
gh --version || sudo apt install gh    # Ubuntu/WSL
gh auth login
```

En las preguntas: **GitHub.com** → **HTTPS** → **Login with a web browser**.

> **Por qué HTTPS y no SSH.** Con HTTPS, `gh` guarda la credencial y ya no te vuelve a pedir nada. Con SSH tienes que generar una llave, subirla, y escribir la frase de paso **en cada push**. A usa SSH porque ya lo tenía montado; ustedes cuatro no empiecen por ahí. Si alguien ya tiene SSH funcionando, que lo deje.

## 1.3 · Clonar

```bash
mkdir -p ~/projects && cd ~/projects
gh repo clone arik36/canastamx
cd canastamx
```

**Dónde NO clonar, si usan WSL:** en `/mnt/c/...`. Es el disco de Windows visto desde Linux y Git ahí va entre cinco y veinte veces más lento, además de que ensucia todo con archivos `:Zone.Identifier`. Clonen en `~/projects`, que es disco de Linux.

**Dónde NO clonar, todos:** dentro de OneDrive, Dropbox o Google Drive. Sincronizan la carpeta `.git` a medio commit y la corrompen.

## 1.4 · Instalar los ganchos

```bash
bash infra/scripts/instalar-hooks.sh
```

Comprueba:

```bash
git config core.hooksPath      # debe decir: .githooks
```

**Por qué esto no viene con el clon.** Los ganchos son archivos ejecutables que Git corre solo en tu máquina. Si vinieran activados por defecto, clonar un repositorio cualquiera de internet ejecutaría código de un desconocido en tu computadora. Por eso Git obliga a que cada quien los active a mano. **Son cinco activaciones distintas, una por persona.** Si alguien se lo salta, sus protecciones simplemente no existen y nadie se entera hasta que rompe algo.

## 1.5 · La verificación de línea base

Cada quien con **su** clave:

```bash
bash infra/scripts/verificar-base.sh C1     # A · B · C1 · C2 · D
```

| Si dice | Qué haces |
|---|---|
| **PUEDES CREAR TU RAMA** | Listo |
| Falta algo **del repositorio** | **No lo subas por tu cuenta.** Avisa en el chat; lo arregla su dueño |
| Falta algo **de tu máquina** (una herramienta) | Instálalo. Es tuyo |

**Por qué existe este paso.** Ramificar desde un `main` incompleto produce trabajo que hay que tirar. El caso más caro: si ramificas antes de que exista el `.gitignore`, tu primer `git add .` se lleva `node_modules/` o `target/` — cientos de archivos generados, en una solicitud que nadie puede revisar.

## ✅ Punto de control del acto 1

Los cinco dicen en voz alta:

- [ ] `git config --global --list | grep user` muestra mi nombre y mi correo de GitHub
- [ ] Clonado en disco de Linux, fuera de carpetas que sincronizan
- [ ] `git config core.hooksPath` dice `.githooks`
- [ ] `verificar-base.sh <mi clave>` en verde

---

# Acto 2 · Una tarea completa · 45 minutos

> **Cómo se conduce:** A hace **el recorrido entero en pantalla, sola, sin que nadie la siga** (12 minutos). Luego los cuatro lo hacen en paralelo con su propia tarjeta (25 minutos), y A va rescatando al que se atore. Los últimos 8 minutos son para revisarse entre ustedes.
>
> El orden importa: si los cinco teclean al mismo tiempo mientras A explica, nadie escucha el porqué y todos preguntan lo mismo el miércoles.

## 2.0 · Lo que van a entregar

`docs/equipo/entorno/<tu clave>.md`. Copien esta plantilla y llénenla:

```markdown
# Entorno de trabajo · C1 · Liseth

## Máquina

- **Sistema operativo:** Windows 11 24H2 + WSL2 Ubuntu 24.04
- **Terminal que uso:** Windows Terminal, perfil Ubuntu
- **Dónde vive el repositorio:** `/home/liseth/projects/canastamx`

## Herramientas

| Herramienta | Versión | Cómo la comprobé |
|---|---|---|
| git | 2.43.0 | `git --version` |
| gh | 2.45.0 | `gh --version` |
| Java | 21.0.4 Temurin | `java -version` |
| Maven | 3.9.6 | `mvn -v` |
| Docker | pendiente | no instalado todavía, lo necesito hasta la semana 7 |

## Notas

Lo que otro integrante necesita saber para reproducir un problema mío:
por ejemplo, que uso WSL y no Linux nativo, o que mi Docker corre sin sudo.
```

**Las versiones se copian de la salida real del comando.** Inventarlas hace que este documento sea peor que no tenerlo: en noviembre alguien va a depurar contra una versión que nunca existió.

Qué comprobar según tu frente:

| | Comandos |
|---|---|
| **A** · datos | `git --version` · `gh --version` · `python3 --version` · `pip --version` |
| **B** · infra | `git --version` · `gh --version` · `docker --version` · `docker compose version` |
| **C1** · dominio | `git --version` · `gh --version` · `java -version` · `mvn -v` |
| **C2** · móvil | `git --version` · `gh --version` · `node --version` · `npm --version` |
| **D** · web | `git --version` · `gh --version` · `node --version` · el navegador y su versión |

Si un comando dice *command not found*, se escribe `pendiente` con una nota. **Eso es información valiosa, no una falta:** significa que hay una instalación que hacer antes de la semana en que se necesita, y es mucho mejor saberlo hoy.

## 2.1 · Tomar la tarjeta

En el tablero, en tu tarjeta:

1. **Assignees** → tú, si no estabas ya.
2. Muévela de `Esta semana` a **`En curso`**.

**Por qué se mueve antes de empezar y no al terminar.** La columna `En curso` es lo único que le dice al resto en qué estás. Si la mueves al final, nadie supo en toda la tarde que ya estabas en eso, y dos personas pueden haber tocado el mismo archivo.

**El límite: dos tarjetas en `En curso` por persona.** Si necesitas una tercera, primero cierras una. Es lo único que impide tener siete cosas empezadas y ninguna terminada.

## 2.2 · La rama

```bash
git switch main
git pull
git switch -c docs/lyl-entorno-c1
```

**Los tres comandos, en ese orden, cada vez.** El `pull` es el que se olvida y el que cuesta: si ramificas desde un `main` de hace tres días, tu rama nace vieja y el conflicto aparece al final, cuando ya no tienes tiempo.

**El nombre:** `tipo/iniciales-descripcion`.

| Tipo | Para |
|---|---|
| `feat` | Funcionalidad nueva |
| `fix` | Corrección |
| `docs` | Documentación |
| `test` | Pruebas |
| `chore` | Configuración, guiones, mantenimiento |

Iniciales: `alm` · `aas` · `lyl` · `orf` · `kah`. Sin acentos, sin eñes, sin espacios, en minúsculas.

Comprueba dónde estás:

```bash
git branch --show-current
```

## 2.3 · El trabajo

```bash
mkdir -p docs/equipo/entorno
nano docs/equipo/entorno/c1.md      # o el editor que uses
```

Llena la plantilla con **la salida real** de tus comandos.

## 2.4 · El commit, y el primer gancho

```bash
git status
```

Léelo. Dice `Untracked files: docs/equipo/entorno/c1.md`. Git ve el archivo pero todavía no lo va a guardar.

```bash
git add docs/equipo/entorno/c1.md
git status
```

Ahora dice `Changes to be committed`. **Eso es el área de preparación:** el montón de lo que va a entrar en el próximo commit. Existe para que puedas confirmar tres archivos de cinco cuando los otros dos no están listos.

```bash
git commit -m "docs(equipo): ficha de entorno de trabajo de C1"
```

**El formato del mensaje:** `tipo(ámbito): descripción en presente`. En presente y en tercera persona: «agrega la ficha», no «agregué la ficha» ni «agregando». Es la convención que hace legible el historial cuando tenga doscientos commits.

Ámbitos: `data` · `infra` · `domain` · `mobile` · `web` · `docs` · `ci` · `equipo`.

### 🎬 Demostración que hace A, una sola vez

Aquí es donde el gancho se ve funcionando. A, en pantalla:

```bash
echo "POSTGRES_PASSWORD=Sup3rSecreta" > .env
git add -f .env
git commit -m "prueba"
```

Sale esto:

```
  ✗ Estás por confirmar un archivo .env.
    Solo .env.example puede subirse, y con los valores VACÍOS.
    Sácalo con:  git restore --staged .env

  Confirmación cancelada. Si de verdad sabes lo que haces: git commit --no-verify
```

Y se deshace:

```bash
git restore --staged .env && rm .env
```

**Lo que hay que entender de esa pantalla:** el gancho `pre-commit` revisa tres cosas antes de dejarte confirmar — que no vaya un `.env`, que no vayan carpetas de dependencias, que no vaya nada de más de 10 MB. Son los tres errores **que no se arreglan borrando el archivo después**: una vez que algo entra al historial de Git, sigue ahí aunque lo borres en un commit posterior. Una contraseña subida es una contraseña quemada.

## 2.5 · El push, y el segundo gancho

```bash
git push -u origin docs/lyl-entorno-c1
```

El `-u` es solo la primera vez de cada rama: ata tu rama local a la del servidor, y a partir de ahí `git push` a secas basta.

Fíjate en lo que imprime: **una dirección para abrir la solicitud.** Cópiala.

```
remote: Create a pull request for 'docs/lyl-entorno-c1' on GitHub by visiting:
remote:      https://github.com/arik36/canastamx/pull/new/docs/lyl-entorno-c1
```

### El otro gancho: `pre-push`

Si alguna vez estás en `main` y haces `git push`, sale esto y no pasa nada:

```
  ✗ ENVÍO BLOQUEADO — estás empujando directo a 'main'.
```

**Por qué está.** Escribir directo en `main` es el error que rompe el trabajo de los otros cuatro: se salta la revisión, se salta la integración continua, y el resto se entera cuando su `git pull` trae algo que no esperaban. En un repositorio con protección de ramas, GitHub lo impediría del lado del servidor. Como todavía no la tenemos *(ver la última sección)*, este gancho es la red — y por eso el paso 1.4 no es opcional.

## 2.6 · La solicitud, en la web

Abre la dirección. La página trae **el título** y **la plantilla ya puesta**.

### El título

El mismo formato del commit. GitHub lo prellena con tu mensaje; si tenías varios commits, lo pone mal y hay que corregirlo:

```
docs(equipo): ficha de entorno de trabajo de C1
```

### La descripción

Los tres apartados de la plantilla, llenos. Así se ve uno bien llenado:

```markdown
## Qué cambia

Agrega docs/equipo/entorno/c1.md con el sistema operativo, la ruta del
repositorio y las versiones de git, gh, Java y Maven de mi máquina.

## Cómo se probó

Cada versión de la tabla es la salida literal de su comando, corrida hoy.
Docker aparece como pendiente porque no lo tengo instalado; lo necesito
hasta la semana 7.

## Qué podría romper

Nada: es un archivo nuevo de documentación, ningún otro archivo lo lee.

---

Closes #37
```

Lo que hace mala una descripción, y pasa siempre:

| Se escribe | Por qué no sirve |
|---|---|
| «Cambios varios» | El revisor tiene que leer el diff completo para saber qué mirar |
| «Se probó y funciona» | No dice **qué** se probó ni **cómo**, así que no se puede repetir |
| «Nada» en *qué podría romper* | A veces es cierto. Escribe **por qué** es cierto |

**`Closes #37` es la línea que más trabajo ahorra.** Con ella, al incorporarse la solicitud el issue se cierra solo y la tarjeta se mueve sola a `Hecho`. Sin ella, hay que ir a cerrar el issue a mano y alguien va a olvidarlo. El número es el de **tu** issue: lo ves en el tablero, en la tarjeta.

### Etiquetas, revisor, responsable

En la barra derecha:

| Campo | Qué pones |
|---|---|
| **Reviewers** | El de la tabla de abajo. **Sin revisor, la solicitud no está lista** |
| **Assignees** | Tú |
| **Labels** | La misma etiqueta de frente que trae tu issue: `datos` `infra` `dominio` `movil` `web` |
| **Projects** | `CanastaMX — Semestre 2026-2` |

Quién te revisa:

| Tú eres | Te revisa | Si no está |
|---|---|---|
| **A** · Ariadne | B · Ari Adair | C1 |
| **B** · Ari Adair | A · Ariadne | C1 |
| **C1** · Liseth | C2 · Oscar | A |
| **C2** · Oscar | C1 · Liseth | D |
| **D** · Karen | C2 · Oscar | A |

No es aleatorio: es la tabla de suplencias de [`como-trabajamos.md`](./como-trabajamos.md). Tu segundo te revisa porque **revisar es cómo se entera de lo que pasa en tu frente**, y es quien tendría que sostener tu demostración si faltas el día de la presentación.

Y avisa en el chat. GitHub manda correo, y el correo no lo lee nadie.

## 2.7 · Las verificaciones de integración continua

Abajo de la conversación aparece un bloque con tres renglones. Es lo que corre solo cada vez que subes algo:

| Verificación | Qué hace |
|---|---|
| **Higiene** | Que no haya `.env` versionado, ni carpetas de dependencias, ni archivos de más de 10 MB |
| **Dominio (Java)** | Compila `services/domain-service` |
| **Datos (Python)** | Análisis estático de los `.py` de `services/` |

Los símbolos:

| | Qué significa | Qué haces |
|---|---|---|
| 🟡 punto amarillo girando | Está corriendo | Esperas. Uno o dos minutos |
| ✅ palomita verde | Pasó | Nada |
| ❌ tache rojo | Falló | **Details** → lees el registro |
| ⬜ gris | No corrió | Suele ser que otra falló antes |

### Lo que va a confundir el lunes

**`Dominio (Java)` y `Datos (Python)` van a salir verdes sin hacer nada, y eso está bien.** Los dos empiezan preguntando si el proyecto que les toca ya existe. Hoy `services/domain-service/` solo tiene un `.gitkeep` y no hay ningún `.py`, así que dejan una nota que dice *«Todavía no hay pom.xml… se omite»* y terminan **en verde**.

Es deliberado. Una canalización que intentara compilar un proyecto inexistente saldría **roja en todas las solicitudes del equipo**, incluidas las de documentación, y en dos días nadie miraría el color. Con la guarda, empiezan a verificar de verdad solas: en cuanto C1 suba su `pom.xml`, `Dominio (Java)` compila sin que nadie toque el archivo.

**La que sí verifica desde hoy es `Higiene`**, y es la que más sirve, porque atrapa justo lo que no se arregla borrando el archivo después.

### Si sale roja

1. **Details** → lee el registro. El error está en la línea roja, casi siempre al final.
2. Arréglalo **en tu máquina**.
3. `git add` → `git commit` → `git push`, **a la misma rama**.
4. La solicitud se actualiza sola y la canalización vuelve a correr.

**No abras una solicitud nueva.** Una rama puede recibir todos los commits que necesite; la solicitud sigue siendo la misma y guarda la conversación entera.

## 2.8 · La revisión

El revisor entra a **Files changed**.

- Verde es lo que se agregó, rojo lo que se quitó.
- Clic en el número de línea para comentar ahí mismo. **Preguntar no es agredir**: es cómo funciona.
- Contrasta contra el criterio del issue, el apartado *cómo saber que quedó*. Si el issue pedía las versiones reales y la tabla dice «la última», todavía no queda.

**Review changes** → una de tres:

| | Cuándo |
|---|---|
| **Approve** | Se puede incorporar |
| **Request changes** | Falta algo concreto. **Di qué**, no «no me convence» |
| **Comment** | Dudas que no bloquean |

Revisar toma diez minutos y ahorra semanas. Aprobar sin leer no es amabilidad: es dejar pasar el problema al que venga después.

> **Para el lunes, revísense en círculo** para que los cinco practiquen las dos puntas: A→B, B→C1, C1→C2, C2→D, D→A. A partir del martes se usa la tabla de arriba.

## 2.9 · Incorporar

Con la verificación en verde y una aprobación:

**Squash and merge** → **Confirm squash and merge** → **Delete branch**.

**Por qué *squash* y no los otros dos botones.** Aplasta todos los commits de tu rama en **uno solo** sobre `main`. Si trabajaste cuatro horas y hiciste ocho commits —incluidos «arreglo el typo» y «ahora sí»—, en `main` queda una línea limpia: `docs(equipo): ficha de entorno de trabajo de C1 (#37)`. El historial de `main` se vuelve la lista de tareas terminadas, legible de corrido.

**Y por qué borrar la rama.** Ya está incorporada; dejarla llena la lista de ramas de basura. El botón la borra solo del servidor. Se puede recuperar mientras GitHub siga mostrando el botón *Restore branch*.

## 2.10 · De vuelta a la terminal

```bash
git switch main
git pull
git branch -D docs/lyl-entorno-c1
```

**Este `pull` es el paso que más se olvida y el que más problemas causa.** Sin él, tu `main` local se queda atrás y la próxima rama que hagas nace vieja.

**Y por qué `-D` (mayúscula) y no `-d`.** Porque *squash* creó en `main` un commit **nuevo**, distinto del tuyo. Git compara y concluye que tu rama «no está fusionada», aunque su contenido sí lo esté. La `-D` fuerza el borrado. **Va a pasar en todas las solicitudes del semestre**, así que no es señal de nada malo — pero úsala solo después de confirmar que tu cambio ya está en `main`.

De vez en cuando, para limpiar las referencias a ramas que ya no existen en el servidor:

```bash
git remote prune origin
```

## 2.11 · Cierra el círculo: mira el tablero

Tu tarjeta ya está en **Hecho** y el issue cerrado, sin que nadie los tocara. Eso lo hizo la línea `Closes #37`.

Si no se movió: `...` → **Workflows** → que **Item closed** esté activo y apunte a `Hecho`.

## ✅ Punto de control del acto 2

- [ ] Los cinco tienen su archivo en `main`
- [ ] Los cinco abrieron, revisaron y aprobaron una solicitud ajena
- [ ] Las cinco tarjetas están en `Hecho`
- [ ] Los cinco vieron el gancho bloquear un `.env`
- [ ] Los cinco entienden por qué dos verificaciones salen verdes sin hacer nada

---

# `--no-verify`: qué es y por qué no se usa

El propio gancho lo sugiere cuando te bloquea:

```
Confirmación cancelada. Si de verdad sabes lo que haces: git commit --no-verify
```

Esa bandera **apaga los ganchos** para ese comando. Existe por razones legítimas: un gancho mal escrito que bloquea todo, o un arreglo urgente a las tres de la mañana con la herramienta rota.

**Ninguna de esas es nuestro caso.** Aquí `--no-verify` significa exactamente una de tres cosas:

| Lo que pasó | Lo que hay que hacer en vez de la bandera |
|---|---|
| El gancho atrapó un `.env` o un archivo pesado | **Sacarlo.** El gancho tiene razón; ese es el error que no se deshace |
| El gancho está mal y bloquea algo válido | **Decirlo.** Es un defecto del gancho, se corrige para los cinco |
| Traigo prisa | La prisa se paga después, con intereses, y la paga otro |

Lo importante de entender: **`--no-verify` no se puede impedir.** Los ganchos corren en tu máquina, y tú mandas en tu máquina. No hay forma de bloquear la bandera.

Por eso el acuerdo no se sostiene en el gancho, sino en dos cosas: que todos entiendan **de qué los está cuidando**, y que las consecuencias se vean. La verificación **Higiene** de la canalización revisa lo mismo del lado del servidor: si te saltaste el gancho, la solicitud se pone roja igual. El gancho solo te lo dice diez minutos antes y sin que quede registrado en público.

---

# Quién aprueba las solicitudes, si `main` no está protegida

La pregunta correcta, y la respuesta honesta es que **hoy nadie lo impide: solo lo acordamos.** GitHub no cobra por proteger ramas en repositorios **públicos**, pero sí en los **privados** de cuenta personal, y el nuestro es privado.

## Lo que sí está puesto hoy

| Capa | Qué detiene | Qué tan fuerte |
|---|---|---|
| Gancho `pre-push` | Empujar directo a `main` | Local, por persona, saltable |
| Gancho `pre-commit` | `.env`, dependencias, archivos pesados | Local, por persona, saltable |
| Verificación **Higiene** | Lo mismo, del lado del servidor | **No es saltable**, pero solo reporta |
| El acuerdo | Todo lo demás | Depende de que se vea |

Nada de eso **impide** que alguien —incluida A— incorpore su propia solicitud sin revisión. Lo que sí se puede hacer es que **se note**.

## La auditoría de dos comandos

Se corre **al inicio de cada reunión semanal**, en pantalla compartida. Diez segundos.

**1 · ¿Entró algo a `main` sin solicitud?**

```bash
git switch main && git pull
git log main --format='%h  %an  %s' | grep -v '(#[0-9]\+)$'
```

Cada incorporación por *squash* deja el número de la solicitud al final: `… (#37)`. Lo que **no** lo tiene, entró por fuera.

Hoy salen dos, y son correctos: `858e858` y `3e1d6c7` son de antes de que existiera este acuerdo. **Cualquier tercero es un salto de la regla.**

**2 · ¿Se incorporó algo sin que nadie lo aprobara?**

```bash
gh pr list --state merged --limit 50 \
  --json number,title,author,reviewDecision \
  --jq '.[] | select(.number > 6) | select(.reviewDecision != "APPROVED")
        | "#\(.number)  \(.author.login)  \(.title)"'
```

Lista las solicitudes incorporadas **sin aprobación**. Lo ideal es que no imprima nada.

**Por qué empieza en la #7.** Las seis primeras se incorporaron sin revisión, y así tenía que ser: se hicieron antes de que el equipo tuviera acceso al repositorio, así que no había a quién pedírsela. Son la línea base de esta auditoría, igual que `858e858` y `3e1d6c7` lo son de la anterior. **De la #7 en adelante, cualquier número que aparezca aquí es un salto de la regla.**

> **A es el caso que más importa vigilar.** Es la dueña del repositorio y la coordinadora: es quien puede saltarse la regla sin fricción y sin que nadie se lo diga. Si la primera solicitud sin aprobar es suya, la regla está muerta para los cinco desde esa semana. Por eso la auditoría se corre en pantalla compartida y no en privado.

## La decisión que hay que tomar antes del lunes

Tres caminos. **Hay que elegir uno**, porque «ya veremos» es en la práctica el tercero.

### Camino 1 · Hacer el repositorio público ahora

La protección de ramas es gratuita en repositorios públicos. Se activa hoy mismo, sin esperar nada.

**A favor**
- Protección de `main` **hoy**: solicitud obligatoria, una aprobación, verificaciones en verde. Deja de ser un acuerdo y pasa a ser un candado.
- **Minutos de GitHub Actions ilimitados.** En repositorios privados hay una bolsa mensual, y por eso quedó pendiente lo de `timeout-minutes`. En público ese problema desaparece.
- El asesor puede verlo sin invitación.
- El plan ya termina en público: es el criterio de cierre de la última tarea del semestre.

**En contra**
- Cualquiera puede leerlo, y copiarlo. En un proyecto escolar con calificación, no es trivial.
- Lo que entre al historial queda expuesto para siempre. Los ganchos y la verificación **Higiene** están justamente para eso, pero el margen de error se vuelve cero.
- **Puede que el reglamento de la materia pida que sea privado.** Hay que confirmarlo con el asesor antes, no después.

### Camino 2 · Esperar el GitHub Student Pack

Da GitHub Pro gratis, y con Pro la protección funciona en repositorios privados. **La solicitud la tiene que enviar A**, que es la dueña de `arik36/canastamx` — que la envíe B no sirve de nada.

Tarda de unos días a un par de semanas y **piden comprobante de estudios**: credencial vigente, constancia o correo institucional. Mientras tanto se trabaja con los ganchos y la auditoría.

### Camino 3 · Quedarse sin protección todo el semestre

Es viable —los ganchos más la auditoría cubren bastante— pero hay que decirlo en voz alta y que los cinco lo sepan, en vez de dejarlo por omisión.

> **Recomendación:** enviar la solicitud del Student Pack **hoy** (es gratis, no compromete a nada y tarda), y preguntarle al asesor el lunes si el repositorio puede ser público. Si dice que sí, se hace público y queda protegido esa misma tarde. Si dice que no, el Student Pack ya viene en camino y mientras tanto se corren los dos comandos de auditoría cada semana.

---

# Cierre · 5 minutos

- [ ] **Horario fijo de la reunión semanal.** Se acuerda hoy y no se mueve el resto del semestre. Un equipo que renegocia el horario cada semana termina reuniéndose cada tres.
- [ ] Los cinco tienen el enlace del panel guardado en el teléfono.
- [ ] Los cinco saben cuál es su tarea del martes y ya leyeron su ficha.
- [ ] A envía la solicitud del Student Pack.
- [ ] Se decide el camino de la protección de `main`.

---

# Lo que va a pasar el lunes, y qué contestar

| Lo que dicen | Qué pasó | La salida |
|---|---|---|
| «`Permission denied (publickey)`» | Clonaron por SSH sin llave | `gh auth login` otra vez, eligiendo **HTTPS** |
| «`fatal: not a git repository`» | Están fuera de la carpeta | `cd ~/projects/canastamx` |
| «No me deja hacer push» | Están en `main`. El gancho hizo su trabajo | `git switch -c tipo/iniciales-descripcion`, y el commit se va con la rama |
| «Mi commit no aparece con mi nombre» | El correo de Git no es el de GitHub | Paso 1.1, y se arregla para los siguientes |
| «La canalización dice *skipped*» | La guarda. Es lo correcto | Sección 2.7 |
| «`Your branch is behind`» | No hicieron `git pull` | `git switch main && git pull` |
| «Se me borró todo» | Casi nunca es cierto | `git reflog`. Casi todo se recupera. **Que nadie borre la carpeta sin avisar** |
| «No veo el tablero» | No tienen acceso al proyecto | A los invita: Settings → Manage access, permiso **Write** |
| «El `-d` dice que no está fusionada» | *Squash*. Es normal | `-D`, después de confirmar que ya está en `main` |
