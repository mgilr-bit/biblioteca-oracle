/**
 * CASL: solo gating de UI (mostrar/ocultar según permisos). La autorización
 * real vive en el backend (Casbin, RBAC+ABAC) — esto es puramente UX, nunca
 * la fuente de verdad; el backend siempre revalida cada acción.
 */
import { AbilityBuilder, createMongoAbility } from '@casl/ability'

export function buildAbilityFor(user) {
  const { can, build } = new AbilityBuilder(createMongoAbility)

  if (!user) {
    return build()
  }

  if (user.rol === 'BIBLIOTECARIO') {
    can('manage', 'all')
  } else {
    can('read', 'Libro')
    can(['create', 'read'], 'Prestamo', { id_usuario: user.id })
    can('read', 'Multa', { id_usuario: user.id })
    can(['read', 'update'], 'Usuario', { id_usuario: user.id })
  }

  return build()
}
