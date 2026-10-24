import { NextResponse } from 'next/server';

// Cierra la sesión de la web: borra sus cookies y manda al acceso. Lo usan el enlace
// «Salir» y las vistas cuando el dominio ya no reconoce el token (vencido o inválido).
export function GET(request: Request) {
  const response = NextResponse.redirect(new URL('/acceso', request.url));
  // «correo» es la cookie de la versión anterior; se borra para no dejarla atrás.
  for (const nombre of ['token', 'rol', 'correo']) {
    response.cookies.delete(nombre);
  }
  return response;
}
