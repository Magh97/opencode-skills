---
name: postgresql-performance
description: "Rendimiento y tuning de queries en PostgreSQL. Cubre EXPLAIN/EXPLAIN ANALYZE, tipos de índices (B-tree, GIN, GiST, BRIN, Hash), vacuum y autovacuum, estadísticas (ANALYZE), particionamiento por poda (pruning), parallel query, async I/O (PG 18), skip scan (PG 18), y estrategias de optimización de queries. Actívala al diagnosticar queries lentas, diseñar índices, o resolver problemas de rendimiento."
disable-model-invocation: true
---

# PostgreSQL Performance & Query Tuning

Guía de rendimiento y optimización de queries PostgreSQL. El mejor advice: encontrar la peor query o índice faltante antes de agregar hardware.

---

## EXPLAIN / EXPLAIN ANALYZE

```sql
-- Plan estimado (sin ejecutar)
EXPLAIN SELECT * FROM sales.orders WHERE customer_id = 'CUST-001';

-- Plan real (ejecutando)
EXPLAIN ANALYZE SELECT * FROM sales.orders WHERE customer_id = 'CUST-001';

-- Con buffers (cuántas páginas de disco/cache)
EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM sales.orders WHERE customer_id = 'CUST-001';

-- Con timing por nodo
EXPLAIN (ANALYZE, BUFFERS, TIMING) SELECT ...;
```

### Lectura del plan (más anidado = más adentro)

```
Sort (cost=..., rows=..., actual time=..., loops=1)
  Sort Key: created_at DESC
  -> Index Scan using idx_orders_customer_id on orders (cost=..., rows=10, loops=1)
       Index Cond: (customer_id = 'CUST-001')
```

**cost=**: `startup_cost..total_cost` (unidades arbitrarias del planner).
**actual time=**: milisegundos reales.
**rows=**: filas estimadas vs reales. Si difieren mucho → estadísticas desactualizadas.

### Nodos comunes

| Nodo | Significado |
|------|-------------|
| **Seq Scan** | Lee toda la tabla secuencialmente |
| **Index Scan** | Usa índice para encontrar filas + heap lookup |
| **Index Only Scan** | El índice cubre todas las columnas (covering). Sin heap lookup. ✅ |
| **Bitmap Index Scan + Heap Scan** | Index scan en bitmap, luego heap scan en orden físico. Bueno para muchas filas. |
| **Nested Loop** | Join fila por fila. Bueno para pocas filas externas + índice en join interno. |
| **Hash Join** | Tabla hash en memoria. Bueno para datasets grandes sin índice. |
| **Merge Join** | Inputs ya ordenados. Necesita índices o sorts previos. |
| **Sort** | Ordenamiento explícito. Verificar si falta índice. |
| **Parallel Seq Scan** | Escaneo paralelo (múltiples workers). |

### `(cost=0.00..387.00 rows=10000 width=68)`

- `0.00` = startup cost (tiempo para devolver primera fila)
- `387.00` = total cost
- `rows=10000` = estimación de filas. Si `(actual rows=50000)` → estadísticas desactualizadas.

---

## Índices

### Tipos de índices

| Tipo | Caso de uso | Ejemplo |
|------|------------|---------|
| **B-tree** (default) | Igualdad, rangos, ORDER BY | `WHERE customer_id = 'X'` |
| **Hash** | Solo igualdad (`=`). PG 10+. | `WHERE email = 'x@x.com'` |
| **GIN** | Arrays, JSONB, full-text, trigram | `WHERE tags @> ARRAY['vip']` |
| **GiST** | Full-text, geométrico, rangos | `WHERE geom && ST_MakeEnvelope(...)` |
| **BRIN** | Tablas enormes ordenadas físicamente | `WHERE created_at > '2025-01-01'` |
| **SP-GiST** | Puntos, rangos, redes | PostGIS, IP ranges |

### Creación de índices

```sql
-- B-tree estándar
CREATE INDEX idx_orders_customer_id ON sales.orders (customer_id);

-- B-tree covering (INCLUDE) — 11+
CREATE INDEX idx_orders_customer_covering ON sales.orders (customer_id)
    INCLUDE (total_amount, created_at, status);

-- Índice parcial (filtered)
CREATE INDEX idx_orders_pending ON sales.orders (created_at)
    WHERE status = 'Pending';

-- Índice multicolumna (orden importa)
CREATE INDEX idx_orders_customer_date ON sales.orders (customer_id, created_at DESC);

-- Índice en expresión
CREATE INDEX idx_orders_lower_email ON users (LOWER(email));

-- GIN para JSONB
CREATE INDEX idx_products_metadata ON catalog.products USING GIN (metadata jsonb_path_ops);

-- BRIN para datos que crecen secuencialmente (logs, eventos)
CREATE INDEX idx_events_time ON events USING BRIN (created_at)
    WITH (pages_per_range = 32);

-- CONCURRENTLY: sin bloquear escrituras
CREATE INDEX CONCURRENTLY idx_orders_new ON sales.orders (new_column);
```

