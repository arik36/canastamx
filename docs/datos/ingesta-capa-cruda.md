# Ingesta a la capa cruda · evidencia de la corrida

**Generado:** 2026-09-28 por `services/data-platform/ingestion/consolidar-corridas.py` · **T020** · issue #90

> Este documento se **genera**, no se escribe a mano. Sale de los registros
> de `ingestion/corridas/`, que no entran al repositorio porque describen el
> estado de una máquina. Lo que sí entra es esto: las cifras y el `sha256`
> de cada archivo que las produjo.

---

## El resultado, en una línea

**La suma de las filas dentro del alcance da 2,658,906.** El contrato declara
`medicion.filas: 2658906`, medido el 2026-09-15 por
`docs/datos/perfilado/verificar-precios.py` sobre otra ruta y con otro código.

| | |
|---|---:|
| Ingesta · suma de los 38 archivos | **2,658,906** |
| Contrato · `medicion.filas` | **2,658,906** |
| Diferencia | **+0** |

**CUADRA al dígito.**
Dos mediciones independientes, separadas en el tiempo y hechas con
código distinto, dando el mismo número.

Filas leídas de los archivos: **21,357,873** · el alcance es el **12.45%** de eso.

## El recorte que se aplicó

Los tres que `medicion.poblacion` nombra, leídos del contrato:

- **7 entidades** · Aguascalientes, Guanajuato, Jalisco, Michoacán, Querétaro, San Luis Potosí, Zacatecas
- **5 catálogos** · BASICOS, PACIC, FRUTAS Y LEGUMBRES, MERCADOS, PESCADOS Y MARISCOS
- **ventana** · 2025-01-01 → 2026-07-31

En el bucket quedaron **7 particiones de `entidad`**: Aguascalientes, Guanajuato, Jalisco, Michoacán, Querétaro, San Luis Potosí, Zacatecas.

## Por archivo

«Fuera por» se solapan: una fila puede fallar en más de un recorte.

