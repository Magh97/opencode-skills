---
name: nodejs-performance
description: "Rendimiento en Node.js. Cubre worker_threads, clustering, streams y backpressure, event loop profiling, memory leaks, profiling (clinic, autocannon), Undici 8 connection pool, análisis de GC, y Temporal API para fechas eficientes. Actívala al optimizar servicios lentos, reducir latencia, o diagnosticar memory leaks."
disable-model-invocation: true
---

# Node.js Performance

Guía de rendimiento para Node.js. Enfoque en event loop, memoria, y profiling.

---

## Event Loop: no bloquearlo

```
   ┌───────────────────────┐
┌─>│        timers         │  setTimeout, setInterval
│  └──────────┬────────────┘
│  ┌──────────┴────────────┐
│  │   pending callbacks   │  I/O callbacks diferidos
│  └──────────┬────────────┘
│  ┌──────────┴────────────┐
│  │     idle, prepare     │  Interno
│  └──────────┬────────────┘
│  ┌──────────┴────────────┐
│  │         poll          │  Nuevos eventos I/O
│  └──────────┬────────────┘
│  ┌──────────┴────────────┐
│   │         check         │  setImmediate
│  └──────────┬────────────┘
│  ┌──────────┴──────┐
└──┤   close callbacks│  socket.on('close', ...)
   └──────────────────┘
```

- **No bloquear:** JSON.parse enorme, crypto sync, regex catastrófica, loops `for` pesados.
- **Mover CPU-bound a worker_threads.**
- **I/O siempre async.** `readFileSync` = bloquea el event loop.

---

## Worker Threads

```typescript
import { Worker } from 'node:worker_threads';

// main.ts — delegar tarea pesada
function runHeavyTask(data: unknown): Promise<unknown> {
  return new Promise((resolve, reject) => {
    const worker = new Worker('./heavy-task.worker.ts', {
      workerData: data,
    });
    worker.on('message', resolve);
    worker.on('error', reject);
    worker.on('exit', (code) => {
      if (code !== 0) reject(new Error(`Worker stopped with exit code ${code}`));
    });
  });
}

// heavy-task.worker.ts
import { parentPort, workerData } from 'node:worker_threads';
const result = heavyComputation(workerData);
parentPort?.postMessage(result);
```

---

## Clustering (escalar multi-core)

```typescript
import cluster from 'node:cluster';
import { availableParallelism } from 'node:os';

if (cluster.isPrimary) {
  const numCPUs = availableParallelism();
  console.log(`Primary ${process.pid} forking ${numCPUs} workers`);

  for (let i = 0; i < numCPUs; i++) {
    cluster.fork();
  }

  cluster.on('exit', (worker, code) => {
    console.log(`Worker ${worker.process.pid} died, restarting...`);
    cluster.fork(); // Auto-restart
  });
} else {
  // Worker: arranca el servidor HTTP
  import('./server.js').then(({ start }) => start());
}
```

⚠️ **Clustering vs PM2**: PM2 maneja clustering + reinicio + monitoreo. Usar PM2 en producción en vez de clustering manual.

---

## Streams y backpressure

```typescript
import { pipeline } from 'node:stream/promises';
import { Transform, Readable } from 'node:stream';

// ✅ Backpressure manejado automáticamente por pipeline
await pipeline(
  Readable.from(async function* () {
    for (let i = 0; i < 1_000_000; i++) {
      yield `${JSON.stringify({ id: i })}\n`;
      // Si el destino está lento → pausa el generador
    }
  }()),
  new Transform({
    writableHighWaterMark: 1024 * 1024, // 1MB buffer
    transform(chunk, _encoding, callback) {
      const line = JSON.parse(chunk.toString());
      callback(null, JSON.stringify(transformLine(line)) + '\n');
    },
  }),
  createWriteStream('output.ndjson'),
);

// ⚠️ Sin pipeline → memory leak seguro con grandes datasets
// readStream.pipe(transform).pipe(writeStream);
```

---

## Profiling

### Autocannon (benchmark HTTP)

```bash
npm install -g autocannon

# Bombardear endpoint
autocannon -c 100 -d 30 http://localhost:3000/api/orders
# -c: connections, -d: duration en segundos
```

### Clinic.js

```bash
npm install -g clinic

# Doctor: diagnóstico general (CPU, memoria, event loop)
clinic doctor -- node dist/server.js
# autocannon -c 100 -d 30 http://localhost:3000/api/orders

# Flame: flamegraph de CPU
clinic flame -- node dist/server.js

# Bubbleprof: operaciones async
clinic bubbleprof -- node dist/server.js

# Heap profiler: memory allocations
clinic heapprofiler -- node dist/server.js
```

### Node built-in profiling

