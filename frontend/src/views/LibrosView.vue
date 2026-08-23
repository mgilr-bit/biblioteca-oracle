<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { librosAPI } from '../api'
import { useToast } from '../composables/useToast'
import { useConfirm } from '../composables/useConfirm'
import AppModal from '../components/AppModal.vue'
import AppPagination from '../components/AppPagination.vue'

const auth = useAuthStore()
const toast = useToast()
const { ask } = useConfirm()

const allLibros = ref([])
const generos = ref([])
const currentPage = ref(1)
const perPage = 50
const loading = ref(true)
const emptyMessage = ref('No hay libros')

const search = ref({ titulo: '', autor: '', isbn: '', genero: '' })

const paginatedLibros = computed(() => {
  const start = (currentPage.value - 1) * perPage
  return allLibros.value.slice(start, start + perPage)
})

async function loadGeneros() {
  try {
    generos.value = await librosAPI.getGeneros()
  } catch (error) {
    console.error('Error cargando géneros:', error)
  }
}

async function loadLibros() {
  loading.value = true
  search.value = { titulo: '', autor: '', isbn: '', genero: '' }
  try {
    const response = await librosAPI.getAll(1, 1000)
    allLibros.value = response.libros || response
    currentPage.value = 1
    emptyMessage.value = 'No hay libros'
  } catch (error) {
    toast.error('Error cargando libros: ' + error.message)
  } finally {
    loading.value = false
  }
}

async function searchLibros() {
  const params = new URLSearchParams()
  if (search.value.titulo) params.append('titulo', search.value.titulo)
  if (search.value.autor) params.append('autor', search.value.autor)
  if (search.value.isbn) params.append('isbn', search.value.isbn)
  if (search.value.genero) params.append('genero', search.value.genero)
  params.append('limit', '2000')

  loading.value = true
  try {
    allLibros.value = await librosAPI.search(params)
    currentPage.value = 1
    emptyMessage.value = 'No se encontraron resultados'
  } catch (error) {
    toast.error('Error buscando libros: ' + error.message)
  } finally {
    loading.value = false
  }
}

// --- Modal CRUD ---
const showModal = ref(false)
const editingId = ref(null)
const form = ref(emptyForm())

function emptyForm() {
  return { titulo: '', autor: '', isbn: '', anio: '', genero: '', editorial: '', copias: 1 }
}

function openCreate() {
  editingId.value = null
  form.value = emptyForm()
  showModal.value = true
}

function openEdit(libro) {
  editingId.value = libro.ID_LIBRO
  form.value = {
    titulo: libro.TITULO,
    autor: libro.AUTOR,
    isbn: libro.ISBN || '',
    anio: libro.ANIO_PUBLICACION || '',
    genero: libro.GENERO || '',
    editorial: libro.EDITORIAL || '',
    copias: libro.NUMERO_COPIAS
  }
  showModal.value = true
}

const saving = ref(false)

async function saveLibro() {
  const emptyToNull = (v) => (v === '' || v === null || v === undefined ? null : v)
  const payload = {
    titulo: form.value.titulo,
    autor: form.value.autor,
    isbn: emptyToNull(form.value.isbn),
    anio_publicacion: form.value.anio ? parseInt(form.value.anio) : null,
    genero: emptyToNull(form.value.genero),
    editorial: emptyToNull(form.value.editorial),
    numero_copias: form.value.copias ? parseInt(form.value.copias) : 1
  }

  saving.value = true
  try {
    const response = editingId.value
      ? await librosAPI.update(editingId.value, payload)
      : await librosAPI.create(payload)
    toast.success(response.message || 'Guardado correctamente')
    showModal.value = false
    loadLibros()
  } catch (error) {
    toast.error('Error: ' + error.message)
  } finally {
    saving.value = false
  }
}

async function deleteLibro(libro) {
  const ok = await ask(`¿Eliminar "${libro.TITULO}"? Esta acción no se puede deshacer.`, {
    title: 'Eliminar libro',
    danger: true
  })
  if (!ok) return

  try {
    const response = await librosAPI.delete(libro.ID_LIBRO)
    toast.success(response.message || 'Libro eliminado')
    loadLibros()
  } catch (error) {
    toast.error('Error: ' + error.message)
  }
}

async function exportarCSV() {
  try {
    const blob = await librosAPI.exportCSV()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `libros_${Date.now()}.csv`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    toast.success('Archivo CSV descargado')
  } catch (error) {
    toast.error('Error al exportar: ' + error.message)
  }
}

onMounted(() => {
  loadGeneros()
  loadLibros()
})
</script>

