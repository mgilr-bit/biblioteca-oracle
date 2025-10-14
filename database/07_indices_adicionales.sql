-- 07_indices_adicionales.sql
-- Agregar índices adicionales para mejorar el rendimiento

-- Índice en email de usuarios (usado en login)
CREATE INDEX idx_usuarios_email ON usuarios(email);

-- Índice compuesto para búsquedas de préstamos
CREATE INDEX idx_prestamos_fecha_estado ON prestamos(fecha_devolucion_esperada, estado);

COMMIT;
EXIT;
