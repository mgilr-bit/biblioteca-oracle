import { defineStore } from 'pinia'
import { getJSONCookie, setJSONCookie, removeCookie } from '../utils/cookies'

const COOKIE_NAME = 'biblioteca_session'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    // Se inicializa leyendo la cookie una sola vez (equivalente a lo que
    // antes hacía JSON.parse(localStorage.getItem('user')))
    user: getJSONCookie(COOKIE_NAME)
  }),

  getters: {
    isAuthenticated: (state) => !!state.user?.token,
    token: (state) => state.user?.token ?? null,
    isBibliotecario: (state) => state.user?.rol === 'BIBLIOTECARIO',
    nombre: (state) => state.user?.nombre ?? ''
  },

  actions: {
    setSession(userData) {
      this.user = userData
      setJSONCookie(COOKIE_NAME, userData)
    },
    logout() {
      this.user = null
      removeCookie(COOKIE_NAME)
    }
  }
})
