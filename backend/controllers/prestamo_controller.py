"""Controllers de gestión de préstamos."""
import logging

from flask import Blueprint, jsonify, request

from config.database import get_session
from services.prestamo_service import PrestamoService
from utils.http import api_route
from utils.security import role_required

prestamos_bp = Blueprint("prestamos", __name__)
logger = logging.getLogger(__name__)


@prestamos_bp.route("/", methods=["GET"])
@api_route
def get_prestamos():
    with get_session() as session:
        prestamos = PrestamoService(session).get_all()
    return jsonify(prestamos)


@prestamos_bp.route("/activos", methods=["GET"])
@api_route
def get_prestamos_activos():
    with get_session() as session:
        prestamos = PrestamoService(session).get_activos()
    return jsonify(prestamos)


@prestamos_bp.route("/usuario/<int:id_usuario>", methods=["GET"])
@api_route
def get_prestamos_usuario(id_usuario):
    with get_session() as session:
        prestamos = PrestamoService(session).get_by_usuario(id_usuario)
    return jsonify(prestamos)


@prestamos_bp.route("/", methods=["POST"])
@role_required(["BIBLIOTECARIO"])
@api_route
def create_prestamo():
    data = request.get_json(silent=True) or {}
    with get_session() as session:
        result = PrestamoService(session).create(
            data.get("id_libro"),
            data.get("id_usuario"),
            data.get("dias_prestamo"),
        )
    return jsonify(result), 201


@prestamos_bp.route("/<int:id_prestamo>/devolver", methods=["PUT"])
@role_required(["BIBLIOTECARIO"])
@api_route
def devolver_prestamo(id_prestamo):
    with get_session() as session:
        result = PrestamoService(session).devolver(id_prestamo)
    return jsonify(result)


@prestamos_bp.route("/vencidos", methods=["GET"])
@api_route
def get_prestamos_vencidos():
    with get_session() as session:
        prestamos = PrestamoService(session).get_vencidos()
    return jsonify(prestamos)
