<script setup>
import { ref, onMounted } from 'vue'
import { auditoriaAPI } from '../api'
import { useToast } from '../composables/useToast'

const toast = useToast()

const registros = ref([])
const page = ref(1)
const totalPages = ref(1)
const loading = ref(true)
const filtroAccion = ref('')
const filtroRecurso = ref('')
const acciones = ref([])
const recursos = ref([])

const ACCION_STAMP = {
  LOGIN: 'stamp-success',
  LOGIN_FALLIDO: 'stamp-danger',
  LOGOUT: 'stamp-neutral',
  REGISTER: 'stamp-neutral',
  PRESTAMO_CREADO: 'stamp-info',
  PRESTAMO_DEVUELTO: 'stamp-info',
  MULTA_GENERADA: 'stamp-danger',
  MULTA_PAGADA: 'stamp-success',
  MULTA_CONDONADA: 'stamp-neutral',
  RESERVA_CREADA: 'stamp-primary',
  RESERVA_CANCELADA: 'stamp-neutral',
  USUARIO_CREADO: 'stamp-primary',
  USUARIO_ACTUALIZADO: 'stamp-neutral',
  USUARIO_ELIMINADO: 'stamp-danger',
  USUARIO_ESTADO: 'stamp-neutral',
  EJEMPLAR_CREADO: 'stamp-primary',
  EJEMPLAR_ESTADO: 'stamp-neutral'
}

function fecha(value) {
  return value ? new Date(value).toLocaleString() : '-'
}

async function load(p = 1) {
  page.value = p
  loading.value = true
  try {
    const data = await auditoriaAPI.getAll(
      p,
      50,
      { accion: filtroAccion.value, recurso: filtroRecurso.value }
    )
    registros.value = data.auditoria || []
    totalPages.value = data.total_pages || 1
  } catch (error) {
    toast.error('Error cargando auditoría: ' + error.message)
  } finally {
    loading.value = false
  }
}

function filtrar() {
  load(1)
}

function limpiar() {
  filtroAccion.value = ''
  filtroRecurso.value = ''
  load(1)
}

onMounted(async () => {
  try {
    const [a, r] = await Promise.all([auditoriaAPI.getAcciones(), auditoriaAPI.getRecursos()])
    acciones.value = a || []
    recursos.value = r || []
  } catch {
    // Los filtros se cargan solos; la grilla no depende de ellos.
  }
  load(1)
})
</script>

<template>
  <div class="stack">
    <div class="page-header">
      <h2>Auditoría de eventos</h2>
    </div>

    <div class="card">
      <div class="card__body cluster">
        <select v-model="filtroAccion" class="select select-sm">
          <option value="">Todas las acciones</option>
          <option v-for="a in acciones" :key="a" :value="a">{{ a }}</option>
        </select>
        <select v-model="filtroRecurso" class="select select-sm">
          <option value="">Todos los recursos</option>
          <option v-for="r in recursos" :key="r" :value="r">{{ r }}</option>
        </select>
        <button class="btn btn-outline btn-sm" @click="filtrar">Filtrar</button>
        <button class="btn btn-outline btn-sm" @click="limpiar">Limpiar</button>
      </div>
    </div>

    <div class="card">
      <div class="card__body table-wrap">
        <table class="data">
          <thead>
            <tr>
              <th>ID</th>
              <th>Fecha</th>
              <th>Acción</th>
              <th>Recurso</th>
              <th>Usuario</th>
              <th>Detalle</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in registros" :key="r.ID_AUDITORIA">
              <td class="cell-mono">{{ r.ID_AUDITORIA }}</td>
              <td>{{ fecha(r.FECHA) }}</td>
              <td>
                <span class="stamp" :class="ACCION_STAMP[r.ACCION] || 'stamp-neutral'">
                  {{ r.ACCION }}
                </span>
              </td>
              <td>{{ r.RECURSO }}</td>
              <td>
                <template v-if="r.EMAIL">{{ r.EMAIL }}</template>
                <template v-else>-</template>
              </td>
              <td>{{ r.DETALLE || '-' }}</td>
            </tr>
            <tr v-if="!loading && !registros.length">
              <td colspan="6" class="cell-empty">No hay eventos registrados</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="totalPages > 1" class="card__body cluster">
        <button class="btn btn-outline btn-sm" :disabled="page <= 1" @click="load(page - 1)">
          Anterior
        </button>
        <span class="text-muted">Página {{ page }} de {{ totalPages }}</span>
        <button
          class="btn btn-outline btn-sm"
          :disabled="page >= totalPages"
          @click="load(page + 1)"
        >
          Siguiente
        </button>
      </div>
    </div>
  </div>
</template>