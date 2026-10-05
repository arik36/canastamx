# Estrategia de ramas · CanastaMX

**Autores:** Ariadne Macías (A) y Ari Adair Soto (B) · T032 · issue #94

> **Qué es esto.** Pone en un solo lugar el convenio que el equipo **ya usa**, y que
> hoy está repartido en `git-paso-a-paso.md`, `ciclo-de-trabajo.md` y la plantilla
> de solicitud. No inventa reglas: las que salieron de la práctica de septiembre y
> octubre dicen de qué caso vienen. Las cifras se midieron sobre `main` el 4 de
> octubre de 2026.

---

## 1 · Una rama por tarea; todo entra a `main` por solicitud

`main` siempre está integrable. Nadie trabaja directo en `main`: cada tarea del
tablero tiene su rama, y la rama entra a `main` con una **solicitud de cambios**
(PR), con revisión pedida a otra persona y la integración continua en verde.

Hay dos capas que lo impiden. En tu máquina, el gancho `pre-push` de
`.githooks/` (ver `ciclo-de-trabajo.md` para activarlo). En GitHub, la regla
«main protegida.» (§7).

## 2 · Cómo se llama la rama

`tipo/iniciales-descripcion-corta`: todo en minúsculas, sin acentos y con las
palabras separadas por guiones.

| Tipo | Cuándo |
|---|---|
| `feat` | Funcionalidad nueva |
| `fix` | Corriges algo roto |
| `docs` | Sólo documentación |
| `test` | Sólo pruebas |
| `chore` | Configuración, dependencias, limpieza |
| `refactor` | Reacomodas código sin cambiar lo que hace |

| Integrante | Iniciales |
|---|---|
| A · Ariadne | `alm` |
| B · Ari Adair | `aas` |
| C1 · Liseth | `lyl` |
| C2 · Oscar Renato | `orf` |
| D · Karen | `kah` |

Ejemplos reales de este semestre:

```
fix/alm-ingesta-integridad         (#126)
docs/alm-modelo-dimensional        (#128)
feat/aas-entornos-y-secretos       (#129)
docs/kh-puntos-de-quiebre          (#125)
```

## 3 · El ciclo de una rama

```bash
git switch main && git pull                     # 1 · siempre desde main actualizado
git switch -c tipo/iniciales-descripcion        # 2 · la rama
git add … && git commit -m "tipo(ámbito): …"    # 3 · commits chicos, con formato
git push -u origin tipo/iniciales-descripcion   # 4 · la primera vez
gh pr create --base main --fill                 # 5 · la solicitud, con «Closes #N»
```

6. Pides revisión a quien conoce el frente que tocas, y esperas el verde de la
   integración continua (§5).
7. **Squash and merge**, y luego **Delete branch**.
8. En tu máquina:

```bash
git switch main && git pull && git branch -d tipo/iniciales-descripcion
```

## 4 · El título

El commit y la solicitud llevan el mismo formato: `tipo(ámbito): descripción en
presente`. Los tipos son los de la tabla de arriba. Los ámbitos que de verdad se
usan en `main` son `equipo`, `infra`, `dominio`, `datos`, `analisis`, `adr`,
`mobile`, `contrato`, `repo` y `ci`.

**Dos reglas que salieron de la práctica:**

- **El título dice todo lo que trae la solicitud.** Si trae dos temas, son dos
  solicitudes. *Viene del #113 y el #114: el título describía una parte, y el
  resto entró sin que nadie lo revisara.*
- **Al integrar, el título conserva el `(#N)` que GitHub le agrega.** Sin ese
  número no se puede saber de qué solicitud vino el commit, y la auditoría lo
  cuenta como entrado sin PR. *Viene del `60dde00`.*

## 5 · La integración

- **La integración continua en verde:** sus tres trabajos son `Dominio (Java)`,
  `Datos (Python)` e `Higiene`.
- **Siempre *Squash and merge*:** un commit por tarea en `main`.
- **La rama se borra** al integrarse.
- **La revisión se pide siempre, pero no bloquea.** Se le pide a quien conoce el
  frente que toca el cambio, o a quien le afecta. El equipo trabaja en horarios
  distintos, y el avance no puede quedar esperando a que una sola persona tenga
  tiempo. Por eso la regla de GitHub no exige aprobaciones (§7).
- **Si la revisión no llega a tiempo,** quien escribió el cambio integra, y antes
  deja en la solicitud un comentario con qué comprobó y a quién le pidió revisión.
  *Así se integraron el #123, el #124 y el #126 a finales de septiembre.*
- **Si la revisión llega después de integrar,** lo que pida va en una solicitud
  nueva.
