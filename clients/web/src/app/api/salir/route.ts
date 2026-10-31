import { NextResponse } from 'next/server';

// Cierra la sesión de la web: borra sus cookies y manda al acceso. Lo usan el enlace
// «Salir» y las vistas cuando el dominio ya no reconoce el token (vencido o inválido).
// La dirección va relativa: en esta ruta `request.url` dice localhost aunque la web se
// abra por 127.0.0.1, por la IP de la red o detrás de un proxy.
export function GET() {
  const response = new NextResponse(null, { status: 307, headers: { Location: '/acceso' } });
  // «correo» es la cookie de la versión anterior; se borra para no dejarla atrás.
  for (const nombre of ['token', 'rol', 'correo']) {
    response.cookies.delete(nombre);
  }
  return response;
}
