import { useAuthStore } from '../stores/auth'
import router from '../router'

// CORRECCIÓN vs. versión original: la URL ya no está hardcodeada ni
// duplicada en varios archivos (estaba repetida en api.js y en
// exportarCSV() dentro de libros.html). Ahora vive en una sola variable de
// entorno, configurable por despliegue sin tocar código.
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

function authHeaders(extra = {}) {
  const auth = useAuthStore()
  const headers = { 'Content-Type': 'application/json', ...extra }
  if (auth.token) headers.Authorization = `Bearer ${auth.token}`
  return headers
}

async function handle(response) {
  if (response.status === 401) {
    const auth = useAuthStore()
    auth.logout()
    router.push('/login')
    throw new Error('Sesión expirada')
  }

  // Respuestas sin cuerpo (ej. algunos 204)
  const contentType = response.headers.get('content-type') || ''
  const data = contentType.includes('application/json') ? await response.json() : null

  if (!response.ok) {
    throw new Error(data?.error || 'Error en la solicitud')
  }

  return data
}

export const http = {
  get: (path, { auth = true } = {}) =>
    fetch(`${API_URL}${path}`, { headers: auth ? authHeaders() : {} }).then(handle),

  post: (path, body, { auth = true } = {}) =>
    fetch(`${API_URL}${path}`, {
      method: 'POST',
      headers: auth ? authHeaders() : { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    }).then(handle),

  put: (path, body) =>
    fetch(`${API_URL}${path}`, {
      method: 'PUT',
      headers: authHeaders(),
      body: JSON.stringify(body)
    }).then(handle),

  patch: (path, body) =>
    fetch(`${API_URL}${path}`, {
      method: 'PATCH',
      headers: authHeaders(),
      body: JSON.stringify(body)
    }).then(handle),

  delete: (path) =>
    fetch(`${API_URL}${path}`, { method: 'DELETE', headers: authHeaders() }).then(handle),

  // Para descargas binarias (ej. export CSV) que necesitan el blob crudo
  getBlob: async (path) => {
    const response = await fetch(`${API_URL}${path}`, { headers: authHeaders() })
    if (!response.ok) throw new Error('Error al exportar')
    return response.blob()
  }
}
