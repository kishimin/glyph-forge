FROM python:3.12.11-slim-bookworm AS builder

WORKDIR /build

COPY requirements-prod.txt setup.py pyproject.toml ./
COPY src ./src

RUN python -m pip wheel \
    --no-cache-dir \
    --wheel-dir /wheels \
    --requirement requirements-prod.txt \
    .


FROM python:3.12.11-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home app

WORKDIR /app

COPY --from=builder /wheels /wheels
RUN python -m pip install --no-cache-dir --no-index /wheels/*.whl \
    && rm -rf /wheels

COPY --chown=app:app app ./app

USER app

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