### Skip Scan (PostgreSQL 18)

```sql
-- Índice multicolumna: (customer_id, status, created_at)
CREATE INDEX idx_orders_multi ON sales.orders (customer_id, status, created_at);

-- PG 18 puede usar este índice incluso cuando customer_id no aparece en WHERE
SELECT * FROM sales.orders
WHERE status = 'Pending'
ORDER BY created_at DESC LIMIT 10;
-- Antes sin skip scan: Seq Scan o índice sin customer_id.
-- PG 18: Skip Scan sobre el índice multicolumna. Mayor rendimiento.
```

---

## VACUUM y Autovacuum

PostgreSQL usa MVCC: los UPDATEs crean nuevas versiones. VACUUM limpia las antiguas.

```sql
-- Ver dead tuples
SELECT
    schemaname, relname,
    n_live_tup, n_dead_tup,
    last_autovacuum, last_autoanalyze
FROM pg_stat_user_tables
WHERE n_dead_tup > 0
ORDER BY n_dead_tup DESC;

-- Forzar vacuum manual (solo en emergencias)
VACUUM ANALYZE sales.orders;
VACUUM FULL sales.orders; -- ⚠️ Bloquea la tabla. Reclama espacio al SO.

-- Autovacuum tuning (parámetros en postgresql.conf)
-- autovacuum_vacuum_scale_factor = 0.05  (5% de la tabla)
-- autovacuum_vacuum_threshold = 50       (mínimo de dead tuples)
-- Para tablas grandes (>100M): bajar scale_factor a 0.01 o 0.005
```

---

## Estadísticas

```sql
-- Actualizar estadísticas
ANALYZE sales.orders;

-- Ver último ANALYZE
SELECT
    schemaname, relname,
    last_analyze, last_autoanalyze
FROM pg_stat_user_tables
ORDER BY last_analyze DESC NULLS LAST;

-- Estadísticas extendidas (correlación entre columnas)
CREATE STATISTICS orders_customer_status (dependencies)
    ON customer_id, status FROM sales.orders;

-- Cardinalidad default: 100 buckets. Aumentar para columnas con distribución skew.
ALTER TABLE sales.orders ALTER COLUMN status SET STATISTICS 1000;
```

---

## Parallel Query

```sql
-- Configurar workers
-- SET max_parallel_workers_per_gather = 2;  (default)
-- SET max_parallel_workers = 8;              (default)

-- Forzar paralelismo para query específica
SET parallel_tuple_cost = 0;
SET parallel_setup_cost = 0;
SELECT * FROM sales.orders WHERE total_amount > 1000;

-- Ver si una query usó paralelismo
EXPLAIN ANALYZE SELECT * FROM sales.orders WHERE total_amount > 1000;
-- Si aparece "Parallel Seq Scan" o "Gather" → está usando paralelismo.
```

---

## Async I/O (PostgreSQL 18)

```sql
-- PG 18: nuevo subsistema de I/O asíncrono
-- Hasta 3x mejor rendimiento en lecturas de almacenamiento
-- Se habilita automáticamente en PG 18.

-- Configuración: postgresql.conf
-- io_method = worker    (default en PG 18, usa workers para I/O async)
-- io_method = sync       (modo legacy, sin async I/O)
```

Este feature es **automático y transparente** en PG 18. No requiere cambios en queries o esquema.

---

## Connection Pooling (PgBouncer)

PostgreSQL usa un proceso por conexión. Para >200 conexiones concurrentes: usar PgBouncer.

```ini
; pgbouncer.ini
[databases]
miapp = host=localhost port=5432 dbname=miapp

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = scram-sha-256
pool_mode = transaction     ; transaction pooling (recomendado)
max_client_conn = 1000
default_pool_size = 25
reserve_pool_size = 5
```

```csharp
// La app se conecta a PgBouncer, no a PostgreSQL directo
// Connection string: Host=localhost;Port=6432;Database=miapp;
```

---

## Particionamiento por poda (pruning)

