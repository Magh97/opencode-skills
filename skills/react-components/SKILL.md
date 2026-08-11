---
name: react-components
description: "Patrones de componentes React + TypeScript. Cubre compound components, polymorphic components, render props, slots, composición sobre herencia, Tailwind CSS 4.3, shadcn/ui 4.11, Radix y Headless UI, y accesibilidad (ARIA, focus, keyboard). Actívala al diseñar sistemas de componentes, construir design systems, o implementar UI accesible."
disable-model-invocation: true
---

# React Component Patterns

Guía de patrones de componentes en React + TypeScript con Tailwind CSS 4.3 y shadcn/ui 4.11.

---

## Composición sobre herencia

```tsx
// ❌ Herencia de props enorme
<SuperButton variant="primary" size="lg" icon={Plus} loading disabled onClick={...} />

// ✅ Composición con children y slots
<Button variant="primary" size="lg">
  <Button.Icon><Plus /></Button.Icon>
  Create Order
  <Button.Spinner /> {/* Solo visible cuando loading */}
</Button>
```

---

## Compound Components

```tsx
// Componente compuesto con Context interno
interface CardContextValue {
  isHovered: boolean;
  setIsHovered: (v: boolean) => void;
}

const CardContext = createContext<CardContextValue | null>(null);

function Card({ children, className }: { children: ReactNode; className?: string }) {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <CardContext value={{ isHovered, setIsHovered }}>
      <article className={cn('rounded-lg border', isHovered && 'shadow-md', className)}>
        {children}
      </article>
    </CardContext>
  );
}

function Header({ children }: { children: ReactNode }) {
  return <header className="border-b px-4 py-3">{children}</header>;
}

function Body({ children }: { children: ReactNode }) {
  return <div className="px-4 py-3">{children}</div>;
}

function Footer({ children }: { children: ReactNode }) {
  const ctx = useContext(CardContext);
  return <footer className="border-t px-4 py-3">{children}</footer>;
}

// Adjuntar sub-componentes
Card.Header = Header;
Card.Body = Body;
Card.Footer = Footer;

// Uso
<Card>
  <Card.Header><h3>Order #123</h3></Card.Header>
  <Card.Body>
    <p>Status: Pending</p>
    <p>Total: $150.00</p>
  </Card.Body>
  <Card.Footer>
    <Button>Cancel</Button>
  </Card.Footer>
</Card>
```

---

## Polymorphic Components

```tsx
// Componente que puede renderizarse como distintos elementos HTML
type TextProps<T extends ElementType = 'p'> = {
  as?: T;
  variant?: 'heading' | 'body' | 'caption';
} & ComponentPropsWithoutRef<T>;

export function Text<T extends ElementType = 'p'>({
  as,
  variant = 'body',
  className,
  ...props
}: TextProps<T>) {
  const Component = as ?? 'p';

  return (
    <Component
      className={cn(
        variant === 'heading' && 'text-2xl font-bold',
        variant === 'body' && 'text-base',
        variant === 'caption' && 'text-sm text-gray-500',
        className,
      )}
      {...props}
    />
  );
}

// Uso
<Text as="h1" variant="heading">Dashboard</Text>
<Text as="span" variant="caption">Last updated 5 min ago</Text>
```

---

## Tailwind CSS 4.3 + shadcn/ui 4.11

### Tailwind 4.3

```css
/* app.css — Tailwind 4.3 usa CSS-first config */
@import "tailwindcss";

/* Custom theme */
@theme {
  --color-primary: #3b82f6;
  --color-primary-foreground: #ffffff;
  --color-destructive: #ef4444;
  --radius-sm: 0.25rem;
  --radius-md: 0.375rem;
}

/* Custom utility */
@utility scrollbar-thin {
  scrollbar-width: thin;
}
```

### shadcn/ui components

```tsx
// shadcn/ui Button — importado directo, full control del código
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/table';

export function OrderDialog() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>New Order</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create Order</DialogTitle>
        </DialogHeader>
        <CreateOrderForm />
      </DialogContent>
    </Dialog>
  );
}
```

### cn() helper

```tsx
// lib/utils.ts — combinar clases condicionalmente
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Uso
<button className={cn(
  'px-4 py-2 rounded',
  variant === 'primary' && 'bg-primary text-primary-foreground',
  disabled && 'opacity-50 cursor-not-allowed',
)}>
  {children}
</button>
```

---

## Accesibilidad (a11y)

```tsx
// ✅ ARIA labels en iconos sin texto
<button aria-label="Delete order" onClick={handleDelete}>
  <Trash2 className="size-4" />
</button>

// ✅ Semántica HTML correcta
<main>
  <nav aria-label="Main navigation">...</nav>
  <article aria-labelledby="order-heading">
    <h1 id="order-heading">Order #123</h1>
  </article>
</main>

// ✅ Form labels asociados
<label htmlFor="customerId">Customer ID</label>
<Input id="customerId" name="customerId" />

// ✅ Focus management (dialog, sheet)
<Dialog onOpenChange={(open) => {
  if (!open) triggerRef.current?.focus(); // Devolver focus al trigger
}}>

// ✅ Keyboard navigation
<div role="listbox" aria-label="Orders" onKeyDown={handleListboxKeys}>
  {orders.map(order => (
    <div
      key={order.id}
      role="option"
      tabIndex={0}
      aria-selected={selected === order.id}
    >
      {order.orderNumber}
    </div>
  ))}
</div>

// ✅ Screen reader only
<span className="sr-only">Loading orders...</span>

// ✅ Live regions (anuncios dinámicos)
<div aria-live="polite" aria-atomic="true">
  {message}
</div>
```

---

## Patrones condicionales

```tsx
// ✅ Early return para estados
export function OrderView({ orderId }: { orderId: string }) {
  const { data: order, isLoading, isError, error } = useOrder(orderId);

  if (isLoading) return <Skeleton />;
  if (isError) return <ErrorAlert message={error.message} />;
  if (!order) return <NotFound resource="Order" />;

  return <OrderDetail order={order} />;
}

// ✅ Render prop para comportamiento reusable
function Toggle({
  children,
}: {
  children: (state: { on: boolean; toggle: () => void }) => ReactNode;
}) {
  const [on, setOn] = useState(false);
  return children({ on, toggle: () => setOn(v => !v) });
}

<Toggle>
  {({ on, toggle }) => (
    <button onClick={toggle}>{on ? 'Hide' : 'Show'} details</button>
  )}
</Toggle>
```

---

## Checklist componentes

- [ ] Compound components para APIs expresivas (Card, Table, Dialog)
- [ ] `cn()` helper para clases condicionales
- [ ] Tailwind 4.3 + shadcn/ui como base de UI
- [ ] Componentes accesibles: aria-label, roles, keyboard navigation
- [ ] Focus management en modals/dialogs
- [ ] `sr-only` para texto solo de screen readers
- [ ] Semántica HTML correcta (`main`, `nav`, `article`, `section`)
- [ ] Tipos exportados junto con el componente
- [ ] Sin inline styles; todo en Tailwind classes
