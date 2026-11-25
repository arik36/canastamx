import type { ReactNode } from 'react'
import { cookies } from 'next/headers'
import Link from 'next/link'

import Sidebar from '@/components/Sidebar'
import {
  centavos,
  conteo,
  dinero,
  entidadesDeLaSerie,
  esQuincena,
  esSimulador,
  leerCatalogo,
  leerDesglose,
  leerSerie,
  nombreDelArticulo,
  quincenaAnterior,
  resumenDeSerie,
  textoDePoblacion,
  urlDeAnalitica,
  urlDelDetalle,
  variacionEnPorcentaje,
  type Establecimiento,
  type PuntoDeSerie,
} from '@/lib/analitica.mjs'
import { exigirCuenta } from '@/lib/sesion'

// Vista 3 del inventario: el detalle de artículo, al que se llega desde la tabla de
// anomalías del tablero. Pide serieDeArticulo y desgloseDeArticulo, y buscarArticulos sólo
// para el ícono del catálogo, desde el servidor y con el token de la sesión. Aquí no hay
// ninguna cifra escrita.

type Consulta = Promise<Record<string, string | string[] | undefined>>

const texto = (valor: string | string[] | undefined) => (typeof valor === 'string' ? valor.trim() : '')

export default async function Page({ searchParams }: { searchParams: Consulta }) {
  const cuenta = await exigirCuenta('ANALISTA')
  const token = (await cookies()).get('token')?.value ?? ''
  const parametros = await searchParams
  const articulo = { producto: texto(parametros.producto), presentacion: texto(parametros.presentacion) }
  const quincenaPedida = esQuincena(texto(parametros.quincena)) ? texto(parametros.quincena) : undefined

  return (
    <div className="flex h-screen w-full overflow-x-auto bg-[#f0eadf]">
      {/* Contenedor forzado a 1025px para obligar el desplazamiento lateral (D-08) */}
      <div className="flex h-full min-w-[1025px] flex-1">
        <Sidebar cuenta={cuenta} />
        <main className="relative flex-1 overflow-y-auto p-10">
          {/* Aviso que SOLO aparece en pantallas menores a 1025px */}
          <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 lg:hidden rounded-xl bg-[#d32f2f] px-6 py-3 text-sm font-bold text-white shadow-xl whitespace-nowrap">
            ⚠️ Pantalla pequeña: Desplázate lateralmente para ver la interfaz.
          </div>
          {articulo.producto && articulo.presentacion ? (
            <Detalle articulo={articulo} entidadPedida={texto(parametros.entidad)}
              quincenaPedida={quincenaPedida} token={token} />
          ) : (
            <>
              <h1 className="text-2xl font-extrabold text-[#2f2f2f]">Detalle de artículo</h1>
              <p className="mt-6 rounded-2xl bg-white px-6 py-5 text-sm font-semibold text-[#2f2f2f] shadow-sm">
                Elige un artículo en la tabla de anomalías del tablero para ver su serie, sus cuatro
                indicadores y su precio por establecimiento.{' '}
                <Link href="/tablero" className="font-bold text-[#158683] underline">Ir al tablero</Link>
              </p>
            </>
          )}
        </main>
      </div>
    </div>
  )
}

async function Detalle({ articulo, entidadPedida, quincenaPedida, token }: {
  articulo: { producto: string; presentacion: string }
  entidadPedida: string
  quincenaPedida: string | undefined
  token: string
}) {
  const dependencias = { analiticaUrl: urlDeAnalitica(), fetch }
  const serie = await leerSerie(token, articulo, dependencias)
  const puntos: PuntoDeSerie[] = serie.estado === 'ok' ? serie.puntos : []
  const entidades = entidadesDeLaSerie(puntos)
  const entidad = entidades.find((e) => e.toLowerCase() === entidadPedida.toLowerCase())
    ?? (entidadPedida || entidades[0] || '')
  const resumen = resumenDeSerie(puntos, entidad, quincenaPedida)
  const quincena = resumen.quincena ?? quincenaPedida ?? null
  const [desglose, catalogo] = await Promise.all([
    entidad && quincena ? leerDesglose(token, { ...articulo, entidad, quincena }, dependencias) : null,
    entidad ? leerCatalogo(token, { ...articulo, entidad }, dependencias) : null,
  ])
  const enlace = (otra: { entidad?: string; quincena?: string | null }) => urlDelDetalle({
    articulo, entidad: otra.entidad ?? entidad, quincena: otra.quincena ?? undefined,
  })

  return (
    <>
      <Link href="/tablero" className="text-sm font-bold text-[#158683] underline">← Volver al tablero</Link>
      <Encabezado articulo={articulo} catalogo={catalogo?.estado === 'ok' ? catalogo.catalogo : null} />

      {esSimulador() && (
        <p className="mt-4 inline-block rounded-md bg-yellow-100 px-4 py-3 text-sm font-bold text-yellow-800">
          ⚠️ Datos del simulador del contrato (Prism): son ejemplos, no mediciones.
        </p>
      )}

      {serie.estado !== 'ok' ? (
        <Falla titulo="No se pudo leer la serie del artículo." motivo={serie.motivo} />
      ) : (
        <>
          <div className="mt-6 flex flex-wrap items-center gap-2">
            <span className="text-[11px] font-bold tracking-wider text-[#5b5b5b] uppercase">Entidad</span>
            {entidades.map((e) => (
              <Link key={e} href={enlace({ entidad: e, quincena })}
                className={`rounded-full px-3 py-1 text-sm font-bold ${e === entidad
                  ? 'bg-[#23bbb7] text-[#0e3533]' : 'bg-white text-[#5b5b5b] hover:bg-[#e7dfd0]'}`}>
                {e}
              </Link>
            ))}
          </div>

          {resumen.punto ? (
            <>
              <div className="mt-4 flex items-center gap-4 text-sm font-semibold text-[#2f2f2f]">
                {resumen.previa
                  ? <Link href={enlace({ quincena: resumen.previa })} className="font-bold text-[#158683] underline">← {resumen.previa}</Link>
                  : <span className="text-[#5b5b5b]">← sin quincena anterior</span>}
                <span className="rounded-md bg-white px-3 py-1 font-extrabold">Quincena {resumen.quincena}</span>
                {resumen.siguiente
                  ? <Link href={enlace({ quincena: resumen.siguiente })} className="font-bold text-[#158683] underline">{resumen.siguiente} →</Link>
                  : <span className="text-[#5b5b5b]">es la más reciente</span>}
              </div>
              <Indicadores entidad={entidad} resumen={resumen} />
            </>
          ) : (
            <Vacio>No hay observaciones de este artículo en {entidad || 'esa entidad'}.</Vacio>
          )}

          <Seccion titulo="Serie histórica por entidad">
            <GraficaDeSerie puntos={puntos} entidad={entidad} quincena={resumen.quincena} enlace={enlace} />
          </Seccion>
        </>
      )}

      {entidad && quincena && (
        <Seccion titulo={`Precio por establecimiento · ${entidad}, ${quincena}`}>
          {desglose?.estado === 'ok' ? (
            <Establecimientos establecimientos={desglose.establecimientos}
              poblacion={textoDePoblacion(desglose.poblacion)} />
          ) : (
            <Falla titulo="No se pudo leer el precio por establecimiento." motivo={desglose?.motivo ?? 'no contestó'} />
          )}
        </Seccion>
      )}
    </>
  )
}

// ── El encabezado: el ícono del catálogo y la llave canónica ────────────────

const CATALOGOS: Record<string, { nombre: string; trazo: string }> = {
  BASICOS: { nombre: 'Básicos', trazo: 'M4 10h16l-1.6 9H5.6zM8 10l4-5 4 5M9.5 14v2M14.5 14v2' },
  PACIC: { nombre: 'PACIC', trazo: 'M4 8l8-4 8 4v8l-8 4-8-4zM4 8l8 4 8-4M12 12v8' },
  'FRUTAS Y LEGUMBRES': { nombre: 'Frutas y legumbres', trazo: 'M12 8c-4-3-8 0-7 5s4 8 7 6c3 2 6-1 7-6s-3-8-7-5zM12 8c0-2 1-3.5 3-4.5' },
  MERCADOS: { nombre: 'Mercados', trazo: 'M4 10h16M5 10l1.5-5h11l1.5 5M6 10v9h12v-9M10 19v-5h4v5' },
  'PESCADOS Y MARISCOS': { nombre: 'Pescados y mariscos', trazo: 'M3 12c3-4 8-5 13-2l4-3v10l-4-3c-5 3-10 2-13-2zM15 11.5h.01' },
}

function Encabezado({ articulo, catalogo }: { articulo: { producto: string; presentacion: string }; catalogo: string | null }) {
  const suyo = catalogo ? CATALOGOS[catalogo] : undefined
  return (
    <div className="mt-4 flex items-center gap-4">
      <span aria-hidden className="grid h-14 w-14 shrink-0 place-items-center rounded-2xl bg-white text-[#158683] shadow-sm">
        <svg viewBox="0 0 24 24" className="h-8 w-8" fill="none" stroke="currentColor" strokeWidth="1.8"
          strokeLinecap="round" strokeLinejoin="round">
          <path d={suyo?.trazo ?? 'M5 5h14v14H5z'} />
        </svg>
      </span>
      <div>
        <p className="text-[11px] font-bold tracking-wider text-[#5b5b5b] uppercase">
          Detalle de artículo · {suyo?.nombre ?? 'Catálogo sin dato'}
        </p>
        <h1 className="text-2xl font-extrabold text-[#2f2f2f]">{nombreDelArticulo(articulo)}</h1>
        <p className="text-[11px] font-semibold text-[#5b5b5b]">Llave canónica del artículo (producto · presentación, ADR 002)</p>
      </div>
    </div>
  )
}

// ── Los cuatro indicadores, cada uno con su población ─────────────────────────

function Indicadores({ entidad, resumen }: { entidad: string; resumen: ReturnType<typeof resumenDeSerie> }) {
  const { punto, anterior, variacion, atipica, quincena } = resumen
  if (!punto || !quincena) return null
  const deLaQuincena = `${observaciones(punto.observaciones)} de ${entidad}`
  const previa = quincenaAnterior(quincena)
  return (
    <div className="mt-4 grid grid-cols-2 gap-4 xl:grid-cols-4">
      <Indicador titulo="Precio típico (mediana)" cifra={dinero(punto.mediana)} detalle={`En ${entidad}`}
        poblacion={deLaQuincena} fecha={`Quincena ${quincena}`} />
      <Indicador
        titulo="Variación contra la quincena anterior"
        cifra={variacion === null ? 'Sin comparar' : variacionEnPorcentaje(variacion)}
        detalle={anterior ? `${dinero(anterior.mediana)} → ${dinero(punto.mediana)}` : `No se observó en ${previa}`}
        poblacion={anterior ? `${conteo(anterior.observaciones)} y ${observaciones(punto.observaciones)}` : deLaQuincena}
        fecha={`${previa} → ${quincena}`}
        marca={atipica ? 'Atípica según P-15' : undefined}
      />
      <Indicador titulo="Mínimo" cifra={punto.minimo ? dinero(punto.minimo) : '—'} detalle="El precio más bajo observado"
        poblacion={deLaQuincena} fecha={`Quincena ${quincena}`} />
      <Indicador titulo="Máximo" cifra={punto.maximo ? dinero(punto.maximo) : '—'} detalle="El precio más alto observado"
        poblacion={deLaQuincena} fecha={`Quincena ${quincena}`} />
    </div>
  )
}

const observaciones = (n: number) => (n === 1 ? '1 observación' : `${conteo(n)} observaciones`)

function Indicador({ titulo, cifra, detalle, poblacion, fecha, marca }: {
  titulo: string; cifra: string; detalle: string; poblacion: string; fecha: string; marca?: string
}) {
  // RNF-16: cada cifra con su población y su fecha. El máximo va en tinta, no en rojo (diseno.md §7, punto 9).
  return (
    <article className="rounded-2xl bg-white p-5 shadow-sm">
      <h2 className="text-[11px] font-bold tracking-wider text-[#5b5b5b] uppercase">{titulo}</h2>
      <p className="mt-2 text-2xl font-extrabold text-[#2f2f2f]">{cifra}</p>
      {marca && (
        <p className="mt-1 inline-block rounded-full bg-[#fdf0cc] px-2.5 py-0.5 text-[11px] font-bold text-[#8a6100]">{marca}</p>
      )}
      <p className="mt-1 text-sm font-semibold text-[#2f2f2f]">{detalle}</p>
      <p className="mt-3 text-[11px] font-semibold text-[#5b5b5b]">Población: {poblacion}</p>
      <p className="text-[11px] font-semibold text-[#5b5b5b]">{fecha}</p>
    </article>
  )
}

// ── La serie por entidad: una línea por entidad, la elegida en turquesa ──────

function GraficaDeSerie({ puntos, entidad, quincena, enlace }: {
  puntos: PuntoDeSerie[]
  entidad: string
  quincena: string | null
  enlace: (otra: { entidad?: string; quincena?: string | null }) => string
}) {
  if (puntos.length === 0) return <Vacio>La serie no trae ningún punto.</Vacio>
  const quincenas = [...new Set(puntos.map((p) => p.quincena))].sort()
  const entidades = entidadesDeLaSerie(puntos)
  const valores = puntos.map((p) => centavos(p.mediana))
  let bajo = Math.min(...valores)
  let alto = Math.max(...valores)
  if (bajo === alto) { bajo -= 100; alto += 100 }
  const margen = (alto - bajo) * 0.08
  const y0 = Math.max(0, bajo - margen)
  const y1 = alto + margen
  const A = 640, H = 260, m = { i: 64, d: 16, a: 14, b: 34 }
  const x = (q: string) => m.i + (quincenas.length === 1 ? (A - m.i - m.d) / 2
    : (quincenas.indexOf(q) * (A - m.i - m.d)) / (quincenas.length - 1))
  const y = (c: number) => m.a + (H - m.a - m.b) * (1 - (c - y0) / (y1 - y0))
  const suyos = (e: string) => puntos.filter((p) => p.entidad === e).sort((a, b) => a.quincena.localeCompare(b.quincena))
  // Una quincena sin dato corta la línea: no se inventa el tramo.
  const trazo = (e: string) => {
    let d = ''
    let previo = -2
    for (const p of suyos(e)) {
      const i = quincenas.indexOf(p.quincena)
      d += `${i === previo + 1 ? 'L' : 'M'}${x(p.quincena).toFixed(1)} ${y(centavos(p.mediana)).toFixed(1)}`
      previo = i
    }
    return d
  }
  const cada = Math.max(1, Math.ceil(quincenas.length / 6))
  const marcas = [0, 1, 2, 3].map((k) => y0 + ((y1 - y0) * k) / 3)
  // Con un rango de menos de $4, en pesos enteros dos marcas dirían lo mismo: van con centavos.
  const etiqueta = (c: number) => (y1 - y0 < 400 ? `$${(c / 100).toFixed(2)}` : `$${conteo(Math.round(c / 100))}`)
  const total = puntos.reduce((s, p) => s + p.observaciones, 0)

  return (
    <div className="mt-3 rounded-2xl bg-white p-5 shadow-sm">
      <svg viewBox={`0 0 ${A} ${H}`} className="h-auto w-full" role="img"
        aria-label={`Mediana por quincena de ${entidades.join(', ')}; ${entidad} resaltada`}>
        {marcas.map((c) => (
          <g key={c}>
            <line x1={m.i} x2={A - m.d} y1={y(c)} y2={y(c)} stroke="#f1ebe1" />
            <text x={m.i - 8} y={y(c) + 4} textAnchor="end" fontSize="10" fill="#5b5b5b">{etiqueta(c)}</text>
          </g>
        ))}
        {quincenas.map((q, i) => {
          // La última siempre lleva etiqueta; las de en medio, cada `cada`, sin encimarse con ella.
          const ultima = i === quincenas.length - 1
          if (!ultima && (i % cada !== 0 || quincenas.length - 1 - i < cada)) return null
          return (
            <text key={q} x={x(q)} y={H - 12} textAnchor={ultima && quincenas.length > 1 ? 'end' : 'middle'}
              fontSize="10" fill="#5b5b5b">{q}</text>
          )
        })}
        {quincena && quincenas.includes(quincena) && (
          <line x1={x(quincena)} x2={x(quincena)} y1={m.a} y2={H - m.b} stroke="#5b5b5b" strokeDasharray="4 4" />
        )}
        {entidades.filter((e) => e !== entidad).map((e) => (
          <path key={e} d={trazo(e)} fill="none" stroke="#c9bfae" strokeWidth="1.5">
            <title>{e}</title>
          </path>
        ))}
        <path d={trazo(entidad)} fill="none" stroke="#23bbb7" strokeWidth="3" />
        {suyos(entidad).map((p) => (
          <a key={p.quincena} href={enlace({ quincena: p.quincena })}>
            <circle cx={x(p.quincena)} cy={y(centavos(p.mediana))} r={p.quincena === quincena ? 6 : 4}
              fill={p.quincena === quincena ? '#158683' : '#23bbb7'} stroke="#fff" strokeWidth="1.5">
              <title>{`${entidad} · ${p.quincena}: ${dinero(p.mediana)}, ${observaciones(p.observaciones)}`}</title>
            </circle>
          </a>
        ))}
      </svg>
      <p className="mt-2 text-[11px] font-semibold text-[#5b5b5b]">
        Mediana de cada quincena; en turquesa, {entidad}, y en gris, las demás entidades. Toca un punto para
        ver esa quincena. Población: {textoDePoblacion({ entidades, desde: quincenas[0], hasta: quincenas[quincenas.length - 1], observaciones: total })}.
      </p>
    </div>
  )
}

// ── El precio por establecimiento ────────────────────────────────────────────

function Establecimientos({ establecimientos, poblacion }: { establecimientos: Establecimiento[]; poblacion: string }) {
  const orden = [...establecimientos].sort((a, b) => centavos(a.promedio) - centavos(b.promedio))
  return (
    <>
      <p className="mt-1 text-[11px] font-semibold text-[#5b5b5b]">
        {establecimientos.length === 1 ? '1 establecimiento' : `${conteo(establecimientos.length)} establecimientos`},
        del promedio más bajo al más alto. Población: {poblacion}.
      </p>
      <div className="mt-3 overflow-hidden rounded-2xl bg-white shadow-sm">
        <table className="w-full border-collapse text-sm text-[#2f2f2f]">
          <thead className="border-b-2 border-[#e7dfd0] text-left text-[11px] font-bold tracking-wider text-[#5b5b5b] uppercase">
            <tr>
              <th className="px-4 py-3">Establecimiento</th>
              <th className="px-4 py-3 text-right">Mínimo</th>
              <th className="px-4 py-3 text-right">Promedio</th>
              <th className="px-4 py-3 text-right">Máximo</th>
              <th className="px-4 py-3 text-right">Observaciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#e7dfd0]">
            {orden.map((e) => (
              <tr key={`${e.nombre}|${e.cadena}`}>
                <td className="px-4 py-3">
                  <span className="font-semibold">{e.nombre || 'Sin nombre en la fuente'}</span>
                  <span className="block text-[11px] text-[#5b5b5b]">{e.cadena || 'Sin cadena'}</span>
                </td>
                <td className="px-4 py-3 text-right whitespace-nowrap">{dinero(e.minimo)}</td>
                <td className="px-4 py-3 text-right font-bold whitespace-nowrap">{dinero(e.promedio)}</td>
                <td className="px-4 py-3 text-right whitespace-nowrap">{dinero(e.maximo)}</td>
                <td className="px-4 py-3 text-right">{conteo(e.observaciones)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}

// ── Piezas ───────────────────────────────────────────────────────────────────

function Seccion({ titulo, children }: { titulo: string; children: ReactNode }) {
  return (
    <section className="mt-10">
      <h2 className="text-lg font-bold text-[#2f2f2f]">{titulo}</h2>
      {children}
    </section>
  )
}

function Vacio({ children }: { children: ReactNode }) {
  return <p className="mt-4 rounded-2xl bg-white px-6 py-5 text-sm font-medium text-[#5b5b5b] shadow-sm">{children}</p>
}

function Falla({ titulo, motivo }: { titulo: string; motivo: string }) {
  return (
    <div role="alert" className="mt-6 rounded-md border border-red-200 bg-red-50 p-4 text-red-700">
      <p className="font-bold">{titulo}</p>
      <p className="mt-1 text-sm">La analítica {motivo}.</p>
    </div>
  )
}
