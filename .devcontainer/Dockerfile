FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git curl ca-certificates gnupg lsb-release \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends docker-ce-cli docker-compose-plugin \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# uv gestiona las dependencias del backend (pyproject.toml/uv.lock); se
# instalan en el Python del sistema (--system) para que el devcontainer
# siga funcionando "listo para usar" sin activar un venv por proyecto.
RUN pip install --no-cache-dir uv

COPY backend/pyproject.toml backend/uv.lock /tmp/backend/
RUN cd /tmp/backend \
    && uv export --frozen --no-hashes -o requirements.lock.txt \
    && uv pip install --system -r requirements.lock.txt

ENV SHELL=/bin/bash
