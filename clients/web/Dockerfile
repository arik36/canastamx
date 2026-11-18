# El cliente web en su contenedor (T054 · #201). Lo revisa D.
#
# Se construye desde esta carpeta:
#   docker build -t canastamx/web clients/web
# En el despliegue lo construye infra/envs/prod/docker-compose.yml, que le pasa
# DOMINIO_URL=http://domain-service:8081. La web llama al dominio desde su
# servidor, nunca desde el navegador, así que esa dirección no sale de la VM.
#
# La construcción necesita red: next/font baja la fuente Inter de Google Fonts.

# ── 1 · Construir ─────────────────────────────────────────────────────────────
FROM node:22-slim AS construccion
WORKDIR /web
ENV NEXT_TELEMETRY_DISABLED=1
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
# Después de construir, sólo quedan las dependencias de producción.
RUN npm run build \
 && npm prune --omit=dev --no-audit --no-fund \
 && rm -rf .next/cache

# ── 2 · Servir ────────────────────────────────────────────────────────────────
FROM node:22-slim
WORKDIR /web
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1
COPY --from=construccion --chown=node:node /web/package.json /web/next.config.ts /web/tsconfig.json ./
COPY --from=construccion --chown=node:node /web/node_modules ./node_modules
COPY --from=construccion --chown=node:node /web/.next ./.next
USER node
EXPOSE 3000
CMD ["node_modules/.bin/next", "start", "-H", "0.0.0.0", "-p", "3000"]
