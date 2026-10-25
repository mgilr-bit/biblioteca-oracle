<script setup>
import { ref, computed, onMounted } from 'vue'
import { reservasAPI, librosAPI, usuariosAPI } from '../api'
import { useAuthStore } from '../stores/auth'
import { useToast } from '../composables/useToast'
import { useConfirm } from '../composables/useConfirm'
import { useCan } from '../composables/useCan'
import AppModal from '../components/AppModal.vue'
import ReportButton from '../components/ReportButton.vue'

const auth = useAuthStore()
const can = useCan()
const toast = useToast()
const { ask } = useConfirm()

const esBibliotecario = computed(() => auth.user?.rol === 'BIBLIOTECARIO' || auth.user?.rol === 'ADMIN')

const reservas = ref([])
const libros = ref([])
// Dañados, en reparación o de baja no se reservan (el backend lo valida igual).
const librosReservables = computed(() => libros.value.filter((l) => l.ESTADO === 'DISPONIBLE'))
const usuarios = ref([])
const loading = ref(true)
const filtroEstado = ref('')
const showModal = ref(false)
const saving = ref(false)
const form = ref({ id_libro: '', id_usuario: '', librosLimitados: false })
const colaLibro = ref('')
const cola = ref([])

// ACTIVA: pendiente de recoger (con fecha = copia apartada por 3 días; sin
// fecha = en cola esperando copia). SIN_RECOGER la marca el sistema al vencer.
const ESTADOS = {
  ACTIVA: { label: 'Activa', stamp: 'stamp-info' },
  RECOGIDA: { label: 'Recogida', stamp: 'stamp-success' },
  SIN_RECOGER: { label: 'Sin recoger', stamp: 'stamp-danger' },
  CANCELADA: { label: 'Cancelada', stamp: 'stamp-neutral' }
}

const filtro = computed(() =>
  filtroEstado.value ? reservas.value.filter((r) => r.ESTADO === filtroEstado.value) : reservas.value
)

async function loadLibros() {
  try {
    const response = await librosAPI.getAll(1, 1000)
    libros.value = response.libros || response
  } catch (error) {
    console.error('Error cargando libros:', error)
  }
}

async function loadUsuarios() {
  if (!esBibliotecario.value) return
  try {
    usuarios.value = await usuariosAPI.getAll()
  } catch (error) {
    console.error('Error cargando usuarios:', error)
  }
}

async function loadReservas() {
  loading.value = true
  try {
    reservas.value = esBibliotecario.value
      ? await reservasAPI.getAll()
      : await reservasAPI.getByUsuario(auth.user.id)
  } catch (error) {
    toast.error('Error cargando reservas: ' + error.message)
  } finally {
    loading.value = false
  }
}

async function loadCola() {
  cola.value = []
  if (!cola.value || !colaLibro.value) return
  try {
    cola.value = await reservasAPI.getCola(colaLibro.value)
  } catch (error) {
    cola.value = []
    console.error('Error cargando cola:', error)
  }
}

function openCreate() {
  form.value = { id_libro: '', id_usuario: '' }
  showModal.value = true
}

async function saveReserva() {
  if (!form.value.id_libro) {
    toast.error('Seleccione el libro')
    return
  }
  // BIBLIOTECARIO/ADMIN reservan a nombre de otro: el backend exige el usuario.
  if (esBibliotecario.value && !form.value.id_usuario) {
    toast.error('Seleccione el usuario')
    return
  }
  const payload = {
    id_libro: parseInt(form.value.id_libro),
    id_usuario: esBibliotecario.value ? parseInt(form.value.id_usuario) : null
  }

  saving.value = true
  try {
    const response = await reservasAPI.create(payload)
    toast.success(response.message || 'Reserva creada')
    showModal.value = false
    loadReservas()
    loadCola()
  } catch (error) {
    toast.error('Error: ' + error.message)
  } finally {
    saving.value = false
  }
}

async function cancelarReserva(reserva) {
  const ok = await ask(`¿Cancelar la reserva de "${reserva.TITULO}" de ${reserva.NOMBRE_USUARIO}?`, {
    title: 'Cancelar reserva',
    danger: true
  })
  if (!ok) return
  try {
    const response = await reservasAPI.cancelar(reserva.ID_RESERVA)
    toast.success(response.message || 'Reserva cancelada')
    loadReservas()
    loadCola()
  } catch (error) {
    toast.error('Error: ' + error.message)
  }
}

async function recogerReserva(reserva) {
  const ok = await ask(
    `¿${reserva.NOMBRE_USUARIO} recogió "${reserva.TITULO}"? Se registrará el préstamo a su nombre.`,
    { title: 'Marcar como recogida' }
  )
  if (!ok) return
  try {
    const response = await reservasAPI.recoger(reserva.ID_RESERVA)
    toast.success(response.message || 'Reserva recogida')
    loadReservas()
    loadCola()
  } catch (error) {
    toast.error('Error: ' + error.message)
  }
}

// Las acciones (recoger/cancelar) son solo de BIBLIOTECARIO/ADMIN.
const verAcciones = computed(() => can('cancel', 'Reserva'))
const columnas = computed(() => 5 + (esBibliotecario.value ? 1 : 0) + (verAcciones.value ? 1 : 0))

onMounted(() => {
  loadLibros()
  loadUsuarios()
  loadReservas()
})
</script>

