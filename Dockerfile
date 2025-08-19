# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Optional: tools needed for some builds (can be reduced later)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first for better layer cache
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy project (will be overridden by bind mount when using docker-compose for dev)
COPY . /app

# Expose default dev port (actual port is configurable at runtime via PORT)
EXPOSE 8100

# Default command uses HOST/PORT from environment (.env or container env)
CMD ["/bin/sh", "-c", "uvicorn app.main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8100}"]