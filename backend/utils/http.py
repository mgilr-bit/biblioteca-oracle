"""Helpers HTTP para los controllers."""
import logging
from functools import wraps

from flask import jsonify

from services.exceptions import ServiceError


def api_route(fn):
    """Envuelve un endpoint capturando errores de servicio y del servidor."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ServiceError as error:
            return jsonify({"error": str(error)}), error.status_code
        except Exception as error:
            logging.getLogger(fn.__module__).exception(
                f"Error no controlado en {fn.__name__}: {error}"
            )
            return jsonify({"error": "Error interno del servidor"}), 500

    return wrapper
