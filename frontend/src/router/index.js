import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { public: true }
  },
  {
    path: '/',
    name: 'dashboard',
    component: () => import('../views/DashboardView.vue')
  },
  {
    path: '/libros',
    name: 'libros',
    component: () => import('../views/LibrosView.vue')
  },
  {
    path: '/prestamos',
    name: 'prestamos',
    component: () => import('../views/PrestamosView.vue')
  },
  {
    path: '/usuarios',
    name: 'usuarios',
    component: () => import('../views/UsuariosView.vue'),
    meta: { requiresBibliotecario: true }
  },
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// CORRECCIÓN vs. versión original: la autenticación se verificaba de forma
// manual y repetida (`auth.requireAuth()`) copiada y pegada al inicio del
// script de cada página HTML. Aquí es un único guard centralizado.
router.beforeEach((to) => {
  const auth = useAuthStore()

  if (!to.meta.public && !auth.isAuthenticated) {
    return { name: 'login' }
  }

  if (to.meta.public && auth.isAuthenticated) {
    return { name: 'dashboard' }
  }

  // CORRECCIÓN: antes, el control de acceso a "Usuarios" era solo visual
  // (el link se ocultaba con display:none pero la página seguía siendo
  // accesible por URL directa, mostrando solo un alert() tardío). Ahora la
  // ruta ni siquiera se resuelve si el rol no es BIBLIOTECARIO.
  if (to.meta.requiresBibliotecario && !auth.isBibliotecario) {
    return { name: 'dashboard' }
  }

  return true
})

export default router
