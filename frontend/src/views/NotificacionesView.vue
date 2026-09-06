<script setup>
import { ref, onMounted } from 'vue'
import { notificacionesAPI } from '../api'
import { useToast } from '../composables/useToast'

const toast = useToast()
const notificaciones = ref([])
const loading = ref(true)

const TIPO_LABEL = {
  RECORDATORIO_HOY: 'Recordatorio',
  RECORDATORIO_3D: 'Recordatorio',
  VENCIDO: 'Vencimiento',
  RESERVA_DISPONIBLE: 'Reserva disponible',
  MULTA: 'Multa',
  SISTEMA: 'Sistema'
}

async function load() {
  loading.value = true
  try {
    notificaciones.value = await notificacionesAPI.getAll()
  } catch (error) {
    toast.error('Error cargando notificaciones: ' + error.message)
  } finally {
    loading.value = false
  }
}

async function marcarLeida(n) {
  if (n.LEIDA) return
  try {
    await notificacionesAPI.marcarLeida(n.ID_NOTIFICACION)
    n.LEIDA = true
  } catch (error) {
    toast.error('Error: ' + error.message)
  }
}

async function marcarTodas() {
  try {
    await notificacionesAPI.marcarTodasLeidas()
    notificaciones.value.forEach((n) => (n.LEIDA = true))
    toast.success('Todas las notificaciones marcadas como leídas')
  } catch (error) {
    toast.error('Error: ' + error.message)
  }
}

onMounted(load)
</script>

<template>
  <div class="stack">
    <div class="page-header">
      <div>
        <h2>Mis notificaciones</h2>
        <p class="text-muted" style="margin:0">Recordatorios de devolución, vencimientos y avisos del sistema.</p>
      </div>
      <button
        v-if="notificaciones.some((n) => !n.LEIDA)"
        class="btn btn-outline"
        @click="marcarTodas"
      >
        Marcar todas como leídas
      </button>
    </div>

    <div class="card">
      <div class="card__body stack">
        <div
          v-for="n in notificaciones"
          :key="n.ID_NOTIFICACION"
          class="notif-item"
          :class="n.LEIDA ? 'is-read' : ''"
          @click="marcarLeida(n)"
        >
          <div class="notif-item__head">
            <span class="stamp" :class="n.LEIDA ? 'stamp-neutral' : 'stamp-info'">
              {{ TIPO_LABEL[n.TIPO] || n.TIPO }}
            </span>
            <span class="text-muted" style="font-size:0.8rem">
              {{ new Date(n.FECHA_GENERACION).toLocaleString() }}
            </span>
          </div>
          <p style="margin:0">{{ n.MENSAJE }}</p>
        </div>
        <div v-if="!loading && !notificaciones.length" class="cell-empty">No tienes notificaciones</div>
      </div>
    </div>
  </div>
</template>