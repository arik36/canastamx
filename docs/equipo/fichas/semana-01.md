# Fichas de tarea · Semana 1

**Del lunes 7 al viernes 11 de septiembre de 2026.** Dieciocho tareas, cinco personas.

Una ficha por tarea. Léela completa **antes** de empezar, no a media tarea. Los siete apartados están en el mismo orden siempre:

| Apartado | Para qué |
|---|---|
| **Qué entregas** | El artefacto concreto, con su ruta exacta |
| **Antes de empezar, verifica** | Lo que tiene que existir ya. Si algo falta, avisa en vez de esperar |
| **Depende de · Bloquea a** | A quién le avisas cuando termines |
| **Lo que necesitas saber** | Los conceptos, explicados aquí. No hay que buscarlos afuera |
| **Paso a paso** | Comandos y acciones reales, para copiar |
| **Cómo se ve terminado** | El esqueleto del archivo o la señal de que quedó |
| **Errores frecuentes** | Los que te vas a encontrar, con su salida |

> **Regla de arranque.** Si el apartado «antes de empezar» tiene una casilla que no puedes marcar, **no empieces y avisa en el chat**. Trabajar sobre un insumo que no existe produce trabajo que hay que tirar, y en un equipo remoto nadie se entera hasta la reunión.

> **La regla de las 24 horas sigue vigente.** Si llevas un día atorado en la misma cosa, abres un issue con etiqueta `bloqueo` y lo dices. No es debilidad, es el procedimiento.

---

# Lunes 7 de septiembre

Siete tareas. El día que desbloquea a todos.

**Orden de prioridad de A**, porque tres de sus tareas bloquean a los demás y conviene saber qué se sacrifica si algo se cae: primero subir el paquete y cerrar la estructura *(desbloquea a los cuatro)*, luego localizar y descargar el archivo *(desbloquea a C2)*, y al final el perfilado nivel 1 *(no bloquea a nadie; puede caerse al martes)*.

---

## T001 · A · Cerrar la estructura del repositorio

**Tiempo estimado:** 60 a 90 minutos · **Prioridad del día: 1 de 3**

### Qué entregas

El repositorio `arik36/canastamx` con:

- La estructura de carpetas del monorepo, cada carpeta vacía con un `.gitkeep` dentro
- `.gitignore`, `README.md` inicial y `.env.example`
- Los cuatro integrantes invitados como colaboradores, **y aceptados**
- La rama `main` protegida
- El tablero de GitHub Projects creado con sus cinco columnas
- El paquete del manual de equipo incorporado a `main`

### Antes de empezar, verifica

- [ ] Tienes el nombre de usuario de GitHub de los otros cuatro. **Si no lo tienes, pídelo en el chat ahora mismo**: es lo único de esta tarea que depende de otras personas y puede tardar horas.
- [ ] Tienes el repositorio clonado y `git status` responde limpio.
- [ ] Tienes a la mano el paquete `CanastaMX_paquete_equipo.zip`.

### Depende de · Bloquea a

**Depende de:** nada. Es el arranque.
**Bloquea a:** T007 (B, docker-compose), T011 (C1, Spring), T014 (C2, Expo), T015 (D, inventario). Los cuatro necesitan que exista la carpeta donde va lo suyo.

**Cuando termines, escribe en el chat:** *«Estructura arriba, ya pueden clonar. Acepten la invitación de colaborador.»*

### Lo que necesitas saber

**Por qué las carpetas van vacías con un `.gitkeep` adentro.** Git no versiona carpetas, solo archivos. Una carpeta vacía no existe para Git y no se sube. El `.gitkeep` es un archivo vacío, sin significado especial —el nombre es pura convención— cuyo único trabajo es hacer que la carpeta tenga contenido y por lo tanto exista en el repositorio.

**Por qué se crea la estructura completa antes de que haya código.** Porque la pregunta «¿dónde pongo esto?» ya tiene respuesta antes de que alguien la haga. Reorganizar un monorepo en octubre, con cuatro personas trabajando en ramas distintas, produce conflictos en cada archivo movido.

**Qué es proteger `main`.** Una regla del lado del servidor que impide escribir directo en la rama principal. Sin ella, el acuerdo de «nadie escribe en main» es verbal, y alguien lo va a romper sin querer un martes a las once de la noche.

### Paso a paso

**1. Crea la estructura.** El paquete trae `infra/scripts/crear-estructura.sh`, que hace esto solo:

```bash
cd ruta/donde/clonaste/canastamx
git switch main && git pull
git switch -c chore/alm-estructura-inicial
bash infra/scripts/crear-estructura.sh
git status          # revisa la lista antes de agregar nada
```

**2. Copia el paquete.** Descomprime el zip y copia el contenido de `entrega/` sobre la raíz del repositorio. Se agregan `docs/equipo/`, `.github/` e `infra/scripts/`.

**3. Sube.**

```bash
git add .
git commit -m "chore(repo): estructura del monorepo y manual de equipo"
git push -u origin chore/alm-estructura-inicial
```

Abre la solicitud con el enlace que imprime el `push` e incorpórala. Esta primera vez puedes aprobarla tú misma: la rama `main` todavía no está protegida y no hay nadie más adentro.

**4. Invita a los colaboradores.** Settings → Collaborators → Add people. Uno por uno, con su usuario de GitHub. **Confirma que los cuatro aceptaron** antes de mandar el enlace del panel: una invitación sin aceptar se ve igual que un repositorio que no existe.

**5. Protege `main` — etapa 1.** Settings → Branches → Add branch protection rule.

- Branch name pattern: `main`
- ☑ Require a pull request before merging
- ☑ Require approvals: **1**
- ☐ Require status checks — **déjala apagada por ahora**
- ☑ Do not allow bypassing the above settings

La casilla de verificaciones se queda apagada porque **GitHub solo deja seleccionar canalizaciones que ya corrieron alguna vez**, y hoy no ha corrido ninguna. La lista está vacía. La etapa 2 la hace B el miércoles, al cerrar T009, cuando su canalización ya salió verde.

Con la etapa 1 ya nadie escribe directo en `main`, que es el 90% del valor.

**6. Crea el tablero.** Projects → New project → plantilla **Board**. Nombre `CanastaMX — Semestre 2026-2`. Las cinco columnas y los campos personalizados están en `docs/equipo/tablero-github.md`, parte 1.

**7. Siembra los issues.**

```bash
# abre el archivo y llena los usuarios de GitHub en el bloque de arriba
bash infra/scripts/sembrar-tablero.sh --simular   # revisa qué haría
bash infra/scripts/sembrar-tablero.sh             # créalos de verdad
```

Requiere `gh` de https://cli.github.com y `gh auth login`.

### Cómo se ve terminado

```
canastamx/
├─ README.md  .gitignore  .env.example  docker-compose.yml
├─ .github/workflows/  .github/ISSUE_TEMPLATE/
├─ docs/
│  ├─ adr/  analisis/  datos/  experimento/  entregas/
│  └─ equipo/          ← el manual, ya con contenido
├─ contracts/
├─ services/data-platform/  analytics-api/  domain-service/
├─ clients/web/  mobile/
├─ packages/types/
└─ infra/traefik/  envs/  scripts/
```

La prueba real: **otro integrante clona y ve exactamente esto.** Pídeselo a B por chat antes de dar la tarea por cerrada.

La lista completa de lo que tiene que estar antes de que alguien ramifique está en [`docs/equipo/linea-base.md`](../linea-base.md). Cuando termines, cada quien corre `bash infra/scripts/verificar-base.sh` y ve si su copia está completa.

### Errores frecuentes

| Qué pasa | Por qué | Salida |
|---|---|---|
| Las carpetas vacías no aparecen tras el push | Git no versiona carpetas | Verifica que cada una tenga su `.gitkeep`: `find . -type d -empty` |
| «Permission denied» a un integrante | No aceptó la invitación, o la mandaste al usuario equivocado | Settings → Collaborators, revisa si dice *Pending invite* |
| Se subió `.env` con datos reales | No estaba en `.gitignore` todavía | Detente, avisa a B. Borrarlo en un commit nuevo no sirve: sigue en el historial |
| El script de siembra crea issues duplicados | Se corrió dos veces | No es reversible en masa. Cierra los duplicados a mano y no lo vuelvas a correr |

---

## T002 · A · Localizar y descargar la fuente QQP

**Tiempo estimado:** 45 a 90 minutos, según lo que pese el archivo · **Prioridad del día: 2 de 3**

### Qué entregas

`docs/datos/fuente-qqp.md` con la ficha técnica de los archivos descargados, y los archivos en tu disco —**no en el repositorio**—.

### Antes de empezar, verifica

- [ ] Tienes al menos 10 GB libres en disco. El conjunto puede ser grande y vas a conservar el crudo.
- [ ] Tienes conexión estable. Una descarga interrumpida a la mitad produce un archivo corrupto que parece bueno.

### Depende de · Bloquea a

**Depende de:** nada.
**Bloquea a:** T003, T004, T005 (tus propios perfilados) y **T013 (C2, diccionario de datos)**.

**Avisa a C2 en cuanto tengas el enlace, sin esperar a que termine la descarga.** Él necesita la URL del diccionario, no el archivo. Si no le avisas, va a buscar por su cuenta, va a encontrar otra versión del conjunto y va a documentar columnas que no son las que tú descargaste.

### Lo que necesitas saber

**QQP** es *Quién es Quién en los Precios*, el programa de monitoreo de precios de PROFECO. Publica precios levantados en establecimientos seleccionados de varias ciudades.

Cuatro puntos de entrada, y sirven para cosas distintas:

| Dónde | Para qué |
|---|---|
| `datos.profeco.gob.mx/datos_abiertos/` | El portal de datos abiertos. Aquí están los archivos |
| `datos.profeco.gob.mx/diccionarioDatosQQP.php` | **El diccionario de datos.** Este enlace es el que le pasas a C2 |
| `datos.gob.mx/dataset/programa_quien_es_quien_precios_2025` | El conjunto de 2025 en el portal federal. Cambia el año en la URL para otros |
| `qqp.profeco.gob.mx` | La aplicación pública de consulta. **No es para descargar**: sirve para contrastar contra tus datos |

