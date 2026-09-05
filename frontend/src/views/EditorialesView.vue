<script setup>
import { ref, onMounted } from 'vue'
import { editorialesAPI } from '../api'
import { useToast } from '../composables/useToast'
import { useConfirm } from '../composables/useConfirm'
import { useCan } from '../composables/useCan'
import AppModal from '../components/AppModal.vue'

const can = useCan()
const toast = useToast()
const { ask } = useConfirm()

const editoriales = ref([])
const loading = ref(true)
const emptyMessage = ref('No hay editoriales')

async function loadEditoriales() {
  loading.value = true
  try {
    const response = await editorialesAPI.getAll(1, 1000)
    editoriales.value = response.editoriales || response
    emptyMessage.value = 'No hay editoriales'
  } catch (error) {
    toast.error('Error cargando editoriales: ' + error.message)
  } finally {
    loading.value = false
  }
}

// --- Modal CRUD ---
const showModal = ref(false)
const editingId = ref(null)
const form = ref(emptyForm())

function emptyForm() {
  return { nombre: '', pais: '', sitio_web: '' }
}

function openCreate() {
  editingId.value = null
  form.value = emptyForm()
  showModal.value = true
}

function openEdit(editorial) {
  editingId.value = editorial.ID_EDITORIAL
  form.value = {
    nombre: editorial.NOMBRE,
    pais: editorial.PAIS || '',
    sitio_web: editorial.SITIO_WEB || ''
  }
  showModal.value = true
}

const saving = ref(false)

async function saveEditorial() {
  const emptyToNull = (v) => (v === '' || v === null || v === undefined ? null : v)
  const payload = {
    nombre: form.value.nombre,
    pais: emptyToNull(form.value.pais),
    sitio_web: emptyToNull(form.value.sitio_web)
  }

  saving.value = true
  try {
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
  const ok = await ask(`¿Eliminar la editorial "${editorial.NOMBRE}"? Los libros asociados se desligarán.`, {
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
      <h2>Gestión de editoriales</h2>
      <button v-can:create="'Editorial'" class="btn btn-primary" @click="openCreate">+ Nueva editorial</button>
    </div>

    <div class="card">
      <div class="card__body table-wrap">
        <table class="data">
          <thead>
            <tr>
              <th>ID</th><th>Nombre</th><th>País</th><th>Sitio web</th><th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="editorial in editoriales" :key="editorial.ID_EDITORIAL">
              <td class="cell-mono">{{ editorial.ID_EDITORIAL }}</td>
              <td>{{ editorial.NOMBRE }}</td>
              <td>{{ editorial.PAIS || '-' }}</td>
              <td>
                <a v-if="editorial.SITIO_WEB" :href="editorial.SITIO_WEB" target="_blank" rel="noopener">
                  {{ editorial.SITIO_WEB }}
                </a>
                <span v-else>-</span>
              </td>
              <td>
                <div class="cluster">
                  <button v-can:update="'Editorial'" class="btn btn-outline btn-sm btn-icon" title="Editar" @click="openEdit(editorial)">✎</button>
                  <button v-can:delete="'Editorial'" class="btn btn-danger btn-sm btn-icon" title="Eliminar" @click="deleteEditorial(editorial)">🗑</button>
                </div>
                <span v-if="!can('update', 'Editorial') && !can('delete', 'Editorial')" class="text-muted" style="font-size:0.8rem">Solo lectura</span>
              </td>
            </tr>
            <tr v-if="!loading && !editoriales.length">
              <td colspan="5" class="cell-empty">{{ emptyMessage }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <AppModal v-if="showModal" :title="editingId ? 'Editar editorial' : 'Nueva editorial'" @close="showModal = false">
      <form class="stack" @submit.prevent="saveEditorial">
        <div class="field">
          <label for="nombre">Nombre *</label>
          <input id="nombre" v-model="form.nombre" class="input" required />
        </div>
        <div class="field">
          <label for="pais">País</label>
          <input id="pais" v-model="form.pais" class="input" />
        </div>
        <div class="field" style="margin-bottom:0">
          <label for="sitioWeb">Sitio web</label>
          <input id="sitioWeb" v-model="form.sitio_web" class="input" placeholder="https://…" />
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