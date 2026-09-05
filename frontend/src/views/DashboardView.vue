<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { librosAPI, prestamosAPI, multasAPI } from '../api'
import { useToast } from '../composables/useToast'

const auth = useAuthStore()
const toast = useToast()
const loading = ref(true)

// --- Estado bibliotecario ---
const stats = ref(null)
const bajoStock = ref([])
const prestamosRecientes = ref([])
const multasPendientes = ref([])

// --- Estado lector ---
const misPrestamos = ref([])
const prestamosVencidos = ref([])
const prestamosPorVencer = ref([])
const totalHistorico = ref(0)
const librosDisponibles = ref([])
const misMultasPendientes = ref([])

function money(value) {
  return 'Q' + Number(value ?? 0).toFixed(2)
}

function diasRestantes(fecha) {
  const hoy = new Date()
  const fechaDev = new Date(fecha)
  return Math.ceil((fechaDev - hoy) / (1000 * 60 * 60 * 24))
}

function badgeDias(p) {
  const dias = diasRestantes(p.FECHA_DEVOLUCION_ESPERADA)
  if (p.ESTADO === 'VENCIDO' || dias < 0) return { cls: 'stamp-danger', text: 'Vencido' }
  if (dias <= 3) return { cls: 'stamp-warning', text: `${dias} días` }
  if (dias <= 7) return { cls: 'stamp-info', text: `${dias} días` }
  return { cls: 'stamp-success', text: `${dias} días` }
}

async function loadBibliotecario() {
  const [estadisticas, activos, stock, multas] = await Promise.all([
    librosAPI.getEstadisticas(),
    prestamosAPI.getActivos(),
    librosAPI.getBajoStock(),
    multasAPI.getPendientes()
  ])
  stats.value = estadisticas
  bajoStock.value = stock
  prestamosRecientes.value = activos.slice(0, 10)
  multasPendientes.value = multas
}

async function loadLector() {
  const todos = await prestamosAPI.getByUsuario(auth.user.id)
  misPrestamos.value = todos.filter((p) => p.ESTADO === 'ACTIVO' || p.ESTADO === 'VENCIDO')
  prestamosVencidos.value = misPrestamos.value.filter((p) => p.ESTADO === 'VENCIDO')
  prestamosPorVencer.value = misPrestamos.value.filter((p) => {
    const dias = diasRestantes(p.FECHA_DEVOLUCION_ESPERADA)
    return dias <= 3 && dias >= 0 && p.ESTADO !== 'VENCIDO'
  })
  totalHistorico.value = todos.length

  const misMultas = await multasAPI.getByUsuario(auth.user.id)
  misMultasPendientes.value = misMultas.filter((m) => m.ESTADO === 'PENDIENTE')

  const respLibros = await librosAPI.getAll(1, 100)
  const todosLosLibros = respLibros.libros || respLibros
  librosDisponibles.value = todosLosLibros.filter((l) => l.COPIAS_DISPONIBLES > 0)
}

