"""Servicios de notificaciones + job de mantenimiento periódico.

`ejecutar_mantenimiento` es la base del "cron" del plan (fase 4): respalda
además por el job DBMS_SCHEDULER de `database/09_cron_jobs.sql`, pero al
vivir en el backend puede dispararse bajo demanda por un ADMIN y es
idempotente (no duplica recordatorios/avisos). Genera:

* Recordatorios de devolución (3 días antes y el mismo día).
* Avisos de vencimiento (préstamos ACTIVO ya vencidos).
* Expiración de reservas CUMPLIDA cuya ventana venció.
"""
from datetime import datetime, timedelta
from typing import List

from core.messages import NotificacionMessages
from models.notificacion import Notificacion
from repositories.notificacion_repository import NotificacionRepository
from repositories.prestamo_repository import PrestamoRepository
from repositories.reserva_repository import ReservaRepository
from schemas.notificacion import NotificacionResponse
from services.base import BaseService

RECORDATORIO_DIAS = 3


class NotificacionService(BaseService[Notificacion]):
    not_found_message = NotificacionMessages.NOT_FOUND

    def __init__(self, session):
        super().__init__(NotificacionRepository(session))
        self.prestamo_repo = PrestamoRepository(session)
        self.reserva_repo = ReservaRepository(session)

    def get_mis_notificaciones(self, id_usuario: int, limit: int = 200) -> List[NotificacionResponse]:
        return [
            NotificacionResponse.model_validate(n)
            for n in self.repository.get_by_usuario(id_usuario, limit)
        ]

    def get_no_leidas_count(self, id_usuario: int) -> int:
        return self.repository.get_no_leidas_count(id_usuario)

    def marcar_leida(self, id_notificacion: int, actor: str) -> dict:
        notificacion = self.get_by_id(id_notificacion)
        if not notificacion.leida:
            notificacion.leida = True
            self.repository.mark_updated(notificacion, actor=actor)
            self.repository.flush()
        return {"success": True, "message": "Notificación marcada como leída"}

    def marcar_todas_leidas(self, id_usuario: int, actor: str) -> dict:
        for notificacion in self.repository.get_by_usuario(id_usuario):
            if not notificacion.leida:
                notificacion.leida = True
                self.repository.mark_updated(notificacion, actor=actor)
        self.repository.flush()
        return {"success": True, "message": "Todas las notificaciones marcadas como leídas"}

    # --- Mantenimiento periódico (cron) ---

    def _generar_si_no_existe(self, id_usuario: int, tipo: str, mensaje: str, actor: str) -> bool:
        if not self.repository.existe_para_usuario(id_usuario, tipo, mensaje):
            self.repository.add(
                Notificacion(id_usuario=id_usuario, tipo=tipo, mensaje=mensaje), actor=actor
            )
            return True
        return False

    def ejecutar_mantenimiento(self, actor: str = "cron") -> dict:
        generadas = 0
        ahora = datetime.now()

        # 1) Recordatorios de devolución (3 días y mismo día).
        for id_prestamo, id_usuario, esperada in self.prestamo_repo.get_activos_por_vencer_raw(
            RECORDATORIO_DIAS
        ):
            dias = (esperada.date() - ahora.date()).days
            if dias <= 0:
                tipo, plantilla = "RECORDATORIO_HOY", NotificacionMessages.RECORDATORIO_HOY
            else:
                tipo, plantilla = "RECORDATORIO_3D", NotificacionMessages.RECORDATORIO_3D
            if self._generar_si_no_existe(id_usuario, tipo, plantilla.format(id=id_prestamo), actor):
                generadas += 1

        # 2) Avisos de vencimiento.
        for id_prestamo, id_usuario, esperada in self.prestamo_repo.get_vencidos_raw():
            dias = (ahora.date() - esperada.date()).days
            if self._generar_si_no_existe(
                id_usuario,
                "VENCIDO",
                NotificacionMessages.VENCIDO.format(dias=dias, id=id_prestamo),
                actor,
            ):
                generadas += 1

        # 3) Expiración de reservas CUMPLIDA cuya ventana ya venció.
        expiradas = 0
        for reserva in self.reserva_repo.get_cumplidas_expiradas():
            reserva.estado = "EXPIRADA"
            self.reserva_repo.mark_updated(reserva, actor=actor)
            expiradas += 1
        if expiradas:
            self.reserva_repo.flush()

        return {
            "success": True,
            "message": "Mantenimiento ejecutado correctamente",
            "notificaciones_generadas": generadas,
            "reservas_expiradas": expiradas,
        }