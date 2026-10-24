import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'

import { leerCuenta, urlDelDominio } from '@/lib/dominio.mjs'

export type Rol = 'ANALISTA' | 'OPERADOR'
export type Cuenta = { correo: string; rol: Rol }

/**
 * La cuenta de la sesión, preguntada al dominio con el token de la cookie (D-10), para
 * una vista que pide `rol`. Si el dominio no reconoce el token, o la cuenta es de otro
 * rol, cierra la sesión y manda al acceso. Al proxy sólo llegan vistas cuyo rol coincide
 * con la cookie, así que un rol distinto aquí es una cookie que no corresponde al token
 * (cambiada a mano, o un rol que cambió en el dominio): mandarla a otra vista haría que
 * el proxy la regresara, en un ciclo. El rol que decide es el del dominio.
 */
export async function exigirCuenta(rol: Rol): Promise<Cuenta> {
  const token = (await cookies()).get('token')?.value
  if (!token) {
    redirect('/api/salir')
  }
  const leida = await leerCuenta(token, { dominioUrl: urlDelDominio(), fetch })
  if (leida.estado === 'sin-sesion') {
    redirect('/api/salir')
  }
  if (leida.estado !== 'ok') {
    throw new Error('No se pudo leer la cuenta de la sesión: el servicio de dominio no respondió.')
  }
  if (leida.cuenta.rol !== rol) {
    redirect('/api/salir')
  }
  return leida.cuenta as Cuenta
}
