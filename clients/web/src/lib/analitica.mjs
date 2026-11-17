// clients/web/src/lib/analitica.mjs

export function urlDeAnalitica(entorno = process.env) {
  return (entorno.ANALITICA_URL || 'http://localhost:4011').replace(/\/+$/, '')
}

export async function leerAnomalias(token, { analiticaUrl, fetch }) {
  try {
    const respuesta = await fetch(`${analiticaUrl}/api/v1/anomalias`, {
      // AQUÍ va el encabezado que pidió Liz para validar la seguridad
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/json'
      },
      cache: 'no-store'
    })
    
    if (!respuesta.ok) {
      return { estado: 'error', motivo: `El servidor respondió con error ${respuesta.status}` }
    }
    
    const datos = await respuesta.json()
    return { estado: 'ok', anomalias: datos }
  } catch (error) {
    return { estado: 'error', motivo: 'No se pudo contactar al servicio de analítica.' }
  }
}