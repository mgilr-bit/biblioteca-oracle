"""Servicios de gestión de multas por devolución tardía.

Regla: multa fija de TARIFA_MULTA_ATRASO (Q35) generada automáticamente por
PrestamoService cuando la devolución ocurre después de la fecha esperada. Una
multa en PENDIENTE bloquea la creación de nuevos préstamos para el usuario
hasta que un BIBLIOTECARIO la marque como PAGADA o CONDONADA.
"""
from datetime import datetime
from typing import List, Optional

from core.messages import MultaMessages, PrestamoMessages
from models.multa import Multa
from models.prestamo import Prestamo
from repositories.multa_repository import MultaRepository
from schemas.multa import MultaResponse
from services.auditoria_service import AuditoriaService
from services.base import BaseService
from services.exceptions import NotFoundError, ValidationError

TARIFA_MULTA_ATRASO = 35.0


class MultaService(BaseService[Multa]):
    not_found_message = MultaMessages.NOT_FOUND

    def __init__(self, session):
        super().__init__(MultaRepository(session))

    def _serializar(self, row) -> MultaResponse:
        multa = row[0]
        return MultaResponse(
            id_multa=multa.id_multa,
            id_prestamo=multa.id_prestamo,
            id_usuario=multa.id_usuario,
            monto=multa.monto,
            dias_retraso=multa.dias_retraso,
            estado=multa.estado,
            motivo=multa.motivo,
            fecha_generacion=multa.created_at,
            fecha_pago=multa.fecha_pago,
            titulo=row[1],
            nombre_usuario=row[2],
        )

    def get_all(self) -> List[MultaResponse]:
        return [self._serializar(row) for row in self.repository.get_all_with_details()]

    def get_pendientes(self) -> List[MultaResponse]:
        return [self._serializar(row) for row in self.repository.get_pendientes_with_details()]

    def get_by_usuario(self, id_usuario: int) -> List[MultaResponse]:
        return [
            self._serializar(row)
            for row in self.repository.get_by_usuario_with_details(id_usuario)
        ]

    def usuario_tiene_pendientes(self, id_usuario: int) -> bool:
        return self.repository.usuario_tiene_pendientes(id_usuario)

    def generar_por_devolucion_tardia(
        self, prestamo: Prestamo, actor: Optional[str] = None
    ) -> Optional[Multa]:
        """Crea la multa solo si la devolución fue tardía y no hay ya una
        pendiente para ese préstamo (idempotente). Devuelve la multa o None."""
        if not prestamo.fecha_devolucion_esperada:
            return None
        momento_devolucion = prestamo.fecha_devolucion_real or datetime.now()
        dias = (momento_devolucion - prestamo.fecha_devolucion_esperada).days
        if dias <= 0:
            return None
        if self.repository.get_pendiente_by_prestamo(prestamo.id_prestamo):
            return None

        multa = Multa(
            id_prestamo=prestamo.id_prestamo,
            id_usuario=prestamo.id_usuario,
            monto=TARIFA_MULTA_ATRASO,
            dias_retraso=dias,
            estado="PENDIENTE",
            motivo=MultaMessages.MOTIVO_ATRASO.format(dias=dias),
        )
        self.repository.add(multa, actor=actor)
        return multa

    def pagar(self, id_multa: int, actor: str) -> dict:
        multa = self.get_by_id(id_multa)
        if multa.estado != "PENDIENTE":
            raise ValidationError(MultaMessages.NO_PENDIENTE)
        multa.estado = "PAGADA"
        multa.fecha_pago = datetime.now()
        self.repository.mark_updated(multa, actor=actor)
        self.repository.flush()

        AuditoriaService(self.repository.session).registrar(
            "MULTA_PAGADA",
            "Multa",
            email=actor,
            id_recurso=multa.id_multa,
            detalle=f"Multa de Q{multa.monto} del préstamo #{multa.id_prestamo}",
        )
        return {"success": True, "message": MultaMessages.PAGADA_OK}

    def condonar(self, id_multa: int, actor: str) -> dict:
        multa = self.get_by_id(id_multa)
        if multa.estado != "PENDIENTE":
            raise ValidationError(MultaMessages.NO_PENDIENTE)
        multa.estado = "CONDONADA"
        multa.fecha_pago = None
        self.repository.mark_updated(multa, actor=actor)
        self.repository.flush()

        AuditoriaService(self.repository.session).registrar(
            "MULTA_CONDONADA",
            "Multa",
            email=actor,
            id_recurso=multa.id_multa,
            detalle=f"Multa de Q{multa.monto} del préstamo #{multa.id_prestamo}",
        )
        return {"success": True, "message": MultaMessages.CONDONADA_OK}
