# ── Stage 1: Builder ──────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build-time system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libpq-dev libffi-dev libcairo2-dev libpango1.0-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-prod.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements-prod.txt

# ── Stage 2: Runtime (Lambda-compatible) ─────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install runtime system deps + FFmpeg for video pipeline
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 ffmpeg curl libcairo2 libpango-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy Lambda Web Adapter extension
# This translates Lambda invocation events into HTTP requests to FastAPI.
# Zero code changes needed — FastAPI runs exactly as it does locally.
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.8.4 \
    /lambda-adapter /opt/extensions/lambda-adapter

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Lambda Web Adapter config
ENV PORT=8000
ENV AWS_LWA_READINESS_CHECK_PATH=/health
ENV AWS_LWA_INVOKE_MODE=response_stream

# Non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && mkdir -p /tmp/video-workspace \
    && chown -R appuser:appuser /app /tmp/video-workspace
USER appuser

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start FastAPI — Lambda Web Adapter handles Lambda <-> HTTP translation
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
