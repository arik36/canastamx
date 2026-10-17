export default function Sidebar({ rol, correo }: { rol: string; correo: string }) {
  return (
    <aside className="flex w-[260px] shrink-0 flex-col border-r border-[#e7dfd0] bg-white h-screen">
      <div className="px-5 py-6">
        <div className="mt-1.5 text-[10px] font-semibold uppercase tracking-wider text-[#5b5b5b]">
          Consola de {rol}
        </div>
      </div>
      
      <nav className="flex flex-1 flex-col gap-1 px-3">
        {/* Aquí irán los botones de navegación después */}
      </nav>

      <div className="border-t border-[#e7dfd0] p-3">
        <div className="flex items-center gap-3 rounded-xl px-2 py-2">
          <div className="grid h-10 w-10 place-items-center rounded-full bg-[#2f2f2f] text-sm font-bold text-white uppercase">
            {correo.charAt(0)}
          </div>
          <div className="min-w-0 leading-tight">
            <div className="truncate text-sm font-bold text-[#2f2f2f]">{correo}</div>
            <div className="truncate text-[11px] text-[#5b5b5b]">{rol}</div>
          </div>
        </div>
      </div>
    </aside>
  )
}