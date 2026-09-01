# CanastaMX

Plataforma de inteligencia de precios de canasta basica con validacion
automatica de calidad de datos.

## Que hace

Toma los datos publicos de precios de PROFECO, los procesa mediante un flujo
con contratos de datos y compuertas de calidad, y los expone a tres perfiles:
consumidor (movil), analista (web) y operador de datos (consola de
observabilidad).

Cuando llega un dato defectuoso, el sistema lo bloquea, lo aisla en una tabla
de cuarentena con el motivo y senala el incidente. No lo deja pasar.

## Arquitectura

Cuatro componentes desplegables de forma independiente detras de un gateway:

| Componente | Ruta | Stack | Responsable |
|---|---|---|---|
| Plataforma de datos | `services/data-platform` | Python, Dagster, dbt, Pandera | A |
| Interfaz analitica | `services/analytics-api` | Python, FastAPI | A |
| Servicio de dominio | `services/domain-service` | Java 21, Spring Boot | C |
| Cliente web | `clients/web` | Next.js, TypeScript | D |
| Cliente movil | `clients/mobile` | React Native, Expo | C |
| Infraestructura | `infra/`, `docker-compose.yml` | Docker, Traefik, GH Actions | B |

## Como levantarlo

Requisitos: Docker Desktop y Git. En Windows, Docker Desktop con backend WSL2.

```bash
git clone <url-del-repo>
cd canastamx
cp .env.example .env     # completa los valores
docker compose up -d
```

Servicios disponibles despues del arranque:

| Servicio | URL |
|---|---|
| MinIO (consola) | http://localhost:9001 |
| Adminer (bases de datos) | http://localhost:8080 |

> Esta seccion se verifica de verdad: alguien que no sea B clona en una
> maquina limpia y sigue estos pasos sin preguntar nada. Si se atora, el
> README esta incompleto.

## Estructura del repositorio

```
docs/         documentacion tecnica (Markdown, no Word)
contracts/    contratos de datos en YAML
services/     los tres servicios de backend
clients/      web y movil
packages/     codigo compartido entre clientes
infra/        contenedores, gateway, scripts de operacion
```

## Convenciones

- Ramas: `tipo/iniciales-descripcion-corta` (ej. `feat/alm-ingesta-profeco`)
- Commits: `tipo(ambito): descripcion en presente`
- Nadie escribe directo en `main`. Todo entra por PR con una aprobacion.
- Decisiones tecnicas: un archivo corto en `docs/adr/`.

## Equipo

| | Integrante | Rol |
|---|---|---|
| A | Macias Campos Ariadne Lizett | Datos y plataforma |
| B | Soto Garnica Ari Adair | Infraestructura, entrega continua y calidad |
| C | Liseth Yareth Lara Lopez y Fonseca Ríos Oscar Renato | Dominio y cliente movil |
| D | Herrera Villalpando Karen Alejandra | Cliente web y maquetacion |

## Fuentes de datos

- PROFECO — Quien es Quien en los Precios: https://datos.profeco.gob.mx
- INEGI — Indice Nacional de Precios al Consumidor

## Documentacion

- Tecnica: carpeta `docs/`
- Entregas y presentaciones: (enlace al Drive compartido)
