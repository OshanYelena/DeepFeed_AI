FROM python:3.12-slim

LABEL maintainer="DeepFeed AI"
LABEL description="DeepFeed AI Backend - FastAPI + Celery"

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
# uvicorn's app-loading inserts CWD into sys.path, but Celery's prefork
# workers don't reliably inherit that — task bodies doing `from application...`
# fail with ModuleNotFoundError inside forked workers without this.
ENV PYTHONPATH=/app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run as non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Default: API server. Override in docker-compose for worker/beat.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
