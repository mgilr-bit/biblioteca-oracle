import { reactive } from 'vue'

const state = reactive({
  visible: false,
  title: '',
  message: '',
  danger: false,
  resolve: null
})

function ask(message, { title = 'Confirmar acción', danger = false } = {}) {
  state.visible = true
  state.title = title
  state.message = message
  state.danger = danger

  return new Promise((resolve) => {
    state.resolve = resolve
  })
}

function respond(value) {
  state.visible = false
  if (state.resolve) state.resolve(value)
  state.resolve = null
}

export function useConfirm() {
  return { state, ask, respond }
}
