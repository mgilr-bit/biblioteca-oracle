-- 08_mejoras_recomendadas.sql
-- Mejoras adicionales para la base de datos

-- ========================================
-- 1. ÍNDICE EN ISBN (búsquedas más rápidas por ISBN)
-- ========================================
CREATE INDEX idx_libros_isbn ON libros(isbn);

-- ========================================
-- 2. ÍNDICE COMPUESTO PARA PRÉSTAMOS ACTIVOS POR USUARIO
-- ========================================
-- Este índice mejora las consultas del dashboard del lector
CREATE INDEX idx_prestamos_usuario_estado ON prestamos(id_usuario, estado);

-- ========================================
-- 3. ÍNDICE EN FECHA DE PRÉSTAMO
-- ========================================
-- Mejora el filtrado por fecha de préstamo
CREATE INDEX idx_prestamos_fecha ON prestamos(fecha_prestamo);

-- ========================================
-- 4. TABLA DE AUDITORÍA PARA PRÉSTAMOS (OPCIONAL)
-- ========================================
-- Registra cambios en préstamos para trazabilidad
CREATE TABLE auditoria_prestamos (
    id_auditoria NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_prestamo NUMBER NOT NULL,
    accion VARCHAR2(50) NOT NULL, -- 'CREADO', 'DEVUELTO', 'VENCIDO'
    usuario_responsable NUMBER,
    fecha_accion TIMESTAMP DEFAULT SYSTIMESTAMP,
    estado_anterior VARCHAR2(20),
    estado_nuevo VARCHAR2(20),
    observaciones VARCHAR2(500)
) TABLESPACE PROYECTO_BD;

CREATE INDEX idx_auditoria_prestamo ON auditoria_prestamos(id_prestamo);
CREATE INDEX idx_auditoria_fecha ON auditoria_prestamos(fecha_accion);

-- ========================================
-- 5. TRIGGER DE AUDITORÍA (OPCIONAL)
-- ========================================
CREATE OR REPLACE TRIGGER trg_auditoria_prestamos
AFTER INSERT OR UPDATE ON prestamos
FOR EACH ROW
BEGIN
    IF INSERTING THEN
        INSERT INTO auditoria_prestamos (id_prestamo, accion, estado_nuevo)
        VALUES (:NEW.id_prestamo, 'CREADO', :NEW.estado);
    ELSIF UPDATING THEN
        IF :NEW.estado != :OLD.estado THEN
            INSERT INTO auditoria_prestamos (
                id_prestamo,
                accion,
                estado_anterior,
                estado_nuevo
            )
            VALUES (
                :NEW.id_prestamo,
                'CAMBIO_ESTADO',
                :OLD.estado,
                :NEW.estado
            );
        END IF;
    END IF;
END;
/

-- ========================================
-- 6. TABLA DE MULTAS (OPCIONAL - FUNCIONALIDAD FUTURA)
-- ========================================
CREATE TABLE multas (
    id_multa NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_prestamo NUMBER NOT NULL,
    id_usuario NUMBER NOT NULL,
    monto NUMBER(10,2) NOT NULL CHECK (monto >= 0),
    fecha_generacion DATE DEFAULT SYSDATE,
    fecha_pago DATE,
    estado VARCHAR2(20) DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE', 'PAGADA', 'CONDONADA')),
    motivo VARCHAR2(200),
    CONSTRAINT fk_multa_prestamo FOREIGN KEY (id_prestamo) REFERENCES prestamos(id_prestamo) ON DELETE CASCADE,
    CONSTRAINT fk_multa_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
) TABLESPACE PROYECTO_BD;

CREATE INDEX idx_multas_usuario ON multas(id_usuario);
CREATE INDEX idx_multas_estado ON multas(estado);
CREATE INDEX idx_multas_prestamo ON multas(id_prestamo);

-- ========================================
-- 7. TABLA DE RESERVAS (OPCIONAL - FUNCIONALIDAD FUTURA)
-- ========================================
CREATE TABLE reservas (
    id_reserva NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_libro NUMBER NOT NULL,
    id_usuario NUMBER NOT NULL,
    fecha_reserva DATE DEFAULT SYSDATE,
    fecha_expiracion DATE NOT NULL,
    estado VARCHAR2(20) DEFAULT 'ACTIVA' CHECK (estado IN ('ACTIVA', 'CUMPLIDA', 'CANCELADA', 'EXPIRADA')),
    CONSTRAINT fk_reserva_libro FOREIGN KEY (id_libro) REFERENCES libros(id_libro) ON DELETE CASCADE,
    CONSTRAINT fk_reserva_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
) TABLESPACE PROYECTO_BD;

CREATE INDEX idx_reservas_libro_estado ON reservas(id_libro, estado);
CREATE INDEX idx_reservas_usuario ON reservas(id_usuario);

