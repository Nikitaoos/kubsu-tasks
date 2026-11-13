# syntax=docker/dockerfile:1

# ---------- Stage 1: builder — ставим зависимости в отдельный префикс ----------
FROM python:3.12-alpine AS builder
WORKDIR /build
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
COPY pyproject.toml .
# Берём список зависимостей прямо из pyproject.toml (без самого проекта)
RUN python -c "import tomllib; d = tomllib.load(open('pyproject.toml', 'rb')); \
print('\n'.join(d['project']['dependencies'])); \
open('test.txt', 'w').write('\n'.join(d['project']['optional-dependencies']['test']))" > requirements.txt \
 && pip install --prefix=/install -r requirements.txt \
 && find /install -type d -name __pycache__ -prune -exec rm -rf {} +

# ---------- Stage 2: base — минимальный образ с приложением ----------
FROM python:3.12-alpine AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8016
WORKDIR /app
COPY --from=builder /install /usr/local
COPY src ./src
RUN adduser -D -H -u 10001 app
USER app
EXPOSE 8016
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/health', timeout=2)"
CMD ["sh", "-c", "exec uvicorn src.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]

# ---------- test: тот же образ + pytest и тесты (используется в CI) ----------
FROM base AS test
USER root
COPY --from=builder /build/test.txt /tmp/test.txt
RUN pip install --no-cache-dir -r /tmp/test.txt && rm /tmp/test.txt
COPY pyproject.toml ./
COPY tests ./tests
USER app
CMD ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"]

# ---------- runtime: итоговый образ (цель по умолчанию) ----------
FROM base AS runtime
