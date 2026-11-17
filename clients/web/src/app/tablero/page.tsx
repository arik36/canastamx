import Sidebar from '@/components/Sidebar'
import { exigirCuenta } from '@/lib/sesion'
import { cookies } from 'next/headers'
import { urlDeAnalitica, leerAnomalias } from '@/lib/analitica.mjs'

// Le explicamos a TypeScript qué forma tienen los datos del simulador (Errores 2 y 3)
interface Anomalia {
  articulo: string;
  precio: number | string;
  poblacion: string;
  periodo: string;
}

export default async function Page() {
  const cuenta = await exigirCuenta('ANALISTA')
  
  // FIX 1: Ahora usamos await antes de leer las cookies
  const cookieStore = await cookies()
  const token = cookieStore.get('token')?.value

  const analiticaUrl = urlDeAnalitica()
  const respuesta = await leerAnomalias(token, { analiticaUrl, fetch })

  return (
    <div className="flex h-screen w-full overflow-x-auto bg-[#f0eadf]">
      <div className="flex h-full min-w-[1025px] flex-1">
        <Sidebar cuenta={cuenta} />
        <main className="relative flex-1 overflow-y-auto p-10">
          <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 lg:hidden rounded-xl bg-[#d32f2f] px-6 py-3 text-sm font-bold text-white shadow-xl whitespace-nowrap">
            ⚠️ Pantalla pequeña: Desplázate lateralmente para ver la interfaz.
          </div>
          
          <h1 className="text-2xl font-extrabold text-[#2f2f2f] capitalize mb-6">
            Tablero del Analista
          </h1>

          <div className="bg-yellow-100 text-yellow-800 px-4 py-3 rounded-md mb-6 font-bold inline-block">
            ⚠️ Mostrando Datos Simulados (Prism)
          </div>

          {respuesta.estado === 'error' ? (
            <div className="bg-red-50 text-red-600 p-4 border border-red-200 rounded-md">
              <p className="font-bold">No pudimos cargar las anomalías en este momento.</p>
              <p className="text-sm mt-1">Detalle: {respuesta.motivo}</p>
            </div>
          ) : (
            <div className="overflow-x-auto bg-white rounded-lg shadow">
              <table className="min-w-full border-collapse">
                <thead className="bg-gray-100 border-b-2 border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-bold text-gray-700 uppercase tracking-wider">Artículo</th>
                    <th className="px-6 py-3 text-left text-sm font-bold text-gray-700 uppercase tracking-wider">Precio Atípico</th>
                    <th className="px-6 py-3 text-left text-sm font-bold text-gray-700 uppercase tracking-wider">Población (RNF-16)</th>
                    <th className="px-6 py-3 text-left text-sm font-bold text-gray-700 uppercase tracking-wider">Periodo (RNF-16)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {/* FIX 2 y 3: Le pasamos los tipos a item e index */}
                  {respuesta.anomalias?.map((item: Anomalia, index: number) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{item.articulo}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-[#d32f2f]">${item.precio}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.poblacion}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.periodo}</td>
                    </tr>
                  ))}
                  {respuesta.anomalias?.length === 0 && (
                    <tr>
                      {/* FIX 4: Cambiamos "4" por {4} */}
                      <td colSpan={4} className="px-6 py-8 text-center text-gray-500 font-medium">
                        No se encontraron anomalías en este periodo.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}