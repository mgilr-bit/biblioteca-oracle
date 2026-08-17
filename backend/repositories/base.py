"""Repositorio base con operaciones CRUD genéricas."""
from typing import Generic, List, Optional, Type, TypeVar

from sqlmodel import Session, SQLModel, select

ModelType = TypeVar("ModelType", bound=SQLModel)


class BaseRepository(Generic[ModelType]):
    def __init__(self, session: Session, model: Type[ModelType]):
        self.session = session
        self.model = model

    def get_by_id(self, primary_key: int) -> Optional[ModelType]:
        return self.session.get(self.model, primary_key)

    def get_all(self) -> List[ModelType]:
        return list(self.session.exec(select(self.model)))

    def add(self, instance: ModelType) -> ModelType:
        self.session.add(instance)
        self.session.flush()
        return instance

    def flush(self) -> None:
        self.session.flush()

    def delete(self, instance: ModelType) -> None:
        self.session.delete(instance)
        self.session.flush()
