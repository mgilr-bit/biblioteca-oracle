FROM python:3.12-slim

# UV_PROJECT_ENVIRONMENT saca el venv de /app a propósito: docker-compose
# monta ./backend:/app para hot-reload en dev, y ese bind-mount taparía
# (y en el host no existe) cualquier .venv creado dentro de /app.
ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# Binario oficial de uv (gestor de dependencias), sin instalar nada via pip.
COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /uvx /bin/

WORKDIR /app

# Instala dependencias primero (capa cacheable) usando el lockfile — antes
# de copiar el codigo fuente, para que un cambio en el codigo no invalide
# la cache de dependencias.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY . .
RUN uv sync --frozen

RUN chmod +x /app/entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["/bin/sh", "/app/entrypoint.sh"]
