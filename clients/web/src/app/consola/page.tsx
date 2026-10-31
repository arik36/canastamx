//export default function Consola() { return <div>Consola del Operador</div> }

import Sidebar from '@/components/Sidebar'
import { exigirCuenta } from '@/lib/sesion'

export default async function Page() {
  const cuenta = await exigirCuenta('OPERADOR')

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
          <h1 className="text-2xl font-extrabold text-[#2f2f2f] capitalize">
            Consola del Operador
          </h1>
        </main>
      </div>
    </div>
  )
}