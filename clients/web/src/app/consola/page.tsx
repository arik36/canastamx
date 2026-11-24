import { Fragment, type ReactNode } from 'react'
import { cookies } from 'next/headers'
import Link from 'next/link'

import Sidebar from '@/components/Sidebar'
import { conteo, esSimulador, urlDeAnalitica } from '@/lib/analitica.mjs'
import {
  LIMITES,
  LOTE,
  duracion,
  estadoGeneral,
  fechaYHora,
  filas,
  leerCorridas,
  leerCuarentena,
  leerEstado,
  leerIncidentes,
  leerLinaje,
  nivelDeCorrida,
  nivelDeFrescura,
  nombreDeLaCausa,
  nombreDeLaFrescura,
  nombreDelResultado,
  porCerrar,
  porcentaje,
  textoDeFila,
  textoDeFrescura,
  type Corrida,
  type FilaEnCuarentena,
  type Incidente,
  type Indicadores,
} from '@/lib/operacion.mjs'
import { exigirCuenta } from '@/lib/sesion'

import CierreDeIncidente from './CierreDeIncidente'

// Vista 4 del inventario: la consola de observabilidad (CU-04 y CU-05, RF-12 y RF-13).
// Todo sale de las rutas de operación de la analítica (analitica.yaml 0.2.1), pedidas
// desde el servidor con el token de la sesión: aquí no hay ninguna cifra escrita.
// Lo primero que se ve responde «¿está todo bien?» en menos de tres segundos.

// El semáforo de diseno.md §1 y §5: verde OK, azul aviso, rojo incidente y gris
// «no aplica». «neutro» es para las cifras que no son un estado, como las filas.
type Nivel = 'ok' | 'aviso' | 'incidente' | 'no-aplica' | 'neutro'

const COLOR: Record<Nivel, { franja: string; punto: string; texto: string }> = {
  ok: { franja: 'border-l-[#00a859]', punto: 'bg-[#00a859]', texto: 'text-[#007a44]' },
  aviso: { franja: 'border-l-[#89ccff]', punto: 'bg-[#89ccff]', texto: 'text-[#0b5394]' },
  incidente: { franja: 'border-l-[#d32f2f]', punto: 'bg-[#d32f2f]', texto: 'text-[#c62828]' },
  'no-aplica': { franja: 'border-l-[#e7dfd0]', punto: 'bg-[#e7dfd0]', texto: 'text-[#5b5b5b]' },
  neutro: { franja: 'border-l-[#e7dfd0]', punto: 'hidden', texto: 'text-[#2f2f2f]' },
}

type Consulta = Promise<Record<string, string | string[] | undefined>>