<template>
  <div class="stack">
    <div class="page-header">
      <h2>Gestión de libros</h2>
      <div class="cluster" v-if="auth.isBibliotecario">
        <button class="btn btn-outline" @click="exportarCSV">Exportar CSV</button>
        <button class="btn btn-primary" @click="openCreate">+ Nuevo libro</button>
      </div>
    </div>

    <div class="card">
      <div class="card__body stack">
        <div class="search-bar">
          <input v-model="search.titulo" class="input" placeholder="Buscar por título…" @keyup.enter="searchLibros" />
          <input v-model="search.autor" class="input" placeholder="Buscar por autor…" @keyup.enter="searchLibros" />
          <input v-model="search.isbn" class="input" placeholder="Buscar por ISBN…" @keyup.enter="searchLibros" />
          <select v-model="search.genero" class="select">
            <option value="">Todos los géneros</option>
            <option v-for="g in generos" :key="g" :value="g">{{ g }}</option>
          </select>
        </div>
        <div class="page-header" style="margin:0">
          <div class="cluster">
            <button class="btn btn-primary btn-sm" @click="searchLibros">Buscar</button>
            <button class="btn btn-outline btn-sm" @click="loadLibros">Limpiar</button>
          </div>
          <span class="text-muted" style="font-size:0.85rem">
            {{ allLibros.length }} libro(s)
          </span>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card__body table-wrap">
        <table class="data">
          <thead>
            <tr>
              <th>ID</th><th>Título</th><th>Autor</th><th>ISBN</th><th>Año</th>
              <th>Género</th><th>Copias</th><th>Disponibles</th><th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="libro in paginatedLibros" :key="libro.ID_LIBRO">
              <td class="cell-mono">{{ libro.ID_LIBRO }}</td>
              <td>{{ libro.TITULO }}</td>
              <td>{{ libro.AUTOR }}</td>
              <td class="cell-mono">{{ libro.ISBN || '-' }}</td>
              <td>{{ libro.ANIO_PUBLICACION || '-' }}</td>
              <td>{{ libro.GENERO || '-' }}</td>
              <td>{{ libro.NUMERO_COPIAS }}</td>
              <td>
                <span class="stamp" :class="libro.COPIAS_DISPONIBLES > 0 ? 'stamp-success' : 'stamp-danger'">
                  {{ libro.COPIAS_DISPONIBLES }}
                </span>
              </td>
              <td>
                <div v-if="auth.isBibliotecario" class="cluster">
                  <button class="btn btn-outline btn-sm btn-icon" title="Editar" @click="openEdit(libro)">✎</button>
                  <button class="btn btn-danger btn-sm btn-icon" title="Eliminar" @click="deleteLibro(libro)">🗑</button>
                </div>
                <span v-else class="text-muted" style="font-size:0.8rem">Solo lectura</span>
              </td>
            </tr>
            <tr v-if="!loading && !paginatedLibros.length">
              <td colspan="9" class="cell-empty">{{ emptyMessage }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="card__body" style="padding-top:0" v-if="allLibros.length > perPage">
        <AppPagination
          :current-page="currentPage"
          :total-items="allLibros.length"
          :per-page="perPage"
          @change="(p) => (currentPage = p)"
        />
      </div>
    </div>

    <AppModal v-if="showModal" :title="editingId ? 'Editar libro' : 'Nuevo libro'" @close="showModal = false">
      <form class="stack" @submit.prevent="saveLibro">
        <div class="field">
          <label for="titulo">Título *</label>
          <input id="titulo" v-model="form.titulo" class="input" required />
        </div>
        <div class="field">
          <label for="autor">Autor *</label>
          <input id="autor" v-model="form.autor" class="input" required />
        </div>
        <div class="field">
          <label for="isbn">ISBN</label>
          <input id="isbn" v-model="form.isbn" class="input" />
        </div>
        <div class="row-fields">
          <div class="field">
            <label for="anio">Año de publicación</label>
            <input id="anio" v-model="form.anio" type="number" min="1900" max="2030" class="input" />
          </div>
          <div class="field">
            <label for="genero">Género</label>
            <input id="genero" v-model="form.genero" class="input" />
          </div>
        </div>
        <div class="field">
          <label for="editorial">Editorial</label>
          <input id="editorial" v-model="form.editorial" class="input" />
        </div>
        <div class="field" style="margin-bottom:0">
          <label for="copias">Número de copias</label>
          <input id="copias" v-model="form.copias" type="number" min="1" class="input" />
        </div>
      </form>
      <template #footer>
        <button class="btn btn-outline" @click="showModal = false">Cancelar</button>
        <button class="btn btn-primary" :disabled="saving" @click="saveLibro">
          {{ saving ? 'Guardando…' : 'Guardar' }}
        </button>
      </template>
    </AppModal>
  </div>
</template>