**No supongas el esquema.** Esta tarea y las tres de perfilado existen precisamente porque no se sabe qué trae el archivo. Todo lo que escribas aquí se mide, no se asume: si el diccionario dice que una columna es numérica y viene con texto, ese es exactamente el hallazgo que justifica el proyecto entero.

### Paso a paso

1. Entra al portal de datos abiertos y localiza el conjunto de QQP.
2. Descarga **el archivo más reciente disponible** y **el de 2025** completo. Dos archivos: uno para trabajar y otro para tener serie histórica.
3. Guárdalos fuera del repositorio. Sugerencia: `~/canastamx-datos/crudo/`.
4. Verifica que abren de verdad. **No con Excel** (ver errores frecuentes). Con la terminal:

```bash
ls -lh ~/canastamx-datos/crudo/            # tamaño real
head -3 archivo.csv                        # primeras filas y encabezado
wc -l archivo.csv                          # cuántas filas
file archivo.csv                           # formato y codificación
```

5. Anota todo en `docs/datos/fuente-qqp.md`. La plantilla ya está en el repositorio.
6. Copia el enlace del diccionario y pásaselo a C2 por el chat.

### Cómo se ve terminado

`docs/datos/fuente-qqp.md` con la tabla llena:

| Archivo | Periodo | Tamaño | Formato | Codificación | Separador | Filas | URL |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

Más una nota de una línea por cada cosa rara que hayas notado al abrirlo. Esas notas son el inicio del perfilado.

### Errores frecuentes

| Qué pasa | Por qué | Salida |
|---|---|---|
| **Excel muestra menos filas de las que hay** | Excel corta en 1,048,576 filas **sin avisar** | Nunca uses Excel para verificar. Usa `wc -l` o pandas. Este error solo te enteras cuando ya construiste encima |
| Acentos rotos: `Frijol` aparece como `Frï¿½jol` | El archivo no es UTF-8, probablemente latin-1 | `file archivo.csv` te dice la codificación. Anótala; el guión de ingesta va a necesitarla |
| El archivo abre pero está a la mitad | Descarga interrumpida | Compara el tamaño contra el que anuncia el portal. Descarga otra vez |
| Se te ocurre subir el CSV al repositorio | Pesa cientos de megas | **No.** Al repositorio va solo una muestra de mil filas, en la semana 2 |

---

## T003 · A · Perfilado nivel 1

**Tiempo estimado:** 90 minutos · **Prioridad del día: 3 de 3** — si se cae al martes, no bloquea a nadie

### Qué entregas

Un cuaderno de análisis en `docs/datos/perfilado/` con la sección de estructura llena: filas, columnas, tipos reales, nulos, rango de fechas y entidades federativas presentes.

### Antes de empezar, verifica

- [ ] T002 terminada: los archivos están en disco y abren.
- [ ] Tienes Python 3.12 y pandas. Si no: `pip install pandas pyarrow jupyter`.

### Depende de · Bloquea a

**Depende de:** T002.
**Bloquea a:** T004 (perfilado nivel 2), y por la cadena, a T005 y T006.

### Lo que necesitas saber

**Perfilar** es medir la forma y la salud de un conjunto de datos antes de construir nada encima. No es análisis: no busca respuestas de negocio, busca sorpresas.

Los tres niveles del perfilado responden preguntas distintas, y por eso están separados:

| Nivel | Pregunta | Cuándo |
|---|---|---|
| **1 · Estructura** | ¿Qué hay? ¿Cuántas filas, qué columnas, de qué tipo, qué tan completas? | Hoy |
| **2 · Rangos y anomalías** | ¿Los valores son plausibles? ¿Hay ceros, negativos, absurdos, duplicados? | Martes |
| **3 · Variantes de escritura** | ¿El mismo producto se escribe igual entre cadenas? | Miércoles |

**Tipo declarado contra tipo real.** El diccionario puede decir que `precio` es numérico y venir con `"$24.50"` o con celdas vacías. Pandas lo va a leer como texto. Esa diferencia es un hallazgo, y es exactamente la clase de cosa contra la que el contrato de datos de la semana 2 va a proteger.

**Lee por partes.** Un archivo de millones de filas puede no caber en memoria. `pd.read_csv(..., chunksize=500_000)` lo procesa por bloques.

### Paso a paso

```python
import pandas as pd

RUTA = "~/canastamx-datos/crudo/archivo.csv"

# 1. Asómate primero: mil filas para ver la forma sin cargar todo
m = pd.read_csv(RUTA, nrows=1000, encoding="latin-1")   # ajusta la codificación
print(m.dtypes)
print(m.head(20))

# 2. Ahora sí, completo (o por bloques si no cabe)
df = pd.read_csv(RUTA, encoding="latin-1", low_memory=False)

# 3. Volumen
print(f"{len(df):,} filas × {len(df.columns)} columnas")

# 4. Tipo real y nulos por columna
resumen = pd.DataFrame({
    "tipo_real":  df.dtypes.astype(str),
    "nulos":      df.isna().sum(),
    "pct_nulos":  (df.isna().mean() * 100).round(2),
    "distintos":  df.nunique(),
    "ejemplo":    [df[c].dropna().iloc[0] if df[c].notna().any() else None
                   for c in df.columns],
})
print(resumen)

# 5. Rango de fechas — cambia el nombre de la columna por el real
f = pd.to_datetime(df["fechaRegistro"], errors="coerce")
print("Desde", f.min(), "hasta", f.max())
print("Fechas que no se pudieron leer:", f.isna().sum())

# 6. Entidades federativas
print(df["estado"].value_counts())
```

Guarda el cuaderno o el script en `docs/datos/perfilado/` y pega la tabla de resultados en `docs/datos/perfilado.md`, que ya tiene la plantilla.

### Cómo se ve terminado

La sección 1 de `docs/datos/perfilado.md` con esta tabla llena y **sin celdas vacías**:

| Columna | Tipo declarado | Tipo real | % nulos | Valores distintos | Ejemplo |
|---|---|---|---|---|---|

Más tres cifras al inicio: total de filas, rango de fechas, número de entidades federativas.

### Errores frecuentes

| Qué pasa | Por qué | Salida |
|---|---|---|
| `UnicodeDecodeError` | La codificación no es UTF-8 | Prueba `encoding="latin-1"` y anótalo en la ficha de la fuente |
| `MemoryError` o la laptop se congela | El archivo no cabe en RAM | `chunksize=500_000` y agrega los resultados por bloque |
| Todas las columnas salen `object` | Vienen con símbolos, comas de miles o espacios | Es un hallazgo, no un problema tuyo. Anótalo: justifica el contrato de datos |
| El % de nulos sale 0 en todo | Los faltantes vienen como `""`, `"NA"` o `"-"`, no como vacío real | `pd.read_csv(..., na_values=["", "NA", "-", "N/A", "null"])` |

---

## T007 · B · docker-compose con los cuatro servicios base

**Tiempo estimado:** 2 a 3 horas

### Qué entregas

`docker-compose.yml` en la raíz, con cuatro servicios que levantan con un solo comando: `postgres-oltp`, `postgres-analytics`, `minio` y `adminer`.

### Antes de empezar, verifica

- [ ] **T001 terminada**: puedes clonar y ves la estructura de carpetas.
- [ ] Docker Desktop instalado y corriendo. `docker --version` y `docker compose version` responden.
- [ ] En Windows: WSL2 habilitado. Docker Desktop no funciona bien sin él.

### Depende de · Bloquea a

**Depende de:** T001.
**Bloquea a:** T008 (Traefik, tuya) y, en la semana 2, a todo lo de A: sin base de datos no hay dónde escribir.

**Cuando termines, escribe en el chat:** *«Compose arriba. Clonen, corran `docker compose up -d` y díganme si les levanta.»* Necesitas que al menos otra persona lo confirme.

### Lo que necesitas saber

**Por qué dos instancias de Postgres y no una con dos esquemas.** El protocolo lo justifica: aísla los datos de usuario del flujo analítico, y ninguna consulta analítica toca la base transaccional. Una consulta pesada de A sobre millones de filas no puede degradar el inicio de sesión que hace C1.

**Qué hace cada servicio:**

| Servicio | Qué es | Para quién |
|---|---|---|
| `postgres-oltp` | Base transaccional. Usuarios, canastas, alertas | C1 |
| `postgres-analytics` | Almacén analítico. Capas intermedia, de consumo y cuarentena | A |
| `minio` | Almacenamiento de objetos compatible con S3. Guarda el crudo en Parquet | A |
| `adminer` | Cliente web de base de datos. Para asomarse sin instalar nada | Todos |

**`healthcheck` no es adorno.** Sin él, `docker compose up` reporta «arriba» en cuanto el contenedor arranca, aunque Postgres todavía esté inicializando y rechace conexiones. Con `healthcheck` más `depends_on: condition: service_healthy`, el orden de arranque se respeta de verdad.

**Los puertos de tu máquina son un recurso escaso.** Si ya tienes un Postgres instalado, el 5432 está ocupado y el contenedor no levanta. Por eso las dos instancias se publican en puertos distintos.

### Paso a paso

1. Copia la plantilla comentada que está en el repositorio como `docker-compose.yml`.
2. Crea tu `.env` local a partir de `.env.example` y pon contraseñas de desarrollo. **El `.env` nunca se sube.**
3. Levanta:

```bash
docker compose up -d
docker compose ps        # los cuatro deben decir "running" y, los que tienen, "healthy"
```

4. Verifica cada uno:

```bash
docker compose exec postgres-oltp       pg_isready -U canastamx
docker compose exec postgres-analytics  pg_isready -U canastamx
```

- MinIO: `http://localhost:9001` — entra con las credenciales del `.env`
- Adminer: `http://localhost:8080` — servidor `postgres-oltp`, usuario y base del `.env`

5. Prueba el reinicio limpio, que es lo que va a hacer otra persona:

