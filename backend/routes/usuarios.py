from flask import Blueprint, request, jsonify
from config.database import db
from utils.security import token_required, role_required, hash_password
import logging

usuarios_bp = Blueprint('usuarios', __name__)
logger = logging.getLogger(__name__)

@usuarios_bp.route('/', methods=['GET'])
@token_required
def get_usuarios():
    """Obtener todos los usuarios"""
    try:
        query = """
            SELECT id_usuario, nombre, email, rol, activo, fecha_registro
            FROM usuarios
            ORDER BY nombre
        """
        usuarios = db.execute_query(query)
        
        for usuario in usuarios:
            if usuario.get('FECHA_REGISTRO'):
                usuario['FECHA_REGISTRO'] = str(usuario['FECHA_REGISTRO'])
        
        return jsonify(usuarios)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@usuarios_bp.route('/<int:id_usuario>', methods=['GET'])
@token_required
def get_usuario(id_usuario):
    """Obtener un usuario por ID"""
    try:
        query = """
            SELECT id_usuario, nombre, email, rol, activo, fecha_registro
            FROM usuarios
            WHERE id_usuario = :id_usuario
        """
        usuarios = db.execute_query(query, {"id_usuario": id_usuario})
        
        if not usuarios:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
        usuario = usuarios[0]
        if usuario.get('FECHA_REGISTRO'):
            usuario['FECHA_REGISTRO'] = str(usuario['FECHA_REGISTRO'])
        
        return jsonify(usuario)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@usuarios_bp.route('/<int:id_usuario>', methods=['PUT'])
@token_required
@role_required(['BIBLIOTECARIO'])
def update_usuario(id_usuario):
    """Actualizar un usuario"""
    try:
        data = request.get_json()
        
        query = """
            UPDATE usuarios 
            SET nombre = :nombre,
                email = :email,
                rol = :rol
            WHERE id_usuario = :id_usuario
        """
        
        params = {
            "id_usuario": id_usuario,
            "nombre": data.get('nombre'),
            "email": data.get('email'),
            "rol": data.get('rol')
        }
        
        result = db.execute_query(query, params, fetch=False)
        
        if result['affected_rows'] == 0:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
        return jsonify({
            "success": True,
            "message": "Usuario actualizado exitosamente"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@usuarios_bp.route('/<int:id_usuario>', methods=['DELETE'])
@token_required
@role_required(['BIBLIOTECARIO'])
def delete_usuario(id_usuario):
    """Eliminar permanentemente un usuario"""
    try:
        # Verificar si el usuario tiene préstamos activos
        check_query = """
            SELECT COUNT(*) as count
            FROM prestamos
            WHERE id_usuario = :id_usuario
            AND estado IN ('ACTIVO', 'VENCIDO')
        """
        check_result = db.execute_query(check_query, {"id_usuario": id_usuario})

        if check_result[0]['COUNT'] > 0:
            return jsonify({
                "error": "No se puede eliminar el usuario. Tiene préstamos activos."
            }), 400

        # Eliminar permanentemente
        query = """
            DELETE FROM usuarios
            WHERE id_usuario = :id_usuario
        """

        result = db.execute_query(query, {"id_usuario": id_usuario}, fetch=False)

        if result['affected_rows'] == 0:
            return jsonify({"error": "Usuario no encontrado"}), 404

        logger.info(f"Usuario {id_usuario} eliminado permanentemente")

        return jsonify({
            "success": True,
            "message": "Usuario eliminado permanentemente"
        })

    except Exception as e:
        logger.error(f"Error eliminando usuario: {str(e)}")
        return jsonify({"error": str(e)}), 500

@usuarios_bp.route('/admin', methods=['POST'])
@token_required
@role_required(['BIBLIOTECARIO'])
def create_usuario_admin():
    """Crear usuario con cualquier rol (solo BIBLIOTECARIOS pueden crear)"""
    try:
        data = request.get_json()
        nombre = data.get('nombre')
        email = data.get('email')
        password = data.get('password')
        rol = data.get('rol')

        if not nombre or not email or not password or not rol:
            return jsonify({"error": "Nombre, email, contraseña y rol son requeridos"}), 400

        # Validar rol
        if rol not in ['LECTOR', 'BIBLIOTECARIO']:
            return jsonify({"error": "Rol inválido. Debe ser LECTOR o BIBLIOTECARIO"}), 400

        # Validar longitud de contraseña
        if len(password) < 6:
            return jsonify({"error": "La contraseña debe tener al menos 6 caracteres"}), 400

        # Verificar si el email ya existe
        check_query = "SELECT COUNT(*) as count FROM usuarios WHERE email = :email"
        check_result = db.execute_query(check_query, {"email": email})

        if check_result[0]['COUNT'] > 0:
            logger.warning(f"Intento de crear usuario con email duplicado: {email}")
            return jsonify({"error": "El email ya está registrado"}), 400

        # Hash de la contraseña
        hashed_password = hash_password(password)

        # Insertar nuevo usuario
        insert_query = """
            INSERT INTO usuarios (nombre, email, password, rol)
            VALUES (:nombre, :email, :password, :rol)
        """

        db.execute_query(
            insert_query,
            {"nombre": nombre, "email": email, "password": hashed_password, "rol": rol},
            fetch=False
        )

        logger.info(f"Nuevo usuario creado por admin: {email} con rol {rol}")

        return jsonify({
            "success": True,
            "message": f"Usuario creado exitosamente como {rol}"
        }), 201

    except Exception as e:
        logger.error(f"Error creando usuario admin: {str(e)}")
        return jsonify({"error": str(e)}), 500

@usuarios_bp.route('/<int:id_usuario>/estado', methods=['PATCH'])
@token_required
@role_required(['BIBLIOTECARIO'])
def toggle_estado_usuario(id_usuario):
    """Cambiar estado activo/inactivo de un usuario"""
    try:
        data = request.get_json()
        nuevo_estado = data.get('activo')

        if nuevo_estado not in ['S', 'N']:
            return jsonify({"error": "Estado inválido. Debe ser 'S' o 'N'"}), 400

        query = """
            UPDATE usuarios
            SET activo = :activo
            WHERE id_usuario = :id_usuario
        """

        result = db.execute_query(
            query,
            {"id_usuario": id_usuario, "activo": nuevo_estado},
            fetch=False
        )

        if result['affected_rows'] == 0:
            return jsonify({"error": "Usuario no encontrado"}), 404

        estado_texto = "activado" if nuevo_estado == 'S' else "desactivado"
        logger.info(f"Usuario {id_usuario} {estado_texto}")

        return jsonify({
            "success": True,
            "message": f"Usuario {estado_texto} exitosamente"
        })

    except Exception as e:
        logger.error(f"Error cambiando estado de usuario: {str(e)}")
        return jsonify({"error": str(e)}), 500
