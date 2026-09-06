"""Servicios de gestión de ejemplares (copias físicas).

Estados posibles (decisión de producto del plan de fases):
DISPONIBLE, PRESTADO, RESERVADO, DANADO, REPARACION, BAJA, DEVUELTO.

PRESTADO/RESERVADO/DISPONIBLE se mueven de forma automática cuando el
módulo de préstamos presta/devuelve/libera (ver PrestamoService); el resto
de estados (DANADO, REPARACION, BAJA, ...) los gestiona el bibliotecario.
"""
from datetime import datetime
from typing import List, Optional

from core.messages import EjemplarMessages
from models.ejemplar import Ejemplar
from models.libro import Libro
from repositories.ejemplar_repository import EjemplarRepository
from repositories.libro_repository import LibroRepository
from services.auditoria_service import AuditoriaService
from services.base import BaseService
from services.exceptions import BusinessRuleError, ValidationError

EJEMPLAR_ESTADOS = (
    "DISPONIBLE",
    "PRESTADO",
    "RESERVADO",
    "DANADO",
    "REPARACION",
    "BAJA",
    "DEVUELTO",
)

PER_PAGE_DEFAULT = 100
MAX_RESULTADOS = 2000


class EjemplarService(BaseService[Ejemplar]):
    not_found_message = EjemplarMessages.NOT_FOUND

    def __init__(self, session):
        super().__init__(EjemplarRepository(session))
        self.libro_repo = LibroRepository(session)

    def _serializar(self, row) -> dict:
        ejemplar = row[0]
        return self.serializar_ejemplar(ejemplar, row[1])

    def serializar_ejemplar(self, ejemplar: Ejemplar, titulo: str) -> dict:
        return {
            "id_ejemplar": ejemplar.id_ejemplar,
            "id_libro": ejemplar.id_libro,
            "codigo_ejemplar": ejemplar.codigo_ejemplar,
            "estado": ejemplar.estado,
            "ubicacion": ejemplar.ubicacion,
            "fecha_adquisicion": ejemplar.fecha_adquisicion,
            "titulo": titulo,
        }

    def get_all(self, page, per_page, id_libro, estado) -> dict:
        page = max(page or 1, 1)
        per_page = min(max(per_page or PER_PAGE_DEFAULT, 1), MAX_RESULTADOS)
        offset = (page - 1) * per_page
        ejemplares = self.repository.get_paginated_with_details(
            offset, per_page, id_libro=id_libro, estado=estado
        )
        total = self.repository.count(id_libro=id_libro, estado=estado)
        return {
            "ejemplares": [self._serializar(row) for row in ejemplares],
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page,
        }

    def get_by_libro(self, id_libro: int) -> List[dict]:
        rows = [
            self.serializar_ejemplar(ejemplar, self._titulo_de(ejemplar.id_libro))
            for ejemplar in self.repository.get_by_libro(id_libro)
        ]
        return rows

    def _titulo_de(self, id_libro: int) -> str:
        libro = self.libro_repo.get_by_id(id_libro)
        return libro.titulo if libro else ""

    def get_estados(self) -> List[str]:
        return list(EJEMPLAR_ESTADOS)

    def create(self, data: dict, actor: str) -> dict:
        id_libro = data.get("id_libro")
        if not id_libro:
            raise ValidationError(EjemplarMessages.ID_LIBRO_REQUERIDO)

        libro = self.libro_repo.get_by_id(id_libro)
        if not libro:
            raise ValidationError(EjemplarMessages.LIBRO_NO_EXISTE)

        codigo = (data.get("codigo_ejemplar") or "").strip()
        if not codigo:
            codigo = self._proximo_codigo(id_libro)

        if self.repository.get_by_codigo(codigo):
            raise ValidationError(EjemplarMessages.CODIGO_DUPLICADO)

        ejemplar = Ejemplar(
            id_libro=id_libro,
            codigo_ejemplar=codigo,
            estado="DISPONIBLE",
            ubicacion=_empty_to_null(data.get("ubicacion")),
            fecha_adquisicion=data.get("fecha_adquisicion"),
        )
        self.repository.add(ejemplar, actor=actor)
        libro.copias_disponibles = self.repository.count_estado(id_libro, "DISPONIBLE")
        self.libro_repo.mark_updated(libro, actor=actor)
        self.libro_repo.flush()

        AuditoriaService(self.repository.session).registrar(
            "EJEMPLAR_CREADO",
            "Ejemplar",
            email=actor,
            id_recurso=ejemplar.id_ejemplar,
            detalle=f"Código {codigo} para el libro #{id_libro}",
        )

        return {"success": True, "message": "Ejemplar creado exitosamente"}

    def _proximo_codigo(self, id_libro: int) -> str:
        existentes = self.repository.get_by_libro(id_libro)
        numero = len(existentes) + 1
        return f"L-{id_libro}-{numero}"

    def update(self, id_ejemplar: int, data: dict, actor: str) -> dict:
        ejemplar = self.get_by_id(id_ejemplar)
        ejemplar.ubicacion = _empty_to_null(data.get("ubicacion"))
        ejemplar.fecha_adquisicion = data.get("fecha_adquisicion")
        self.repository.mark_updated(ejemplar, actor=actor)
        self.repository.flush()
        return {"success": True, "message": "Ejemplar actualizado exitosamente"}

    def change_estado(self, id_ejemplar: int, nuevo_estado: str, actor: str) -> dict:
        ejemplar = self.get_by_id(id_ejemplar)
        estado = (nuevo_estado or "").upper().strip()
        if estado not in EJEMPLAR_ESTADOS:
            raise ValidationError(EjemplarMessages.ESTADO_INVALIDO.format(estados=", ".join(EJEMPLAR_ESTADOS)))

        # Un prestamo en curso protege la copia: marco el ejemplar con su estado
        # solo si no está prestado (la liberación la hace la devolución).
        if ejemplar.estado == "PRESTADO" and estado != "PRESTADO":
            raise BusinessRuleError(EjemplarMessages.NO_CAMBIAR_PRESTADO)

        ejemplar.estado = estado
        self.repository.mark_updated(ejemplar, actor=actor)
        self.repository.flush()

        AuditoriaService(self.repository.session).registrar(
            "EJEMPLAR_ESTADO",
            "Ejemplar",
            email=actor,
            id_recurso=ejemplar.id_ejemplar,
            detalle=f"Código {ejemplar.codigo_ejemplar}: {estado}",
        )
        return {"success": True, "message": f"Estado del ejemplar cambiado a {estado}"}

    def delete(self, id_ejemplar: int, actor: str) -> dict:
        ejemplar = self.get_by_id(id_ejemplar)
        if ejemplar.estado == "PRESTADO":
            raise BusinessRuleError(EjemplarMessages.NO_BORRAR_PRESTADO)

        self.delete_entity(id_ejemplar, actor=actor)
        # Recalcula disponibilidad real del libro tras el borrado.
        libro = self.libro_repo.get_by_id(ejemplar.id_libro)
        if libro:
            libro.copias_disponibles = self.repository.count_estado(ejemplar.id_libro, "DISPONIBLE")
            self.libro_repo.mark_updated(libro, actor=actor)
            self.libro_repo.flush()
        return {"success": True, "message": "Ejemplar eliminado exitosamente"}

    # --- Sincronización con el módulo de préstamos (usado por PrestamoService) ---

    def asignar_a_prestamo(self, id_libro: int) -> Optional[Ejemplar]:
        """Devuelve la primera copia DISPONIBLE y la marca PRESTADA, o None."""
        ejemplar = self.repository.get_primer_disponible(id_libro)
        if ejemplar:
            ejemplar.estado = "PRESTADO"
            self.repository.mark_updated(ejemplar, actor="prestamo")
            self.repository.flush()
        return ejemplar

    def liberar(self, id_ejemplar: int) -> None:
        ejemplar = self.session_get(id_ejemplar)
        if ejemplar and ejemplar.estado == "PRESTADO":
            ejemplar.estado = "DISPONIBLE"
            self.repository.mark_updated(ejemplar, actor="prestamo")
            self.repository.flush()

    def session_get(self, pk: int) -> Optional[Ejemplar]:
        return self.repository.get_by_id(pk)


def _empty_to_null(value) -> Optional[str]:
    if value is None:
        return None
    stripped = str(value).strip()
    return stripped or None