import { NextResponse } from 'next/server';

import { iniciarSesion, urlDelDominio } from '@/lib/dominio.mjs';
import { destinoPorRol } from '@/lib/rutas.mjs';

// El acceso llama a POST /api/v1/sesiones de C1 desde el servidor de la web: el token
// queda en una cookie httpOnly y nunca llega al JavaScript del navegador.
export async function POST(request: Request) {
  const { correo, contrasena } = await request.json().catch(() => ({}));

  const resultado = await iniciarSesion({ correo, contrasena }, { dominioUrl: urlDelDominio(), fetch });
  if (!('sesion' in resultado)) {
    return NextResponse.json({ error: resultado.error }, { status: resultado.estado });
  }

  const { token, expiraEn, rol } = resultado.sesion;
  const response = NextResponse.json({ rol, destino: destinoPorRol(rol) });

  // Las dos cookies vencen con el token. El correo no se guarda: cada vista lo pide a
  // GET /api/v1/cuentas/yo (D-10).
  const opciones = {
    httpOnly: true,
    sameSite: 'lax' as const,
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    expires: expiraEn,
  };
  response.cookies.set('token', token, opciones);
  response.cookies.set('rol', rol, opciones);

  return response;
}