```bash
docker compose down -v && docker compose up -d
```

### Cómo se ve terminado

`docker compose ps` muestra cuatro contenedores en `running`, los dos Postgres en `healthy`, y las dos interfaces web abren. **En la máquina de alguien más, no solo en la tuya.**

### Errores frecuentes

| Qué pasa | Por qué | Salida |
|---|---|---|
| `port is already allocated` | Ya hay algo en ese puerto | `lsof -i :5432` (Mac/Linux) o `netstat -ano \| findstr :5432` (Windows). Cambia el puerto publicado en el compose |
| Postgres arranca y se apaga solo | Faltan variables de entorno, o el volumen trae datos de otra versión | `docker compose logs postgres-oltp`. Si es el volumen: `docker compose down -v` borra los datos y vuelve a empezar |
| `database files are incompatible with server` | El volumen se creó con otra versión de Postgres | `docker compose down -v` |
| MinIO abre pero no deja entrar | Las credenciales del `.env` no coinciden | Revisa `MINIO_ROOT_USER` y `MINIO_ROOT_PASSWORD` |
| Levanta en tu máquina y en la de nadie más | Rutas absolutas tuyas, o el `.env` no está en `.env.example` | Toda variable nueva se agrega a `.env.example` **con valor vacío**, en el mismo commit |

---

## T011 · C1 · Esqueleto de Spring Boot con las tres capas

**Tiempo estimado:** 2 a 3 horas

### Qué entregas

`services/domain-service/` con un proyecto de Spring Boot que arranca con `mvn spring-boot:run` y responde `GET /health`, con las tres capas ya separadas en paquetes.

### Antes de empezar, verifica

- [ ] **T001 terminada**: existe `services/domain-service/` en tu copia del repositorio.
- [ ] JDK 21 instalado. `java -version` dice `21`.
- [ ] Maven instalado. `mvn -version` responde.

### Depende de · Bloquea a

**Depende de:** T001.
**Bloquea a:** **T009 (B, integración continua)** — B necesita algo que compilar. Y a T012, tu propio modelo de dominio.

**Cuando termines, avísale a B directamente.** Si te atrasas y no le dices, él va a configurar una canalización que no tiene nada que construir y va a pensar que su configuración está mal.

### Lo que necesitas saber

**Esto es lo más importante de la ficha.** El cronograma dice «tres capas separadas», y eso se presta a un malentendido caro.

El protocolo compromete **arquitectura hexagonal**, también llamada *puertos y adaptadores*. **No es** el patrón clásico controlador → servicio → repositorio que se enseña en la mayoría de los cursos. Si armas el clásico, en octubre hay que reescribirlo, y el diagrama de clases del 18 de septiembre no va a corresponder a lo entregado.

Las tres capas, en concreto:

| Paquete | Qué vive ahí | La regla que no se rompe |
|---|---|---|
| `domain` | Entidades, objetos de valor, agregados, reglas de negocio, e **interfaces** de repositorio | **Cero `import org.springframework`.** Cero JPA, cero anotaciones de framework. Java puro |
| `application` | Casos de uso que orquestan el dominio. Servicios de aplicación | Puede depender de `domain`. **No conoce** HTTP ni base de datos |
| `infrastructure` | Controladores REST, implementaciones JPA de los repositorios, configuración | Aquí sí vive Spring. Depende de las otras dos |

**La dirección de las dependencias es lo único que importa.** `infrastructure → application → domain`. Nunca al revés. La prueba: si borras la carpeta `infrastructure`, el paquete `domain` debe seguir compilando solo.

**Por qué así.** Porque la lógica de negocio se puede probar sin levantar Spring, sin base de datos y sin servidor. Cuando en la semana 10 tengas que demostrar cobertura de pruebas del dominio, esa decisión de hoy es la que hace que sea posible en una tarde en vez de en una semana.

**Qué es un endpoint de salud.** Una ruta que responde «estoy vivo» sin tocar nada más. La usan Docker para el `healthcheck`, la integración continua para saber si el servicio arrancó, y Traefik para decidir si mandarle tráfico.

### Paso a paso

1. Genera el proyecto en `start.spring.io` (o desde IntelliJ: File → New → Spring Initializr):

   - Project **Maven** · Language **Java** · Spring Boot **3.x**
   - Group `mx.tecnm.canastamx` · Artifact `domain-service` · Java **21**
   - Dependencias: **Spring Web**, **Spring Boot Actuator**, **Spring Data JPA**, **PostgreSQL Driver**, **Validation**, **Lombok** *(opcional)*

2. Descomprime dentro de `services/domain-service/`.

3. Crea los paquetes:

```
services/domain-service/src/main/java/mx/tecnm/canastamx/domain_service/
├─ domain/
│  ├─ model/          ← Usuario, Canasta, Alerta (vacío hoy, se llena en T012)
│  └─ repository/     ← interfaces, no implementaciones
├─ application/
│  └─ service/
└─ infrastructure/
   ├─ web/            ← controladores REST
   ├─ persistence/    ← implementaciones JPA
   └─ config/
```

Cada carpeta que quede vacía lleva su `.gitkeep`.

4. El endpoint de salud, en `infrastructure/web/HealthController.java`:

```java
package mx.tecnm.canastamx.domain_service.infrastructure.web;

import java.time.Instant;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HealthController {

    @GetMapping("/health")
    public Map<String, Object> health() {
        return Map.of(
            "status",  "UP",
            "service", "domain-service",
            "time",    Instant.now().toString()
        );
    }
}
```

5. **Desactiva la conexión a base de datos por ahora.** Todavía no hay esquema y Spring no arranca si no puede conectarse. En `src/main/resources/application.properties`:

```properties
spring.application.name=domain-service
server.port=8081
spring.autoconfigure.exclude=\
  org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration,\
  org.springframework.boot.autoconfigure.orm.jpa.HibernateJpaAutoConfiguration
```

Se quita en la semana 7, cuando haya tablas.

6. Corre y prueba:

```bash
cd services/domain-service
mvn spring-boot:run
# en otra terminal:
curl http://localhost:8081/health
```

### Cómo se ve terminado

```
$ curl http://localhost:8081/health
{"status":"UP","service":"domain-service","time":"2026-09-07T21:14:02.881Z"}
```

Y los tres paquetes existen, aunque `domain` y `application` estén vacíos. Pega la respuesta de `curl` en el issue como evidencia.

### Errores frecuentes

| Qué pasa | Por qué | Salida |
|---|---|---|
| `Failed to configure a DataSource` | Spring quiere conectarse a Postgres y no hay | Es el paso 5. Excluye las autoconfiguraciones |
| `release version 21 not supported` | Maven usa otro JDK | `mvn -version` te dice cuál. Ajusta `JAVA_HOME` |
| `Port 8080 was already in use` | Adminer, del compose de B, usa el 8080 | Por eso `server.port=8081`. No lo cambies |
| Pusiste anotaciones de JPA en `domain` | Es lo natural si vienes del patrón clásico | Se corrige ahora, no en octubre. `domain` no importa nada de framework |
| No sabes si el paquete se llama `domain_service` o `domainservice` | Depende de cómo lo generó Initializr | Abre `DomainServiceApplication.java` y usa el paquete que ya trae |

---

## T013 · C2 · Diccionario de datos de QQP

**Tiempo estimado:** 2 horas

### Qué entregas

`docs/datos/diccionario-qqp.md` con la lista completa de columnas del conjunto y qué significa cada una.

### Antes de empezar, verifica

- [ ] **T001 terminada**: existe `docs/datos/` en tu copia del repositorio.
- [ ] **A ya te pasó el enlace del diccionario por el chat.** Si no lo tienes, **pídelo antes de buscar por tu cuenta**: hay más de una versión del conjunto publicada y documentar la equivocada es peor que no documentar nada.

### Depende de · Bloquea a

**Depende de:** T002 (A localiza la fuente).
**Bloquea a:** en la semana 2, el contrato de datos de A. Ella va a declarar tipos y rangos por columna, y este documento es la única fuente de qué significa cada una.

### Lo que necesitas saber

**Por qué esta tarea es tuya y no de A.** Porque no es una tarea de datos, es una tarea de comprensión, y a ti te sirve directo: la app móvil va a mostrar precios por producto y establecimiento, y necesitas saber qué campos existen y cómo se llaman.

**Un diccionario de datos** describe cada columna: nombre exacto, tipo, qué representa y qué valores admite. Es el contrato entre quien publica y quien consume, y es lo que permite que el contrato de datos de la semana 2 se escriba con algo más que suposiciones.

**Copiar no basta.** El diccionario oficial dice qué *debería* traer cada columna. Tu trabajo incluye anotar lo que no queda claro: si «establecimiento» es la sucursal o la cadena, si la fecha es de captura o de vigencia, si el precio incluye impuestos. Esas dudas son insumo directo para A.

### Paso a paso

1. Abre el diccionario en `datos.profeco.gob.mx/diccionarioDatosQQP.php`.
2. Copia la plantilla `docs/datos/diccionario-qqp.md` y llena una fila por columna.
3. **Contrasta contra el archivo real.** Pídele a A el encabezado:

```bash
head -1 archivo.csv
```

Si el diccionario lista veinte columnas y el archivo trae dieciocho, **ese es un hallazgo** y va anotado en la sección de discrepancias.

4. Marca con `?` toda columna cuyo significado no te quede claro. La lista de dudas va al final del documento y se resuelve en la reunión del viernes.
5. Para las columnas categóricas —estado, categoría, tipo de establecimiento— pídele a A la lista de valores distintos:

```python
df["estado"].unique()
```

### Cómo se ve terminado

| Columna | Tipo | Significado | Ejemplo | Admite nulos | Notas |
|---|---|---|---|---|---|
| | | | | | |

Más dos secciones al final:

- **Discrepancias entre el diccionario y el archivo real**
- **Dudas para la reunión del viernes** — numeradas, para poder responderlas una por una

### Errores frecuentes

