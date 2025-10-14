"""
Script para inicializar datos en la base de datos con contraseñas hasheadas
Ejecutar con: python init_data.py
"""
from config.database import db
from utils.security import hash_password

def init_usuarios():
    """Insertar usuarios iniciales con contraseñas hasheadas"""
    usuarios = [
        ("Admin Biblioteca", "admin@biblioteca.com", "admin123", "BIBLIOTECARIO"),
        ("Juan Perez", "juan@email.com", "lector123", "LECTOR"),
        ("Maria Garcia", "maria@email.com", "lector123", "LECTOR")
    ]

    try:
        # Limpiar tabla
        db.execute_query("DELETE FROM usuarios", fetch=False)

        # Insertar usuarios con contraseñas hasheadas
        query = """
            INSERT INTO usuarios (nombre, email, password, rol)
            VALUES (:nombre, :email, :password, :rol)
        """

        for nombre, email, password, rol in usuarios:
            hashed_password = hash_password(password)
            db.execute_query(
                query,
                {
                    "nombre": nombre,
                    "email": email,
                    "password": hashed_password,
                    "rol": rol
                },
                fetch=False
            )
            print(f"  ✓ Usuario creado: {email} (contraseña hasheada)")

        print(f"\n✓ Total: {len(usuarios)} usuarios insertados")
    except Exception as e:
        print(f"✗ Error insertando usuarios: {e}")

def init_libros():
    """Insertar libros iniciales"""
    libros = [
        ("Cien Anios de Soledad", "Gabriel Garcia Marquez", "978-0307474728", 1967, "Realismo Magico", 5, 5, "Editorial Sudamericana"),
        ("1984", "George Orwell", "978-0451524935", 1949, "Distopia", 3, 3, "Secker and Warburg"),
        ("El Principito", "Antoine de Saint-Exupery", "978-0156012195", 1943, "Fabula", 7, 7, "Reynal and Hitchcock"),
        ("Don Quijote de la Mancha", "Miguel de Cervantes", "978-8424194093", 1950, "Novela", 4, 4, "Francisco de Robles"),
        ("Rayuela", "Julio Cortazar", "978-8437604572", 1963, "Novela Experimental", 2, 2, "Editorial Sudamericana"),
        ("La Sombra del Viento", "Carlos Ruiz Zafon", "978-8408043640", 2001, "Misterio", 6, 6, "Editorial Planeta"),
        ("Los Detectives Salvajes", "Roberto Bolano", "978-8433920850", 1998, "Novela", 3, 3, "Editorial Anagrama"),
        ("Pedro Paramo", "Juan Rulfo", "978-0802133908", 1955, "Realismo Magico", 4, 4, "Fondo de Cultura Economica"),
        ("Ficciones", "Jorge Luis Borges", "978-0802130303", 1944, "Cuentos", 5, 5, "Editorial Sur"),
        ("El Aleph", "Jorge Luis Borges", "978-8499089515", 1949, "Cuentos", 4, 4, "Editorial Losada")
    ]
    
    try:
        # Limpiar tabla
        db.execute_query("DELETE FROM libros", fetch=False)
        
        # Insertar libros
        query = """
            INSERT INTO libros (titulo, autor, isbn, anio_publicacion, genero, 
                              numero_copias, copias_disponibles, editorial)
            VALUES (:1, :2, :3, :4, :5, :6, :7, :8)
        """
        
        for libro in libros:
            db.execute_query(query, libro, fetch=False)
        
        print(f"✓ {len(libros)} libros insertados")
    except Exception as e:
        print(f"✗ Error insertando libros: {e}")

def main():
    """Función principal"""
    print("=== Iniciando inserción de datos ===\n")
    
    try:
        # Verificar conexión
        conn = db.get_connection()
        conn.close()
        print("✓ Conexión a la base de datos exitosa\n")
        
        # Insertar datos
        init_usuarios()
        init_libros()
        
        print("\n=== Datos inicializados correctamente ===")
        
        # Mostrar resumen
        usuarios_count = db.execute_query("SELECT COUNT(*) as count FROM usuarios")[0]['COUNT']
        libros_count = db.execute_query("SELECT COUNT(*) as count FROM libros")[0]['COUNT']
        
        print(f"\nResumen:")
        print(f"  - Usuarios: {usuarios_count}")
        print(f"  - Libros: {libros_count}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")

if __name__ == "__main__":
    main()

