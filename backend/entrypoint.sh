#!/bin/sh
set -e

echo "==> [backend] Esperando conexion a Oracle (${DB_DSN:-$DB_HOST:$DB_PORT/$DB_SERVICE})..."

if ! python - <<'PY'
import oracledb, os, sys, time

from config.oracle_dsn import get_dsn

dsn = get_dsn()
last_error = None
for intento in range(1, 61):
    try:
        conn = oracledb.connect(
            user=os.environ['DB_USER'],
            password=os.environ['DB_PASSWORD'],
            dsn=dsn,
        )
        conn.cursor().execute("SELECT 1 FROM DUAL")
        conn.close()
        print("==> [backend] Conexion a Oracle OK")
        sys.exit(0)
    except Exception as e:  # noqa: BLE001
        last_error = e
        # Imprime el error real en el 1er intento y luego cada 5, para no
        # quedarse "esperando" en silencio si las credenciales/ACL/DSN fallan.
        if intento == 1 or intento % 5 == 0:
            print(f"==> [backend] intento {intento}/60 fallo: {type(e).__name__}: {e}")
    time.sleep(5)
print(f"==> [backend] ERROR: no se pudo conectar a la base de datos: {last_error}")
sys.exit(1)
PY
then
    exit 1
fi

echo "==> [backend] Verificando que el esquema base exista..."
if ! python - <<'PY'
import oracledb, os, sys

from config.oracle_dsn import get_dsn

conn = oracledb.connect(
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASSWORD'],
    dsn=get_dsn(),
)
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = 'USUARIOS'")
if cur.fetchone()[0]:
    sys.exit(0)
print("==> [backend] ERROR: la tabla USUARIOS no existe en este esquema.")
print("==> [backend] Carga primero database/*.sql (02_tables.sql, 03_triggers.sql, ...)")
print("==> [backend] en la base de la nube antes de levantar el backend.")
sys.exit(1)
PY
then
    exit 1
fi

echo "==> [backend] Verificando estado de Alembic..."
if [ -z "$(python -m alembic current 2>/dev/null)" ]; then
    echo "==> [backend] Primer arranque: alembic stamp 0001 (el schema base ya existe, creado por database/*.sql)"
    python -m alembic stamp 0001
fi
echo "==> [backend] Aplicando migraciones pendientes (alembic upgrade head)..."
python -m alembic upgrade head

echo "==> [backend] Verificando datos iniciales..."

if python - <<'PY'
import oracledb, os, sys

from config.oracle_dsn import get_dsn

dsn = get_dsn()
conn = oracledb.connect(
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASSWORD'],
    dsn=dsn,
)
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM usuarios")
sys.exit(0 if cur.fetchone()[0] == 0 else 1)
PY
then
    echo "==> [backend] Cargando datos semilla (seed.py)..."
    python seed.py || echo "==> [backend] seed.py omitido (ver mensaje anterior)"
else
    echo "==> [backend] Datos ya presentes, omitiendo seed.py"
fi

echo "==> [backend] Iniciando servidor..."
if [ "${ENV:-development}" = "development" ]; then
    echo "==> [backend] Modo desarrollo (hot-reload)"
    exec uvicorn main:app --reload --host 0.0.0.0 --port "${PORT:-5000}"
fi
exec gunicorn -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:"${PORT:-5000}" main:app
