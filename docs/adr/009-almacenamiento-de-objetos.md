# ADR 009 · Qué hacemos con el almacenamiento de objetos

- **Fecha:** 19 de septiembre de 2026
- **Estado:** propuesta · se decide en la reunión de la semana 3
- **Lo descubrió:** Ari Adair (B), levantando la máquina virtual
- **Escribe la propuesta:** Ariadne (A), porque la capa bronze es del frente de datos
- **Decide:** el equipo

> **Numeración.** 006 y 007 ya están ocupados por los ADR de móvil, y 008 es el
> de dónde vive la base desplegada. A éste le toca 009.

## Contexto

MinIO archivó su edición de código abierto y dejó el proyecto como *source
only*. El paso final de eso llegó alrededor del **16 de septiembre**: borraron
los repositorios `minio/minio` y `minio/mc` de Docker Hub. Desde entonces,
cualquier máquina que no tenga una copia en caché falla así:

```
X Image minio/minio:latest  Error  pull access denied for minio/minio,
  repository does not exist or may require 'docker login'
```

No es un problema nuestro y no está solo: el mismo día se abrieron reportes
idénticos en decenas de proyectos.

**Nos pega en dos tareas a la vez.** B estaba creando la máquina virtual del
ADR 008, y T026 —la guía de arranque— exige justamente que *otro integrante
clone en máquina limpia y levante sin preguntar*. Una máquina limpia es
exactamente la que no tiene la imagen en caché.

Las otras cuatro imágenes del `docker-compose` no están rotas. Aparecen como
`Interrupted` porque Compose aborta todas las descargas cuando una falla.

### Tres hechos que enmarcan la decisión

**1 · Todavía no hemos escrito un solo byte en MinIO.** La primera tarea que lo
usa de verdad es **T020, semana 3** —*«primer guión de ingesta: descarga el
archivo y lo guarda como Parquet particionado en MinIO»*—, y no ha empezado.
Todo el perfilado, el contrato y los cinco ADR anteriores se hicieron con DuckDB
leyendo Parquet de rutas locales.

Revisando el repositorio archivo por archivo, MinIO aparece en 14 archivos y
**todos son de infraestructura o de documentación de entorno**:

| Dónde | Menciones | Qué es |
|---|---:|---|
| `docker-compose.yml` | 23 | el servicio, hoy con `image: minio/minio:latest` |
| `.env.example` | 6 | credenciales, puertos, `MINIO_BUCKET=canastamx-bronze` |
| `bootstrap.sh` · `infra/scripts/sembrar-tablero.sh` | 7 | arranque y siembra |
| `fichas/semana-01.md` · `README.md` · 4 docs de equipo | 12 | la URL de la consola y cómo entrar |
| `cronograma.md` | 2 | T007 y T020 |

**No aparece ni una sola vez** en `contracts/qqp-v1.yaml`, en `perfilado.md`, en
los dos informes de perfilado, en ningún ADR, en los guiones de perfilado, en el
servicio de dominio ni en el cliente móvil.

> **Cuidado al verificar esto.** Un `grep minio` da falsos positivos por todos
> lados, porque **«do·minio» contiene «minio»**. Hay que excluirlo.

**Consecuencia: éste es el momento más barato que vamos a tener para cambiar.**
De aquí en adelante el costo sólo sube — después de T020 hay código de ingesta
con un cliente S3, después de T043 hay una capa bronze con datos, y después de
T048 dbt lee de ahí.

**2 · El volumen es diminuto.** Medido con `medir-el-peso.py` el 19 de
septiembre:

| | filas | Parquet |
|---|---:|---:|
| Corpus completo | 21,357,873 | **97 MB** |
| Recorte territorial | 4,384,962 | 20 MB |
| Alcance del contrato | 2,658,906 | **10 MB** |

Los archivos tal cual están en disco hoy suman 127 MB. El almacenamiento de
objetos existe para terabytes repartidos en muchas máquinas; aquí no está
resolviendo un problema de escala, está cumpliendo una figura del protocolo.

