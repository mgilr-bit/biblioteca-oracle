"""Controllers de gestión de libros."""
import csv
import io
import logging
from datetime import datetime

from flask import Blueprint, jsonify, make_response, request

from config.database import get_session
from services.libro_service import LibroService
from utils.http import api_route
from utils.security import role_required

libros_bp = Blueprint("libros", __name__)
logger = logging.getLogger(__name__)


@libros_bp.route("/", methods=["GET"])
@api_route
def get_libros():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 100, type=int)
    limit = request.args.get("limit", type=int)
    with get_session() as session:
        result = LibroService(session).get_all(page, per_page, limit)
    return jsonify(result)


@libros_bp.route("/<int:id_libro>", methods=["GET"])
@api_route
def get_libro(id_libro):
    with get_session() as session:
        libro = LibroService(session).get_by_id(id_libro)
    return jsonify(libro)


@libros_bp.route("/generos", methods=["GET"])
@api_route
def get_generos():
    with get_session() as session:
        generos = LibroService(session).get_generos()
    return jsonify(generos)


@libros_bp.route("/search", methods=["GET"])
@api_route
def search_libros():
    titulo = request.args.get("titulo", "")
    autor = request.args.get("autor", "")
    isbn = request.args.get("isbn", "")
    genero = request.args.get("genero", "")
    limit = request.args.get("limit", 200, type=int)
    with get_session() as session:
        libros = LibroService(session).search(titulo, autor, isbn, genero, limit)
    return jsonify(libros)


@libros_bp.route("/", methods=["POST"])
@role_required(["BIBLIOTECARIO"])
@api_route
def create_libro():
    data = request.get_json(silent=True) or {}
    with get_session() as session:
        result = LibroService(session).create(data)
    return jsonify(result), 201


@libros_bp.route("/<int:id_libro>", methods=["PUT"])
@role_required(["BIBLIOTECARIO"])
@api_route
def update_libro(id_libro):
    data = request.get_json(silent=True) or {}
    with get_session() as session:
        result = LibroService(session).update(id_libro, data)
    return jsonify(result)


@libros_bp.route("/<int:id_libro>/copias", methods=["PATCH"])
@api_route
def update_copias(id_libro):
    data = request.get_json(silent=True) or {}
    with get_session() as session:
        result = LibroService(session).update_copias(
            id_libro, data.get("copias_disponibles")
        )
    return jsonify(result)


@libros_bp.route("/<int:id_libro>", methods=["DELETE"])
@role_required(["BIBLIOTECARIO"])
@api_route
def delete_libro(id_libro):
    with get_session() as session:
        result = LibroService(session).delete(id_libro)
    return jsonify(result)


@libros_bp.route("/bajo-stock", methods=["GET"])
@api_route
def libros_bajo_stock():
    with get_session() as session:
        libros = LibroService(session).get_bajo_stock()
    return jsonify(libros)


@libros_bp.route("/export/csv", methods=["GET"])
@role_required(["BIBLIOTECARIO"])
@api_route
def export_libros_csv():
    with get_session() as session:
        libros = LibroService(session).get_all_for_export()

    output = io.StringIO()
    writer = csv.writer(output)

    if libros:
        headers = list(libros[0].keys())
        writer.writerow(headers)
        for libro in libros:
            writer.writerow([libro.get(h) for h in headers])

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = (
        f'attachment; filename=libros_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )
    logger.info(f"Exportación CSV: {len(libros)} libros exportados por usuario {request.user['email']}")

    return response


@libros_bp.route("/estadisticas", methods=["GET"])
@api_route
def get_estadisticas():
    with get_session() as session:
        stats = LibroService(session).get_estadisticas()
    return jsonify(stats)