| Qué pasa | Por qué | Salida |
|---|---|---|
| Documentas columnas que no están en el archivo | El diccionario describe otra versión del conjunto | Siempre contrasta contra el `head -1` real |
| Copias el diccionario tal cual sin leerlo | Se siente productivo y no lo es | Si no puedes explicar una columna con tus palabras, ponle `?` |
| Los nombres no coinciden exactamente | Mayúsculas, acentos, guiones bajos | Copia el nombre **literal** del archivo. El contrato de datos falla por una mayúscula |

---

## T015 · D · Inventario de las ocho vistas

**Tiempo estimado:** 90 minutos

### Qué entregas

El archivo de Figma del proyecto creado y compartido, más `docs/analisis/inventario-vistas.md` con una línea de contenido por vista.

### Antes de empezar, verifica

- [ ] **T001 terminada**: existe `docs/analisis/` en tu copia del repositorio.
- [ ] Cuenta de Figma. La gratuita alcanza.

### Depende de · Bloquea a

**Depende de:** T001.
**Bloquea a:** T016 y T017, tus propios wireframes. Y en la semana 2, al sistema de diseño.

### Lo que necesitas saber

**Las ocho vistas ya están definidas en el protocolo de investigación.** No las inventes: si propones otras, el prototipo que se entregue el 18 de septiembre no va a corresponder al documento entregado el mismo día, y eso se nota.

| Vista | Cliente | Contenido principal | De dónde salen los datos |
|---|---|---|---|
| **Acceso** | Web y móvil | Autenticación, recuperación de contraseña | Servicio de dominio (C1) |
| **Tablero analítico** | Web | Evolución de precios por categoría, entidad y cadena; contraste contra el INPC | Interfaz analítica (A) |
| **Detalle de producto** | Web | Serie histórica, comparativo entre establecimientos, dispersión | Interfaz analítica (A) |
| **Consola de observabilidad** | Web | Los seis indicadores, linaje e incidentes | Interfaz analítica (A) |
| **Cola de reconciliación** | Web | Variantes de producto sin resolver, con acción de asignación manual | Interfaz analítica (A) |
| **Búsqueda** | Móvil | Búsqueda de producto y comparación por establecimiento | Interfaz analítica (A) |
| **Mi canasta** | Móvil | Composición de la canasta y costo estimado por establecimiento | Dominio (C1) y analítica (A) |
| **Alertas** | Móvil | Alta, edición y consulta de alertas de precio | Servicio de dominio (C1) |

**Tu trabajo no es decidir cuáles son.** Es decidir **qué contiene cada una y en qué orden**, que es donde está el diseño de verdad.

**La columna «de dónde salen los datos» te dice a quién preguntarle.** Si tienes una duda sobre qué muestra el tablero analítico, le preguntas a A. Sobre la pantalla de alertas, a C1. Escribirlo así desde hoy te ahorra mandar preguntas al chat general que nadie contesta porque nadie se siente aludido.

### Paso a paso

1. Crea el archivo de Figma. Nómbralo `CanastaMX`. Compártelo con permiso de **lectura para cualquiera con el enlace** —si no, los demás ven un 404— y pásale el enlace a A para el README.
2. Crea ocho *frames*, uno por vista, con el nombre exacto de la tabla. Vacíos por ahora.
3. Llena `docs/analisis/inventario-vistas.md`. Por cada vista:
   - Qué contiene, en una o dos líneas
   - Qué puede hacer el usuario ahí
   - Qué necesita del sistema para funcionar
   - Quién es el dueño del dato
4. Anota tus dudas al final. Van a la reunión del viernes.

### Cómo se ve terminado

El enlace de Figma abre en una ventana de incógnito y se ven los ocho *frames* nombrados. El inventario en el repositorio tiene las ocho vistas, ninguna vacía.

### Errores frecuentes

| Qué pasa | Por qué | Salida |
|---|---|---|
| El enlace de Figma da 404 a los demás | Está en privado por defecto | Share → Anyone with the link → **can view**. Pruébalo en incógnito |
| Inventas vistas que no están en el protocolo | Nadie te dijo que ya estaban definidas | Es la tabla de arriba. Ocho, ni una más |
| Empiezas a diseñar en vez de inventariar | Es lo divertido | Hoy es la lista. Los wireframes vienen después: T016 el martes y T017 el miércoles |
| El nombre del *frame* no coincide con el del protocolo | Se abrevia sin querer | Cópialos literales. En octubre alguien va a cruzar las dos listas |

---

# Martes 8 de septiembre

Cinco tareas. Cada quien avanza sobre lo que dejó ayer: A entra a los rangos, B pone el enrutamiento, C1 abre el modelo, C2 levanta el proyecto móvil y D dibuja el primer wireframe.

---

## T004 · A · Perfilado nivel 2: rangos y anomalías

**Tiempo estimado:** 2 horas

### Qué entregas

La sección de rangos y anomalías de `docs/datos/perfilado.md`, **escrita con números concretos, no con adjetivos**.

### Antes de empezar, verifica

- [ ] T003 terminada: sabes qué columnas hay y de qué tipo son de verdad.
- [ ] Sabes cuál columna es el precio y cuál la categoría. Si el nombre no es obvio, pregúntale a C2, que está leyendo el diccionario.

### Depende de · Bloquea a

**Depende de:** T003. **Bloquea a:** T006 (el informe) y, en la semana 2, el contrato de datos: los rangos que midas hoy son los umbrales que el contrato va a hacer cumplir.

### Lo que necesitas saber

Aquí no se pregunta «¿qué hay?» sino «¿es plausible?». Un flujo puede correr sin error y entregar precios negativos durante semanas: ese es exactamente el problema que el proyecto ataca.

**Qué se considera anomalía en precios:**

| Anomalía | Por qué importa | Qué se hace con ella |
|---|---|---|
| Precio en cero | O es un faltante disfrazado, o un error de captura | Regla de contrato: `precio > 0` |
| Precio negativo | No existe. Es error de captura o de signo | Regla de contrato |
| Precio absurdamente alto | Suele ser un decimal corrido: `2450` en vez de `24.50` | Umbral por categoría, no global |
| Duplicado exacto | El mismo levantamiento cargado dos veces | Deduplicación en la capa intermedia |

**«Absurdamente alto» depende de la categoría.** Un kilo de frijol en 800 pesos es absurdo; un electrodoméstico en 800 no. Por eso los percentiles se calculan **por categoría** y no sobre toda la tabla. Un umbral global marcaría como anómalo todo lo caro y dejaría pasar todo lo barato mal capturado.

**El percentil 99 es tu herramienta.** Si el p99 de una categoría es 180 y el máximo es 240,000, ese máximo es un error de captura, no un producto caro.

### Paso a paso

```python
import pandas as pd
PRECIO, CATEG = "precio", "categoria"       # nombres reales del archivo

# 1. Distribución por categoría
dist = df.groupby(CATEG)[PRECIO].describe(percentiles=[.01,.25,.5,.75,.95,.99])
print(dist.round(2))

# 2. Valores imposibles
print("En cero:   ", (df[PRECIO] == 0).sum())
print("Negativos: ", (df[PRECIO] <  0).sum())
print("Nulos:     ",  df[PRECIO].isna().sum())

# 3. Absurdos, con umbral POR CATEGORÍA
p99 = df.groupby(CATEG)[PRECIO].transform(lambda s: s.quantile(0.99))
absurdos = df[df[PRECIO] > p99 * 10]
print(f"Sospechosos (más de 10x el p99 de su categoría): {len(absurdos)}")
print(absurdos[[CATEG, "producto", PRECIO]].head(20))

# 4. Duplicados exactos
print("Duplicados exactos:", df.duplicated().sum())

# 5. Cardinalidad de las entidades del negocio
for c in ["establecimiento", "cadenaComercial", "estado", "municipio"]:
    if c in df.columns:
        print(f"{c}: {df[c].nunique():,} distintos")
```

Cada cifra se convierte en **una línea del informe y, casi siempre, en una regla del contrato de datos**. Anota las dos cosas.

### Cómo se ve terminado

```markdown
## 2. Rangos y anomalías

Precios en cero: 1,204 (0.34%)   ·   negativos: 0   ·   nulos: 88 (0.02%)
Duplicados exactos: 3,417 (0.97%)
Establecimientos distintos: 2,140  ·  cadenas: 38  ·  entidades: 32

| Categoría | mín | p25 | mediana | p75 | p95 | p99 | máx | sospechosos |
|---|---|---|---|---|---|---|---|---|

Reglas de contrato que se derivan de esto:
- precio > 0
- precio < p99 × 10 por categoría
- clave de unicidad: (producto, establecimiento, fecha)
```

### Errores frecuentes

| Qué pasa | Por qué | Salida |
|---|---|---|
| `describe()` no devuelve nada útil | La columna de precio es texto | `pd.to_numeric(df[PRECIO], errors="coerce")` y cuenta cuántos no se pudieron convertir: eso es otro hallazgo |
| Marcas como absurdo todo lo caro | Usaste un umbral global | Umbral por categoría, siempre |
| `duplicated()` devuelve cero | Hay una columna de identificador único que los distingue | Prueba con el subconjunto de negocio: `df.duplicated(subset=[producto, establecimiento, fecha])` |
| Escribes «hay bastantes nulos» | Es un adjetivo | «88 nulos, 0.02%». Los adjetivos no sostienen una recomendación |

---

## T008 · B · Traefik y enrutamiento local

**Tiempo estimado:** 2 a 3 horas

### Qué entregas

Traefik en el `docker-compose.yml`, con los servicios respondiendo por nombre de dominio local, y `.env.example` con todas las llaves y valores vacíos.

### Antes de empezar, verifica

- [ ] T007 terminada: `docker compose up -d` levanta los cuatro servicios.

### Depende de · Bloquea a

**Depende de:** T007. **Bloquea a:** en la semana 11, el despliegue con certificados. Hoy no bloquea a nadie.

### Lo que necesitas saber

**Qué es una puerta de enlace inversa.** Un servicio que recibe todo el tráfico en un solo puerto y lo reparte al contenedor que corresponde, según el nombre de dominio pedido. En vez de recordar que Adminer está en el 8080, MinIO en el 9001 y el dominio en el 8081, todo entra por el 80 y se distingue por nombre.

