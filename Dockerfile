FROM astral/uv:debian
WORKDIR /app
COPY backend/ backend/
COPY pyproject.toml .
# Without it uv picks the newest Python requires-python allows, which can run
# ahead of the wheels our dependencies publish (psycopg-binary on 3.15).
COPY .python-version .
COPY uv.lock .
RUN uv sync
