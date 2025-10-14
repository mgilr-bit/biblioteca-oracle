-- 03_triggers.sql
CREATE OR REPLACE TRIGGER trg_prestamo_insert
AFTER INSERT ON prestamos
FOR EACH ROW
BEGIN
    IF :NEW.estado = 'ACTIVO' THEN
        UPDATE libros
        SET copias_disponibles = copias_disponibles - 1
        WHERE id_libro = :NEW.id_libro
        AND copias_disponibles > 0;
    END IF;
END;
/

CREATE OR REPLACE TRIGGER trg_prestamo_devolucion
AFTER UPDATE OF fecha_devolucion_real, estado ON prestamos
FOR EACH ROW
BEGIN
    IF :NEW.estado = 'DEVUELTO' AND :OLD.estado != 'DEVUELTO' THEN
        UPDATE libros
        SET copias_disponibles = copias_disponibles + 1
        WHERE id_libro = :NEW.id_libro;
    END IF;
END;
/

CREATE OR REPLACE TRIGGER trg_validar_disponibilidad
BEFORE INSERT ON prestamos
FOR EACH ROW
DECLARE
    v_disponibles NUMBER;
BEGIN
    SELECT copias_disponibles INTO v_disponibles
    FROM libros
    WHERE id_libro = :NEW.id_libro;
    
    IF v_disponibles <= 0 THEN
        RAISE_APPLICATION_ERROR(-20001, 'No hay copias disponibles de este libro');
    END IF;
END;
/

COMMIT;
EXIT;
