import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

//export function middleware(request: NextRequest) {
export function proxy(request: NextRequest) {
  const rol = request.cookies.get('rol')?.value
  const path = request.nextUrl.pathname

  // Permitir archivos estáticos y API
  if (path.startsWith('/_next') || path.startsWith('/api') || path === '/favicon.ico') {
    return NextResponse.next()
  }

  // Si no tiene sesión y no está en acceso, lo mandamos a login
  if (!rol && path !== '/acceso') {
    return NextResponse.redirect(new URL('/acceso', request.url))
  }

  // Si ya tiene sesión e intenta ir al login, lo mandamos a su panel
  if (rol && path === '/acceso') {
    if (rol === 'ANALISTA') return NextResponse.redirect(new URL('/tablero', request.url))
    if (rol === 'OPERADOR') return NextResponse.redirect(new URL('/consola', request.url))
  }

  // Protegemos las rutas del Analista
  if ((path.startsWith('/tablero') || path.startsWith('/detalle')) && rol !== 'ANALISTA') {
    return NextResponse.redirect(new URL('/acceso', request.url))
  }

  // Protegemos las rutas del Operador
  if ((path.startsWith('/consola') || path.startsWith('/cola')) && rol !== 'OPERADOR') {
    return NextResponse.redirect(new URL('/acceso', request.url))
  }

  return NextResponse.next()
}

// Esto le dice a Next.js que ejecute este archivo en todas las rutas
export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}