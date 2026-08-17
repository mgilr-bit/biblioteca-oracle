"""Controllers de gestión de usuarios."""
import logging

from flask import Blueprint, jsonify, request

from config.database import get_session
from services.usuario_service import UsuarioService
from utils.http import api_route
from utils.security import role_required

usuarios_bp = Blueprint("usuarios", __name__)
logger = logging.getLogger(__name__)


@usuarios_bp.route("/", methods=["GET"])
@api_route
def get_usuarios():
    with get_session() as session:
        usuarios = UsuarioService(session).get_all()
    return jsonify(usuarios)


@usuarios_bp.route("/<int:id_usuario>", methods=["GET"])
@api_route
def get_usuario(id_usuario):
    with get_session() as session:
        usuario = UsuarioService(session).get_by_id(id_usuario)
    return jsonify(usuario)


@usuarios_bp.route("/admin", methods=["POST"])
@role_required(["BIBLIOTECARIO"])
@api_route
def create_usuario_admin():
    data = request.get_json(silent=True) or {}
    with get_session() as session:
        result = UsuarioService(session).create_admin(data)
    return jsonify(result), 201


@usuarios_bp.route("/<int:id_usuario>", methods=["PUT"])
@role_required(["BIBLIOTECARIO"])
@api_route
def update_usuario(id_usuario):
    data = request.get_json(silent=True) or {}
    with get_session() as session:
        result = UsuarioService(session).update(id_usuario, data)
    return jsonify(result)


@usuarios_bp.route("/<int:id_usuario>/estado", methods=["PATCH"])
@role_required(["BIBLIOTECARIO"])
@api_route
def toggle_estado_usuario(id_usuario):
    data = request.get_json(silent=True) or {}
    with get_session() as session:
        result = UsuarioService(session).toggle_estado(
            id_usuario, data.get("activo")
        )
    return jsonify(result)


@usuarios_bp.route("/<int:id_usuario>", methods=["DELETE"])
@role_required(["BIBLIOTECARIO"])
@api_route
def delete_usuario(id_usuario):
    with get_session() as session:
        result = UsuarioService(session).delete(id_usuario)
    return jsonify(result)
