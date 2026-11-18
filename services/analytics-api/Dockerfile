# La interfaz analítica en su contenedor (T054 · #201). La revisa A.
#
# Se construye desde esta carpeta:
#   docker build -t canastamx/analytics-api services/analytics-api
# En el despliegue lo construye infra/envs/prod/docker-compose.yml, que le pasa
# ANALYTICS_HOST=postgres-analytics y DOMINIO_URL=http://domain-service:8081.

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /servicio
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY analitica/ analitica/
RUN useradd --system --no-create-home servicio
USER servicio
EXPOSE 8000
# Detrás de Traefik: --proxy-headers para que la aplicación sepa que entró por
# HTTPS. Sólo se alcanza desde la red de Compose, así que se confía en ella.
CMD ["uvicorn", "analitica.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips", "*"]