| lote | del archivo | fuera · estado | fuera · ventana | fuera · catálogo | **dentro** | % | objetos |
|---|---:|---:|---:|---:|---:|---:|---:|
| `01-2025_01` | 547,782 | 437,769 | 0 | 170,171 | **69,510** | 12.69% | 7 |
| `01-2025_02` | 696,182 | 549,677 | 0 | 223,153 | **92,284** | 13.26% | 7 |
| `01-2026_Q1` | 496,726 | 399,942 | 0 | 165,594 | **60,159** | 12.11% | 7 |
| `01-2026_Q2` | 630,371 | 507,492 | 0 | 210,243 | **74,456** | 11.81% | 7 |
| `02-2025_01` | 536,078 | 421,309 | 0 | 163,041 | **74,529** | 13.90% | 7 |
| `02-2025_02` | 606,776 | 478,710 | 0 | 196,198 | **79,711** | 13.14% | 7 |
| `02-2026_Q1` | 496,645 | 390,400 | 0 | 158,147 | **67,624** | 13.62% | 7 |
| `02-2026_Q2` | 547,811 | 449,120 | 0 | 183,426 | **60,964** | 11.13% | 7 |
| `03-2025_01` | 587,058 | 462,562 | 0 | 188,992 | **80,660** | 13.74% | 7 |
| `03-2025_02` | 594,320 | 470,192 | 0 | 200,518 | **76,244** | 12.83% | 7 |
| `03-2026_Q1` | 558,146 | 446,242 | 0 | 174,509 | **71,328** | 12.78% | 7 |
| `03-2026_Q2` | 606,522 | 487,947 | 0 | 208,192 | **72,401** | 11.94% | 7 |
| `04-2025_01` | 594,887 | 476,167 | 0 | 181,027 | **77,489** | 13.03% | 7 |
| `04-2025_02` | 430,973 | 336,843 | 0 | 140,073 | **60,720** | 14.09% | 7 |
| `04-2026_Q1` | 480,842 | 390,940 | 0 | 153,069 | **57,958** | 12.05% | 7 |
| `04-2026_Q2` | 597,634 | 482,093 | 0 | 208,557 | **70,393** | 11.78% | 7 |
| `05-2025_01` | 437,833 | 349,598 | 0 | 141,228 | **56,639** | 12.94% | 7 |
| `05-2025_02` | 526,969 | 411,427 | 0 | 176,099 | **74,213** | 14.08% | 7 |
| `05-2026_Q1` | 479,993 | 382,725 | 0 | 150,282 | **60,751** | 12.66% | 7 |
| `05-2026_Q2` | 527,089 | 434,366 | 0 | 184,001 | **56,772** | 10.77% | 7 |
| `06-2025_01` | 534,834 | 426,907 | 0 | 167,696 | **69,080** | 12.92% | 7 |
| `06-2025_02` | 573,713 | 456,791 | 0 | 208,631 | **69,558** | 12.12% | 7 |
| `06-2026_Q1` | 622,490 | 508,743 | 0 | 202,968 | **72,091** | 11.58% | 7 |
| `06-2026_Q2` | 632,548 | 506,886 | 0 | 240,171 | **71,758** | 11.34% | 7 |
| `07-2025_01` | 664,946 | 532,278 | 0 | 243,068 | **78,489** | 11.80% | 7 |
| `07-2025_02` | 715,246 | 565,040 | 0 | 265,417 | **88,034** | 12.31% | 7 |
| `07-2026_Q1` | 665,909 | 540,202 | 0 | 254,876 | **71,413** | 10.72% | 7 |
| `07-2026_Q2` | 744,623 | 598,780 | 0 | 291,379 | **82,898** | 11.13% | 7 |
| `08-2025_01` | 692,569 | 552,018 | 0 | 273,994 | **77,901** | 11.25% | 7 |
| `08-2025_02` | 489,955 | 377,997 | 0 | 178,581 | **67,816** | 13.84% | 7 |
| `09-2025_01` | 542,922 | 422,494 | 0 | 176,248 | **78,757** | 14.51% | 7 |
| `09-2025_02` | 534,092 | 412,527 | 0 | 183,758 | **74,521** | 13.95% | 7 |
| `10-2025_01` | 528,492 | 405,317 | 0 | 177,826 | **75,910** | 14.36% | 7 |
| `10-2025_02` | 595,062 | 472,180 | 0 | 221,401 | **71,681** | 12.05% | 7 |
| `11-2025_01` | 486,182 | 391,265 | 0 | 215,698 | **48,201** | 9.91% | 7 |
| `11-2025_02` | 437,363 | 333,238 | 0 | 207,124 | **52,453** | 11.99% | 7 |
| `12-2025_01` | 481,458 | 372,818 | 0 | 208,094 | **58,268** | 12.10% | 7 |
| `12-2025_02` | 434,832 | 331,909 | 0 | 191,148 | **55,272** | 12.71% | 7 |
| **TOTAL** | **21,357,873** | | | | **2,658,906** | **12.45%** | |

### El alcance no es parejo en el tiempo

2025 promedia **12.90%** y 2026 **11.82%**. La fuente publica
proporcionalmente menos de estas entidades y catálogos en 2026 que en
2025. **No es un defecto de la ingesta**, es una propiedad de la fuente —
y hay que tenerla presente antes de comparar precios entre años.

Extremos: `11-2025_01` con 9.91% y `09-2025_01` con 14.51%.

### Deriva de esquema detectada

| lote | columnas ignoradas |
|---|---|
| `06-2026_Q1` | `folio`, `cv_producto`, `cv_marca` |
| `06-2026_Q2` | `folio`, `cv_producto`, `cv_marca` |

Avisadas, no descartadas en silencio (contrato · `columnas_extra`).

## Identidad de los archivos de entrada

El `sha256` es lo que amarra cada cifra a un archivo concreto. Si mañana
alguien reprocesa y una cifra no sale, esto dice si el archivo era el mismo.

