import { reactive } from 'vue'

// CORRECCIÓN vs. versión original: toda la app usaba alert() del navegador
// para éxitos y errores, lo cual bloquea el hilo principal y se ve
// completamente fuera de lugar en cualquier interfaz moderna. Se sustituye
// por un sistema de toasts no bloqueante.

const state = reactive({ items: [] })
let nextId = 1

function push(message, type = 'info', timeout = 4000) {
  const id = nextId++
  state.items.push({ id, message, type })
  if (timeout) {
    setTimeout(() => dismiss(id), timeout)
  }
  return id
}

function dismiss(id) {
  const idx = state.items.findIndex((t) => t.id === id)
  if (idx !== -1) state.items.splice(idx, 1)
}

export function useToast() {
  return {
    toasts: state.items,
    success: (msg) => push(msg, 'success'),
    error: (msg) => push(msg, 'error', 6000),
    info: (msg) => push(msg, 'info'),
    dismiss
  }
}
