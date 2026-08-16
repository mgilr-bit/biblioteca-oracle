INSERT INTO usuarios (nombre, email, password, rol) VALUES ('Admin', 'admin@biblioteca.com', '$2b$12$f9OHyufcs1NHqsiPvJirVeMO0NAsIE8KeHFjJL6vwrK0YazSp77la', 'BIBLIOTECARIO');
INSERT INTO usuarios (nombre, email, password, rol) VALUES ('Juan', 'juan@email.com', '$2b$12$pTWZUH7ILOeuEz5qPq.HAOQn5lZ2eHWKX4BRP/GW/UPGDUHAf7fjG', 'LECTOR');
INSERT INTO libros (titulo, autor, isbn, anio_publicacion, genero, numero_copias, copias_disponibles) VALUES ('Cien Anios de Soledad', 'Garcia Marquez', '111', 1967, 'Ficcion', 5, 5);
INSERT INTO libros (titulo, autor, isbn, anio_publicacion, genero, numero_copias, copias_disponibles) VALUES ('1984', 'George Orwell', '222', 1949, 'Ficcion', 3, 3);
COMMIT;
EXIT;