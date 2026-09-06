"""Servicios de la bitácora de auditoría.

`registrar(...)`: punto único de escritura usado por los demás servicios
(AuthService, PrestamoService, MultaService, ReservaService,
UsuarioService, EjemplarService). La bitácora es append-only: cada fila se
hace flush con la misma sesión del flujo que la emite, así un registro de
negocio y su evento de auditoría se confirman juntos (o ninguno, si hay
rollback).
"""
from typing import List, Optional

from models.auditoria import Auditoria
from repositories.auditoria_repository import AuditoriaRepository
from services.base import BaseService

PER_PAGE_DEFAULT = 50
MAX_RESULTADOS = 2000


class AuditoriaService(BaseService[Auditoria]):
    not_found_message = "Registro de auditoría no encontrado"

    def __init__(self, session):
        super().__init__(AuditoriaRepository(session))

    def registrar(
        self,
        accion: str,
        recurso: str,
        id_usuario: Optional[int] = None,
        email: Optional[str] = None,
        rol: Optional[str] = None,
        id_recurso: Optional[int] = None,
        detalle: Optional[str] = None,
    ) -> None:
        fila = Auditoria(
            id_usuario=id_usuario,
            email=email,
            rol=rol,
            accion=accion[:50],
            recurso=recurso[:50],
            id_recurso=id_recurso,
            detalle=(detalle[:500] if detalle else None),
        )
        self.repository.session.add(fila)
        # Sin flush aquí: la fila se confirma junto con el flujo que la emitio

    def listar(self, page: int, per_page: int, accion=None, recurso=None, id_usuario=None) -> dict:
        page = max(page or 1, 1)
        per_page = min(max(per_page or PER_PAGE_DEFAULT, 1), MAX_RESULTADOS)
        offset = (page - 1) * per_page
        registros = self.repository.search(
            offset, per_page, accion=accion, recurso=recurso, id_usuario=id_usuario
        )
        total = self.repository.count(accion=accion, recurso=recurso, id_usuario=id_usuario)
        return {
            "auditoria": registros,
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page,
        }

    def get_acciones_disponibles(self) -> List[str]:
        return [
            "LOGIN",
            "LOGIN_FALLIDO",
            "LOGOUT",
            "REGISTER",
            "PRESTAMO_CREADO",
            "PRESTAMO_DEVUELTO",
            "MULTA_GENERADA",
            "MULTA_PAGADA",
            "MULTA_CONDONADA",
            "RESERVA_CREADA",
            "RESERVA_CANCELADA",
            "USUARIO_CREADO",
            "USUARIO_ACTUALIZADO",
            "USUARIO_ELIMINADO",
            "USUARIO_ESTADO",
            "EJEMPLAR_CREADO",
            "EJEMPLAR_ESTADO",
        ]

    def get_recursos_disponibles(self) -> List[str]:
        return ["Libro", "Prestamo", "Usuario", "Reserva", "Multa", "Ejemplar", "Auth"]