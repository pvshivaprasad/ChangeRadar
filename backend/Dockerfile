# ==============================================================================
# ChangeRadar 1.0 — Production Backend Dockerfile (Context: backend/)
# ==============================================================================
FROM python:3.13-slim AS builder

WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
RUN pip install --no-cache-dir --user psycopg2-binary cryptography alembic uvicorn

FROM python:3.13-slim AS runtime
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -g 10001 changeradar && \
    useradd -u 10001 -g changeradar -m -s /bin/bash changeradar

COPY --from=builder /root/.local /home/changeradar/.local

ENV PATH="/home/changeradar/.local/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

COPY --chown=changeradar:changeradar app /app/app
COPY --chown=changeradar:changeradar alembic /app/alembic
COPY --chown=changeradar:changeradar alembic.ini /app/alembic.ini

RUN mkdir -p /app/storage/repositories && \
    chown -R changeradar:changeradar /app/storage

USER changeradar
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'"]
