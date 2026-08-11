---
name: react-performance
description: "Rendimiento en React 19. Cubre memo/useMemo/useCallback, virtualización con TanStack Virtual, code splitting (React.lazy, loadable), bundle analysis, React Server Components (zero JS), streaming SSR, useDeferredValue/useTransition, y profiling con React DevTools. Actívala al optimizar renders, reducir bundle size, o implementar virtualización."
disable-model-invocation: true
---

# React Performance

Guía de rendimiento en React 19. Optimizar renders, reducir JS al cliente, medir antes de optimizar.

---

## Medir primero — React DevTools Profiler

```
React DevTools → Profiler tab → Record → Interactúa → Stop
```

Buscar:
- **Render duration** > 16ms (60fps)
- **Re-renders innecesarios** (componentes que se renderizan sin cambios de props)
- **Commit phase** lenta (DOM mutations)

---

## memo, useMemo, useCallback

```tsx
// memo: evita re-render si props no cambian (comparación superficial)
import { memo } from 'react';

const OrderCard = memo(function OrderCard({ order, onCancel }: OrderCardProps) {
  return (
    <article>
      <h3>{order.orderNumber}</h3>
      <p>{order.status}</p>
      <button onClick={() => onCancel(order.id)}>Cancel</button>
    </article>
  );
});

// useMemo: cachea resultado de cálculo costoso
function OrderList({ orders, filterFn }: Props) {
  const filtered = useMemo(
    () => orders.filter(filterFn),
    [orders, filterFn],
  );
  return <>{filtered.map(o => <OrderCard key={o.id} order={o} />)}</>;
}

// useCallback: estabiliza referencia de función (útil con memo)
function Parent() {
  const handleCancel = useCallback((orderId: string) => {
    cancelOrder(orderId);
  }, []); // Referencia estable

  return <OrderCard order={order} onCancel={handleCancel} />;
}
```

⚠️ **No memoizar todo.** Solo componentes que:
1. Renderizan frecuentemente
2. Tienen props complejas (objetos, arrays)
3. Su padre re-renderea a menudo pero sus props rara vez cambian

---

## useTransition y useDeferredValue

```tsx
// useTransition: marcar updates como no urgentes
import { useTransition, useState } from 'react';

export function OrderSearch() {
  const [query, setQuery] = useState('');
  const [isPending, startTransition] = useTransition();

  function handleChange(e: ChangeEvent<HTMLInputElement>) {
    // Urgente: actualizar el input inmediatamente
    setQuery(e.target.value);

    // No urgente: filtrar la lista (puede esperar)
    startTransition(() => {
      setFilteredOrders(filterOrders(e.target.value));
    });
  }

  return (
    <>
      <input value={query} onChange={handleChange} />
      {isPending && <Spinner />}
      <OrderList orders={filteredOrders} /> {/* Se actualiza sin bloquear el input */}
    </>
  );
}

// useDeferredValue: versión diferida de un valor
export function OrderList({ query }: { query: string }) {
  const deferredQuery = useDeferredValue(query);
  const filtered = useMemo(
    () => filterOrders(deferredQuery),
    [deferredQuery],
  );

  return (
    <ul style={{ opacity: query !== deferredQuery ? 0.5 : 1 }}>
      {filtered.map(order => <li key={order.id}>{order.orderNumber}</li>)}
    </ul>
  );
}
```

---

## Virtualización — TanStack Virtual

```bash
npm install @tanstack/react-virtual
```

```tsx
import { useVirtualizer } from '@tanstack/react-virtual';

export function VirtualOrderList({ orders }: { orders: Order[] }) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: orders.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 72, // Altura estimada de cada fila en px
    overscan: 10,           // Renderizar 10 filas extras arriba/abajo
  });

  return (
    <div ref={parentRef} className="h-[600px] overflow-auto">
      <div style={{ height: `${virtualizer.getTotalSize()}px`, position: 'relative' }}>
        {virtualizer.getVirtualItems().map(virtualRow => (
          <div
            key={orders[virtualRow.index].id}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: `${virtualRow.size}px`,
              transform: `translateY(${virtualRow.start}px)`,
            }}
          >
            <OrderCard order={orders[virtualRow.index]} />
          </div>
        ))}
      </div>
    </div>
  );
}
```

