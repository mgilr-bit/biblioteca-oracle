"""Servicios de gestión de libros.

Devuelven entidades SQLModel (o listas de ellas); el mapeo a DTO de
respuesta lo hace el router vía `response_model`.
"""
import logging
from typing import List

from core.messages import LibroMessages
from models.libro import Libro
from repositories.libro_repository import LibroRepository
from services.base import BaseService
from services.exceptions import BusinessRuleError, ValidationError

logger = logging.getLogger(__name__)

MAX_RESULTADOS = 2000
PER_PAGE_DEFAULT = 100


class LibroService(BaseService[Libro]):
    not_found_message = LibroMessages.NOT_FOUND

    def __init__(self, session):
        super().__init__(LibroRepository(session))

    def get_all(self, page, per_page, limit) -> dict:
        page = max(page or 1, 1)
        per_page = min(max(per_page or PER_PAGE_DEFAULT, 1), MAX_RESULTADOS)

        if limit:
            limit = min(max(limit, 1), MAX_RESULTADOS)
            libros = self.repository.get_first_n(limit)
        else:
            offset = (page - 1) * per_page
            libros = self.repository.get_paginated(offset, per_page)

        total = self.repository.count()
        return {
            "libros": libros,
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page,
        }

    def get_all_for_export(self) -> List[Libro]:
        return self.repository.get_ordered_by_titulo()

    def get_generos(self) -> List[str]:
        return self.repository.get_generos()

    def search(self, titulo="", autor="", isbn="", genero="", limit=200) -> List[Libro]:
        limit = min(max(limit or 200, 1), MAX_RESULTADOS)
        libros = self.repository.search(
            titulo=titulo, autor=autor, isbn=isbn, genero=genero, limit=limit
        )
        logger.info(f"Búsqueda de libros: {len(libros)} resultados encontrados")
        return libros

    def create(self, data: dict, actor: str) -> dict:
        titulo = data.get("titulo")
        autor = data.get("autor")
        if not titulo or not autor:
            raise ValidationError(LibroMessages.CAMPOS_REQUERIDOS)

        numero_copias = int(data.get("numero_copias", 1) or 1)
        libro = Libro(
            titulo=titulo,
            autor=autor,
            isbn=data.get("isbn"),
            anio_publicacion=data.get("anio_publicacion"),
            genero=data.get("genero"),
            numero_copias=numero_copias,
            copias_disponibles=numero_copias,
            editorial=data.get("editorial"),
        )
        self.repository.add(libro, actor=actor)

        return {"success": True, "message": "Libro creado exitosamente"}

    def update(self, id_libro: int, data: dict, actor: str) -> dict:
        libro = self.get_by_id(id_libro)

        titulo = data.get("titulo")
        autor = data.get("autor")
        if not titulo or not autor:
            raise ValidationError(LibroMessages.CAMPOS_REQUERIDOS)

        nuevas_copias = int(data.get("numero_copias", libro.numero_copias) or libro.numero_copias)
        diferencia = nuevas_copias - libro.numero_copias
        nuevas_disponibles = libro.copias_disponibles + diferencia

        if nuevas_disponibles < 0:
            raise BusinessRuleError(
                f"No se puede reducir a {nuevas_copias} copias. "
                f"Hay {libro.numero_copias - libro.copias_disponibles} copias prestadas."
            )

        libro.titulo = titulo
        libro.autor = autor
        libro.isbn = data.get("isbn")
        libro.anio_publicacion = data.get("anio_publicacion")
        libro.genero = data.get("genero")
        libro.numero_copias = nuevas_copias
        libro.copias_disponibles = nuevas_disponibles
        libro.editorial = data.get("editorial")
        self.repository.mark_updated(libro, actor=actor)
        self.repository.flush()

        return {
            "success": True,
            "message": f"Libro actualizado exitosamente. Copias disponibles: {nuevas_disponibles}",
        }

    def update_copias(self, id_libro: int, copias, actor: str) -> dict:
        if copias is None:
            raise ValidationError(LibroMessages.COPIAS_REQUERIDO)

        libro = self.get_by_id(id_libro)
        libro.copias_disponibles = int(copias)
        self.repository.mark_updated(libro, actor=actor)
        self.repository.flush()

        return {"success": True, "message": "Copias actualizadas exitosamente"}

    def delete(self, id_libro: int, actor: str) -> dict:
        self.delete_entity(id_libro, actor=actor)
        return {"success": True, "message": "Libro eliminado exitosamente"}

    def get_bajo_stock(self) -> List[Libro]:
        return self.repository.get_bajo_stock()

    def get_estadisticas(self) -> dict:
        return self.repository.get_estadisticas()
