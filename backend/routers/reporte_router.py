"""Router de reportes: un endpoint por sección de la aplicación.

`GET /api/reportes/{seccion}?formato=json|xlsx|csv&<filtros>`

* `json`: la SPA lo convierte en PDF (jsPDF) con el mismo contenido.
* `xlsx`: libro con hoja de resumen y una hoja por tabla.
* `csv`: UTF-8 con BOM, cabeceras legibles.

Autorización (Casbin): cada reporte exige el mismo permiso de lectura que
la pantalla correspondiente. En préstamos, reservas y multas el alcance se
ramifica como en las vistas: BIBLIOTECARIO/ADMIN ven todo y LECTOR/PROFESOR
solo lo propio. Cada generación queda en la bitácora (REPORTE_GENERADO).

Handlers sync porque la sesión de BD hace I/O bloqueante contra Oracle.
"""
from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlmodel import Session

from core.sessions import SessionUser
from dependencies.auth import get_current_user
from dependencies.db import get_db_session
from dependencies.rbac import has_permission, require_permission, require_permission_session_owned
from schemas.reporte import FormatoReporte, ReporteResponse
from services.auditoria_service import AuditoriaService
from services.reporte_service import ReporteService
from utils.reporte_export import exportar_csv, exportar_xlsx, nombre_archivo

router = APIRouter()

_MEDIA_TYPES = {
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "csv": "text/csv; charset=utf-8",
}

Texto = Query(default="", max_length=100)


def _responder(reporte: ReporteResponse, formato: FormatoReporte, session: Session, user: SessionUser) -> Response:
    if formato == "json":
        respuesta = JSONResponse(content=jsonable_encoder(reporte))
    else:
        contenido = exportar_xlsx(reporte) if formato == "xlsx" else exportar_csv(reporte)
        respuesta = Response(
            content=contenido,
            media_type=_MEDIA_TYPES[formato],
            headers={"Content-Disposition": f'attachment; filename="{nombre_archivo(reporte, formato)}"'},
        )
    respuesta.headers["Cache-Control"] = "no-store"

    AuditoriaService(session).registrar(
        "REPORTE_GENERADO",
        "Reporte",
        id_usuario=user.id,
        email=user.email,
        rol=user.rol,
        detalle=f"{reporte.titulo} en {'PDF' if formato == 'json' else formato.upper()} "
        f"({reporte.total_filas} registro(s))",
    )
    return respuesta


@router.get("/libros")
def reporte_libros(
    formato: FormatoReporte = "json",
    titulo: str = Texto,
    autor: str = Texto,
    isbn: str = Texto,
    genero: str = Texto,
    session: Session = Depends(get_db_session),
    user: SessionUser = Depends(require_permission("Libro", "read")),
):
    reporte = ReporteService(session).libros(user, titulo=titulo, autor=autor, isbn=isbn, genero=genero)
    return _responder(reporte, formato, session, user)


@router.get("/editoriales")
def reporte_editoriales(
    formato: FormatoReporte = "json",
    session: Session = Depends(get_db_session),
    user: SessionUser = Depends(require_permission("Editorial", "read")),
):
    return _responder(ReporteService(session).editoriales(user), formato, session, user)


@router.get("/ejemplares")
def reporte_ejemplares(
    formato: FormatoReporte = "json",
    id_libro: Optional[int] = Query(default=None, ge=1),
    estado: str = Texto,
    session: Session = Depends(get_db_session),
    user: SessionUser = Depends(require_permission("Ejemplar", "read")),
):
    reporte = ReporteService(session).ejemplares(user, id_libro=id_libro, estado=estado)
    return _responder(reporte, formato, session, user)


@router.get("/reservas")
def reporte_reservas(
    formato: FormatoReporte = "json",
    estado: str = Texto,
    session: Session = Depends(get_db_session),
    user: SessionUser = Depends(require_permission_session_owned("Reserva", "read")),
):
    ver_todo = has_permission(user, "Reserva", "read")
    reporte = ReporteService(session).reservas(user, ver_todo, estado=estado)
    return _responder(reporte, formato, session, user)


@router.get("/prestamos")
def reporte_prestamos(
    formato: FormatoReporte = "json",
    vista: Literal["todos", "activos", "vencidos"] = "todos",
    fecha_prestamo: Optional[date] = None,
    fecha_devolucion: Optional[date] = None,
    libro: str = Texto,
    session: Session = Depends(get_db_session),
    user: SessionUser = Depends(require_permission_session_owned("Prestamo", "read")),
):
    ver_todo = has_permission(user, "Prestamo", "read")
    reporte = ReporteService(session).prestamos(
        user,
        ver_todo,
        vista=vista,
        fecha_prestamo=fecha_prestamo,
        fecha_devolucion=fecha_devolucion,
        libro=libro,
    )
    return _responder(reporte, formato, session, user)


@router.get("/multas")
def reporte_multas(
    formato: FormatoReporte = "json",
    vista: Literal["todas", "pendientes"] = "todas",
    session: Session = Depends(get_db_session),
    user: SessionUser = Depends(require_permission_session_owned("Multa", "read")),
):
    ver_todo = has_permission(user, "Multa", "read")
    reporte = ReporteService(session).multas(user, ver_todo, vista=vista)
    return _responder(reporte, formato, session, user)


@router.get("/usuarios")
def reporte_usuarios(
    formato: FormatoReporte = "json",
    nombre: str = Texto,
    rol: str = Texto,
    estado: str = Texto,
    session: Session = Depends(get_db_session),
    user: SessionUser = Depends(require_permission("Usuario", "read")),
):
    reporte = ReporteService(session).usuarios(user, nombre=nombre, rol=rol, estado=estado)
    return _responder(reporte, formato, session, user)


@router.get("/auditoria")
def reporte_auditoria(
    formato: FormatoReporte = "json",
    accion: str = Texto,
    recurso: str = Texto,
    session: Session = Depends(get_db_session),
    user: SessionUser = Depends(require_permission("Auditoria", "read")),
):
    reporte = ReporteService(session).auditoria(user, accion=accion, recurso=recurso)
    return _responder(reporte, formato, session, user)


@router.get("/notificaciones")
def reporte_notificaciones(
    formato: FormatoReporte = "json",
    session: Session = Depends(get_db_session),
    user: SessionUser = Depends(require_permission_session_owned("Notificacion", "read")),
):
    return _responder(ReporteService(session).notificaciones(user), formato, session, user)


@router.get("/analitica")
def reporte_analitica(
    formato: FormatoReporte = "json",
    session: Session = Depends(get_db_session),
    user: SessionUser = Depends(require_permission("Analitica", "read")),
):
    return _responder(ReporteService(session).analitica(user), formato, session, user)


@router.get("/dashboard")
def reporte_dashboard(
    formato: FormatoReporte = "json",
    session: Session = Depends(get_db_session),
    user: SessionUser = Depends(get_current_user),
):
    ver_todo = has_permission(user, "Prestamo", "read")
    return _responder(ReporteService(session).dashboard(user, ver_todo), formato, session, user)
