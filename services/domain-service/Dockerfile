# El servicio de dominio en su contenedor (T054 · #201). Lo revisa C1.
#
# Se construye desde esta carpeta:
#   docker build -t canastamx/domain-service services/domain-service
# En el despliegue lo construye infra/envs/prod/docker-compose.yml, en la propia
# VM: Ampere A1 es arm64, y las dos imágenes base existen para arm64 y amd64.
#
# La base de datos no se escribe aquí. application.properties apunta a
# localhost, que dentro del contenedor es el contenedor mismo; el despliegue la
# cambia con SPRING_DATASOURCE_URL, sin tocar el código.

# ── 1 · Compilar ──────────────────────────────────────────────────────────────
FROM eclipse-temurin:21-jdk AS construccion
WORKDIR /fuente
COPY .mvn/ .mvn/
COPY mvnw pom.xml ./
COPY src/main/ src/main/
# Sin pruebas: ya corren en la CI («Dominio (Java)»), contra PostgreSQL. La caché
# de Maven sobrevive entre construcciones: volver a desplegar no baja todo otra vez.
RUN --mount=type=cache,target=/root/.m2 \
    ./mvnw -B -q package -Dmaven.test.skip=true -Djacoco.skip=true \
 && cp target/domain-service-*.jar /servicio.jar

# ── 2 · Correr ────────────────────────────────────────────────────────────────
FROM eclipse-temurin:21-jre
RUN groupadd --system servicio && useradd --system --gid servicio --no-create-home servicio
WORKDIR /servicio
COPY --from=construccion /servicio.jar app.jar
USER servicio
EXPOSE 8081
ENTRYPOINT ["java", "-jar", "app.jar"]
