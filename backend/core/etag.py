"""Soporte de ETag / 304 Not Modified para respuestas GET cacheables."""
import hashlib

from fastapi import Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def etag_response(request: Request, payload) -> Response:
    """Calcula el ETag del payload serializado y devuelve 304 si coincide con If-None-Match."""
    body = JSONResponse(content=jsonable_encoder(payload)).body
    etag = hashlib.sha256(body).hexdigest()

    if_none_match = request.headers.get("if-none-match")
    if if_none_match and if_none_match.strip('"') == etag:
        not_modified = Response(status_code=304)
        not_modified.headers["ETag"] = f'"{etag}"'
        return not_modified

    final = JSONResponse(content=jsonable_encoder(payload))
    final.headers["ETag"] = f'"{etag}"'
    final.headers["Cache-Control"] = "private, must-revalidate"
    return final
