<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { usuariosAPI } from '../api'
import { useToast } from '../composables/useToast'
import { useConfirm } from '../composables/useConfirm'
import AppModal from '../components/AppModal.vue'
import ReportButton from '../components/ReportButton.vue'

const auth = useAuthStore()
const toast = useToast()
const { ask } = useConfirm()

const todos = ref([])
const loading = ref(true)

const filtro = ref({ nombre: '', rol: '', estado: '' })

const filtrados = computed(() => {
  return todos.value.filter((u) => {
    const nombre = filtro.value.nombre.toLowerCase()
    const matchNombre =
      !nombre || u.NOMBRE.toLowerCase().includes(nombre) || u.EMAIL.toLowerCase().includes(nombre)
    const matchRol = !filtro.value.rol || u.ROL === filtro.value.rol
    const matchEstado = !filtro.value.estado || u.ACTIVO === filtro.value.estado
    return matchNombre && matchRol && matchEstado
  })
})

// Un sello de color por rol: antes ADMIN, PROFESOR y LECTOR compartían el
// mismo azul y solo BIBLIOTECARIO se distinguía. El color sigue el nivel de
// privilegio (rojo → ámbar → verde → azul); `neutral` cubre roles futuros.
const STAMP_POR_ROL = {
  ADMIN: 'stamp-danger',
  BIBLIOTECARIO: 'stamp-warning',
  PROFESOR: 'stamp-success',
  LECTOR: 'stamp-info'
}

function stampRol(rol) {
  return STAMP_POR_ROL[rol] || 'stamp-neutral'
}

async function loadUsuarios() {
  loading.value = true
  try {
    todos.value = await usuariosAPI.getAll()
  } catch (error) {
    toast.error('Error cargando usuarios: ' + error.message)
  } finally {
    loading.value = false
  }
}

// --- Modal CRUD ---
const showModal = ref(false)
const editingId = ref(null)
const form = ref(emptyForm())
const saving = ref(false)

function emptyForm() {
  return { nombre: '', email: '', password: '', rol: 'LECTOR' }
}

function openCreate() {
  editingId.value = null
  form.value = emptyForm()
  showModal.value = true
}

function openEdit(u) {
  editingId.value = u.ID_USUARIO
  form.value = { nombre: u.NOMBRE, email: u.EMAIL, password: '', rol: u.ROL }
  showModal.value = true
}

async function saveUsuario() {
  if (!form.value.nombre || !form.value.email || !form.value.rol) {
    toast.error('Completa todos los campos obligatorios')
    return
  }
  if (!editingId.value && !form.value.password) {
    toast.error('La contraseña es requerida para nuevos usuarios')
    return
  }
  // El backend exige 8 caracteres (NIST SP 800-63B); validarlo aquí evita
  // un 422 y da el motivo exacto sin ir al servidor.
  if (!editingId.value && form.value.password.length < 8) {
    toast.error('La contraseña debe tener al menos 8 caracteres')
    return
  }

  saving.value = true
  try {
    const response = editingId.value
      ? await usuariosAPI.update(editingId.value, {
          nombre: form.value.nombre,
          email: form.value.email,
          rol: form.value.rol
        })
      : await usuariosAPI.createAdmin({
          nombre: form.value.nombre,
          email: form.value.email,
          password: form.value.password,
          rol: form.value.rol
        })
    toast.success(response.message || 'Usuario guardado')
    showModal.value = false
    loadUsuarios()
  } catch (error) {
    toast.error('Error: ' + error.message)
  } finally {
    saving.value = false
  }
}

async function toggleEstado(u) {
  const nuevoEstado = u.ACTIVO === 'S' ? 'N' : 'S'
  const accion = nuevoEstado === 'S' ? 'activar' : 'desactivar'
  const ok = await ask(`¿Deseas ${accion} a "${u.NOMBRE}"?`, { title: 'Cambiar estado' })
  if (!ok) return

  try {
    const response = await usuariosAPI.toggleEstado(u.ID_USUARIO, nuevoEstado)
    toast.success(response.message || 'Estado actualizado')
    loadUsuarios()
  } catch (error) {
    toast.error('Error: ' + error.message)
  }
}

async function deleteUsuario(u) {
  const ok = await ask(`¿Eliminar permanentemente a "${u.NOMBRE}"? Esta acción no se puede deshacer.`, {
    title: 'Eliminar usuario',
    danger: true
  })
  if (!ok) return

  try {
    const response = await usuariosAPI.delete(u.ID_USUARIO)
    toast.success(response.message || 'Usuario eliminado')
    loadUsuarios()
  } catch (error) {
    toast.error('Error: ' + error.message)
  }
}

