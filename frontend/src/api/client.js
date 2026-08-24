import { useAuthStore } from '../stores/auth'
import router from '../router'
import { getCookie } from '../utils/cookies'

// CORRECCIÓN vs. versión original: la URL ya no está hardcodeada ni
// duplicada en varios archivos (estaba repetida en api.js y en
// exportarCSV() dentro de libros.html). Ahora vive en una sola variable de
// entorno, configurable por despliegue sin tocar código.
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

// La sesión ahora es una cookie httpOnly (`sid`) que el navegador maneja
// solo — por eso `credentials: 'include'` en cada fetch. Ya no existe un
// token que adjuntar a mano.
function jsonHeaders(extra = {}) {
  return { 'Content-Type': 'application/json', ...extra }
}

// CSRF de doble-envío: el backend lee esta cookie (no-httpOnly a propósito)
// y la compara contra el header en cada mutación.
function csrfHeader() {
  const token = getCookie('XSRF-TOKEN')
  return token ? { 'X-XSRF-TOKEN': token } : {}
}

async function handle(response) {
  if (response.status === 401) {
    const auth = useAuthStore()
    auth.user = null
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
  get: (path) =>
    fetch(`${API_URL}${path}`, { credentials: 'include' }).then(handle),

  post: (path, body) =>
    fetch(`${API_URL}${path}`, {
      method: 'POST',
      credentials: 'include',
      headers: jsonHeaders(csrfHeader()),
      body: JSON.stringify(body)
    }).then(handle),

  put: (path, body) =>
    fetch(`${API_URL}${path}`, {
      method: 'PUT',
      credentials: 'include',
      headers: jsonHeaders(csrfHeader()),
      body: JSON.stringify(body)
    }).then(handle),

  patch: (path, body) =>
    fetch(`${API_URL}${path}`, {
      method: 'PATCH',
      credentials: 'include',
      headers: jsonHeaders(csrfHeader()),
      body: JSON.stringify(body)
    }).then(handle),

  delete: (path) =>
    fetch(`${API_URL}${path}`, {
      method: 'DELETE',
      credentials: 'include',
      headers: csrfHeader()
    }).then(handle),

  // Para descargas binarias (ej. export CSV) que necesitan el blob crudo
  getBlob: async (path) => {
    const response = await fetch(`${API_URL}${path}`, { credentials: 'include' })
    if (!response.ok) throw new Error('Error al exportar')
    return response.blob()
  }
}