**Por qué desde ahora y no en noviembre.** Porque los clientes de C2 y D van a apuntar a una dirección. Si hoy apuntan a `localhost:8081` y en noviembre hay que cambiarlos a un dominio con HTTPS, hay que tocar código en dos clientes en la semana de la entrega final.

**Cómo se configura Traefik.** No con un archivo de rutas, sino con **etiquetas en cada servicio** del propio compose. Traefik lee las etiquetas de los contenedores y arma sus rutas solo. Por eso el protocolo lo eligió: la configuración vive en el mismo archivo que el servicio.

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.adminer.rule=Host(`db.canastamx.localhost`)"
  - "traefik.http.services.adminer.loadbalancer.server.port=8080"
```

**`*.localhost` resuelve solo** en los navegadores modernos: apuntan a `127.0.0.1` sin tocar el archivo `hosts`. Por eso los nombres locales terminan así.

### Paso a paso

1. Agrega el servicio `traefik` al compose, publicando el 80 y el 8090 para su panel.
2. Ponle etiquetas a `minio` y `adminer` con sus nombres locales.
3. Levanta y verifica:

```bash
docker compose up -d
docker compose logs traefik | head -30
```

- `http://db.canastamx.localhost` → Adminer
- `http://minio.canastamx.localhost` → MinIO
- `http://localhost:8090/dashboard/` → panel de Traefik: ahí ves qué rutas registró

4. **Crea `.env.example`.** Copia tu `.env`, borra **todos** los valores y déjalo así:

```bash
POSTGRES_OLTP_USER=
POSTGRES_OLTP_PASSWORD=
MINIO_ROOT_USER=
MINIO_ROOT_PASSWORD=
```

5. Confirma que `.env` está en `.gitignore` y que `.env.example` **sí** se sube.

### Cómo se ve terminado

Los dos nombres locales abren en el navegador, y el panel de Traefik lista las rutas en verde. Captura del panel en el issue.

### Errores frecuentes

| Qué pasa | Por qué | Salida |
|---|---|---|
| 404 de Traefik en todos los nombres | Faltan las etiquetas, o el contenedor no está en la misma red | `docker compose logs traefik`. Verifica `traefik.enable=true` |
| El nombre local no resuelve | Navegador viejo, o usaste otro sufijo | Usa `.localhost`. Si no, agrega la línea al archivo `hosts` |
| Traefik apunta al puerto equivocado | La etiqueta `server.port` es el puerto **interno** del contenedor, no el publicado | Adminer escucha en 8080 adentro, aunque lo publiques en otro |
| Subiste `.env` con contraseñas | No estaba ignorado | Detente, avisa a A. Rotar la credencial y limpiar el historial |

---

## T012 · C1 · Primer borrador del modelo de dominio

**Tiempo estimado:** 3 horas

### Qué entregas

`docs/analisis/modelo-dominio.md` con la clasificación de entidades, objetos de valor y los límites de los tres agregados, cada decisión justificada.

### Antes de empezar, verifica

- [ ] T011 terminada: tienes el proyecto con el paquete `domain` vacío esperando.
- [ ] Leíste la sección de casos de uso del protocolo, en particular CU-08 a CU-11.

### Depende de · Bloquea a

**Depende de:** T011. **Bloquea a:** en la semana 2, la implementación de Usuario y Canasta; en la semana 3, el diagrama de clases; en la 5, el modelo entidad-relación.

### Lo que necesitas saber

**Los tres agregados ya están nombrados en el protocolo: Usuario, Canasta y Alerta.** No inventes otros. Tu trabajo es decidir qué hay dentro de cada uno.

**Entidad contra objeto de valor.** La distinción es una sola pregunta: *¿tiene identidad propia que persiste aunque cambien sus atributos?*

| | Entidad | Objeto de valor |
|---|---|---|
| Identidad | Sí, un identificador | No. Es lo que vale |
| Igualdad | Dos usuarios con el mismo nombre son distintos | Dos precios de $24.50 MXN son el mismo |
| Mutabilidad | Cambia y sigue siendo el mismo | Inmutable. Para cambiarlo, se reemplaza |
| Ejemplos aquí | `Usuario`, `Canasta`, `Alerta` | `Dinero`, `CorreoElectronico`, `RangoDePrecio`, `Cantidad` |

**Qué es un agregado.** Un grupo de objetos que se trata como una unidad para los cambios. Tiene una **raíz**: el único objeto al que se puede llegar desde afuera. Todo lo de adentro se toca a través de ella.

Ejemplo concreto: `Canasta` es raíz y contiene `ItemDeCanasta`. Nadie modifica un ítem directamente; se le pide a la canasta que agregue, quite o cambie la cantidad. Así la canasta puede hacer valer sus reglas —no repetir productos, no aceptar cantidades negativas— porque todo pasa por ella.

**Las dos reglas de los agregados:**

1. **Una transacción, un agregado.** Guardar una canasta no debe modificar un usuario en la misma operación.
2. **Entre agregados se referencia por identificador, no por objeto.** `Canasta` guarda el `UsuarioId`, no un `Usuario` completo.

**Dónde viven las reglas de negocio.** Dentro del agregado, no en el controlador ni en la consulta. «Una alerta se dispara cuando el precio observado cae por debajo del umbral» es un método de `Alerta`, y se prueba sin levantar Spring. Eso es lo que hace posible la cobertura de pruebas de la semana 10.

**Punto de contacto con C2.** Lo que decidas aquí es lo que la app móvil va a consumir. Si defines que una canasta tiene un máximo de ítems, Oscar necesita saberlo para la pantalla. Coméntalo con él antes del viernes.

### Paso a paso

1. **Lista los sustantivos** de CU-08 a CU-12: usuario, contraseña, sesión, canasta, producto, cantidad, alerta, umbral, precio, notificación, establecimiento.
2. **Clasifica cada uno** con la pregunta de la identidad. Justifica en una línea; la justificación es lo que se evalúa.
3. **Dibuja los límites** de los tres agregados: qué queda dentro de cada uno.
4. **Escribe las reglas de negocio** que van dentro de cada agregado, una por línea.
5. **Anota lo que quede en duda** al final, para el viernes.

### Cómo se ve terminado

```markdown
## Agregado: Canasta
Raíz: Canasta

| Elemento | Tipo | Por qué |
|---|---|---|
| Canasta        | Entidad         | Tiene identidad; el usuario la nombra y la edita en el tiempo |
| ItemDeCanasta  | Entidad local   | Identidad solo dentro de la canasta; no se accede desde afuera |
| Cantidad       | Objeto de valor | Dos cantidades de 3 son la misma; inmutable |
| UsuarioId      | Referencia      | Se referencia por identificador, no por objeto |

Reglas dentro del agregado:
- No puede haber dos ítems del mismo producto; se suma la cantidad
- La cantidad es un entero mayor que cero
- Una canasta pertenece a exactamente un usuario y no cambia de dueño
- El costo estimado se calcula, no se almacena
```

Lo mismo para `Usuario` y `Alerta`.

### Errores frecuentes

| Qué pasa | Por qué | Salida |
|---|---|---|
| Todo sale entidad | Es lo que se enseña con bases de datos | Aplica la pregunta de la identidad a cada uno. Si dos instancias iguales son intercambiables, es objeto de valor |
| Un agregado gigante que contiene todo | Parece más simple | Si guardar una alerta obliga a cargar el usuario y sus canastas, el límite está mal |
| Modelas tablas en vez de dominio | Es el reflejo natural | El modelo entidad-relación viene en la semana 5. Hoy es dominio: sin claves foráneas, sin tipos de columna |
| Las reglas quedan en la descripción, no en el agregado | Es más rápido escribirlo así | Cada regla tiene que poder ser un método de una clase |

---

## T014 · C2 · Proyecto base de Expo corriendo

**Tiempo estimado:** 2 a 3 horas

### Qué entregas

`clients/mobile/` con un proyecto de Expo que arranca en un teléfono real o emulador, con navegación entre dos pantallas vacías.

### Antes de empezar, verifica

- [ ] T001 terminada: existe `clients/mobile/`.
- [ ] Node 20 instalado. `node -v` dice `v20.x`.
- [ ] Un teléfono con la app **Expo Go**, o un emulador funcionando.

### Depende de · Bloquea a

**Depende de:** T001. **Bloquea a:** toda la app móvil de aquí en adelante.

### Lo que necesitas saber

**Qué es Expo.** Una capa sobre React Native que evita configurar Xcode y Android Studio. Con la app **Expo Go** en tu teléfono, escaneas un código y tu aplicación corre ahí, con recarga en caliente.

**Por qué Expo y no React Native puro.** El protocolo lo justifica: comparte el paquete de tipos de TypeScript con el cliente web de D, lo que elimina divergencias de contrato. Si el servicio de dominio devuelve un campo, web y móvil lo tipan igual porque leen la misma definición.

**TypeScript desde el primer día, no después.** Convertir un proyecto de JavaScript a TypeScript en octubre cuesta un día entero. Arrancar en TypeScript cuesta cero.

**Enrutamiento por archivos.** Expo Router usa la estructura de carpetas como rutas: un archivo `app/busqueda.tsx` es la ruta `/busqueda`. No hay que configurar navegación a mano.

**Las cuatro pantallas** que vas a construir, para que las crees con el nombre correcto desde hoy: **Búsqueda**, **Detalle de producto**, **Mi canasta** y **Alertas**. Están en el inventario de vistas de D.

### Paso a paso

```bash
cd clients
npx create-expo-app@latest mobile --template blank-typescript
cd mobile
npx expo install expo-router react-native-safe-area-context react-native-screens
npx expo start
```

Escanea el código con Expo Go. La app abre en tu teléfono.

Crea dos pantallas mínimas para probar la navegación:

```
clients/mobile/app/
├─ _layout.tsx
├─ index.tsx          ← Búsqueda
└─ canasta.tsx        ← Mi canasta
```

