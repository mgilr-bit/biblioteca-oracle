<script setup>
import { ref, computed, onMounted } from "vue";
import { useAuthStore } from "../stores/auth";
import { prestamosAPI, librosAPI, usuariosAPI } from "../api";
import { useToast } from "../composables/useToast";
import { useConfirm } from "../composables/useConfirm";
import { useCan } from "../composables/useCan";
import AppModal from "../components/AppModal.vue";

const auth = useAuthStore();
const can = useCan();
const toast = useToast();
const { ask } = useConfirm();

const allPrestamos = ref([]);
const activeTab = ref("todos");
const loading = ref(true);

const filters = ref({ fechaPrestamo: "", fechaDevolucion: "", libro: "" });

function extractDate(value) {
  if (!value) return "";
  return value.split("T")[0].split(" ")[0].trim();
}

const filteredPrestamos = computed(() => {
  return allPrestamos.value.filter((p) => {
    if (
      filters.value.fechaPrestamo &&
      extractDate(p.FECHA_PRESTAMO) !== filters.value.fechaPrestamo
    ) {
      return false;
    }
    if (
      filters.value.fechaDevolucion &&
      extractDate(p.FECHA_DEVOLUCION_ESPERADA) !== filters.value.fechaDevolucion
    ) {
      return false;
    }
    if (
      filters.value.libro &&
      !p.TITULO?.toLowerCase().includes(filters.value.libro.toLowerCase())
    ) {
      return false;
    }
    return true;
  });
});

function clearFilters() {
  filters.value = { fechaPrestamo: "", fechaDevolucion: "", libro: "" };
}

async function loadTab(tab) {
  activeTab.value = tab;
  loading.value = true;
  clearFilters();
  try {
    if (tab === "todos") {
      allPrestamos.value = auth.isBibliotecario
        ? await prestamosAPI.getAll()
        : await prestamosAPI.getByUsuario(auth.user.id);
    } else if (tab === "activos") {
      if (auth.isBibliotecario) {
        allPrestamos.value = await prestamosAPI.getActivos();
      } else {
        const todos = await prestamosAPI.getByUsuario(auth.user.id);
        allPrestamos.value = todos.filter(
          (p) => p.ESTADO === "ACTIVO" || p.ESTADO === "VENCIDO",
        );
      }
    } else if (tab === "vencidos") {
      if (auth.isBibliotecario) {
        allPrestamos.value = await prestamosAPI.getVencidos();
      } else {
        const todos = await prestamosAPI.getByUsuario(auth.user.id);
        allPrestamos.value = todos.filter((p) => p.ESTADO === "VENCIDO");
      }
    }
  } catch (error) {
    toast.error("Error cargando préstamos: " + error.message);
  } finally {
    loading.value = false;
  }
}

function badgeClass(estado) {
  if (estado === "DEVUELTO") return "stamp-neutral";
  if (estado === "VENCIDO") return "stamp-danger";
  return "stamp-success";
}

// --- Modal nuevo préstamo ---
const showModal = ref(false);
const libroOptions = ref([]);
const usuarioOptions = ref([]);
const form = ref({ id_libro: "", id_usuario: "", dias_prestamo: 14 });
const saving = ref(false);

async function openModal() {
  form.value = { id_libro: "", id_usuario: "", dias_prestamo: 14 };
  showModal.value = true;
  try {
    const [respLibros, usuarios] = await Promise.all([
      librosAPI.getAll(1, 2000),
      usuariosAPI.getAll(),
    ]);
    const libros = respLibros.libros || respLibros;
    libroOptions.value = libros.filter((l) => l.COPIAS_DISPONIBLES > 0);
    usuarioOptions.value = usuarios.filter((u) => u.ACTIVO === "S");
  } catch (error) {
    toast.error("Error cargando datos: " + error.message);
  }
}

async function savePrestamo() {
  if (!form.value.id_libro || !form.value.id_usuario) {
    toast.error("Selecciona un libro y un usuario");
    return;
  }

  saving.value = true;
  try {
    const response = await prestamosAPI.create({
      id_libro: parseInt(form.value.id_libro),
      id_usuario: parseInt(form.value.id_usuario),
      dias_prestamo: parseInt(form.value.dias_prestamo),
    });
    toast.success(response.message || "Préstamo creado");
    showModal.value = false;
    loadTab(activeTab.value);
  } catch (error) {
    toast.error("Error: " + error.message);
  } finally {
    saving.value = false;
  }
}

async function devolver(prestamo) {
  const ok = await ask(`¿Registrar la devolución de "${prestamo.TITULO}"?`, {
    title: "Devolver libro",
  });
  if (!ok) return;

  try {
    const response = await prestamosAPI.devolver(prestamo.ID_PRESTAMO);
    toast.success(response.message || "Devolución registrada");
    loadTab(activeTab.value);
  } catch (error) {
    toast.error("Error: " + error.message);
  }
}

onMounted(() => loadTab("todos"));
</script>

