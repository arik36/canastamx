# ADR 011 · De dónde salen las imágenes de MinIO

- **Fecha:** 26 de septiembre de 2026
- **Estado:** **aceptada** · ejecutada por B y verificada en las dos
  arquitecturas el 26 de septiembre
- **Autor:** Ariadne (A), a partir del reporte y la verificación de B
- **Reemplaza:** la decisión de origen del **ADR 009**. El resto del 009 —que
  seguimos con MinIO, que la salida cuesta una línea, que las variables se
  llaman `S3_*`— sigue vigente sin cambio.

> **Por qué hay un ADR nuevo y no se edita el 009.** El 009 decidió bien con la
> información que había: usar quay.io con el digest fijado. Lo que falló no fue
> la decisión sino **el supuesto de que quay.io aguantaría**. La convención del
> proyecto es corregir desde el ADR que viene, para que quede el rastro de qué
> se decidió con qué información y por qué dejó de servir.

## Contexto

El 16 de septiembre MinIO borró `minio/minio` y `minio/mc` de Docker Hub. El
ADR 009 respondió apuntando a `quay.io/minio/minio`, que era el registro oficial
del proyecto.

**El 26 de septiembre B reportó que quay.io también las quitó.** Está
confirmado fuera del equipo: varios proyectos migraron esta misma semana por lo
mismo.

| Proyecto | Qué hizo | Cita |
|---|---|---|
| **Istio** | cambió a `alpine/minio` | *«the official image was removed»* |
| **Olake** | espejo en su propio espacio de nombres | *«quay.io removed them too»* |
| **Paperplane** | cambió a `bitnamilegacy/minio` | — |

**Lo que estaba roto, y lo que no.** La máquina virtual seguía corriendo: tenía
las imágenes en caché. Lo que no funcionaba es que **cualquiera que clonara en
limpio no podía levantar el sistema**, que es el mismo problema del lunes con
otra causa.

**Lo que este episodio enseña, y que vale más que el arreglo:** dependíamos de
un registro que no controlamos, y falló dos veces en once días. Es exactamente
el riesgo que este proyecto estudia en los datos —una fuente externa que cambia
sin avisar— sólo que en la infraestructura. CanastaMX congela el corpus de
PROFECO por esa razón; no hacer lo mismo con las imágenes era incoherente.

---

## Las tres opciones que se consideraron

### Opción A · Otra imagen de un tercero

Apuntar a una imagen mantenida por alguien más que sí siga publicando:
`alpine/minio`, `bitnamilegacy/minio` o similar.

| A favor | En contra |
|---|---|
| Una línea de cambio, el mismo día | **Es el mismo riesgo otra vez.** Un tercero que no controlamos |
| No hay que crear cuentas ni subir nada | No sabemos quién la construye ni con qué |
| Es lo que escogió Istio, que es un proyecto grande | Si desaparece en noviembre, estamos igual y con menos tiempo |

### Opción B · Espejo propio  ·  **elegida**

Subir a un espacio de nombres **nuestro** las imágenes, y que el compose apunte
ahí.

| A favor | En contra |
|---|---|
| **Deja de depender de un registro ajeno**, que es el problema de fondo | Hay que subirlas |
| Son exactamente las versiones que se verificaron, no unas nuevas | Requiere cuenta y credenciales que alguien sostenga |
| Sobrevive al semestre: nadie puede borrárnoslas | Hay que armar el manifiesto de dos arquitecturas |
| Es el mismo principio que aplicamos al corpus de PROFECO | |

### Opción C · Sólo el archivo local

Que cada quien cargue las imágenes desde el `.tar` con `docker load`, sin
ningún registro.

| A favor | En contra |
|---|---|
| Cero dependencias externas | **El que clona en limpio no tiene nada.** Rompe el entregable de infraestructura reproducible |
| Ya tenemos los archivos | El `.tar` no cabe en el repositorio: la CI rechaza archivos de más de 10 MB |
| Sirve el mismo día, sin trámites | Hay que pasarlo a mano a cada persona nueva, y a la VM |

