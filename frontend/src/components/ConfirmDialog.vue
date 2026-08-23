<script setup>
import { useConfirm } from '../composables/useConfirm'

const { state, respond } = useConfirm()
</script>

<template>
  <div v-if="state.visible" class="modal-overlay" @click.self="respond(false)">
    <div class="modal" role="alertdialog" aria-modal="true">
      <div class="modal__header">
        <h3>{{ state.title }}</h3>
        <button class="modal-close" aria-label="Cerrar" @click="respond(false)">×</button>
      </div>
      <div class="modal__body">
        <p style="margin:0">{{ state.message }}</p>
      </div>
      <div class="modal__footer">
        <button class="btn btn-outline" @click="respond(false)">Cancelar</button>
        <button
          class="btn"
          :class="state.danger ? 'btn-danger' : 'btn-primary'"
          @click="respond(true)"
        >
          Confirmar
        </button>
      </div>
    </div>
  </div>
</template>
