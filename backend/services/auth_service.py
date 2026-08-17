"""Servicios de autenticación (login y registro)."""
import logging

from models.usuario import Usuario
from repositories.usuario_repository import UsuarioRepository
from services.exceptions import AuthError, ValidationError
from utils.security import generate_token, hash_password, verify_password

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, session):
        self.usuario_repo = UsuarioRepository(session)

    def login(self, email, password):
        if not email or not password:
            raise ValidationError("Email y contraseña son requeridos")

        usuario = self.usuario_repo.get_by_email(email)
        if (
            not usuario
            or usuario.activo != "S"
            or not verify_password(password, usuario.password)
        ):
            logger.warning(f"Intento de login fallido para email: {email}")
            raise AuthError("Credenciales inválidas")

        token = generate_token(usuario.id_usuario, usuario.email, usuario.rol)
        logger.info(f"Login exitoso para usuario: {email}")

        return {
            "success": True,
            "token": token,
            "user": {
                "id": usuario.id_usuario,
                "nombre": usuario.nombre,
                "email": usuario.email,
                "rol": usuario.rol,
            },
            "message": "Login exitoso",
        }

    def register(self, nombre, email, password):
        if not nombre or not email or not password:
            raise ValidationError("Nombre, email y contraseña son requeridos")
        if len(password) < 6:
            raise ValidationError("La contraseña debe tener al menos 6 caracteres")

        if self.usuario_repo.get_by_email(email):
            logger.warning(f"Intento de registro con email duplicado: {email}")
            raise ValidationError("El email ya está registrado")

        # SEGURIDAD: el rol siempre es LECTOR (se ignora cualquier rol enviado)
        usuario = Usuario(
            nombre=nombre,
            email=email,
            password=hash_password(password),
            rol="LECTOR",
        )
        self.usuario_repo.add(usuario)

        logger.info(f"Nuevo usuario registrado: {email}")
        return {"success": True, "message": "Usuario registrado exitosamente"}