**No se descarta: queda como respaldo**, documentado en la guía de arranque. Lo
que no puede ser es el camino normal.

---

## Decisión

**Opción B**, con las siguientes concreciones:

| | |
|---|---|
| **Registro** | Docker Hub, espacio de nombres `canastamx` |
| **Imagen del servidor** | `canastamx/minio:RELEASE.2025-09-07T16-13-09Z` |
| **Imagen del cliente** | `canastamx/mc:RELEASE.2025-08-13T08-35-41Z` |
| **Arquitecturas** | `amd64` y `arm64`, bajo una sola etiqueta |
| **Respaldo** | los dos `.tar` en el Drive del equipo, con `docker load` |
| **Dueño** | B, como responsable del frente de infraestructura |

### Por qué Docker Hub y no GHCR

La propuesta original de este ADR recomendaba GitHub Container Registry, con el
argumento de que no hacía falta cuenta nueva. **B, que es quien ejecuta y
sostiene esto, eligió Docker Hub.** Se respeta: es su frente, y la diferencia
entre los dos registros no cambia nada del sistema.

Queda anotada la contra conocida: **Docker Hub limita las descargas anónimas.**
En un equipo de cinco personas y una VM no se alcanza el límite, y si algún día
estorbara, el `.tar` del Drive cubre el caso. No es un riesgo que valga un
cambio de registro.

**La contraseña de la cuenta va en el gestor del equipo, nunca en el
repositorio** (regla 7 del tablero).

### Por qué no se fijó el digest

El ADR 009 pidió fijar la imagen **con su digest**
(`…@sha256:<digest>`), no sólo con la etiqueta. **B decidió no hacerlo.** Se
respeta y se explica, porque deshacer una decisión de un ADR aceptado sin
escribir por qué es peor que la decisión misma.

El argumento del 009 era bueno **en su contexto**: la etiqueta vivía en un
registro ajeno, y quien manda en ese registro puede reapuntarla a otra cosa sin
que nadie se entere. El digest era la defensa contra eso.

Ese contexto ya no existe:

| El 009 suponía | Hoy |
|---|---|
| La etiqueta vive en un registro ajeno | Vive en un espacio de nombres **nuestro** |
| Cualquiera podría reapuntarla | Sólo podemos nosotros, con nuestras credenciales |
| No sabíamos qué traía dentro | **Están registradas las cuatro sumas de los binarios** |

Y esa última fila es la que de verdad resuelve el problema: un digest garantiza
que la imagen sea *la misma de siempre*; la tabla de sumas garantiza que su
contenido sea *el que MinIO publicó*, que es la pregunta que importaba. Es una
garantía más fuerte y, además, legible por una persona.

En contra, y es real: **el digest también protege de nosotros mismos.** Si
alguien republica esa etiqueta por error, el compose seguiría a lo nuevo sin
avisar. El riesgo es chico —somos cinco y una sola cuenta— pero no es cero, así
que queda una regla en su lugar:

> **Si alguna vez se vuelve a publicar cualquiera de las dos etiquetas, se
> repiten las cuatro sumas y se actualiza la tabla de verificación de este
> documento.** Publicar sin volver a medir deja el ADR mintiendo.

**Lo que no cambia** es el fondo del 009: la causa raíz fue `latest`, una
etiqueta móvil. `RELEASE.2025-09-07T16-13-09Z` no se mueve. La lección se
respeta.

---

## El disparador del ADR 009 se activó y no se siguió

Esto hay que decirlo antes que nada, porque es lo más delicado del documento.

El ADR 009 dejó escrita, **de antemano**, una regla para este escenario exacto:

> *«Si Quay.io también retira las imágenes → se pasa a **B**, no a C. Con 127 MB,
> el sistema de archivos hace lo mismo y no hay que aprender nada.»*

**Quay.io retiró las imágenes. La regla se activó. No se siguió.**

