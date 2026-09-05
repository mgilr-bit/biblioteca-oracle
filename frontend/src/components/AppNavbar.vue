<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { notificacionesAPI } from '../api'

const auth = useAuthStore()
const router = useRouter()

const noLeidas = ref(0)
const panelOpen = ref(false)
const notis = ref([])

async function refreshCount() {
  if (!auth.isAuthenticated) return
  try {
    const data = await notificacionesAPI.getNoLeidas()
    noLeidas.value = data?.no_leidas ?? 0
  } catch (error) {
    noLeidas.value = 0
  }
}

async function togglePanel() {
  panelOpen.value = !panelOpen.value
  if (panelOpen.value) {
    try {
      notis.value = await notificacionesAPI.getAll()
    } catch (error) {
      notis.value = []
    }
  }
}

async function marcarLeida(n) {
  if (n.LEIDA) return
  try {
    await notificacionesAPI.marcarLeida(n.ID_NOTIFICACION)
    n.LEIDA = true
    noLeidas.value = Math.max(0, noLeidas.value - 1)
  } catch (error) {
    console.error(error)
  }
}

function irTodas() {
  panelOpen.value = false
  router.push('/notificaciones')
}

function cerrarPanel(event) {
  if (!event.target.closest('.bell')) {
    panelOpen.value = false
  }
}

async function logout() {
  await auth.logout()
  router.push('/login')
}

onMounted(() => {
  refreshCount()
  document.addEventListener('click', cerrarPanel)
  // Refresca el contador al volver de background (ej. devolución de otra pestaña).
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') refreshCount()
  })
})

onBeforeUnmount(() => {
  document.removeEventListener('click', cerrarPanel)
})
</script>

<template>
  <header class="app-nav">
    <div class="container app-nav__inner">
      <router-link to="/" class="app-nav__brand">
        <span class="app-nav__brand-mark" />
        Biblioteca
      </router-link>

      <nav class="app-nav__links">
        <router-link to="/" class="app-nav__link" active-class="is-active" exact-active-class="is-active">
          Dashboard
        </router-link>
        <router-link to="/libros" class="app-nav__link" active-class="is-active">
          Libros
        </router-link>
        <router-link v-can:read="'Editorial'" to="/editoriales" class="app-nav__link" active-class="is-active">
          Editoriales
        </router-link>
        <router-link v-can:read="'Ejemplar'" to="/ejemplares" class="app-nav__link" active-class="is-active">
          Ejemplares
        </router-link>
        <router-link v-can:read="'Reserva'" to="/reservas" class="app-nav__link" active-class="is-active">
          Reservas
        </router-link>
        <router-link to="/prestamos" class="app-nav__link" active-class="is-active">
          Préstamos
        </router-link>
        <router-link v-can:manage="'all'" to="/usuarios" class="app-nav__link" active-class="is-active">
          Usuarios
        </router-link>
      </nav>

      <div class="app-nav__user">
        <div class="bell" @click.stop="togglePanel">
          <button class="btn btn-ghost btn-sm bell__btn" title="Notificaciones">
            🔔
            <span v-if="noLeidas > 0" class="bell__badge">{{ noLeidas > 99 ? '99+' : noLeidas }}</span>
          </button>
          <div v-if="panelOpen" class="bell__panel">
            <div class="bell__panel-title">
              <strong>Notificaciones</strong>
              <button class="btn btn-ghost btn-sm" @click="irTodas">Ver todas</button>
            </div>
            <div v-if="notis.length" class="bell__list">
              <button
                v-for="n in notis.slice(0, 8)"
                :key="n.ID_NOTIFICACION"
                class="bell__item"
                :class="n.LEIDA ? 'is-read' : ''"
                @click="marcarLeida(n)"
              >
                <span class="bell__item-msg">{{ n.MENSAJE }}</span>
                <span class="bell__item-date">{{ new Date(n.FECHA_GENERACION).toLocaleString() }}</span>
              </button>
            </div>
            <p v-else class="bell__empty">Sin notificaciones</p>
          </div>
        </div>
        <span>{{ auth.nombre }}</span>
        <button class="btn btn-ghost btn-sm" @click="logout">Salir</button>
      </div>
    </div>
  </header>
</template>