- **Si la solicitud aplica una decisión que se avisó al equipo con un plazo,** se
  integra cuando vence el plazo, no antes.

## 6 · Si `main` avanzó mientras tu solicitud estaba abierta

Usa **Update branch** en la solicitud. Hace un *merge* de `main` hacia tu rama y no
reescribe nada. Luego, en tu máquina, `git pull` en tu rama.

No uses `rebase` con `--force` en una rama que ya tiene solicitud abierta, salvo
que sólo tú trabajes en ella y sepas por qué lo haces.

## 7 · La protección de `main`

Dos capas:

- **En tu máquina**, los ganchos `pre-commit` y `pre-push` (`ciclo-de-trabajo.md`).
  Atrapan el error honesto antes de que salga, pero son una red: se pueden saltar
  con `--no-verify`.
- **En GitHub**, la regla **«main protegida.»** (*Settings → Rules → Rulesets*),
  activa sobre la rama por defecto. Ésa no se puede saltar.

Medido el 4 de octubre, la regla aplica esto:

| Regla | Qué hace |
|---|---|
| Restringir borrados | Nadie puede borrar `main` |
| Bloquear *force push* | Nadie reescribe la historia de `main` |
| Exigir solicitud | Nada entra a `main` sin PR |

**Lo que todavía no exige, aunque el convenio sí:**

| Convenio | La regla hoy |
|---|---|
| La integración continua en verde (§5) | No exige ningún *check* |
| Siempre *Squash and merge* (§5) | Permite *merge*, *squash* y *rebase* |

### Ajustes que se aplican junto con este documento

En *Settings → Rules → Rulesets → «main protegida.» → Edit*:

1. **Métodos de integración permitidos: sólo *Squash*.** Ya no se puede repetir lo
   del #55 y el #64.
2. **Checks requeridos: `Dominio (Java)`, `Datos (Python)` e `Higiene`.** La CI
   corre en toda solicitud hacia `main`, así que ninguna se queda esperando un
   *check* que nunca llega.
**Las aprobaciones no se exigen, a propósito.** Con la regla pidiendo una, el
avance quedaría atado al horario de una sola persona (§5).

## 8 · La plantilla de solicitud

`.github/pull_request_template.md` se carga sola al abrir una solicitud. Pide
cuatro cosas:

1. qué cambia;
2. qué tarea cierra (`Closes #N`);
3. cómo lo probó quien lo escribió;
4. qué tiene que revisar quien revise.

## 9 · La vista por semana del tablero

**Dónde está:** en el tablero del proyecto, la pestaña **Por semana**. Agrupa las
tarjetas por el campo `Semana` y las ordena por `Fecha límite`: abre la semana en
curso y ahí está lo que toca.

---

## Lo que no cuadraba, y cómo quedó

Medido el 4 de octubre sobre `main`, que tenía 81 commits:

| Qué | Escrito | Hecho | Cómo quedó |
|---|---|---|---|
| Iniciales de D | `kah` | `kh` en dos de sus ramas | **Se queda `kah`**, la del manual. Las dos ramas con `kh` quedan como historia |
| Ámbitos | La plantilla de PR decía `data`, `domain`, `mobile`… | Casi todos en español; `datos` (5 veces) y `data` (4) conviven | **Se usa `datos`.** La plantilla ya lista los ámbitos en uso |
| Protección de `main` | `ciclo-de-trabajo.md` decía que exigía plan de pago | Ya existe la regla «main protegida.» | **Corregido en este mismo cambio** (§7) |
| La regla de GitHub contra el convenio | CI en verde y sólo *squash* | Sin *checks* y tres métodos | **Ajustes de §7** |
| Aprobación obligatoria | El manual decía «con una aprobación» | El equipo trabaja en horarios distintos | **Revisión pedida, no obligatoria (§5).** Corregido en este mismo cambio en el README, `git-paso-a-paso.md`, `ciclo-de-trabajo.md`, `linea-base.md` y `tablero-github.md`. Los guiones de sesiones pasadas (`reunion-de-arranque.md`, `simulacion-grabada.md`) quedan como historia |
| Títulos | Todos con `tipo(ámbito):` | 13 de 81 sin ese formato, como «actividades de la semana 4 actualizadas (#122)» | Es historia; §4 se aplica en adelante |
| *Squash* | Siempre | El #55 y el #64 entraron con *merge commit*, y el `60dde00` sin solicitud | Es historia y no se reescribe; con el ajuste 1 de §7 ya no puede pasar |
| Tipos de rama | La ficha de T032 decía «tres tipos» | El manual tiene seis | Vale el manual |
