# La plataforma de datos en su contenedor (T054 · #201). La revisa A.
#
# Una imagen para dos contenedores, como en docs/arquitectura/05-despliegue.dot:
# el servidor de Dagster (la orden por omisión) y su daemon, que corre el sensor y
# la cola de corridas. infra/envs/prod/docker-compose.yml levanta los dos.
#
# Se construye desde la RAÍZ del repositorio, porque la plataforma lee dos cosas
# fuera de su carpeta: el contrato (contracts/qqp-v1.yaml) y el SQL del esquema de
# operación (docs/datos/esquema-de-operacion.sql). Qué entra y qué no lo dice
# Dockerfile.dockerignore, junto a este archivo:
#   docker build -f services/data-platform/Dockerfile -t canastamx/data-platform .

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HOME=/home/plataforma \
    DAGSTER_HOME=/datos/dagster \
    CANASTAMX_LOTES=/datos/lotes \
    CANASTAMX_CORRIDAS=/datos/corridas

# Las tres carpetas de la plataforma, fuera del código. En el despliegue son
# volúmenes; nacen con estos dueños, así que el usuario sin privilegios escribe ahí.
RUN useradd --system --create-home --home-dir /home/plataforma plataforma \
 && mkdir -p /datos/lotes /datos/corridas /datos/dagster /app/services/data-platform \
 && chown -R plataforma:plataforma /datos /app/services/data-platform

WORKDIR /app/services/data-platform
COPY services/data-platform/requirements.txt .
RUN pip install -r requirements.txt

COPY contracts/ /app/contracts/
COPY docs/datos/esquema-de-operacion.sql /app/docs/datos/esquema-de-operacion.sql
COPY --chown=plataforma:plataforma services/data-platform/ ./

USER plataforma
# Las extensiones de DuckDB se bajan aquí, una vez, y no en la primera corrida:
# httpfs para escribir en MinIO y postgres para la capa intermedia.
RUN python -c "import duckdb; c = duckdb.connect(); [c.install_extension(e) for e in ('httpfs', 'postgres')]"

EXPOSE 3000
CMD ["dagster-webserver", "-h", "0.0.0.0", "-p", "3000", "-m", "orquestacion.definiciones"]
