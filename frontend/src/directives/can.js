/**
 * Directiva `v-can` — gating de UI basado en CASL (same philosophy as the
 * ability: UX only, el backend siempre revalida).
 *
 * Uso:
 *   <button v-can:create="'Prestamo'">Crear préstamo</button>
 *   <button v-can="['update', 'Libro']">Editar</button>
 *   <button v-can:manage="'all'">Admin only</button>
 *   <input v-can.disabled:update="'Libro'" />   // deshabilitar en vez de ocultar
 *
 * Argumento = acción ('manage' | 'create' | 'read' | 'update' | 'delete' | 'devolver' ...).
 * Valor     = subject ('Libro' | 'Prestamo' | 'Usuario' | 'all' | ...) o [acción, subject, field?].
 * Modificador `.disabled` deshabilita el elemento en vez de ocultarlo.
 *
 * Es reactivo: se re-evalúa cuando cambia la sesión (login/logout) porque
 * `auth.ability` depende del getter `auth.user` de Pinia.
 */
import { watchEffect } from 'vue'
import { useAuthStore } from '../stores/auth'

function resolveParams(binding) {
  let action = null
  let subject = null
  let field = null

  if (binding.arg) {
    action = binding.arg
    subject = binding.value
  } else if (Array.isArray(binding.value)) {
    ;[action, subject, field] = binding.value
  } else if (binding.value && typeof binding.value === 'object') {
    action = binding.value.action
    subject = binding.value.subject
    field = binding.value.field
  } else if (binding.value === undefined || binding.value === null) {
    // v-can sin argumento ni valor: perímite visualizarlo a cualquier rol autenticado
    action = 'read'
    subject = 'Libro'
  } else {
    action = 'read'
    subject = binding.value
  }

  return { action, subject, field }
}

function isAllowed(binding, ability) {
  const { action, subject, field } = resolveParams(binding)
  try {
    return ability.can(action, subject, field)
  } catch {
    return false
  }
}

function apply(el, binding, allowed) {
  if (binding.modifiers.disabled) {
    el.disabled = !allowed
    el.style.pointerEvents = allowed ? '' : 'none'
    el.style.opacity = allowed ? '' : '0.5'
    if (el.localName === 'button' || el.localName === 'input' || el.localName === 'select') {
      el.classList.toggle('is-disabled', !allowed)
    }
  } else {
    el.style.display = allowed ? '' : 'none'
  }
}

function start(el, binding) {
  if (el.__vCanStop__) {
    el.__vCanStop__()
  }
  const auth = useAuthStore()
  el.__vCanStop__ = watchEffect(() => {
    apply(el, binding, isAllowed(binding, auth.ability))
  })
}

export const vCan = {
  mounted: start,
  updated: start,
  unmounted(el) {
    if (el.__vCanStop__) {
      el.__vCanStop__()
      el.__vCanStop__ = null
    }
  }
}

export default vCan