FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy source
COPY . .

# Install all dependencies (non-editable for Docker)
RUN pip install --no-cache-dir python-telegram-bot httpx aiohttp qrcode

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser && \
    mkdir -p /home/appuser/config /home/appuser/logs && \
    chown -R appuser:appuser /home/appuser

USER appuser

ENTRYPOINT ["python3", "-m", "src.main"]
