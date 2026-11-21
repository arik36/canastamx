import { cookies } from 'next/headers'

import Sidebar from '@/components/Sidebar'
import {
  conteo,
  esSimulador,
  leerAnomalias,
  nombreDelArticulo,
  textoDePoblacion,
  urlDeAnalitica,
  variacionEnPorcentaje,
} from '@/lib/analitica.mjs'
import { exigirCuenta } from '@/lib/sesion'

// Vista 2 del inventario, con la tabla de anomalías (el índice salió con el recorte del
// 5 de noviembre). Las cifras salen de GET /api/v1/anomalias, pedida desde el servidor
// con el token de la sesión: aquí no hay ningún dato escrito.
export default async function Page() {
  const cuenta = await exigirCuenta('ANALISTA')
  const token = (await cookies()).get('token')?.value ?? ''
  const lectura = await leerAnomalias(token, { analiticaUrl: urlDeAnalitica(), fetch })

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
          <h1 className="mb-6 text-2xl font-extrabold text-[#2f2f2f] capitalize">
            Tablero del Analista
          </h1>

          {esSimulador() && (
            <p className="mb-6 inline-block rounded-md bg-yellow-100 px-4 py-3 text-sm font-bold text-yellow-800">
              ⚠️ Datos del simulador del contrato (Prism): son ejemplos, no mediciones.
            </p>
          )}

          {lectura.estado === 'ok' ? (
            <section>
              <h2 className="text-lg font-bold text-[#2f2f2f]">Artículos anómalos</h2>
              {/* RNF-16: la población y el periodo de la respuesta, arriba de sus cifras */}
              <p className="mt-1 mb-4 text-sm text-gray-600">
                Variación de la mediana contra la quincena anterior, según P-15. Población:{' '}
                {textoDePoblacion(lectura.poblacion)}.
              </p>
              <div className="overflow-x-auto rounded-lg bg-white shadow">
                <table className="min-w-full border-collapse text-sm">
                  <thead className="border-b-2 border-gray-200 bg-gray-100 text-left text-xs font-bold tracking-wider text-gray-700 uppercase">
                    <tr>
                      <th className="px-6 py-3">Artículo</th>
                      <th className="px-6 py-3">Entidad</th>
                      <th className="px-6 py-3">Quincena</th>
                      <th className="px-6 py-3 text-right">Variación</th>
                      <th className="px-6 py-3 text-right">Observaciones</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {lectura.articulos.map((fila) => (
                      <tr
                        key={`${fila.articulo.producto}|${fila.articulo.presentacion}|${fila.entidad}|${fila.quincena}`}
                        className="hover:bg-gray-50"
                      >
                        <td className="px-6 py-4 text-gray-900">{nombreDelArticulo(fila.articulo)}</td>
                        <td className="px-6 py-4 text-gray-700">{fila.entidad}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-gray-700">{fila.quincena}</td>
                        <td className="px-6 py-4 text-right font-bold whitespace-nowrap text-[#d32f2f]">
                          {variacionEnPorcentaje(fila.variacion)}
                        </td>
                        <td className="px-6 py-4 text-right text-gray-700">{conteo(fila.observaciones)}</td>
                      </tr>
                    ))}
                    {lectura.articulos.length === 0 && (
                      <tr>
                        <td colSpan={5} className="px-6 py-8 text-center font-medium text-gray-500">
                          Ninguna variación pasa el umbral de P-15 en esta población.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
              <p className="mt-2 text-xs text-gray-500">
                Observaciones: las menos de las dos quincenas que se comparan.
              </p>
            </section>
          ) : (
            <div className="rounded-md border border-red-200 bg-red-50 p-4 text-red-700">
              <p className="font-bold">No se pudieron leer las anomalías.</p>
              <p className="mt-1 text-sm">La analítica {lectura.motivo}.</p>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
