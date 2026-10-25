"""Servicios de reservas con cola FIFO y cupos simultáneos.

Reglas de producto (plan de fases):
* Un usuario puede tener a lo sumo `MAX_ACTIVAS_POR_USUARIO` reservas ACTIVA.
* No puede reservar dos veces el mismo libro estando ACTIVA.
* Ciclo: ACTIVA -> RECOGIDA | SIN_RECOGER | CANCELADA.
* Una reserva ACTIVA con `fecha_expiracion` tiene una copia apartada y
  `DIAS_VALIDEZ` días para recogerla. Se aparta al crearla si hay una copia
  libre (disponible y no apartada por otra reserva); si no, espera en la
  cola FIFO sin fecha y `repartir_copias` le aparta la siguiente que se libere.
* Si vence la ventana sin recogerla pasa a SIN_RECOGER (`actualizar_estados`,
  que corre en cada consulta y en el job de mantenimiento: la BD no tiene un
  scheduler propio) y su copia pasa al siguiente de la cola.
* Recoger (PrestamoService.recoger_reserva) registra el préstamo y la marca
  RECOGIDA. Cancelar y recoger son solo de BIBLIOTECARIO/ADMIN.
"""
from datetime import timedelta
from typing import List, Optional

from core.messages import NotificacionMessages, ReservaMessages
from core.roles import puede_operar_por_terceros
from core.zona_horaria import ahora_utc
from models.reserva import Reserva
from models.usuario import Usuario
from repositories.libro_repository import LibroRepository
from repositories.reserva_repository import ReservaRepository
from schemas.reserva import ReservaResponse
from services import avisos
from services.auditoria_service import AuditoriaService
from services.base import BaseService
from services.exceptions import BusinessRuleError, ValidationError
from services.libro_service import ESTADO_ETIQUETAS

