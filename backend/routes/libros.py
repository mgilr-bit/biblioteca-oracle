from flask import Blueprint, request, jsonify
from config.database import db
from utils.security import token_required, role_required
import logging

libros_bp = Blueprint('libros', __name__)
logger = logging.getLogger(__name__)

@libros_bp.route('/', methods=['GET'])
@token_required
def get_libros():
    """Obtener todos los libros con paginación opcional"""
    try:
        # Parámetros de paginación opcionales
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)  # Por defecto 100 libros
        limit_results = request.args.get('limit', None, type=int)  # Límite total opcional

        # Validaciones
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 500:
            per_page = 100

        offset = (page - 1) * per_page

        # Query con paginación
        if limit_results:
            query = f"""
                SELECT id_libro, titulo, autor, isbn, anio_publicacion,
                       genero, numero_copias, copias_disponibles,
                       editorial, fecha_registro
                FROM libros
                ORDER BY titulo
                FETCH FIRST {limit_results} ROWS ONLY
            """
        else:
            query = f"""
                SELECT id_libro, titulo, autor, isbn, anio_publicacion,
                       genero, numero_copias, copias_disponibles,
                       editorial, fecha_registro
                FROM libros
                ORDER BY titulo
                OFFSET {offset} ROWS
                FETCH NEXT {per_page} ROWS ONLY
            """

        libros = db.execute_query(query)

        # Obtener total de libros
        count_query = "SELECT COUNT(*) as total FROM libros"
        total_result = db.execute_query(count_query)
        total_libros = total_result[0]['TOTAL']

        # Convertir fechas a string
        for libro in libros:
            if libro.get('FECHA_REGISTRO'):
                libro['FECHA_REGISTRO'] = str(libro['FECHA_REGISTRO'])

        # Retornar con metadata de paginación
        return jsonify({
            "libros": libros,
            "page": page,
            "per_page": per_page,
            "total": total_libros,
            "total_pages": (total_libros + per_page - 1) // per_page
        })
    except Exception as e:
        logger.error(f"Error obteniendo libros: {str(e)}")
        return jsonify({"error": str(e)}), 500

@libros_bp.route('/<int:id_libro>', methods=['GET'])
@token_required
def get_libro(id_libro):
    """Obtener un libro por ID"""
    try:
        query = """
            SELECT id_libro, titulo, autor, isbn, anio_publicacion, 
                   genero, numero_copias, copias_disponibles, 
                   editorial, fecha_registro
            FROM libros
            WHERE id_libro = :id_libro
        """
        libros = db.execute_query(query, {"id_libro": id_libro})
        
        if not libros:
            return jsonify({"error": "Libro no encontrado"}), 404
        
        libro = libros[0]
        if libro.get('FECHA_REGISTRO'):
            libro['FECHA_REGISTRO'] = str(libro['FECHA_REGISTRO'])
        
        return jsonify(libro)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@libros_bp.route('/generos', methods=['GET'])
@token_required
def get_generos():
    """Obtener lista de todos los géneros disponibles"""
    try:
        query = """
            SELECT DISTINCT genero
            FROM libros
            WHERE genero IS NOT NULL
            ORDER BY genero
        """
        result = db.execute_query(query)
        generos = [row['GENERO'] for row in result]

        return jsonify(generos)
    except Exception as e:
        logger.error(f"Error obteniendo géneros: {str(e)}")
        return jsonify({"error": str(e)}), 500

@libros_bp.route('/search', methods=['GET'])
@token_required
def search_libros():
    """Buscar libros por título, autor o género con límite de resultados"""
    try:
        titulo = request.args.get('titulo', '')
        autor = request.args.get('autor', '')
        genero = request.args.get('genero', '')
        limit = request.args.get('limit', 200, type=int)  # Límite por defecto de 200 resultados

        # Validar límite
        if limit < 1 or limit > 500:
            limit = 200

        query = """
            SELECT id_libro, titulo, autor, isbn, anio_publicacion,
                   genero, numero_copias, copias_disponibles,
                   editorial, fecha_registro
            FROM libros
            WHERE 1=1
        """
        params = {}

        if titulo:
            query += " AND UPPER(titulo) LIKE UPPER(:titulo)"
            params['titulo'] = f"%{titulo}%"

        if autor:
            query += " AND UPPER(autor) LIKE UPPER(:autor)"
            params['autor'] = f"%{autor}%"

        if genero:
            query += " AND UPPER(genero) LIKE UPPER(:genero)"
            params['genero'] = f"%{genero}%"

        query += f" ORDER BY titulo FETCH FIRST {limit} ROWS ONLY"

        libros = db.execute_query(query, params if params else None)

        for libro in libros:
            if libro.get('FECHA_REGISTRO'):
                libro['FECHA_REGISTRO'] = str(libro['FECHA_REGISTRO'])

        logger.info(f"Búsqueda de libros: {len(libros)} resultados encontrados")

        return jsonify(libros)
    except Exception as e:
        logger.error(f"Error buscando libros: {str(e)}")
        return jsonify({"error": str(e)}), 500

