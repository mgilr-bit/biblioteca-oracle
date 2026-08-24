"""Servicios de gestión de usuarios.

Devuelven entidades SQLModel (o listas de ellas); el mapeo a DTO de
respuesta (`schemas.usuario.UsuarioResponse`, que nunca incluye el
password) lo hace el router vía `response_model`.
"""
import logging

from models.usuario import Usuario
from repositories.usuario_repository import UsuarioRepository
from services.base import BaseService
from services.exceptions import BusinessRuleError, ValidationError
from utils.security import hash_password

logger = logging.getLogger(__name__)

ROLES_VALIDOS = ("LECTOR", "BIBLIOTECARIO")


class UsuarioService(BaseService[Usuario]):
    not_found_message = "Usuario no encontrado"

    def __init__(self, session):
        super().__init__(UsuarioRepository(session))

    def update(self, id_usuario: int, data: dict, requesting_user) -> dict:
        usuario = self.get_by_id(id_usuario)

        nombre = data.get("nombre")
        email = data.get("email")
        rol = data.get("rol")
        if not nombre or not email or not rol:
            raise ValidationError("Nombre, email y rol son requeridos")

        # SEGURIDAD: solo BIBLIOTECARIO puede cambiar el rol de un usuario;
        # un LECTOR editando su propio perfil no puede auto-promoverse.
        if requesting_user.rol != "BIBLIOTECARIO":
            rol = usuario.rol

        usuario.nombre = nombre
        usuario.email = email
        usuario.rol = rol
        self.repository.flush()

        return {"success": True, "message": "Usuario actualizado exitosamente"}

    def delete(self, id_usuario: int) -> dict:
        if self.repository.count_active_prestamos(id_usuario) > 0:
            raise BusinessRuleError(
                "No se puede eliminar el usuario. Tiene préstamos activos."
            )

        self.delete_entity(id_usuario)
        logger.info(f"Usuario {id_usuario} eliminado permanentemente")
        return {"success": True, "message": "Usuario eliminado permanentemente"}

    def create_admin(self, data: dict) -> dict:
        nombre = data.get("nombre")
        email = data.get("email")
        password = data.get("password")
        rol = data.get("rol")

        if not nombre or not email or not password or not rol:
            raise ValidationError(
                "Nombre, email, contraseña y rol son requeridos"
            )
        if rol not in ROLES_VALIDOS:
            raise ValidationError("Rol inválido. Debe ser LECTOR o BIBLIOTECARIO")
        if len(password) < 6:
            raise ValidationError("La contraseña debe tener al menos 6 caracteres")

        if self.repository.get_by_email(email):
            logger.warning(f"Intento de crear usuario con email duplicado: {email}")
            raise ValidationError("El email ya está registrado")

        usuario = Usuario(
            nombre=nombre,
            email=email,
            password=hash_password(password),
            rol=rol,
        )
        self.repository.add(usuario)

        logger.info(f"Nuevo usuario creado por admin: {email} con rol {rol}")
        return {"success": True, "message": f"Usuario creado exitosamente como {rol}"}

    def toggle_estado(self, id_usuario: int, activo) -> dict:
        if activo not in ("S", "N"):
            raise ValidationError("Estado inválido. Debe ser 'S' o 'N'")

        usuario = self.get_by_id(id_usuario)
        usuario.activo = activo
        self.repository.flush()

        estado_texto = "activado" if activo == "S" else "desactivado"
        logger.info(f"Usuario {id_usuario} {estado_texto}")
        return {"success": True, "message": f"Usuario {estado_texto} exitosamente"}