onMounted(async () => {
  try {
    if (auth.isBibliotecario) {
      await loadBibliotecario()
    } else {
      await loadLector()
    }
  } catch (error) {
    toast.error('Error cargando el dashboard: ' + error.message)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="stack">
    <h2>Dashboard</h2>

    <p v-if="loading" class="text-muted">Cargando…</p>

    <template v-else-if="auth.isBibliotecario">
      <div class="stat-grid">
        <div class="stat-card">
          <div class="stat-card__label">Total libros</div>
          <div class="stat-card__value">{{ stats.total_libros }}</div>
        </div>
        <div class="stat-card is-success">
          <div class="stat-card__label">Copias disponibles</div>
          <div class="stat-card__value">{{ stats.total_disponibles }}</div>
        </div>
        <div class="stat-card is-warning">
          <div class="stat-card__label">Préstamos activos</div>
          <div class="stat-card__value">{{ prestamosRecientes.length }}</div>
        </div>
        <div class="stat-card is-danger">
          <div class="stat-card__label">Bajo stock</div>
          <div class="stat-card__value">{{ bajoStock.length }}</div>
        </div>
        <div class="stat-card is-danger">
          <div class="stat-card__label">Multas pendientes</div>
          <div class="stat-card__value">{{ multasPendientes.length }}</div>
          <div class="stat-card__hint">
            {{ money(multasPendientes.reduce((a, m) => a + Number(m.MONTO ?? 0), 0)) }} por cobrar
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card__header"><h3>Libros con bajo stock</h3></div>
        <div class="card__body table-wrap">
          <table class="data">
            <thead>
              <tr><th>Título</th><th>Autor</th><th>Disponibles</th><th>Total</th></tr>
            </thead>
            <tbody>
              <tr v-for="l in bajoStock" :key="l.ID_LIBRO">
                <td>{{ l.TITULO }}</td>
                <td>{{ l.AUTOR }}</td>
                <td><span class="stamp stamp-danger">{{ l.COPIAS_DISPONIBLES }}</span></td>
                <td>{{ l.NUMERO_COPIAS }}</td>
              </tr>
              <tr v-if="!bajoStock.length"><td colspan="4" class="cell-empty">No hay libros con bajo stock</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="card">
        <div class="card__header"><h3>Préstamos activos recientes</h3></div>
        <div class="card__body table-wrap">
          <table class="data">
            <thead>
              <tr><th>Libro</th><th>Usuario</th><th>Préstamo</th><th>Devolución</th><th>Estado</th></tr>
            </thead>
            <tbody>
              <tr v-for="p in prestamosRecientes" :key="p.ID_PRESTAMO">
                <td>{{ p.TITULO }}</td>
                <td>{{ p.NOMBRE_USUARIO }}</td>
                <td>{{ new Date(p.FECHA_PRESTAMO).toLocaleDateString() }}</td>
                <td>{{ new Date(p.FECHA_DEVOLUCION_ESPERADA).toLocaleDateString() }}</td>
                <td><span class="stamp" :class="p.ESTADO === 'VENCIDO' ? 'stamp-danger' : 'stamp-success'">{{ p.ESTADO }}</span></td>
              </tr>
              <tr v-if="!prestamosRecientes.length"><td colspan="5" class="cell-empty">No hay préstamos activos</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <template v-else>
      <div class="stat-grid">
        <div class="stat-card">
          <div class="stat-card__label">Libros prestados</div>
          <div class="stat-card__value">{{ misPrestamos.length }}</div>
          <div class="stat-card__hint">Activos ahora</div>
        </div>
        <div class="stat-card is-warning">
          <div class="stat-card__label">Por vencer</div>
          <div class="stat-card__value">{{ prestamosPorVencer.length }}</div>
          <div class="stat-card__hint">Próximos 3 días</div>
        </div>
        <div class="stat-card is-danger">
          <div class="stat-card__label">Vencidos</div>
          <div class="stat-card__value">{{ prestamosVencidos.length }}</div>
          <div class="stat-card__hint">Devolver urgente</div>
        </div>
        <div class="stat-card">
          <div class="stat-card__label">Total histórico</div>
          <div class="stat-card__value">{{ totalHistorico }}</div>
        </div>
        <div class="stat-card is-danger">
          <div class="stat-card__label">Multas pendientes</div>
          <div class="stat-card__value">{{ misMultasPendientes.length }}</div>
          <div class="stat-card__hint">
            {{ money(misMultasPendientes.reduce((a, m) => a + Number(m.MONTO ?? 0), 0)) }} a pagar
          </div>
        </div>
      </div>

      <div v-if="misMultasPendientes.length" class="notice notice-danger">
        Tienes {{ misMultasPendientes.length }} multa(s) pendiente(s) por
        {{ money(misMultasPendientes.reduce((a, m) => a + Number(m.MONTO ?? 0), 0)) }}.
        No podrás solicitar nuevos préstamos hasta regularizar tu situación con el bibliotecario.
      </div>

      <div class="card">
        <div class="card__header"><h3>Mis préstamos activos</h3></div>
        <div class="card__body">
          <div v-if="!misPrestamos.length" class="notice notice-success">
            No tienes préstamos activos. Explora el catálogo y solicita un libro al bibliotecario.
          </div>
          <template v-else>
            <div class="notice notice-info mb-4">
              Recuerda devolver tus libros a tiempo para evitar sanciones.
            </div>
            <div class="table-wrap">
              <table class="data">
                <thead>
                  <tr><th>Libro</th><th>Autor</th><th>Préstamo</th><th>Devolución</th><th>Tiempo restante</th></tr>
                </thead>
                <tbody>
                  <tr v-for="p in misPrestamos" :key="p.ID_PRESTAMO">
                    <td>{{ p.TITULO }}</td>
                    <td>{{ p.AUTOR || '-' }}</td>
                    <td>{{ new Date(p.FECHA_PRESTAMO).toLocaleDateString() }}</td>
                    <td>{{ new Date(p.FECHA_DEVOLUCION_ESPERADA).toLocaleDateString() }}</td>
                    <td><span class="stamp" :class="badgeDias(p).cls">{{ badgeDias(p).text }}</span></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>
        </div>
      </div>

      <div class="card">
        <div class="card__header"><h3>Libros disponibles</h3></div>
        <div class="card__body table-wrap">
          <table class="data">
            <thead>
              <tr><th>Título</th><th>Autor</th><th>Género</th><th>Disponibilidad</th></tr>
            </thead>
            <tbody>
              <tr v-for="l in librosDisponibles" :key="l.ID_LIBRO">
                <td>{{ l.TITULO }}</td>
                <td>{{ l.AUTOR }}</td>
                <td>{{ l.GENERO || '-' }}</td>
                <td><span class="stamp stamp-success">{{ l.COPIAS_DISPONIBLES }} disp.</span></td>
              </tr>
              <tr v-if="!librosDisponibles.length"><td colspan="4" class="cell-empty">No hay libros disponibles</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>
