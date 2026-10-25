"""Servicios de gestión de préstamos."""
from datetime import timedelta
from typing import List, Optional

from core.messages import NotificacionMessages, PrestamoMessages, ReservaMessages
from core.roles import puede_operar_por_terceros
from core.zona_horaria import ahora_utc
from models.prestamo import Prestamo
from repositories.libro_repository import LibroRepository
from repositories.prestamo_repository import PrestamoRepository
from schemas.prestamo import PrestamoResponse
from services import avisos
from services.auditoria_service import AuditoriaService
from services.base import BaseService
from services.exceptions import BusinessRuleError, ValidationError
from services.libro_service import ESTADO_ETIQUETAS
from services.multa_service import MultaService, dias_de_retraso
from services.reserva_service import ReservaService

DIAS_PRESTAMO_DEFAULT = 14


class PrestamoService(BaseService[Prestamo]):
    not_found_message = PrestamoMessages.NOT_FOUND

    def __init__(self, session):
        super().__init__(PrestamoRepository(session))
        self.libro_repo = LibroRepository(session)
        self.reserva_service = ReservaService(session)
        self.multa_service = MultaService(session)

    def _calcular_estado(self, prestamo: Prestamo) -> str:
        if (
            prestamo.estado == "ACTIVO"
            and prestamo.fecha_devolucion_esperada
            and prestamo.fecha_devolucion_esperada < ahora_utc()
        ):
            return "VENCIDO"
        return prestamo.estado

    def _serializar(self, row) -> PrestamoResponse:
        prestamo = row[0]
        return PrestamoResponse(
            id_prestamo=prestamo.id_prestamo,
            id_libro=prestamo.id_libro,
            id_usuario=prestamo.id_usuario,
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
        # SEGURIDAD: un LECTOR/PROFESOR solo puede pedir prestado para sí
        # mismo, sin importar qué id_usuario mande en el body (mismo patrón
        # que el rol forzado en AuthService.register). BIBLIOTECARIO y ADMIN
        # sí prestan a nombre de otro.
        if not puede_operar_por_terceros(requesting_user.rol):
            id_usuario = requesting_user.id
        elif not id_usuario:
            raise ValidationError(PrestamoMessages.CAMPOS_REQUERIDOS)

        if not id_libro or not id_usuario:
            raise ValidationError(PrestamoMessages.CAMPOS_REQUERIDOS)

        dias = int(dias_prestamo or DIAS_PRESTAMO_DEFAULT)

        # Fase 5 (multas): una multa pendiente bloquea nuevos préstamos.
        if self.multa_service.usuario_tiene_pendientes(id_usuario):
            raise BusinessRuleError(PrestamoMessages.MULTAS_PENDIENTES)

        # Vence las reservas sin recoger antes de contar copias apartadas.
        self.reserva_service.actualizar_estados()

        libro = self.libro_repo.get_by_id(id_libro)
        if libro and libro.estado != "DISPONIBLE":
            raise BusinessRuleError(PrestamoMessages.LIBRO_NO_DISPONIBLE.format(estado=ESTADO_ETIQUETAS.get(libro.estado, libro.estado)))
        if not libro or libro.copias_disponibles <= 0:
            raise BusinessRuleError(PrestamoMessages.SIN_COPIAS)
        # Las copias apartadas para reservas de otros no se prestan.
        if libro.copias_disponibles - self.reserva_service.copias_apartadas_para_otros(id_libro, id_usuario) <= 0:
            raise BusinessRuleError(PrestamoMessages.COPIAS_APARTADAS)

        prestamo = Prestamo(
            id_libro=id_libro,
            id_usuario=id_usuario,
            fecha_devolucion_esperada=ahora_utc() + timedelta(days=dias),
        )
        self.repository.add(prestamo, actor=requesting_user.email)
        # Si el usuario tenía una reserva de este libro, este préstamo la cumple.
        reserva = self.reserva_service.marcar_recogida(id_libro, id_usuario, actor=requesting_user.email)
        plantilla = NotificacionMessages.RESERVA_RECOGIDA if reserva else NotificacionMessages.PRESTAMO_REGISTRADO
        avisos.avisar_usuario(
            self.repository.session,
            id_usuario,
            "RESERVA_RECOGIDA" if reserva else "PRESTAMO",
            plantilla.format(titulo=libro.titulo, fecha=avisos.fecha(prestamo.fecha_devolucion_esperada)),
        )

        AuditoriaService(self.repository.session).registrar(
            "PRESTAMO_CREADO",
            "Prestamo",
            id_usuario=requesting_user.id,
            email=requesting_user.email,
            rol=requesting_user.rol,
            id_recurso=prestamo.id_prestamo,
            detalle=f"Libro #{id_libro} prestado a usuario #{id_usuario} ({dias} días)",
        )

        return {"success": True, "message": "Préstamo creado exitosamente"}

    def recoger_reserva(self, id_reserva: int, requesting_user) -> dict:
        """El usuario pasó por su reserva: se le presta el libro y la reserva
        queda RECOGIDA (lo hace `create` vía `marcar_recogida`)."""
        self.reserva_service.actualizar_estados()
        reserva = self.reserva_service.get_by_id(id_reserva)
        if reserva.estado != "ACTIVA":
            raise ValidationError(ReservaMessages.NO_RECOGIBLE)
        if reserva.fecha_expiracion is None:
            raise BusinessRuleError(ReservaMessages.EN_COLA)

        self.create(reserva.id_libro, reserva.id_usuario, None, requesting_user)

        AuditoriaService(self.repository.session).registrar(
            "RESERVA_RECOGIDA",
            "Reserva",
            id_usuario=requesting_user.id,
            email=requesting_user.email,
            rol=requesting_user.rol,
            id_recurso=reserva.id_reserva,
            detalle=f"Libro #{reserva.id_libro} entregado a usuario #{reserva.id_usuario}",
        )
        return {"success": True, "message": ReservaMessages.RECOGIDA}

    def devolver(self, id_prestamo: int, actor: str) -> dict:
        prestamo = self.get_by_id(id_prestamo)
        if prestamo.estado == "DEVUELTO":
            raise ValidationError(PrestamoMessages.YA_DEVUELTO)

        prestamo.estado = "DEVUELTO"
        prestamo.fecha_devolucion_real = ahora_utc()
        self.repository.mark_updated(prestamo, actor=actor)
        self.repository.flush()

        # Fase 3 (reservas): la copia que vuelve se aparta a la reserva más
        # antigua de la cola, que tiene 3 días para recogerla.
        self.reserva_service.repartir_copias(prestamo.id_libro, actor=actor)

        # Fase 5 (multas): normalmente el job ya generó la multa al vencer el
        # préstamo; si todavía no pasó, se genera aquí. Luego se fijan los
        # días reales de retraso.
        self.multa_service.generar_por_atraso(prestamo, actor=actor)
        multa = self.multa_service.cerrar_atraso(prestamo, actor=actor)

        libro = self.libro_repo.get_by_id(prestamo.id_libro)
        titulo = libro.titulo if libro else f"#{prestamo.id_libro}"
        if prestamo.fecha_devolucion_real > prestamo.fecha_devolucion_esperada:
            dias = dias_de_retraso(prestamo.fecha_devolucion_esperada, prestamo.fecha_devolucion_real)
            mensaje = (
                NotificacionMessages.DEVOLUCION_TARDIA_MULTA.format(titulo=titulo, dias=dias, monto=f"{multa.monto:.2f}")
                if multa
                else NotificacionMessages.DEVOLUCION_TARDIA.format(titulo=titulo, dias=dias)
            )
        else:
            mensaje = NotificacionMessages.DEVOLUCION_A_TIEMPO.format(titulo=titulo)
        avisos.avisar_usuario(self.repository.session, prestamo.id_usuario, "DEVOLUCION", mensaje)

        if multa is not None:
            AuditoriaService(self.repository.session).registrar(
                "PRESTAMO_DEVUELTO",
                "Prestamo",
                email=actor,
                id_recurso=prestamo.id_prestamo,
                detalle=f"Devuelto con {multa.dias_retraso} día(s) de retraso; multa #{multa.id_multa} pendiente",
            )
            return {
                "success": True,
                "message": PrestamoMessages.DEVOLUCION_CON_MULTA.format(
                    monto=multa.monto, dias=multa.dias_retraso
                ),
            }

        AuditoriaService(self.repository.session).registrar(
            "PRESTAMO_DEVUELTO",
            "Prestamo",
            email=actor,
            id_recurso=prestamo.id_prestamo,
        )

        return {"success": True, "message": "Devolución registrada exitosamente"}
