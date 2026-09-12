FROM astral/uv:debian
WORKDIR /app
COPY backend/ backend/
COPY pyproject.toml .
COPY uv.lock .
RUN uv sync
