<script setup>
import { ref, onMounted, computed } from 'vue'
import { analiticaAPI } from '../api'
import { useToast } from '../composables/useToast'

const toast = useToast()
const loading = ref(true)
const resumen = ref(null)

const meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

function etiquetaMes(m) {
  const i = Number(m.mes) - 1
  return `${meses[i] || m.mes} ${m.anio}`
}

function money(value) {
  return 'Q' + Number(value ?? 0).toFixed(2)
}

const totalPrestamosUltimoAno = computed(() =>
  (resumen.value?.prestamos_mensual || []).reduce((acc, m) => acc + Number(m.total_prestamos || 0), 0)
)

const totalMultasGeneradas = computed(() =>
  (resumen.value?.multas_mensual || []).reduce((acc, m) => acc + Number(m.monto_generado || 0), 0)
)

const totalMultasRecaudadas = computed(() =>
  (resumen.value?.multas_mensual || []).reduce((acc, m) => acc + Number(m.monto_recaudado || 0), 0)
)

onMounted(async () => {
  try {
    resumen.value = await analiticaAPI.getResumen()
  } catch (error) {
    toast.error('Error cargando métricas: ' + error.message)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="stack">
    <div class="page-header">
      <h2>Dashboard analítico</h2>
      <span v-if="!loading" class="text-muted" style="font-size:0.8rem">
        Datos OLAP (vistas materializadas, refresco diario)
      </span>
    </div>

    <p v-if="loading" class="text-muted">Cargando…</p>

    <template v-else-if="resumen">
      <div class="stat-grid">
        <div class="stat-card">
          <div class="stat-card__label">Préstamos activos</div>
          <div class="stat-card__value">{{ resumen.totales.prestamos_activos }}</div>
        </div>
        <div class="stat-card is-success">
          <div class="stat-card__label">Copias disponibles</div>
          <div class="stat-card__value">{{ resumen.totales.copias_disponibles }}</div>
        </div>
        <div class="stat-card is-warning">
          <div class="stat-card__label">Multas pendientes</div>
          <div class="stat-card__value">{{ resumen.totales.multas_pendientes }}</div>
          <div class="stat-card__hint">{{ money(resumen.totales.deuda_pendiente) }} por cobrar</div>
        </div>
        <div class="stat-card">
          <div class="stat-card__label">Usuarios activos</div>
          <div class="stat-card__value">{{ resumen.totales.usuarios_activos }}</div>
        </div>
      </div>

      <div class="stat-grid">
        <div class="stat-card">
          <div class="stat-card__label">Préstamos últimos 12 meses</div>
          <div class="stat-card__value">{{ totalPrestamosUltimoAno }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-card__label">Multas generadas (12m)</div>
          <div class="stat-card__value">{{ money(totalMultasGeneradas) }}</div>
        </div>
        <div class="stat-card is-success">
          <div class="stat-card__label">Multas recaudadas (12m)</div>
          <div class="stat-card__value">{{ money(totalMultasRecaudadas) }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card__header"><h3>Préstamos por mes</h3></div>
        <div class="card__body table-wrap">
          <table class="data">
            <thead>
              <tr><th>Mes</th><th>Totales</th><th>Devueltos</th><th>Activos</th><th>Vencidos</th></tr>
            </thead>
            <tbody>
              <tr v-for="m in resumen.prestamos_mensual" :key="m.anio + '-' + m.mes">
                <td>{{ etiquetaMes(m) }}</td>
                <td>{{ m.total_prestamos }}</td>
                <td>{{ m.devueltos }}</td>
                <td>{{ m.activos }}</td>
                <td><span :class="m.vencidos > 0 ? 'stamp stamp-warning' : ''">{{ m.vencidos }}</span></td>
              </tr>
              <tr v-if="!resumen.prestamos_mensual.length">
                <td colspan="5" class="cell-empty">Sin préstamos en los últimos 12 meses</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="cluster" style="align-items: stretch">
        <div class="card" style="flex:1; min-width:0">
          <div class="card__header"><h3>Top libros prestados</h3></div>
          <div class="card__body table-wrap">
            <table class="data">
              <thead><tr><th>Título</th><th>Autor</th><th>Préstamos</th></tr></thead>
              <tbody>
                <tr v-for="l in resumen.top_libros" :key="l.id_libro">
                  <td>{{ l.titulo }}</td>
                  <td>{{ l.autor }}</td>
                  <td><span class="stamp stamp-info">{{ l.total_prestamos }}</span></td>
                </tr>
                <tr v-if="!resumen.top_libros.length">
                  <td colspan="3" class="cell-empty">Sin datos</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div class="card" style="flex:1; min-width:0">
          <div class="card__header"><h3>Préstamos por género</h3></div>
          <div class="card__body table-wrap">
            <table class="data">
              <thead><tr><th>Género</th><th>Préstamos</th></tr></thead>
              <tbody>
                <tr v-for="g in resumen.prestamos_por_genero" :key="g.genero">
                  <td>{{ g.genero }}</td>
                  <td><span class="stamp stamp-info">{{ g.total_prestamos }}</span></td>
                </tr>
                <tr v-if="!resumen.prestamos_por_genero.length">
                  <td colspan="2" class="cell-empty">Sin datos</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card__header"><h3>Multas por mes</h3></div>
        <div class="card__body table-wrap">
          <table class="data">
            <thead>
              <tr><th>Mes</th><th>Generado</th><th>Recaudado</th><th>Pendientes</th></tr>
            </thead>
            <tbody>
              <tr v-for="m in resumen.multas_mensual" :key="m.anio + '-' + m.mes">
                <td>{{ etiquetaMes(m) }}</td>
                <td>{{ money(m.monto_generado) }}</td>
                <td>{{ money(m.monto_recaudado) }}</td>
                <td>{{ m.pendientes }}</td>
              </tr>
              <tr v-if="!resumen.multas_mensual.length">
                <td colspan="4" class="cell-empty">Sin multas en los últimos 12 meses</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>