<script setup>
import { ref, computed, onMounted } from 'vue'
import { editorialesAPI } from '../api'
import { useToast } from '../composables/useToast'
import { useConfirm } from '../composables/useConfirm'
import AppModal from '../components/AppModal.vue'

const toast = useToast()
const { ask } = useConfirm()

const todas = ref([])
const loading = ref(true)
const filtro = ref('')

const filtradas = computed(() => {
  const q = filtro.value.trim().toLowerCase()
  return q ? todas.value.filter((e) => e.NOMBRE.toLowerCase().includes(q)) : todas.value
})

async function loadEditoriales() {
  loading.value = true
  try {
    todas.value = await editorialesAPI.getAll()
  } catch (error) {
    toast.error('Error cargando editoriales: ' + error.message)
  } finally {
    loading.value = false
  }
}

// --- Modal CRUD ---
const showModal = ref(false)
const editingId = ref(null)
const nombre = ref('')
const saving = ref(false)

function openCreate() {
  editingId.value = null
  nombre.value = ''
  showModal.value = true
}

function openEdit(editorial) {
  editingId.value = editorial.ID_EDITORIAL
  nombre.value = editorial.NOMBRE
  showModal.value = true
}

async function saveEditorial() {
  if (!nombre.value.trim()) {
    toast.error('El nombre es requerido')
    return
  }

  saving.value = true
  try {
    const payload = { nombre: nombre.value.trim() }
    const response = editingId.value
      ? await editorialesAPI.update(editingId.value, payload)
      : await editorialesAPI.create(payload)
    toast.success(response.message || 'Guardado correctamente')
    showModal.value = false
    loadEditoriales()
  } catch (error) {
    toast.error('Error: ' + error.message)
  } finally {
    saving.value = false
  }
}

async function deleteEditorial(editorial) {
  const ok = await ask(`¿Eliminar la editorial "${editorial.NOMBRE}"?`, {
    title: 'Eliminar editorial',
    danger: true
  })
  if (!ok) return

  try {
    const response = await editorialesAPI.delete(editorial.ID_EDITORIAL)
    toast.success(response.message || 'Editorial eliminada')
    loadEditoriales()
  } catch (error) {
    toast.error('Error: ' + error.message)
  }
}

onMounted(loadEditoriales)
</script>

<template>
  <div class="stack">
    <div class="page-header">
      <h2>Editoriales</h2>
      <button class="btn btn-primary" @click="openCreate">+ Nueva editorial</button>
    </div>

    <div class="card">
      <div class="card__body stack">
        <input v-model="filtro" class="input" placeholder="Buscar editorial…" />
        <span class="text-muted" style="font-size:0.85rem">{{ filtradas.length }} editorial(es)</span>
      </div>
    </div>

    <div class="card">
      <div class="card__body table-wrap">
        <table class="data">
          <thead>
            <tr><th>ID</th><th>Nombre</th><th>Acciones</th></tr>
          </thead>
          <tbody>
            <tr v-for="e in filtradas" :key="e.ID_EDITORIAL">
              <td class="cell-mono">{{ e.ID_EDITORIAL }}</td>
              <td>{{ e.NOMBRE }}</td>
              <td>
                <div class="cluster">
                  <button class="btn btn-outline btn-sm btn-icon" title="Editar" @click="openEdit(e)">✎</button>
                  <button class="btn btn-danger btn-sm btn-icon" title="Eliminar" @click="deleteEditorial(e)">🗑</button>
                </div>
              </td>
            </tr>
            <tr v-if="!loading && !filtradas.length">
              <td colspan="3" class="cell-empty">No hay editoriales</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <AppModal v-if="showModal" :title="editingId ? 'Editar editorial' : 'Nueva editorial'" @close="showModal = false">
      <form class="stack" @submit.prevent="saveEditorial">
        <div class="field" style="margin-bottom:0">
          <label for="nombre">Nombre *</label>
          <input id="nombre" v-model="nombre" class="input" maxlength="100" required />
        </div>
      </form>
      <template #footer>
        <button class="btn btn-outline" @click="showModal = false">Cancelar</button>
        <button class="btn btn-primary" :disabled="saving" @click="saveEditorial">
          {{ saving ? 'Guardando…' : 'Guardar' }}
        </button>
      </template>
    </AppModal>
  </div>
</template>
