# Verificación de la guía de arranque · 27 de septiembre de 2026

> **T026 · issue [#32](https://github.com/arik36/canastamx/issues/32).** Registro
> de la primera vez que alguien distinto a quien escribió la infraestructura
> intentó levantar CanastaMX siguiendo la guía.

## Resultado

**El sistema levanta y funciona**, pero **no levantaba siguiendo la guía tal como
estaba**. Hicieron falta dos correcciones al repositorio —una de ellas
bloqueante— y catorce correcciones a la guía.

Ésa es exactamente la diferencia que T026 existe para medir: no «¿arranca en la
máquina de quien lo hizo?», sino «¿alcanza el documento?».

| | |
|---|---|
| **Quién probó** | Ariadne (A), frente de datos |
| **Máquina** | Windows con WSL 2 · Ubuntu 24.04 · navegador Edge |
| **Punto de partida** | repositorio clonado y `verificar-base.sh A` en verde. **Sin Docker instalado.** |
| **Docker instalado** | Docker Desktop · motor 29.8.0 · compose v5.5.1 |
| **Primera corrida** | 35.8 s, con descarga de las seis imágenes |
| **Corridas siguientes** | 16.6 s |
| **Resultado final** | seis contenedores, bucket creado, dos bases accesibles |

> **Honestidad sobre esta prueba:** la persona que probó participó en escribir la
> guía, así que **no fue una lectura ciega**. Encontró los defectos igual —nunca
> había levantado el sistema— pero falta una prueba con alguien de Windows
> nativo que no la haya escrito. Ver el registro al final.

---

## 1 · Correcciones al repositorio · rama `fix/alm-variables-s3`

Dos cosas estaban mal en `main` y ninguna daba error al revisar el archivo a
simple vista.

### 1.1 · `minio-init` definía unas variables y leía otras · **bloqueante**

```yaml
    environment:
      MINIO_ROOT_USER:     ${S3_ROOT_USER}     ← definía MINIO_ROOT_USER
      MINIO_BUCKET:        ${S3_BUCKET}        ← definía MINIO_BUCKET
    entrypoint: >
      mc mb --ignore-existing local/$$S3_BUCKET     ← leía S3_BUCKET
```

El renombre de `MINIO_*` a `S3_*` se aplicó en el cuerpo del guión pero no en las
llaves de `environment`. Dentro del contenedor existían unos nombres y el guión
pedía otros. **Un shell no se queja de una variable que no existe: la sustituye
por nada.** Lo que se ejecutaba era, literalmente:

```
mc alias set local http://minio:9000
mc mb --ignore-existing local/
```

**Efecto observado:** `cmx-minio-init` salía con `Exited (1)` y **el bucket
`canastamx-bronze` nunca se creaba.** El sistema se reportaba sano con cinco de
seis contenedores arriba.

**Registro real del error:**

```
cmx-minio-init  | Added `local` successfully.
cmx-minio-init  | mc: <ERROR> Unable to make bucket, please use
                  `mc mb local/your-bucket-name`. Bucket name cannot be empty.
```

Nótese que **`mc alias set` aceptó sin protestar un alias con usuario y
contraseña en blanco.** Por eso el mensaje de error no habla de credenciales.

**Corregido:** en `minio-init` se renombraron también las llaves, y se agregó un
seguro para que la próxima vez falle diciendo el nombre de la variable en vez de
inventar un comando vacío:

```yaml
      mc mb --ignore-existing local/$${S3_BUCKET:?falta S3_BUCKET en el .env}
```

> En el servicio `minio` el lado izquierdo **sigue** diciendo `MINIO_ROOT_USER`
> a propósito: ese nombre lo exige el programa MinIO dentro del contenedor. Sólo
> cambió el lado derecho. La diferencia entre *el nombre que pide el programa* y
> *el nombre que elegimos nosotros* es justo lo que el ADR 009 quería separar.

### 1.2 · Los nombres no eran los que decidió el ADR 009

| En `main` | Lo que dice el ADR 009 |
|---|---|
| `S3_ROOT_USER` | `S3_ACCESS_KEY` |
| `S3_ROOT_PASSWORD` | `S3_SECRET_KEY` |
| *(no existía)* | **`S3_ENDPOINT`** |

Se le había puesto el prefijo `S3_` a los nombres viejos en vez de renombrarlos
al vocabulario de S3.

**`S3_ENDPOINT` faltaba, y eso rompía T020.** El guión de ingesta arranca
leyendo `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY` y `S3_BUCKET`, y muere si
falta alguna: de las cuatro, **tres no existían con ese nombre**.

Y el propio `.env.example` declara en su encabezado:

> *«REGLA: toda variable nueva se agrega aquí, con el valor vacío, en el mismo
> commit donde se empieza a usar.»*

La regla estaba escrita y aun así se rompió. Eso no debilita el hallazgo: lo
confirma. Las reglas escritas no se aplican solas.

**Corregido** en `docker-compose.yml` y en `.env.example`, con el comentario que
explica la diferencia entre la dirección desde tu máquina y desde dentro de la
red de compose.

---

## 2 · Hallazgos de la guía

| # | Qué pasó | Corrección |
|---|---|---|
| 1 | **`instalar/windows.md` dice «Docker: no lo necesitas»** y la guía de arranque lo exige. El documento que se nombra como requisito previo contradice al que lo nombra | La guía declara sus propios requisitos en la primera línea: Docker instalado **y corriendo** |
| 2 | Docker Desktop **pide cuenta al abrirlo** por primera vez. Parece obligatorio y no lo es | Decir: *«te va a pedir iniciar sesión; dale a `Skip`, arriba a la derecha»* |
| 3 | En WSL falta **activar la integración**. Sin eso `docker` no existe dentro de Ubuntu aunque Docker Desktop esté corriendo | Paso propio: Settings → Resources → WSL Integration → tu Ubuntu → Apply & Restart |
| 4 | La tabla de variables nombraba `S3_ACCESS_KEY`/`S3_SECRET_KEY` y el archivo tenía otros | Corregido en el repositorio; ahora coinciden |
| 5 | **`docker compose ps` nunca muestra seis contenedores.** Los que terminaron no aparecen | `docker compose ps -a`. Sin la `-a`, la comprobación de la guía es imposible de cumplir |
| 6 | La fila de `exited (1)` culpa a las credenciales; el mensaje real hablaba de un bucket vacío | Reescribir esa fila con el texto literal del error |
| 7 | **No dice qué se espera ver.** Un bucket vacío y «No existen tablas» son lo correcto y parecen fallas | Decirlo: *«vas a ver el bucket vacío y las bases sin tablas; así tiene que ser»* |
| 8 | **Las rutas `*.canastamx.localhost` fallan en silencio** si algo más ocupa el puerto 80. Docker **no da ningún error** | Fila nueva en la tabla de problemas, y cambiar el puerto por omisión — ver abajo |
| 9 | No dice cuánto tarda | **35.8 s** la primera vez, **16.6 s** después |
| 10 | No dice **cómo** editar el `.env` | En Windows, el Bloc de notas deja el archivo en una sola línea. Usar Notepad++, VS Code o `nano` desde WSL |
| 11 | Referencias internas rotas: *«ve a la sección 6»*, *«la tabla de la sección 3»* | Ya no hay secciones numeradas tras la reestructura. Enlazar por título |
| 12 | El comando de respaldo dice `docker load -i minio.tar` | Tiene que coincidir con el nombre real de los archivos del Drive |
| 13 | El clon por **SSH** no está contemplado y funciona igual | Aclarar que cómo clonaste no afecta a esto |
| 14 | *«veáse Readme.md»* | *véase* |

### El hallazgo 8, explicado, porque es el menos obvio

`http://minio.canastamx.localhost` y `http://db.canastamx.localhost` llevaban a
**la página de bienvenida de XAMPP.**

La conclusión fácil habría sido «los nombres `.localhost` no resuelven en
Windows». **Es falsa.** Se comprobó:

| Prueba | Resultado |
|---|---|
| Panel de Traefik en `localhost:8090` | funciona · 4 rutas, 5 servicios, **0 errores** |
| `TRAEFIK_WEB_PORT=8081` y abrir `minio.canastamx.localhost:8081` | **entra a la consola de MinIO** |

O sea: `.localhost` resuelve bien en Windows, Traefik enruta bien, y **el que
estorbaba era el Apache de XAMPP escuchando en el puerto 80.**

Lo importante no es XAMPP. Es que **Docker no avisó.** `docker compose ps`
mostraba `0.0.0.0:80->80/tcp` y `Up`; todo verde, sirviendo el contenido
equivocado. La tabla de problemas de la guía sí prevé el puerto 80 ocupado, pero
supone que verías `port is already allocated`. Aquí no hay error de ninguna
clase.

**Y XAMPP está instalado en media escuela**, así que esto le va a pasar a varios.

**Propuesta:** que `.env.example` traiga `TRAEFIK_WEB_PORT=8081` por omisión. El
puerto 80 se queda para la máquina virtual, que sí lo pone explícito en su
propio `.env`. Un puerto raro en la URL es mucho menos caro que una falla
silenciosa.

---

## 3 · Lo que se comprobó de paso

**Los dos repositorios de Docker Hub son públicos.** Las seis imágenes se
descargaron **sin haber iniciado sesión** en Docker Desktop. Eso cierra una de
las casillas abiertas del [ADR 012](../adr/012-de-donde-salen-las-imagenes.md).

No iniciar sesión fue deliberado: la cuenta `canastamx` es la dueña de los
repositorios y habría podido descargarlos aunque estuvieran privados. Una sesión
anónima prueba lo que hay que probar; una autenticada lo habría escondido.

**Hubo una colisión de numeración de ADR.** En el mismo `git pull` entró
`docs/adr/011-sistema-diseno-mobile.md` (C2), y el ADR de las imágenes de MinIO
—escrito el 26— también se había numerado 011.

**Resuelto así: el de móvil conserva el 011 y el de las imágenes pasa a 012.**
La regla aplicada es *el que ya está en `main` conserva el número*. El de C2 ya
estaba fusionado; el otro todavía no se había subido, así que renombrarlo sólo
cuesta ajustar tres documentos que tampoco estaban subidos.

**Y la causa vale más que el arreglo:** dos personas eligieron el mismo número
el mismo día sin saberlo, porque **el número se elige al escribir y no se reserva
en ningún lado**. Conviene una regla en la estrategia de ramas de T032:
*el número de ADR se aparta en el tablero antes de escribirlo.*

---

## 4 · Lo que queda

- [ ] Fusionar la rama `fix/alm-variables-s3`
- [ ] Aplicar los catorce hallazgos a la guía, en su rama `docs/aas-guia-de-arranque`
- [ ] Resolver la colisión de los dos ADR 012
- [ ] `TRAEFIK_WEB_PORT=8081` por omisión, si se acepta la propuesta
- [ ] **La segunda prueba**, con alguien de Windows nativo que no escribió la guía
- [ ] Correr `ingesta.py --simular` ahora que `S3_ENDPOINT` existe, para cerrar T020

---

## Registro de verificación

| Quién | Sistema | Fecha | ¿Llegó al final sin preguntar? | Qué se atoró |
|---|---|---|---|---|
| Ariadne (A) | Windows + WSL 2 · Edge | 27-09-2026 | **No** | Docker no instalado; `.env` con nombres distintos a los de la guía; `minio-init` fallaba; `ps` sin `-a`; las rutas de Traefik iban a XAMPP |
| *(por definir)* | Windows nativo | *(pendiente)* | | |

**La columna «qué se atoró» es la más útil del documento.** Cada cosa anotada
ahí es una línea que le faltaba a la guía, y es lo que hace que la siguiente
persona no se atore igual.
