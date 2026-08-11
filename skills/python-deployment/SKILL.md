---
name: python-deployment
description: "Despliegue y operaciones de aplicaciones Python. Cubre Docker multi-stage, Uvicorn + Gunicorn, Celery 5.6 para tareas asíncronas, CI/CD con GitHub Actions, logging con structlog, health checks, graceful shutdown, y gestión de secretos con Pydantic Settings. Actívala al preparar una app FastAPI para producción, configurar workers, o monitorear servicios."
disable-model-invocation: true
---

# Python Deployment & Operations

Guía de despliegue para aplicaciones Python. FastAPI + Uvicorn + Celery + Docker.

---

## Servidor ASGI — Uvicorn + Gunicorn

```bash
# Desarrollo: uvicorn con hot reload
uv run uvicorn miapp.main:app --reload --port 3000

# Producción: gunicorn con uvicorn workers
uv add gunicorn
gunicorn miapp.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 4 \
    --bind 0.0.0.0:3000 \
    --timeout 30 \
    --graceful-timeout 10 \
    --max-requests 10000 \
    --max-requests-jitter 1000
```

---

## Docker

```dockerfile
# Dockerfile
FROM python:3.14-slim AS build
WORKDIR /app

# Instalar uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Instalar dependencias
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copiar código
COPY src/ src/

# Production stage
FROM python:3.14-slim AS production
WORKDIR /app

RUN groupadd -r app && useradd -r -g app app
USER app

COPY --from=build /app/.venv /app/.venv
COPY --from=build /app/src /app/src

ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:3000/health')"

CMD ["gunicorn", "miapp.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", "--bind", "0.0.0.0:3000"]
```

```yaml
# docker-compose.yml (desarrollo)
services:
  app:
    build: .
    ports: ["3000:3000"]
    env_file: .env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./src:/app/src  # Hot reload

  postgres:
    image: postgres:18-alpine
    environment:
      POSTGRES_DB: miapp
      POSTGRES_USER: app_user
      POSTGRES_PASSWORD: dev_pass
    ports: ["5432:5432"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app_user -d miapp"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
```

---

## Celery 5.6 — Task Queue

```bash
uv add celery[redis]
```

```python
# shared/celery_app.py
from celery import Celery

celery_app = Celery(
    "miapp",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,          # Reintentar si worker muere
    worker_prefetch_multiplier=1,  # 1 tarea a la vez
)
```

```python
# modules/orders/tasks.py
from miapp.shared.celery_app import celery_app
from miapp.shared.database import async_session_factory
import asyncio

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_order_async(self, order_id: str):
    """Tarea larga: generar invoice, notificar, actualizar stock."""
    async def _process():
        async with async_session_factory() as db:
            order = await order_repo.find_by_id(db, order_id)
            if not order:
                raise ValueError(f"Order {order_id} not found")

            # Generar invoice (PDF) — operación lenta
            await generate_invoice(order)

            # Notificar por email
            await send_confirmation(order)

            # Actualizar stock
            await update_stock(db, order.items)

    try:
        asyncio.run(_process())
    except Exception as exc:
        raise self.retry(exc=exc)

# Llamar desde FastAPI
@router.post("/")
async def create_order(body: OrderCreate, service: OrderService = Depends()):
    order = await service.create(body)
    process_order_async.delay(str(order.id))  # Encolar tarea
    return order
```

### Ejecutar worker

```bash
# Worker
celery -A miapp.shared.celery_app worker --loglevel=info --concurrency=4

# Beat (tareas programadas)
celery -A miapp.shared.celery_app beat --loglevel=info

# Flower (dashboard)
uv add flower
celery -A miapp.shared.celery_app flower --port=5555
```

---

## Logging — structlog

```python
# shared/logging.py
import structlog

def setup_logging():
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.dev.ConsoleRenderer() if settings.DEBUG
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

logger = structlog.get_logger()

# Uso estructurado
logger.info("order_created", order_id=str(order.id), customer_id=order.customer_id)
logger.error("order_failed", order_id=str(order.id), error=str(exc))
```

---

## Graceful Shutdown

```python
# main.py
import signal
import asyncio

async def shutdown():
    logger.info("Shutting down...")
    await engine.dispose()
    await redis_client.close()

def handle_signal(signum, frame):
    loop = asyncio.get_event_loop()
    loop.create_task(shutdown())

signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)
```

---

## Health Checks

```python
@app.get("/health")
async def health():
    return {"status": "ok", "uptime": time.time() - start_time}

@app.get("/health/ready")
async def readiness(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        await redis_client.ping()
        return {"status": "ok", "db": "connected", "redis": "connected"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))
```

---

## CI/CD — GitHub Actions

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:18-alpine
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test
        ports: ["5432:5432"]
      redis:
        image: redis:7-alpine
        ports: ["6379:6379"]
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - run: uv sync --frozen
      - run: uv run ruff check .
      - run: uv run mypy src/
      - run: uv run pytest --cov --cov-report=xml
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/test
          REDIS_URL: redis://localhost:6379/0

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build and push Docker image
        run: |
          docker build -t ghcr.io/mi-org/miapp:${{ github.sha }} .
          docker push ghcr.io/mi-org/miapp:${{ github.sha }}
```

---

## Checklist deployment

- [ ] Docker multi-stage (build separado de runtime)
- [ ] Gunicorn + Uvicorn workers para producción
- [ ] Celery para tareas asíncronas pesadas (>5s o que pueden fallar)
- [ ] Redis como broker + backend de Celery
- [ ] structlog configurado (pretty en dev, JSON en prod)
- [ ] Health checks `/health` (liveness) y `/health/ready` (readiness)
- [ ] Graceful shutdown: desconectar DB, Redis, drenar requests
- [ ] CI/CD: lint → typecheck → test → build Docker → deploy
- [ ] `uv sync --frozen` en CI (respeta lock file)
- [ ] `PYTHONUNBUFFERED=1` en Docker
- [ ] Secrets en Pydantic Settings, nunca en código
- [ ] No `DEBUG=True` en producción
