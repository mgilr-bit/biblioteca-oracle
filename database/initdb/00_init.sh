#!/bin/sh
# Inicializacion del esquema de la Biblioteca (se ejecuta en el primer arranque
# del contenedor de Oracle, en el contexto del entrypoint de gvenzl/oracle-xe).
#
# NOTA: este script es montado como volumen, por lo que en hosts Windows no
# posee el bit de ejecucion y es "sourced" por el entrypoint. Por eso NO debe
# contener sentencias `exit`, ya que abortarian el entrypoint del contenedor.

echo "==> [biblio] 01_setup.sql: creando tablespace y usuario"
sqlplus -S -L sys/"$ORACLE_PASSWORD" as sysdba @/opt/proyecto-sql/01_setup.sql

echo "==> [biblio] 02_tables.sql: creando tablas"
sqlplus -S -L biblioteca_user/BiblioPass123@//localhost:1521/XEPDB1 @/opt/proyecto-sql/02_tables.sql

echo "==> [biblio] 03_triggers.sql: creando triggers"
sqlplus -S -L biblioteca_user/BiblioPass123@//localhost:1521/XEPDB1 @/opt/proyecto-sql/03_triggers.sql

echo "==> [biblio] 07_indices_adicionales.sql: creando indices"
sqlplus -S -L biblioteca_user/BiblioPass123@//localhost:1521/XEPDB1 @/opt/proyecto-sql/07_indices_adicionales.sql

echo "==> [biblio] Inicializacion de esquema completada"
