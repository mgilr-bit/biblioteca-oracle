/**
 * CASL: solo gating de UI (mostrar/ocultar según permisos). La autorización
 * real vive en el backend (Casbin, RBAC+ABAC) — esto es puramente UX, nunca
 * la fuente de verdad; el backend siempre revalida cada acción.
 */
import { AbilityBuilder, createMongoAbility } from '@casl/ability'

export function buildAbilityFor(user) {
  const { can, cannot, build } = new AbilityBuilder(createMongoAbility)

  if (!user) {
    return build()
  }

  // ADMIN y BIBLIOTECARIO: acceso total. La diferencia de jerarquía
  // (un BIBLIOTECARIO no puede gestionar a un ADMIN) se aplica en el
  // backend; aquí solo se usa para mostrar/ocultar UI.
  if (user.rol === 'ADMIN' || user.rol === 'BIBLIOTECARIO') {
    can('manage', 'all')
    // La bitácora de auditoría es exclusiva del ADMIN: registra lo que hace
    // el propio equipo de biblioteca, así que un BIBLIOTECARIO no la ve.
    // El backend lo revalida (política Casbin retirada en REVOKED_POLICIES).
    if (user.rol !== 'ADMIN') {
      cannot('read', 'Auditoria')
    }
  } else {
    // PROFESOR comparte exactamente el mismo alcance que LECTOR por
    // decisión de producto (2026-09-05): perfil, préstamos propios, lectura.
    can('read', 'Libro')
    can(['create', 'read'], 'Prestamo', { id_usuario: user.id })
    can('read', 'Multa', { id_usuario: user.id })
    can(['read', 'update'], 'Usuario', { id_usuario: user.id })
    can(['create', 'read', 'cancel'], 'Reserva', { id_usuario: user.id })
    can('read', 'Editorial')
    can('read', 'Ejemplar')
    can('read', 'Multa')
  }

  return build()
}
