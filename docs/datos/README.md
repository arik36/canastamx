# Guiones de perfilado · QQP

Qué es cada archivo de esta carpeta y en qué orden se corren. Existe porque
son quince guiones y sin este mapa no se distingue cuál es un análisis, cuál es
un resultado y cuál lleva trabajo hecho a mano que no se debe borrar.

> **Los guiones se agrupan por la POBLACIÓN que miden, no por lo que hacen.**
> Hay tres y no son intercambiables:
>
> | población | filas | qué documento alimenta |
> |---|---:|---|
> | corpus completo | 21,357,873 | `perfilado.md`, el informe |
> | recorte territorial | 4,384,962 | ADR 001, ADR 002 |
> | alcance del contrato | 2,658,906 | `contracts/qqp-v1.yaml` |
>
> Copiar una cifra de una población a otra **ya costó tres campos mal puestos en
> el contrato**. Antes de citar un número de aquí, mira con qué guión se midió.

Todos se corren **desde la raíz del repositorio**, no desde aquí:

```bash
python docs/datos/perfilado/perfilado_nivel1.py
```

Y todos leen los parquets de `~/canastamx-datos/procesado/por_archivo/`, que se
puede cambiar con la variable `CANASTAMX_DATOS`.

## Orden

Hay dependencias reales entre ellos. Éste es el orden que funciona:

| # | Guión | Qué hace | Necesita antes |
|---|---|---|---|
| 1 | `perfilado_nivel1.py` | Filas, columnas, tipos, nulos, rango de fechas. Convierte los CSV a parquet. | los CSV descargados |
| 2 | `mojibake.py` | Mide el texto corrompido y arma el diccionario de reparación. | 1 |
| 3 | `perfilado_nivel2.py` | Rangos, duplicados, clave candidata, columnas ausentes. | 1, 2 |
| 4 | `perfilado_nivel3.py` | Variantes de escritura por artículo. Escribe `variantes-para-revisar.txt`. | 1 |
| 5 | `centinelas.py` | Busca valores centinela en `precio`. Separa puntos de precio de candidatos reales. | 1, 2 |
| 6 | `revisar-candidatos.py` | Contrasta cada candidato contra la mediana de su propia presentación. | 5 |
| 7 | `medir-decisiones.py` | Las cifras que pidieron los ADR del 11 de septiembre. | 1 |
| 8 | `h3-entre-cadenas.py` | ¿Las cadenas escriben distinto el mismo producto? | 1 |
| 9 | `h3-muestra-para-calificar.py` | Arma la muestra de 200 pares que H3 necesita de verdad. | 8 |

`diagnostico.py` es de la primera semana y ya no forma parte del flujo: quedó
como registro de cómo se encontró el problema de los archivos con esquema
distinto. No hace falta correrlo.

`demos-explicativas.py` no analiza nada: son ocho demostraciones que se corren
solas para explicar los conceptos del perfilado. Sirve para estudiar, no para
medir.

## Los tres tipos de archivo

Distinguirlos importa porque **uno de los tres no se puede regenerar**.

### Guiones · los `.py`

Se corren. Si se borran, se recuperan del repositorio.

### Resultados · todo lo que está en `salidas/`

Los escriben los guiones. **Si se borran, se regeneran corriendo el guión otra
vez.** Ninguno lleva trabajo humano dentro.

```
salidas/
  resumen-nivel1.md                   ← guión 1
  mojibake-clasificado.csv            ← guión 2
  mojibake-diccionario.csv            ← guión 2 · lo LEEN los guiones 3 y 5
  precios-redondos-clasificados.csv   ← guión 5
  centinelas-confirmados.csv          ← guión 5
  candidatos-revisados.csv            ← guión 6
  estados-literales.csv               ← guión 7
  catalogos.csv                       ← guión 7
  recorte-resumen.csv                 ← guión 7
  h3-pares-entre-cadenas.csv          ← guión 8
  h3-diferencias-por-columna.csv      ← guión 9
  h3-muestra-para-calificar.csv       ← guión 9
```

