# syntax=docker/dockerfile:1
ARG NODE_IMAGE=node:22-bookworm-slim
ARG PYTHON_IMAGE=python:3.11-slim-bookworm

FROM ${NODE_IMAGE} AS frontend
WORKDIR /build
COPY frontend/Admin/package.json frontend/Admin/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/Admin/src/assets ./src/assets
COPY frontend/Admin/vite.pen.config.js frontend/Admin/package-libs-config.json ./
COPY docker/build-frontend.mjs ./build-frontend.mjs
RUN node build-frontend.mjs && npx --no-install vite build --config vite.pen.config.js

FROM ${PYTHON_IMAGE} AS python-dependencies
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
WORKDIR /build
RUN python -m venv /opt/venv
COPY requirements.txt requirements-docker.txt ./
RUN /opt/venv/bin/pip install -r requirements-docker.txt && /opt/venv/bin/pip check

FROM ${PYTHON_IMAGE} AS runtime
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=pen.settings
RUN sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends libmagic1 ca-certificates tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 pen \
    && useradd --uid 10001 --gid pen --create-home pen
WORKDIR /app
COPY --from=python-dependencies /opt/venv /opt/venv
COPY --chown=pen:pen manage.py ./
COPY --chown=pen:pen pen ./pen
COPY --chown=pen:pen apps ./apps
COPY --chown=pen:pen frontend/Admin/pen-templates ./frontend/Admin/pen-templates
COPY --from=frontend --chown=pen:pen /build/src/assets ./frontend/Admin/src/assets
COPY --chown=pen:pen docker/gunicorn.conf.py docker/healthcheck.py ./docker/
RUN mkdir -p /app/media /app/staticfiles /app/run \
    && chown pen:pen /app/media /app/staticfiles /app/run
USER pen
EXPOSE 8000
CMD ["gunicorn", "--config", "docker/gunicorn.conf.py", "pen.wsgi:application"]
