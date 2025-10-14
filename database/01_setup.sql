-- 01_setup.sql
ALTER SESSION SET CONTAINER = XEPDB1;

-- Crear tablespace personalizado
CREATE TABLESPACE PROYECTO_BD
DATAFILE '/opt/oracle/oradata/XE/XEPDB1/proyecto_bd.dbf' SIZE 100M
AUTOEXTEND ON NEXT 10M MAXSIZE 500M;

-- Crear usuario para el proyecto
CREATE USER biblioteca_user IDENTIFIED BY BiblioPass123
DEFAULT TABLESPACE PROYECTO_BD
TEMPORARY TABLESPACE TEMP
QUOTA UNLIMITED ON PROYECTO_BD;

-- Otorgar permisos necesarios
GRANT CONNECT, RESOURCE TO biblioteca_user;
GRANT CREATE SESSION TO biblioteca_user;
GRANT CREATE TABLE TO biblioteca_user;
GRANT CREATE VIEW TO biblioteca_user;
GRANT CREATE SEQUENCE TO biblioteca_user;
GRANT CREATE TRIGGER TO biblioteca_user;
GRANT UNLIMITED TABLESPACE TO biblioteca_user;

EXIT;
