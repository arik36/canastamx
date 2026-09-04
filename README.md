# CanastaMX

Plataforma de inteligencia de precios de canasta básica con validación automática de calidad de datos.

<!-- Este README nació del bootstrap que corrió B. Se conservó su estructura y
     se actualizaron tres cosas: la tabla del equipo (ya no hay "por definir"),
     los enlaces al manual de equipo, y la sección de cómo levantarlo.

     La sección "Cómo levantarlo" se verifica DE VERDAD en la semana 3:
     alguien que no sea B clona en una máquina limpia y sigue los pasos sin
     preguntar nada. Si se atora, el README está incompleto. -->

## Qué hace

Toma los datos públicos de precios de PROFECO, los procesa mediante un flujo con contratos de datos y compuertas de calidad, y los expone a tres perfiles: consumidor (móvil), analista (web) y operador de datos (consola de observabilidad).

Cuando llega un dato defectuoso, el sistema lo bloquea, lo aísla en una tabla de cuarentena con el motivo y señala el incidente. No lo deja pasar.

## Arquitectura

Componentes desplegables de forma independiente detrás de una puerta de enlace:

| Componente | Ruta | Tecnologías | Responsable |
|---|---|---|---|
| Plataforma de datos | `services/data-platform` | Python, Dagster, dbt, Pandera | A |
| Interfaz analítica | `services/analytics-api` | Python, FastAPI | A |
| Servicio de dominio | `services/domain-service` | Java 21, Spring Boot | C1 |
| Cliente web | `clients/web` | Next.js, TypeScript | D |
| Cliente móvil | `clients/mobile` | React Native, Expo | C2 |
| Infraestructura | `infra/`, `docker-compose.yml` | Docker, Traefik, GitHub Actions | B |

## Cómo levantarlo

Requisitos: Docker Desktop y Git. En Windows, Docker Desktop con backend WSL2.

```bash
git clone https://github.com/arik36/canastamx.git
cd canastamx
cp .env.example .env     # completa los valores vacíos
docker compose up -d
docker compose ps        # los servicios deben decir running / healthy
```

Servicios disponibles después del arranque:

| Servicio | URL |
|---|---|
| MinIO (consola) | http://localhost:9001 |
| Adminer (bases de datos) | http://localhost:8080 |

Los puertos se cambian en el `.env` si alguno ya está ocupado en tu máquina.

> Esta sección se verifica de verdad: alguien que no sea B clona en una máquina limpia y sigue estos pasos sin preguntar nada. Si se atora, el README está incompleto.

## Antes de crear tu primera rama

```bash
git switch main && git pull
bash infra/scripts/verificar-base.sh C1   # tu clave: A · B · C1 · C2 · D
```

Te dice si tu copia tiene la línea base y si tus herramientas están instaladas. Si dice que todavía no ramifiques, no ramifiques: el detalle está en [`docs/equipo/linea-base.md`](docs/equipo/linea-base.md).

## Estructura del repositorio

```
docs/         documentación técnica en Markdown, no en Word
  equipo/     manual de operación, cronograma y fichas de tarea
contracts/    contratos de datos en YAML
services/     los tres servicios de backend
clients/      web y móvil
packages/     código compartido entre clientes
infra/        contenedores, puerta de enlace y guiones de operación
```

## Convenciones

- **Ramas:** `tipo/iniciales-descripcion-corta` — por ejemplo `feat/alm-ingesta-profeco`
- **Commits:** `tipo(ámbito): descripción en presente`
- **Nadie escribe directo en `main`.** Todo entra por solicitud con una aprobación.
- **Decisiones técnicas:** un archivo corto en `docs/adr/`.
- **Si una tarea no está en el tablero, no existe.**

El detalle, con comandos para terminal y para GitHub Desktop, está en [`docs/equipo/git-paso-a-paso.md`](docs/equipo/git-paso-a-paso.md).

## Equipo

| | Integrante | Iniciales | Rol |
|---|---|---|---|
| A | Macías Campos Ariadne Lizett | `alm` | Datos y plataforma |
| B | Soto Garnica Ari Adair | `aas` | Infraestructura, entrega continua y calidad |
| C1 | Lara López Liseth Yareth | `lyl` | Servicio de dominio |
| C2 | Fonseca Ríos Oscar Renato | `orf` | Cliente móvil |
| D | Herrera Villalpando Karen Alejandra | `kah` | Cliente web y maquetación |

Quién hace qué cada semana, con su criterio de cierre: [`docs/equipo/cronograma.md`](docs/equipo/cronograma.md).

## Fuentes de datos

- **PROFECO** — Quién es Quién en los Precios: https://datos.profeco.gob.mx
- **INEGI** — Índice Nacional de Precios al Consumidor

## Documentación

| Qué | Dónde |
|---|---|
| **Cómo trabajamos** | [`docs/equipo/README.md`](docs/equipo/README.md) — índice del manual |
| Fichas de tarea de la semana | [`docs/equipo/fichas/`](docs/equipo/fichas/) |
| Decisiones de arquitectura | [`docs/adr/`](docs/adr/) |
| Documentos de entrega y presentaciones | Drive compartido <!-- enlace --> |
| Prototipo de las vistas | Figma <!-- enlace --> |
