# Borusan AI Ecosystem CRM - backend (FastAPI)
#
# Build from the REPOSITORY ROOT (the image needs backend/ and config/):
#   docker build -f backend/Dockerfile -t borusan-crm-backend .
# Run:
#   docker run --env-file backend/.env -p 8001:8001 borusan-crm-backend
# Apply migrations (explicit deploy step, not at container start):
#   docker run --env-file backend/.env borusan-crm-backend python -m alembic upgrade head
#
# No secrets are baked into the image; all configuration is provided at
# runtime through environment variables (see backend/.env.example).

# ---- builder: compile wheels so the runtime stage needs no compilers ----
FROM python:3.12-slim AS builder

WORKDIR /build
COPY backend/requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ---- runtime ----
FROM python:3.12-slim

# Microsoft ODBC Driver 18 for SQL Server (required by pyodbc).
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl gnupg2 ca-certificates apt-transport-https \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /etc/apt/keyrings/microsoft.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 unixodbc \
    && apt-get purge -y curl gnupg2 apt-transport-https \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* && rm -rf /wheels

# Mirror the repository layout: the app resolves ../config relative to the
# backend package, so config/ must sit next to backend/ inside the image.
WORKDIR /srv/backend
COPY backend/alembic.ini ./
COPY backend/alembic ./alembic
COPY backend/app ./app
COPY backend/scripts ./scripts
COPY config /srv/config

# Writable upload directory (mount a volume over this in production).
RUN mkdir -p /srv/uploads

# Non-root runtime user.
RUN useradd --create-home --uid 10001 crm && chown -R crm:crm /srv
USER crm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8001

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