-- ========================================
-- 8. VISTA PARA LIBROS MÁS PRESTADOS
-- ========================================
CREATE OR REPLACE VIEW v_libros_populares AS
SELECT
    l.id_libro,
    l.titulo,
    l.autor,
    l.genero,
    COUNT(p.id_prestamo) as total_prestamos,
    COUNT(CASE WHEN p.estado = 'ACTIVO' THEN 1 END) as prestamos_activos
FROM libros l
LEFT JOIN prestamos p ON l.id_libro = p.id_libro
GROUP BY l.id_libro, l.titulo, l.autor, l.genero
ORDER BY total_prestamos DESC;

-- ========================================
-- 9. VISTA PARA USUARIOS CON PRÉSTAMOS VENCIDOS
-- ========================================
CREATE OR REPLACE VIEW v_usuarios_morosos AS
SELECT
    u.id_usuario,
    u.nombre,
    u.email,
    COUNT(p.id_prestamo) as prestamos_vencidos,
    MIN(p.fecha_devolucion_esperada) as fecha_vencimiento_mas_antiguo
FROM usuarios u
INNER JOIN prestamos p ON u.id_usuario = p.id_usuario
WHERE p.estado = 'ACTIVO'
  AND p.fecha_devolucion_esperada < SYSDATE
GROUP BY u.id_usuario, u.nombre, u.email
ORDER BY prestamos_vencidos DESC;

-- ========================================
-- 10. FUNCIÓN PARA CALCULAR MULTA POR DÍAS DE RETRASO
-- ========================================
CREATE OR REPLACE FUNCTION calcular_multa(
    p_id_prestamo NUMBER,
    p_tarifa_diaria NUMBER DEFAULT 1.00
) RETURN NUMBER IS
    v_dias_retraso NUMBER;
    v_multa NUMBER;
    v_fecha_esperada DATE;
    v_fecha_real DATE;
    v_estado VARCHAR2(20);
BEGIN
    SELECT fecha_devolucion_esperada, fecha_devolucion_real, estado
    INTO v_fecha_esperada, v_fecha_real, v_estado
    FROM prestamos
    WHERE id_prestamo = p_id_prestamo;

    -- Si está activo, usar fecha actual
    IF v_estado = 'ACTIVO' THEN
        v_fecha_real := SYSDATE;
    END IF;

    -- Calcular días de retraso
    v_dias_retraso := TRUNC(v_fecha_real) - TRUNC(v_fecha_esperada);

    -- Solo multa si hay retraso
    IF v_dias_retraso > 0 THEN
        v_multa := v_dias_retraso * p_tarifa_diaria;
    ELSE
        v_multa := 0;
    END IF;

    RETURN v_multa;
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        RETURN 0;
END;
/

-- ========================================
-- 11. PROCEDIMIENTO PARA ACTUALIZAR PRÉSTAMOS VENCIDOS
-- ========================================
CREATE OR REPLACE PROCEDURE actualizar_prestamos_vencidos IS
    v_count NUMBER;
BEGIN
    UPDATE prestamos
    SET estado = 'VENCIDO'
    WHERE estado = 'ACTIVO'
      AND fecha_devolucion_esperada < SYSDATE;

    v_count := SQL%ROWCOUNT;

    DBMS_OUTPUT.PUT_LINE('Préstamos actualizados a VENCIDO: ' || v_count);
    COMMIT;
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE;
END;
/

-- ========================================
-- 12. JOB AUTOMÁTICO PARA ACTUALIZAR VENCIDOS (OPCIONAL)
-- ========================================
-- Este job se ejecuta diariamente a las 00:00
-- Comentado por defecto - descomentar si se desea activar
/*
BEGIN
    DBMS_SCHEDULER.CREATE_JOB (
        job_name        => 'JOB_ACTUALIZAR_VENCIDOS',
        job_type        => 'PLSQL_BLOCK',
        job_action      => 'BEGIN actualizar_prestamos_vencidos; END;',
        start_date      => SYSTIMESTAMP,
        repeat_interval => 'FREQ=DAILY; BYHOUR=0; BYMINUTE=0',
        enabled         => TRUE,
        comments        => 'Job para actualizar préstamos vencidos diariamente'
    );
END;
/
*/

-- ========================================
-- 13. AÑADIR COLUMNA DE DESCRIPCIÓN A LIBROS (OPCIONAL)
-- ========================================
-- ALTER TABLE libros ADD (descripcion VARCHAR2(1000));
-- CREATE INDEX idx_libros_descripcion ON libros(descripcion);

-- ========================================
-- 14. RESTRICCIÓN ADICIONAL: UN USUARIO NO PUEDE TENER EL MISMO LIBRO PRESTADO DOS VECES
-- ========================================
CREATE UNIQUE INDEX idx_prestamo_unico
ON prestamos(id_usuario, id_libro)
WHERE estado = 'ACTIVO';

COMMIT;
EXIT;
