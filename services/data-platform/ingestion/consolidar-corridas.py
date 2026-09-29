#!/usr/bin/env python3
"""
consolidar-corridas.py — CanastaMX · T020

Lee los registros de `ingestion/corridas/*.json` y escribe la evidencia
consolidada en `docs/datos/ingesta-capa-cruda.md`.

POR QUÉ EXISTE
--------------
Los JSON de `corridas/` son registros de operación: describen el estado de UNA
máquina, con su ruta local y su reloj. No entran al repositorio —si dos personas
corren la ingesta, generan dos juegos distintos y ninguno es el correcto—.

Pero hay algo en ellos que sí es un hallazgo y no puede perderse: **la suma de
las filas dentro del alcance, y el sha256 de cada archivo que la produjo.** Eso
es lo que este guión rescata y deja en un documento versionado.

    python services/data-platform/ingestion/consolidar-corridas.py
"""

import datetime as dt
import json
import pathlib
import sys

AQUI = pathlib.Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
CORRIDAS = AQUI / "corridas"
SALIDA = RAIZ / "docs" / "datos" / "ingesta-capa-cruda.md"
CONTRATO = RAIZ / "contracts" / "qqp-v1.yaml"


def main():
    archivos = sorted(CORRIDAS.glob("*.json"))
    if not archivos:
        sys.exit(f"no hay registros en {CORRIDAS}")

    import yaml
    contrato = yaml.safe_load(CONTRATO.read_text(encoding="utf-8"))
    esperado = contrato["medicion"]["filas"]
    alcance = contrato["alcance"]

    filas, sin_recorte = [], []
    for j in archivos:
        d = json.loads(j.read_text(encoding="utf-8"))
        r = d.get("recorte")
        if not isinstance(r, dict):
            sin_recorte.append(d.get("lote", j.stem))
            continue
        filas.append({
            "lote": d["lote"],
            "archivo": pathlib.Path(d["archivo"]).name,   # sólo el nombre
            "sha256": d["sha256_entrada"],
            "del_archivo": r["filas_del_archivo"],
            "dentro": r["dentro_del_alcance"],
            "f_estado": r["fuera_por_estado"],
            "f_ventana": r["fuera_por_ventana"],
            "f_catalogo": r["fuera_por_catalogo"],
            "objetos": d["cinco_cifras"]["objetos"],
            "bytes": d["cinco_cifras"]["bytes"],
            "extra": d.get("columnas_extra_ignoradas") or [],
            "lectura": d.get("lectura_declarada", {}),
            "entidades": sorted({p["entidad"] for p in d["particiones"]}),
        })

    filas.sort(key=lambda x: x["lote"])
    total = sum(f["dentro"] for f in filas)
    corpus = sum(f["del_archivo"] for f in filas)
    ents = sorted({e for f in filas for e in f["entidades"]})
    cuadra = total == esperado

    L = []
    w = L.append
    w("# Ingesta a la capa cruda · evidencia de la corrida")
    w("")
    w(f"**Generado:** {dt.datetime.now(dt.timezone.utc).date().isoformat()} por "
      "`services/data-platform/ingestion/consolidar-corridas.py` · **T020** · issue #90")
    w("")
    w("> Este documento se **genera**, no se escribe a mano. Sale de los registros")
    w("> de `ingestion/corridas/`, que no entran al repositorio porque describen el")
    w("> estado de una máquina. Lo que sí entra es esto: las cifras y el `sha256`")
    w("> de cada archivo que las produjo.")
    w("")
    w("---")
    w("")
    w("## El resultado, en una línea")
    w("")
    w(f"**La suma de las filas dentro del alcance da {total:,}.** El contrato declara")
    w(f"`medicion.filas: {esperado}`, medido el {contrato['medicion']['fecha']} por")
    w(f"`{contrato['medicion']['guion']}` sobre otra ruta y con otro código.")
    w("")
    w("| | |")
    w("|---|---:|")
    w(f"| Ingesta · suma de los {len(filas)} archivos | **{total:,}** |")
    w(f"| Contrato · `medicion.filas` | **{esperado:,}** |")
    w(f"| Diferencia | **{total - esperado:+,}** |")
    w("")
    w(f"**{'CUADRA al dígito.' if cuadra else 'NO CUADRA — hay que averiguar por qué antes de cerrar el issue.'}**")
    if cuadra:
        w("Dos mediciones independientes, separadas en el tiempo y hechas con")
        w("código distinto, dando el mismo número.")
    w("")
    w(f"Filas leídas de los archivos: **{corpus:,}** · el alcance es el "
      f"**{100*total/corpus:.2f}%** de eso.")
    w("")
    w("## El recorte que se aplicó")
    w("")
    w("Los tres que `medicion.poblacion` nombra, leídos del contrato:")
    w("")
    w(f"- **{len(alcance['entidades'])} entidades** · {', '.join(alcance['entidades'])}")
    w(f"- **{len(alcance['catalogos_normalizados'])} catálogos** · "
      f"{', '.join(alcance['catalogos_normalizados'])}")
    w(f"- **ventana** · {alcance['ventana']['desde']} → {alcance['ventana']['hasta']}")
    w("")
    w(f"En el bucket quedaron **{len(ents)} particiones de `entidad`**: "
      f"{', '.join(ents)}.")
    if len(ents) != len(alcance["entidades"]):
        w("")
        w(f"> ⚠ **Son {len(ents)} y el alcance declara "
          f"{len(alcance['entidades'])}.** Algún literal de `estado` no se unificó. "
          "Hay que revisarlo antes de cerrar.")
    w("")
    w("## Por archivo")
    w("")
    w("«Fuera por» se solapan: una fila puede fallar en más de un recorte.")
    w("")
    w("| lote | del archivo | fuera · estado | fuera · ventana | fuera · catálogo | **dentro** | % | objetos |")
    w("|---|---:|---:|---:|---:|---:|---:|---:|")
    for f in filas:
        w(f"| `{f['lote']}` | {f['del_archivo']:,} | {f['f_estado']:,} | "
          f"{f['f_ventana']:,} | {f['f_catalogo']:,} | **{f['dentro']:,}** | "
          f"{100*f['dentro']/f['del_archivo']:.2f}% | {f['objetos']} |")
    w(f"| **TOTAL** | **{corpus:,}** | | | | **{total:,}** | "
      f"**{100*total/corpus:.2f}%** | |")
    w("")

    # lo que no es parejo en el tiempo
    p25 = [f for f in filas if "2025" in f["lote"]]
    p26 = [f for f in filas if "2026" in f["lote"]]
    if p25 and p26:
        m25 = sum(100*f["dentro"]/f["del_archivo"] for f in p25)/len(p25)
        m26 = sum(100*f["dentro"]/f["del_archivo"] for f in p26)/len(p26)
        w("### El alcance no es parejo en el tiempo")
        w("")
        w(f"2025 promedia **{m25:.2f}%** y 2026 **{m26:.2f}%**. La fuente publica")
        w("proporcionalmente menos de estas entidades y catálogos en 2026 que en")
        w("2025. **No es un defecto de la ingesta**, es una propiedad de la fuente —")
        w("y hay que tenerla presente antes de comparar precios entre años.")
        w("")
        ext = sorted(filas, key=lambda f: f["dentro"]/f["del_archivo"])
        w(f"Extremos: `{ext[0]['lote']}` con "
          f"{100*ext[0]['dentro']/ext[0]['del_archivo']:.2f}% y "
          f"`{ext[-1]['lote']}` con "
          f"{100*ext[-1]['dentro']/ext[-1]['del_archivo']:.2f}%.")
        w("")

    # lecturas que no fueron las de por omisión
    exc = [f for f in filas if f["lectura"].get("es_excepcion_del_contrato")]
    if exc:
        w("### Archivos leídos con una excepción declarada")
        w("")
        w("| lote | codificación | formato de fecha |")
        w("|---|---|---|")
        for f in exc:
            w(f"| `{f['lote']}` | {f['lectura']['encoding']} | "
              f"{f['lectura']['formato_de_fecha']} |")
        w("")
        w("El contrato declara las dos en `archivo.codificacion` y")
        w("`archivo.formato_de_fecha`. **No las adivina DuckDB**: leerlas con el")
        w("formato de los otros 36 intercambiaría día y mes, y el error no dejaría")
        w("rastro porque la fecha saldría válida.")
        w("")

    ex = [f for f in filas if f["extra"]]
    if ex:
        w("### Deriva de esquema detectada")
        w("")
        w("| lote | columnas ignoradas |")
        w("|---|---|")
        for f in ex:
            w(f"| `{f['lote']}` | {', '.join(f'`{c}`' for c in f['extra'])} |")
        w("")
        w("Avisadas, no descartadas en silencio (contrato · `columnas_extra`).")
        w("")

    if sin_recorte:
        w("### Corridas sin recorte")
        w("")
        w(f"{len(sin_recorte)} corrida(s) con `--sin-recorte`, excluidas del total: "
          f"{', '.join(f'`{s}`' for s in sin_recorte)}.")
        w("")

    w("## Identidad de los archivos de entrada")
    w("")
    w("El `sha256` es lo que amarra cada cifra a un archivo concreto. Si mañana")
    w("alguien reprocesa y una cifra no sale, esto dice si el archivo era el mismo.")
    w("")
    w("| lote | archivo | sha256 |")
    w("|---|---|---|")
    for f in filas:
        w(f"| `{f['lote']}` | `{f['archivo']}` | `{f['sha256'][:16]}…` |")
    w("")
    w("## Lo que esta ingesta NO hace")
    w("")
    w("Se dice porque es una decisión, no una omisión. La capa cruda guarda el dato")
    w("**tal como llegó**: no limpia el `?`, no valida precios, no normaliza `S/m`")
    w("contra `S/M` y no deduplica las colisiones de clave. La compuerta de calidad")
    w("contra el contrato es de la semana 6.")
    w("")
    w("Las dos únicas columnas que se agregan, `quincena` y `entidad`, son **llaves")
    w("de partición**, no limpieza. Las 15 del contrato entran intactas.")

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"escrito: {SALIDA}")
    print(f"  {len(filas)} corridas · total {total:,} · contrato {esperado:,} · "
          f"{'CUADRA' if cuadra else 'NO CUADRA'}")
    print(f"  {len(ents)} entidades en el bucket")


if __name__ == "__main__":
    main()