`mojibake-diccionario.csv` es el único que es resultado de uno y **entrada** de
otros dos. Por eso vive aquí y no suelto entre los guiones: si falta, el
perfilado nivel 2 y el de centinelas avisan y siguen sin reparar categorías.

### Trabajo a mano · los `.txt` de arriba

**Éstos no se regeneran.** El guión escribe el archivo vacío de marcas; las
marcas las pone una persona. Si se sobrescriben, ese trabajo se pierde.

| Archivo | Lo escribe | Quién lo marca | Para qué |
|---|---|---|---|
| `variantes-para-revisar.txt` | guión 4 | A | Verificar que la normalización agrupó bien. Es la evidencia del «0 agrupamientos incorrectos» de `perfilado.md` §3. |
| `h3-muestra-para-calificar.txt` | guión 9 | A | Calificar los 200 pares de H3. Es la evidencia de la cobertura y la precisión que se reporten. |

> **Antes de volver a correr los guiones 4 o 9, copia el `.txt` marcado a otro
> lado.** Los dos sobrescriben sin preguntar.

Y ojo con la polaridad, porque es **al revés** entre los dos:

- En `variantes-para-revisar.txt`, «sí» significa *el sistema acertó al
  juntarlos*. Es una buena noticia.
- En `h3-muestra-para-calificar.txt`, «sí» significa *son el mismo artículo y
  el sistema NO los juntó*. Es un fallo de cobertura.

## Documentos

`recapitulado-perfilado.md` explica desde cero cómo funciona cada guión, qué
estaba mal en las primeras versiones y por qué se arregló como se arregló. Es
para entender, no para consultar de prisa.

Los resultados del perfilado, ya redactados, están un nivel arriba en
`docs/datos/perfilado.md`, y la recomendación que fue a la reunión del 11 en
`docs/datos/informe-perfilado-v0.md`.


---

## Guiones que se agregaron después de la primera versión de este README

| Guión | Población | Qué mide | Alimenta |
|---|---|---|---|
| `medir-decisiones.py` | recorte territorial | volumen, claves candidatas, catálogos, colisiones | ADR 001, ADR 002 |
| `revisar-catalogo-especial.py` | un catálogo | qué contiene `Especial` | ADR 005 |
| `verificar-precios.py` | alcance del contrato | techos de precio y colisiones, ya acotadas | `contracts/` |
| `revisar-techos-y-marca.py` | alcance del contrato | qué producto ancla cada techo · los literales de `S/M` | `contracts/` |
| `medir-para-contrato.py` | alcance del contrato | conteo de artículos · el `?` dentro del alcance · categorías de `Basicos` | `contracts/` |
| `diagnostico.py` | — | utilería | — |

## Archivos que NO se regeneran

Estos dos se marcan **a mano** y volver a producirlos cuesta un día de trabajo.
El guión que los escribe **los sobrescribe sin preguntar**, así que se respaldan
antes de volver a correrlo:

- `variantes-para-revisar.txt` — lo escribe `perfilado_nivel3.py`
- `h3-muestra-para-calificar.txt` — lo escribe `h3-muestra-para-calificar.py`

```bash
cp docs/datos/perfilado/h3-muestra-para-calificar.txt{,.bak}
```

Todo lo de `salidas/` sí se regenera y se puede borrar sin pensarlo.

## Cómo va a quedar esta carpeta

Está previsto reordenarla en cuatro subcarpetas, **después de la entrega del 18**
y no antes: hay más de sesenta citas a estas rutas en el contrato, los ADR, el
informe y las fichas, y moverlas sin reescribirlas deja el paquete apuntando a
archivos que no existen.

```
docs/datos/perfilado/
├── README.md
├── describir-la-fuente/    corpus completo      → perfilado.md, informe
├── medir-para-decidir/     población acotada    → ADR y contrato
├── h3/                     la hipótesis         → ADR 004
├── calificado-a-mano/      NUNCA se regenera
└── salidas/                todo regenerable
```

Lo hace `infra/scripts/ordenar-perfilado.py`, que mueve **y reescribe las
referencias** en la misma pasada, con `--simular` primero.
