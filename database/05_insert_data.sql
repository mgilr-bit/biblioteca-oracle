SET DEFINE OFF;
DELETE FROM prestamos;
DELETE FROM libros;
DELETE FROM usuarios;

INSERT INTO usuarios (nombre, email, password, rol) VALUES ('Admin Biblioteca', 'admin@biblioteca.com', 'admin123', 'BIBLIOTECARIO');
INSERT INTO usuarios (nombre, email, password, rol) VALUES ('Juan Perez', 'juan@email.com', 'lector123', 'LECTOR');
INSERT INTO usuarios (nombre, email, password, rol) VALUES ('Maria Garcia', 'maria@email.com', 'lector123', 'LECTOR');

INSERT INTO libros (titulo, autor, isbn, anio_publicacion, genero, numero_copias, copias_disponibles, editorial) VALUES ('Cien Anios de Soledad', 'Gabriel Garcia Marquez', '978-0307474728', 1967, 'Realismo Magico', 5, 5, 'Editorial Sudamericana');
INSERT INTO libros (titulo, autor, isbn, anio_publicacion, genero, numero_copias, copias_disponibles, editorial) VALUES ('1984', 'George Orwell', '978-0451524935', 1949, 'Distopia', 3, 3, 'Secker and Warburg');
INSERT INTO libros (titulo, autor, isbn, anio_publicacion, genero, numero_copias, copias_disponibles, editorial) VALUES ('El Principito', 'Antoine de Saint-Exupery', '978-0156012195', 1943, 'Fabula', 7, 7, 'Reynal and Hitchcock');
INSERT INTO libros (titulo, autor, isbn, anio_publicacion, genero, numero_copias, copias_disponibles, editorial) VALUES ('Don Quijote de la Mancha', 'Miguel de Cervantes', '978-8424194093', 1605, 'Novela', 4, 4, 'Francisco de Robles');
INSERT INTO libros (titulo, autor, isbn, anio_publicacion, genero, numero_copias, copias_disponibles, editorial) VALUES ('Rayuela', 'Julio Cortazar', '978-8437604572', 1963, 'Novela Experimental', 2, 2, 'Editorial Sudamericana');

COMMIT;
EXIT;
