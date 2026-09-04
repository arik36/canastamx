# Cronograma rebaseado — CanastaMX

**Rebase del 2 de septiembre de 2026.** La semana 1 se comprime en jueves 3, viernes 4 y lunes 7. **Ninguna entrega institucional se mueve.** Las semanas 2 a 14 conservan sus fechas originales.

Qué cambió respecto al manual original:

| | Manual original | Rebase |
|---|---|---|
| Semana 1 | lun 31 ago – vie 4 sep, cinco días | jue 3 – lun 7 sep, tres días de trabajo |
| Reunión de decisión | viernes 4 de septiembre | **lunes 7 de septiembre** |
| Se recorre a semana 2 | — | sistema de diseño (D) y cierre del modelo de dominio (C1) |
| Entregas institucionales | 18 sep · 9 oct · 4 nov · 18 nov · 2, 7 y 9 dic | **idénticas** |

---

## Los cinco roles

El manual definía cuatro. El integrante C son dos personas, lo que rompe la regla de "ningún componente tiene dos dueños". Se parte en dos frentes con dueño único cada uno:

| | Quién | Iniciales | Frente | Suplente |
|---|---|---|---|---|
| **A** | Ariadne Lizett Macías Campos | `alm` | Datos y plataforma | B |
| **B** | Ari Adair Soto Garnica | `aas` | Infraestructura, entrega continua y calidad | A |
| **C1** | Liseth Yareth Lara López | `lyl` | Servicio de dominio (Java, Spring Boot) | C2 |
| **C2** | Oscar Renato Fonseca Ríos | `orf` | Cliente móvil (React Native, Expo) | C1 y D |
| **D** | Karen Alejandra Herrera Villalpando | `kah` | Cliente web y maquetación | C2 |

C1 y C2 comparten el contrato OpenAPI del servicio de dominio: C1 lo publica, C2 lo consume. Es su punto de acuerdo y su punto de fricción; se revisa en cada reunión semanal.

> Si Liseth y Oscar prefieren el reparto al revés, cámbienlo **en la reunión del lunes 7 y no después**. Lo que no es negociable es que cada frente tenga un solo dueño.

---

## Fechas que no se mueven

| Fecha | Día | Qué se entrega |
|---|---|---|
| **18 de septiembre** | viernes | Definición del proyecto, integrantes y responsabilidades. Con presentación. |
| **9 de octubre** | viernes | Documento de análisis: requerimientos, 14 casos de uso, BPMN, prototipo navegable. |
| **4 de noviembre** | miércoles | Avance de construcción: cuatro suites de pruebas demostradas. |
| **18 de noviembre** | miércoles | Versión final desplegada. **A partir de aquí, congelamiento de funcionalidad.** |
| **2, 7 y 9 de diciembre** | mié, lun, mié | Presentaciones finales. |

El **16 de noviembre es festivo** y cae dos días antes de la entrega final. Esa semana se planea con capacidad reducida: lo que se pueda cerrar el viernes 13, se cierra el viernes 13.

---

## Semana 1 comprimida — jueves 3 a lunes 7 de septiembre

**Objetivo único:** decidir si la fuente de PROFECO sirve. Si el archivo no tiene lo que suponemos, hay que saberlo ahora y no en octubre, cuando ya no haya margen para cambiar de rumbo.

### Jueves 3 de septiembre — día doble