onMounted(loadUsuarios)
</script>

<template>
  <div class="stack">
    <div class="page-header">
      <h2>Gestión de usuarios</h2>
      <div class="cluster">
        <ReportButton seccion="usuarios" :filtros="filtro" />
        <button class="btn btn-primary" @click="openCreate">+ Nuevo usuario</button>
      </div>
    </div>

    <div class="card">
      <div class="card__body">
        <div class="search-bar">
          <input v-model="filtro.nombre" class="input" placeholder="Buscar por nombre o email…" />
          <select v-model="filtro.rol" class="select">
            <option value="">Todos los roles</option>
            <option value="ADMIN">Administradores</option>
            <option value="BIBLIOTECARIO">Bibliotecarios</option>
            <option value="PROFESOR">Profesores</option>
            <option value="LECTOR">Lectores</option>
          </select>
          <select v-model="filtro.estado" class="select">
            <option value="">Todos los estados</option>
            <option value="S">Activos</option>
            <option value="N">Inactivos</option>
          </select>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card__body table-wrap">
        <table class="data">
          <thead>
            <tr>
              <th>ID</th><th>Nombre</th><th>Email</th><th>Rol</th>
              <th>Estado</th><th>Registro</th><th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in filtrados" :key="u.ID_USUARIO">
              <td class="cell-mono">{{ u.ID_USUARIO }}</td>
              <td>{{ u.NOMBRE }}</td>
              <td>{{ u.EMAIL }}</td>
              <td>
                <span class="stamp" :class="stampRol(u.ROL)">
                  {{ u.ROL }}
                </span>
              </td>
              <td>
                <span class="stamp" :class="u.ACTIVO === 'S' ? 'stamp-success' : 'stamp-neutral'">
                  {{ u.ACTIVO === 'S' ? 'Activo' : 'Inactivo' }}
                </span>
              </td>
              <td>{{ new Date(u.FECHA_REGISTRO).toLocaleDateString() }}</td>
              <td>
                <div class="cluster">
                  <button class="btn btn-outline btn-sm btn-icon" title="Editar" @click="openEdit(u)">✎</button>
                  <button
                    class="btn btn-sm btn-icon"
                    :class="u.ACTIVO === 'S' ? 'btn-outline' : 'btn-success'"
                    :title="u.ACTIVO === 'S' ? 'Desactivar' : 'Activar'"
                    @click="toggleEstado(u)"
                  >
                    {{ u.ACTIVO === 'S' ? '⛔' : '✓' }}
                  </button>
                  <button
                    v-if="u.ID_USUARIO !== auth.user.id"
                    class="btn btn-danger btn-sm btn-icon"
                    title="Eliminar"
                    @click="deleteUsuario(u)"
                  >
                    🗑
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="!loading && !filtrados.length">
              <td colspan="7" class="cell-empty">No hay usuarios</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <AppModal v-if="showModal" :title="editingId ? 'Editar usuario' : 'Nuevo usuario'" @close="showModal = false">
      <form class="stack" @submit.prevent="saveUsuario">
        <div class="field">
          <label for="nombre">Nombre completo *</label>
          <input id="nombre" v-model="form.nombre" class="input" required />
        </div>
        <div class="field">
          <label for="email">Email *</label>
          <input id="email" v-model="form.email" type="email" class="input" required />
        </div>
        <div class="field" v-if="!editingId">
          <label for="password">Contraseña *</label>
          <input id="password" v-model="form.password" type="password" class="input" minlength="8" required />
          <small class="hint">Mínimo 8 caracteres</small>
        </div>
        <div class="field" style="margin-bottom:0">
          <label for="rol">Rol *</label>
          <select id="rol" v-model="form.rol" class="select" required>
            <option value="LECTOR">Lector</option>
            <option value="PROFESOR">Profesor</option>
            <option value="BIBLIOTECARIO">Bibliotecario</option>
          </select>
          <small class="hint">Los bibliotecarios tienen acceso administrativo completo</small>
        </div>
      </form>
      <template #footer>
        <button class="btn btn-outline" @click="showModal = false">Cancelar</button>
        <button class="btn btn-primary" :disabled="saving" @click="saveUsuario">
          {{ saving ? 'Guardando…' : 'Guardar' }}
        </button>
      </template>
    </AppModal>
  </div>
</template>
