/**
 * Utilidad mínima de cookies.
 *
 * La sesión ya NO se maneja aquí: el backend emite la cookie `sid`
 * (httpOnly, no accesible desde JS) al hacer login, y el navegador la
 * reenvía solo porque `client.js` pide `credentials: 'include'` en cada
 * fetch. Lo único que este archivo sigue exponiendo es la lectura de la
 * cookie `XSRF-TOKEN` (no-httpOnly a propósito, es el lado "legible" del
 * patrón CSRF de doble-envío) para reenviarla como header en mutaciones.
 */

export function getCookie(name) {
  const match = document.cookie
    .split('; ')
    .find((row) => row.startsWith(`${name}=`))

  if (!match) return null
  return decodeURIComponent(match.split('=').slice(1).join('='))
}
