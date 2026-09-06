<script setup>
import { ref, onMounted } from 'vue'
import { ejemplaresAPI, librosAPI } from '../api'
import { useToast } from '../composables/useToast'
import { useConfirm } from '../composables/useConfirm'
import { useCan } from '../composables/useCan'

const can = useCan()
const toast = useToast()
const { ask } = useConfirm()

const ejemplares = ref([])
const estados = ref([])
const libros = ref([])
const loading = ref(true)
const filters = ref({ id_libro: '', estado: '' })
const emptyMessage = ref('No hay ejemplares')

const ESTADO_CLASS = {
  DISPONIBLE: 'stamp-success',
  PRESTADO: 'stamp-info',
  RESERVADO: 'stamp-warning',
  DANADO: 'stamp-danger',
  REPARACION: 'stamp-warning',
  BAJA: 'stamp-neutral',
  DEVUELTO: 'stamp-neutral'
}

async function loadEstados() {
  try {
    estados.value = await ejemplaresAPI.getEstados()
  } catch (error) {
    console.error('Error cargando estados:', error)
  }
}

async function loadLibros() {
  try {
    const response = await librosAPI.getAll(1, 1000)
    libros.value = response.libros || response
  } catch (error) {
    console.error('Error cargando libros:', error)
  }
}

async function loadEjemplares() {
  loading.value = true
  try {
    const response = await ejemplaresAPI.getAll(1, 1000, filters.value)
    ejemplares.value = response.ejemplares || response
    emptyMessage.value = 'No hay ejemplares'
  } catch (error) {
    toast.error('Error cargando ejemplares: ' + error.message)
  } finally {
    loading.value = false
  }
}

function limpiarFiltros() {
  filters.value = { id_libro: '', estado: '' }
  loadEjemplares()
}

async function cambiarEstado(ejemplar, estado) {
  try {
    const response = await ejemplaresAPI.changeEstado(ejemplar.ID_EJEMPLAR, estado)
    toast.success(response.message || 'Estado actualizado')
    loadEjemplares()
  } catch (error) {
    toast.error('Error: ' + error.message)
  }
}

async function deleteEjemplar(ejemplar) {
  const ok = await ask(`¿Eliminar el ejemplar "${ejemplar.CODIGO_EJEMPLAR}"?`, {
    title: 'Eliminar ejemplar',
    danger: true
  })
  if (!ok) return

  try {
    const response = await ejemplaresAPI.delete(ejemplar.ID_EJEMPLAR)
    toast.success(response.message || 'Ejemplar eliminado')
    loadEjemplares()
  } catch (error) {
    toast.error('Error: ' + error.message)
  }
}

onMounted(() => {
  loadEstados()
  loadLibros()
  loadEjemplares()
})
</script>

<template>
  <div class="stack">
    <div class="page-header">
      <div>
        <h2>Gestión de ejemplares</h2>
        <p class="text-muted" style="margin:0">Copias físicas de cada libro y su estado.</p>
      </div>
    </div>

    <div class="card">
      <div class="card__body">
        <div class="search-bar">
          <select v-model="filters.id_libro" class="select" @change="loadEjemplares">
            <option value="">Todos los libros</option>
            <option v-for="l in libros" :key="l.ID_LIBRO" :value="l.ID_LIBRO">{{ l.TITULO }}</option>
          </select>
          <select v-model="filters.estado" class="select" @change="loadEjemplares">
            <option value="">Todos los estados</option>
            <option v-for="e in estados" :key="e" :value="e">{{ e }}</option>
          </select>
          <button class="btn btn-outline btn-sm" @click="limpiarFiltros">Limpiar</button>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card__body table-wrap">
        <table class="data">
          <thead>
            <tr>
              <th>Código</th><th>Libro</th><th>Estado</th><th>Ubicación</th><th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="ejemplar in ejemplares" :key="ejemplar.ID_EJEMPLAR">
              <td class="cell-mono">{{ ejemplar.CODIGO_EJEMPLAR }}</td>
              <td>{{ ejemplar.TITULO }} <span class="cell-mono text-muted">#{{ ejemplar.ID_LIBRO }}</span></td>
              <td>
                <span class="stamp" :class="ESTADO_CLASS[ejemplar.ESTADO] || 'stamp-neutral'">{{ ejemplar.ESTADO }}</span>
              </td>
              <td>{{ ejemplar.UBICACION || '-' }}</td>
              <td>
                <div class="cluster" v-if="can('update', 'Ejemplar')">
                  <select
                    class="select select-sm"
                    :value="ejemplar.ESTADO"
                    title="Cambiar estado"
                    @change="cambiarEstado(ejemplar, $event.target.value)"
                  >
                    <option v-for="e in estados" :key="e" :value="e" :selected="e === ejemplar.ESTADO">{{ e }}</option>
                  </select>
                  <button v-can:delete="'Ejemplar'" class="btn btn-danger btn-sm btn-icon" title="Eliminar" @click="deleteEjemplar(ejemplar)">🗑</button>
                </div>
                <span v-else class="text-muted" style="font-size:0.8rem">Solo lectura</span>
              </td>
            </tr>
            <tr v-if="!loading && !ejemplares.length">
              <td colspan="5" class="cell-empty">{{ emptyMessage }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>