"""Zona horaria de la aplicación.

Convención: en la BD todo instante se guarda como DATE/TIMESTAMP *naive en
UTC*. En Oracle Autonomous DB `SYSDATE`/`SYSTIMESTAMP` devuelven UTC sin
importar la sesión, y el backend usa `ahora_utc()` para que sus propios
valores calcen con los de la BD (comparaciones de vencimiento, ventanas de
recogida, etc.) sin depender de la zona del host.

Hacia afuera (API JSON y reportes) los instantes se presentan en la hora de
Guatemala (`APP_TIMEZONE`). Sin esto la SPA mostraba la hora UTC —seis horas
adelantada— porque recibía ISO sin zona y lo leía como hora local.
"""
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    ZONA_LOCAL = ZoneInfo(os.getenv("APP_TIMEZONE", "America/Guatemala"))
except ZoneInfoNotFoundError:
    # Imagen sin base de zonas horarias: Guatemala es UTC-6 fijo (sin horario de verano).
    ZONA_LOCAL = timezone(timedelta(hours=-6), "America/Guatemala")

# ISO de un datetime naive tal como lo serializa pydantic/jsonable_encoder.
_ISO_NAIVE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?$")


def ahora_utc() -> datetime:
    """Instante actual como datetime naive en UTC (la convención de la BD)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def a_local(valor: datetime) -> datetime:
    """Convierte un instante de la BD (naive = UTC) a la hora local, con zona."""
    if valor.tzinfo is None:
        valor = valor.replace(tzinfo=timezone.utc)
    return valor.astimezone(ZONA_LOCAL)


def localizar_fechas(dato: Any) -> Any:
    """Recorre un payload ya serializado a JSON (dicts/listas/strings) y
    reescribe cada datetime ISO naive como ISO con la zona local.

    Ej.: "2026-10-07T02:02:55" -> "2026-10-06T20:02:55-06:00". Las fechas sin
    hora ("2026-10-07") no se tocan: no son instantes.
    """
    if isinstance(dato, str):
        if _ISO_NAIVE.match(dato):
            return a_local(datetime.fromisoformat(dato)).isoformat()
        return dato
    if isinstance(dato, dict):
        return {k: localizar_fechas(v) for k, v in dato.items()}
    if isinstance(dato, list):
        return [localizar_fechas(v) for v in dato]
    return dato
