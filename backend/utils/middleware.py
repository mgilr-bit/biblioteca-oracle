"""Middleware de autenticación JWT vía hook before_request."""
from flask import jsonify, request

from utils.security import decode_token

PUBLIC_PATHS = {
    "/api/auth/login",
    "/api/auth/register",
    "/api/health",
}


def before_request_jwt():
    """Valida el JWT en todas las rutas /api/* excepto las públicas."""
    if request.method == "OPTIONS":
        return None
    if not request.path.startswith("/api/"):
        return None
    if request.endpoint is None or request.path in PUBLIC_PATHS:
        return None

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Token requerido"}), 401

    try:
        token = auth_header.split(" ", 1)[1].strip()
        request.user = decode_token(token)
    except ValueError as error:
        return jsonify({"error": str(error)}), 401

    return None
