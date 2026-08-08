"""Servicios de gestión de libros."""
import logging

from models.libro import Libro
from repositories.libro_repository import LibroRepository
from services.exceptions import (
    BusinessRuleError,
    NotFoundError,
    ValidationError,
)
from utils.serializers import to_dict, to_list

logger = logging.getLogger(__name__)

MAX_RESULTADOS = 2000
PER_PAGE_DEFAULT = 100


class LibroService:
    def __init__(self, session):
        self.libro_repo = LibroRepository(session)

    def get_all(self, page, per_page, limit):
        page = max(page or 1, 1)
        per_page = min(max(per_page or PER_PAGE_DEFAULT, 1), MAX_RESULTADOS)

        if limit:
            limit = min(max(limit, 1), MAX_RESULTADOS)
            libros = self.libro_repo.get_first_n(limit)
        else:
            offset = (page - 1) * per_page
            libros = self.libro_repo.get_paginated(offset, per_page)

        total = self.libro_repo.count()
        return {
            "libros": to_list(libros),
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page,
        }

    def get_all_for_export(self):
        return to_list(self.libro_repo.get_ordered_by_titulo())

    def get_by_id(self, id_libro):
        libro = self.libro_repo.get_by_id(id_libro)
        if not libro:
            raise NotFoundError("Libro no encontrado")
        return to_dict(libro)

    def get_generos(self):
        return self.libro_repo.get_generos()

    def search(self, titulo="", autor="", isbn="", genero="", limit=200):
        limit = min(max(limit or 200, 1), MAX_RESULTADOS)
        libros = self.libro_repo.search(
            titulo=titulo, autor=autor, isbn=isbn, genero=genero, limit=limit
        )
        logger.info(f"Búsqueda de libros: {len(libros)} resultados encontrados")
        return to_list(libros)

    def create(self, data):
        titulo = data.get("titulo")
        autor = data.get("autor")
        if not titulo or not autor:
            raise ValidationError("Los campos titulo y autor son requeridos")

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
        self.libro_repo.add(libro)

        return {"success": True, "message": "Libro creado exitosamente"}

    def update(self, id_libro, data):
        libro = self.libro_repo.get_by_id(id_libro)
        if not libro:
            raise NotFoundError("Libro no encontrado")

        titulo = data.get("titulo")
        autor = data.get("autor")
        if not titulo or not autor:
            raise ValidationError("Los campos titulo y autor son requeridos")

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
        self.libro_repo.flush()

        return {
            "success": True,
            "message": f"Libro actualizado exitosamente. Copias disponibles: {nuevas_disponibles}",
        }

    def update_copias(self, id_libro, copias):
        if copias is None:
            raise ValidationError("copias_disponibles es requerido")

        libro = self.libro_repo.get_by_id(id_libro)
        if not libro:
            raise NotFoundError("Libro no encontrado")

        libro.copias_disponibles = int(copias)
        self.libro_repo.flush()

        return {"success": True, "message": "Copias actualizadas exitosamente"}

    def delete(self, id_libro):
        libro = self.libro_repo.get_by_id(id_libro)
        if not libro:
            raise NotFoundError("Libro no encontrado")

        self.libro_repo.delete(libro)
        return {"success": True, "message": "Libro eliminado exitosamente"}

    def get_bajo_stock(self):
        return to_list(self.libro_repo.get_bajo_stock())

    def get_estadisticas(self):
        return self.libro_repo.get_estadisticas()