```sql
-- Tabla particionada por fecha
CREATE TABLE sales.orders (
    id UUID DEFAULT uuidv7(),
    customer_id TEXT NOT NULL,
    total_amount NUMERIC(18,4) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
) PARTITION BY RANGE (created_at);

-- Particiones mensuales
CREATE TABLE sales.orders_2025_01 PARTITION OF sales.orders
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
CREATE TABLE sales.orders_2025_02 PARTITION OF sales.orders
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- Queries que incluyen created_at hacen pruning automático
SELECT * FROM sales.orders WHERE created_at >= '2025-01-01' AND created_at < '2025-02-01';
-- Solo escanea orders_2025_01. ✅
```

---

## Buenas prácticas de queries

```sql
-- ✅ Sargable (Search ARGument ABLE)
SELECT * FROM orders WHERE customer_id = 'CUST-001';
SELECT * FROM orders WHERE created_at >= '2025-01-01';

-- ❌ No sargable
SELECT * FROM orders WHERE EXTRACT(YEAR FROM created_at) = 2025;  -- Función sobre columna
SELECT * FROM orders WHERE LOWER(customer_id) = 'cust-001';       -- Función sobre columna

-- ✅ Alternativa sargable
SELECT * FROM orders WHERE created_at >= '2025-01-01' AND created_at < '2026-01-01';
-- Crear índice funcional si LOWER es necesario
CREATE INDEX idx_orders_lower_customer ON orders (LOWER(customer_id));

-- ✅ EXISTS en vez de COUNT(*)
IF EXISTS (SELECT 1 FROM orders WHERE customer_id = 'X') THEN ... END IF;

-- ✅ UNION ALL sobre UNION (no deduplica, más rápido)
SELECT customer_id FROM current_orders
UNION ALL
SELECT customer_id FROM archived_orders;

-- ✅ LIMIT con ORDER BY, siempre
SELECT * FROM orders ORDER BY created_at DESC LIMIT 10;

-- ❌ OFFSET pagination en páginas profundas
SELECT * FROM orders ORDER BY id OFFSET 100000 LIMIT 10;  -- Leer 100K filas para saltar

-- ✅ Keyset pagination
SELECT * FROM orders WHERE id > :lastId ORDER BY id LIMIT 10;
```

---

## Parámetros de configuración clave (postgresql.conf)

```ini
# Memoria
shared_buffers = 4GB              # 25% de RAM del servidor
effective_cache_size = 12GB       # 75% de RAM
work_mem = 256MB                  # Memoria por operación (sort, hash)
maintenance_work_mem = 1GB        # Para VACUUM, CREATE INDEX

# Paralelismo
max_parallel_workers_per_gather = 2
max_parallel_workers = 8

# WAL
wal_buffers = 64MB
checkpoint_timeout = 15min

# Planner
random_page_cost = 1.1            # SSD: 1.1. HDD: 4.0
effective_io_concurrency = 200    # SSD: 200. HDD: 2

# Autovacuum
autovacuum_max_workers = 3
autovacuum_vacuum_scale_factor = 0.05
```

Usar **https://pgtune.leopard.in.ua** para configuración inicial según hardware.

---

## pg_stat_statements (monitoreo)

```sql
-- Top queries por tiempo total
SELECT
    queryid,
    LEFT(query, 100) AS query_preview,
    calls,
    mean_exec_time::NUMERIC(10,2) AS avg_ms,
    total_exec_time::NUMERIC(10,2) AS total_ms,
    rows,
    shared_blks_hit,
    shared_blks_read
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;

-- Top queries por carga de disco (bloques leídos)
SELECT queryid, LEFT(query, 100), shared_blks_read
FROM pg_stat_statements
ORDER BY shared_blks_read DESC
LIMIT 20;
```

---

## Checklist de rendimiento

- [ ] `pg_stat_statements` habilitado
- [ ] EXPLAIN ANALYZE revisado para queries del top-10 por consumo
- [ ] Índices covering para queries frecuentes (INCLUDE desde PG 11)
- [ ] Índices parciales para queries con WHERE fijo (ej: `WHERE status = 'Pending'`)
- [ ] Estadísticas actualizadas (AUTOANALYZE + ANALYZE manual en tablas grandes)
- [ ] VACUUM al día: dead tuples < 5% en tablas activas
- [ ] Autovacuum tuning para tablas grandes (>100M filas)
- [ ] PgBouncer configurado para >200 conexiones
- [ ] Particionamiento para tablas >100GB o >500M filas
- [ ] Keyset pagination en vez de OFFSET para páginas profundas
- [ ] `shared_buffers` = 25% RAM, `effective_cache_size` = 75% RAM
- [ ] `random_page_cost` = 1.1 (SSD) o 4.0 (HDD)
- [ ] Queries sargables: sin funciones sobre columnas en WHERE
- [ ] `work_mem` suficiente para sorts y hashes (256MB+)
