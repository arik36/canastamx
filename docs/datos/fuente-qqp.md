# Fuente de datos · Quién es Quién en los Precios

<!-- Este archivo tiene como proposito llenar T002 (A) · lunes 7 de septiembre.
     Todo lo de aquí se MIDE, no se supone. Verifica con la terminal, no con Excel:
     Excel corta en 1,048,576 filas sin avisar. -->

**Última revisión:** 7 de septiembre de 2026 · **Responsable:** A

## Dónde está

| Recurso | URL | Para qué |
|---|---|---|
| Portal de datos abiertos | https://datos.profeco.gob.mx/datos_abiertos/ | Aquí están los archivos |
| Diccionario de datos | https://datos.profeco.gob.mx/diccionarioDatosQQP.php | Se lo pasas a C2 para T013 |
| Conjunto 2025, portal federal | https://www.datos.gob.mx/dataset/programa_quien_es_quien_precios_2025 | Serie histórica |
| Aplicación pública de consulta | https://qqp.profeco.gob.mx/ | Para contrastar. NO para descargar |

## Archivos descargados

<!-- Comandos: ls -lh · wc -l · file · head -3 -->

| Archivo | Periodo | Tamaño | Formato | Codificación | Separador | Filas | Descargado el |
|---|---|---|---|---|---|---|---|
| `QQP_2025/` (24 archivos quincenales) | 2025 completo, 2025/01/02–2025/12/31 | 3.9 GB | CSV | UTF-8 con BOM, uniforme en las 24 piezas | Coma (campos con coma propia van entre comillas) | 13,270,524 | _(poner fecha real de descarga)_ |
| `QQP_2026/` (14 archivos quincenales) | 2026 parcial, 2026/01/02–2026/07/31 | 2.4 GB | CSV | Mixta: UTF-8 con BOM en 12 de 14 piezas; ISO-8859-1 (Latin-1) en `05-2026_Q1.csv` y `05-2026_Q2.csv` | Coma | 8,087,349 | _(poner fecha real de descarga)_ |

**Dónde viven los archivos crudos:** `~/canastamx-datos/crudo/QQP_2025/` y `~/canastamx-datos/crudo/QQP_2026/` (fuera del repositorio)

## Encabezado real

```bash
head -n 1 ~/canastamx-datos/crudo/QQP_2025/01-2025_01.csv
﻿producto,presentacion,marca,categoria,catalogo,precio,fecha_registro,cadena_comercial,giro,nombre_comercial,direccion,estado,municipio,latitud,longitud
```

<!-- impresion mas estilizada -->
```bash
mlizz@GAMINGARI:~/canastamx-datos$ head -n 1 ~/canastamx-datos/crudo/QQP_2025/01-2025_01.csv | tr ',' '\n'
﻿producto
presentacion
marca
categoria
catalogo
precio
fecha_registro
cadena_comercial
giro
nombre_comercial
direccion
estado
municipio
latitud
longitud
```

<!-- el simbolo ﻿ antes de producto simboliza un espacio, es un BOM invisible delante (\ufeff). Leer con encoding="utf-8-sig" para que la columna se llame producto y no \ufeffproducto.-->

```
producto,presentacion,marca,categoria,catalogo,precio,fecha_registro,cadena_comercial,giro,nombre_comercial,direccion,estado,municipio,latitud,longitud
```

> El primer campo trae un BOM invisible delante (`\ufeff`) en todas las piezas excepto `05-2026_Q1.csv` y `05-2026_Q2.csv`. Leer con `encoding="utf-8-sig"` para que la columna se llame `producto` y no `\ufeffproducto`. Esas dos piezas de mayo van aparte, con `encoding="latin-1"`.
>
> Los nombres reales (minúsculas, con guión bajo) **no coinciden** con los del diccionario oficial (mayúsculas, pegadas: `FECHAREGISTRO`, `CADENACOMERCIAL`, `NOMBRECOMERCIAL`). Avisado a C2.

## Primeras filas

<!-- head -3 archivo.csv -->