<template>
  <div class="stack">
    <div class="page-header">
      <h2>Gestión de préstamos</h2>
      <button
        v-can:create="'Prestamo'"
        class="btn btn-primary"
        @click="openModal"
      >
        + Nuevo préstamo
      </button>
    </div>

    <div class="card">
      <div class="card__body">
        <div class="search-bar">
          <div class="field" style="margin: 0">
            <label for="fp">Fecha de préstamo</label>
            <input
              id="fp"
              v-model="filters.fechaPrestamo"
              type="date"
              class="input"
            />
          </div>
          <div class="field" style="margin: 0">
            <label for="fd">Fecha de devolución</label>
            <input
              id="fd"
              v-model="filters.fechaDevolucion"
              type="date"
              class="input"
            />
          </div>
          <div class="field" style="margin: 0; grid-column: span 2">
            <label for="lb">Libro</label>
            <input
              id="lb"
              v-model="filters.libro"
              class="input"
              placeholder="Buscar por título…"
            />
          </div>
        </div>
        <div class="cluster mt-4">
          <button class="btn btn-outline btn-sm" @click="clearFilters">
            Limpiar filtros
          </button>
        </div>
      </div>
    </div>

    <div class="cluster" role="tablist">
      <button
        v-for="t in [
          ['todos', 'Todos'],
          ['activos', 'Activos'],
          ['vencidos', 'Vencidos'],
        ]"
        :key="t[0]"
        class="app-nav__link"
        :class="{ 'is-active': activeTab === t[0] }"
        @click="loadTab(t[0])"
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
              <th>Autor</th>
              <th v-can:manage="'Prestamo'">Usuario</th>
              <th>Ejemplar</th>
              <th>Préstamo</th>
              <th>Devolución</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in filteredPrestamos" :key="p.ID_PRESTAMO">
              <td class="cell-mono">{{ p.ID_PRESTAMO }}</td>
              <td>{{ p.TITULO }}</td>
              <td>{{ p.AUTOR || "-" }}</td>
              <td v-can:manage="'Prestamo'">{{ p.NOMBRE_USUARIO || "" }}</td>
              <td class="cell-mono">{{ p.CODIGO_EJEMPLAR || "-" }}</td>
              <td>{{ new Date(p.FECHA_PRESTAMO).toLocaleDateString() }}</td>
              <td>
                {{ new Date(p.FECHA_DEVOLUCION_ESPERADA).toLocaleDateString() }}
              </td>
              <td>
                <span class="stamp" :class="badgeClass(p.ESTADO)">{{
                  p.ESTADO
                }}</span>
              </td>
              <td>
                <button
                  v-can:devolver="'Prestamo'"
                  v-if="p.ESTADO !== 'DEVUELTO'"
                  class="btn btn-success btn-sm"
                  @click="devolver(p)"
                >
                  Devolver
                </button>
                <span
                  v-if="p.ESTADO === 'DEVUELTO' || !can('devolver', 'Prestamo')"
                  class="text-muted"
                  style="font-size: 0.8rem"
                >
                  {{ p.ESTADO === "DEVUELTO" ? "Devuelto" : "-" }}
                </span>
              </td>
            </tr>
            <tr v-if="!loading && !filteredPrestamos.length">
              <td :colspan="can('manage', 'Prestamo') ? 9 : 8" class="cell-empty">
                No hay préstamos
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <AppModal
      v-if="showModal"
      title="Nuevo préstamo"
      @close="showModal = false"
    >
      <form class="stack" @submit.prevent="savePrestamo">
        <div class="field">
          <label for="libroSelect">Libro *</label>
          <select
            id="libroSelect"
            v-model="form.id_libro"
            class="select"
            required
          >
            <option value="">Seleccione un libro</option>
            <option
              v-for="l in libroOptions"
              :key="l.ID_LIBRO"
              :value="l.ID_LIBRO"
            >
              {{ l.TITULO }} — {{ l.AUTOR }} ({{
                l.COPIAS_DISPONIBLES
              }}
              disponibles)
            </option>
          </select>
        </div>
        <div class="field">
          <label for="usuarioSelect">Usuario *</label>
          <select
            id="usuarioSelect"
            v-model="form.id_usuario"
            class="select"
            required
          >
            <option value="">Seleccione un usuario</option>
            <option
              v-for="u in usuarioOptions"
              :key="u.ID_USUARIO"
              :value="u.ID_USUARIO"
            >
              {{ u.NOMBRE }} ({{ u.EMAIL }})
            </option>
          </select>
        </div>
        <div class="field" style="margin-bottom: 0">
          <label for="dias">Días de préstamo</label>
          <input
            id="dias"
            v-model="form.dias_prestamo"
            type="number"
            min="1"
            class="input"
          />
        </div>
      </form>
      <template #footer>
        <button class="btn btn-outline" @click="showModal = false">
          Cancelar
        </button>
        <button
          class="btn btn-primary"
          :disabled="saving"
          @click="savePrestamo"
        >
          {{ saving ? "Creando…" : "Crear préstamo" }}
        </button>
      </template>
    </AppModal>
  </div>
</template>