<template>
  <div class="stack">
    <div class="page-header">
      <div>
        <h2>Gestión de reservas</h2>
        <p class="text-muted" style="margin:0">Cada reserva aparta una copia por 3 días; si no hay copias libres espera en cola (FIFO).</p>
      </div>
      <div class="cluster">
        <ReportButton seccion="reservas" :filtros="{ estado: filtroEstado }" />
        <button v-can:create="'Reserva'" class="btn btn-primary" @click="openCreate">+ Nueva reserva</button>
      </div>
    </div>

    <div class="card" v-if="can('read', 'Reserva') && !can('manage', 'all')">
      <div class="card__body">
        <p class="text-muted" style="margin:0 0 var(--space-2)">
          Tus reservas se muestran a continuación.
        </p>
      </div>
    </div>

    <div class="card" v-if="can('read', 'Reserva')">
      <div class="card__body search-bar" style="border:none; padding:var(--space-3)">
        <select v-model="filtroEstado" class="select">
          <option value="">Todos los estados</option>
          <option v-for="(info, valor) in ESTADOS" :key="valor" :value="valor">{{ info.label }}</option>
        </select>
      </div>
      <div class="card__body table-wrap" style="padding-top:0">
        <table class="data">
          <thead>
            <tr>
              <th>ID</th><th>Libro</th><th v-if="esBibliotecario">Usuario</th>
              <th>Fecha</th><th>Expira</th><th>Estado</th><th v-if="verAcciones">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in filtro" :key="r.ID_RESERVA">
              <td class="cell-mono">{{ r.ID_RESERVA }}</td>
              <td>{{ r.TITULO }}</td>
              <td v-if="esBibliotecario">{{ r.NOMBRE_USUARIO }}</td>
              <td>{{ new Date(r.FECHA_RESERVA).toLocaleString() }}</td>
              <td>
                <template v-if="r.FECHA_EXPIRACION">{{ new Date(r.FECHA_EXPIRACION).toLocaleString() }}</template>
                <span v-else-if="r.ESTADO === 'ACTIVA'" class="text-muted">En cola (sin copia libre)</span>
                <template v-else>-</template>
              </td>
              <td>
                <span class="stamp" :class="ESTADOS[r.ESTADO]?.stamp || 'stamp-neutral'">
                  {{ ESTADOS[r.ESTADO]?.label || r.ESTADO }}
                </span>
              </td>
              <td v-if="verAcciones">
                <div v-if="r.ESTADO === 'ACTIVA'" class="cluster">
                  <button
                    class="btn btn-primary btn-sm"
                    :disabled="!r.FECHA_EXPIRACION"
                    :title="r.FECHA_EXPIRACION ? 'Entregar el libro y registrar el préstamo' : 'Aún no hay copia apartada para esta reserva'"
                    @click="recogerReserva(r)"
                  >
                    Recogido
                  </button>
                  <button class="btn btn-outline btn-sm" @click="cancelarReserva(r)">Cancelar</button>
                </div>
              </td>
            </tr>
            <tr v-if="!loading && !filtro.length">
              <td :colspan="columnas" class="cell-empty">No hay reservas</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="card" v-if="esBibliotecario">
      <div class="card__body stack">
        <h3 style="margin:0">Cola FIFO por libro</h3>
        <div class="search-bar">
          <select v-model="colaLibro" class="select" @change="loadCola">
            <option value="">Seleccione un libro…</option>
            <option v-for="l in libros" :key="l.ID_LIBRO" :value="l.ID_LIBRO">{{ l.TITULO }}</option>
          </select>
        </div>
        <table v-if="cola.length" class="data">
          <thead>
            <tr><th>Posición</th><th>Usuario</th><th>Solicitado</th><th>Recoger hasta</th></tr>
          </thead>
          <tbody>
            <tr v-for="(item, idx) in cola" :key="item.id_reserva">
              <td class="cell-mono">#{{ idx + 1 }}</td>
              <td>{{ item.nombre_usuario || `Usuario #${item.id_usuario}` }}</td>
              <td>{{ new Date(item.fecha_reserva).toLocaleString() }}</td>
              <td>
                <template v-if="item.fecha_expiracion">{{ new Date(item.fecha_expiracion).toLocaleString() }}</template>
                <span v-else class="text-muted">En espera de copia</span>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-else class="text-muted" style="margin:0">No hay reservas en cola para el libro seleccionado.</p>
      </div>
    </div>

    <AppModal v-if="showModal" title="Nueva reserva" @close="showModal = false">
      <form class="stack" @submit.prevent="saveReserva">
        <div class="field">
          <label for="libroRes">Libro *</label>
          <select id="libroRes" v-model="form.id_libro" class="select">
            <option value="">Seleccione un libro…</option>
            <option v-for="l in librosReservables" :key="l.ID_LIBRO" :value="l.ID_LIBRO">
              {{ l.TITULO }} ({{ l.COPIAS_DISPONIBLES }} disp.)
            </option>
          </select>
        </div>
        <div class="field" v-if="esBibliotecario">
          <label for="usuarioRes">Usuario *</label>
          <select id="usuarioRes" v-model="form.id_usuario" class="select">
            <option value="">Seleccione un usuario…</option>
            <option v-for="u in usuarios" :key="u.ID_USUARIO" :value="u.ID_USUARIO">{{ u.NOMBRE }}</option>
          </select>
        </div>
      </form>
      <template #footer>
        <button class="btn btn-outline" @click="showModal = false">Cancelar</button>
        <button class="btn btn-primary" :disabled="saving" @click="saveReserva">
          {{ saving ? 'Guardando…' : 'Reservar' }}
        </button>
      </template>
    </AppModal>
  </div>
</template>