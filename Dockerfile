FROM astral/uv:debian
WORKDIR /app
# stdout isn't a TTY in a container, so Python block-buffers it and the
# services' print() logs (job errors included) never reach the platform logs.
ENV PYTHONUNBUFFERED=1
COPY backend/ backend/
COPY pyproject.toml .
# Without it uv picks the newest Python requires-python allows, which can run
# ahead of the wheels our dependencies publish (psycopg-binary on 3.15).
COPY .python-version .
COPY uv.lock .
RUN uv sync
