import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const { correo, contrasena } = await request.json();
    const dominioUrl = process.env.DOMINIO_URL || 'http://127.0.0.1:4010';

    // Llamamos al backend de C1 (o al simulador)
    const res = await fetch(`${dominioUrl}/api/v1/sesiones`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ correo, contrasena }),
    });

    if (!res.ok) {
      return NextResponse.json({ error: 'Credenciales inválidas' }, { status: 401 });
    }

    const data = await res.json();
    
    // Creamos la respuesta y le inyectamos las cookies httpOnly
    const response = NextResponse.json({ success: true, rol: data.rol });
    
    response.cookies.set('token', data.token, { httpOnly: true, path: '/' });
    response.cookies.set('rol', data.rol, { httpOnly: true, path: '/' });
    // Guardamos el correo temporalmente porque el backend aún no lo hace (D-10)
    response.cookies.set('correo', correo, { httpOnly: true, path: '/' }); 

    return response;
  } catch (error) {
    return NextResponse.json({ error: 'Error del servidor' }, { status: 500 });
  }
}
