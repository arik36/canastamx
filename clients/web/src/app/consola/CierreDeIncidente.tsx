'use client'

import { startTransition, useActionState, type FormEvent } from 'react'

import { CAUSAS, LARGO_DE_LA_DECISION } from '@/lib/operacion.mjs'

import { cerrarConCausa, type Rechazo } from './acciones'

// «Cerrar con causa» (diseno.md, «Historial»), sólo para los incidentes abiertos: los
// avisos no se cierran (RF-13). Si el cierre falla, el motivo sale aquí mismo; si sale
// bien, la consola se vuelve a pedir con el incidente ya cerrado en el historial.
export default function CierreDeIncidente({ id }: { id: string }) {
  const [rechazo, cerrar, cerrando] = useActionState<Rechazo | null, FormData>(cerrarConCausa, null)

  // Con onSubmit y no con <form action>: con action, React 19 vacía el formulario al
  // terminar, aunque el cierre haya fallado, y el <select> queda en «El archivo de la
  // fuente», una causa que nadie eligió. Así, lo escrito se queda como estaba.
  function enviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const datos = new FormData(evento.currentTarget)
    startTransition(() => cerrar(datos))
  }

  return (
    <details className="mt-4 rounded-xl border border-[#e7dfd0] bg-[#f0eadf]/40 px-4 py-3">
      <summary className="cursor-pointer text-sm font-bold text-[#c62828]">Cerrar con causa</summary>
      <form onSubmit={enviar} className="mt-3 flex flex-col gap-3">
        <input type="hidden" name="incidenteId" value={id} />
        <label className="flex flex-col gap-1">
          <span className="text-[11px] font-bold tracking-wide text-[#5b5b5b] uppercase">Causa</span>
          <select
            name="causa"
            required
            defaultValue=""
            className="rounded-xl border border-[#e7dfd0] bg-white px-3 py-2 text-sm font-semibold text-[#2f2f2f] focus:border-[#23bbb7] focus:ring-2 focus:ring-[#23bbb7]/25 focus:outline-none"
          >
            <option value="" disabled>Elige la causa</option>
            {Object.entries(CAUSAS).map(([valor, nombre]) => (
              <option key={valor} value={valor}>{nombre}</option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-[11px] font-bold tracking-wide text-[#5b5b5b] uppercase">
            Decisión: qué se hizo, en una o dos frases
          </span>
          <textarea
            name="decision"
            required
            rows={2}
            maxLength={LARGO_DE_LA_DECISION}
            className="rounded-xl border border-[#e7dfd0] bg-white px-3 py-2 text-sm text-[#2f2f2f] focus:border-[#23bbb7] focus:ring-2 focus:ring-[#23bbb7]/25 focus:outline-none"
          />
        </label>
        <label className="flex items-center gap-2 text-sm text-[#2f2f2f]">
          <input type="checkbox" name="reprocesarLote" value="si" />
          Dejar el lote marcado para reprocesarse cuando la fuente lo corrija
        </label>
        {rechazo && (
          <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm font-bold text-[#c62828]">
            {rechazo.motivo}
          </p>
        )}
        <button
          type="submit"
          disabled={cerrando}
          className="self-start rounded-xl bg-[#137a77] px-5 py-2 text-sm font-bold text-white hover:bg-[#158683] disabled:opacity-60"
        >
          {cerrando ? 'Cerrando…' : 'Cerrar el incidente'}
        </button>
      </form>
    </details>
  )
}
