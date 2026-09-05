"""Servicios de gestión de usuarios.

Devuelven entidades SQLModel (o listas de ellas); el mapeo a DTO de
respuesta (`schemas.usuario.UsuarioResponse`, que nunca incluye el
password) lo hace el router vía `response_model`.
"""
import logging

from core.messages import UsuarioMessages
from models.usuario import Usuario
from repositories.usuario_repository import UsuarioRepository
from services.base import BaseService
from services.exceptions import BusinessRuleError, ValidationError
from utils.security import hash_password

logger = logging.getLogger(__name__)

ROLES_VALIDOS = ("LECTOR", "PROFESOR", "BIBLIOTECARIO", "ADMIN")
ROLES_SOLO_ADMIN = ("BIBLIOTECARIO", "ADMIN")


def _es_rol_superior(rol: str) -> bool:
    """Roles que solo un ADMIN puede crear o asignar."""
    return rol in ROLES_SOLO_ADMIN


def _validar_cambio_rol(actor_rol: str, rol_objetivo: str) -> None:
    """Un BIBLIOTECARIO no puede crear/asignar BIBLIOTECARIO ni ADMIN.

    Un LECTOR/PROFESOR nunca llega aquí (no puede cambiar roles, lo fuerza
    `update`); un ADMIN pasa sin restricción.
    """
    if actor_rol == "BIBLIOTECARIO" and _es_rol_superior(rol_objetivo):
        raise BusinessRuleError(UsuarioMessages.ROL_SUPERIOR_BLOQUEADO)


def _validar_objetivo_protegido(target_rol: str, actor_rol: str) -> None:
    """Un usuario con rol ADMIN solo puede ser tocado por otro ADMIN."""
    if target_rol == "ADMIN" and actor_rol != "ADMIN":
        raise BusinessRuleError(UsuarioMessages.SOLO_ADMIN_GESTIONA_ADMIN)


class UsuarioService(BaseService[Usuario]):
    not_found_message = UsuarioMessages.NOT_FOUND

    def __init__(self, session):
        super().__init__(UsuarioRepository(session))

    def update(self, id_usuario: int, data: dict, requesting_user) -> dict:
        usuario = self.get_by_id(id_usuario)

        nombre = data.get("nombre")
        email = data.get("email")
        rol = data.get("rol")
        if not nombre or not email or not rol:
            raise ValidationError(UsuarioMessages.UPDATE_CAMPOS_REQUERIDOS)
        if rol not in ROLES_VALIDOS:
            raise ValidationError(UsuarioMessages.ROL_INVALIDO)

        _validar_objetivo_protegido(usuario.rol, requesting_user.rol)

        # SEGURIDAD: solo BIBLIOTECARIO/ADMIN puede cambiar el rol de otro
        # usuario; un LECTOR/PROFESOR editando su propio perfil no puede
        # auto-promoverse. Y un BIBLIOTECARIO no puede asignar roles superiores.
        if requesting_user.rol in ("LECTOR", "PROFESOR"):
            rol = usuario.rol
        else:
            _validar_cambio_rol(requesting_user.rol, rol)

        usuario.nombre = nombre
        usuario.email = email
        usuario.rol = rol
        self.repository.mark_updated(usuario, actor=requesting_user.email)
        self.repository.flush()

        return {"success": True, "message": "Usuario actualizado exitosamente"}

    def delete(self, id_usuario: int, requesting_user) -> dict:
        usuario = self.get_by_id(id_usuario)
        _validar_objetivo_protegido(usuario.rol, requesting_user.rol)

        if self.repository.count_active_prestamos(id_usuario) > 0:
            raise BusinessRuleError(UsuarioMessages.TIENE_PRESTAMOS_ACTIVOS)

        self.delete_entity(id_usuario, actor=requesting_user.email)
        logger.info(f"Usuario {id_usuario} eliminado (soft-delete) por {requesting_user.email}")
        return {"success": True, "message": "Usuario eliminado exitosamente"}

    def create_admin(self, data: dict, requesting_user) -> dict:
        nombre = data.get("nombre")
        email = data.get("email")
        password = data.get("password")
        rol = data.get("rol")

        if not nombre or not email or not password or not rol:
            raise ValidationError(UsuarioMessages.ADMIN_CAMPOS_REQUERIDOS)
        if rol not in ROLES_VALIDOS:
            raise ValidationError(UsuarioMessages.ROL_INVALIDO)
        _validar_longitud_password(password)

        _validar_cambio_rol(requesting_user.rol, rol)

        if self.repository.get_by_email(email):
            logger.warning(f"Intento de crear usuario con email duplicado: {email}")
            raise ValidationError(UsuarioMessages.EMAIL_DUPLICADO)

        usuario = Usuario(
            nombre=nombre,
            email=email,
            password=hash_password(password),
            rol=rol,
        )
        self.repository.add(usuario, actor=requesting_user.email)

        logger.info(
            f"Nuevo usuario creado por {requesting_user.email}: {email} con rol {rol}"
        )
        return {"success": True, "message": f"Usuario creado exitosamente como {rol}"}

    def toggle_estado(self, id_usuario: int, activo, requesting_user) -> dict:
        if activo not in ("S", "N"):
            raise ValidationError(UsuarioMessages.ESTADO_INVALIDO)

        usuario = self.get_by_id(id_usuario)
        _validar_objetivo_protegido(usuario.rol, requesting_user.rol)

        usuario.activo = activo
        self.repository.mark_updated(usuario, actor=requesting_user.email)
        self.repository.flush()

        estado_texto = "activado" if activo == "S" else "desactivado"
        logger.info(f"Usuario {id_usuario} {estado_texto} por {requesting_user.email}")
        return {"success": True, "message": f"Usuario {estado_texto} exitosamente"}


def _validar_longitud_password(password: str) -> None:
    # NIST SP 800-63B 5.1.1.2: mínimo 8 caracteres, sin reglas de
    # complejidad forzada. El máximo evita el truncamiento silencioso de
    # bcrypt (trunca a 72 bytes) — mejor rechazar explícito que aceptar
    # una contraseña cuyos caracteres extra nunca se validan.
    if len(password) < 8:
        raise ValidationError(UsuarioMessages.PASSWORD_MUY_CORTA)
    if len(password.encode("utf-8")) > 72:
        raise ValidationError(UsuarioMessages.PASSWORD_MUY_LARGA)
