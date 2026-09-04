# Entrega 1 — Definición del proyecto

**Viernes 18 de septiembre de 2026** · Con presentación · Hito `E1 — Definición`

Es la entrega más fácil de subestimar. No se evalúa código: se evalúa si el equipo sabe qué va a construir, quién hace qué y con qué evidencia sostiene sus decisiones. Un equipo que llega con buenas intenciones y sin números pierde puntos aquí y arrastra la duda todo el semestre.

---

## Qué se entrega

| Pieza | Quién la arma | De dónde sale |
|---|---|---|
| Documento de definición del proyecto | A consolida | Protocolo de investigación ya escrito |
| Tabla de integrantes y responsabilidades | A | `docs/equipo/cronograma.md`, sección de roles |
| Cronograma con las 14 semanas | A | `docs/equipo/cronograma.md` |
| Informe de perfilado de la fuente | A | `docs/datos/informe-perfilado-v0.md` |
| ADR 001 sobre la fuente de datos | Equipo | `docs/adr/001-fuente-de-datos.md` |
| Prototipo navegable en Figma | D | Enlace |
| Repositorio funcionando | B | `github.com/arik36/canastamx` |
| Presentación | Todos | Drive |

---

## Qué aporta cada quien

**A · Ariadne** — El informe de perfilado cerrado, con el recorte geográfico y de productos justificado con números. Es la pieza que distingue a este equipo: mientras otros dicen "vamos a usar datos de PROFECO", ustedes dicen "la fuente tiene 340 mil filas, 12% de nulos en marca, 47 variantes de escritura para 'leche entera 1L', y por eso acotamos a estos tres estados".

**B · Ari Adair** — El repositorio levanta con `docker compose up` y la guía de arranque está verificada por alguien que no es él. En la presentación, esto se demuestra en vivo o con video de 30 segundos.

**C1 · Liseth** — Diagrama de clases del modelo de dominio y el servicio de Spring Boot respondiendo en `/health`.

**C2 · Oscar** — El diccionario de datos de QQP documentado y la app móvil arrancando con el sistema de diseño aplicado.

**D · Karen** — Prototipo navegable de las ocho vistas. Es lo que hace tangible el proyecto para quien no lee código.

---

## Qué revisa el asesor

Basado en la estructura del protocolo y en los criterios institucionales:

- [ ] **Planteamiento del problema** con datos y estadísticas que lo sostengan, no con opiniones.
- [ ] **Objetivo general** con verbo medible, y objetivos específicos con criterio de cumplimiento verificable.
- [ ] **Hipótesis** enunciadas de forma contrastable, con su variable y su criterio.
- [ ] **Alcances y limitaciones** explícitos: qué sí y qué no.
- [ ] **Responsabilidades repartidas**, con nombre y apellido por componente.
- [ ] **Cronograma realista**, con fechas que caen en días hábiles y entregas alineadas al calendario institucional.
- [ ] **Referencias** en formato consistente.

La pregunta que casi siempre aparece: *"¿y cómo van a saber si funcionó?"* La respuesta está en la tabla de las cuatro hipótesis: H1 contención ≥95%, H2 detección <15 min, H3 cobertura ≥85% y precisión ≥90%, H4 correlación positiva contra el INPC. Que la sepan decir los cinco, no solo A.

---

## Guión de presentación sugerido — 10 minutos

| Min | Quién | Qué |
|---|---|---|
| 0–2 | A | El problema: los datos de precios existen pero no son utilizables, y los flujos de datos fallan en silencio. Un dato duro de cada cosa. |
| 2–3 | A | Qué se va a construir, en una frase y un diagrama. |
| 3–5 | A | Qué encontramos en la fuente. **Números, no adjetivos.** |
| 5–6 | D | Cómo se va a ver. Prototipo navegable en pantalla. |
| 6–7 | B | Cómo se levanta. Demostración o video corto. |
| 7–8 | C1 y C2 | Modelo de dominio y app móvil. |
| 8–10 | A | Las cuatro hipótesis y cómo se van a contrastar. Cronograma. |

---

## Checklist de cierre — se revisa el miércoles 16, no el jueves 17

- [ ] Todas las ramas de las semanas 1 a 3 incorporadas a `main`, integración continua en verde
- [ ] `docs/entregas/2026-09-18/` existe con un archivo de texto que enlaza el documento en Drive
- [ ] El documento en Word tiene índice automático generado con estilos de título, no escrito a mano
- [ ] Portada según el formato institucional
- [ ] Los cinco nombres completos y correctos en la tabla de responsabilidades
- [ ] El prototipo de Figma abre desde el enlace **en modo incógnito** (permisos de compartir bien puestos)
- [ ] Presentación ensayada una vez completa, cronometrada
- [ ] Bitácora exportada del tablero, con el semáforo de las semanas 1 a 3

---

## El error clásico de esta entrega

Presentar el cronograma como una lista de buenas intenciones. Lo que convence es la relación entre el perfilado y el resto: *"medimos la fuente, encontramos esto, y por eso el alcance es este y no otro"*. Esa es la diferencia entre un plan y una promesa.