```tsx
// app/index.tsx
import { Link } from "expo-router";
import { Text, View } from "react-native";

export default function Busqueda() {
  return (
    <View style={{ flex: 1, justifyContent: "center", alignItems: "center", gap: 16 }}>
      <Text style={{ fontSize: 20 }}>Búsqueda</Text>
      <Link href="/canasta">Ir a mi canasta</Link>
    </View>
  );
}
```

**Antes de subir**, confirma que `node_modules/` está en `.gitignore`. Son cientos de megabytes.

### Cómo se ve terminado

La app abre en tu teléfono, se ve «Búsqueda», el enlace lleva a «Mi canasta» y se puede regresar. Graba un video de diez segundos y súbelo al issue.

### Errores frecuentes

| Qué pasa | Por qué | Salida |
|---|---|---|
| Expo Go no encuentra el servidor | Teléfono y computadora en redes distintas | Misma red Wi-Fi. Si no se puede: `npx expo start --tunnel` |
| `Unable to resolve module expo-router` | Falta el punto de entrada | En `package.json`: `"main": "expo-router/entry"` |
| Se subió `node_modules/` | No estaba ignorado | `git rm -r --cached node_modules` y agrégalo al `.gitignore` en el mismo commit |
| Errores de tipos por todas partes | Es TypeScript haciendo su trabajo | Son avisos, no fallas de arranque. Se resuelven conforme avanzas |

---

## T016 · D · Wireframe del tablero analítico

**Tiempo estimado:** 2 a 3 horas

### Qué entregas

Wireframe de baja fidelidad del tablero analítico en Figma: qué gráficas van, en qué orden y con qué filtros.

### Antes de empezar, verifica

- [ ] T015 terminada: el inventario existe y el archivo de Figma está compartido.

### Depende de · Bloquea a

**Depende de:** T015. **Bloquea a:** el sistema de diseño de la semana 2 y el tablero real de la semana 8.

### Lo que necesitas saber

**Baja fidelidad significa cajas y etiquetas.** Sin colores de marca, sin tipografía definitiva, sin iconos bonitos. Lo que se decide hoy es **qué información va y en qué jerarquía**, y esa discusión se contamina cuando hay color: la gente opina del azul en vez de opinar de si la gráfica correcta es de líneas.

**Qué muestra el tablero analítico**, según el protocolo: evolución de precios por categoría, entidad y cadena; dispersión de precios; productos con comportamiento anómalo; y comparación contra la inflación oficial del INEGI.

**Quién lo usa: el analista.** No el consumidor. Quiere ver tendencias y comparar, no armar una canasta.

**Cuatro decisiones que este wireframe tiene que resolver:**

1. **Qué se ve primero.** Lo que ocupa la parte de arriba es lo que el analista mira. ¿La evolución de precios o el contraste contra el INPC?
2. **Qué filtros hay y dónde.** Categoría, entidad, cadena y periodo. ¿Barra superior o panel lateral?
3. **Qué tipo de gráfica para cada cosa.** Evolución en el tiempo pide líneas. Comparación entre categorías pide barras. Dispersión pide caja y bigotes o puntos.
4. **Qué pasa cuando no hay datos.** Un filtro puede dejar el tablero vacío. Ese estado se diseña, no se improvisa.

**Habla con A antes de dar por bueno el orden.** Ella sabe qué indicadores va a poder calcular de verdad y cuáles dependen de datos que quizá no existan.

### Paso a paso

1. En Figma, en el *frame* «Tablero analítico», dibuja cajas grises con etiqueta de texto. Nada más.
2. Define la retícula: encabezado, filtros, zona de gráficas.
3. Coloca cada gráfica como una caja con tres datos escritos adentro: **título**, **tipo de gráfica** y **qué eje es qué**.
4. Escribe al lado de cada caja de dónde sale el dato. Todo el tablero viene de la interfaz analítica de A.
5. Agrega el estado vacío como un *frame* aparte.
6. Comparte el enlace en el issue y menciona a A.

### Cómo se ve terminado

Un *frame* donde alguien que no conoce el proyecto puede decir qué información muestra la pantalla y en qué orden la leería, sin que nadie se lo explique.

### Errores frecuentes

| Qué pasa | Por qué | Salida |
|---|---|---|
| Pones color y tipografía bonita | Es lo divertido | La conversación se desvía al color. Gris y cajas |
| Diseñas gráficas que necesitan datos que no existen | Nadie te dijo qué se puede calcular | Pregúntale a A antes de dibujar |
| Ocho gráficas en una pantalla | Todo parece importante | Tres o cuatro. Lo demás va al detalle de producto |
| No hay estado vacío ni de carga | Solo se diseñó el caso feliz | Los dos se van a ver en la demostración. Diséñalos |

---

# Miércoles 9 de septiembre

Cuatro tareas. Es el día que produce el insumo de la reunión: sale el perfilado nivel 3 —el número que decide si H3 es alcanzable— y la canalización de integración continua empieza a correr.

---

## T005 · A · Perfilado nivel 3: variantes de escritura

**Tiempo estimado:** 2 a 3 horas · **La tarea más importante de la semana**

### Qué entregas

La tabla de variantes por producto en `docs/datos/perfilado.md`, con el conteo de veinte productos comunes, y una conclusión sobre si la meta de 85% de cobertura de H3 es realista.

### Antes de empezar, verifica

- [ ] T004 terminada: ya sabes cuántas cadenas y establecimientos hay.
- [ ] Identificaste la columna de nombre de producto y la de cadena comercial.

### Depende de · Bloquea a

**Depende de:** T004. **Bloquea a:** T006 y, sobre todo, **a la hipótesis H3 del protocolo**.

### Lo que necesitas saber

**Por qué esta tarea decide algo del protocolo.** H3 compromete cobertura mínima del 85% y precisión mínima del 90% en la reconciliación de nombres de producto entre cadenas. Ese número se comprometió **antes** de ver los datos. Hoy se mide si es alcanzable.

Ajustar la meta en septiembre con datos en la mano es método. Ajustarla en noviembre porque no salió es lo que el protocolo llama, textualmente, «ajuste retrospectivo de los criterios», y se declara que no se va a hacer. Hoy es el único momento en que se puede mover con honestidad.

**El problema de reconciliación, en concreto.** El mismo producto físico se escribe distinto en cada cadena:

```
LECHE ENTERA LALA 1 LT
Leche Lala entera 1L
LALA LECHE ENT. 1000ML
Leche entera Lala 1 litro
```

Cuatro cadenas, cuatro escrituras, un producto. Sin reconciliar, comparar precios entre cadenas es imposible, y comparar precios entre cadenas es la razón de ser del sistema.

**Cómo leer el resultado:**

| Variantes promedio por producto | Qué significa |
|---|---|
| 1 a 3 | La fuente ya trae un catálogo normalizado. H3 al 85% es cómodo |
| 4 a 8 | Normal. H3 al 85% es alcanzable con normalización más comparación difusa |
| Más de 10 | El problema es grande. Hay que **bajar la meta o acotar el recorte de productos**, y decirlo el viernes |

### Paso a paso

```python
import re, unicodedata, pandas as pd

def normaliza(s):
    """Minúsculas, sin acentos, sin puntuación, espacios colapsados."""
    s = str(s).lower()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

PROD, CADENA = "producto", "cadenaComercial"

# 1. Los veinte productos más frecuentes
top20 = df[PROD].value_counts().head(20).index.tolist()

# 2. Variantes por producto normalizado
df["_norm"] = df[PROD].apply(normaliza)
var = (df.groupby("_norm")
         .agg(variantes=(PROD, "nunique"),
              cadenas=(CADENA, "nunique"),
              ejemplos=(PROD, lambda s: " | ".join(sorted(set(s))[:4])))
         .sort_values("variantes", ascending=False))
print(var.head(20))

# 3. La cifra que decide
print("Variantes promedio por producto:", round(var["variantes"].mean(), 1))
print("Mediana:", var["variantes"].median())
print("Productos con más de 10 variantes:",
      (var["variantes"] > 10).sum(), "de", len(var))
```

**Revisa a mano una muestra.** Toma diez grupos y verifica que las variantes agrupadas sean de verdad el mismo producto. Si `leche entera 1l` juntó leche entera y leche deslactosada, tu normalización es demasiado agresiva y la cifra está inflada.

### Cómo se ve terminado

```markdown
## 3. Variantes de escritura

Variantes promedio por producto: 6.4   ·   mediana: 5   ·   máximo: 31
Productos con más de 10 variantes: 214 de 1,890 (11%)

| Producto (normalizado) | Variantes | Cadenas | Ejemplos |
|---|---|---|---|
| leche entera lala 1 l  | 7 | 5 | LECHE ENTERA LALA 1 LT / Leche Lala entera 1L / ... |

### Qué implica para H3
Con 6.4 variantes promedio, la meta de 85% de cobertura es alcanzable
mediante normalización más comparación difusa, siempre que el recorte de
productos se limite a la canasta básica. Se recomienda sostener la meta.

[o bien]

Con 14.2 variantes promedio y 38% de productos por encima de 10 variantes,
sostener el 85% no es realista sin trabajo manual extenso. Se recomienda
ajustar la meta a 70% y documentar el ajuste en el ADR 001, antes de la
entrega del 18 de septiembre.
```

### Errores frecuentes

| Qué pasa | Por qué | Salida |
|---|---|---|
| Salen dos variantes por producto y parece muy fácil | La normalización juntó productos distintos | Revisa diez grupos a mano. Siempre |
| Salen cincuenta variantes y parece imposible | No normalizaste antes de contar | Aplica `normaliza()` primero. Contar sobre el texto crudo mide otra cosa |
| No sabes cuál columna es el producto | Puede haber `descripcion`, `producto`, `presentacion` | Pregúntale a C2, que tiene el diccionario. Puede que necesites concatenar dos |
| Te quedas sin decidir sobre H3 | La conclusión se siente arriesgada | Es el punto de la tarea. Un número con una recomendación vale más que tres tablas sin conclusión |

---