@libros_bp.route('/', methods=['POST'])
@token_required
@role_required(['BIBLIOTECARIO'])
def create_libro():
    """Crear un nuevo libro - Solo bibliotecarios"""
    try:
        data = request.get_json()
        
        required_fields = ['titulo', 'autor']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"El campo {field} es requerido"}), 400
        
        query = """
            INSERT INTO libros (titulo, autor, isbn, anio_publicacion, 
                              genero, numero_copias, copias_disponibles, editorial)
            VALUES (:titulo, :autor, :isbn, :anio_publicacion, 
                   :genero, :numero_copias, :copias_disponibles, :editorial)
        """
        
        params = {
            "titulo": data.get('titulo'),
            "autor": data.get('autor'),
            "isbn": data.get('isbn'),
            "anio_publicacion": data.get('anio_publicacion'),
            "genero": data.get('genero'),
            "numero_copias": data.get('numero_copias', 1),
            "copias_disponibles": data.get('numero_copias', 1),
            "editorial": data.get('editorial')
        }
        
        db.execute_query(query, params, fetch=False)
        
        return jsonify({
            "success": True,
            "message": "Libro creado exitosamente"
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@libros_bp.route('/<int:id_libro>', methods=['PUT'])
@token_required
@role_required(['BIBLIOTECARIO'])
def update_libro(id_libro):
    """Actualizar un libro - Solo bibliotecarios"""
    try:
        data = request.get_json()

        # Obtener datos actuales del libro
        query_actual = """
            SELECT numero_copias, copias_disponibles
            FROM libros
            WHERE id_libro = :id_libro
        """
        libro_actual = db.execute_query(query_actual, {"id_libro": id_libro})

        if not libro_actual:
            return jsonify({"error": "Libro no encontrado"}), 404

        copias_actuales = libro_actual[0]['NUMERO_COPIAS']
        disponibles_actuales = libro_actual[0]['COPIAS_DISPONIBLES']
        nuevas_copias = data.get('numero_copias', copias_actuales)

        # Calcular nuevas copias disponibles
        diferencia = nuevas_copias - copias_actuales
        nuevas_disponibles = disponibles_actuales + diferencia

        # No permitir que las disponibles sean negativas
        if nuevas_disponibles < 0:
            return jsonify({
                "error": f"No se puede reducir a {nuevas_copias} copias. Hay {copias_actuales - disponibles_actuales} copias prestadas."
            }), 400

        query = """
            UPDATE libros
            SET titulo = :titulo,
                autor = :autor,
                isbn = :isbn,
                anio_publicacion = :anio_publicacion,
                genero = :genero,
                numero_copias = :numero_copias,
                copias_disponibles = :copias_disponibles,
                editorial = :editorial
            WHERE id_libro = :id_libro
        """

        params = {
            "id_libro": id_libro,
            "titulo": data.get('titulo'),
            "autor": data.get('autor'),
            "isbn": data.get('isbn'),
            "anio_publicacion": data.get('anio_publicacion'),
            "genero": data.get('genero'),
            "numero_copias": nuevas_copias,
            "copias_disponibles": nuevas_disponibles,
            "editorial": data.get('editorial')
        }

        result = db.execute_query(query, params, fetch=False)

        if result['affected_rows'] == 0:
            return jsonify({"error": "Libro no encontrado"}), 404

        return jsonify({
            "success": True,
            "message": f"Libro actualizado exitosamente. Copias disponibles: {nuevas_disponibles}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@libros_bp.route('/<int:id_libro>/copias', methods=['PATCH'])
@token_required
def update_copias(id_libro):
    """Actualizar el número de copias disponibles"""
    try:
        data = request.get_json()
        copias = data.get('copias_disponibles')
        
        if copias is None:
            return jsonify({"error": "copias_disponibles es requerido"}), 400
        
        query = """
            UPDATE libros 
            SET copias_disponibles = :copias
            WHERE id_libro = :id_libro
        """
        
        result = db.execute_query(
            query, 
            {"id_libro": id_libro, "copias": copias},
            fetch=False
        )
        
        if result['affected_rows'] == 0:
            return jsonify({"error": "Libro no encontrado"}), 404
        
        return jsonify({
            "success": True,
            "message": "Copias actualizadas exitosamente"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@libros_bp.route('/<int:id_libro>', methods=['DELETE'])
@token_required
@role_required(['BIBLIOTECARIO'])
def delete_libro(id_libro):
    """Eliminar un libro - Solo bibliotecarios"""
    try:
        query = "DELETE FROM libros WHERE id_libro = :id_libro"
        result = db.execute_query(query, {"id_libro": id_libro}, fetch=False)
        
        if result['affected_rows'] == 0:
            return jsonify({"error": "Libro no encontrado"}), 404
        
        return jsonify({
            "success": True,
            "message": "Libro eliminado exitosamente"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@libros_bp.route('/bajo-stock', methods=['GET'])
@token_required
def libros_bajo_stock():
    """Obtener libros con bajo stock (copias_disponibles < 2)"""
    try:
        query = """
            SELECT id_libro, titulo, autor, copias_disponibles, numero_copias
            FROM libros
            WHERE copias_disponibles < 2
            ORDER BY copias_disponibles
        """
        libros = db.execute_query(query)
        return jsonify(libros)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@libros_bp.route('/export/csv', methods=['GET'])
@token_required
@role_required(['BIBLIOTECARIO'])
def export_libros_csv():
    """Exportar todos los libros a formato CSV - Solo bibliotecarios"""
    try:
        from flask import make_response
        from datetime import datetime
        import io
        import csv

        query = """
            SELECT id_libro, titulo, autor, isbn, anio_publicacion,
                   genero, editorial, numero_copias, copias_disponibles,
                   TO_CHAR(fecha_registro, 'YYYY-MM-DD') as fecha_registro
            FROM libros
            ORDER BY titulo
        """
        libros = db.execute_query(query)

        # Crear CSV en memoria
        output = io.StringIO()
        writer = csv.writer(output)

        # Encabezados
        if libros:
            headers = list(libros[0].keys())
            writer.writerow(headers)

            # Datos
            for libro in libros:
                writer.writerow([libro.get(h) for h in headers])

        # Preparar respuesta
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=libros_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

        logger.info(f"Exportación CSV: {len(libros)} libros exportados por usuario {request.user['email']}")

        return response

    except Exception as e:
        logger.error(f"Error exportando a CSV: {str(e)}")
        return jsonify({"error": str(e)}), 500
