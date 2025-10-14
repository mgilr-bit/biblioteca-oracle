"""
Script para poblar la base de datos con 500 libros
"""
import random
from config.database import db
from faker import Faker
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

fake = Faker(['es_ES', 'es_MX'])

# Listas de datos realistas para libros
GENEROS = [
    'Ficción', 'No Ficción', 'Ciencia Ficción', 'Fantasía', 'Misterio',
    'Thriller', 'Romance', 'Horror', 'Biografía', 'Historia',
    'Ciencia', 'Tecnología', 'Filosofía', 'Poesía', 'Drama',
    'Aventura', 'Policiaco', 'Autoayuda', 'Ensayo', 'Infantil'
]

EDITORIALES = [
    'Penguin Random House', 'Planeta', 'Anagrama', 'Alfaguara', 'Tusquets',
    'Salamandra', 'Seix Barral', 'Destino', 'Debolsillo', 'Sudamericana',
    'Paidós', 'Grijalbo', 'Ediciones B', 'Espasa', 'Santillana',
    'Crítica', 'Acantilado', 'Pre-Textos', 'Siruela', 'Alianza Editorial'
]

# Títulos base para generar combinaciones únicas
TITULOS_BASE = [
    'El secreto de', 'La historia de', 'Los misterios de', 'El jardín de',
    'La sombra de', 'El último', 'La venganza de', 'Los hijos de',
    'El legado de', 'La profecía de', 'Los guardianes de', 'El reino de',
    'La guerra de', 'Los secretos de', 'El destino de', 'La búsqueda de',
    'Los caminos de', 'El poder de', 'La noche de', 'Los días de',
    'El viaje de', 'La luz de', 'Los sueños de', 'El despertar de',
    'La caída de', 'Los ecos de', 'El retorno de', 'La voz de'
]

SUFIJOS = [
    'la montaña', 'las estrellas', 'los olvidados', 'la eternidad',
    'las sombras', 'los vientos', 'la memoria', 'los perdidos',
    'la luna', 'los ancestros', 'el tiempo', 'las cenizas',
    'la tormenta', 'los ríos', 'el sol', 'las olas',
    'la noche', 'los bosques', 'el fuego', 'las nubes'
]

def generar_isbn():
    """Generar un ISBN-13 válido"""
    # ISBN-13 comienza con 978 o 979
    prefix = random.choice(['978', '979'])
    # Generar 9 dígitos aleatorios
    middle = ''.join([str(random.randint(0, 9)) for _ in range(9)])

    # Calcular dígito de verificación
    isbn_sin_check = prefix + middle
    suma = 0
    for i, digit in enumerate(isbn_sin_check):
        if i % 2 == 0:
            suma += int(digit)
        else:
            suma += int(digit) * 3
    check_digit = (10 - (suma % 10)) % 10

    return f"{prefix}-{middle[:5]}-{middle[5:]}-{check_digit}"

def generar_titulo():
    """Generar un título único y realista"""
    base = random.choice(TITULOS_BASE)
    sufijo = random.choice(SUFIJOS)

    # 30% de probabilidad de agregar un subtítulo
    if random.random() < 0.3:
        subtitulo = random.choice(['Una novela', 'Un relato', 'Una historia', 'Cuentos', 'Memorias'])
        return f"{base} {sufijo}: {subtitulo}"

    return f"{base} {sufijo}"

def generar_autor():
    """Generar nombre de autor realista"""
    nombre = fake.first_name()
    apellido1 = fake.last_name()

    # 50% de probabilidad de tener segundo apellido
    if random.random() < 0.5:
        apellido2 = fake.last_name()
        return f"{nombre} {apellido1} {apellido2}"

    return f"{nombre} {apellido1}"

def crear_libro():
    """Crear un libro con datos aleatorios pero realistas"""
    titulo = generar_titulo()
    autor = generar_autor()
    isbn = generar_isbn()
    anio_publicacion = random.randint(1950, 2024)
    genero = random.choice(GENEROS)
    editorial = random.choice(EDITORIALES)
    numero_copias = random.randint(1, 15)
    copias_disponibles = random.randint(0, numero_copias)  # Algunas pueden estar prestadas

    return {
        'titulo': titulo,
        'autor': autor,
        'isbn': isbn,
        'anio_publicacion': anio_publicacion,
        'genero': genero,
        'editorial': editorial,
        'numero_copias': numero_copias,
        'copias_disponibles': copias_disponibles
    }

def poblar_libros(cantidad=500):
    """Poblar la base de datos con libros"""
    logger.info(f"Iniciando población de {cantidad} libros...")

    query = """
        INSERT INTO libros (titulo, autor, isbn, anio_publicacion, genero, editorial, numero_copias, copias_disponibles)
        VALUES (:titulo, :autor, :isbn, :anio_publicacion, :genero, :editorial, :numero_copias, :copias_disponibles)
    """

    libros_insertados = 0
    errores = 0

    for i in range(cantidad):
        try:
            libro = crear_libro()
            db.execute_query(query, libro, fetch=False)
            libros_insertados += 1

            if (i + 1) % 50 == 0:
                logger.info(f"Insertados {i + 1} libros...")

        except Exception as e:
            errores += 1
            logger.error(f"Error insertando libro {i + 1}: {str(e)}")
            continue

    logger.info(f"Proceso completado:")
    logger.info(f"  - Libros insertados: {libros_insertados}")
    logger.info(f"  - Errores: {errores}")

    return libros_insertados, errores

if __name__ == '__main__':
    try:
        # Verificar conexión a la base de datos
        logger.info("Verificando conexión a la base de datos...")
        test_query = "SELECT COUNT(*) as count FROM libros"
        result = db.execute_query(test_query)
        logger.info(f"Libros actuales en la base de datos: {result[0]['COUNT']}")

        # Poblar con 500 libros
        insertados, errores = poblar_libros(500)

        # Verificar total después de inserción
        result = db.execute_query(test_query)
        logger.info(f"Total de libros en la base de datos: {result[0]['COUNT']}")

    except Exception as e:
        logger.error(f"Error fatal: {str(e)}")
        exit(1)
