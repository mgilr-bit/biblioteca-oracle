<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { authAPI } from "../api";
import { useAuthStore } from "../stores/auth";
import { useToast } from "../composables/useToast";

const router = useRouter();
const auth = useAuthStore();
const toast = useToast();

const loginForm = ref({ email: "", password: "" });

const loading = ref(false);

async function handleLogin() {
  loading.value = true;
  try {
    const data = await authAPI.login(
      loginForm.value.email,
      loginForm.value.password,
    );
    auth.setSession(data.user);
    router.push("/");
  } catch (error) {
    toast.error(error.message);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="auth-screen">
    <div class="auth-card card">
      <div class="card__body">
        <div class="auth-brand">
          <h1>Biblioteca</h1>
          <span class="auth-brand__rule" />
          <p class="text-muted">Gestión de inventario y préstamos</p>
        </div>

        <form class="stack" @submit.prevent="handleLogin">
          <div class="field">
            <label for="loginEmail">Email</label>
            <input
              id="loginEmail"
              v-model="loginForm.email"
              type="email"
              class="input"
              required
            />
          </div>
          <div class="field" style="margin-bottom: 0">
            <label for="loginPassword">Contraseña</label>
            <input
              id="loginPassword"
              v-model="loginForm.password"
              type="password"
              class="input"
              required
            />
          </div>
          <button
            class="btn btn-primary"
            style="width: 100%; justify-content: center"
            :disabled="loading"
            type="submit"
          >
            {{ loading ? "Entrando…" : "Iniciar sesión" }}
          </button>

          <p class="auth-note text-muted">
            El acceso es exclusivo para la comunidad universitaria. Si no tienes
            cuenta, solicítala a la universidad.
          </p>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-screen {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg) url("/login.jpg") center / cover no-repeat;
  padding: var(--space-4);
}

/* Vela suavemente la foto para que la tarjeta destaque y el texto
   del navegador (barra de direcciones, etc.) no compita visualmente. */
.auth-screen::before {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(
    180deg,
    rgba(20, 18, 14, 0.45) 0%,
    rgba(20, 18, 14, 0.25) 45%,
    rgba(20, 18, 14, 0.5) 100%
  );
}

.auth-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 400px;
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(6px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 24px 60px rgba(10, 9, 6, 0.35);
  border-radius: 10px;
}

.auth-brand {
  text-align: center;
  margin-bottom: var(--space-5);
}

.auth-brand h1 {
  margin-bottom: var(--space-2);
}

.auth-brand__rule {
  display: block;
  width: 40px;
  height: 3px;
  margin: 0 auto var(--space-3);
  background: var(--accent);
  border-radius: 2px;
}

.auth-note {
  margin: 0;
  text-align: center;
  font-size: 0.82rem;
  line-height: 1.4;
}
</style>
