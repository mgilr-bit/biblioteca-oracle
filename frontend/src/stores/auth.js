import { defineStore } from 'pinia'
import { authAPI } from '../api'
import { buildAbilityFor } from '../casl/ability'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    // La sesión real vive en la cookie httpOnly `sid` (el backend la
    // resuelve, JS no puede leerla). Este estado es solo para la UI y se
    // pierde en cada recarga de página — por eso `initAuth()` la rehidrata
    // llamando a GET /api/auth/me antes de montar el router (ver main.js).
    user: null,
    initialized: false
  }),

  getters: {
    isAuthenticated: (state) => !!state.user,
    nombre: (state) => state.user?.nombre ?? '',
    // Getters normales (no arrow) para poder encadenar `this.ability` —
    // Pinia no expone otros getters a través del `state` que reciben las
    // funciones flecha.
    ability(state) {
      return buildAbilityFor(state.user)
    },
    isBibliotecario() {
      return this.ability.can('manage', 'all')
    }
  },

  actions: {
    setSession(userData) {
      this.user = userData
    },

    async initAuth() {
      try {
        this.user = await authAPI.me()
      } catch {
        this.user = null
      } finally {
        this.initialized = true
      }
    },

    async logout() {
      try {
        await authAPI.logout()
      } catch {
        // Si la sesión ya estaba vencida/revocada del lado del servidor,
        // igual queremos limpiar el estado local.
      }
      this.user = null
    }
  }
})
