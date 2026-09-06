"""Servicios de gestión de editoriales."""
from typing import List, Optional

from sqlalchemy import update as sa_update

from core.messages import EditorialMessages
from models.editorial import Editorial
from models.libro import Libro
from repositories.editorial_repository import EditorialRepository
from services.base import BaseService
from services.exceptions import ValidationError

PER_PAGE_DEFAULT = 100
MAX_RESULTADOS = 2000


def _empty_to_null(value) -> Optional[str]:
    if value is None:
        return None
    stripped = str(value).strip()
    return stripped or None


class EditorialService(BaseService[Editorial]):
    not_found_message = EditorialMessages.NOT_FOUND

    def __init__(self, session):
        super().__init__(EditorialRepository(session))

    def get_all(self, page, per_page) -> dict:
        page = max(page or 1, 1)
        per_page = min(max(per_page or PER_PAGE_DEFAULT, 1), MAX_RESULTADOS)
        offset = (page - 1) * per_page
        editoriales = self.repository.get_paginated(offset, per_page)
        total = self.repository.count()
        return {
            "editoriales": editoriales,
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page,
        }

    def get_all_flat(self) -> List[Editorial]:
        return self.repository.get_ordered_by_nombre()

    def create(self, data: dict, actor: str) -> dict:
        nombre = (data.get("nombre") or "").strip()
        if not nombre:
            raise ValidationError(EditorialMessages.NOMBRE_REQUERIDO)
        if self.repository.get_by_nombre(nombre):
            raise ValidationError(EditorialMessages.NOMBRE_DUPLICADO)

        editorial = Editorial(
            nombre=nombre,
            pais=_empty_to_null(data.get("pais")),
            sitio_web=_empty_to_null(data.get("sitio_web")),
        )
        self.repository.add(editorial, actor=actor)

        return {"success": True, "message": "Editorial creada exitosamente"}

    def update(self, id_editorial: int, data: dict, actor: str) -> dict:
        editorial = self.get_by_id(id_editorial)

        nombre = (data.get("nombre") or "").strip()
        if not nombre:
            raise ValidationError(EditorialMessages.NOMBRE_REQUERIDO)
        existing = self.repository.get_by_nombre(nombre)
        if existing and existing.id_editorial != id_editorial:
            raise ValidationError(EditorialMessages.NOMBRE_DUPLICADO)

        editorial.nombre = nombre
        editorial.pais = _empty_to_null(data.get("pais"))
        editorial.sitio_web = _empty_to_null(data.get("sitio_web"))
        self.repository.mark_updated(editorial, actor=actor)
        self.repository.flush()

        return {"success": True, "message": "Editorial actualizada exitosamente"}

    def delete(self, id_editorial: int, actor: str) -> dict:
        # Como el borrado es soft, los libros que la referencian quedarían
        # apuntando a una editorial "eliminada": se desligan (no se borran).
        self.repository.session.execute(
            sa_update(Libro)
            .where(Libro.id_editorial == id_editorial)
            .values(id_editorial=None)
        )
        self.delete_entity(id_editorial, actor=actor)
        return {"success": True, "message": "Editorial eliminada exitosamente"}