| Quién | Actividad | Cómo saber que quedó |
|---|---|---|
| A | Termina la estructura del repositorio: carpetas con `.gitkeep`, `.gitignore`, README inicial, `main` protegida, los cuatro colaboradores invitados. Crea el tablero en GitHub Projects. | Los cinco clonan y ven la misma estructura. `git status` limpio en las cinco máquinas. |
| A | Localiza el conjunto QQP en el portal de PROFECO. Descarga el archivo más reciente y el de 2025. Verifica que abren; anota tamaño y formato. | Los archivos abren. Tamaño y formato anotados en `docs/datos/fuente-qqp.md`. |
| A | **Perfilado nivel 1.** Filas, columnas, tipos de dato reales, porcentaje de nulos por columna, rango de fechas, entidades federativas presentes. | Cuaderno con tabla de resultados en `docs/datos/perfilado/`. |
| B | `docker-compose.yml` con cuatro servicios: `postgres-oltp`, `postgres-analytics`, `minio`, `adminer`. | `docker compose up` levanta los cuatro sin error. MinIO y Adminer abren en el navegador. |
| C1 | Instala JDK 21 y Maven. Esqueleto de Spring Boot con las tres capas separadas y un endpoint de salud. | `GET /health` responde. Arranca con `mvn spring-boot:run`. |
| C2 | Descarga y lee el diccionario de datos de QQP. Anota qué columnas existen y qué significa cada una. | Existe `docs/datos/diccionario-qqp.md` con la lista de columnas y su significado. |
| D | Crea el archivo de Figma. Inventario de las ocho vistas con una línea de contenido cada una. | Enlace de Figma en el README; inventario en `docs/analisis/inventario-vistas.md`. |

### Viernes 4 de septiembre

| Quién | Actividad | Cómo saber que quedó |
|---|---|---|
| A | **Perfilado nivel 2.** Distribución de precios: mínimo, máximo, mediana y percentiles por categoría. Precios en cero, negativos o absurdos. Duplicados exactos. Cuántos establecimientos y cadenas. | La sección de rangos y anomalías está escrita con números concretos, no con adjetivos. |
| A | **Perfilado nivel 3, el crítico.** Cuántas formas distintas de escribir aparecen para un mismo producto. Veinte productos comunes, contando variantes entre cadenas. | Tabla de variantes por producto, con el conteo de los veinte. **Este número decide si la meta de 85% de cobertura de H3 es realista o hay que ajustarla.** |
| B | Traefik en el archivo de composición, enrutamiento local por nombre de servicio. Crea `.env.example`. Integración continua mínima: análisis estático y compilación al abrir una solicitud. | Los servicios responden por nombre de dominio local. Una solicitud de prueba dispara la canalización y sale en verde. |
| B | Registro en Oracle Cloud y solicitud del GitHub Student Pack. | Ambos registros enviados, con captura del acuse. |
| C1 | Primer borrador del modelo de dominio: qué son entidades, qué son objetos de valor, dónde están los límites de los agregados Usuario, Canasta y Alerta. | Existe `docs/analisis/modelo-dominio.md` con la lista y su justificación. |
| C2 | Instala Node 20 y Expo. Proyecto móvil base que arranca en un teléfono real o emulador, con navegación entre dos pantallas vacías. | La app abre en el teléfono de Oscar. Captura en el issue. |
| D | Wireframe de baja fidelidad del tablero analítico y de la consola de observabilidad. La consola se revisa **con A** antes de darla por buena: los seis indicadores tienen que leerse de un vistazo. | Los dos wireframes existen en Figma. A dio su visto bueno por escrito en el issue. |

### Sábado 5 y domingo 6 — colchón

Sin trabajo planeado para nadie, con una excepción: **A redacta el informe de perfilado versión cero**, porque de ese informe depende la reunión del lunes. Es la única tarea de fin de semana del semestre y recae en quien la propuso.

`docs/datos/informe-perfilado-v0.md`, tres secciones y una conclusión explícita: **la fuente sirve, o no sirve, y por qué.**

### Lunes 7 de septiembre — reunión de decisión

La reunión más importante del semestre. Cuarenta y cinco minutos, los cinco presentes, cámara encendida.

| Quién | Actividad | Cómo saber que quedó |
|---|---|---|
| A | Presenta el informe de perfilado. No es una lectura: es una recomendación con números que la sostienen. | Los cinco entienden qué tan sucia está la fuente y qué implica para el alcance. |
| Equipo | **Decisión de continuar o no.** Si la fuente sirve, se fija el recorte geográfico definitivo con datos en mano, no con suposiciones. Si no sirve, se activa el plan alternativo: base 2025 más recolección propia acotada de dos o tres cadenas. | La decisión queda escrita en `docs/adr/001-fuente-de-datos.md` con fecha, contexto, decisión y alternativas descartadas. |
| Equipo | Cada quien incorpora su avance mediante solicitud, revisada por otro integrante. | Cinco solicitudes incorporadas a `main`, integración continua en verde. |
| Equipo | Se cargan al tablero las tareas de la semana 2 y se acuerda el **horario fijo** de la reunión semanal. | El tablero tiene la columna de la semana 2 poblada y la reunión está en el calendario de los cinco. |

