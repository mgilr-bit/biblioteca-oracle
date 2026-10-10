"""Servicios de gestión de editoriales."""
import logging

from core.messages import EditorialMessages
from models.editorial import Editorial
from repositories.editorial_repository import EditorialRepository
from services.base import BaseService
from services.exceptions import BusinessRuleError, ValidationError

logger = logging.getLogger(__name__)


class EditorialService(BaseService[Editorial]):
    not_found_message = EditorialMessages.NOT_FOUND

    def __init__(self, session):
        super().__init__(EditorialRepository(session))

    def _validar_nombre(self, nombre, exclude_id=None) -> str:
        nombre = (nombre or "").strip()
        if not nombre:
            raise ValidationError(EditorialMessages.NOMBRE_REQUERIDO)
        existente = self.repository.get_by_nombre(nombre)
        if existente and existente.id_editorial != exclude_id:
            raise ValidationError(EditorialMessages.NOMBRE_DUPLICADO)
        return nombre

    def create(self, data: dict, actor: str) -> dict:
        nombre = self._validar_nombre(data.get("nombre"))
        self.repository.add(Editorial(nombre=nombre), actor=actor)
        logger.info(f"Editorial '{nombre}' creada por {actor}")
        return {"success": True, "message": "Editorial creada exitosamente"}

    def update(self, id_editorial: int, data: dict, actor: str) -> dict:
        editorial = self.get_by_id(id_editorial)
        editorial.nombre = self._validar_nombre(data.get("nombre"), exclude_id=id_editorial)
        self.repository.mark_updated(editorial, actor=actor)
        self.repository.flush()
        return {"success": True, "message": "Editorial actualizada exitosamente"}

    def delete(self, id_editorial: int, actor: str) -> dict:
        if self.repository.count_libros(id_editorial) > 0:
            raise BusinessRuleError(EditorialMessages.TIENE_LIBROS)
        self.delete_entity(id_editorial, actor=actor)
        return {"success": True, "message": "Editorial eliminada exitosamente"}
