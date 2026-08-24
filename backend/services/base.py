"""Servicio base con las operaciones comunes a los 3 recursos.

Mirror del patrón BaseService/BaseController de wallet-api (NestJS): cada
servicio concreto extiende esto y solo aporta lo que le es propio (reglas
de negocio en create/update); lo genérico -- buscar por id o levantar
NotFoundError, listar todo, borrar (soft-delete) -- vive una sola vez acá,
igual que BaseRepository ya centraliza el CRUD de bajo nivel.
"""
from typing import Generic, List, Optional, TypeVar

from sqlmodel import SQLModel

from repositories.base import BaseRepository
from services.exceptions import NotFoundError

ModelType = TypeVar("ModelType", bound=SQLModel)


class BaseService(Generic[ModelType]):
    #: Mensaje de error cuando get_by_id/delete_entity no encuentran el registro.
    #: Cada subclase lo pisa con el mensaje de core.messages correspondiente.
    not_found_message: str = "Registro no encontrado"

    def __init__(self, repository: BaseRepository[ModelType]):
        self.repository = repository

    def get_all(self) -> List[ModelType]:
        return self.repository.get_all()

    def get_by_id(self, pk: int) -> ModelType:
        instance = self.repository.get_by_id(pk)
        if not instance:
            raise NotFoundError(self.not_found_message)
        return instance

    def delete_entity(self, pk: int, actor: Optional[str] = None) -> ModelType:
        """Busca (o levanta NotFoundError) y hace soft-delete; devuelve la
        instancia para que el servicio concreto arme su propio mensaje."""
        instance = self.get_by_id(pk)
        self.repository.delete(instance, actor=actor)
        return instance