| lote | archivo | sha256 |
|---|---|---|
| `01-2025_01` | `01-2025_01.parquet` | `840e6b0475b9f10d…` |
| `01-2025_02` | `01-2025_02.parquet` | `6902d8af7ff0b5ab…` |
| `01-2026_Q1` | `01-2026_Q1.parquet` | `f8e98fc02e4b813a…` |
| `01-2026_Q2` | `01-2026_Q2.parquet` | `b24ffdcc239b6f24…` |
| `02-2025_01` | `02-2025_01.parquet` | `c989f1c143794408…` |
| `02-2025_02` | `02-2025_02.parquet` | `4d40f76ba84fde8b…` |
| `02-2026_Q1` | `02-2026_Q1.parquet` | `afa67fc04284f10d…` |
| `02-2026_Q2` | `02-2026_Q2.parquet` | `832c011969d5beec…` |
| `03-2025_01` | `03-2025_01.parquet` | `297247297c71f3af…` |
| `03-2025_02` | `03-2025_02.parquet` | `1df1ecd627e50a99…` |
| `03-2026_Q1` | `03-2026_Q1.parquet` | `7f47263fc82f15b2…` |
| `03-2026_Q2` | `03-2026_Q2.parquet` | `30a23ea3d37ba3f6…` |
| `04-2025_01` | `04-2025_01.parquet` | `d73308e1646cb4c5…` |
| `04-2025_02` | `04-2025_02.parquet` | `8a5fa0c730d4cfdd…` |
| `04-2026_Q1` | `04-2026_Q1.parquet` | `7e3eca9047851f09…` |
| `04-2026_Q2` | `04-2026_Q2.parquet` | `ca25383de4cd4eb7…` |
| `05-2025_01` | `05-2025_01.parquet` | `f27f65a5907dc9b7…` |
| `05-2025_02` | `05-2025_02.parquet` | `afb2ddc240955c6c…` |
| `05-2026_Q1` | `05-2026_Q1.parquet` | `ecb3c565ba36b83e…` |
| `05-2026_Q2` | `05-2026_Q2.parquet` | `4092efd383a4427f…` |
| `06-2025_01` | `06-2025_01.parquet` | `a55064a4df48e5b2…` |
| `06-2025_02` | `06-2025_02.parquet` | `6ee22124894e0b1d…` |
| `06-2026_Q1` | `06-2026_Q1.parquet` | `ee5eaa30358e031f…` |
| `06-2026_Q2` | `06-2026_Q2.parquet` | `4535e33d4de0f589…` |
| `07-2025_01` | `07-2025_01.parquet` | `ae43322de06cd4ee…` |
| `07-2025_02` | `07-2025_02.parquet` | `c17d6fe59cd8a766…` |
| `07-2026_Q1` | `07-2026_Q1.parquet` | `bb726cec6d6e5e40…` |
| `07-2026_Q2` | `07-2026_Q2.parquet` | `b7a50f9bcb634de4…` |
| `08-2025_01` | `08-2025_01.parquet` | `e7c4c32247549fe4…` |
| `08-2025_02` | `08-2025_02.parquet` | `5f1d19d0c7c45f50…` |
| `09-2025_01` | `09-2025_01.parquet` | `2634567d31d8c249…` |
| `09-2025_02` | `09-2025_02.parquet` | `43a380f5a8241bb1…` |
| `10-2025_01` | `10-2025_01.parquet` | `ed01a0555c6489d5…` |
| `10-2025_02` | `10-2025_02.parquet` | `e60eae0efad6a05e…` |
| `11-2025_01` | `11-2025_01.parquet` | `aed6c47283943445…` |
| `11-2025_02` | `11-2025_02.parquet` | `0718f8b18ff8ad1f…` |
| `12-2025_01` | `12-2025_01.parquet` | `3b022563bcaac1e4…` |
| `12-2025_02` | `12-2025_02.parquet` | `af1f88676ad7e6c9…` |

## Lo que esta ingesta NO hace

Se dice porque es una decisión, no una omisión. La capa cruda guarda el dato
**tal como llegó**: no limpia el `?`, no valida precios, no normaliza `S/m`
contra `S/M` y no deduplica las colisiones de clave. La compuerta de calidad
contra el contrato es de la semana 6.

Las dos únicas columnas que se agregan, `quincena` y `entidad`, son **llaves
de partición**, no limpieza. Las 15 del contrato entran intactas.
