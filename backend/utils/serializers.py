"""Serialización de entidades a dicts compatibles con el frontend."""
from datetime import date, datetime
from typing import Any, List, Optional, Set


def _serialize_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def to_dict(instance: Any, exclude: Optional[Set[str]] = None) -> dict:
    """Convierte una entidad en dict con claves en MAYÚSCULAS (contrato actual)."""
    return {
        key.upper(): _serialize_value(value)
        for key, value in instance.model_dump(exclude=exclude).items()
    }


def to_list(instances: List[Any], exclude: Optional[Set[str]] = None) -> List[dict]:
    return [to_dict(instance, exclude) for instance in instances]
