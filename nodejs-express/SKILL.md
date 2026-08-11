---
name: nodejs-express
description: "APIs REST y frameworks HTTP en Node.js. Cubre Express 5, Fastify y Hono — cuándo elegir cada uno. Middleware, routing, validación con Zod, manejo de errores, CORS, helmet, rate limiting, file upload, y buenas prácticas REST. Actívala al diseñar APIs HTTP, implementar endpoints REST, o migrar entre frameworks."
disable-model-invocation: true
---

# Node.js HTTP Frameworks & REST APIs

Guía de frameworks HTTP en Node.js 2026. Express 5, Fastify y Hono como opciones principales.

---

## Elección de framework

| Framework | Mejor para | Bundle (min) | Throughput | Ecosistema |
|-----------|-----------|--------------|------------|------------|
| **Express 5** | Compatibilidad, ecosistema, equipos grandes | Medio | Bueno | ⭐⭐⭐⭐⭐ Enorme |
| **Fastify** | Rendimiento Node puro, schema validation nativo | Bajo | ⭐⭐⭐⭐⭐ Excelente | ⭐⭐⭐ Creciente |
| **Hono** | Multi-runtime (Node/Bun/Deno/Workers), ultra-ligero | ~14KB | ⭐⭐⭐⭐ Muy bueno | ⭐⭐ Emergente |

**Regla 2026**: proyecto nuevo Node-only → **Fastify**. Necesitas ecosistema gigante / equipo grande → **Express 5**. Serverless / Edge / Multi-runtime → **Hono**.

---

## Express 5

### Setup mínimo

```typescript
import express, { type Request, type Response, type NextFunction } from 'express';
import helmet from 'helmet';
import cors from 'cors';
import rateLimit from 'express-rate-limit';

const app = express();

// Middleware global
app.use(helmet());
app.use(cors({ origin: process.env.CORS_ORIGIN }));
app.use(express.json());
app.use(rateLimit({ windowMs: 15 * 60 * 1000, max: 100 }));

// Routes
app.get('/health', (_req: Request, res: Response) => {
  res.json({ status: 'ok', uptime: process.uptime() });
});

app.listen(3000, () => console.log('Server on port 3000'));
```

### Router y estructura

```typescript
// orders.routes.ts
import { Router } from 'express';
import { createOrder, getOrderById, listOrders } from './orders.controller.js';
import { validate } from '../../shared/middleware/validation.js';
import { CreateOrderSchema } from './orders.schema.js';

const router = Router();

router.get('/', listOrders);
router.get('/:id', getOrderById);
router.post('/', validate(CreateOrderSchema), createOrder);

export { router as ordersRouter };

// app.ts
app.use('/api/orders', ordersRouter);
```

### Zod validation middleware

```typescript
import type { Request, Response, NextFunction } from 'express';
import { ZodSchema, ZodError } from 'zod';

export function validate(schema: ZodSchema) {
  return (req: Request, _res: Response, next: NextFunction) => {
    try {
      req.body = schema.parse(req.body);
      next();
    } catch (error) {
      if (error instanceof ZodError) {
        next(new ValidationError('Validation failed', error.errors));
      } else {
        next(error);
      }
    }
  };
}
```

### Error handler

```typescript
export class AppError extends Error {
  constructor(
    message: string,
    public statusCode: number = 500,
    public code?: string,
  ) {
    super(message);
    this.name = 'AppError';
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string) {
    super(`${resource} not found`, 404, 'NOT_FOUND');
  }
}

// Middleware de error (último en la cadena)
app.use((err: Error, _req: Request, res: Response, _next: NextFunction) => {
  if (err instanceof AppError) {
    return res.status(err.statusCode).json({
      error: { message: err.message, code: err.code },
    });
  }

  // Error inesperado
  console.error('Unhandled error:', err);
  res.status(500).json({ error: { message: 'Internal server error' } });
});
```

### Response helpers

```typescript
// Resultados semánticos
res.status(201).json(order);                        // Created
res.status(204).send();                             // No Content
res.status(400).json({ error: { message: '...' } }); // Bad Request
res.status(404).json({ error: { message: '...' } }); // Not Found
res.status(409).json({ error: { message: '...' } }); // Conflict

// Paginación
res.json({
  data: orders,
  pagination: {
    page: 1,
    pageSize: 20,
    total: 150,
    totalPages: 8,
  },
});
```

---

## Fastify

### Setup

```typescript
import Fastify from 'fastify';
import cors from '@fastify/cors';
import helmet from '@fastify/helmet';
import rateLimit from '@fastify/rate-limit';

const app = Fastify({ logger: true });

await app.register(cors, { origin: process.env.CORS_ORIGIN });
await app.register(helmet);
await app.register(rateLimit, { max: 100, timeWindow: '15 minutes' });

// Schema validation built-in (con Zod adaptado o Typebox)
app.post('/api/orders', {
  schema: {
    body: {
      type: 'object',
      required: ['customerId', 'amount'],
      properties: {
        customerId: { type: 'string' },
        amount: { type: 'number', minimum: 0.01 },
      },
    },
  },
}, async (request, reply) => {
  const { customerId, amount } = request.body as any;
  const order = await createOrder({ customerId, amount });
  return reply.status(201).send(order);
});

await app.listen({ port: 3000 });
```

