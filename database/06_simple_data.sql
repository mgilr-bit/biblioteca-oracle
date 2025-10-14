INSERT INTO usuarios (nombre, email, password, rol) VALUES ('Admin', 'admin@biblioteca.com', 'admin123', 'BIBLIOTECARIO');
INSERT INTO usuarios (nombre, email, password, rol) VALUES ('Juan', 'juan@email.com', 'lector123', 'LECTOR');
INSERT INTO libros (titulo, autor, isbn, anio_publicacion, genero, numero_copias, copias_disponibles) VALUES ('Cien Anios de Soledad', 'Garcia Marquez', '111', 1967, 'Ficcion', 5, 5);
INSERT INTO libros (titulo, autor, isbn, anio_publicacion, genero, numero_copias, copias_disponibles) VALUES ('1984', 'George Orwell', '222', 1949, 'Ficcion', 3, 3);
COMMIT;
EXIT;
