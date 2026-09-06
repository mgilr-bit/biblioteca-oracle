import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'
import vCan from './directives/can'
import './assets/main.css'

const app = createApp(App)

app.use(createPinia())
app.directive('can', vCan)

// La sesión vive en una cookie httpOnly que JS no puede leer, así que en
// cada carga de página hay que preguntarle al backend "¿quién soy?" antes
// de resolver la primera ruta — si no, el guard de router vería
// isAuthenticated=false en el primer render aunque la cookie sea válida.
const auth = useAuthStore()
auth.initAuth().finally(() => {
  app.use(router)
  app.mount('#app')
})
