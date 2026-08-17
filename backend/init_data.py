"""
Script para inicializar datos en la base de datos con contraseñas hasheadas
Ejecutar con: python init_data.py
"""
from sqlalchemy import delete, text

from config.database import SessionLocal
from models.libro import Libro
from models.prestamo import Prestamo
from models.usuario import Usuario
from utils.security import hash_password

USUARIOS = [
    ("Admin Biblioteca", "admin@biblioteca.com", "admin123", "BIBLIOTECARIO"),
    ("Juan Perez", "juan@email.com", "lector123", "LECTOR"),
    ("Maria Garcia", "maria@email.com", "lector123", "LECTOR"),
]

LIBROS = [
    ("Cien Anios de Soledad", "Gabriel Garcia Marquez", "978-0307474728", 1967, "Realismo Magico", 5, "Editorial Sudamericana"),
    ("1984", "George Orwell", "978-0451524935", 1949, "Distopia", 3, "Secker and Warburg"),
    ("El Principito", "Antoine de Saint-Exupery", "978-0156012195", 1943, "Fabula", 7, "Reynal and Hitchcock"),
    ("Don Quijote de la Mancha", "Miguel de Cervantes", "978-8424194093", 1950, "Novela", 4, "Francisco de Robles"),
    ("Rayuela", "Julio Cortazar", "978-8437604572", 1963, "Novela Experimental", 2, "Editorial Sudamericana"),
    ("La Sombra del Viento", "Carlos Ruiz Zafon", "978-8408043640", 2001, "Misterio", 6, "Editorial Planeta"),
    ("Los Detectives Salvajes", "Roberto Bolano", "978-8433920850", 1998, "Novela", 3, "Editorial Anagrama"),
    ("Pedro Paramo", "Juan Rulfo", "978-0802133908", 1955, "Realismo Magico", 4, "Fondo de Cultura Economica"),
    ("Ficciones", "Jorge Luis Borges", "978-0802130303", 1944, "Cuentos", 5, "Editorial Sur"),
    ("El Aleph", "Jorge Luis Borges", "978-8499089515", 1949, "Cuentos", 4, "Editorial Losada"),
]


def init_usuarios(session):
    """Insertar usuarios iniciales con contraseñas hasheadas"""
    for nombre, email, password, rol in USUARIOS:
        session.add(
            Usuario(
                nombre=nombre,
                email=email,
                password=hash_password(password),
                rol=rol,
            )
        )
        print(f"  ✓ Usuario creado: {email} (contraseña hasheada)")

    print(f"\n✓ Total: {len(USUARIOS)} usuarios insertados")


def init_libros(session):
    """Insertar libros iniciales"""
    for titulo, autor, isbn, anio, genero, copias, editorial in LIBROS:
        session.add(
            Libro(
                titulo=titulo,
                autor=autor,
                isbn=isbn,
                anio_publicacion=anio,
                genero=genero,
                numero_copias=copias,
                copias_disponibles=copias,
                editorial=editorial,
            )
        )

    print(f"✓ {len(LIBROS)} libros insertados")


def main():
    """Función principal"""
    print("=== Iniciando inserción de datos ===\n")

    session = SessionLocal()
    try:
        # Verificar conexión
        session.execute(text("SELECT 1 FROM DUAL"))
        print("✓ Conexión a la base de datos exitosa\n")

        # Limpiar tablas (en orden por las claves foráneas)
        session.execute(delete(Prestamo))
        session.execute(delete(Libro))
        session.execute(delete(Usuario))

        init_usuarios(session)
        init_libros(session)
        session.commit()

        print("\n=== Datos inicializados correctamente ===")
    except Exception as e:
        session.rollback()
        print(f"\n✗ Error: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
