"""Servicios de reservas con cola FIFO y cupos simultáneos.

Reglas de producto (plan de fases):
* Un usuario puede tener a lo sumo `MAX_ACTIVAS_POR_USUARIO` reservas ACTIVA.
* No puede reservar dos veces el mismo libro estando ACTIVA.
* La cola es FIFO: cuando vuelve una copia (ver PrestamoService.devolver),
  `promover_siguiente` marca CUMPLIDA la reserva más antigua y deja una
  ventana (`DIAS_VALIDEZ`) para que el usuario la recoja; si no, el job de
  vencidos (fase 4) la expira.
* Un LECTOR/PROFESOR solo puede cancelar sus propias reservas (ABAC por
  dueño en el router); el bibliotecario gestiona cualquiera.
"""
from datetime import datetime, timedelta
from typing import List, Optional

from core.messages import ReservaMessages
from models.reserva import Reserva
from repositories.libro_repository import LibroRepository
from repositories.reserva_repository import ReservaRepository
from schemas.reserva import ReservaResponse
from services.base import BaseService
from services.exceptions import BusinessRuleError, ValidationError

MAX_ACTIVAS_POR_USUARIO = 3
DIAS_VALIDEZ = 3  # ventana de recogida una vez la reserva pasa a CUMPLIDA


class ReservaService(BaseService[Reserva]):
    not_found_message = ReservaMessages.NOT_FOUND

    def __init__(self, session):
        super().__init__(ReservaRepository(session))
        self.libro_repo = LibroRepository(session)

    def _serializar(self, row) -> ReservaResponse:
        reserva = row[0]
        return ReservaResponse(
            id_reserva=reserva.id_reserva,
            id_libro=reserva.id_libro,
            id_usuario=reserva.id_usuario,
            fecha_reserva=reserva.fecha_reserva,
            estado=reserva.estado,
            fecha_expiracion=reserva.fecha_expiracion,
            titulo=row[1],
            autor=row[2],
            nombre_usuario=row[3],
        )

    def get_all(self) -> List[ReservaResponse]:
        return [self._serializar(row) for row in self.repository.get_all_with_details()]

    def get_by_usuario(self, id_usuario: int) -> List[ReservaResponse]:
        return [
            self._serializar(row)
            for row in self.repository.get_by_usuario_with_details(id_usuario)
        ]

    def get_cola(self, id_libro: int) -> List[dict]:
        return [
            {"id_reserva": r.id_reserva, "id_usuario": r.id_usuario, "fecha_reserva": r.fecha_reserva}
            for r in self.repository.get_activas_fifo(id_libro)
        ]

    def create(self, id_libro: int, id_usuario: Optional[int], requesting_user) -> dict:
        # SEGURIDAD: un LECTOR/PROFESOR solo reserva para sí mismo (patrón del
        # módulo de préstamos); el bibliotecario puede reservar a nombre de otro.
        if requesting_user.rol != "BIBLIOTECARIO":
            id_usuario = requesting_user.id
        elif not id_usuario:
            raise ValidationError(ReservaMessages.ID_USUARIO_REQUERIDO)

        if not id_libro or not id_usuario:
            raise ValidationError(ReservaMessages.CAMPOS_REQUERIDOS)

        libro = self.libro_repo.get_by_id(id_libro)
        if not libro:
            raise ValidationError(ReservaMessages.LIBRO_NO_EXISTE)

        if self.repository.count_activas_por_usuario(id_usuario) >= MAX_ACTIVAS_POR_USUARIO:
            raise BusinessRuleError(
                ReservaMessages.MAX_RESERVAS.format(max=MAX_ACTIVAS_POR_USUARIO)
            )

        if self.repository.existe_activa(id_libro, id_usuario):
            raise ValidationError(ReservaMessages.RESERVA_DUPLICADA)

        reserva = Reserva(
            id_libro=id_libro,
            id_usuario=id_usuario,
            estado="ACTIVA",
            fecha_expiracion=None,
        )
        self.repository.add(reserva, actor=requesting_user.email)

        return {"success": True, "message": "Reserva creada exitosamente"}

    def cancelar(self, id_reserva: int, requesting_user) -> dict:
        reserva = self.get_by_id(id_reserva)
        if reserva.estado != "ACTIVA":
            raise ValidationError(ReservaMessages.NO_CANCELABLE)

        reserva.estado = "CANCELADA"
        self.repository.mark_updated(reserva, actor=requesting_user.email)
        self.repository.flush()
        return {"success": True, "message": "Reserva cancelada exitosamente"}

    def promover_siguiente(self, id_libro: int) -> Optional[Reserva]:
        """Marcas CUMPLIDA la reserva más antigua (FIFO) del libro y abre su
        ventana de recogida. Devuelve la reserva o None si no hay cola."""
        fila = self.repository.get_activas_fifo(id_libro)
        if not fila:
            return None
        reserva = fila[0]
        reserva.estado = "CUMPLIDA"
        reserva.fecha_expiracion = datetime.now() + timedelta(days=DIAS_VALIDEZ)
        self.repository.mark_updated(reserva, actor="prestamo")
        self.repository.flush()
        return reserva