export default async function Page({ searchParams }: { searchParams: Consulta }) {
  const cuenta = await exigirCuenta('OPERADOR')
  const token = (await cookies()).get('token')?.value ?? ''
  const { lote: loteDeLaUrl, cerrado } = await searchParams
  const dependencias = { analiticaUrl: urlDeAnalitica(), fetch }
  const consultadaEn = new Date()

  const [plataforma, corridas, abiertos, historial] = await Promise.all([
    leerEstado(token, dependencias),
    leerCorridas(token, { limit: LIMITES.corridas }, dependencias),
    leerIncidentes(token, { estado: 'ABIERTO', severidad: 'INCIDENTE', limit: LIMITES.abiertos }, dependencias),
    leerIncidentes(token, { limit: LIMITES.historial }, dependencias),
  ])

  // El lote que se revisa abajo: el que se eligió (CU-05 · 4), o el de la última corrida.
  const elegido = typeof loteDeLaUrl === 'string' && LOTE.test(loteDeLaUrl) ? loteDeLaUrl : null
  const lote = elegido ?? (plataforma.estado === 'ok' ? plataforma.indicadores.ultimaCorrida.lote : null)
  const [linaje, cuarentena] = lote
    ? await Promise.all([leerLinaje(token, lote, dependencias), leerCuarentena(token, { lote }, dependencias)])
    : [null, null]

  const abiertosPorCerrar = abiertos.estado === 'ok' ? porCerrar(abiertos.incidentes) : []
  const recienCerrado = typeof cerrado === 'string' && /^[\w-]{1,40}$/.test(cerrado) ? cerrado : null

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
          <h1 className="text-2xl font-extrabold text-[#2f2f2f]">Consola de observabilidad</h1>
          <p className="mt-1 text-[11px] font-semibold text-[#5b5b5b]">
            Estado de la plataforma de datos, calculado sobre los registros de las corridas (CU-05).
            Consultado el {fechaYHora(consultadaEn)}.
          </p>

          {esSimulador() && (
            <p className="mt-4 inline-block rounded-md bg-yellow-100 px-4 py-3 text-sm font-bold text-yellow-800">
              ⚠️ Datos del simulador del contrato (Prism): son ejemplos, no mediciones.
            </p>
          )}

          {recienCerrado && (
            <p role="status" className="mt-4 rounded-md border border-[#00a859] bg-white px-4 py-3 text-sm font-bold text-[#007a44]">
              ✓ El incidente {recienCerrado} quedó cerrado. En el historial están su causa, su decisión,
              quién lo cerró y cuándo.
            </p>
          )}

          {plataforma.estado === 'ok' ? (
            <Resumen
              indicadores={plataforma.indicadores}
              totalDeCorridas={corridas.estado === 'ok' ? corridas.total : null}
              masReciente={abiertosPorCerrar[0] ?? null}
              consultadaEn={consultadaEn}
            />
          ) : plataforma.estado === 'sin-corridas' ? (
            <p className="mt-6 rounded-2xl bg-white px-6 py-5 text-sm font-semibold text-[#2f2f2f] shadow-sm">
              Todavía no hay ninguna corrida registrada. Los seis indicadores aparecen con la primera
              (CU-05 · 2b).
            </p>
          ) : (
            <Falla titulo="No se pudo leer el estado de la plataforma." motivo={plataforma.motivo}>
              Sin él no se puede confirmar que todo esté bien: repórtalo a infraestructura (CU-05).
            </Falla>
          )}

          {abiertos.estado === 'ok' ? (
            abiertosPorCerrar.length > 0 && <Abiertos incidentes={abiertosPorCerrar} total={abiertos.total} />
          ) : (
            <Falla titulo="No se pudieron leer los incidentes abiertos." motivo={abiertos.motivo} />
          )}

          <Seccion id="historial" titulo="Historial de avisos e incidentes">
            {historial.estado === 'ok' ? (
              <Historial incidentes={historial.incidentes} total={historial.total} />
            ) : (
              <Falla titulo="No se pudo leer el historial." motivo={historial.motivo} />
            )}
          </Seccion>

          <Seccion id="corridas" titulo="Corridas">
            {corridas.estado === 'ok' ? (
              <Corridas corridas={corridas.corridas} total={corridas.total} />
            ) : (
              <Falla titulo="No se pudieron leer las corridas." motivo={corridas.motivo} />
            )}
          </Seccion>

          {lote && linaje && cuarentena && (
            <Seccion id="lote" titulo={`Lote ${lote}: linaje y cuarentena`}>
              {linaje.estado === 'ok' ? (
                <Linaje corridas={linaje.corridas} />
              ) : (
                <Falla titulo={`No se pudo leer el linaje del lote ${lote}.`} motivo={linaje.motivo} />
              )}
              {cuarentena.estado === 'ok' ? (
                <Cuarentena lote={lote} filas={cuarentena.filas} total={cuarentena.total} />
              ) : (
                <Falla titulo={`No se pudo leer la cuarentena del lote ${lote}.`} motivo={cuarentena.motivo} />
              )}
            </Seccion>
          )}
        </main>
      </div>
    </div>
  )
}

// ── Los seis indicadores y la respuesta de los tres segundos (CU-05 · 2 y 3) ──

