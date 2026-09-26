# PAPI backend image
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System dependencies for psycopg2 / reportlab (build tools kept out of final layers where possible)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first to leverage Docker layer cache
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application source
COPY . .

# Non-root user and uploads directory (mounted as a volume in compose)
RUN useradd -m appuser \
    && mkdir -p /app/uploads/documents /app/uploads/reports /app/uploads/inventory /app/uploads/asset_photos /app/uploads/prints \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.infrastructure.main:app", "--host", "0.0.0.0", "--port", "8000"]
