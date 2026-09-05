"""Servicios de gestión de préstamos."""
from datetime import datetime, timedelta
from typing import List, Optional

from core.messages import PrestamoMessages
from models.prestamo import Prestamo
from repositories.libro_repository import LibroRepository
from repositories.prestamo_repository import PrestamoRepository
from schemas.prestamo import PrestamoResponse
from services.base import BaseService
from services.ejemplar_service import EjemplarService
from services.exceptions import BusinessRuleError, ValidationError
from services.reserva_service import ReservaService

DIAS_PRESTAMO_DEFAULT = 14


class PrestamoService(BaseService[Prestamo]):
    not_found_message = PrestamoMessages.NOT_FOUND

    def __init__(self, session):
        super().__init__(PrestamoRepository(session))
        self.libro_repo = LibroRepository(session)
        self.ejemplar_service = EjemplarService(session)
        self.reserva_service = ReservaService(session)

    def _calcular_estado(self, prestamo: Prestamo) -> str:
        if (
            prestamo.estado == "ACTIVO"
            and prestamo.fecha_devolucion_esperada
            and prestamo.fecha_devolucion_esperada < datetime.now()
        ):
            return "VENCIDO"
        return prestamo.estado

    def _serializar(self, row) -> PrestamoResponse:
        prestamo = row[0]
        return PrestamoResponse(
            id_prestamo=prestamo.id_prestamo,
            id_libro=prestamo.id_libro,
            id_usuario=prestamo.id_usuario,
            id_ejemplar=prestamo.id_ejemplar,
            codigo_ejemplar=row[4] if len(row) > 4 else None,
            fecha_prestamo=prestamo.fecha_prestamo,
            fecha_devolucion_esperada=prestamo.fecha_devolucion_esperada,
            fecha_devolucion_real=prestamo.fecha_devolucion_real,
            estado=self._calcular_estado(prestamo),
            titulo=row[1],
            autor=row[2],
            nombre_usuario=row[3],
        )

    def get_all(self) -> List[PrestamoResponse]:
        return [self._serializar(row) for row in self.repository.get_all_with_details()]

    def get_activos(self) -> List[PrestamoResponse]:
        return [self._serializar(row) for row in self.repository.get_activos_with_details()]

    def get_by_usuario(self, id_usuario: int) -> List[PrestamoResponse]:
        return [
            self._serializar(row)
            for row in self.repository.get_by_usuario_with_details(id_usuario)
        ]

    def get_vencidos(self) -> List[PrestamoResponse]:
        return [
            self._serializar(row)
            for row in self.repository.get_vencidos_with_details()
        ]

    def create(self, id_libro: int, id_usuario: Optional[int], dias_prestamo, requesting_user) -> dict:
        # SEGURIDAD: un LECTOR solo puede pedir prestado para sí mismo, sin
        # importar qué id_usuario mande en el body (mismo patrón que el rol
        # forzado en AuthService.register).
        if requesting_user.rol != "BIBLIOTECARIO":
            id_usuario = requesting_user.id
        elif not id_usuario:
            raise ValidationError(PrestamoMessages.CAMPOS_REQUERIDOS)

        if not id_libro or not id_usuario:
            raise ValidationError(PrestamoMessages.CAMPOS_REQUERIDOS)

        dias = int(dias_prestamo or DIAS_PRESTAMO_DEFAULT)

        libro = self.libro_repo.get_by_id(id_libro)
        if not libro or libro.copias_disponibles <= 0:
            raise BusinessRuleError(PrestamoMessages.SIN_COPIAS)

        prestamo = Prestamo(
            id_libro=id_libro,
            id_usuario=id_usuario,
            fecha_devolucion_esperada=datetime.now() + timedelta(days=dias),
        )
        self.repository.add(prestamo, actor=requesting_user.email)

        # Fase 2: asocia la copia física disponible al préstamo (si hay ejemplares).
        ejemplar = self.ejemplar_service.asignar_a_prestamo(id_libro)
        if ejemplar:
            prestamo.id_ejemplar = ejemplar.id_ejemplar
            self.repository.flush()

        return {"success": True, "message": "Préstamo creado exitosamente"}

    def devolver(self, id_prestamo: int, actor: str) -> dict:
        prestamo = self.get_by_id(id_prestamo)
        if prestamo.estado == "DEVUELTO":
            raise ValidationError(PrestamoMessages.YA_DEVUELTO)

        prestamo.estado = "DEVUELTO"
        prestamo.fecha_devolucion_real = datetime.now()
        self.repository.mark_updated(prestamo, actor=actor)
        self.repository.flush()

        if prestamo.id_ejemplar:
            self.ejemplar_service.liberar(prestamo.id_ejemplar)

        # Fase 3 (reservas): al volver una copia, la reserva FIFO más antigua
        # pasa a CUMPLIDA y abre su ventana de recogida para el reservante.
        self.reserva_service.promover_siguiente(prestamo.id_libro)

        return {"success": True, "message": "Devolución registrada exitosamente"}