function Resumen({ indicadores, totalDeCorridas, masReciente, consultadaEn }: {
  indicadores: Indicadores
  totalDeCorridas: number | null
  masReciente: Incidente | null
  consultadaEn: Date
}) {
  const { ultimoDato, frescura, ultimaCorrida, filasProcesadas, cuarentena, avisosDeEsquema,
    incidentesAbiertos } = indicadores
  const general = estadoGeneral(indicadores)
  // Las cifras de los lotes vigentes valen hasta el dato más reciente (RNF-16).
  const hasta = ultimoDato ? `Hasta ${ultimoDato}` : 'Todavía no ha pasado ningún lote'

  return (
    <>
      <EstadoGeneral nivel={general.nivel} titulo={general.titulo}>
        {masReciente ? (
          <>
            El más reciente: lote {masReciente.lote}, compuerta {masReciente.compuerta}, motivo{' '}
            {masReciente.motivo}, abierto el {fechaYHora(masReciente.abiertoEn)}.{' '}
            <a href={`#incidente-${masReciente.id}`} className="underline">Atenderlo</a>
          </>
        ) : (
          <>Última corrida: lote {ultimaCorrida.lote}, iniciada el {fechaYHora(ultimaCorrida.fecha)}.</>
        )}
      </EstadoGeneral>

      {/* Arriba, los tres que responden «¿está bien?»; abajo, los volúmenes. */}
      <div className="mt-6 grid grid-cols-3 gap-4">
        <Indicador
          titulo="Última corrida"
          nivel={nivelDeCorrida(ultimaCorrida.resultado)}
          cifra={nombreDelResultado(ultimaCorrida.resultado)}
          detalle={`Lote ${ultimaCorrida.lote} · ${filas(ultimaCorrida.filasLeidas)} leídas`}
          poblacion={totalDeCorridas === null ? 'La más reciente de las corridas registradas'
            : `La más reciente de ${conteo(totalDeCorridas)} corridas registradas`}
          fecha={`Iniciada el ${fechaYHora(ultimaCorrida.fecha)}`}
        />
        <Indicador
          titulo="Frescura"
          nivel={nivelDeFrescura(frescura.estado)}
          cifra={nombreDeLaFrescura(frescura.estado)}
          detalle={textoDeFrescura(frescura, ultimoDato)}
          poblacion={`Medida en la última corrida, la del lote ${ultimaCorrida.lote}`}
          fecha={ultimoDato ? `Dato más reciente: ${ultimoDato}` : 'Todavía sin dato'}
        />
        <Indicador
          titulo="Incidentes abiertos"
          nivel={incidentesAbiertos > 0 ? 'incidente' : 'ok'}
          cifra={conteo(incidentesAbiertos)}
          detalle={incidentesAbiertos > 0 ? 'Abajo, cada uno se cierra con su causa' : 'Ninguno por atender'}
          poblacion="De todas las corridas registradas"
          fecha={`Consultado el ${fechaYHora(consultadaEn)}`}
        />
        <Indicador
          titulo="Filas procesadas"
          nivel="neutro"
          cifra={conteo(filasProcesadas)}
          detalle="Leídas del alcance"
          poblacion="Corrida vigente de cada lote"
          fecha={hasta}
        />
        <Indicador
          titulo="En cuarentena"
          nivel="neutro"
          cifra={filas(cuarentena.filas)}
          detalle={`${porcentaje(cuarentena.porcentaje)} de las filas procesadas`}
          poblacion={`Población: ${cuarentena.poblacion}`}
          fecha={hasta}
        />
        <Indicador
          titulo="Avisos de esquema"
          nivel={avisosDeEsquema > 0 ? 'aviso' : 'ok'}
          cifra={conteo(avisosDeEsquema)}
          detalle="Columnas que el contrato no declara: el lote entra y el aviso no se cierra"
          poblacion="Corrida vigente de cada lote"
          fecha={hasta}
        />
      </div>
    </>
  )
}

