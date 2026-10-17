//export default function Acceso() { return <div>Pantalla de Acceso</div> }

//useRouter: Es la herramienta de Next.js para cambiar de 
// página sin recargar el navegador.
'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function Acceso() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    //fetch('/api/v1/sesiones'): Hace la petición exacta 
    // a la ruta que tu compañero C1 construyó.
    try {
      // Aquí nos conectamos a la API que hizo C1
      const res = await fetch('/api/v1/sesiones', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      })

      if (!res.ok) throw new Error('Credenciales inválidas')

      const data = await res.json()
      
      //El condicional if (data.rol === ...): Es el núcleo de tu 
      // Paso 4. Lee el rol que devuelve el backend y te manda a /tablero o a /consola.
      // La magia de la redirección según el rol
      if (data.rol === 'Analista') {
        router.push('/tablero')
      } else if (data.rol === 'Operador') {
        router.push('/consola')
      } else {
        setError('Rol desconocido o sin acceso')
      }
    } catch (err) {
      setError('No se pudo iniciar sesión. Verifica tus datos.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f0eadf]">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-[0_10px_30px_-20px_rgba(47,47,47,0.4)]">
        <h1 className="mb-6 text-center text-2xl font-extrabold text-[#2f2f2f]">
          CanastaMX
        </h1>
        
        <form onSubmit={handleLogin} className="flex flex-col gap-4">
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-bold uppercase tracking-wide text-[#5b5b5b]">Correo electrónico</span>
            <input 
              type="email" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="rounded-xl border border-[#e7dfd0] px-4 py-3 text-sm font-semibold text-[#2f2f2f] focus:border-[#23bbb7] focus:outline-none focus:ring-2 focus:ring-[#23bbb7]/25"
              required 
            />
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-bold uppercase tracking-wide text-[#5b5b5b]">Contraseña</span>
            <input 
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="rounded-xl border border-[#e7dfd0] px-4 py-3 text-sm font-semibold text-[#2f2f2f] focus:border-[#23bbb7] focus:outline-none focus:ring-2 focus:ring-[#23bbb7]/25"
              required 
            />
          </label>

          {error && <p className="text-sm font-bold text-[#d32f2f]">{error}</p>}

          <button 
            type="submit" 
            disabled={loading}
            className="mt-2 rounded-xl bg-[#137a77] py-3 text-sm font-bold text-white transition hover:bg-[#158683] disabled:opacity-50"
          >
            {loading ? 'Entrando...' : 'Iniciar sesión'}
          </button>
        </form>
      </div>
    </div>
  )
}


