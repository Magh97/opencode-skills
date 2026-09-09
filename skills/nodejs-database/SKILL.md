---
name: nodejs-database
description: "Acceso a datos en Node.js con Prisma 7, Drizzle y drivers nativos. Cubre PostgreSQL, SQL Server, migraciones, connection pooling, queries type-safe, raw SQL, y buenas prácticas de integración. Actívala al configurar ORM, diseñar esquemas de datos, optimizar queries, o migrar entre ORMs."
disable-model-invocation: true
---

# Node.js Database Access

Guía de acceso a datos en Node.js 2026. **Prisma 7 vs Drizzle** como ORMs. Drivers nativos para casos específicos.

---

## Elección del ORM

| Criterio | Prisma 7 | Drizzle |
|----------|----------|---------|
| **Abstracción** | Alta (schema.prisma) | Baja (SQL-like) |
| **Bundle size** | ~12MB CLI + ~2MB runtime | ~7.4KB runtime |
| **Serverless** | Cold start más lento | ⭐ Optimizado para serverless |
| **Type safety** | Excelente | ⭐ Excelente (inferido del schema) |
| **Migrations** | Built-in, maduro | Built-in (`drizzle-kit`) |
| **Relaciones** | API declarativa alta | API SQL-like con joins |
| **Raw SQL** | `$queryRaw` | Nativo con `sql` template |

**Regla**: Equipo que prefiere schema-first + abstracción → **Prisma 7**. Serverless + control SQL fino → **Drizzle**.

Para el detalle completo de schema, queries, migraciones y connection pooling de cada ORM, ver `nodejs-prisma` o `nodejs-drizzle` según el ORM elegido.

---

## Drivers nativos (sin ORM)

Cuándo usarlos: reportes/analytics con SQL muy específico, scripts puntuales, o control total sobre el driver sin la capa de abstracción de un ORM.

| Motor | Driver | Uso típico |
|-------|--------|-----------|
| **PostgreSQL** | `pg` | Queries parametrizadas directas, `pg.Pool` para pooling |
| **SQL Server** | `mssql` (wrapper sobre `tedious`) | Queries parametrizadas vía `.input()`, pooling con `pool: { max, min }` |
| **MySQL** | `mysql2` | Soporta promesas nativas y prepared statements |

En todos los casos: siempre parametrizar queries (nunca concatenar strings), y configurar límites de pool (`max`, `idleTimeoutMillis`) explícitamente.

```typescript
// Ejemplo mínimo: pg (PostgreSQL) sin ORM
import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,
  idleTimeoutMillis: 30000,
});

const result = await pool.query(
  'SELECT * FROM orders WHERE customer_id = $1',
  [customerId],
);
```

```typescript
// Ejemplo mínimo: mssql (SQL Server) sin ORM
import sql from 'mssql';

const pool = await sql.connect({
  server: 'localhost',
  database: 'miapp',
  options: { encrypt: true },
  pool: { max: 10, min: 2, idleTimeoutMillis: 30000 },
});

const result = await pool.request()
  .input('customerId', sql.NVarChar, customerId)
  .query('SELECT * FROM orders WHERE customer_id = @customerId');
```

Para el detalle operativo de connection pooling, migraciones y patrones de queries con ORM, ver `nodejs-prisma` (Prisma 7) o `nodejs-drizzle` (Drizzle) según corresponda.

---

## Checklist database

- [ ] ORM elegido según caso (Prisma: equipo grande, Drizzle: serverless) o driver nativo si no se necesita ORM
- [ ] Connection pooling configurado (max connections, idle timeout) — ver guía del ORM elegido
- [ ] Migraciones versionadas y en CI
- [ ] Sin N+1: usar `include`/`with` o `in` batch queries
- [ ] Batch updates en vez de loop + update individual
- [ ] Raw SQL solo para queries complejas (reportes, analytics)
- [ ] SQL parametrizado siempre (Prisma/Drizzle lo manejan; drivers nativos requieren hacerlo explícito)
- [ ] PgBouncer si >200 conexiones concurrentes en PostgreSQL