**3 · La máquina destino es ARM.** El ADR 008 eligió una Ampere A1 de Oracle
—`aarch64`, 2 OCPU y 12 GB—. Cualquier imagen que se elija tiene que traer
manifiesto `arm64`, y hay que confirmarlo con `docker manifest inspect` antes
de comprometerse, no al desplegar.

## Decisión

- [ ] **A · Quedarse en MinIO, apuntando a Quay.io** ← *recomendada*
- [ ] **B · Quitar el almacenamiento de objetos y usar el sistema de archivos*
- [ ] **C · Reemplazar por otro S3 compatible**

### Qué cuesta cada una

| | Trabajo | Riesgo que queda | Qué se conserva |
|---|---|---|---|
| **A** | una línea del compose | imagen congelada, sin parches | todo |
| **B** | reescribir T020 y quitar un servicio | contradice el protocolo | nada de S3 |
| **C** | aprender un componente nuevo en semana 3 | producto joven o pesado | la API S3 |

### Por qué se recomienda A

**El objeto de investigación de este proyecto son los contratos de datos, las
compuertas de calidad y la observabilidad.** No es el almacenamiento de objetos.
Cada hora que el equipo gaste migrando de S3 es una hora que no gasta en H1 y
H2, y el equipo ya viene retrasado.

**El riesgo real, en nuestro horizonte, es casi nulo.** El semestre congela
funcionalidad el 18 de noviembre: son ocho semanas con una imagen fija que no se
va a mover. «Sin parches de seguridad» suena grave y en un servicio que corre en
una red interna, sin datos personales y durante ocho semanas, no lo es.

**Y la salida está preparada, no cerrada.** Con las dos medidas de higiene de
abajo, cambiar después cuesta una línea del compose. Es la opción que mantiene
abiertas las otras dos en lugar de cerrarlas.

### Las dos medidas de higiene, que se hacen igual gane quien gane

**Fijar la versión.** Hoy dice `image: minio/minio:latest`. **Eso es lo que nos
tronó**: `latest` apuntaba a algo que dejó de existir. Queda así, con el digest:

```yaml
minio:
  image: quay.io/minio/minio:RELEASE.2025-05-24T17-08-30Z@sha256:<digest>
```

Quay.io es un **snapshot congelado** —no habrá más versiones ahí—, así que un
`latest` en Quay tampoco significa nada. B confirma el digest y el manifiesto
`arm64` antes de subirlo.

**Renombrar las variables a algo neutral.** `MINIO_ROOT_USER` y `MINIO_BUCKET`
amarran el nombre del proveedor a la configuración de todo el proyecto. Con
nombres neutrales, cambiar de producto es una línea del compose en vez de una
búsqueda y reemplazo por todo el repositorio:

| Hoy | Queda |
|---|---|
| `MINIO_ROOT_USER` | `S3_ACCESS_KEY` |
| `MINIO_ROOT_PASSWORD` | `S3_SECRET_KEY` |
| `MINIO_BUCKET` | `S3_BUCKET` |
| `MINIO_PORT` / `MINIO_CONSOLE_PORT` | `S3_PORT` / `S3_CONSOLE_PORT` |
| *(no existe)* | `S3_ENDPOINT` |

Ese `S3_ENDPOINT` es el que hace la diferencia: **el guión de ingesta de T020
tiene que leer el endpoint de una variable, nunca escribir `minio:9000` en el
código.** Si eso se respeta, la opción C se vuelve trivial el día que haga
falta.

### Cuándo se revisa esta decisión

- Si Quay.io también retira las imágenes → se pasa a **B**, no a C. Con 127 MB,
  el sistema de archivos hace lo mismo y no hay que aprender nada.
- Si aparece una necesidad real de la API S3 —varias máquinas escribiendo, o un
  consumidor externo— → se reabre con **C**.
- **Antes de que arranque T020**, que es el punto de no retorno barato.

## Alternativas descartadas

