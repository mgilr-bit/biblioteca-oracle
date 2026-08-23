/**
 * Utilidad mínima de cookies para sustituir localStorage.
 *
 * IMPORTANTE (ver CORRECCIONES.md, punto de seguridad #1):
 * Estas cookies se leen/escriben desde JavaScript (document.cookie), por lo
 * que NO son httpOnly y siguen siendo accesibles a un ataque XSS, igual que
 * localStorage. La diferencia práctica frente a localStorage es:
 *   - Se puede fijar expiración, SameSite y Secure de forma centralizada.
 *   - El backend puede leer la cookie si se le pasa `credentials: 'include'`.
 * La forma robusta de eliminar el riesgo de robo de token vía XSS es que el
 * PROPIO BACKEND emita la cookie de sesión con flags `HttpOnly; Secure;
 * SameSite=Strict` en la respuesta de login, y el frontend deje de manejar
 * el token por completo. Este helper es un reemplazo directo de
 * localStorage tal como se pidió; la migración a cookie httpOnly emitida
 * por el servidor es la recomendación a futuro.
 */

const DEFAULT_DAYS = 7

export function setCookie(name, value, days = DEFAULT_DAYS) {
  const maxAge = days * 24 * 60 * 60
  const encoded = encodeURIComponent(value)
  const secure = window.location.protocol === 'https:' ? '; Secure' : ''
  document.cookie = `${name}=${encoded}; path=/; max-age=${maxAge}; SameSite=Lax${secure}`
}

export function getCookie(name) {
  const match = document.cookie
    .split('; ')
    .find((row) => row.startsWith(`${name}=`))

  if (!match) return null
  return decodeURIComponent(match.split('=').slice(1).join('='))
}

export function removeCookie(name) {
  document.cookie = `${name}=; path=/; max-age=0; SameSite=Lax`
}

export function setJSONCookie(name, obj, days = DEFAULT_DAYS) {
  setCookie(name, JSON.stringify(obj), days)
}

export function getJSONCookie(name) {
  const raw = getCookie(name)
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}
