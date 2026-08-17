#!/bin/sh
set -e

echo "==> [backend] Esperando conexion a Oracle ($DB_HOST:$DB_PORT/$DB_SERVICE)..."

if ! python - <<'PY'
import oracledb, os, sys, time

dsn = f"{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_SERVICE']}"
for _ in range(120):
    try:
        conn = oracledb.connect(
            user=os.environ['DB_USER'],
            password=os.environ['DB_PASSWORD'],
            dsn=dsn,
        )
        cur = conn.cursor()
        cur.execute("SELECT table_name FROM user_tables WHERE table_name = 'USUARIOS'")
        if cur.fetchone():
            print("==> [backend] Conexion OK y esquema listo")
            sys.exit(0)
        conn.close()
    except Exception:
        pass
    time.sleep(5)
print("==> [backend] ERROR: no se pudo conectar a la base de datos")
sys.exit(1)
PY
then
    exit 1
fi

echo "==> [backend] Verificando datos iniciales..."

if python - <<'PY'
import oracledb, os, sys

dsn = f"{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_SERVICE']}"
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
    echo "==> [backend] Cargando datos semilla (init_data.py)..."
    python init_data.py
else
    echo "==> [backend] Datos ya presentes, omitiendo init_data.py"
fi

echo "==> [backend] Iniciando servidor..."
if [ "${FLASK_DEBUG:-False}" = "True" ] || [ "${FLASK_DEBUG:-false}" = "true" ]; then
    echo "==> [backend] Modo desarrollo (hot-reload)"
    exec flask --app app run --debug --host 0.0.0.0 --port "${PORT:-5000}"
fi
exec gunicorn --bind 0.0.0.0:"${PORT:-5000}" app:app
