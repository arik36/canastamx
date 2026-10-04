# CU-01 · Ingerir un lote de la fuente a la capa cruda

- **Actor primario:** el orquestador de la plataforma de datos (actor automático)
- **Interesados:**
  - **Operador de datos** — necesita que cada lote entre completo o no entre, nunca
    a medias, y saber por qué cuando no entra.
  - **Analista** — necesita que la capa cruda tenga todas las quincenas del
    alcance, sin huecos ni filas repetidas.
  - **Equipo del experimento** — necesita volver a ingerir un lote y obtener
    exactamente lo mismo.
- **Precondiciones:**
  1. Existe `contracts/qqp-v1.yaml` en su versión vigente, que declara la
     codificación, el formato de fecha y el alcance.
  2. El almacenamiento de objetos está arriba y el bucket de la capa cruda existe.
  3. El archivo de la quincena está descargado y su nombre sigue el de la fuente
     (`MM-AAAA_01` o `MM-AAAA_Q1`).
- **Disparador:** PROFECO publica una quincena nueva y el orquestador descarga el
  archivo.

## Flujo principal

1. El orquestador entrega el archivo al proceso de ingesta.
2. El proceso lo lee con la codificación y el formato de fecha que el contrato
   declara para ese archivo.
3. El proceso revisa que ningún texto traiga caracteres de control C1.
4. El proceso revisa que `estado` y `catalogo` no traigan `?`.
5. El proceso recorta al alcance: 7 entidades, 5 catálogos y la ventana del
   2025-01-01 al 2026-07-31.
6. El proceso comprueba que todas las filas son de la quincena del lote.
7. El proceso escribe las filas en la capa cruda como Parquet, una partición por
   entidad y quincena.
8. El proceso cuenta lo que quedó escrito y lo compara con lo que leyó.
9. El proceso registra la corrida: archivo, huella sha256, filas leídas, filas
   dentro del alcance, filas fuera por cada motivo, particiones y duración.
10. El orquestador dispara la validación del lote (CU-02).

## Flujos alternos

**2a · La fecha no se puede leer con el formato del contrato**
1. El proceso no ingiere el lote y dice cuántas filas fallaron y qué formato
   esperaba.
2. El caso de uso termina sin éxito.

**3a · Algún texto trae caracteres de control C1**
1. El lote completo va a cuarentena: el contrato dice `al_fallar:
   cuarentena_del_lote`, porque un lote ilegible no se ingiere a medias.
2. El proceso levanta un incidente con el número de filas y tres ejemplos (CU-04).
3. El caso de uso termina sin éxito.

**4a · `estado` o `catalogo` traen `?`**
1. El proceso se detiene. Con un `?` en esos campos no se puede saber si la fila es
   del alcance, y filtrarla la perdería sin dejar rastro.
2. El proceso levanta un incidente con los valores afectados (CU-04).
3. El caso de uso termina sin éxito, hasta que el diccionario del contrato traiga
   la reparación.

**6a · Hay filas de otra quincena**
1. El proceso se detiene: escribirlas borraría lo que otro lote dejó en esa
   partición.
2. El proceso dice cuántas filas son y de qué quincena.
3. El caso de uso termina sin éxito.

**6b · El nombre del archivo no dice su quincena**
1. El proceso pide la quincena como parámetro.
2. Con el parámetro, continúa en el paso 6. Sin él, el caso de uso termina sin
   éxito.

**7a · El lote ya se había ingerido**
1. El proceso borra las particiones de ese lote antes de escribir.
2. Continúa en el paso 7. El resultado es el mismo que la primera vez.

**8a · Lo escrito no coincide con lo leído**
1. El proceso borra las particiones del lote y marca la corrida como fallida.
2. El proceso levanta un incidente (CU-04).
3. El caso de uso termina sin éxito.

## Postcondiciones

- **De éxito:** la capa cruda tiene las filas del alcance del lote en sus
  particiones; lo escrito coincide con lo leído; la corrida quedó registrada.
- **De fallo:** la capa cruda no tiene ninguna fila del lote; el motivo quedó
  escrito; hay un incidente abierto, salvo en 2a y 6b, donde el motivo lo muestra
  la propia corrida.

## Requisito no funcional asociado

- **Volver a ingerir no duplica nada.** Tras las 38 corridas del alcance, el
  bucket guarda **2,658,906 filas, exactamente las que se leyeron** (consolidado
  del 2 de octubre: `CUADRA`).
- **Ningún lote queda a medias:** 0.

## Notas

- Implementado en `services/data-platform/ingestion/ingesta.py` (T020 y #126).
  Las pruebas de los alternos 3a, 4a, 6a y 6b están en
  `services/data-platform/tests/test_ingesta.py`.
- La capa cruda no repara ni deduplica: eso es de CU-02 y CU-03.
- Los dos archivos de mayo de 2026 vienen en latin-1; el contrato los declara como
  excepción.