## T009 · B · Integración continua mínima

**Tiempo estimado:** 2 horas

### Qué entregas

`.github/workflows/ci.yml` que, al abrir una solicitud, corre análisis estático y compilación, y aparece en verde.

### Antes de empezar, verifica

- [ ] T001 terminada: `main` está protegida y existe `.github/workflows/`.
- [ ] T011 (C1) **no es bloqueante**: la canalización se salta el trabajo de Java mientras no exista el `pom.xml`. Aun así, pregúntale a C1 cómo va: si ya terminó, puedes ver el trabajo compilando de verdad y no solo saltándose.

### Depende de · Bloquea a

**Depende de:** T001 y T011. **Bloquea a:** nada hoy, pero desde la semana 2 toda solicitud pasa por aquí.

### Lo que necesitas saber

**Qué es integración continua.** Un conjunto de verificaciones que corren solas en cada cambio propuesto. Si fallan, la solicitud no se puede incorporar. Convierte la calidad en condición de ingreso al repositorio en vez de en un acuerdo de buena voluntad.

**«Mínima» hoy significa dos cosas:** que el código compile y que pase el análisis estático. Las pruebas llegan en la semana 2, cuando existan.

**Un flujo de trabajo tiene tres partes:** cuándo corre (`on`), en qué máquina (`runs-on`), y qué hace (`steps`).

**Usa trabajos separados por lenguaje.** Uno para Java y uno para Python. Si van juntos, un fallo de Python bloquea el reporte de Java y nadie sabe cuál falló.

### Paso a paso

1. Copia la plantilla `.github/workflows/ci.yml` del repositorio.
2. **No tienes que ajustar nada para que arranque.** Cada trabajo revisa primero si el proyecto que le toca ya existe: si `services/domain-service/` todavía no tiene `pom.xml`, el trabajo de Java lo dice y se salta, en verde. Empieza a compilar solo, en cuanto C1 suba el suyo.

   Esto es a propósito: una canalización que intenta compilar un proyecto inexistente sale **roja en toda solicitud**, y el resto del equipo no entiende por qué su cambio de documentación falla.
3. Prueba con una solicitud de verdad:

```bash
git switch -c chore/aas-ci-minima
# edita ci.yml
git add .github/workflows/ci.yml
git commit -m "ci: análisis estático y compilación en cada solicitud"
git push -u origin chore/aas-ci-minima
```

4. Abre la solicitud. Abajo aparecen las verificaciones. **Espera a que terminen.**
5. Si sale roja: *Details* → busca la línea que dice `Error:` → arregla en tu rama → commit → push. La solicitud se actualiza sola, no abras otra.
6. **Protege `main`, etapa 2.** Ahora que la canalización ya corrió una vez, sus trabajos aparecen en la lista de GitHub. Settings → Branches → edita la regla de `main` → ☑ **Require status checks to pass** → selecciona **Dominio (Java)**, **Datos (Python)** e **Higiene**.

Ese paso es el que convierte la canalización en compuerta. Sin él corre, reporta y no impide nada. A dejó la etapa 1 antes de arrancar la semana —solicitud obligatoria y una aprobación—; esta es la que faltaba.

### Cómo se ve terminado

La solicitud muestra los dos trabajos con palomita verde, y el botón de incorporar está habilitado. En una rama con un error de sintaxis a propósito, sale roja y el botón se bloquea. **Pruébalo**: una compuerta que nunca cerró nadie sabe si cierra.

### Errores frecuentes

| Qué pasa | Por qué | Salida |
|---|---|---|
| El flujo no se dispara | Está en la rama, no en `main`, o el `on:` está mal | Los flujos se leen de la rama de la solicitud, pero conviene incorporarlo pronto |
| `mvn: command not found` | Falta el paso de configurar Java | `actions/setup-java@v4` con `distribution: temurin` y `java-version: 21` |
| Sale verde pero no verifica nada | Las rutas no existen y el paso se salta | Revisa el registro: si dice «no such directory», la ruta está mal |
| Tarda diez minutos cada vez | Sin caché de dependencias | `cache: maven` en `setup-java` y `cache: pip` en `setup-python` |

---

## T010 · B · Oracle Cloud y GitHub Student Pack

**Tiempo estimado:** 45 minutos de trámite, más la espera

### Qué entregas

Ambos registros enviados, con captura del acuse en el issue.

### Antes de empezar, verifica

- [ ] Tienes tu credencial de estudiante o comprobante de inscripción a la mano, en foto legible.
- [ ] Tienes tu correo institucional funcionando.

### Depende de · Bloquea a

**Depende de:** nada. **Bloquea a:** la semana 9, cuando toca preparar la máquina virtual y hacer el primer despliegue.

### Lo que necesitas saber

**Por qué se hace la primera semana si se usa hasta la novena.** Porque ninguno de los dos es instantáneo. El Student Pack requiere verificación con documento y puede tardar días o rebotar. Oracle Cloud pide tarjeta para verificar identidad —no cobra en la capa gratuita— y a veces rechaza el registro sin explicación clara.

Si esto se hace en la semana 8, un rechazo deja al equipo sin nube en la semana del despliegue. Hacerlo hoy deja siete semanas de margen para resolver o buscar alternativa.

**Qué da cada uno:**

| Servicio | Qué aporta |
|---|---|
| Oracle Cloud, capa siempre gratuita | Máquinas virtuales sin costo permanente. Donde vive el sistema desplegado |
| GitHub Student Developer Pack | Crédito en varios proveedores, dominio gratuito por un año, herramientas |

**Alternativas si algo se cae:** Hetzner (de pago, barato y confiable), Fly.io o Railway en sus capas gratuitas, o Azure for Students si el Tec tiene convenio. **Pregunta en el Tec antes de pagar de tu bolsa.**

### Paso a paso

1. **Oracle Cloud** — `cloud.oracle.com` → Start for free. Región: elige una de Estados Unidos o Brasil, no Europa. Vas a necesitar tarjeta para verificar. **Anota qué región elegiste**: las instancias no se mueven entre regiones.
2. **GitHub Student Pack** — `education.github.com/pack` → Get student benefits. Sube foto legible de tu credencial y usa el correo institucional. Si rebota, se puede volver a intentar con otro documento.
3. Captura ambos acuses y pégalos en el issue.
4. **Si alguno es rechazado, ábrelo como bloqueo el mismo día.** No lo dejes para la reunión del viernes: hay que activar la alternativa temprano.

### Cómo se ve terminado

Dos capturas en el issue: la de Oracle diciendo que la cuenta está en aprovisionamiento, y la de GitHub diciendo que la solicitud está en revisión. **Aprobado no es requisito hoy; enviado sí.**

### Errores frecuentes

| Qué pasa | Por qué | Salida |
|---|---|---|
| Oracle rechaza la tarjeta | Algunas tarjetas de débito mexicanas no pasan | Prueba otra, o pide apoyo en el chat. Es común y no es tu culpa |
| El Student Pack rebota | La foto de la credencial no se lee, o el correo no es institucional | Vuelve a intentar con horario visible y documento nítido |
| Elegiste región equivocada | Se ve igual al registrarse | Anótala hoy. En la semana 9 importa |

---

## T017 · D · Wireframe de la consola de observabilidad

**Tiempo estimado:** 2 a 3 horas · **Requiere visto bueno de A por escrito**

### Qué entregas

Wireframe de la consola de observabilidad en Figma, revisado por A y con su aprobación escrita en el issue.

### Antes de empezar, verifica

- [ ] T015 terminada.
- [ ] Leíste los seis indicadores de aquí abajo. **No los inventes.**

### Depende de · Bloquea a

**Depende de:** T015 y la revisión de A. **Bloquea a:** la consola real de la semana 11.

### Lo que necesitas saber

**Esta es la pantalla más importante del proyecto para la investigación.** El protocolo lo dice con todas sus letras: si un incidente de calidad no salta a la vista en tres segundos, el mecanismo de detección no sirve de nada. La hipótesis H2 mide el tiempo entre que llega un dato malo y que el sistema lo señaliza. Si el sistema lo señaliza y la pantalla no lo hace evidente, la medición no significa nada.

**Los seis indicadores, exactos, del protocolo:**

| # | Indicador | Qué muestra |
|---|---|---|
| 1 | **Estado de la última ejecución** | ¿La última corrida del flujo terminó bien, con advertencias o falló? |
| 2 | **Frescura por fuente** | Cuánto hace que llegó dato nuevo de cada fuente. Se rompe si pasa el umbral |
| 3 | **Resultado de las validaciones** | Cuántas reglas del contrato se evaluaron, cuántas pasaron, cuáles fallaron |
| 4 | **Linaje entre activos** | Qué tabla alimenta a cuál. Permite ver qué se afecta cuando algo falla |
| 5 | **Historial de incidentes** | Los incidentes recientes, con su hora, severidad y estado |
| 6 | **Volumen en cuarentena** | Cuántas filas fueron rechazadas y por qué regla |

**Quién la usa: el operador de datos.** Alguien que la abre para responder una sola pregunta: *¿está todo bien?* Si la respuesta es sí, cierra en tres segundos. Si es no, quiere saber qué, desde cuándo y qué se afectó.

**El principio de diseño que hay que aplicar.** El estado se codifica en la **forma**, no solo en el número. Un «3 incidentes» en texto negro entre otros números negros no se ve. Un contador rojo con una franja de severidad al costado, sí. El color semántico —bien, advertencia, crítico— es distinto del color de marca.

**Diseña dos estados, no uno.** Todo en verde y algo roto. La demostración del 18 de noviembre consiste en pasar del primero al segundo en vivo: esa transición tiene que ser visible desde el fondo del salón.

### Paso a paso