### Lista de verificación al cierre

- [ ] Repositorio con estructura completa, `.gitignore`, README inicial y `main` protegida.
- [ ] Los cinco clonaron y ven lo mismo.
- [ ] `docker compose up` levanta cuatro servicios en la máquina de al menos dos integrantes.
- [ ] Informe de perfilado v0 en `docs/datos/`, con conclusión explícita.
- [ ] `docs/adr/001-fuente-de-datos.md` escrito, con fecha.
- [ ] Recorte geográfico y de productos definido con base en datos reales.
- [ ] Cuentas de Oracle Cloud y GitHub Student Pack solicitadas.
- [ ] Diccionario QQP documentado.
- [ ] Inventario de ocho vistas y dos wireframes en Figma.
- [ ] Modelo de dominio en primer borrador.
- [ ] Proyecto móvil base arrancando.
- [ ] Tablero con las tareas de la semana 2 y horario fijo de reunión acordado.

---

## Fase 1 — Exploración y definición

### Semana 2 · 8 al 13 de septiembre

| Quién | Actividad | Queda en |
|---|---|---|
| A | Contrato de datos versión uno para QQP en YAML: columnas, tipos, obligatoriedad, rangos y umbral de frescura. Primer guión de ingesta que descarga el archivo y lo guarda como Parquet particionado en MinIO. | `contracts/`, `services/data-platform/ingestion/` |
| B | Separa entornos de desarrollo y pruebas. Manejo de secretos. Extiende la integración continua para que corra `pytest`. | `infra/envs/`, `.github/workflows/` |
| C1 | Cierra el modelo de dominio: atributos de cada entidad y reglas de negocio dentro del agregado. Estructura el servicio en capas. Implementa Usuario y Canasta con sus reglas. | `docs/analisis/`, `services/domain-service/` |
| C2 | Navegación completa de la app con las cuatro pantallas vacías: búsqueda, detalle, mi canasta, alertas. | `clients/mobile/` |
| D | Sistema de diseño mínimo en Figma: paleta, tipografía y componentes base, aplicado a los wireframes existentes. Completa los wireframes de las ocho vistas. | Figma, enlace en `docs/analisis/` |

### Semana 3 · 14 al 20 de septiembre — **entrega del 18**

| Quién | Actividad | Queda en |
|---|---|---|
| A | Cierra el informe de perfilado. Documenta el recorte definitivo con su justificación cuantitativa. | `docs/datos/` |
| B | Escribe y **verifica** la guía de arranque: otro integrante clona en máquina limpia y levanta sin preguntar nada. | `README.md` |
| C1 | Diagrama de clases del modelo de dominio. | `docs/analisis/` |
| C2 | Prototipo móvil navegable con el sistema de diseño de D aplicado. | `clients/mobile/`, Figma |
| D | Prototipo navegable presentable. | Figma |
| Equipo | **Entrega del 18 de septiembre** + presentación. | `docs/entregas/2026-09-18/` |

---

## Fase 2 — Requerimientos, análisis y diseño

### Semana 4 · 21 al 27 de septiembre

| Quién | Actividad | Queda en |
|---|---|---|
| A | Modelo dimensional completo: declaración de grano, tabla de hechos, cuatro dimensiones, agregados y diccionario. Requerimientos no funcionales de datos: frescura, completitud, latencia. | `docs/datos/modelo-dimensional.md` |
| B | Estrategia de ramas y plantilla de solicitudes. Organiza el tablero por iteración. | `.github/`, GitHub Projects |
| C1 | Casos de uso CU-08 a CU-11 en formato completo (Cockburn). | `docs/analisis/casos-uso/` |
| C2 | Caso de uso CU-12 en formato completo. | `docs/analisis/casos-uso/` |
| D | CU-13 y CU-14. Inicia la maquetación de alta fidelidad. | `docs/analisis/casos-uso/`, Figma |

### Semana 5 · 28 de septiembre al 4 de octubre

