from flask import Flask, jsonify
from flask_cors import CORS
import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from pathlib import Path

# Cargar .env desde el directorio raíz del proyecto
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# Configurar logging
if not os.path.exists('logs'):
    os.mkdir('logs')

file_handler = RotatingFileHandler('logs/biblioteca.log', maxBytes=10240000, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Biblioteca API startup')

# Configurar CORS - En producción, cambiar a dominios específicos
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:5500,http://127.0.0.1:5500').split(',')
CORS(app, resources={
    r"/api/*": {
        "origins": ALLOWED_ORIGINS,
        "methods": ["GET", "POST", "PUT", "DELETE", "PATCH"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Importar rutas
from routes.auth import auth_bp
from routes.libros import libros_bp
from routes.usuarios import usuarios_bp
from routes.prestamos import prestamos_bp

# Registrar blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(libros_bp, url_prefix='/api/libros')
app.register_blueprint(usuarios_bp, url_prefix='/api/usuarios')
app.register_blueprint(prestamos_bp, url_prefix='/api/prestamos')

@app.route('/')
def home():
    return jsonify({
        "message": "API Sistema de Gestión de Biblioteca",
        "version": "1.0",
        "endpoints": {
            "auth": "/api/auth",
            "libros": "/api/libros",
            "usuarios": "/api/usuarios",
            "prestamos": "/api/prestamos"
        }
    })

@app.route('/api/health')
def health():
    """Endpoint para verificar el estado de la API"""
    try:
        from config.database import db
        db.get_connection().close()
        return jsonify({"status": "healthy", "database": "connected"})
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint no encontrado"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Error interno del servidor"}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

