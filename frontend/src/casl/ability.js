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

  // ADMIN y BIBLIOTECARIO: acceso total. La diferencia de jerarquía
  // (un BIBLIOTECARIO no puede gestionar a un ADMIN) se aplica en el
  // backend; aquí solo se usa para mostrar/ocultar UI.
  if (user.rol === 'ADMIN' || user.rol === 'BIBLIOTECARIO') {
    can('manage', 'all')
  } else {
    // PROFESOR comparte exactamente el mismo alcance que LECTOR por
    // decisión de producto (2026-09-05): perfil, préstamos propios, lectura.
    can('read', 'Libro')
    can(['create', 'read'], 'Prestamo', { id_usuario: user.id })
    can(['read', 'update'], 'Usuario', { id_usuario: user.id })
    can(['create', 'read', 'cancel'], 'Reserva', { id_usuario: user.id })
    can('read', 'Editorial')
    can('read', 'Ejemplar')
  }

  return build()
}
