---
name: react-testing
description: "Testing en React con Vitest + Testing Library, Playwright E2E, y MSW. Cubre unit tests de componentes, hooks testing, integration tests con user-event, accesibilidad (axe), snapshot testing, MSW para mock de APIs, y Playwright con AI agents. Pirámide invertida 2026: más integration, menos unit. Actívala al escribir tests, configurar CI/CD, o auditar cobertura."
disable-model-invocation: true
---

# React Testing

Guía de testing en React 2026. **Vitest + Testing Library + Playwright.**

---

## Stack de testing

| Herramienta | Propósito |
|-------------|-----------|
| **Vitest 4/5** | Runner + assertions |
| **Testing Library** | Render + queries accesibles |
| **user-event** | Simulación realista de interacciones |
| **MSW** | Mock de APIs a nivel red |
| **Playwright** | E2E + AI assertions |
| **jest-axe** | Accesibilidad (a11y) |

```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom msw @playwright/test
```

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: true,
  },
});
```

```typescript
// src/test/setup.ts
import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

afterEach(() => cleanup());
```

---

## Testing Library — Unit + Integration

```tsx
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { OrderCard } from './order-card.js';

describe('OrderCard', () => {
  it('displays order information', () => {
    const order = { id: '1', orderNumber: 1001, status: 'pending', totalAmount: '150.00' };

    render(<OrderCard order={order} />);

    expect(screen.getByText('#1001')).toBeInTheDocument();
    expect(screen.getByText('pending')).toBeInTheDocument();
    expect(screen.getByText('$150.00')).toBeInTheDocument();
  });

  it('calls onCancel when cancel button clicked', async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();
    const order = { id: '1', orderNumber: 1001, status: 'pending', totalAmount: '150.00' };

    render(<OrderCard order={order} onCancel={onCancel} />);

    await user.click(screen.getByRole('button', { name: /cancel/i }));
    expect(onCancel).toHaveBeenCalledWith('1');
  });

  it('hides cancel button when order is not pending', () => {
    const order = { id: '1', orderNumber: 1001, status: 'shipped', totalAmount: '150.00' };

    render(<OrderCard order={order} />);

    expect(screen.queryByRole('button', { name: /cancel/i })).not.toBeInTheDocument();
  });
});
```

### Queries — prioridad de Testing Library

```tsx
// 1. ✅ getByRole — más accesible, verifica ARIA implícito
screen.getByRole('button', { name: 'Create Order' });
screen.getByRole('heading', { name: /orders/i });

// 2. ✅ getByLabelText — para inputs con label
screen.getByLabelText('Customer ID');

// 3. ✅ getByText — para contenido visible
screen.getByText('Order #1001');

// 4. ⚠️ getByTestId — último recurso
screen.getByTestId('order-card');
```

---

## Form testing

```tsx
it('submits form with valid data', async () => {
  const user = userEvent.setup();
  const onSubmit = vi.fn();

  render(<CreateOrderForm onSubmit={onSubmit} />);

  await user.type(screen.getByLabelText('Customer ID'), 'CUST-001');
  await user.type(screen.getByLabelText('Amount'), '150');
  await user.selectOptions(screen.getByLabelText('Currency'), 'USD');
  await user.click(screen.getByRole('button', { name: /create/i }));

  expect(onSubmit).toHaveBeenCalledWith({
    customerId: 'CUST-001',
    amount: 150,
    currency: 'USD',
  });
});

it('shows validation errors for empty fields', async () => {
  const user = userEvent.setup();

  render(<CreateOrderForm onSubmit={vi.fn()} />);

  await user.click(screen.getByRole('button', { name: /create/i }));

  expect(screen.getByText('Customer ID is required')).toBeInTheDocument();
  expect(screen.getByText('Must be positive')).toBeInTheDocument();
});
```

---

## Testing hooks

```tsx
import { renderHook, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

function createWrapper() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

it('useCounter increments', () => {
  const { result } = renderHook(() => useCounter(0));

  act(() => result.current.increment());

  expect(result.current.count).toBe(1);
});
```

---

## MSW para mock de APIs

```tsx
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

const handlers = [
  http.get('/api/orders', () => {
    return HttpResponse.json({
      data: [{ id: '1', orderNumber: 1001, status: 'pending', totalAmount: '150.00' }],
      pagination: { page: 1, totalPages: 1 },
    });
  }),

  http.post('/api/orders', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({ id: '2', ...body, status: 'pending' }, { status: 201 });
  }),
];

const server = setupServer(...handlers);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// Test que usa MSW
it('renders order list from API', async () => {
  render(<OrderList customerId="CUST-001" />);

  expect(await screen.findByText('#1001')).toBeInTheDocument();
});
```

---

## Playwright E2E

```tsx
import { test, expect } from '@playwright/test';

test.describe('Orders', () => {
  test('create and view order', async ({ page }) => {
    await page.goto('/orders');

    await page.getByRole('button', { name: 'New Order' }).click();
    await page.getByLabel('Customer ID').fill('CUST-001');
    await page.getByLabel('Amount').fill('150');
    await page.getByRole('button', { name: 'Create' }).click();

    await expect(page.getByText('#1001')).toBeVisible();
  });

  // Playwright 2026: ARIA snapshot assertion
  test('displays order details correctly', async ({ page }) => {
    await page.goto('/orders/1');

    await expect(page).toMatchAriaSnapshot(`
      - heading "Order #1001" [level=1]
      - text: Status: pending
      - text: Total: $150.00
      - button "Cancel"
      - button "Download Invoice"
    `);
  });
});
```

---

## Accessibility testing (axe)

```tsx
import { it, expect } from 'vitest';
import { render } from '@testing-library/react';
import axe from 'axe-core';

it('has no accessibility violations', async () => {
  const { container } = render(<OrderCard order={order} />);
  const results = await axe.run(container);

  expect(results.violations).toEqual([]);
});
```

---

## Pirámide de testing 2026 (invertida)

```
       ╱ E2E ╲            Playwright: pocos tests, críticos (happy paths)
      ╱───────╲
     ╱─────────╲
    ╱ Integration ╲       Testing Library + MSW: mayoría de tests
   ╱───────────────╲
  ╱     Unit         ╲    Vitest: lógica pura, hooks, utilidades
 ╱───────────────────╲
```

---

## Checklist testing

- [ ] Vitest + Testing Library como stack principal
- [ ] Queries accesibles: `getByRole` > `getByLabelText` > `getByText` > `getByTestId`
- [ ] `userEvent` sobre `fireEvent` (simula interacciones reales)
- [ ] MSW para mock de APIs
- [ ] Playwright para E2E de happy paths críticos
- [ ] axe para validar a11y
- [ ] Tests independientes (sin estado compartido)
- [ ] Sin mock de fetch global (usar MSW)
- [ ] Coverage ≥ 80% en componentes de negocio
- [ ] CI ejecuta tests antes de merge