| Alternativa | Por qué no, hoy |
|---|---|
| **SeaweedFS** (Apache-2.0) | El sustituto más sólido: más de diez años y fuerte con muchos archivos chicos. Pero es un componente nuevo que aprender en la semana en que arranca la ingesta, y no resuelve ningún problema que hoy tengamos. Es la primera opción si algún día se va a C. |
| **Garage** (AGPL-3.0) | Deliberadamente ligero y de bajo consumo, lo cual encaja con los 12 GB de la VM. En contra: ecosistema chico, menos respuestas publicadas para casos raros y sin interfaz web —y la consola de MinIO es justo lo que el equipo usa para ver que algo llegó—. |
| **RustFS** (Apache-2.0) | Se presenta como el sucesor natural y trae interfaz web. Es el más joven de todos; no queremos que el proyecto de titulación sea quien descubra sus aristas. |
| **Ceph** | El esfuerzo de operación es desproporcionado para necesitar sólo S3, y no tenemos Ceph corriendo para otra cosa. |
| **Un servicio administrado** (Hetzner, Backblaze y similares) | Cuesta dinero, mete una dependencia externa y obliga a manejar credenciales reales en un proyecto escolar cuyo repositorio se hace público al final. La regla 7 del tablero ya dice que las contraseñas no entran al repositorio. |
| **Quedarse en Docker Hub y esperar** | Las imágenes no van a volver. MinIO archivó la edición comunitaria; el borrado fue la consecuencia, no un accidente. |

## Consecuencias

### Lo que cambia en el trabajo de cada quien

**B · infraestructura, esta semana.** Fija la imagen con versión y digest,
confirma el manifiesto `arm64`, renombra las cinco variables en
`docker-compose.yml` y `.env.example`, y avisa al equipo para que actualicen su
`.env` local. **Y no cierra T026 hasta que esto esté**, porque si no va a
escribir la guía de arranque dos veces.

**A · plataforma de datos, T020 semana 3.** El guión de ingesta lee
`S3_ENDPOINT`, `S3_ACCESS_KEY` y `S3_BUCKET` del entorno. Ni una sola mención de
`minio` dentro del código.

**Todos.** Su `.env` local cambia de nombres de variables. Es copiar el
`.env.example` nuevo y volver a llenarlo.

**D · consola de observabilidad.** Si alguno de los seis indicadores iba a
mostrar el estado del almacenamiento, que lo etiquete «almacenamiento de
objetos» y no «MinIO».

### Lo que este incidente deja para el informe

Vale la pena escribirlo, porque no es relleno: **este proyecto se trata de
detectar cuándo lo que te llega se rompe.** Acabamos de vivirlo, sólo que del
lado de la infraestructura en vez del lado de los datos, y la causa raíz fue
exactamente la misma que atacamos en los datos: **una dependencia sin versión
fija**. `minio/minio:latest` es, en software, lo mismo que ingerir un archivo
sin verificar su esquema.

Eso da una línea real para las conclusiones: las compuertas de calidad no sirven
de nada si la plataforma que las ejecuta se construye sobre etiquetas móviles.

### Lo que queda abierto

- Confirmar el digest exacto y el manifiesto `arm64` del tag elegido · **B**
- Si el equipo elige B o C en vez de A, este documento se reescribe antes de
  T020, no después.

## Referencias

- [MinIO image no longer available on Docker Hub — milvus-io/milvus #53430](https://github.com/milvus-io/milvus/issues/53430)
- [minio image no longer exists on Docker Hub — shellhub-io/shellhub #7117](https://github.com/shellhub-io/shellhub/issues/7117)
- [El parche de una línea — shellhub-io/shellhub PR #7120](https://github.com/shellhub-io/shellhub/pull/7120)
- [MinIO is archived: self-hosted S3-compatible storage compared](https://wz-it.com/en/blog/minio-successor-s3-storage-comparison/)
- `docs/adr/008-donde-vive-la-base.md` — la VM Ampere y por qué importa ARM
- `docs/datos/perfilado/medir-el-peso.py` — de dónde salen los 97 MB
