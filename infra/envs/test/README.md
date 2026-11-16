# CANASTAMX - TEST

En este directorio se encuentran los archivos necesarios para levantar el entorno de pruebas. 

> **NOTA**
> ---
> Consulte la [📖 **GUÍA DE ARRANQUE**](../../../docs/infra/arranque.md) para tener un mejor entendimiento del proceso.  

## GUÍA RÁPIDA

### Método A

1. Ubique el directorio de trabajo de su terminal en `canastamx/infra/envs/test`

2. Haga una copia de `.env.example` con el nombre de `.env` en el mismo directorio

3. Rellene los campos indicados en `.env` (Consulte **Guía de arranque** para recordar este procedimiento)

4. Ejecute `docker compose up -d`

### MÉTODO B

1. Siga pasos del 1 al 3 del [método A](#método-a)

2. Posicione el directorio de trabajo de su terminal en la raíz (`canastamx/`)

3. Ejecute el siguiente comando en su terminal

```bash
docker compose -f infra/envs/test/docker-compose.yml --env-file infra/envs/test/.env up -d
```

> **NOTA**
> ---
> El llenado de .env solo es necesario hacerlo una vez. Tras realizarlo, puede omitir esos pasos y ejecutar directamente docker compose de acuerdo al método elegido.

**RESULTADO ESPERADO**
Un entorno de canastamx bajo el nombre de canastamx_test, que pueda ser ejecutado en conjunto a canastamx (dev)

> **IMPORTANTE · levante y baje los entornos desde una terminal sin ningún `.env` cargado**
> ---
> Docker Compose toma los puertos, las contraseñas y el nombre del bucket de las variables que la terminal ya tiene exportadas **antes** que del `.env` o del `--env-file`. Si levanta desarrollo en una terminal donde cargó el `.env` de pruebas, desarrollo se queda con los puertos de pruebas (5443, 9010), y la plataforma «de pruebas» escribe en desarrollo. Pasó el 15 de noviembre (#187).
>
> Antes de `up` o `down`, compruebe que la terminal está limpia:
>
> ```bash
> env | grep -E '^(OLTP|ANALYTICS|S3)_' || echo "terminal limpia"
> ```
>
> Las terminales donde corre `set -a; source …` son sólo para la plataforma y la comprobación, nunca para Docker.
## LA PLATAFORMA DE DATOS CONTRA PRUEBAS

Docker Compose levanta las bases y MinIO de pruebas, pero la plataforma de datos (Dagster y `ingesta.py`) **corre en su terminal, fuera de Docker**. Escribe donde digan las variables de esa terminal: si la terminal tiene cargado el `.env` de desarrollo, la plataforma escribe en desarrollo aunque el entorno de pruebas esté arriba. Por eso levantar los contenedores no basta.

### 1. Apuntar la plataforma a pruebas

1. En `infra/envs/test/.env`, escriba las tres carpetas con **ruta absoluta**, fuera del repositorio y sin `~` ni `$HOME`. Por ejemplo:

   ```
   CANASTAMX_LOTES=/home/<su-usuario>/canastamx-pruebas/lotes
   CANASTAMX_CORRIDAS=/home/<su-usuario>/canastamx-pruebas/corridas
   DAGSTER_HOME=/home/<su-usuario>/canastamx-pruebas/dagster
   ```

2. Créelas y deje **vacía** la de lotes: el sensor pide una corrida por cada archivo que encuentre ahí.

   ```bash
   mkdir -p /home/<su-usuario>/canastamx-pruebas/{lotes,corridas,dagster}
   ```

3. Desde la raíz del repositorio, cargue el `.env` de pruebas en la terminal. Vale sólo para esa terminal: si abre otra, hay que cargarlo otra vez.

   ```bash
   set -a; source infra/envs/test/.env; set +a
   ```

| Variable | Qué es | En pruebas |
|---|---|---|
| `CANASTAMX_LOTES` | La carpeta que vigila el sensor: ahí llegan los archivos | Una carpeta propia, vacía al empezar |
| `CANASTAMX_CORRIDAS` | Donde queda la evidencia de cada corrida | Una carpeta propia |
| `DAGSTER_HOME` | Donde Dagster guarda sus corridas, lo que el sensor ya vio y las salidas de cada activo | Una carpeta propia, que no sea `~/.dagster` |
| `CANASTAMX_SIMULAR` | `0` escribe de verdad en MinIO y en PostgreSQL | `0`: el experimento no simula |
| `CANASTAMX_FECHA_REFERENCIA` | Contra qué fecha se mide la frescura | `2026-08-10` (10 días); el experimento usa también `2026-08-25` y `2026-09-20` |

### 2. Comprobar a dónde apunta

Antes de cada corrida, **en la misma terminal donde va a lanzar Dagster**:

```bash
python3 infra/envs/test/verificar-entorno-pruebas.py
```

Termina con `OK: la terminal apunta al entorno de pruebas.` o con `DETENIDO` y la lista de lo que falla. Con `DETENIDO` no se corre nada. Revisa las variables de la terminal, no las del archivo:

- el bucket y su puerto: `canastamx-bronze-test` en el 9010 (desarrollo: `canastamx-bronze` en el 9000);
- la base analítica: `test-canastamx_analytics` en el 5443 (desarrollo: `canastamx_analytics` en el 5433);
- `CANASTAMX_SIMULAR=0` y una fecha de referencia válida;
- **qué contenedor está detrás de cada puerto:** le pregunta a Docker quién publica el 9010 y el 5443, y se detiene si no son contenedores del proyecto `canastamx_test`. Así detecta los puertos cruzados de arriba, aunque las variables de la terminal estén bien, y también el entorno de pruebas abajo;
- las tres carpetas: rutas absolutas que existen, fuera del repositorio aunque se llegue por un enlace, cada una por su lado (ni la misma ni una dentro de otra) y `DAGSTER_HOME` distinta de `~/.dagster`.

Lo que **no** revisa:

- las carpetas de desarrollo que alguien tenga fuera del repositorio: no puede saber dónde están en cada máquina;
- otras terminales: sólo protege la terminal donde se corre;
- lo que pase después: si alguien baja y vuelve a levantar los entornos a media corrida, hay que correrla otra vez.

Necesita que Docker conteste sin `sudo`. Si no contesta, se detiene: sin Docker no se sabe qué contenedor hay detrás de cada puerto.

Para ver además si una variable que quedó exportada de antes le gana al archivo, sin mostrar valores:

```bash
python3 infra/scripts/revisar-env.py --entorno infra/envs/test/.env
```

### 3. Una corrida con el sensor encendido

Use terminales separadas: una de pruebas sólo para Dagster, y otra de pruebas para copiar el lote y revisar. Si necesita contar algo de desarrollo, hágalo en una tercera terminal con el `.env` de la raíz cargado, y **nunca lance Dagster en ella**.

1. En la terminal de Dagster, con la comprobación en `OK`:

   ```bash
   cd services/data-platform
   dagster dev -m orquestacion.definiciones
   ```

   Es normal el aviso `No dagster instance configuration file (dagster.yaml) found`: dice que Dagster guarda su estado en su `DAGSTER_HOME`. Para quitarlo, cree el archivo vacío: `touch "$DAGSTER_HOME/dagster.yaml"`.

2. Abra `http://localhost:3000` y, en **Automation**, encienda `archivo_nuevo`. Revisa la carpeta cada 30 segundos; mientras está vacía, el log dice `skipped: ningún archivo nuevo en la carpeta de llegada`.

3. En la otra terminal de pruebas, copie un lote con su nombre exacto (por ejemplo `07-2026_Q2.parquet`):

   ```bash
   cp <ruta-del-lote>/07-2026_Q2.parquet "$CANASTAMX_LOTES"/
   ```

   En menos de 30 segundos aparece la corrida en **Runs**, con las etiquetas `canastamx/disparo` (el cero de H2) y `canastamx/lote`.

4. Al terminar, apague el sensor en **Automation** y detenga Dagster con Ctrl+C.

La primera corrida, con su evidencia, está en #187.

## BAJAR SÓLO PRUEBAS

**Siempre con `-f`, y desde una terminal sin `.env` cargado.** Sin `-f`, desde la raíz, Docker Compose usa el `docker-compose.yml` de desarrollo, y con `-v` borra los volúmenes de desarrollo.

```bash
# Apaga y conserva los datos de pruebas
docker compose -f infra/envs/test/docker-compose.yml --env-file infra/envs/test/.env down

# Apaga y BORRA los volúmenes de pruebas: las dos bases y el bucket
docker compose -f infra/envs/test/docker-compose.yml --env-file infra/envs/test/.env down -v

# Los de desarrollo siguen en la lista
docker volume ls
```

Las tres carpetas de la plataforma no son volúmenes de Docker: `down -v` no las toca. Para empezar de cero, vacíelas a mano. `DAGSTER_HOME` guarda lo que el sensor ya vio, y si no se vacía, Dagster sigue mostrando las corridas anteriores.