| Quién | Actividad | Queda en |
|---|---|---|
| A | CU-01 a CU-07. Diagrama BPMN del proceso de ingesta y del proceso de atención de incidentes. | `docs/analisis/` |
| B | Coordina el acuerdo de los contratos OpenAPI entre los tres servicios, para que nadie construya contra una interfaz imaginaria. | `docs/analisis/openapi/` |
| C1 | BPMN del proceso de alerta y notificación. Modelo entidad-relación de la base transaccional. | `docs/analisis/` |
| C2 | Consume el OpenAPI del dominio desde la app: primera llamada real. | `clients/mobile/` |
| D | Cierra el prototipo navegable. Define los tres puntos de quiebre y el comportamiento en cada uno. | Figma, `docs/analisis/` |

### Semana 6 · 5 al 11 de octubre — **entrega del 9**

| Quién | Actividad | Queda en |
|---|---|---|
| Equipo | Consolidan el documento de análisis. **Revisión cruzada:** cada quien revisa el trabajo de otro, no el propio. | `docs/entregas/2026-10-09/` |

---

## Fase 3 — Construcción

### Semana 7 · 12 al 18 de octubre

| Quién | Actividad | Queda en |
|---|---|---|
| A | Ingesta operando de extremo a extremo hasta la capa cruda. Pandera validando el contrato en el momento de la ingesta. | `services/data-platform/` |
| B | La integración continua corre las tres suites existentes. Guión de carga de datos semilla. | `.github/`, `infra/scripts/` |
| C1 | Autenticación con token funcionando. Endpoints de canasta. | `services/domain-service/` |
| C2 | Pantalla de acceso conectada a la autenticación real de C1. | `clients/mobile/` |
| D | Estructura de la aplicación web con acceso y navegación. | `clients/web/` |

### Semana 8 · 19 al 25 de octubre

| Quién | Actividad | Queda en |
|---|---|---|
| A | Transformaciones de capa cruda a intermedia en dbt: tipado, deduplicación y normalización. Primeras pruebas de dbt. | `services/data-platform/dbt/` |
| B | Monta el entorno de pruebas aislado que usará el experimento. | `infra/envs/test/` |
| C1 | Alertas y notificaciones. Pruebas unitarias con JUnit. | `services/domain-service/` |
| C2 | Pantalla de búsqueda con datos reales. | `clients/mobile/` |
| D | Tablero analítico consumiendo la interfaz analítica con datos simulados. | `clients/web/` |

### Semana 9 · 26 de octubre al 1 de noviembre

| Quién | Actividad | Queda en |
|---|---|---|
| A | Capa intermedia a capa de consumo: esquema estrella cargado. Reconciliación de productos versión uno. | `services/data-platform/` |
| B | Prepara la máquina virtual en la nube y realiza el primer despliegue. | `infra/` |
| C1 | Cobertura de pruebas de la lógica de dominio. | `services/domain-service/` |
| C2 | Móvil: pantalla de canasta operando. | `clients/mobile/` |
| D | Vista de detalle de producto. Comportamiento responsivo en los tres puntos de quiebre. | `clients/web/` |

### Semana 10 · 2 al 8 de noviembre — **entrega del 4**

| Quién | Actividad | Queda en |
|---|---|---|
| A | Interfaz analítica con cuatro endpoints. Mide cobertura y precisión de la reconciliación sobre muestra de 200 pares. | `services/analytics-api/`, `docs/datos/` |
| B | Configura Playwright. Primeras pruebas automatizadas de interfaz. | `clients/web/tests/` |
| C1 | Cierra cobertura de pruebas unitarias del dominio. | `services/domain-service/` |
| C2 | Pruebas de integración de la app móvil. | `clients/mobile/` |
| D | Pruebas de manejo de sesión y navegabilidad. | `docs/entregas/2026-11-04/` |

---

## Fase 4 — Calidad, observabilidad e integración

### Semana 11 · 9 al 15 de noviembre