Esto no es un detalle de trámite: es precisamente lo que este proyecto critica
cuando pasa del lado de los datos. Declarar un criterio antes de ver el
resultado y después ignorarlo porque no gustó es lo que la disciplina del
ADR 004 existe para impedir. Así que o se justifica por escrito, o se sigue.

**Se justifica, y la razón es que la regla resolvía un problema que no ocurrió.**
Lo que el 009 temía era quedarse **sin poder obtener MinIO**, y por eso proponía
abandonarlo y usar el sistema de archivos. Pero montar un espejo devolvió la
disponibilidad en una tarde y sin cambiar nada del sistema — un camino que el
009 no consideró, porque cuando se escribió nadie había pensado en que las
imágenes podían guardarse en otro lado.

Cambiar a la opción B habría significado, con el problema ya resuelto:

| | |
|---|---|
| Tirar el servicio de almacenamiento y su consola | que es lo que el equipo usa para ver que algo llegó |
| Reescribir el guión de ingesta de T020 | que ya está escrito contra S3 |
| Rehacer la guía de arranque y el `.env` | por segunda vez en una semana |
| Cerrar la salida a un proveedor S3 real | que el 009 quería mantener abierta |

Es decir: aplicar la regla al pie de la letra habría costado más que el problema
que pretendía evitar.

**Lo que se aprende, y vale para el informe:** una regla escrita de antemano se
respeta, pero puede quedar obsoleta cuando aparece una opción que su autor no
tenía a la vista. Lo que no se vale es saltársela en silencio. La diferencia
entre desviarse y hacer trampa es exactamente este apartado.

---

## Verificación · de dónde salen realmente esos binarios

Ésta es la parte que vale para el informe, y la razón por la que este ADR no se
cerró el mismo día que se decidió.

Las imágenes se armaron a partir de una imagen de un tercero (`wolff06/minio`).
Eso por sí solo no vale nada: cualquiera puede publicar una imagen y llamarla
MinIO. Lo que la hace utilizable es haber comparado **los binarios que trae
dentro** contra los que publica MinIO en su canal de lanzamientos, y que
coincidan byte por byte.

### Las cuatro sumas

| Binario | Arquitectura | SHA-256 | Medido en | Comparado contra |
|---|---|---|---|---|
| `minio` | `amd64` | `7c5bd851…65fb855f` | `canastamx/minio` | binario oficial `linux-amd64` |
| `mc` | `amd64` | `01f866e9…0312e891` | `canastamx/mc` | binario oficial `linux-amd64` |
| `minio` | `arm64` | `5c83cd2c…4fd6f03d` | `canastamx/minio` | `minio.linux-arm64.…sha256sum` oficial |
| `mc` | `arm64` | `14c8c961…4c27c12c` | `canastamx/mc` | `mc.linux-arm64.…sha256sum` oficial |

**Las cuatro coincidieron, y las cuatro están medidas sobre la imagen
publicada**, no sobre la de origen. Esa distinción parece pedante y no lo es:
medir el origen prueba que el origen era bueno, no que lo que subimos sea lo
mismo. Las dos de `amd64` se repitieron sobre `canastamx/` por esa razón, y
dieron idéntico.

De paso quedó comprobado algo que no se buscaba: el `mc` de la imagen
`canastamx/mc` y el que viene dentro de `canastamx/minio` son **el mismo
binario**, porque la suma de `amd64` se midió una vez en cada uno y coincidió.

### Que la etiqueta trae las dos arquitecturas

Una etiqueta como `…:RELEASE.2025-09-07T16-13-09Z` no es un archivo: es una
**lista de manifiestos** que apunta a una imagen por arquitectura. Si se sube
una arquitectura y luego la otra con `docker push` a secas, **la segunda pisa a
la primera** y la etiqueta acaba sirviendo a una sola. El sistema entonces
levanta en la VM y no levanta en ninguna laptop, y no se nota hasta que alguien
clona en limpio.

Comprobado el 26 de septiembre:

