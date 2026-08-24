"""Límite de tamaño de body por request (OWASP API4:2023 — Unrestricted
Resource Consumption). Sin esto, cualquier endpoint que acepte JSON queda
expuesto a un payload arbitrariamente grande antes de que Pydantic
siquiera tenga oportunidad de rechazarlo."""
from fastapi import Request
from fastapi.responses import JSONResponse

from core.messages import GenericMessages

MAX_BODY_BYTES = 2 * 1024 * 1024  # 2 MiB — generoso para JSON de este dominio


async def body_size_limit_middleware(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_BODY_BYTES:
        return JSONResponse(status_code=413, content={"error": GenericMessages.PAYLOAD_MUY_GRANDE})
    return await call_next(request)
