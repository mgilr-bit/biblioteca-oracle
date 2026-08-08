"""Controllers de autenticación."""
import logging

from flask import Blueprint, jsonify, request

from config.database import get_session
from services.auth_service import AuthService
from utils.http import api_route

auth_bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)


@auth_bp.route("/login", methods=["POST"])
@api_route
def login():
    data = request.get_json(silent=True) or {}
    with get_session() as session:
        result = AuthService(session).login(data.get("email"), data.get("password"))
    return jsonify(result)


@auth_bp.route("/register", methods=["POST"])
@api_route
def register():
    data = request.get_json(silent=True) or {}
    with get_session() as session:
        result = AuthService(session).register(
            data.get("nombre"), data.get("email"), data.get("password")
        )
    return jsonify(result), 201
