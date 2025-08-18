# syntax=docker/dockerfile:1.7
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md /app/
RUN pip install --upgrade pip && pip install .

COPY app /app/app
COPY .env.example /app/.env.example

EXPOSE 8000

ENV ENV=production

CMD ["uvicorn", "app.main:app", "--host=0.0.0.0", "--port=8000"]
