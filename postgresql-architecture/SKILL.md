---
name: postgresql-architecture
description: "Arquitectura y administración de PostgreSQL. Cubre MVCC en profundidad, WAL y checkpointing, tablespaces, replicación (streaming y lógica), particionamiento declarativo, backups (pg_dump, pg_basebackup, Barman), y alta disponibilidad (Patroni, repmgr). Actívala al diseñar infraestructura PostgreSQL productiva, planear HA/DR, o configurar replicación."
disable-model-invocation: true
---

# PostgreSQL Architecture & Administration

Guía de arquitectura, replicación y administración de PostgreSQL para producción.

---

## MVCC en profundidad

```sql
-- Cada fila tiene metadatos invisibles:
-- xmin:  transaction ID que creó la fila
-- xmax:  transaction ID que la eliminó/actualizó (0 = visible)
-- ctid:  ubicación física (page, offset). Cambia en cada UPDATE.

SELECT xmin, xmax, ctid, * FROM sales.orders WHERE id = @id;
```

### Implicaciones de MVCC

- **UPDATE = INSERT + marcar antigua como obsoleta.** El espacio no se libera hasta VACUUM.
- **Cada UPDATE escribe un tuple completo**, no solo la columna modificada.
- **Transacciones largas** impiden limpiar dead tuples (vacuum no puede removerlos si alguna snapshot los necesita).
- **Transaction ID wraparound**: los XIDs son de 32 bits. Si se agotan → la DB se detiene. VACUUM previene esto (congela XIDs antiguos).

---

## WAL (Write-Ahead Logging)

```sql
-- WAL: registro de cambios antes de escribir datos. Garantiza durabilidad.
-- Ubicación: pg_wal/ (16MB por segmento)

-- Ver posición actual del WAL
SELECT pg_current_wal_lsn(), pg_current_wal_insert_lsn();

-- Tamaño total del WAL
SELECT pg_size_pretty(SUM(size)) FROM pg_ls_waldir();
```

### Checkpoint

Periódicamente, todos los datos modificados en shared_buffers se escriben a disco y el WAL puede truncarse.

```ini
# postgresql.conf
checkpoint_timeout = 15min       # Máximo entre checkpoints
max_wal_size = 16GB              # WAL máximo antes de checkpoint forzado
min_wal_size = 4GB               # WAL mínimo (no se trunca menos de esto)
```

---

## Tablespaces

```sql
-- Crear tablespace en disco rápido (SSD/NVMe)
CREATE TABLESPACE fastspace LOCATION '/mnt/ssd/pgdata';

-- Tablespace para datos fríos (HDD)
CREATE TABLESPACE slowspace LOCATION '/mnt/hdd/pgdata';

-- Mover tabla a tablespace específico
ALTER TABLE sales.orders SET TABLESPACE fastspace;

-- Mover toda una base de datos
ALTER DATABASE miapp SET TABLESPACE fastspace;

-- Índices en tablespace separado
CREATE INDEX idx_orders_created_at ON sales.orders (created_at)
    TABLESPACE fastspace;
```

---

## Replicación

### Streaming Replication (física)

```
Primary                    →    Standby (hot standby)
  WAL sender process       →       WAL receiver process
  pg_wal/                  →       pg_wal/
  Read/Write               →       Read-only
```

```ini
# PRIMARY: postgresql.conf
wal_level = replica
max_wal_senders = 5
wal_keep_size = 1024          # MB de WAL a retener

# PRIMARY: pg_hba.conf
host replication replicator 10.0.0.2/32 scram-sha-256

# STANDBY: Crear base backup
pg_basebackup -h primary -D /var/lib/postgresql/18/data -U replicator -P -R

# STANDBY: Se crea signal file automáticamente (-R)
# standby.signal → PostgreSQL arranca en modo recovery

# STANDBY: postgresql.conf (opcional)
primary_conninfo = 'host=primary port=5432 user=replicator'
primary_slot_name = 'standby_slot'
hot_standby = on               # Permitir queries de solo lectura en standby
```

### Logical Replication

Replica cambios a nivel de tabla (no bloque a bloque). Útil para:
- Migraciones con mínima downtime
- Replicación selectiva (solo algunas tablas)
- Diferentes versiones de PostgreSQL entre primary y replica
- Multi-master limitado

```sql
-- PRIMARY
CREATE PUBLICATION orders_pub FOR TABLE sales.orders, sales.order_items;

-- SUBSCRIBER
CREATE SUBSCRIPTION orders_sub
    CONNECTION 'host=primary dbname=miapp user=replicator'
    PUBLICATION orders_pub;
```

