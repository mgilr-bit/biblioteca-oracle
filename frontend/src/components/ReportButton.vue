<script setup>
/**
 * Botón "Reporte" con menú de formatos (PDF, Excel, CSV) para cualquier
 * sección. El contenido y los permisos los resuelve el backend en
 * /api/reportes/{seccion}; `filtros` debe reflejar lo que el usuario tiene
 * aplicado en pantalla para que el reporte coincida con la vista.
 */
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { reportesAPI } from '../api'
import { useToast } from '../composables/useToast'
import { descargarArchivo, generarPdf, marcaDeTiempo } from '../utils/reportes'

const props = defineProps({
  seccion: { type: String, required: true },
  filtros: { type: Object, default: () => ({}) },
  label: { type: String, default: 'Reporte' }
})

const toast = useToast()
const abierto = ref(false)
const generando = ref(false)
const raiz = ref(null)

const FORMATOS = [
  { id: 'pdf', label: 'PDF', hint: 'Documento con resumen, listo para imprimir' },
  { id: 'xlsx', label: 'Excel (.xlsx)', hint: 'Hoja de resumen y datos con autofiltro' },
  { id: 'csv', label: 'CSV', hint: 'Datos planos para otras herramientas' }
]

async function generar(formato) {
  abierto.value = false
  generando.value = true
  try {
    if (formato === 'pdf') {
      await generarPdf(await reportesAPI.obtener(props.seccion, props.filtros))
    } else {
      const blob = await reportesAPI.descargar(props.seccion, formato, props.filtros)
      descargarArchivo(blob, `reporte_${props.seccion}_${marcaDeTiempo()}.${formato}`)
    }
    toast.success('Reporte generado')
  } catch (error) {
    toast.error('Error al generar el reporte: ' + error.message)
  } finally {
    generando.value = false
  }
}

function cerrarAlHacerClicFuera(event) {
  if (raiz.value && !raiz.value.contains(event.target)) abierto.value = false
}

function cerrarConEscape(event) {
  if (event.key === 'Escape') abierto.value = false
}

onMounted(() => {
  document.addEventListener('click', cerrarAlHacerClicFuera)
  document.addEventListener('keydown', cerrarConEscape)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', cerrarAlHacerClicFuera)
  document.removeEventListener('keydown', cerrarConEscape)
})
</script>

<template>
  <div ref="raiz" class="menu">
    <button
      class="btn btn-outline"
      :disabled="generando"
      aria-haspopup="menu"
      :aria-expanded="abierto"
      @click="abierto = !abierto"
    >
      {{ generando ? 'Generando…' : label }}
      <span class="menu__caret" aria-hidden="true">▾</span>
    </button>
    <div v-if="abierto" class="menu__panel" role="menu">
      <button
        v-for="formato in FORMATOS"
        :key="formato.id"
        class="menu__item"
        role="menuitem"
        @click="generar(formato.id)"
      >
        <span class="menu__item-label">{{ formato.label }}</span>
        <span class="menu__item-hint">{{ formato.hint }}</span>
      </button>
    </div>
  </div>
</template>
