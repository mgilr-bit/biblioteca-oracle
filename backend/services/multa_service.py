"""Servicios de gestión de multas por devolución tardía.

Regla: multa fija de TARIFA_MULTA_ATRASO (Q35), una por préstamo, generada
automáticamente en cuanto el préstamo pasa su fecha límite sin devolverse
(job de mantenimiento) o al registrar una devolución tardía. Una
multa en PENDIENTE bloquea la creación de nuevos préstamos para el usuario
hasta que un BIBLIOTECARIO la marque como PAGADA.
"""
import math
from typing import List, Optional

from core.messages import MultaMessages, NotificacionMessages, PrestamoMessages
from core.zona_horaria import ahora_utc
from models.libro import Libro
from models.multa import Multa
from models.prestamo import Prestamo
from models.usuario import Usuario
from repositories.multa_repository import MultaRepository
from schemas.multa import MultaResponse
from services import avisos
from services.auditoria_service import AuditoriaService
from services.base import BaseService
from services.exceptions import NotFoundError, ValidationError

TARIFA_MULTA_ATRASO = 35.0


def dias_de_retraso(esperada, momento) -> int:
    """Días de atraso redondeados hacia arriba: pasarse unas horas cuenta 1."""
    segundos = (momento - esperada).total_seconds()
    return max(1, math.ceil(segundos / 86400))


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

    def generar_por_atraso(self, prestamo: Prestamo, actor: Optional[str] = None) -> Optional[Multa]:
        """Genera la multa en cuanto el préstamo pasa su fecha límite sin
        devolverse (job de mantenimiento) o, si el job aún no pasó, al
        registrar la devolución tardía. Una sola multa por préstamo
        (idempotente). Avisa al usuario y al personal. Devuelve la multa
        nueva o None."""
        if not prestamo.fecha_devolucion_esperada:
            return None
        momento = prestamo.fecha_devolucion_real or ahora_utc()
        if momento <= prestamo.fecha_devolucion_esperada:
            return None
        if self.repository.get_by_prestamo(prestamo.id_prestamo):
            return None

        multa = Multa(
            id_prestamo=prestamo.id_prestamo,
            id_usuario=prestamo.id_usuario,
            monto=TARIFA_MULTA_ATRASO,
            dias_retraso=dias_de_retraso(prestamo.fecha_devolucion_esperada, momento),
            estado="PENDIENTE",
            motivo=MultaMessages.MOTIVO_VENCIDO.format(fecha=avisos.fecha(prestamo.fecha_devolucion_esperada)),
        )
        self.repository.add(multa, actor=actor)

        session = self.repository.session
        libro = session.get(Libro, prestamo.id_libro)
        usuario = session.get(Usuario, prestamo.id_usuario)
        datos = {
            "titulo": libro.titulo if libro else f"#{prestamo.id_libro}",
            "nombre": usuario.nombre if usuario else f"Usuario #{prestamo.id_usuario}",
            "fecha": avisos.fecha(prestamo.fecha_devolucion_esperada),
            "monto": f"{TARIFA_MULTA_ATRASO:.2f}",
        }
        avisos.avisar_usuario(session, prestamo.id_usuario, "MULTA", NotificacionMessages.MULTA_GENERADA.format(**datos))
        avisos.avisar_personal(session, "MULTA", NotificacionMessages.PERSONAL_MULTA.format(**datos))

        AuditoriaService(session).registrar(
            "MULTA_GENERADA",
            "Multa",
            email=actor,
            id_recurso=multa.id_multa,
            detalle=f"Prestamo #{prestamo.id_prestamo} vencido sin devolver, Q{multa.monto}",
        )
        return multa

    def cerrar_atraso(self, prestamo: Prestamo, actor: Optional[str] = None) -> Optional[Multa]:
        """Al devolver tarde, deja en la multa pendiente los días reales de
        retraso. Devuelve esa multa (o None si no hay una pendiente)."""
        multa = self.repository.get_pendiente_by_prestamo(prestamo.id_prestamo)
        if multa and prestamo.fecha_devolucion_real and prestamo.fecha_devolucion_esperada:
            multa.dias_retraso = dias_de_retraso(prestamo.fecha_devolucion_esperada, prestamo.fecha_devolucion_real)
            multa.motivo = MultaMessages.MOTIVO_ATRASO.format(dias=multa.dias_retraso)
            self.repository.mark_updated(multa, actor=actor)
            self.repository.flush()
        return multa

    def pagar(self, id_multa: int, actor: str) -> dict:
        multa = self.get_by_id(id_multa)
        if multa.estado != "PENDIENTE":
            raise ValidationError(MultaMessages.NO_PENDIENTE)
        multa.estado = "PAGADA"
        multa.fecha_pago = ahora_utc()
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