```bash
docker manifest inspect canastamx/minio:RELEASE.2025-09-07T16-13-09Z | grep -E '"architecture"'
    "architecture": "amd64",
    "architecture": "arm64"

docker manifest inspect canastamx/mc:RELEASE.2025-08-13T08-35-41Z | grep -E '"architecture"'
    "architecture": "amd64",
    "architecture": "arm64"
```

La `arm64` importa más que la otra: **la máquina virtual de Oracle es Ampere
A1**, y es el único entorno desplegado.

### Qué prueba esto, y qué no

**Prueba** que los dos binarios que el sistema ejecuta son exactamente los que
MinIO publicó. Eso es lo que permite escribir en el informe que el espejo
contiene los binarios oficiales, sin asterisco.

**No prueba** que el resto de la imagen esté limpio: las capas base, el
`entrypoint`, los certificados. Eso no se verificó y no se afirma. Para el
alcance de este proyecto es aceptable; queda escrito para que nadie lo lea como
más de lo que es.

**Si se quisiera cerrar también esa parte**, el camino está a la mano y no es
caro: construir la imagen nosotros con un `Dockerfile` de cinco líneas que copie
el binario ya verificado sobre una base conocida. B tiene en su máquina los
binarios oficiales de las dos arquitecturas con sus sumas, que es todo lo que
haría falta. Se deja anotado como mejora posible, no como pendiente.

---

## Una simplificación que se consideró y no se tomó

`mc` **viene dentro de la imagen de `minio`**: lo mostró la propia verificación,
y el `healthcheck` del compose ya dependía de ello sin que nadie lo hubiera
notado (ejecuta `mc ready local` dentro del contenedor de minio). El hash de ese
`mc` es el de `RELEASE.2025-08-13T08-35-41Z`, la misma versión que se publicó
aparte.

Es decir: **`minio-init` podría usar la misma imagen que `minio`**, y el espejo
sería de un solo repositorio en vez de dos.

Se dejaron las dos. Dos imágenes es lo que hacía el proyecto original, mantiene
las versiones independientes y es lo que ya estaba subido cuando se notó. Queda
escrito aquí para que no se vuelva a discutir desde cero: **las dos formas
funcionan**, y si algún día mantener dos repositorios estorba, unificarlos es un
cambio de una línea.

---

## Qué cambia, y qué NO cambia

### Cambia

| Archivo | Qué |
|---|---|
| `docker-compose.yml` | **dos líneas**: de dónde sale cada imagen |
| `.env.example` | el renombre a `S3_*`, que ya estaba planeado (ADR 009) |
| `README.md` | la guía de arranque: el apartado de respaldo y la nota del espejo |
| `docs/adr/` | este documento |

```yaml
  minio:
    image: canastamx/minio:RELEASE.2025-09-07T16-13-09Z

  minio-init:
    image: canastamx/mc:RELEASE.2025-08-13T08-35-41Z
```

### No cambia

| | |
|---|---|
| **El dominio** | `canastamx.localhost` y las rutas de Traefik se quedan igual |
| **Los puertos** | 9000 y 9001, sin cambio |
| **El bucket y los datos** | `canastamx-bronze` y su contenido, intactos |
| **El código** | ni el servicio de dominio, ni la interfaz analítica, ni los clientes |
| **El guión de ingesta** | lee `S3_ENDPOINT` y le da igual de dónde salió la imagen |
| **La máquina virtual** | sigue corriendo; sólo cambia de dónde descarga |
| **Las versiones** | son las verificadas, no unas nuevas |

**El radio de afectación son dos líneas en un archivo.** Lo que cambia es el
nombre del lugar del que se descarga el programa, no el programa, ni cómo se
configura, ni con quién habla.

---

## Lo que falta para dar esto por cerrado

- [x] ~~Las dos sumas de `amd64` medidas sobre `canastamx/`~~ · hecho el 26 de
      septiembre; la tabla de verificación está completa
- [ ] Los dos repositorios de Docker Hub en **público** — si quedan privados, el
      arranque en limpio pide credenciales y se rompe
