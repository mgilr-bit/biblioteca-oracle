-- 09_cron_jobs.sql
-- Job automático de mantenimiento (fase 4 del plan): recordatorios de
-- devolución, avisos de vencimiento y expiración de reservas CUMPLIDA.
--
-- Es el respaldo en BD del mantenimiento que también expone el backend en
-- `PUT /api/notificaciones/mantenimiento` (NotificacionService.ejecutar_mantenimiento).
-- Si el backend corre todos los días, este job puede dejarse deshabilitado;
-- si no, conviene habilitarlo para no depender del proceso de la API.
--
-- Idempotente: usa NOT EXISTS para no duplicar notificaciones.

-- ========================================
-- 1. PROCEDIMIENTO DE MANTENIMIENTO
-- ========================================
CREATE OR REPLACE PROCEDURE ejecutar_cron_biblioteca IS
    v_avisos NUMBER := 0;
BEGIN
    -- (a) Recordatorios a 3 días y el mismo día (préstamos ACTIVO no vencidos).
    INSERT INTO notificaciones (id_usuario, tipo, mensaje, leida, created_by)
    SELECT p.id_usuario,
           CASE WHEN TRUNC(SYSDATE) = TRUNC(p.fecha_devolucion_esperada)
                THEN 'RECORDATORIO_HOY' ELSE 'RECORDATORIO_3D' END,
           CASE WHEN TRUNC(SYSDATE) = TRUNC(p.fecha_devolucion_esperada)
                THEN 'Su prestamo #' || p.id_prestamo || ' vence HOY. Devuélvalo a tiempo para evitar multas.'
                ELSE 'El prestamo #' || p.id_prestamo || ' vence en 3 dias. Recuerde devolverlo a tiempo.' END,
               0,
           'cron'
      FROM prestamos p
     WHERE p.estado = 'ACTIVO'
       AND p.fecha_devolucion_esperada >= SYSDATE
       AND p.fecha_devolucion_esperada <= SYSDATE + 3
       AND NOT EXISTS (
           SELECT 1 FROM notificaciones n
            WHERE n.id_usuario = p.id_usuario
              AND n.tipo IN ('RECORDATORIO_HOY', 'RECORDATORIO_3D')
              AND n.mensaje LIKE '%#' || p.id_prestamo || '%'
       );
    v_avisos := v_avisos + SQL%ROWCOUNT;

    -- (b) Avisos de vencimiento (préstamos ACTIVO ya vencidos).
    INSERT INTO notificaciones (id_usuario, tipo, mensaje, leida, created_by)
    SELECT p.id_usuario,
           'VENCIDO',
           'Su prestamo #' || p.id_prestamo || ' lleva '
               || (TRUNC(SYSDATE) - TRUNC(p.fecha_devolucion_esperada))
               || ' dia(s) de retraso. Devuélvalo para evitar una multa.',
           0,
           'cron'
      FROM prestamos p
     WHERE p.estado = 'ACTIVO'
       AND p.fecha_devolucion_esperada < SYSDATE
       AND NOT EXISTS (
           SELECT 1 FROM notificaciones n
            WHERE n.id_usuario = p.id_usuario
              AND n.tipo = 'VENCIDO'
              AND n.mensaje LIKE '%#' || p.id_prestamo || '%'
       );
    v_avisos := v_avisos + SQL%ROWCOUNT;

    -- (c) Expirar reservas CUMPLIDA cuya ventana de recogida ya venció.
    UPDATE reservas
       SET estado = 'EXPIRADA', updated_by = 'cron', updated_at = SYSTIMESTAMP
     WHERE estado = 'CUMPLIDA'
       AND fecha_expiracion IS NOT NULL
       AND fecha_expiracion < SYSDATE;

    COMMIT;

    DBMS_OUTPUT.PUT_LINE('Notificaciones generadas: ' || v_avisos);
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE;
END;
/

-- ========================================
-- 2. JOB DIARIO (00:00). Descomentar para activar.
-- ========================================
/*
BEGIN
    DBMS_SCHEDULER.DROP_JOB('JOB_CRON_BIBLIOTECA');
EXCEPTION
    WHEN OTHERS THEN NULL;
END;
/

BEGIN
    DBMS_SCHEDULER.CREATE_JOB (
        job_name        => 'JOB_CRON_BIBLIOTECA',
        job_type        => 'PLSQL_BLOCK',
        job_action      => 'BEGIN ejecutar_cron_biblioteca; END;',
        start_date      => SYSTIMESTAMP,
        repeat_interval => 'FREQ=DAILY; BYHOUR=0; BYMINUTE=0',
        enabled         => TRUE,
        comments        => 'Job diario: recordatorios, vencidos y expiracion de reservas'
    );
END;
/
*/

COMMIT;
EXIT;