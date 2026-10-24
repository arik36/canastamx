import Link from 'next/link'

import type { Cuenta } from '@/lib/sesion'

// El correo y el rol vienen de GET /api/v1/cuentas/yo (D-10), que pide cada vista con
// exigirCuenta(). Nunca un nombre: la cuenta no tiene (P-13).
export default function Sidebar({ cuenta }: { cuenta: Cuenta }) {
  const { correo, rol } = cuenta

  return (
    <aside className="flex w-[260px] shrink-0 flex-col border-r border-[#e7dfd0] bg-white h-screen">
      <div className="px-5 py-6">
        <div className="mt-1.5 text-[10px] font-semibold uppercase tracking-wider text-[#5b5b5b]">
          Consola de {rol.toLowerCase()}
        </div>
      </div>
      
      {/* Enlaces de navegación dependientes del rol */}
      <nav className="flex flex-1 flex-col gap-1 px-3">
        {rol === 'ANALISTA' && (
          <>
            <Link href="/tablero" className="rounded-lg px-3 py-2 text-sm font-bold text-[#5b5b5b] hover:bg-[#f0eadf]">Tablero</Link>
            <Link href="/detalle" className="rounded-lg px-3 py-2 text-sm font-bold text-[#5b5b5b] hover:bg-[#f0eadf]">Detalle</Link>
          </>
        )}
        {rol === 'OPERADOR' && (
          <>
            <Link href="/consola" className="rounded-lg px-3 py-2 text-sm font-bold text-[#5b5b5b] hover:bg-[#f0eadf]">Consola</Link>
            <Link href="/cola" className="rounded-lg px-3 py-2 text-sm font-bold text-[#5b5b5b] hover:bg-[#f0eadf]">Cola</Link>
          </>
        )}
      </nav>

      <div className="border-t border-[#e7dfd0] p-3">
        <div className="flex items-center gap-3 rounded-xl px-2 py-2">
          <div className="grid h-10 w-10 place-items-center rounded-full bg-[#2f2f2f] text-sm font-bold text-white uppercase">
            {correo ? correo.charAt(0).toUpperCase() : 'U'}
          </div>
          <div className="min-w-0 leading-tight">
            <div className="truncate text-sm font-bold text-[#2f2f2f]">{correo}</div>
            <div className="truncate text-[11px] text-[#5b5b5b]">{rol}</div>
          </div>
        </div>
        {/* <a> y no <Link>: Link precarga la ruta, y precargar /api/salir cerraría la sesión */}
        <a href="/api/salir" className="mt-1 block rounded-lg px-3 py-2 text-sm font-bold text-[#5b5b5b] hover:bg-[#f0eadf]">Salir</a>
      </div>
    </aside>
  )
}