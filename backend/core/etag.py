"""Soporte de ETag / 304 Not Modified para respuestas GET cacheables."""
import hashlib

from fastapi import Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from core.zona_horaria import localizar_fechas


def etag_response(request: Request, payload) -> Response:
    """Calcula el ETag del payload serializado y devuelve 304 si coincide con If-None-Match."""
    # Los datetimes salen en hora de Guatemala con zona explícita (ver core.zona_horaria).
    contenido = localizar_fechas(jsonable_encoder(payload))
    body = JSONResponse(content=contenido).body
    etag = hashlib.sha256(body).hexdigest()

    if_none_match = request.headers.get("if-none-match")
    if if_none_match and if_none_match.strip('"') == etag:
        not_modified = Response(status_code=304)
        not_modified.headers["ETag"] = f'"{etag}"'
        return not_modified

    final = JSONResponse(content=contenido)
    final.headers["ETag"] = f'"{etag}"'
    final.headers["Cache-Control"] = "private, must-revalidate"
    return final