function EstadoGeneral({ nivel, titulo, children }: { nivel: Nivel; titulo: string; children: ReactNode }) {
  // Tinta sobre el azul y blanco sobre el rojo y el verde oscuro: los pares que pasan en
  // diseno.md («Contraste medido»). La forma también cambia: ✓, ! o ✕.
  const estilo = nivel === 'incidente' ? 'bg-[#d32f2f] text-white'
    : nivel === 'aviso' ? 'bg-[#89ccff] text-[#2f2f2f]' : 'bg-[#007a44] text-white'
  const marca = nivel === 'incidente' ? '✕' : nivel === 'aviso' ? '!' : '✓'
  return (
    <section aria-live="polite" className={`mt-6 flex items-center gap-4 rounded-2xl px-6 py-5 shadow ${estilo}`}>
      <span aria-hidden className="grid h-12 w-12 shrink-0 place-items-center rounded-full border-4 border-current text-2xl font-extrabold">
        {marca}
      </span>
      <div>
        <p className="text-xl font-extrabold">{titulo}</p>
        <p className="mt-1 text-sm font-semibold">{children}</p>
      </div>
    </section>
  )
}

function Indicador({ titulo, nivel, cifra, detalle, poblacion, fecha }: {
  titulo: string
  nivel: Nivel
  cifra: string
  detalle: string
  poblacion: string
  fecha: string
}) {
  // RNF-16: cada cifra con su población y su fecha, en las dos últimas líneas.
  return (
    <article className={`rounded-2xl border-l-8 bg-white p-5 shadow-sm ${COLOR[nivel].franja}`}>
      <h2 className="text-[11px] font-bold tracking-wider text-[#5b5b5b] uppercase">{titulo}</h2>
      <p className={`mt-2 flex items-center gap-2 text-2xl font-extrabold ${COLOR[nivel].texto}`}>
        <span aria-hidden className={`h-3 w-3 shrink-0 rounded-full ${COLOR[nivel].punto}`} />
        {cifra}
      </p>
      <p className="mt-1 text-sm font-semibold text-[#2f2f2f]">{detalle}</p>
      <p className="mt-3 text-[11px] font-semibold text-[#5b5b5b]">{poblacion}</p>
      <p className="text-[11px] font-semibold text-[#5b5b5b]">{fecha}</p>
    </article>
  )
}

// ── Incidentes y avisos (CU-04, RF-13) ───────────────────────────────────────

function Abiertos({ incidentes, total }: { incidentes: Incidente[]; total: number }) {
  return (
    <Seccion id="abiertos" titulo="Incidentes abiertos">
      <Poblacion>
        {seMuestran(incidentes.length, total, 'incidente abierto', 'incidentes abiertos')}, del más
        reciente al más antiguo. Revisa su lote y sus filas en cuarentena antes de cerrarlo.
      </Poblacion>
      <div className="mt-4 flex flex-col gap-4">
        {incidentes.map((i) => (
          <article key={i.id} id={`incidente-${i.id}`} className="rounded-2xl border-l-8 border-l-[#d32f2f] bg-white p-5 shadow-sm">
            <p className="text-sm font-extrabold text-[#c62828]">
              Incidente {i.id} · {filas(i.filas)} afectadas
            </p>
            <dl className="mt-3 grid grid-cols-4 gap-3 text-sm">
              <Dato nombre="Lote"><span className="font-mono">{i.lote}</span></Dato>
              <Dato nombre="Compuerta"><span className="font-mono">{i.compuerta}</span></Dato>
              <Dato nombre="Motivo"><span className="font-mono">{i.motivo}</span></Dato>
              <Dato nombre="Abierto">{fechaYHora(i.abiertoEn)}</Dato>
            </dl>
            <Link href={`/consola?lote=${encodeURIComponent(i.lote)}#lote`} className="mt-3 inline-block text-sm font-bold text-[#158683] underline">
              Revisar el lote {i.lote} y sus filas en cuarentena
            </Link>
            <CierreDeIncidente id={i.id} />
          </article>
        ))}
      </div>
    </Seccion>
  )
}

