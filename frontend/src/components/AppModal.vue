<script setup>
defineProps({
  title: { type: String, required: true }
})
const emit = defineEmits(['close'])
</script>

<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal" role="dialog" aria-modal="true">
      <div class="modal__header">
        <h3>{{ title }}</h3>
        <button class="modal-close" aria-label="Cerrar" @click="emit('close')">×</button>
      </div>
      <div class="modal__body">
        <slot />
      </div>
      <div class="modal__footer">
        <slot name="footer" />
      </div>
    </div>
  </div>
</template>
