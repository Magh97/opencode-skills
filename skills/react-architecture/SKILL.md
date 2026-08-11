---
name: react-architecture
description: "Arquitectura de aplicaciones React. Cubre estructura de proyecto (feature-based vs file-type), Next.js 16 (Turbopack, PPR, RSC) vs Vite 8 SPA vs TanStack Start, monorepo con Turborepo/Nx, micro-frontends (Module Federation), y patrones de composición a nivel aplicación. Actívala al diseñar la estructura de un proyecto React, evaluar frameworks, o planear migraciones."
disable-model-invocation: true
---

# React Architecture (2026)

Guía de arquitectura para aplicaciones React + TypeScript. Decisiones de framework, estructura y escalabilidad.

---

## Elección de framework

| Framework | Mejor para | Build tool | SSR | RSC |
|-----------|-----------|------------|-----|-----|
| **Next.js 16** | Full-stack, SSR, SEO, ecommerce | Turbopack | ✅ | ✅ |
| **Vite 8 (SPA)** | Dashboards, admin panels, PWAs | Rolldown | ❌ | ❌ |
| **TanStack Start** | SPA con type-safety extrema, SSR ligero | Vite | ✅ | ❌ (SSR + hydration) |

- **Next.js 16**: Aplicación full-stack. SEO importa. Necesitas RSC para reducir JS al cliente. Turbopack es estable y rápido.
- **Vite 8 SPA**: Dashboard interno, admin panel. SEO no importa. Quieres el build más rápido y simplicidad.
- **TanStack Start**: SPA con type safety end-to-end. Ya usas TanStack Router y Query en el ecosistema.

---

## Next.js 16 — Estructura

```
src/
├── app/                          # App Router
│   ├── layout.tsx                # Root layout (html, body, providers)
│   ├── page.tsx                  # Home page
│   ├── loading.tsx               # Root loading skeleton
│   ├── error.tsx                 # Root error boundary
│   ├── (auth)/                   # Route group (no afecta URL)
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (dashboard)/              # Route group protegido
│   │   ├── layout.tsx            # Sidebar + header
│   │   ├── orders/
│   │   │   ├── page.tsx          # List
│   │   │   ├── [id]/page.tsx     # Detail
│   │   │   ├── new/page.tsx      # Create
│   │   │   └── actions.ts        # Server Actions
│   │   └── settings/page.tsx
│   └── api/                      # API Routes (opcional, usa Server Actions/RSC)
├── components/
│   ├── orders/
│   └── ui/                       # shadcn/ui components
├── hooks/                        # Client hooks
├── lib/
│   ├── db.ts                     # Prisma singleton
│   ├── auth.ts                   # NextAuth / Auth.js
│   └── utils.ts
└── types/
```

### Data flow en Next.js 16

```
Server Component (RSC)
  ↓ direct DB query (Prisma/Drizzle)
  ↓ renderiza HTML en servidor
  ↓ envía HTML al cliente
Client Component ('use client')
  ↓ recibe data como props
  ↓ interactividad (useState, onClick, etc.)

Server Actions ('use server')
  ↓ funciones que corren en servidor
  ↓ pasadas a <form action={...}>
  ↓ revalidan cache: revalidatePath(), revalidateTag()
```

### Cache Components y PPR (Next.js 16)

```tsx
// Partial Pre-Rendering (PPR): combina static + dynamic
// Static shell se sirve del CDN, dynamic slots se streamean

export default function OrdersLayout({ children }: { children: ReactNode }) {
  return (
    <div>
      <Suspense fallback={<StatsSkeleton />}>
        <OrderStats />      {/* Se streamea cuando esté listo */}
      </Suspense>
      {children}             {/* Static shell */}
    </div>
  );
}
```

---

## Vite 8 SPA — Estructura

