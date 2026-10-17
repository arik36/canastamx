//export default function Consola() { return <div>Consola del Operador</div> }

import Sidebar from '@/components/Sidebar'

export default function Consola() {
  return (
    <>
      {/* Aviso que solo se ve en pantallas menores a 1025px */}
      <div className="flex h-screen w-full flex-col items-center justify-center bg-[#f0eadf] p-8 text-center min-[1025px]:hidden">
        <div className="max-w-sm rounded-2xl border border-[#e7dfd0] bg-white p-6 shadow-[0_10px_30px_-20px_rgba(47,47,47,0.4)]">
          <div className="mb-4 text-4xl">🖥️</div>
          <h2 className="text-lg font-extrabold text-[#2f2f2f]">Pantalla demasiado pequeña</h2>
          <p className="mt-2 text-sm font-medium text-[#5b5b5b]">
            Por decisión de diseño (D-08), esta consola requiere resolución de escritorio (mínimo 1025px). 
            Por favor, maximiza tu ventana.
          </p>
        </div>
      </div>

      {/* Consola real que solo se ve en pantallas de 1025px o más */}
      <div className="hidden h-screen w-full bg-[#f0eadf] min-[1025px]:flex">
        <Sidebar rol="Operador" correo="operador@example.com" />
        <main className="flex-1 overflow-y-auto p-10">
          <h1 className="text-2xl font-extrabold text-[#2f2f2f]">Consola del Operador</h1>
        </main>
      </div>
    </>
  )
}