function Historial({ incidentes, total }: { incidentes: Incidente[]; total: number }) {
  if (incidentes.length === 0) {
    return <Vacio>Todavía no se ha registrado ningún aviso ni incidente.</Vacio>
  }
  return (
    <>
      <Poblacion>
        {seMuestran(incidentes.length, total, 'registro', 'registros')}, del más reciente al más
        antiguo. Los avisos van en azul: informan y no se cierran (RF-13).
      </Poblacion>
      <Tabla encabezados={['Tipo', 'Lote', 'Compuerta', 'Motivo', 'Filas', 'Abierto', 'Estado']} derecha={[4]}>
        {incidentes.map((i) => {
          const nivel = i.severidad === 'INCIDENTE' ? 'incidente' : 'aviso'
          return (
            <Fragment key={i.id}>
              <tr>
                <td className={`border-l-4 px-4 py-3 whitespace-nowrap ${COLOR[nivel].franja}`}>
                  <span className={`font-bold ${COLOR[nivel].texto}`}>
                    {i.severidad === 'INCIDENTE' ? 'Incidente' : 'Aviso'} {i.id}
                  </span>
                </td>
                <td className="px-4 py-3 font-mono whitespace-nowrap">{i.lote}</td>
                <td className="px-4 py-3 font-mono">{i.compuerta}</td>
                <td className="px-4 py-3 font-mono">{i.motivo}</td>
                <td className="px-4 py-3 text-right">{conteo(i.filas)}</td>
                <td className="px-4 py-3 whitespace-nowrap">{fechaYHora(i.abiertoEn)}</td>
                <td className="px-4 py-3 whitespace-nowrap">
                  {i.severidad === 'AVISO' ? (
                    <span className="font-semibold text-[#0b5394]">Informativo</span>
                  ) : i.estado === 'ABIERTO' ? (
                    <a href={`#incidente-${i.id}`} className="font-bold text-[#c62828] underline">Abierto</a>
                  ) : (
                    <span className="font-semibold text-[#5b5b5b]">Cerrado</span>
                  )}
                </td>
              </tr>
              {i.severidad === 'INCIDENTE' && i.estado === 'CERRADO' && (
                <tr>
                  <td />
                  <td colSpan={6} className="px-4 pb-3 text-[11px] font-semibold text-[#5b5b5b]">
                    Causa: {nombreDeLaCausa(i.causa ?? '')}. Decisión: {i.decision}
                    {' '}· Lo cerró {i.cerradoPor} el {i.cerradoEn ? fechaYHora(i.cerradoEn) : '—'}
                    {i.reprocesarLote ? ' · El lote quedó marcado para reprocesarse' : ''}
                  </td>
                </tr>
              )}
            </Fragment>
          )
        })}
      </Tabla>
    </>
  )
}

// ── Corridas, linaje y cuarentena (CU-05 · 4 y 5, RF-12) ─────────────────────

function Corridas({ corridas, total }: { corridas: Corrida[]; total: number }) {
  if (corridas.length === 0) {
    return <Vacio>Todavía no hay corridas registradas.</Vacio>
  }
  return (
    <>
      <Poblacion>
        {seMuestran(corridas.length, total, 'corrida registrada', 'corridas registradas')}, de la más
        reciente a la más antigua. Elige un lote para ver su linaje y su cuarentena (CU-05 · 4).
      </Poblacion>
      <Tabla encabezados={['Lote', 'Iniciada', 'Resultado', 'Leídas', 'Aceptadas', 'En cuarentena', 'Duración']} derecha={[3, 4, 5, 6]}>
        {corridas.map((c, n) => (
          <tr key={`${c.lote}|${c.fecha}|${n}`}>
            <td className="px-4 py-3 whitespace-nowrap">
              <Link href={`/consola?lote=${encodeURIComponent(c.lote)}#lote`} className="font-mono font-bold text-[#158683] underline">
                {c.lote}
              </Link>
            </td>
            <td className="px-4 py-3 whitespace-nowrap">{fechaYHora(c.fecha)}</td>
            <td className="px-4 py-3"><Resultado corrida={c} /></td>
            <td className="px-4 py-3 text-right">{conteo(c.filasLeidas)}</td>
            <td className="px-4 py-3 text-right">{conteo(c.filasAceptadas)}</td>
            <td className="px-4 py-3 text-right">{conteo(c.filasEnCuarentena)}</td>
            <td className="px-4 py-3 text-right whitespace-nowrap">{duracion(c.duracionSegundos)}</td>
          </tr>
        ))}
      </Tabla>
    </>
  )
}

