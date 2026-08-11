---
name: react-core
description: "Guía principal de React 19 + TypeScript. Cubre componentes funcionales, hooks (useState, useEffect, useRef, useId, use, useActionState, useOptimistic), JSX tipado, eventos, Suspense, Server Components vs Client Components, Strict Mode, y fundamentos del framework. Actívala para cualquier tarea React: nuevas features, migraciones, revisión de código. Las sub-skills del kit profundizan en dominios específicos."
---

# React 19 + TypeScript Core Guide

Guía canónica para desarrollo React 19 con TypeScript. React 19 estabiliza Server Components, Actions y nuevos hooks. Todo código sigue estas reglas.

---

## React 19 — Novedades clave (2025-2026)

| Feature | Descripción | Reemplaza a |
|---------|------------|-------------|
| **Server Components (RSC)** | Componentes que solo corren en servidor. 0 JS al cliente. | — |
| **`use()`** | Lee Promises y Context directamente en render | `useEffect` + `useState` para fetch |
| **`useActionState`** | Maneja estado de Server Actions (loading, error, data) | `useFormState` (deprecated) |
| **`useOptimistic`** | UI optimista con rollback automático | Mutación manual + catch |
| **`useFormStatus`** | Estado del formulario padre desde hijo | Context manual |
| **Actions (form actions)** | Funciones pasadas a `action` prop de `<form>` | `onSubmit` + `event.preventDefault()` |
| **ref como prop** | `ref` se pasa como prop normal, sin `forwardRef` | `forwardRef` |
| **`<Context>` como provider** | `React.createContext` devuelve `Context.Provider` directamente | — |

---

## Componentes funcionales

```tsx
// ✅ Function component con props tipados
interface OrderCardProps {
  order: Order;
  onCancel?: (orderId: string) => void;
}

export function OrderCard({ order, onCancel }: OrderCardProps) {
  return (
    <article className="rounded-lg border p-4">
      <h3>Order #{order.orderNumber}</h3>
      <p>Status: {order.status}</p>
      <p>Amount: ${order.totalAmount}</p>
      {onCancel && (
        <button onClick={() => onCancel(order.id)}>Cancel</button>
      )}
    </article>
  );
}
```

### Server Component vs Client Component

```tsx
// Server Component (default en Next.js App Router, TanStack Start)
// ✅ Acceso directo a DB, sin useState/useEffect/event handlers
import { db } from '@/lib/db';

export default async function OrdersPage() {
  const orders = await db.order.findMany({ take: 20 });
  return (
    <ul>
      {orders.map(order => (
        <li key={order.id}>{order.orderNumber}</li>
      ))}
    </ul>
  );
}

// Client Component — necesita interactividad
'use client';

import { useState } from 'react';

export function OrderForm() {
  const [customerId, setCustomerId] = useState('');

  return (
    <form action={createOrderAction}>
      <input
        name="customerId"
        value={customerId}
        onChange={e => setCustomerId(e.target.value)}
      />
      <button type="submit">Create Order</button>
    </form>
  );
}
```

---

## Hooks esenciales

### useState y useEffect

```tsx
// useState con tipo inferido o explícito
const [count, setCount] = useState(0);
const [status, setStatus] = useState<OrderStatus>('pending');
const [orders, setOrders] = useState<Order[]>([]);

// useEffect: sincronizar con sistemas externos
useEffect(() => {
  const controller = new AbortController();

  fetch(`/api/orders/${id}`, { signal: controller.signal })
    .then(res => res.json())
    .then(setOrder);

  return () => controller.abort(); // Cleanup
}, [id]); // Dependencias correctas
```

### use() — React 19

```tsx
// ✅ Leer Promise directamente en render (con Suspense)
import { use, Suspense } from 'react';

async function fetchOrder(id: string) {
  const res = await fetch(`/api/orders/${id}`);
  return res.json();
}

function OrderDetail({ orderPromise }: { orderPromise: Promise<Order> }) {
  const order = use(orderPromise); // Suspende hasta que la Promise resuelve
  return <div>{order.customerId} — {order.status}</div>;
}

export default function Page({ params }: { params: { id: string } }) {
  const orderPromise = fetchOrder(params.id);

  return (
    <Suspense fallback={<OrderSkeleton />}>
      <OrderDetail orderPromise={orderPromise} />
    </Suspense>
  );
}
```

### useActionState — React 19

```tsx
import { useActionState } from 'react';
import { createOrder } from './actions.js';

export function CreateOrderForm() {
  const [state, formAction, isPending] = useActionState(createOrder, {
    error: null,
    order: null,
  });

  return (
    <form action={formAction}>
      <input name="customerId" required />
      <input name="amount" type="number" required />
      <button type="submit" disabled={isPending}>
        {isPending ? 'Creating...' : 'Create Order'}
      </button>
      {state.error && <p className="text-red-500">{state.error}</p>}
      {state.order && <p>Created: #{state.order.orderNumber}</p>}
    </form>
  );
}

// actions.ts
'use server';
export async function createOrder(prevState: State, formData: FormData) {
  const customerId = formData.get('customerId') as string;
  const amount = Number(formData.get('amount'));
  try {
    const order = await db.order.create({ data: { customerId, amount } });
    return { error: null, order };
  } catch {
    return { error: 'Failed to create order', order: null };
  }
}
```

### useOptimistic — React 19