Para 100,000 filas: solo se renderizan ~20 visibles. DOM liviano, scroll fluido.

---

## Code Splitting

```tsx
import { lazy, Suspense } from 'react';

// Por ruta (lo más efectivo)
const OrdersPage = lazy(() => import('./pages/orders.js'));
const AnalyticsPage = lazy(() => import('./pages/analytics.js'));

// Por componente pesado (charts, rich text editors)
const HeavyChart = lazy(() => import('./components/sales-chart.js'));

export function App() {
  return (
    <Suspense fallback={<PageSkeleton />}>
      <Routes>
        <Route path="/orders" element={<OrdersPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
      </Routes>
    </Suspense>
  );
}
```

### Bundle analysis

```bash
# Next.js
ANALYZE=true next build

# Vite
npm install -D rollup-plugin-visualizer
# vite.config.ts
import { visualizer } from 'rollup-plugin-visualizer';
export default defineConfig({
  plugins: [visualizer({ open: true })],
});
```

---

## React Server Components (RSC) — Zero JS

```tsx
// Server Component: 0 KB de JS enviado al cliente
import { db } from '@/lib/db';

export default async function OrderSummary() {
  const totalOrders = await db.order.count();
  const totalRevenue = await db.order.aggregate({ _sum: { totalAmount: true } });

  return (
    <div>
      <p>Total Orders: {totalOrders}</p>
      <p>Revenue: ${totalRevenue._sum.totalAmount}</p>
    </div>
  );
}
// Este componente nunca llega al bundle de JS del cliente.
```

**Regla**: mover todo lo que no necesita interactividad a Server Components. Solo `'use client'` cuando uses hooks, event handlers, o browser APIs.

---

## Streaming SSR

```tsx
import { Suspense } from 'react';

export default function OrderPage({ params }: { params: { id: string } }) {
  return (
    <div>
      <h1>Order #{params.id}</h1>

      {/* Se envía inmediatamente (no bloquea la página) */}
      <OrderHeader id={params.id} />

      {/* Se streamea cuando esté listo */}
      <Suspense fallback={<OrderItemsSkeleton />}>
        <OrderItems id={params.id} />
      </Suspense>

      {/* Otro chunk independiente */}
      <Suspense fallback={<PaymentHistorySkeleton />}>
        <PaymentHistory id={params.id} />
      </Suspense>
    </div>
  );
}
```

El HTML se envía por chunks al navegador. El usuario ve contenido inmediatamente, incluso si algunas queries son lentas.

---

## Images — next/image

```tsx
import Image from 'next/image';

// ✅ Optimización automática: WebP/AVIF, lazy loading, placeholder blur
<Image
  src="/products/widget.jpg"
  alt="Widget"
  width={400}
  height={300}
  placeholder="blur"
  priority={isHero}  // Carga eager para above-the-fold
/>
```

---

## Checklist performance

- [ ] Profiler de React DevTools antes de optimizar
- [ ] Server Components para contenido sin interactividad (0 JS)
- [ ] Streaming SSR con `<Suspense>` para datos lentos
- [ ] Code splitting por ruta (`React.lazy`)
- [ ] Virtualización para listas >500 elementos (TanStack Virtual)
- [ ] `useTransition`/`useDeferredValue` para inputs que filtran listas grandes
- [ ] `memo` solo en componentes con props que rara vez cambian
- [ ] Bundle analysis (`rollup-plugin-visualizer` o `ANALYZE=true`)
- [ ] Imágenes optimizadas (`next/image` o similar)
- [ ] Sin dependencias enormes (moment.js → date-fns, lodash → native)
- [ ] `loading="lazy"` en iframes y videos
