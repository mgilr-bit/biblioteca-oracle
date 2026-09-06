/**
 * Composable `useCan` — equivalente programático de la directiva `v-can`
 * para usar dentro de `<script setup>`:
 *
 *   const can = useCan()
 *   const puedeEditar = can('update', 'Libro')
 *
 * Reactivo de la misma forma que `v-can` (depende del store de auth).
 */
import { useAuthStore } from '../stores/auth'

export function useCan() {
  const auth = useAuthStore()

  return (action, subject, field) => auth.ability.can(action, subject, field)
}

export default useCan