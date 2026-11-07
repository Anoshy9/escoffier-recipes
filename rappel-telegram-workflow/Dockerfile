FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY pyproject.toml ./
COPY src ./src

RUN pip install --no-cache-dir "mistralai-workflows>=3.10,<4" "httpx>=0.27"

CMD ["python", "src/entrypoints/worker.py"]
