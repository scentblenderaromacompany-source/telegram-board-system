FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency file first for layer caching
COPY pyproject.toml .

# Copy source
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -e ".[qrcode]" || \
    pip install --no-cache-dir python-telegram-bot httpx qrcode

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser && \
    mkdir -p /home/appuser/config /home/appuser/logs && \
    chown -R appuser:appuser /home/appuser

USER appuser

ENTRYPOINT ["python3", "-m", "src.main"]
