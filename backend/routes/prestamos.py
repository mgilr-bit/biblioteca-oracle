from flask import Blueprint, request, jsonify
from config.database import db
from datetime import datetime, timedelta
from utils.security import token_required, role_required
import logging

prestamos_bp = Blueprint('prestamos', __name__)
logger = logging.getLogger(__name__)

@prestamos_bp.route('/', methods=['GET'])
@token_required
def get_prestamos():
    """Obtener todos los préstamos"""
    try:
        query = """
            SELECT p.id_prestamo, p.id_libro, p.id_usuario,
                   p.fecha_prestamo, p.fecha_devolucion_esperada,
                   p.fecha_devolucion_real, p.estado,
                   l.titulo, l.autor,
                   u.nombre as nombre_usuario
            FROM prestamos p
            JOIN libros l ON p.id_libro = l.id_libro
            JOIN usuarios u ON p.id_usuario = u.id_usuario
            ORDER BY p.fecha_prestamo DESC
        """
        prestamos = db.execute_query(query)
        
        for prestamo in prestamos:
            if prestamo.get('FECHA_PRESTAMO'):
                prestamo['FECHA_PRESTAMO'] = str(prestamo['FECHA_PRESTAMO'])
            if prestamo.get('FECHA_DEVOLUCION_ESPERADA'):
                prestamo['FECHA_DEVOLUCION_ESPERADA'] = str(prestamo['FECHA_DEVOLUCION_ESPERADA'])
            if prestamo.get('FECHA_DEVOLUCION_REAL'):
                prestamo['FECHA_DEVOLUCION_REAL'] = str(prestamo['FECHA_DEVOLUCION_REAL'])
        
        return jsonify(prestamos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@prestamos_bp.route('/activos', methods=['GET'])
@token_required
def get_prestamos_activos():
    """Obtener préstamos activos"""
    try:
        query = """
            SELECT p.id_prestamo, p.id_libro, p.id_usuario,
                   p.fecha_prestamo, p.fecha_devolucion_esperada,
                   p.estado,
                   l.titulo, l.autor,
                   u.nombre as nombre_usuario
            FROM prestamos p
            JOIN libros l ON p.id_libro = l.id_libro
            JOIN usuarios u ON p.id_usuario = u.id_usuario
            WHERE p.estado IN ('ACTIVO', 'VENCIDO')
            ORDER BY p.fecha_devolucion_esperada
        """
        prestamos = db.execute_query(query)
        
        for prestamo in prestamos:
            if prestamo.get('FECHA_PRESTAMO'):
                prestamo['FECHA_PRESTAMO'] = str(prestamo['FECHA_PRESTAMO'])
            if prestamo.get('FECHA_DEVOLUCION_ESPERADA'):
                prestamo['FECHA_DEVOLUCION_ESPERADA'] = str(prestamo['FECHA_DEVOLUCION_ESPERADA'])
        
        return jsonify(prestamos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@prestamos_bp.route('/usuario/<int:id_usuario>', methods=['GET'])
@token_required
def get_prestamos_usuario(id_usuario):
    """Obtener préstamos de un usuario"""
    try:
        query = """
            SELECT p.id_prestamo, p.id_libro,
                   p.fecha_prestamo, p.fecha_devolucion_esperada,
                   p.fecha_devolucion_real, p.estado,
                   l.titulo, l.autor
            FROM prestamos p
            JOIN libros l ON p.id_libro = l.id_libro
            WHERE p.id_usuario = :id_usuario
            ORDER BY p.fecha_prestamo DESC
        """
        prestamos = db.execute_query(query, {"id_usuario": id_usuario})
        
        for prestamo in prestamos:
            if prestamo.get('FECHA_PRESTAMO'):
                prestamo['FECHA_PRESTAMO'] = str(prestamo['FECHA_PRESTAMO'])
            if prestamo.get('FECHA_DEVOLUCION_ESPERADA'):
                prestamo['FECHA_DEVOLUCION_ESPERADA'] = str(prestamo['FECHA_DEVOLUCION_ESPERADA'])
            if prestamo.get('FECHA_DEVOLUCION_REAL'):
                prestamo['FECHA_DEVOLUCION_REAL'] = str(prestamo['FECHA_DEVOLUCION_REAL'])
        
        return jsonify(prestamos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@prestamos_bp.route('/', methods=['POST'])
@token_required
@role_required(['BIBLIOTECARIO'])
def create_prestamo():
    """Crear un nuevo préstamo - Solo bibliotecarios"""
    try:
        data = request.get_json()
        
        id_libro = data.get('id_libro')
        id_usuario = data.get('id_usuario')
        dias_prestamo = data.get('dias_prestamo', 14)
        
        if not id_libro or not id_usuario:
            return jsonify({"error": "id_libro e id_usuario son requeridos"}), 400
        
        # Verificar disponibilidad
        check_query = """
            SELECT copias_disponibles 
            FROM libros 
            WHERE id_libro = :id_libro
        """
        result = db.execute_query(check_query, {"id_libro": id_libro})
        
        if not result or result[0]['COPIAS_DISPONIBLES'] <= 0:
            return jsonify({"error": "No hay copias disponibles"}), 400
        
        # Calcular fecha de devolución
        fecha_devolucion = datetime.now() + timedelta(days=dias_prestamo)
        
        # Crear préstamo
        insert_query = """
            INSERT INTO prestamos (id_libro, id_usuario, fecha_devolucion_esperada)
            VALUES (:id_libro, :id_usuario, TO_DATE(:fecha_devolucion, 'YYYY-MM-DD'))
        """
        
        db.execute_query(
            insert_query,
            {
                "id_libro": id_libro,
                "id_usuario": id_usuario,
                "fecha_devolucion": fecha_devolucion.strftime('%Y-%m-%d')
            },
            fetch=False
        )
        
        return jsonify({
            "success": True,
            "message": "Préstamo creado exitosamente"
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@prestamos_bp.route('/<int:id_prestamo>/devolver', methods=['PUT'])
@token_required
@role_required(['BIBLIOTECARIO'])
def devolver_prestamo(id_prestamo):
    """Registrar devolución de un préstamo - Solo bibliotecarios"""
    try:
        query = """
            UPDATE prestamos 
            SET fecha_devolucion_real = SYSDATE,
                estado = 'DEVUELTO'
            WHERE id_prestamo = :id_prestamo
            AND estado != 'DEVUELTO'
        """
        
        result = db.execute_query(query, {"id_prestamo": id_prestamo}, fetch=False)
        
        if result['affected_rows'] == 0:
            return jsonify({"error": "Préstamo no encontrado o ya devuelto"}), 404
        
        return jsonify({
            "success": True,
            "message": "Devolución registrada exitosamente"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@prestamos_bp.route('/vencidos', methods=['GET'])
@token_required
def get_prestamos_vencidos():
    """Obtener préstamos vencidos"""
    try:
        query = """
            SELECT p.id_prestamo, p.id_libro, p.id_usuario,
                   p.fecha_prestamo, p.fecha_devolucion_esperada,
                   l.titulo, l.autor,
                   u.nombre as nombre_usuario, u.email
            FROM prestamos p
            JOIN libros l ON p.id_libro = l.id_libro
            JOIN usuarios u ON p.id_usuario = u.id_usuario
            WHERE p.fecha_devolucion_esperada < SYSDATE
            AND p.estado = 'ACTIVO'
            ORDER BY p.fecha_devolucion_esperada
        """
        prestamos = db.execute_query(query)
        
        for prestamo in prestamos:
            if prestamo.get('FECHA_PRESTAMO'):
                prestamo['FECHA_PRESTAMO'] = str(prestamo['FECHA_PRESTAMO'])
            if prestamo.get('FECHA_DEVOLUCION_ESPERADA'):
                prestamo['FECHA_DEVOLUCION_ESPERADA'] = str(prestamo['FECHA_DEVOLUCION_ESPERADA'])
        
        return jsonify(prestamos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
