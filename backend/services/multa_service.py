"""Servicios de gestión de multas por devolución tardía.

Una multa nace únicamente en `PrestamoService.devolver`, cuando la fecha
real de devolución es posterior a la esperada. El monto es fijo
(`TARIFA_MULTA_ATRASO`, Q35) independientemente de los días de retraso.
El bibliotecario luego la marca como PAGADA o CONDONADA; mientras siga
PENDIENTE, el usuario no puede pedir nuevos préstamos.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from core.messages import MultaMessages
from models.multa import Multa
from models.prestamo import Prestamo
from repositories.multa_repository import MultaRepository
from schemas.multa import MultaResponse
from services.base import BaseService
from services.exceptions import ValidationError

#: Sanción fija (GTQ) por devolver un préstamo después de la fecha esperada.
TARIFA_MULTA_ATRASO = Decimal("35.00")


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
        return self.repository.count_pendientes_by_usuario(id_usuario) > 0

    def generar_por_devolucion_tardia(self, prestamo: Prestamo, actor: str) -> Optional[Multa]:
        """Crea (una sola vez por préstamo) la multa fija de Q35 si el préstamo
        se devolvió después de la fecha esperada. Devuelve la multa creada, o
        None si no correspondía."""
        esperada = prestamo.fecha_devolucion_esperada
        real = prestamo.fecha_devolucion_real or datetime.now()
        if not esperada or real.date() <= esperada.date():
            return None
        if self.repository.exists_for_prestamo(prestamo.id_prestamo):
            return None

        dias_retraso = (real.date() - esperada.date()).days
        multa = Multa(
            id_prestamo=prestamo.id_prestamo,
            id_usuario=prestamo.id_usuario,
            monto=TARIFA_MULTA_ATRASO,
            dias_retraso=dias_retraso,
            estado="PENDIENTE",
            motivo=MultaMessages.MOTIVO_ATRASO.format(dias=dias_retraso),
        )
        self.repository.add(multa, actor=actor)
        return multa

    def pagar(self, id_multa: int, actor: str) -> dict:
        return self._cambiar_estado(id_multa, "PAGADA", actor, MultaMessages.PAGADA_OK, con_fecha_pago=True)

    def condonar(self, id_multa: int, actor: str) -> dict:
        return self._cambiar_estado(id_multa, "CONDONADA", actor, MultaMessages.CONDONADA_OK)

    def _cambiar_estado(
        self, id_multa: int, nuevo_estado: str, actor: str, mensaje: str, con_fecha_pago: bool = False
    ) -> dict:
        multa = self.get_by_id(id_multa)
        if multa.estado != "PENDIENTE":
            raise ValidationError(MultaMessages.NO_PENDIENTE)

        multa.estado = nuevo_estado
        if con_fecha_pago:
            multa.fecha_pago = datetime.now()
        self.repository.mark_updated(multa, actor=actor)
        self.repository.flush()

        return {"success": True, "message": mensaje}
