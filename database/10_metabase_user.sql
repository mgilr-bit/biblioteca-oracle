-- 10_metabase_user.sql
-- Usuario de SOLO LECTURA para Metabase (estadísticas / BI).
--
-- Metabase solo consulta: por eso nada de DML/DDL, unicamente:
--   * CONNECT / CREATE SESSION      -> puede iniciar sesión.
--   * SELECT ANY TABLE              -> puede leer cualquier tabla, vista o
--       vista materializada del esquema biblioteca_user, incluyendo las
--       que creen las migraciones posteriores (multas, auditoria, V_OLAP_*).
--
-- Se ejecuta como sysdba dentro de XEPDB1 al primer arranque (initdb).
-- Idempotente: si el usuario ya existe no lo duplica.
ALTER SESSION SET CONTAINER = XEPDB1;

DECLARE
    v_count NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_count FROM all_users WHERE username = 'METABASE_USER';
    IF v_count = 0 THEN
        EXECUTE IMMEDIATE 'CREATE USER metabase_user IDENTIFIED BY MetabaseAnalytics123 '
            || 'DEFAULT TABLESPACE PROYECTO_BD TEMPORARY TABLESPACE TEMP QUOTA 10M ON PROYECTO_BD';
    END IF;
END;
/

GRANT CONNECT, CREATE SESSION TO metabase_user;
GRANT SELECT ANY TABLE TO metabase_user;

EXIT;