function Linaje({ corridas }: { corridas: Corrida[] }) {
  // linajeDeLote trae las corridas de la más antigua a la más reciente: la última es la
  // vigente (CU-05 · 5a).
  const vigente = corridas[corridas.length - 1]
  const detenido = vigente.resultado === 'RECHAZADA' || vigente.resultado === 'FALLIDA'
  const capas = [
    { capa: 'Archivo', cifra: vigente.lote, nota: 'El lote de la fuente' },
    { capa: 'Cruda', cifra: filas(vigente.filasLeidas), nota: 'Leídas del alcance' },
    { capa: 'Compuertas', cifra: filas(vigente.filasEnCuarentena), nota: 'Apartadas a cuarentena' },
    { capa: 'Intermedia', cifra: filas(vigente.filasAceptadas), nota: detenido ? 'El lote se detuvo' : 'Aceptadas' },
  ]
  return (
    <>
      <Poblacion>
        Corrida vigente: la del {fechaYHora(vigente.fecha)}, {nombreDelResultado(vigente.resultado).toLowerCase()}
        {corridas.length > 1 ? `. El lote se corrió ${conteo(corridas.length)} veces; abajo, todas en orden` : ''}.
      </Poblacion>
      <ol className="mt-4 flex items-stretch gap-2">
        {capas.map((c, n) => (
          <li key={c.capa} className="flex flex-1 items-center gap-2">
            <div className={`flex-1 rounded-2xl border-l-8 bg-white p-4 shadow-sm ${COLOR[n === 3 && detenido ? 'incidente' : 'neutro'].franja}`}>
              <p className="text-[11px] font-bold tracking-wider text-[#5b5b5b] uppercase">{c.capa}</p>
              <p className="mt-1 text-base font-extrabold text-[#2f2f2f]">{c.cifra}</p>
              <p className="text-[11px] font-semibold text-[#5b5b5b]">{c.nota}</p>
            </div>
            {n < capas.length - 1 && <span aria-hidden className="text-xl font-bold text-[#5b5b5b]">→</span>}
          </li>
        ))}
      </ol>
      {corridas.length > 1 && (
        <Tabla encabezados={['Corrida', 'Iniciada', 'Resultado', 'Leídas', 'Aceptadas', 'En cuarentena']} derecha={[3, 4, 5]}>
          {corridas.map((c, n) => (
            <tr key={`${c.fecha}|${n}`}>
              <td className="px-4 py-3 whitespace-nowrap">{n + 1}{n === corridas.length - 1 ? ' · vigente' : ''}</td>
              <td className="px-4 py-3 whitespace-nowrap">{fechaYHora(c.fecha)}</td>
              <td className="px-4 py-3"><Resultado corrida={c} /></td>
              <td className="px-4 py-3 text-right">{conteo(c.filasLeidas)}</td>
              <td className="px-4 py-3 text-right">{conteo(c.filasAceptadas)}</td>
              <td className="px-4 py-3 text-right">{conteo(c.filasEnCuarentena)}</td>
            </tr>
          ))}
        </Tabla>
      )}
      <p className="mt-2 text-[11px] font-semibold text-[#5b5b5b]">
        El contrato 0.2.1 todavía no trae el nombre del archivo, los pasos por compuerta ni las
        filas de la capa de consumo (docs/analisis/openapi/README.md): el linaje se arma con los
        conteos de la corrida.
      </p>
    </>
  )
}

