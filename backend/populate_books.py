"""
Script para poblar la base de datos con 500 libros
"""
import random

import logging
from sqlalchemy import func
from sqlmodel import select

from config.database import SessionLocal
from models.libro import Libro

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

NOMBRES = [
    'Juan', 'María', 'Carlos', 'Lucía', 'Andrés', 'Sofía', 'Miguel',
    'Valentina', 'José', 'Camila', 'Luis', 'Ana', 'Pedro', 'Isabella',
    'Jorge', 'Carolina', 'Fernando', 'Daniela', 'Ricardo', 'Gabriela'
]

APELLIDOS = [
    'García', 'Rodríguez', 'Martínez', 'López', 'González', 'Pérez',
    'Sánchez', 'Ramírez', 'Torres', 'Flores', 'Rivera', 'Gómez',
    'Díaz', 'Cruz', 'Morales', 'Vargas', 'Castillo', 'Rojas'
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
    """Generar nombre de autor realista sin dependencias externas"""
    nombre = random.choice(NOMBRES)
    apellido1 = random.choice(APELLIDOS)

    # 50% de probabilidad de tener segundo apellido
    if random.random() < 0.5:
        apellido2 = random.choice(APELLIDOS)
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
    """Poblar la base de datos con libros usando el ORM"""
    logger.info(f"Iniciando población de {cantidad} libros...")

    session = SessionLocal()
    insertados = 0
    errores = 0

    try:
        for i in range(cantidad):
            try:
                session.add(Libro(**crear_libro()))

                # Commit en lotes de 50
                if (i + 1) % 50 == 0:
                    session.commit()
                    insertados = i + 1
                    logger.info(f"Insertados {i + 1} libros...")
            except Exception as e:
                session.rollback()
                errores += 1
                logger.error(f"Error insertando libro {i + 1}: {str(e)}")

        # Commit final
        session.commit()
        insertados = cantidad - errores
    finally:
        session.close()

    logger.info("Proceso completado:")
    logger.info(f"  - Libros insertados: {insertados}")
    logger.info(f"  - Errores: {errores}")

    return insertados, errores

if __name__ == '__main__':
    try:
        # Verificar conexión a la base de datos
        session = SessionLocal()
        try:
            total = session.execute(select(func.count(Libro.id_libro))).scalar_one()
            logger.info(f"Libros actuales en la base de datos: {total}")

            # Poblar con 500 libros
            insertados, errores = poblar_libros(500)

            # Verificar total después de inserción
            total = session.execute(select(func.count(Libro.id_libro))).scalar_one()
            logger.info(f"Total de libros en la base de datos: {total}")
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error fatal: {str(e)}")
        exit(1)
