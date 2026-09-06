<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { multasAPI } from '../api'
import { useToast } from '../composables/useToast'
import { useConfirm } from '../composables/useConfirm'

const auth = useAuthStore()
const toast = useToast()
const { ask } = useConfirm()

const multas = ref([])
const activeTab = ref('pendientes')
const loading = ref(true)

const ESTADO_STAMP = {
  PENDIENTE: 'stamp-danger',
  PAGADA: 'stamp-success',
  CONDONADA: 'stamp-neutral'
}

function money(value) {
  return 'Q' + Number(value ?? 0).toFixed(2)
}

function fecha(value) {
  return value ? new Date(value).toLocaleDateString() : '-'
}

const totalPendiente = computed(() =>
  multas.value
    .filter((m) => m.ESTADO === 'PENDIENTE')
    .reduce((acc, m) => acc + Number(m.MONTO ?? 0), 0)
)

async function load(tab = activeTab.value) {
  activeTab.value = tab
  loading.value = true
  try {
    if (!auth.isBibliotecario) {
      multas.value = await multasAPI.getByUsuario(auth.user.id)
    } else if (tab === 'pendientes') {
      multas.value = await multasAPI.getPendientes()
    } else {
      multas.value = await multasAPI.getAll()
    }
  } catch (error) {
    toast.error('Error cargando multas: ' + error.message)
  } finally {
    loading.value = false
  }
}

async function pagar(multa) {
  const ok = await ask(
    `¿Registrar el pago de ${money(multa.MONTO)} de ${multa.NOMBRE_USUARIO}?`,
    { title: 'Cobrar multa' }
  )
  if (!ok) return
  try {
    const res = await multasAPI.pagar(multa.ID_MULTA)
    toast.success(res.message || 'Multa pagada')
    load()
  } catch (error) {
    toast.error('Error: ' + error.message)
  }
}

async function condonar(multa) {
  const ok = await ask(
    `¿Condonar la multa de ${money(multa.MONTO)} de ${multa.NOMBRE_USUARIO}?`,
    { title: 'Condonar multa' }
  )
  if (!ok) return
  try {
    const res = await multasAPI.condonar(multa.ID_MULTA)
    toast.success(res.message || 'Multa condonada')
    load()
  } catch (error) {
    toast.error('Error: ' + error.message)
  }
}

onMounted(() => load())
</script>

<template>
  <div class="stack">
    <div class="page-header">
      <h2>{{ auth.isBibliotecario ? 'Gestión de multas' : 'Mis multas' }}</h2>
      <span v-if="totalPendiente > 0" class="stamp stamp-danger">
        Pendiente: {{ money(totalPendiente) }}
      </span>
    </div>

    <div v-if="!auth.isBibliotecario" class="notice notice-info">
      Las multas por devolución tardía son de Q35.00. Mientras tengas una multa pendiente
      no podrás solicitar nuevos préstamos.
    </div>

    <div v-if="auth.isBibliotecario" class="cluster" role="tablist">
      <button
        v-for="t in [['pendientes', 'Pendientes'], ['todas', 'Todas']]"
        :key="t[0]"
        class="app-nav__link"
        :class="{ 'is-active': activeTab === t[0] }"
        @click="load(t[0])"
      >
        {{ t[1] }}
      </button>
    </div>

    <div class="card">
      <div class="card__body table-wrap">
        <table class="data">
          <thead>
            <tr>
              <th>ID</th>
              <th>Libro</th>
              <th v-if="auth.isBibliotecario">Usuario</th>
              <th>Motivo</th>
              <th>Generada</th>
              <th>Monto</th>
              <th>Estado</th>
              <th v-if="auth.isBibliotecario">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="m in multas" :key="m.ID_MULTA">
              <td class="cell-mono">{{ m.ID_MULTA }}</td>
              <td>{{ m.TITULO }}</td>
              <td v-if="auth.isBibliotecario">{{ m.NOMBRE_USUARIO }}</td>
              <td>{{ m.MOTIVO || '-' }}</td>
              <td>{{ fecha(m.FECHA_GENERACION) }}</td>
              <td class="cell-mono">{{ money(m.MONTO) }}</td>
              <td><span class="stamp" :class="ESTADO_STAMP[m.ESTADO]">{{ m.ESTADO }}</span></td>
              <td v-if="auth.isBibliotecario">
                <div v-if="m.ESTADO === 'PENDIENTE'" class="cluster">
                  <button class="btn btn-success btn-sm" @click="pagar(m)">Cobrar</button>
                  <button class="btn btn-outline btn-sm" @click="condonar(m)">Condonar</button>
                </div>
                <span v-else class="text-muted" style="font-size:0.8rem">
                  {{ m.ESTADO === 'PAGADA' ? `Pagada ${fecha(m.FECHA_PAGO)}` : 'Condonada' }}
                </span>
              </td>
            </tr>
            <tr v-if="!loading && !multas.length">
              <td :colspan="auth.isBibliotecario ? 8 : 6" class="cell-empty">
                No hay multas
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