```tsx
import { useOptimistic } from 'react';

export function OrderList({ orders }: { orders: Order[] }) {
  const [optimisticOrders, addOptimistic] = useOptimistic(
    orders,
    (state, newOrder: Order) => [newOrder, ...state],
  );

  async function handleCreate(formData: FormData) {
    const tempOrder = { id: 'temp', customerId: '...', status: 'pending' };
    addOptimistic(tempOrder);
    await createOrderAction(formData); // Si falla, React revierte el optimismo
  }

  return (
    <form action={handleCreate}>
      {/* ... */}
      <ul>
        {optimisticOrders.map(order => (
          <li key={order.id}>{order.status}</li>
        ))}
      </ul>
    </form>
  );
}
```

---

## Eventos tipados

```tsx
import { type MouseEvent, type ChangeEvent, type FormEvent } from 'react';

// Click
function handleClick(e: MouseEvent<HTMLButtonElement>) {
  e.preventDefault();
  console.log(e.currentTarget.value);
}

// Input change
function handleChange(e: ChangeEvent<HTMLInputElement>) {
  setName(e.target.value);
}

// Form submit
function handleSubmit(e: FormEvent<HTMLFormElement>) {
  e.preventDefault();
  const formData = new FormData(e.currentTarget);
}

// Keyboard
function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
  if (e.key === 'Escape') close();
  if (e.key === 'Enter') submit();
}
```

---

## Suspense y Error Boundaries

```tsx
import { Suspense } from 'react';
import { ErrorBoundary } from 'react-error-boundary';

export default function OrderPage({ params }: { params: { id: string } }) {
  return (
    <ErrorBoundary fallback={<OrderError />}>
      <Suspense fallback={<OrderSkeleton />}>
        <OrderDetail id={params.id} />
      </Suspense>
    </ErrorBoundary>
  );
}

// Error Boundary con reset
function OrderError({ error, resetErrorBoundary }: FallbackProps) {
  return (
    <div role="alert">
      <p>Failed to load order: {error.message}</p>
      <button onClick={resetErrorBoundary}>Retry</button>
    </div>
  );
}
```

---

## Strict Mode

```tsx
// React 19 Strict Mode: doble render en desarrollo para detectar efectos impuros
<StrictMode>
  <App />
</StrictMode>
```

⚠️ En desarrollo, `useEffect` se ejecuta dos veces. No es un bug, es intencional.

---

## Convenciones de código

### Naming

| Elemento | Convención | Ejemplo |
|----------|------------|---------|
| Componentes | `PascalCase` | `OrderCard`, `CreateOrderForm` |
| Hooks custom | `use + PascalCase` | `useOrders()`, `useAuth()` |
| Event handlers | `handle + Evento` | `handleSubmit`, `handleClick` |
| Props types | `ComponentName + Props` | `OrderCardProps` |
| Archivos | `kebab-case.tsx` | `order-card.tsx` |

### Estructura de proyecto

```
src/
├── app/                     # Next.js App Router
│   ├── orders/
│   │   ├── page.tsx
│   │   ├── [id]/page.tsx
│   │   └── actions.ts
│   └── layout.tsx
├── components/
│   ├── orders/
│   │   ├── order-card.tsx
│   │   ├── order-form.tsx
│   │   └── order-list.tsx
│   └── ui/                   # shadcn/ui components
│       ├── button.tsx
│       └── input.tsx
├── hooks/
│   ├── use-orders.ts
│   └── use-auth.ts
├── lib/
│   ├── db.ts
│   └── utils.ts
└── types/
    └── order.ts
```

---

## Reglas de oro

1. **Un componente por archivo.** Nombre del archivo = nombre del componente en kebab-case.
2. **Props tipadas siempre.** `interface MyComponentProps { ... }`.
3. **`'use client'` solo donde se necesita interactividad.** Default: Server Component.
4. **`use()` + Suspense sobre `useEffect` + `useState` para data fetching.**
5. **`useActionState` + Server Actions sobre `onSubmit` manual.**
6. **`useOptimistic` para UI instantánea con rollback automático.**
7. **`key` estable en listas.** No usar `index` si la lista se reordena.
8. **`AbortController` en `useEffect` fetch.** Evita memory leaks y race conditions.
9. **Components pequeños.** Si un componente tiene >200 líneas, probablemente debería dividirse.
10. **Evitar `any`.** Si un tipo es complejo, vale la pena definirlo.

---

## Sub-skills del kit

> 📁 Cada sub-skill tiene su guía detallada en `./{nombre}/GUIDE.md`. Usa `read` para cargarla cuando el tema lo requiera.


| Skill | Cuándo cargarla |
|-------|-----------------|
| `react-state` | Zustand, Redux Toolkit, TanStack Query, Context |
| `react-routing` | React Router v7, TanStack Router, loaders, guards |
| `react-components` | Compound, polymorphic, Tailwind 4.3, shadcn/ui, a11y |
| `react-antdesign` | Ant Design 5.29 + ProComponents v3 — stack del equipo Sputnik (Vite + Ant Design) |
| `react-forms` | React Hook Form + Zod, Server Actions, file upload |
| `react-performance` | memo, virtualization, code splitting, RSC, streaming |
| `react-testing` | Vitest + Testing Library, Playwright E2E, MSW |
| `react-architecture` | Project structure, Next.js 16 vs Vite 8, monorepo, micro-frontends |

---

## Stack recomendado

| Propósito | Herramienta |
|-----------|-------------|
| Framework | Next.js 16 (full-stack) o Vite 8 (SPA) |
| UI Components | shadcn/ui 4.11 + Tailwind CSS 4.3 (o Ant Design 5.29 para stack Sputnik) |
| Forms | React Hook Form + Zod |
| State (server) | TanStack Query v5 |
| State (client) | Zustand v5 |
| Testing | Vitest + Testing Library + Playwright |