```
Acelga,Manojo,S/m,Hortalizas Frescas,Frutas y Legumbres,19,2025/01/02,Central de Abastos,Central de Abasto,Central de Abasto,Av. Mahatma Gandhi S/n. Salida a México. Col. Central de Abasto. Cp. 20280,Aguascalientes,Aguascalientes,21.832072,-102.292976
Aguacate,1 Kg. Granel. Hass,S/m,Frutas Frescas,Frutas y Legumbres,39,2025/01/02,Central de Abastos,Central de Abasto,Central de Abasto,Av. Mahatma Gandhi S/n. Salida a México. Col. Central de Abasto. Cp. 20280,Aguascalientes,Aguascalientes,21.832072,-102.292976
```

Ejemplo de la excepción de mayo 2026 (`05-2026_Q1.csv`, `latin-1`, fecha en `DD/MM/YYYY`):

```
Jitomate,1 Kg. Granel. Saladette/huaje o Tomate Saladette/huaje. Primera,S/M,Hortalizas Frescas,Frutas y Legumbres,50,02/05/2026,Central de Abasto,Central de Abasto,Central de Abasto,Av. Mahatma Gandhi S/n. Salida a M xico. Col. Central de Abasto. Cp. 20280,Aguascalientes,Aguascalientes,21.832072,-102.292976
```

## Lo que llamó la atención al abrirlo

<!-- Una línea por cosa rara. Estas notas son el inicio del perfilado. -->

- Los nombres de columna reales (`fecha_registro`, `cadena_comercial`, `nombre_comercial`, minúsculas con guión bajo) no coinciden con el diccionario oficial de PROFECO (mayúsculas pegadas: `FECHAREGISTRO`, `CADENACOMERCIAL`, `NOMBRECOMERCIAL`). Crítico para el contrato de datos (T019), que exige nombres literales.
- El "archivo" del portal no es un CSV único: viene empaquetado en cortes quincenales — 24 piezas para 2025 (año completo), 14 piezas para 2026 (parcial, hasta la 2ª quincena de julio).
- Los cortes quincenales no caen en fecha fija de calendario, se ajustan a días hábiles (ej. agosto 2025 corta el día 29 en vez del 31; noviembre 2025 arranca el día 03 en vez del 01).
- `05-2026_Q1.csv` y `05-2026_Q2.csv` (mayo 2026) vienen en ISO-8859-1 (Latin-1) en vez de UTF-8 con BOM como el resto del corpus.
- Esos mismos dos archivos traen `fecha_registro` en formato `DD/MM/YYYY` en vez de `YYYY/MM/DD` del resto. Confirmado que el cambio es limpio a nivel de archivo completo: 100% de las filas de ambos (479,993 y 527,089 filas) siguen ese formato, sin mezcla interna fila por fila.
- `MARCA` trae `S/m` en 2025 y `S/M` en 2026 para el mismo caso (producto sin marca) — variante de escritura menor, insumo para T005.
- Aparecen archivos sueltos `*.csv:Zone.Identifier` en `QQP_2026` — son metadata de Windows/WSL ("mark of the web"), no datos. Ver `docs/equipo/fusion-con-el-repo.md`.
- `wc -l`/`awk` sobre los CSV cuadra exacto contra la suma de filas leídas por `csv.DictReader` en Python (13,270,524 y 8,087,349) — descarta campos con saltos de línea internos rompiendo el conteo por líneas.

## Periodicidad de publicación

<!-- ¿Cada cuánto publica PROFECO? De esto sale el umbral de frescura del
     contrato de datos de la semana 2. Si no está declarado, anótalo así. -->

PROFECO publica QQP en cortes quincenales: dos archivos por mes, aproximadamente días 1–15 y 16–fin de mes, pero el corte se ajusta a días hábiles y no siempre cae en el día calendario exacto. Para 2026 (año en curso), a la fecha de esta revisión el dato más reciente disponible llega hasta 2026/07/31 (2ª quincena de julio).

Pendiente de T019: confirmar cuántos días hábiles corren entre el cierre real de una quincena y su publicación en el portal, para fijar el umbral de frescura del contrato — no medido en esta tarea, requiere comparar fecha de publicación contra la fecha máxima de `fecha_registro` de cada pieza según vayan saliendo nuevas.
