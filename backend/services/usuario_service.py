"""Servicios de gestión de usuarios."""
import logging

from models.usuario import Usuario
from repositories.usuario_repository import UsuarioRepository
from services.exceptions import (
    BusinessRuleError,
    NotFoundError,
    ValidationError,
)
from utils.security import hash_password
from utils.serializers import to_dict, to_list

logger = logging.getLogger(__name__)

ROLES_VALIDOS = ("LECTOR", "BIBLIOTECARIO")
CAMPOS_SENSIBLES = {"password"}


class UsuarioService:
    def __init__(self, session):
        self.usuario_repo = UsuarioRepository(session)

    def get_all(self):
        return to_list(self.usuario_repo.get_all(), exclude=CAMPOS_SENSIBLES)

    def get_by_id(self, id_usuario):
        usuario = self.usuario_repo.get_by_id(id_usuario)
        if not usuario:
            raise NotFoundError("Usuario no encontrado")
        return to_dict(usuario, exclude=CAMPOS_SENSIBLES)

    def update(self, id_usuario, data):
        usuario = self.usuario_repo.get_by_id(id_usuario)
        if not usuario:
            raise NotFoundError("Usuario no encontrado")

        nombre = data.get("nombre")
        email = data.get("email")
        rol = data.get("rol")
        if not nombre or not email or not rol:
            raise ValidationError("Nombre, email y rol son requeridos")

        usuario.nombre = nombre
        usuario.email = email
        usuario.rol = rol
        self.usuario_repo.flush()

        return {"success": True, "message": "Usuario actualizado exitosamente"}

    def delete(self, id_usuario):
        if self.usuario_repo.count_active_prestamos(id_usuario) > 0:
            raise BusinessRuleError(
                "No se puede eliminar el usuario. Tiene préstamos activos."
            )

        usuario = self.usuario_repo.get_by_id(id_usuario)
        if not usuario:
            raise NotFoundError("Usuario no encontrado")

        self.usuario_repo.delete(usuario)
        logger.info(f"Usuario {id_usuario} eliminado permanentemente")
        return {"success": True, "message": "Usuario eliminado permanentemente"}

    def create_admin(self, data):
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

        if self.usuario_repo.get_by_email(email):
            logger.warning(f"Intento de crear usuario con email duplicado: {email}")
            raise ValidationError("El email ya está registrado")

        usuario = Usuario(
            nombre=nombre,
            email=email,
            password=hash_password(password),
            rol=rol,
        )
        self.usuario_repo.add(usuario)

        logger.info(f"Nuevo usuario creado por admin: {email} con rol {rol}")
        return {"success": True, "message": f"Usuario creado exitosamente como {rol}"}

    def toggle_estado(self, id_usuario, activo):
        if activo not in ("S", "N"):
            raise ValidationError("Estado inválido. Debe ser 'S' o 'N'")

        usuario = self.usuario_repo.get_by_id(id_usuario)
        if not usuario:
            raise NotFoundError("Usuario no encontrado")

        usuario.activo = activo
        self.usuario_repo.flush()

        estado_texto = "activado" if activo == "S" else "desactivado"
        logger.info(f"Usuario {id_usuario} {estado_texto}")
        return {"success": True, "message": f"Usuario {estado_texto} exitosamente"}
