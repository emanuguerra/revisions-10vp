# Production image (Fly.io): the built React app served by the FastAPI backend, one container.
# Local development keeps using docker-compose.yml (Vite dev server + backend).

# 1. Build the frontend
FROM node:22-alpine AS frontend
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# 2. Backend + built frontend
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.10.12 /uv /usr/local/bin/uv

WORKDIR /app/backend
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv PATH="/opt/venv/bin:$PATH"

COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev

COPY backend/ ./
COPY content/ /app/content/
COPY --from=frontend /app/dist /app/static
ENV CONTENT_DIR=/app/content DATA_DIR=/data STATIC_DIR=/app/static

EXPOSE 8010
# Apply migrations, load content, start the API (which also serves the app)
CMD ["sh", "-c", "alembic upgrade head && python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port 8010 --proxy-headers --forwarded-allow-ips='*'"]
