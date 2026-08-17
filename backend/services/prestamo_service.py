"""Servicios de gestión de préstamos."""
from datetime import datetime, timedelta
from typing import Optional

from models.prestamo import Prestamo
from repositories.libro_repository import LibroRepository
from repositories.prestamo_repository import PrestamoRepository
from services.exceptions import (
    BusinessRuleError,
    NotFoundError,
    ValidationError,
)

DIAS_PRESTAMO_DEFAULT = 14


def _iso(value: Optional[datetime]):
    return value.isoformat() if value else None


class PrestamoService:
    def __init__(self, session):
        self.prestamo_repo = PrestamoRepository(session)
        self.libro_repo = LibroRepository(session)

    def _calcular_estado(self, prestamo):
        if (
            prestamo.estado == "ACTIVO"
            and prestamo.fecha_devolucion_esperada
            and prestamo.fecha_devolucion_esperada < datetime.now()
        ):
            return "VENCIDO"
        return prestamo.estado

    def _serializar(self, row):
        prestamo = row[0]
        data = {
            "id_prestamo": prestamo.id_prestamo,
            "id_libro": prestamo.id_libro,
            "id_usuario": prestamo.id_usuario,
            "fecha_prestamo": _iso(prestamo.fecha_prestamo),
            "fecha_devolucion_esperada": _iso(prestamo.fecha_devolucion_esperada),
            "fecha_devolucion_real": _iso(prestamo.fecha_devolucion_real),
            "estado": self._calcular_estado(prestamo),
            "titulo": row[1],
            "autor": row[2],
            "nombre_usuario": row[3],
        }
        return {key.upper(): value for key, value in data.items()}

    def get_all(self):
        return [self._serializar(row) for row in self.prestamo_repo.get_all_with_details()]

    def get_activos(self):
        return [self._serializar(row) for row in self.prestamo_repo.get_activos_with_details()]

    def get_by_usuario(self, id_usuario):
        return [
            self._serializar(row)
            for row in self.prestamo_repo.get_by_usuario_with_details(id_usuario)
        ]

    def get_vencidos(self):
        return [
            self._serializar(row)
            for row in self.prestamo_repo.get_vencidos_with_details()
        ]

    def create(self, id_libro, id_usuario, dias_prestamo):
        if not id_libro or not id_usuario:
            raise ValidationError("id_libro e id_usuario son requeridos")

        dias = int(dias_prestamo or DIAS_PRESTAMO_DEFAULT)

        libro = self.libro_repo.get_by_id(id_libro)
        if not libro or libro.copias_disponibles <= 0:
            raise BusinessRuleError("No hay copias disponibles")

        prestamo = Prestamo(
            id_libro=id_libro,
            id_usuario=id_usuario,
            fecha_devolucion_esperada=datetime.now() + timedelta(days=dias),
        )
        self.prestamo_repo.add(prestamo)

        return {"success": True, "message": "Préstamo creado exitosamente"}

    def devolver(self, id_prestamo):
        prestamo = self.prestamo_repo.get_by_id(id_prestamo)
        if not prestamo or prestamo.estado == "DEVUELTO":
            raise NotFoundError("Préstamo no encontrado o ya devuelto")

        prestamo.estado = "DEVUELTO"
        prestamo.fecha_devolucion_real = datetime.now()
        self.prestamo_repo.flush()

        return {"success": True, "message": "Devolución registrada exitosamente"}