MAX_ACTIVAS_POR_USUARIO = 3
DIAS_VALIDEZ = 3  # ventana para recoger una vez se le aparta una copia


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
        self.actualizar_estados()
        return [self._serializar(row) for row in self.repository.get_all_with_details()]

    def get_by_usuario(self, id_usuario: int) -> List[ReservaResponse]:
        self.actualizar_estados()
        return [
            self._serializar(row)
            for row in self.repository.get_by_usuario_with_details(id_usuario)
        ]

    def get_cola(self, id_libro: int) -> List[dict]:
        self.actualizar_estados()
        return [
            {
                "id_reserva": r.id_reserva,
                "id_usuario": r.id_usuario,
                "nombre_usuario": nombre_usuario,
                "fecha_reserva": r.fecha_reserva,
                "fecha_expiracion": r.fecha_expiracion,
            }
            for r, _titulo, _autor, nombre_usuario in self.repository.get_cola_with_details(id_libro)
        ]

    def create(self, id_libro: int, id_usuario: Optional[int], requesting_user) -> dict:
        # SEGURIDAD: un LECTOR/PROFESOR solo reserva para sí mismo (patrón del
        # módulo de préstamos); BIBLIOTECARIO y ADMIN reservan a nombre de otro.
        if not puede_operar_por_terceros(requesting_user.rol):
            id_usuario = requesting_user.id
        elif not id_usuario:
            raise ValidationError(ReservaMessages.ID_USUARIO_REQUERIDO)

        if not id_libro or not id_usuario:
            raise ValidationError(ReservaMessages.CAMPOS_REQUERIDOS)

        libro = self.libro_repo.get_by_id(id_libro)
        if not libro:
            raise ValidationError(ReservaMessages.LIBRO_NO_EXISTE)
        if libro.estado != "DISPONIBLE":
            raise BusinessRuleError(ReservaMessages.LIBRO_NO_DISPONIBLE.format(estado=ESTADO_ETIQUETAS.get(libro.estado, libro.estado)))

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
        # Si hay copia libre se le aparta ya (y arranca su ventana de 3 días);
        # si no, queda en la cola. Se reparte en orden FIFO, así una reserva
        # nueva nunca adelanta a las que ya esperaban.
        self.repartir_copias(id_libro, notificar=False)

        AuditoriaService(self.repository.session).registrar(
            "RESERVA_CREADA",
            "Reserva",
            id_usuario=requesting_user.id,
            email=requesting_user.email,
            rol=requesting_user.rol,
            id_recurso=reserva.id_reserva,
            detalle=f"Reserva del libro #{id_libro} para usuario #{id_usuario}",
        )

        hasta = avisos.fecha_hora(reserva.fecha_expiracion) if reserva.fecha_expiracion else None
        # La biblioteca se entera de las reservas que hacen los propios
        # usuarios (las que registra el personal ya las conoce).
        if not puede_operar_por_terceros(requesting_user.rol):
            self._avisar_al_personal(requesting_user.nombre, libro.titulo, hasta)

        if hasta:
            return {"success": True, "message": ReservaMessages.CREADA_CON_COPIA.format(hasta=hasta)}
        return {"success": True, "message": ReservaMessages.CREADA_EN_COLA}

    def _avisar_al_personal(self, nombre: str, titulo: str, hasta: Optional[str]) -> None:
        if hasta:
            mensaje = NotificacionMessages.RESERVA_NUEVA_CON_COPIA.format(nombre=nombre, titulo=titulo, hasta=hasta)
        else:
            mensaje = NotificacionMessages.RESERVA_NUEVA_EN_COLA.format(nombre=nombre, titulo=titulo)
        avisos.avisar_personal(self.repository.session, "RESERVA_NUEVA", mensaje)

    def _titulo(self, id_libro: int) -> str:
        libro = self.libro_repo.get_by_id(id_libro)
        return libro.titulo if libro else f"#{id_libro}"

    def cancelar(self, id_reserva: int, requesting_user) -> dict:
        reserva = self.get_by_id(id_reserva)
        if reserva.estado != "ACTIVA":
            raise ValidationError(ReservaMessages.NO_CANCELABLE)

        tenia_copia = reserva.fecha_expiracion is not None
        reserva.estado = "CANCELADA"
        self.repository.mark_updated(reserva, actor=requesting_user.email)
        self.repository.flush()
        if tenia_copia:
            self.repartir_copias(reserva.id_libro)
        avisos.avisar_usuario(
            self.repository.session,
            reserva.id_usuario,
            "RESERVA_CANCELADA",
            NotificacionMessages.RESERVA_CANCELADA.format(titulo=self._titulo(reserva.id_libro)),
        )

        AuditoriaService(self.repository.session).registrar(
            "RESERVA_CANCELADA",
            "Reserva",
            id_usuario=requesting_user.id,
            email=requesting_user.email,
            rol=requesting_user.rol,
            id_recurso=reserva.id_reserva,
        )
        return {"success": True, "message": "Reserva cancelada exitosamente"}

    def marcar_recogida(self, id_libro: int, id_usuario: int, actor: str) -> Optional[Reserva]:
        """Al prestar un libro, cierra la reserva ACTIVA que el usuario tenga sobre él."""
        reserva = self.repository.get_activa_de_usuario(id_libro, id_usuario)
        if reserva:
            reserva.estado = "RECOGIDA"
            self.repository.mark_updated(reserva, actor=actor)
            self.repository.flush()
        return reserva

    def copias_apartadas_para_otros(self, id_libro: int, id_usuario: int) -> int:
        return self.repository.count_apartadas(id_libro, excluir_usuario=id_usuario)

    def repartir_copias(self, id_libro: int, actor: str = "sistema", notificar: bool = True) -> int:
        """Aparta las copias libres del libro a la cola, en orden FIFO.

        Libres = disponibles - ya apartadas. Cada reserva que recibe copia
        arranca su ventana de `DIAS_VALIDEZ` días. Devuelve cuántas se apartaron.
        """
        libres = self.repository.get_copias_disponibles(id_libro) - self.repository.count_apartadas(id_libro)
        if libres <= 0:
            return 0
        apartadas = 0
        for reserva in self.repository.get_en_cola(id_libro)[:libres]:
            reserva.fecha_expiracion = ahora_utc() + timedelta(days=DIAS_VALIDEZ)
            self.repository.mark_updated(reserva, actor=actor)
            if notificar:
                avisos.avisar_usuario(
                    self.repository.session,
                    reserva.id_usuario,
                    "RESERVA_DISPONIBLE",
                    NotificacionMessages.RESERVA_DISPONIBLE.format(dias=DIAS_VALIDEZ),
                )
            apartadas += 1
        self.repository.flush()
        return apartadas

    def actualizar_estados(self, actor: str = "sistema") -> int:
        """Pasa a SIN_RECOGER las reservas cuya ventana venció y reparte las
        copias que se liberan (también las devueltas desde la última vez).
        Idempotente; devuelve cuántas reservas vencieron."""
        vencidas = self.repository.get_vencidas_sin_recoger()
        session = self.repository.session
        for reserva in vencidas:
            reserva.estado = "SIN_RECOGER"
            self.repository.mark_updated(reserva, actor=actor)
            usuario = session.get(Usuario, reserva.id_usuario)
            datos = {
                "titulo": self._titulo(reserva.id_libro),
                "nombre": usuario.nombre if usuario else f"Usuario #{reserva.id_usuario}",
                "fecha": avisos.fecha(reserva.fecha_expiracion),
            }
            avisos.avisar_usuario(
                session, reserva.id_usuario, "RESERVA_SIN_RECOGER", NotificacionMessages.RESERVA_SIN_RECOGER.format(**datos)
            )
            avisos.avisar_personal(
                session, "RESERVA_SIN_RECOGER", NotificacionMessages.PERSONAL_RESERVA_SIN_RECOGER.format(**datos)
            )
        if vencidas:
            self.repository.flush()
        for id_libro in self.repository.get_libros_con_cola():
            self.repartir_copias(id_libro, actor=actor)
        return len(vencidas)
