# Stage 1: build the virtual environment with uv.
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.13.0 /uv /uvx /bin/

# No development dependencies, and use this image's Python rather than downloading one.
ENV UV_NO_DEV=1 \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Dependencies first, so this layer is reused while only the code changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project --no-editable

# Then the package itself, installed as a real copy so the source is not needed at run time.
COPY src ./src
RUN uv sync --locked --no-editable

# Stage 2: run it. No uv, no source code, no build tools.
FROM python:3.12-slim

RUN useradd --create-home app
WORKDIR /app
COPY --from=builder /app/.venv ./.venv
COPY config ./config
COPY resources/models ./resources/models
# SQLite writes here, so the non-root user must own it.
RUN mkdir storage && chown app:app storage

USER app
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uvicorn", "--factory", "job_processor.main:create_app", "--host", "0.0.0.0", "--port", "8000"]
