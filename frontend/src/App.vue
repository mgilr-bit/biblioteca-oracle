<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppNavbar from './components/AppNavbar.vue'
import ToastStack from './components/ToastStack.vue'
import ConfirmDialog from './components/ConfirmDialog.vue'

const route = useRoute()
const showNav = computed(() => !route.meta.public)
</script>

<template>
  <AppNavbar v-if="showNav" />
  <main :class="{ 'container mt-4': showNav }">
    <router-view />
  </main>
  <ToastStack />
  <ConfirmDialog />
</template>
