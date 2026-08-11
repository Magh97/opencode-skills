---
name: python-performance
description: "Rendimiento en Python 3.14. Cubre asyncio avanzado, profiling (py-spy, scalene), free-threading para CPU-bound, caching (Redis, lru_cache), multiprocessing, memory profiling, y optimización de queries SQLAlchemy. Actívala al optimizar servicios lentos, reducir latencia, o escalar aplicaciones Python."
disable-model-invocation: true
---

# Python Performance

Guía de rendimiento en Python 3.14. Free-threading para CPU-bound, asyncio para I/O, profiling antes de optimizar.

---

## Profiling — medir primero

### py-spy (sampling profiler, sin overhead)

```bash
uv add --dev py-spy

# Perfilar proceso en vivo (sin reiniciar)
py-spy top --pid <PID>

# Flamegraph
py-spy record -o flame.svg --pid <PID> --duration 30

# Ver qué está bloqueando el GIL
py-spy dump --pid <PID>
```

### scalene (CPU + memoria)

```bash
uv add --dev scalene
scalene src/miapp/main.py
# Reporte: CPU time, memory usage, lines que asignan más memoria
```

### cProfile (built-in)

```bash
python -m cProfile -s cumulative src/miapp/main.py
```

---

## asyncio avanzado

```python
import asyncio

# ✅ TaskGroup: cancelación segura (Python 3.11+)
async def fetch_all(urls: list[str]) -> list[dict]:
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(fetch_json(url)) for url in urls]
    return [t.result() for t in tasks]
    # Si alguna falla, todas se cancelan. Sin excepciones silenciadas.

# ✅ Semaphore: limitar concurrencia
sem = asyncio.Semaphore(10)

async def fetch_with_limit(url: str) -> dict:
    async with sem:
        return await fetch_json(url)

async def fetch_all_limited(urls: list[str]) -> list[dict]:
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(fetch_with_limit(url)) for url in urls]
    return [t.result() for t in tasks]

# ✅ asyncio.timeout (Python 3.11+)
async def fetch_safe(url: str) -> dict | None:
    try:
        async with asyncio.timeout(5.0):
            return await fetch_json(url)
    except TimeoutError:
        logger.warning(f"Timeout for {url}")
        return None

# ✅ Queue.shutdown (Python 3.13+) — cierre limpio
async def worker(queue: asyncio.Queue[Task]):
    while True:
        try:
            task = await queue.get()
        except asyncio.QueueShutDown:
            return  # Salida limpia
        await process(task)
        queue.task_done()

# ✅ to_thread para CPU-bound (no bloquea event loop)
import hashlib

async def hash_password_async(password: str) -> str:
    return await asyncio.to_thread(
        hashlib.pbkdf2_hmac, "sha256", password.encode(), b"salt", 100_000
    )
```

---

## Free-threading (Python 3.14 — sin GIL)

```python
# Ejecutar en modo free-threaded
# uv run --free-threaded python script.py

from concurrent.futures import ThreadPoolExecutor
import time

def cpu_heavy(n: int) -> int:
    total = 0
    for i in range(1, n + 1):
        total += i * i
    return total

# ✅ Con free-threading: ThreadPoolExecutor escala en multi-core
with ThreadPoolExecutor(max_workers=4) as executor:
    start = time.perf_counter()
    results = list(executor.map(cpu_heavy, [10_000_000] * 4))
    elapsed = time.perf_counter() - start
    print(f"4 threads: {elapsed:.2f}s")  # ~1x el tiempo de 1 thread

# ⚠️ Sin free-threading: ThreadPoolExecutor no escala
# 4 threads toman ~4x el tiempo (serializados por GIL)
```

### Precauciones free-threading

- **No todas las extensiones C son thread-safe.** Verificar compatibilidad.
- **`collections.deque`, `dict`, `list`** son thread-safe en free-threaded CPython.
- **Usar `threading.Lock`** para proteger secciones críticas.

---

## Multiprocessing (para CPU-bound sin free-threading)

```python
from multiprocessing import Pool

def process_batch(items: list[int]) -> int:
    return sum(i * i for i in items)

# Paralelismo real (procesos separados, sin GIL)
with Pool(processes=4) as pool:
    results = pool.map(process_batch, [range(1_000_000)] * 4)
```

---

## Caching

### functools.lru_cache (en memoria)

```python
from functools import lru_cache

@lru_cache(maxsize=1024)
def calculate_shipping(weight: float, distance: float) -> float:
    # Cálculo costoso cacheado
    ...

# Async: usar async_lru o implementar manual con dict
```

### Redis cache

```python
import redis.asyncio as redis
import json

redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

async def get_cached_order(order_id: str) -> dict | None:
    data = await redis_client.get(f"order:{order_id}")
    return json.loads(data) if data else None

async def cache_order(order_id: str, order: dict, ttl: int = 300):
    await redis_client.setex(
        f"order:{order_id}",
        ttl,
        json.dumps(order, default=str),
    )
```

---

## SQLAlchemy — Queries optimizadas

```python
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload, noload

# ✅ Proyección: solo columnas necesarias
stmt = (
    select(Order.id, Order.status, Order.total_amount)
    .where(Order.customer_id == customer_id)
)
result = await db.execute(stmt)
orders = result.all()

# ✅ selectinload sobre joinedload (evita JOIN explosivo)
stmt = (
    select(Order)
    .where(Order.customer_id == customer_id)
    .options(selectinload(Order.items), selectinload(Order.payments))
)

# ✅ noload: explícitamente no cargar relaciones
stmt = select(Order).options(noload(Order.items))

# ✅ Batch insert
async def bulk_create_orders(db: AsyncSession, orders: list[Order]):
    db.add_all(orders)
    await db.flush()  # Un solo round-trip
```

---

## Memory profiling

```python
# memory-profiler
# uv add --dev memory-profiler

@profile
def memory_intensive_function():
    data = [i * i for i in range(1_000_000)]  # ~8 MB
    return sum(data)

# Ver leaks con tracemalloc (built-in)
import tracemalloc

tracemalloc.start()
# ... ejecutar código ...
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics("lineno")
for stat in top_stats[:10]:
    print(stat)
```

---

## Checklist rendimiento

- [ ] Profiling **antes** de optimizar (py-spy, scalene)
- [ ] TaskGroup para tareas concurrentes con cancelación segura
- [ ] Semaphore para limitar concurrencia (DB pool, APIs externas)
- [ ] asyncio.timeout en toda I/O externa
- [ ] Free-threading (3.14) para CPU-bound; multiprocessing como fallback
- [ ] Redis cache para queries repetitivas
- [ ] SQLAlchemy: proyección, selectinload, batch operations
- [ ] Sin `except Exception: pass` ni logs en loops calientes
- [ ] Memory profiling en staging para detectar leaks
- [ ] Connection pooling configurado (SQLAlchemy pool_size)