function Cuarentena({ lote, filas: apartadas, total }: { lote: string; filas: FilaEnCuarentena[]; total: number }) {
  return (
    <div className="mt-8">
      <h3 className="text-base font-bold text-[#2f2f2f]">Filas en cuarentena</h3>
      {apartadas.length === 0 ? (
        <Vacio>La corrida vigente del lote {lote} no apartó ninguna fila.</Vacio>
      ) : (
        <>
          <Poblacion>
            {seMuestran(apartadas.length, total, 'fila', 'filas')} que apartó la corrida vigente del
            lote {lote}, con su motivo y tal como llegaron.
          </Poblacion>
          <Tabla encabezados={['Motivo', 'Compuerta', 'La fila, tal como llegó']}>
            {apartadas.map((f, n) => (
              <tr key={n}>
                <td className="px-4 py-3 align-top font-mono whitespace-nowrap">{f.motivo}</td>
                <td className="px-4 py-3 align-top font-mono">{f.compuerta ?? '—'}</td>
                <td className="px-4 py-3 font-mono text-[11px] break-words">{textoDeFila(f.fila)}</td>
              </tr>
            ))}
          </Tabla>
        </>
      )}
    </div>
  )
}

// ── Piezas ───────────────────────────────────────────────────────────────────

function Resultado({ corrida }: { corrida: Corrida }) {
  const nivel = nivelDeCorrida(corrida.resultado)
  return (
    <span className={`inline-flex items-center gap-1.5 font-bold whitespace-nowrap ${COLOR[nivel].texto}`}>
      <span aria-hidden className={`h-2.5 w-2.5 rounded-full ${COLOR[nivel].punto}`} />
      {nombreDelResultado(corrida.resultado)}
    </span>
  )
}

function Seccion({ id, titulo, children }: { id: string; titulo: string; children: ReactNode }) {
  return (
    <section id={id} className="mt-10 scroll-mt-6">
      <h2 className="text-lg font-bold text-[#2f2f2f]">{titulo}</h2>
      {children}
    </section>
  )
}

function Tabla({ encabezados, derecha = [], children }: { encabezados: string[]; derecha?: number[]; children: ReactNode }) {
  return (
    <div className="mt-3 overflow-x-auto rounded-2xl bg-white shadow-sm">
      <table className="min-w-full border-collapse text-sm text-[#2f2f2f]">
        <thead className="border-b-2 border-[#e7dfd0] text-left text-[11px] font-bold tracking-wider text-[#5b5b5b] uppercase">
          <tr>
            {encabezados.map((e, n) => (
              <th key={e} className={`px-4 py-3 ${derecha.includes(n) ? 'text-right' : ''}`}>{e}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-[#e7dfd0]">{children}</tbody>
      </table>
    </div>
  )
}

function Dato({ nombre, children }: { nombre: string; children: ReactNode }) {
  return (
    <div>
      <dt className="text-[11px] font-bold tracking-wider text-[#5b5b5b] uppercase">{nombre}</dt>
      <dd className="mt-0.5 font-semibold text-[#2f2f2f]">{children}</dd>
    </div>
  )
}

function Poblacion({ children }: { children: ReactNode }) {
  return <p className="mt-1 text-[11px] font-semibold text-[#5b5b5b]">{children}</p>
}

function Vacio({ children }: { children: ReactNode }) {
  return <p className="mt-3 rounded-2xl bg-white px-6 py-5 text-sm font-medium text-[#5b5b5b] shadow-sm">{children}</p>
}

function Falla({ titulo, motivo, children }: { titulo: string; motivo: string; children?: ReactNode }) {
  return (
    <div role="alert" className="mt-6 rounded-md border border-red-200 bg-red-50 p-4 text-red-700">
      <p className="font-bold">{titulo}</p>
      <p className="mt-1 text-sm">La analítica {motivo}.</p>
      {children && <p className="mt-1 text-sm">{children}</p>}
    </div>
  )
}

// RNF-16 en una lista: cuántos se ven de cuántos hay. «Se muestran 10 de 38 corridas registradas».
function seMuestran(vistos: number, total: number, uno: string, varios: string) {
  return `${vistos === 1 ? 'Se muestra' : 'Se muestran'} ${conteo(vistos)} de ${conteo(total)} ${total === 1 ? uno : varios}`
}