1. En el *frame* «Consola de observabilidad», coloca los seis indicadores. Los tres que responden «¿está bien?» arriba: estado de la última ejecución, frescura y resultado de validaciones.
2. Para cada uno decide **qué se ve cuando todo está bien** y **qué se ve cuando está roto**. Escríbelo al lado de la caja.
3. El linaje es un diagrama de cajas conectadas. En baja fidelidad, cinco cajas con flechas alcanzan.
4. La cuarentena y el historial de incidentes son tablas. Define sus columnas.
5. Duplica el *frame* y haz la versión «con incidente»: qué cambia de color, qué aparece, qué se mueve.
6. **Compártelo con A y pídele visto bueno por escrito en el issue.** No basta un «sí» en el chat: se necesita rastro escrito, porque esta pantalla es objeto de investigación.

### Cómo se ve terminado

Dos *frames*: «todo bien» y «con incidente». Alguien que los vea uno tras otro debe notar la diferencia **sin leer ningún número**. Y en el issue, un comentario de A que diga que los seis indicadores están completos y bien representados.

### Errores frecuentes

| Qué pasa | Por qué | Salida |
|---|---|---|
| Inventas indicadores | Nadie te los había dado | Son los seis de la tabla. Ni más ni menos |
| Solo diseñas el estado sano | Es el que se dibuja primero | El estado roto es el que se demuestra. Diséñalo con el mismo cuidado |
| El incidente se comunica solo con un número | Es lo más rápido | Forma y color, no solo dígitos. La prueba de los tres segundos |
| Sigues sin el visto bueno de A | Da pena insistir | La ficha lo exige. Etiquétala en el issue y espera |

---

# Jueves 10 de septiembre

Una sola tarea, y es la que sostiene la reunión del viernes.

---

## T006 · A · Informe de perfilado versión cero

**Tiempo estimado:** 3 horas · **Jueves 10**

### Qué entregas

`docs/datos/informe-perfilado-v0.md` con las tres secciones del perfilado y una conclusión explícita: **la fuente sirve, o no sirve, y por qué.**

### Antes de empezar, verifica

- [ ] T003, T004 y T005 terminadas. Las tres secciones del perfilado tienen números.

### Depende de · Bloquea a

**Depende de:** todo el perfilado. **Bloquea a:** T018, la reunión del viernes. Sin informe, la reunión no tiene de qué decidir y hay que reagendarla.

### Lo que necesitas saber

**Esto no es un resumen: es una recomendación.** La diferencia está en el último párrafo. Un resumen termina con «estos son los hallazgos». Una recomendación termina con «por lo tanto, propongo esto, y estas son las cifras que lo sostienen».

**Tres preguntas que el informe tiene que contestar sin ambigüedad:**

1. **¿La fuente sirve?** Sí o no. No «depende».
2. **¿Con qué recorte?** El protocolo ya comprometió centro-occidente y 2024–2026. ¿Se sostiene con los datos que viste?
3. **¿H3 al 85% es realista?** Del perfilado nivel 3 sale la respuesta.

**Qué haría que la fuente no sirviera.** Que no haya serie histórica utilizable, que el precio no sea recuperable de forma confiable, que no se pueda distinguir establecimiento de cadena, o que las variantes de escritura sean tantas que la reconciliación no sea abordable en el semestre. Si alguna se cumple, se activa el plan alternativo: base de 2025 más recolección propia acotada de dos o tres cadenas.

**Nadie espera que la fuente esté limpia.** Que esté sucia es la premisa del proyecto: el sistema existe para atrapar datos malos. Lo que hay que determinar es si está **utilizable**, que es otra cosa.

### Paso a paso

1. Copia la plantilla `docs/datos/informe-perfilado-v0.md`.
2. Pega las tres secciones del perfilado, cada una con sus tablas.
3. Escribe la conclusión **al final y en firme**, con tres partes: el veredicto, el recorte recomendado con su justificación numérica, y la postura sobre H3.
4. Marca lo que quede sin resolver como pregunta abierta para la reunión.
5. Súbelo por solicitud y avisa en el chat el jueves, no el viernes: los demás deberían llegar leídos.

### Cómo se ve terminado

Un documento que alguien puede leer en diez minutos y salir sabiendo si el proyecto sigue adelante y con qué alcance. Con tablas. Sin adjetivos sueltos.

### Errores frecuentes

| Qué pasa | Por qué | Salida |
|---|---|---|
| Termina con «se recomienda continuar analizando» | La conclusión da miedo | Es exactamente lo que no puede pasar. Toma postura |
| Solo tablas, sin interpretación | Las tablas se sienten objetivas | Cada tabla necesita una línea que diga qué significa |
| No dices nada sobre H3 | Es la parte incómoda | Es la parte que convierte esto en investigación |

---

# Viernes 11 de septiembre

La reunión de decisión. Los cinco, cámara encendida.

---

## T018 · Equipo · Reunión de decisión y ADR de la fuente

**Tiempo estimado:** 45 minutos de reunión, más 30 de escritura del ADR

### Qué entregan

`docs/adr/001-fuente-de-datos.md` con la decisión, y el horario fijo de la reunión semanal en el calendario de los cinco.

### Antes de empezar, verifiquen

- [ ] Los cinco **leyeron el informe de perfilado**. La reunión no es para leerlo en voz alta.
- [ ] Cada quien incorporó su avance de la semana por solicitud, revisada por otro.
- [ ] Cámara encendida. Son cuarenta y cinco minutos al semestre; no es mucho pedir.

### Lo que necesitan saber

**Por qué esta reunión es la más importante del semestre.** Porque es la única en la que todavía se puede cambiar de rumbo sin costo. Si la fuente no sirve y se descubre en octubre, no hay margen. Hoy sí lo hay.

**El recorte geográfico no se decide desde cero.** El protocolo ya comprometió en Alcances: **centro-occidente, ventana 2024 a 2026, entre dos y cuatro millones de registros.** La pregunta correcta no es «¿qué recorte hacemos?» sino **«¿el recorte que ya comprometimos se sostiene con los datos que A midió?»**. Tres respuestas posibles:

- **Se sostiene** — el ADR lo confirma y no se toca el protocolo.
- **Hay que acotarlo** — menos estados, o menos productos. Se registra y **se corrige el protocolo antes del 18 de septiembre**.
- **Se puede ampliar** — raro, pero si los datos son mejores de lo esperado, se documenta igual.

**Qué es un ADR.** Un registro de decisión de arquitectura. Media cuartilla con cuatro cosas: fecha, contexto, decisión y alternativas descartadas. Existe porque en diciembre nadie recuerda por qué se descartó algo, y el asesor lo va a preguntar.

**Se escribe aunque la respuesta sea «todo sigue igual».** Un ADR que confirma una decisión previa con datos nuevos es tan válido como uno que la cambia, y demuestra que la confirmación fue deliberada y no inercia.

### Agenda, cronometrada

| Min | Qué | Quién |
|---|---|---|
| 0–10 | Presentación del perfilado. **Recomendación con números, no lectura** | A |
| 10–20 | Decisión sobre la fuente: ¿sirve o se activa el plan alternativo? | Los cinco |
| 20–28 | El recorte: ¿centro-occidente y 2024–2026 se sostiene, se acota o se amplía? | Los cinco |
| 28–33 | H3: ¿la meta de 85% se sostiene o se ajusta? | A propone, los cinco deciden |
| 33–38 | Confirmar el reparto C1 y C2, y quién es dueño del README | Los cinco |
| 38–45 | Horario fijo de la reunión semanal y carga de las tareas de la semana 2 | Los cinco |

### Cómo se ve terminado

```markdown
# ADR 001 · Fuente de datos

- **Fecha:** 11 de septiembre de 2026
- **Estado:** aceptada
- **Participantes:** los cinco integrantes

## Contexto
[Qué se midió, con las tres cifras que más pesaron en la decisión]

## Decisión
[Se continúa con QQP / se activa el plan alternativo]
[Recorte: se confirma o se ajusta centro-occidente y 2024–2026. Con su razón]
[H3: se sostiene el 85% o se ajusta a __%. Con su razón]

## Alternativas descartadas
[Plan alternativo con recolección propia: por qué no, o por qué sí]

## Consecuencias
[Qué cambia en el protocolo, si algo cambia]
[Quién lo corrige y antes de qué fecha]
```

Más, en el tablero: la columna de la semana 2 poblada y el horario de la reunión en el calendario de los cinco.

### Errores frecuentes

| Qué pasa | Por qué | Salida |
|---|---|---|
| La reunión se va en leer el informe | Nadie lo leyó antes | Se manda el jueves y se lee antes. Si nadie lo leyó, se pospone media hora |
| Se decide «seguir viendo» | Es cómodo | No es una decisión. Se decide hoy |
| El ADR se escribe «después» | La reunión se acaba y todos se van | Se escribe en los últimos diez minutos, con todos presentes |
| Se cambia el recorte y nadie corrige el protocolo | Se olvida | La sección de consecuencias del ADR pone nombre y fecha |
| Se ajusta H3 sin registrarlo | Da la impresión de fracaso | Al revés: ajustar con datos en septiembre es método. Ajustar en noviembre sin datos no lo es |

---

# Cierre de la semana

- [ ] Repositorio con estructura completa, `.gitignore`, README inicial y `main` protegida
- [ ] Los cinco clonaron y ven lo mismo
- [ ] `docker compose up` levanta cuatro servicios en la máquina de al menos dos integrantes
- [ ] Informe de perfilado v0 con conclusión explícita
- [ ] `docs/adr/001-fuente-de-datos.md` escrito, con fecha
- [ ] Recorte confirmado o ajustado con base en datos reales
- [ ] Postura sobre H3 registrada
- [ ] Cuentas de Oracle Cloud y GitHub Student Pack solicitadas
- [ ] Diccionario QQP documentado, con sus discrepancias
- [ ] Inventario de ocho vistas y dos wireframes en Figma, la consola con visto bueno de A
- [ ] Modelo de dominio en primer borrador
- [ ] Proyecto móvil base arrancando
- [ ] Tablero con las tareas de la semana 2 y horario fijo de reunión acordado

**Las fichas de la semana 2 se escriben el viernes 11, al cerrar la reunión**, con `PLANTILLA-ficha.md`. Escribirlas es parte de cerrar la reunión, no una tarea aparte: es el momento en que ya se sabe qué se recorrió y qué no.