```bash
# CPU profile
node --cpu-prof --cpu-prof-dir=./profiles dist/server.js

# Heap snapshot
node --heapsnapshot --heapsnapshot-dir=./profiles dist/server.js
```

---

## Memory Leaks — diagnóstico

```typescript
// Causas comunes de memory leaks en Node.js:

// 1. Event listeners sin remover
// ❌ Cada request agrega un listener nuevo
app.get('/orders', (req, res) => {
  db.on('data', handler); // Se acumula
  res.send('ok');
});
// ✅ Usar once() o remover con removeListener
app.get('/orders', (req, res) => {
  db.once('data', handler);
  res.send('ok');
});

// 2. SetInterval sin clearInterval
// ❌
setInterval(() => fetchStatus(), 1000);
// ✅ Guardar referencia y limpiar
const interval = setInterval(() => fetchStatus(), 1000);
process.on('SIGTERM', () => clearInterval(interval));

// 3. Closures capturando objetos grandes
// ❌
function createHandler(largeData: HugeObject) {
  return () => process(largeData); // largeData nunca se libera
}

// 4. Global cache sin límite
// ❌
const cache = new Map();
// ✅ LRU cache con límite
import { LRUCache } from 'lru-cache';
const cache = new LRUCache({ max: 1000, ttl: 1000 * 60 * 5 });
```

### Inspeccionar memoria

```typescript
// Tomar heap snapshot desde código
import { writeHeapSnapshot } from 'node:v8';
writeHeapSnapshot(); // Escribe a disco

// Memory usage
const usage = process.memoryUsage();
console.log({
  rss: `${(usage.rss / 1024 / 1024).toFixed(1)} MB`,           // Total asignado
  heapTotal: `${(usage.heapTotal / 1024 / 1024).toFixed(1)} MB`,
  heapUsed: `${(usage.heapUsed / 1024 / 1024).toFixed(1)} MB`,  // Heap en uso
  external: `${(usage.external / 1024 / 1024).toFixed(1)} MB`,   // C++ objects
});

// GC tracking
import { PerformanceObserver } from 'node:perf_hooks';
const obs = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    console.log(`GC: kind=${entry.detail?.kind}, duration=${entry.duration}ms`);
  }
});
obs.observe({ type: 'gc', buffered: true });
```

---

## Undici 8 — HTTP client rápido

```typescript
// Undici es el cliente HTTP built-in de Node (reemplazo de fetch)
// Node 26 incluye Undici 8 por defecto

// ✅ fetch global (basado en Undici)
const response = await fetch('https://api.stripe.com/v1/charges', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${process.env.STRIPE_KEY}`,
    'Content-Type': 'application/x-www-form-urlencoded',
  },
  body: new URLSearchParams({ amount: '1000', currency: 'mxn' }),
});

if (!response.ok) throw new Error(`HTTP ${response.status}`);

// Pool de conexiones compartido (automático con fetch global)
// Para control fino:
import { Pool } from 'undici';

const pool = new Pool('https://api.stripe.com', {
  connections: 100,           // Máximo de conexiones concurrentes
  pipelining: 2,              // Requests por conexión
  keepAliveTimeout: 30_000,   // 30 segundos
  keepAliveMaxTimeout: 600_000,
});

const { statusCode, body } = await pool.request({
  path: '/v1/charges',
  method: 'POST',
  headers: {
    'authorization': `Bearer ${process.env.STRIPE_KEY}`,
    'content-type': 'application/x-www-form-urlencoded',
  },
  body: 'amount=1000&currency=mxn',
});

const data = await body.json();
```

---

## GC tuning

```bash
# Node arranca con GC concurrente por defecto.

# Para servicios con memoria grande:
node --max-old-space-size=4096 dist/server.js   # 4GB heap max

# Forzar GC solo en desarrollo para debugging
node --expose-gc dist/server.js                 # global.gc() disponible

# Semi-space tuning (para apps con muchos objetos pequeños)
node --max-semi-space-size=64 dist/server.js     # 64MB semi-space
```

---

## Checklist de rendimiento

- [ ] No bloquear event loop: JSON.parse pesado → worker thread
- [ ] CPU-bound tasks en worker_threads
- [ ] Clustering o PM2 para escalar en multi-core
- [ ] Streams con `pipeline()` para datos grandes (nunca cargar todo en memoria)
- [ ] Undici 8 `fetch` con keep-alive para HTTP calls salientes
- [ ] LRU cache con límite para datos frecuentes
- [ ] Sin `setInterval` sin limpieza, sin listeners acumulados
- [ ] Profiling con clinic doctor antes de optimizar
- [ ] `process.memoryUsage()` monitoreado periódicamente
- [ ] GC tracking en staging para detectar leaks
- [ ] `max-old-space-size` configurado en producción según RAM disponible
