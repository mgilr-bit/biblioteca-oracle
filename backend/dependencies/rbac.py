"""Autorización RBAC + ABAC (Casbin) aplicada como dependencias de ruta."""
import types
from typing import Optional

from fastapi import Depends, HTTPException, Request

from core.casbin_enforcer import enforcer
from core.messages import AuthMessages
from core.sessions import SessionUser
from dependencies.auth import get_current_user


def _enforce(user: SessionUser, subject: str, act: str, owner_id: Optional[int]) -> bool:
    sub = types.SimpleNamespace(rol=user.rol, id=user.id)
    obj = types.SimpleNamespace(subject=subject, owner_id=owner_id)
    return enforcer.enforce(sub, obj, act)


def require_permission(subject: str, act: str):
    """Gate de RBAC puro (sin contexto de dueño): listas, creación, acciones admin."""

    def dependency(user: SessionUser = Depends(get_current_user)) -> SessionUser:
        if not _enforce(user, subject, act, owner_id=None):
            raise HTTPException(status_code=403, detail=AuthMessages.SIN_PERMISOS)
        return user

    return dependency


def require_permission_owned(subject: str, act: str, owner_param: str):
    """Gate de RBAC + ABAC: valida además que `owner_param` (path param) sea del usuario en sesión,
    salvo que su rol tenga la política sin restricción de dueño (ej. BIBLIOTECARIO)."""

    def dependency(request: Request, user: SessionUser = Depends(get_current_user)) -> SessionUser:
        owner_id = int(request.path_params[owner_param])
        if not _enforce(user, subject, act, owner_id=owner_id):
            # 404 en vez de 403 en lecturas ajenas: no confirmar la existencia del recurso a quien no es su dueño.
            status_code = 404 if act == "read" else 403
            detail = AuthMessages.NO_ENCONTRADO if act == "read" else AuthMessages.SIN_PERMISOS
            raise HTTPException(status_code=status_code, detail=detail)
        return user

    return dependency