```
src/
├── pages/                    # Page components (manualmente code-split)
│   ├── dashboard.tsx
│   ├── orders/
│   │   ├── list.tsx
│   │   ├── detail.tsx
│   │   └── create.tsx
│   └── login.tsx
├── features/                 # Feature-based modules
│   └── orders/
│       ├── components/
│       │   ├── order-card.tsx
│       │   └── order-form.tsx
│       ├── hooks/
│       │   └── use-orders.ts
│       ├── stores/
│       │   └── order-store.ts
│       └── api/
│           └── orders-api.ts
├── shared/
│   ├── components/
│   │   └── ui/              # shadcn/ui
│   ├── hooks/
│   └── utils/
├── app.tsx                   # Entry + router setup
└── main.tsx                  # ReactDOM.createRoot
```

### Data flow en Vite SPA

```
React Router Loader
  ↓ fetch() a API backend
  ↓ retorna datos al componente
Componente
  ↓ useLoaderData() recibe datos
  ↓ TanStack Query para cache + refetch

Mutations:
  ↓ useMutation() → POST/PUT/DELETE al API backend
  ↓ onSuccess: invalida queries o actualiza cache
```

---

## Monorepo — Turborepo

```
packages/
├── apps/
│   ├── api/                  # Node.js backend
│   │   ├── src/
│   │   ├── package.json
│   │   └── tsconfig.json
│   └── web/                  # React frontend (Next.js o Vite)
│       ├── src/
│       ├── package.json
│       └── tsconfig.json
├── packages/
│   ├── shared/               # Tipos, DTOs, Zod schemas
│   │   ├── src/
│   │   │   ├── schemas/
│   │   │   └── types/
│   │   └── package.json
│   ├── database/             # Prisma schema (compartido)
│   │   └── prisma/
│   ├── ui/                   # Componentes React compartidos
│   │   └── src/
│   ├── config-eslint/
│   └── config-typescript/
├── package.json
├── turbo.json
└── pnpm-workspace.yaml
```

### Por qué monorepo

- **Tipos compartidos**: `packages/shared` exporta DTOs y Zod schemas. Backend y frontend usan los mismos tipos.
- **Sin duplicación**: Prisma schema en un solo lugar.
- **Cambios atómicos**: PR agrega campo al schema → backend lo usa → frontend lo muestra. Un solo PR.

---

## Micro-Frontends (Module Federation)

```typescript
// Solo para apps muy grandes (>5 equipos independientes)
// vite.config.ts (host app)
import { defineConfig } from 'vite';
import federation from '@originjs/vite-plugin-federation';

export default defineConfig({
  plugins: [
    federation({
      name: 'host',
      remotes: {
        orders: 'http://localhost:5001/assets/remoteEntry.js',
        catalog: 'http://localhost:5002/assets/remoteEntry.js',
      },
      shared: ['react', 'react-dom'],
    }),
  ],
});
```

⚠️ Micro-frontends agregan complejidad. Solo si la app es mantenida por equipos independientes que deployan en ciclos distintos.

---

## Principios de arquitectura React

1. **Feature-based > File-type.** Agrupar por dominio (`orders/`, `customers/`), no por tipo (`components/`, `hooks/`).
2. **Server Components por defecto.** Solo `'use client'` cuando realmente se necesita interactividad.
3. **Composición sobre configuración.** Pasar componentes como children, no flags booleanas infinitas.
4. **Data fetching en Server Components o loaders.** No `useEffect` + `useState` para fetch.
5. **Server Actions para mutaciones.** Reemplazan API routes para operaciones CRUD simples.
6. **Monorepo cuando hay backend + frontend en el mismo repo.** Tipos compartidos = menos bugs.
7. **Sin estado global innecesario.** ¿Realmente necesita Zustand/Redux o es server state que TanStack Query cubre?

---

## Checklist arquitectura

- [ ] Framework elegido según caso (Next.js 16 full-stack, Vite 8 SPA)
- [ ] Feature-based structure (modules/dominios)
- [ ] Server Components por defecto, `'use client'` mínimo
- [ ] Server Actions para mutaciones (no API routes simples)
- [ ] Monorepo con Turborepo si hay backend + frontend
- [ ] Tipos y Zod schemas compartidos en `packages/shared`
- [ ] Data fetching en loaders o RSC, no en useEffect
- [ ] Error boundaries en layouts para contención de fallos
- [ ] Loading skeletons para UX percibida rápida
- [ ] Micro-frontends solo si >5 equipos independientes
