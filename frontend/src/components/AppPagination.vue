<script setup>
import { computed } from 'vue'

const props = defineProps({
  currentPage: { type: Number, required: true },
  totalItems: { type: Number, required: true },
  perPage: { type: Number, required: true }
})
const emit = defineEmits(['change'])

const totalPages = computed(() => Math.max(1, Math.ceil(props.totalItems / props.perPage)))

const pages = computed(() => {
  const max = 5
  let start = Math.max(1, props.currentPage - Math.floor(max / 2))
  let end = Math.min(totalPages.value, start + max - 1)
  if (end - start < max - 1) start = Math.max(1, end - max + 1)
  const arr = []
  for (let i = start; i <= end; i++) arr.push(i)
  return arr
})

function go(page) {
  if (page < 1 || page > totalPages.value) return
  emit('change', page)
}
</script>

<template>
  <div class="cluster">
    <ul class="pager">
      <li>
        <button :disabled="currentPage === 1" @click="go(currentPage - 1)" aria-label="Anterior">‹</button>
      </li>
      <li v-if="pages[0] > 1">
        <button @click="go(1)">1</button>
      </li>
      <li v-if="pages[0] > 2"><span class="text-muted">…</span></li>
      <li v-for="p in pages" :key="p">
        <button :class="{ 'is-active': p === currentPage }" @click="go(p)">{{ p }}</button>
      </li>
      <li v-if="pages[pages.length - 1] < totalPages - 1"><span class="text-muted">…</span></li>
      <li v-if="pages[pages.length - 1] < totalPages">
        <button @click="go(totalPages)">{{ totalPages }}</button>
      </li>
      <li>
        <button :disabled="currentPage === totalPages" @click="go(currentPage + 1)" aria-label="Siguiente">›</button>
      </li>
    </ul>
  </div>
</template>