### Replication Slots

Evitan que el primary borre WAL que el standby aún no ha recibido.

```sql
-- Ver slots
SELECT * FROM pg_replication_slots;

-- Crear slot
SELECT pg_create_physical_replication_slot('standby_slot');

-- ⚠️ Monitorear: si el standby se cae y el slot existe → WAL se acumula en primary → disco lleno.
```

---

## Particionamiento declarativo

### Por rango (fechas, IDs)

```sql
CREATE TABLE sales.orders (
    id UUID DEFAULT uuidv7(),
    customer_id TEXT NOT NULL,
    total_amount NUMERIC(18,4) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
) PARTITION BY RANGE (created_at);

CREATE TABLE sales.orders_2025_01 PARTITION OF sales.orders
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE sales.orders_2025_02 PARTITION OF sales.orders
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- Partición default (catch-all)
CREATE TABLE sales.orders_default PARTITION OF sales.orders DEFAULT;
```

### Por lista (categorías, regiones)

```sql
CREATE TABLE sales.orders_by_status PARTITION BY LIST (status);

CREATE TABLE sales.orders_active PARTITION OF sales.orders_by_status
    FOR VALUES IN ('Pending', 'Confirmed', 'Shipped');

CREATE TABLE sales.orders_archived PARTITION OF sales.orders_by_status
    FOR VALUES IN ('Delivered', 'Cancelled', 'Expired');
```

### Por hash (distribución uniforme)

```sql
CREATE TABLE users PARTITION BY HASH (id);

CREATE TABLE users_0 PARTITION OF users FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE users_1 PARTITION OF users FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE users_2 PARTITION OF users FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE users_3 PARTITION OF users FOR VALUES WITH (MODULUS 4, REMAINDER 3);
```

### Detach/Attach (archivado sin downtime)

```sql
-- Desacoplar partición (queda como tabla independiente)
ALTER TABLE sales.orders DETACH PARTITION sales.orders_2023_01;

-- Acoplar tabla existente como partición
ALTER TABLE sales.orders ATTACH PARTITION sales.orders_2026_01
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
```

---

## Backups

### pg_dump (lógico)

```bash
# Backup completo
pg_dump -h localhost -U postgres -d miapp -Fc -f miapp_backup.dump

# Backup solo schema
pg_dump --schema-only -d miapp -f schema.sql

# Restore
pg_restore -h localhost -U postgres -d miapp_new miapp_backup.dump
```

### pg_basebackup (físico)

Backup a nivel de archivos. Base para streaming replication.

```bash
# Backup físico completo
pg_basebackup -h localhost -U replicator -D /backups/base -Ft -z -P
```

### Barman (backup enterprise)

```bash
# Configurar Barman para backups incrementales (PG 17+) y WAL continuo
barman switch-wal miapp
barman backup miapp
barman list-backup miapp
```

---

## Alta Disponibilidad: Patroni + etcd

```
┌────────────────────────────────────┐
│  etcd cluster (3 nodes)             │
│  Leader election + config store     │
└────────────────────────────────────┘
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼
 Node 1    Node 2    Node 3
(Leader)  (Standby) (Standby)
 Patroni   Patroni   Patroni
 PG 18     PG 18     PG 18

Client → HAProxy/VIP → Leader (reads + writes)
                     → Standbys (reads only)
```

Patroni maneja: failover automático, switchover controlado, reinicio de réplicas.

---

## PostgreSQL en contenedores

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:18-alpine
    environment:
      POSTGRES_DB: miapp
      POSTGRES_USER: app_user
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    # Config para producción ligera
    command: >
      -c shared_buffers=256MB
      -c effective_cache_size=1GB
      -c max_connections=200

volumes:
  pgdata:
```

---

## Checklist de arquitectura

- [ ] `shared_buffers` = 25% RAM, `effective_cache_size` = 75% RAM
- [ ] WAL en disco separado (si posible)
- [ ] Autovacuum configurado y sin wraparound warnings
- [ ] Replicación configurada según RPO/RTO
- [ ] Backups programados: pg_dump diario + WAL continuo
- [ ] pg_stat_statements habilitado
- [ ] Particionamiento para tablas >100GB
- [ ] PgBouncer en front de producción
- [ ] Monitoreo de replication lag
- [ ] Tablespaces en discos rápidos para tablas de alta carga
- [ ] pg_upgrade probado antes de upgrades de versión mayor