### Plugins y DI con Fastify

```typescript
// Plugin: encapsula un módulo con sus rutas y dependencias
import fp from 'fastify-plugin';

async function ordersModule(app: FastifyInstance) {
  const orderService = new OrderService(app.db);

  app.get('/api/orders', async (req, reply) => {
    const orders = await orderService.list();
    return reply.send(orders);
  });

  app.post('/api/orders', async (req, reply) => {
    const order = await orderService.create(req.body);
    return reply.status(201).send(order);
  });
}

app.register(fp(ordersModule));
```

---

## Hono (Multi-runtime)

```typescript
import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { zValidator } from '@hono/zod-validator';
import { z } from 'zod';

const app = new Hono();

app.use('/api/*', cors());
app.get('/health', (c) => c.json({ status: 'ok' }));

// Validación con Zod integrada
const CreateOrderSchema = z.object({
  customerId: z.string().min(1),
  amount: z.number().positive(),
});

app.post('/api/orders', zValidator('json', CreateOrderSchema), async (c) => {
  const body = c.req.valid('json'); // Tipado automático
  const order = await createOrder(body);
  return c.json(order, 201);
});

export default app; // Deployable a Node, Bun, Deno, Cloudflare Workers
```

---

## File Upload

```typescript
import multer from 'multer';

// Configurar multer
const storage = multer.diskStorage({
  destination: 'uploads/',
  filename: (_req, file, cb) => {
    const uniqueName = `${Date.now()}-${file.originalname}`;
    cb(null, uniqueName);
  },
});

const upload = multer({
  storage,
  limits: { fileSize: 10 * 1024 * 1024 }, // 10 MB
  fileFilter: (_req, file, cb) => {
    const allowed = ['image/jpeg', 'image/png', 'application/pdf'];
    cb(null, allowed.includes(file.mimetype));
  },
});

// Ruta
app.post('/api/upload', upload.single('file'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No file uploaded' });
  }
  res.json({ filename: req.file.filename, size: req.file.size });
});
```

---

## Buenas prácticas REST

```typescript
// ✅ Nombres de recursos en plural, sustantivos
//   GET    /api/orders          → lista
//   POST   /api/orders          → crear
//   GET    /api/orders/:id      → obtener
//   PUT    /api/orders/:id      → reemplazar completo
//   PATCH  /api/orders/:id      → actualizar parcial
//   DELETE /api/orders/:id      → eliminar

// ✅ Paginación con query params
//   GET /api/orders?page=2&pageSize=20&status=pending

// ✅ Filtrado y ordenamiento
//   GET /api/orders?status=pending&sortBy=createdAt&sortOrder=desc

// ✅ Versionado (URL o header)
//   GET /api/v2/orders
//   o Accept: application/vnd.miapp.v2+json

// ✅ Manejo de errores consistente
interface ApiError {
  error: {
    message: string;
    code: string;
    details?: unknown;
  };
}

// ✅ HATEOAS links (opcional)
interface OrderResponse {
  data: Order;
  _links: {
    self: { href: string };
    cancel?: { href: string; method: 'POST' };
    items: { href: string };
  };
}
```

---

## Middleware patterns

```typescript
// Async handler wrapper (evita try/catch en cada ruta)
const asyncHandler = (fn: RequestHandler) =>
  (req: Request, res: Response, next: NextFunction) =>
    Promise.resolve(fn(req, res, next)).catch(next);

// Uso
router.get('/', asyncHandler(async (req, res) => {
  const orders = await orderService.list(req.query);
  res.json(orders);
}));

// Request ID por tracing
app.use((req, _res, next) => {
  req.id = req.headers['x-request-id'] as string ?? crypto.randomUUID();
  next();
});

// Response time
app.use((_req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    res.setHeader('X-Response-Time', `${duration}ms`);
  });
  next();
});
```

---

## Checklist API

- [ ] Framework elegido según caso (Express/Fastify/Hono)
- [ ] Helmet configurado para headers de seguridad
- [ ] CORS con orígenes explícitos (no `*` en producción)
- [ ] Rate limiting en endpoints sensibles
- [ ] Zod validation en todos los inputs (body, query, params)
- [ ] Error handler global con `AppError` y status codes semánticos
- [ ] Async errors capturados (asyncHandler o express 5 nativo)
- [ ] Response helpers para paginación consistente
- [ ] File upload con límites de tamaño y tipo
- [ ] Request ID para tracing en logs
- [ ] Health check en `/health`
