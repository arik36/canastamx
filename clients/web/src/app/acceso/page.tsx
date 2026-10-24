'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function Acceso() {
  const router = useRouter()
  const [correo, setCorreo] = useState('')
  const [contrasena, setContrasena] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      // Llamamos a nuestro propio servidor que acabamos de crear
      const res = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ correo, contrasena })
      })

      const data = await res.json().catch(() => ({}))

      // El servidor dice por qué no entró (credenciales, cuenta de la app o el dominio
      // sin responder) y, si entró, a dónde va según el rol: tablero o consola (P-07).
      if (!res.ok || !data.destino) {
        setError(data.error ?? 'No se pudo iniciar sesión. Verifica tus datos.')
        return
      }
      router.push(data.destino)
    } catch {
      setError('No se pudo contactar al servidor de la web.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f0eadf]">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-[0_10px_30px_-20px_rgba(47,47,47,0.4)]">
        <h1 className="mb-2 text-center text-2xl font-extrabold text-[#2f2f2f]">
          CanastaMX
        </h1>
        {/* Aquí está el RF-23: No somos PROFECO */}
        <p className="mb-6 text-center text-sm font-bold text-[#d32f2f]">
          No somos PROFECO
        </p>
        
        <form onSubmit={handleLogin} className="flex flex-col gap-4">
          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-bold uppercase tracking-wide text-[#5b5b5b]">Correo electrónico</span>
            <input 
              type="email" 
              value={correo}
              onChange={(e) => setCorreo(e.target.value)}
              className="rounded-xl border border-[#e7dfd0] px-4 py-3 text-sm font-semibold text-[#2f2f2f] focus:border-[#23bbb7] focus:outline-none focus:ring-2 focus:ring-[#23bbb7]/25"
              required 
            />
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-[11px] font-bold uppercase tracking-wide text-[#5b5b5b]">Contraseña</span>
            <input 
              type="password" 
              value={contrasena}
              onChange={(e) => setContrasena(e.target.value)}
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