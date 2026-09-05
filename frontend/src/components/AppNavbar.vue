<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

async function logout() {
  await auth.logout()
  router.push('/login')
}
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
        <router-link to="/prestamos" class="app-nav__link" active-class="is-active">
          Préstamos
        </router-link>
        <router-link v-can:manage="'all'" to="/usuarios" class="app-nav__link" active-class="is-active">
          Usuarios
        </router-link>
      </nav>

      <div class="app-nav__user">
        <span>{{ auth.nombre }}</span>
        <button class="btn btn-ghost btn-sm" @click="logout">Salir</button>
      </div>
    </div>
  </header>
</template>