| Quién | Actividad | Queda en |
|---|---|---|
| A | **Compuertas de calidad y tabla de cuarentena operando:** un registro defectuoso ya no llega a la capa de consumo. Integración de la fuente de inflación de INEGI. | `services/data-platform/` |
| B | Despliegue continuo automatizado. Traefik con certificados. Datos de prueba cargados en ambas bases. | `infra/`, `.github/` |
| C1 | Notificaciones por correo. | `services/domain-service/` |
| C2 | Móvil: pantalla de alertas. Genera el primer build instalable. | `clients/mobile/` |
| D | Consola de observabilidad conectada a los seis indicadores reales. | `clients/web/` |

### Semana 12 · 16 al 22 de noviembre — **entrega del 18** · lunes 16 festivo

| Quién | Actividad | Queda en |
|---|---|---|
| A | Cierra la consola. Calcula el índice de canasta, la dispersión de precios y la correlación contra el INPC. | `services/analytics-api/`, `docs/datos/` |
| B | Suite de pruebas de integración entre front y back en verde. Construye el arnés de inyección de fallas. | `infra/scripts/`, `docs/experimento/` |
| C1 | Cierra pendientes de dominio. | `services/domain-service/` |
| C2 | Build instalable definitivo, probado en dos teléfonos distintos. | `clients/mobile/` |
| D | Cola de reconciliación. Pulido responsivo final. | `clients/web/` |
| Equipo | **Entrega del 18: versión final desplegada. A partir de aquí, congelamiento de funcionalidad.** | `docs/entregas/2026-11-18/` |

---

## Fase 5 — Experimentación

### Semana 13 · 23 al 29 de noviembre

| Quién | Actividad | Queda en |
|---|---|---|
| A | Especifica las cinco tipologías de falla y el procedimiento de cada corrida. Analiza resultados: tasa de detección, tasa de contención, latencia media. Contrasta las cuatro hipótesis. Redacta el reporte de hallazgos económicos. | `docs/experimento/` |
| B | **Ejecuta las treinta corridas** sobre el entorno aislado, más las corridas de control con las validaciones desactivadas. Registra las tres variables por corrida. | `docs/experimento/bitacora.csv` |
| C1 | Documentación técnica del dominio y manual de operación. | `docs/` |
| C2 | Documentación de la app móvil y capturas para la presentación. | `docs/` |
| D | Documentación de la interfaz web. Capturas para la presentación. | `docs/` |

---

## Fase 6 — Cierre y presentación

### Semana 14 · 30 de noviembre al 6 de diciembre

| Quién | Actividad | Queda en |
|---|---|---|
| Equipo | Guión de demostración escrito y **ensayado dos veces completas**. | `docs/entregas/final/` |
| Equipo | **Video de respaldo de la demostración, grabado.** Si la red falla el día de la presentación, el video salva la calificación. | Drive, enlace en el README |
| Equipo | README final con diagrama de arquitectura. Documento de traspaso con deuda técnica conocida y líneas de continuación. | `README.md`, `docs/` |
| Equipo | Lámina de métricas: filas procesadas, validaciones activas, incidentes detectados, resultado de las cuatro hipótesis. | `docs/entregas/final/` |
| Equipo | **Presentaciones: 2, 7 y 9 de diciembre.** Presenta el responsable de cada parte. | — |

**Regla que no se negocia:** la semana 14 no lleva desarrollo de funcionalidad nueva. Los proyectos escolares no se caen construyendo, se caen presentando.

---

## Las cuatro hipótesis, para tenerlas presentes

Todo lo que se construye existe para poder contrastar esto en la semana 13:

| | Qué se mide | Se cumple si |
|---|---|---|
| **H1 Contención** | % de filas defectuosas inyectadas que quedan en cuarentena y no llegan a la capa de consumo | ≥ 95% |
| **H2 Detección** | Tiempo entre la ingesta del lote defectuoso y la señalización del incidente | < 15 minutos |
| **H3 Reconciliación** | Cobertura y precisión de la normalización de nombres entre cadenas | Cobertura ≥ 85%, precisión ≥ 90% sobre 200 pares |
| **H4 Validez del índice** | Correlación entre el índice de canasta propio y el INPC oficial | Positiva y significativa; divergencias documentadas |

El perfilado nivel 3 del viernes 4 es el que dice si H3 es alcanzable con 85% o hay que ajustar la meta **antes** de comprometerla. Ajustarla en septiembre con datos es método; ajustarla en noviembre porque no salió es otra cosa.
