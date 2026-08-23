"""Router de gestión de usuarios.

Handlers sync (no `async def`) para que FastAPI los ejecute en threadpool,
dado que `get_session()` es I/O bloqueante contra Oracle.
"""
from fastapi import APIRouter, Depends, Request

from config.database import get_session
from core.etag import etag_response
from core.sessions import SessionUser
from dependencies.rbac import require_permission, require_permission_owned
from schemas.common import MessageResponse
from schemas.usuario import (
    UsuarioAdminCreate,
    UsuarioEstadoUpdate,
    UsuarioResponse,
    UsuarioUpdate,
)
from services.usuario_service import UsuarioService

router = APIRouter()


@router.get("/", response_model=list[UsuarioResponse])
def get_usuarios(request: Request, user=Depends(require_permission("Usuario", "read"))):
    with get_session() as session:
        usuarios = UsuarioService(session).get_all()
    return etag_response(request, [UsuarioResponse.model_validate(u) for u in usuarios])


@router.post("/admin", response_model=MessageResponse, status_code=201)
def create_usuario_admin(
    body: UsuarioAdminCreate, user=Depends(require_permission("Usuario", "create"))
):
    with get_session() as session:
        result = UsuarioService(session).create_admin(body.model_dump())
    return result


@router.get("/{id_usuario}", response_model=UsuarioResponse)
def get_usuario(
    id_usuario: int,
    request: Request,
    user: SessionUser = Depends(require_permission_owned("Usuario", "read", "id_usuario")),
):
    with get_session() as session:
        usuario = UsuarioService(session).get_by_id(id_usuario)
    return etag_response(request, UsuarioResponse.model_validate(usuario))


@router.put("/{id_usuario}", response_model=MessageResponse)
def update_usuario(
    id_usuario: int,
    body: UsuarioUpdate,
    user: SessionUser = Depends(require_permission_owned("Usuario", "update", "id_usuario")),
):
    with get_session() as session:
        result = UsuarioService(session).update(id_usuario, body.model_dump(), requesting_user=user)
    return result


@router.patch("/{id_usuario}/estado", response_model=MessageResponse)
def toggle_estado_usuario(
    id_usuario: int, body: UsuarioEstadoUpdate, user=Depends(require_permission("Usuario", "toggle_estado"))
):
    with get_session() as session:
        result = UsuarioService(session).toggle_estado(id_usuario, body.activo)
    return result


@router.delete("/{id_usuario}", response_model=MessageResponse)
def delete_usuario(id_usuario: int, user=Depends(require_permission("Usuario", "delete"))):
    with get_session() as session:
        result = UsuarioService(session).delete(id_usuario)
    return result
