"""Excepciones de la capa de servicios con código HTTP asociado."""
from typing import Optional


class ServiceError(Exception):
    """Error de negocio con un código HTTP para devolver al cliente."""

    status_code: int = 400

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        if status_code is not None:
            self.status_code = status_code


class NotFoundError(ServiceError):
    status_code = 404


class ValidationError(ServiceError):
    status_code = 400


class BusinessRuleError(ServiceError):
    status_code = 400


class AuthError(ServiceError):
    status_code = 401
