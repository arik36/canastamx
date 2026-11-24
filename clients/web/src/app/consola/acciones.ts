'use server'

import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'

import { urlDeAnalitica } from '@/lib/analitica.mjs'
import { cerrarIncidente, leerCierre } from '@/lib/operacion.mjs'

/** Por qué no se cerró, para decirlo junto al formulario. */
export type Rechazo = { motivo: string }

/**
 * Cierra un incidente con su causa (CU-04, pasos 5 y 6), desde el formulario de la
 * consola. Corre en el servidor de la web: el token sale de la cookie httpOnly y el
 * navegador nunca lo ve.
 *
 * Quien autoriza es la analítica, no esta función: verifica el token (firma, vencimiento
 * y rol OPERADOR) y le pregunta al dominio de quién es, para guardar su correo (D-11).
 * Si algo falla, regresa el motivo; lo escrito se queda en el formulario.
 */
export async function cerrarConCausa(_anterior: Rechazo | null, datos: FormData): Promise<Rechazo | null> {
  const token = (await cookies()).get('token')?.value
  if (!token) {
    redirect('/api/salir')
  }
  const pedido = leerCierre(datos)
  if (pedido.estado === 'error') {
    return { motivo: pedido.motivo }
  }
  const cierre = await cerrarIncidente(token, pedido.id, pedido.cierre,
    { analiticaUrl: urlDeAnalitica(), fetch })
  if (cierre.estado === 'error') {
    return { motivo: `No se cerró: la analítica ${cierre.motivo}.` }
  }
  // Fuera de cualquier try: redirect() lanza su propia señal (documentación de Next, «redirect»).
  redirect(`/consola?cerrado=${encodeURIComponent(pedido.id)}`)
}
