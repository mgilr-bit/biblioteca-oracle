"""Router de gestión de préstamos.

Cambios de autorización respecto al Flask original (documentados, no
accidentales): `GET /`, `GET /activos` y `GET /vencidos` listaban los
préstamos de TODOS los usuarios sin restricción de rol; ahora requieren
BIBLIOTECARIO. `POST /` deja de ser BIBLIOTECARIO-only: un LECTOR ahora
sí puede pedir prestado un libro para sí mismo (el servicio fuerza su
propio id_usuario, ignorando cualquier otro que mande en el body).

Handlers sync (no `async def`) porque `get_session()` es I/O bloqueante
contra Oracle — FastAPI los corre en threadpool.
"""
from fastapi import APIRouter, Depends, Request

from config.database import get_session
from core.etag import etag_response
from core.sessions import SessionUser
from dependencies.rbac import require_permission, require_permission_owned
from schemas.common import MessageResponse
from schemas.prestamo import PrestamoCreate, PrestamoResponse
from services.prestamo_service import PrestamoService

router = APIRouter()

LIST_ALL = require_permission("Prestamo", "read")


@router.get("/", response_model=list[PrestamoResponse])
def get_prestamos(request: Request, user=Depends(LIST_ALL)):
    with get_session() as session:
        prestamos = PrestamoService(session).get_all()
    return etag_response(request, prestamos)


@router.get("/activos", response_model=list[PrestamoResponse])
def get_prestamos_activos(request: Request, user=Depends(LIST_ALL)):
    with get_session() as session:
        prestamos = PrestamoService(session).get_activos()
    return etag_response(request, prestamos)


@router.get("/vencidos", response_model=list[PrestamoResponse])
def get_prestamos_vencidos(request: Request, user=Depends(LIST_ALL)):
    with get_session() as session:
        prestamos = PrestamoService(session).get_vencidos()
    return etag_response(request, prestamos)


@router.get("/usuario/{id_usuario}", response_model=list[PrestamoResponse])
def get_prestamos_usuario(
    id_usuario: int,
    request: Request,
    user: SessionUser = Depends(require_permission_owned("Prestamo", "read", "id_usuario")),
):
    with get_session() as session:
        prestamos = PrestamoService(session).get_by_usuario(id_usuario)
    return etag_response(request, prestamos)


@router.post("/", response_model=MessageResponse, status_code=201)
def create_prestamo(
    body: PrestamoCreate, user: SessionUser = Depends(require_permission("Prestamo", "create"))
):
    with get_session() as session:
        result = PrestamoService(session).create(
            body.id_libro, body.id_usuario, body.dias_prestamo, requesting_user=user
        )
    return result


@router.put("/{id_prestamo}/devolver", response_model=MessageResponse)
def devolver_prestamo(id_prestamo: int, user=Depends(require_permission("Prestamo", "devolver"))):
    with get_session() as session:
        result = PrestamoService(session).devolver(id_prestamo)
    return result
