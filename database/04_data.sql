-- 04_data.sql
SET DEFINE OFF;

INSERT INTO usuarios (nombre, email, password, rol) 
VALUES ('Admin Biblioteca', 'admin@biblioteca.com', 'admin123', 'BIBLIOTECARIO');

INSERT INTO usuarios (nombre, email, password, rol) 
VALUES ('Juan Pérez', 'juan@email.com', 'lector123', 'LECTOR');

INSERT INTO usuarios (nombre, email, password, rol) 
VALUES ('María García', 'maria@email.com', 'lector123', 'LECTOR');

INSERT INTO libros (titulo, autor, isbn, anio_publicacion, genero, numero_copias, copias_disponibles, editorial)
VALUES ('Cien Años de Soledad', 'Gabriel García Márquez', '978-0307474728', 1967, 'Realismo Mágico', 5, 5, 'Editorial Sudamericana');

INSERT INTO libros (titulo, autor, isbn, anio_publicacion, genero, numero_copias, copias_disponibles, editorial)
VALUES ('1984', 'George Orwell', '978-0451524935', 1949, 'Distopía', 3, 3, 'Secker & Warburg');

INSERT INTO libros (titulo, autor, isbn, anio_publicacion, genero, numero_copias, copias_disponibles, editorial)
VALUES ('El Principito', 'Antoine de Saint-Exupéry', '978-0156012195', 1943, 'Fábula', 7, 7, 'Reynal & Hitchcock');

INSERT INTO libros (titulo, autor, isbn, anio_publicacion, genero, numero_copias, copias_disponibles, editorial)
VALUES ('Don Quijote de la Mancha', 'Miguel de Cervantes', '978-8424194093', 1605, 'Novela', 4, 4, 'Francisco de Robles');

INSERT INTO libros (titulo, autor, isbn, anio_publicacion, genero, numero_copias, copias_disponibles, editorial)
VALUES ('Rayuela', 'Julio Cortázar', '978-8437604572', 1963, 'Novela Experimental', 2, 2, 'Editorial Sudamericana');

INSERT INTO libros (titulo, autor, isbn, anio_publicacion, genero, numero_copias, copias_disponibles, editorial)
VALUES ('La Sombra del Viento', 'Carlos Ruiz Zafón', '978-8408043640', 2001, 'Misterio', 6, 6, 'Editorial Planeta');

INSERT INTO libros (titulo, autor, isbn, anio_publicacion, genero, numero_copias, copias_disponibles, editorial)
VALUES ('Los Detectives Salvajes', 'Roberto Bolaño', '978-8433920850', 1998, 'Novela', 3, 3, 'Editorial Anagrama');

INSERT INTO libros (titulo, autor, isbn, anio_publicacion, genero, numero_copias, copias_disponibles, editorial)
VALUES ('Pedro Páramo', 'Juan Rulfo', '978-0802133908', 1955, 'Realismo Mágico', 4, 4, 'Fondo de Cultura Económica');

COMMIT;
EXIT;
