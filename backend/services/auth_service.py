"""Servicio de autenticación (login). La emisión de la sesión (cookies)
queda a cargo del router: este servicio solo valida credenciales y
devuelve la entidad de usuario.

No existe alta pública de cuentas: el sistema es de uso interno de la
biblioteca universitaria y las cuentas las crea un BIBLIOTECARIO/ADMIN
desde `UsuarioService.create_admin`."""
import logging

from core.messages import AuthMessages
from models.usuario import Usuario
from repositories.usuario_repository import UsuarioRepository
from services.auditoria_service import AuditoriaService
from services.exceptions import AuthError, ValidationError
from utils.security import verify_password

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
            AuditoriaService(self.usuario_repo.session).registrar(
                "LOGIN_FALLIDO", "Auth", email=email
            )
            raise AuthError(AuthMessages.CREDENCIALES_INVALIDAS)

        AuditoriaService(self.usuario_repo.session).registrar(
            "LOGIN",
            "Auth",
            id_usuario=usuario.id_usuario,
            email=usuario.email,
            rol=usuario.rol,
        )
        logger.info(f"Login exitoso para usuario: {email}")
        return usuario
