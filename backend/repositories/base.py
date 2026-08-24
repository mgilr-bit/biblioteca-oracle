"""Repositorio base con operaciones CRUD genéricas.

`delete()` hace soft-delete (marca is_deleted/deleted_at/deleted_by) en
vez de borrar la fila, para las entidades que traen `AuditMixin`
(ver models/base.py) — preserva el historial para auditoría. Si el
modelo no tiene esas columnas, cae a un DELETE real (comportamiento
anterior), por si algún día se agrega una entidad sin auditoría.
"""
from datetime import datetime, timezone
from typing import Generic, List, Optional, Type, TypeVar

from sqlmodel import Session, SQLModel, select

ModelType = TypeVar("ModelType", bound=SQLModel)


class BaseRepository(Generic[ModelType]):
    def __init__(self, session: Session, model: Type[ModelType]):
        self.session = session
        self.model = model

    def _not_deleted(self, stmt):
        if hasattr(self.model, "is_deleted"):
            stmt = stmt.where(self.model.is_deleted == False)  # noqa: E712
        return stmt

    def get_by_id(self, primary_key: int) -> Optional[ModelType]:
        instance = self.session.get(self.model, primary_key)
        if instance is not None and getattr(instance, "is_deleted", False):
            return None
        return instance

    def get_all(self) -> List[ModelType]:
        return list(self.session.exec(self._not_deleted(select(self.model))))

    def add(self, instance: ModelType, actor: Optional[str] = None) -> ModelType:
        if actor and hasattr(instance, "created_by"):
            instance.created_by = actor
        self.session.add(instance)
        self.session.flush()
        return instance

    def flush(self) -> None:
        self.session.flush()

    def mark_updated(self, instance: ModelType, actor: Optional[str] = None) -> None:
        """Sella updated_at/updated_by; llamar antes de flush() en cada update."""
        if hasattr(instance, "updated_at"):
            instance.updated_at = datetime.now(timezone.utc)
        if actor and hasattr(instance, "updated_by"):
            instance.updated_by = actor

    def delete(self, instance: ModelType, actor: Optional[str] = None) -> None:
        if hasattr(instance, "is_deleted"):
            instance.is_deleted = True
            instance.deleted_at = datetime.now(timezone.utc)
            instance.deleted_by = actor
            self.session.add(instance)
            self.session.flush()
        else:
            self.session.delete(instance)
            self.session.flush()

    def restore(self, instance: ModelType, actor: Optional[str] = None) -> None:
        instance.is_deleted = False
        instance.deleted_at = None
        instance.deleted_by = None
        self.mark_updated(instance, actor)
        self.session.flush()