- [ ] Los dos `.tar` creados y subidos al Drive del equipo, con las líneas de
      `docker load` en la guía de arranque:

      ```bash
      docker save canastamx/minio:RELEASE.2025-09-07T16-13-09Z \
        -o canastamx-minio-RELEASE.2025-09-07T16-13-09Z-amd64.tar
      docker save canastamx/mc:RELEASE.2025-08-13T08-35-41Z \
        -o canastamx-mc-RELEASE.2025-08-13T08-35-41Z-amd64.tar
      ```

      **La arquitectura va en el nombre a propósito:** `docker save` guarda sólo
      la de la máquina donde se corre, no la etiqueta completa. Hechos en la
      laptop de B salen `amd64`, que es lo que necesitan los otros cuatro. La VM
      es `arm64` y no los necesita. Si pesan demasiado para el Drive,
      `docker save … | gzip > archivo.tar.gz`: `docker load -i` los lee
      comprimidos.
- [ ] `docker compose down -v` → `docker image rm` → `docker compose up -d` en la
      VM
- [ ] **Que alguien más lo levante en su máquina**, que es el criterio de T026
- [ ] El pull request con las dos líneas del compose y el renombre `MINIO_*` → `S3_*`

---

## Consecuencias por frente

**B · infraestructura.** Dueño del espacio de nombres `canastamx` en Docker Hub
y de las dos imágenes. Agrega a la guía de arranque el apartado de respaldo con
`docker load` y la ubicación de los `.tar`. Si alguna vez hay que republicar,
el procedimiento y las sumas están en este documento.

**A · datos.** Ninguna. El guión de ingesta de T020 lee `S3_ENDPOINT` y no sabe
ni le importa de qué registro salió el contenedor.

**C1, C2, D.** Ninguna, más allá de hacer `git pull` y actualizar su `.env`
cuando se fusione el pull request.

**Para el informe.** Este episodio es material aprovechable y conviene no
desperdiciarlo: una dependencia externa que cambió dos veces en once días, y la
decisión de dejar de depender de ella. Es el mismo argumento que sostiene
congelar el corpus de PROFECO, aplicado a la infraestructura — y la tabla de las
cuatro sumas es la evidencia de que el espejo contiene lo que dice contener, que
es exactamente el tipo de comprobación que este proyecto defiende para los datos.
Vale un apartado, no un párrafo.

---

## Lo que esta decisión deja abierto

**Que nosotros mismos pisemos la etiqueta.** Sin digest fijado, republicar
cualquiera de las dos etiquetas cambiaría lo que descarga todo el equipo sin que
nadie lo note. La regla está escrita arriba —republicar obliga a volver a medir
las cuatro sumas— pero es una regla, no un candado. Si alguna vez el equipo
crece, ahí es donde conviene volver a poner el digest.

**Cuánto dura el espejo.** Docker Hub es gratis para imágenes públicas hoy. No
hay compromiso de que lo siga siendo, y ya limita las descargas anónimas. El
`.tar` en el Drive cubre ese caso y por eso no se retira nunca.

**Quién sostiene la cuenta.** Si la cuenta se pierde, se pierden las imágenes.
La contraseña va en el gestor del equipo y B no es el único que debe poder
entrar.

**La imagen más allá de los binarios.** Explicado arriba: verificado el
contenido que se ejecuta, no verificadas las capas base. El camino para cerrarlo
está descrito.

## Cerrado por este ADR

**Si `mc` existe para `arm64`.** La propuesta de este documento lo dejaba como
el único riesgo real del plan, porque la etiqueta `-cpuv1` del origen anterior
era una variante de x86. **Existe**, se descargó, se verificó contra su suma
oficial y está publicada en `canastamx/mc`. El pendiente se cierra.

## Referencias

- `docs/adr/009-almacenamiento-de-objetos.md` — la decisión que este ADR
  reemplaza en su parte de origen
- istio/release-builder#2441 — migración a `alpine/minio`
- datazip-inc/olake#1255 — espejo propio, con verificación de sumas
- aquaproj/aqua-registry#60567 — repunte a los lanzamientos de GitHub, que
  publican el binario junto con su suma y su firma