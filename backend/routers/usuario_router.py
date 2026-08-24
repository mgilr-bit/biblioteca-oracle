"""Router de gestión de usuarios.

Handlers sync (no `async def`) para que FastAPI los ejecute en threadpool,
dado que la sesión de BD hace I/O bloqueante contra Oracle.
"""
from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from core.etag import etag_response
from core.sessions import SessionUser
from dependencies.db import get_db_session
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
def get_usuarios(
    request: Request,
    session: Session = Depends(get_db_session),
    user=Depends(require_permission("Usuario", "read")),
):
    usuarios = UsuarioService(session).get_all()
    return etag_response(request, [UsuarioResponse.model_validate(u) for u in usuarios])


@router.post("/admin", response_model=MessageResponse, status_code=201)
def create_usuario_admin(
    body: UsuarioAdminCreate,
    session: Session = Depends(get_db_session),
    user=Depends(require_permission("Usuario", "create")),
):
    return UsuarioService(session).create_admin(body.model_dump())


@router.get("/{id_usuario}", response_model=UsuarioResponse)
def get_usuario(
    id_usuario: int,
    request: Request,
    session: Session = Depends(get_db_session),
    user: SessionUser = Depends(require_permission_owned("Usuario", "read", "id_usuario")),
):
    usuario = UsuarioService(session).get_by_id(id_usuario)
    return etag_response(request, UsuarioResponse.model_validate(usuario))


@router.put("/{id_usuario}", response_model=MessageResponse)
def update_usuario(
    id_usuario: int,
    body: UsuarioUpdate,
    session: Session = Depends(get_db_session),
    user: SessionUser = Depends(require_permission_owned("Usuario", "update", "id_usuario")),
):
    return UsuarioService(session).update(id_usuario, body.model_dump(), requesting_user=user)


@router.patch("/{id_usuario}/estado", response_model=MessageResponse)
def toggle_estado_usuario(
    id_usuario: int,
    body: UsuarioEstadoUpdate,
    session: Session = Depends(get_db_session),
    user=Depends(require_permission("Usuario", "toggle_estado")),
):
    return UsuarioService(session).toggle_estado(id_usuario, body.activo)


@router.delete("/{id_usuario}", response_model=MessageResponse)
def delete_usuario(
    id_usuario: int,
    session: Session = Depends(get_db_session),
    user=Depends(require_permission("Usuario", "delete")),
):
    return UsuarioService(session).delete(id_usuario)
