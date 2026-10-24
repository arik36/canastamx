import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

import { decidir } from '@/lib/rutas.mjs'

// Primera barrera: sin sesión manda al acceso, y cada rol a sus vistas (P-07). La
// regla está en lib/rutas.mjs, que prueba `npm test`. La cookie de rol puede
// cambiarse a mano, por eso cada vista vuelve a preguntar la cuenta al dominio
// (lib/sesion.ts) antes de mostrarse.
export function proxy(request: NextRequest) {
  const decision = decidir(request.nextUrl.pathname, request.cookies.get('rol')?.value)
  if ('redirigeA' in decision) {
    return NextResponse.redirect(new URL(decision.redirigeA, request.url))
  }
  return NextResponse.next()
}

// Esto le dice a Next.js que ejecute este archivo en todas las rutas
export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}
