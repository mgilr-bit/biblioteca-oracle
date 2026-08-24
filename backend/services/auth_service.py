"""Servicios de autenticación (login y registro). La emisión de la sesión
(cookies) queda a cargo del router: este servicio solo valida credenciales
y devuelve la entidad de usuario."""
import logging

from core.messages import AuthMessages, UsuarioMessages
from models.usuario import Usuario
from repositories.usuario_repository import UsuarioRepository
from services.exceptions import AuthError, ValidationError
from utils.security import hash_password, verify_password

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, session):
        self.usuario_repo = UsuarioRepository(session)

    def login(self, email, password) -> Usuario:
        if not email or not password:
            raise ValidationError(AuthMessages.EMAIL_PASSWORD_REQUERIDOS)

        usuario = self.usuario_repo.get_by_email(email)
        if (
            not usuario
            or usuario.is_deleted
            or usuario.activo != "S"
            or not verify_password(password, usuario.password)
        ):
            logger.warning(f"Intento de login fallido para email: {email}")
            raise AuthError(AuthMessages.CREDENCIALES_INVALIDAS)

        logger.info(f"Login exitoso para usuario: {email}")
        return usuario

    def register(self, nombre, email, password):
        if not nombre or not email or not password:
            raise ValidationError(UsuarioMessages.REGISTRO_CAMPOS_REQUERIDOS)
        if len(password) < 8:
            # NIST SP 800-63B 5.1.1.2: mínimo 8 caracteres, sin reglas de
            # complejidad forzada.
            raise ValidationError(UsuarioMessages.PASSWORD_MUY_CORTA)
        if len(password.encode("utf-8")) > 72:
            # bcrypt trunca silenciosamente a 72 bytes; mejor rechazar
            # explícito que aceptar una contraseña cuya cola nunca se valida.
            raise ValidationError(UsuarioMessages.PASSWORD_MUY_LARGA)

        if self.usuario_repo.get_by_email(email):
            logger.warning(f"Intento de registro con email duplicado: {email}")
            raise ValidationError(UsuarioMessages.EMAIL_DUPLICADO)

        # SEGURIDAD: el rol siempre es LECTOR (se ignora cualquier rol enviado)
        usuario = Usuario(
            nombre=nombre,
            email=email,
            password=hash_password(password),
            rol="LECTOR",
        )
        self.usuario_repo.add(usuario, actor=email)

        logger.info(f"Nuevo usuario registrado: {email}")
        return {"success": True, "message": "Usuario registrado exitosamente"}
