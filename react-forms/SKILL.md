---
name: react-forms
description: "Formularios en React con React Hook Form + Zod y Server Actions. Cubre validación client-side y server-side, arrays dinámicos (useFieldArray), file upload, controlled vs uncontrolled, formularios multi-step, y patrones con useActionState. Actívala al implementar formularios complejos, validación, o manejo de archivos."
disable-model-invocation: true
---

# React Forms

Guía de formularios en React 19. **React Hook Form + Zod** para client-side forms. **Server Actions** para server-side.

---

## React Hook Form + Zod

```bash
npm install react-hook-form zod @hookform/resolvers
```

```tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const CreateOrderSchema = z.object({
  customerId: z.string().min(1, 'Customer ID is required'),
  amount: z.coerce.number().positive('Must be positive'),
  currency: z.enum(['MXN', 'USD', 'EUR']).default('MXN'),
  notes: z.string().max(500).optional(),
});

type CreateOrderInput = z.infer<typeof CreateOrderSchema>;

export function CreateOrderForm() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<CreateOrderInput>({
    resolver: zodResolver(CreateOrderSchema),
    defaultValues: { currency: 'MXN' },
  });

  const onSubmit = async (data: CreateOrderInput) => {
    const response = await fetch('/api/orders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (response.ok) reset();
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label htmlFor="customerId">Customer ID</label>
        <input id="customerId" {...register('customerId')} />
        {errors.customerId && <p className="text-red-500">{errors.customerId.message}</p>}
      </div>

      <div>
        <label htmlFor="amount">Amount</label>
        <input id="amount" type="number" step="0.01" {...register('amount')} />
        {errors.amount && <p className="text-red-500">{errors.amount.message}</p>}
      </div>

      <div>
        <label htmlFor="currency">Currency</label>
        <select id="currency" {...register('currency')}>
          <option value="MXN">MXN</option>
          <option value="USD">USD</option>
          <option value="EUR">EUR</option>
        </select>
      </div>

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Creating...' : 'Create Order'}
      </button>
    </form>
  );
}
```

---

## useFieldArray (arrays dinámicos)

```tsx
import { useFieldArray } from 'react-hook-form';

const OrderWithItemsSchema = z.object({
  customerId: z.string().min(1),
  items: z.array(z.object({
    sku: z.string().min(1),
    quantity: z.coerce.number().int().min(1),
    unitPrice: z.coerce.number().positive(),
  })).min(1, 'At least one item required'),
});

export function OrderWithItemsForm() {
  const { register, control, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(OrderWithItemsSchema),
    defaultValues: { items: [{ sku: '', quantity: 1, unitPrice: 0 }] },
  });

  const { fields, append, remove } = useFieldArray({ control, name: 'items' });

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      {fields.map((field, index) => (
        <div key={field.id} className="flex gap-2">
          <input {...register(`items.${index}.sku`)} placeholder="SKU" />
          <input {...register(`items.${index}.quantity`)} type="number" />
          <input {...register(`items.${index}.unitPrice`)} type="number" step="0.01" />
          <button type="button" onClick={() => remove(index)}>Remove</button>
        </div>
      ))}
      {errors.items?.message && <p className="text-red-500">{errors.items.message}</p>}

      <button type="button" onClick={() => append({ sku: '', quantity: 1, unitPrice: 0 })}>
        Add Item
      </button>
      <button type="submit">Create Order</button>
    </form>
  );
}
```

---

## Server Actions (React 19)

```tsx
// actions.ts
'use server';

import { z } from 'zod';
import { db } from '@/lib/db';
import { revalidatePath } from 'next/cache';

const CreateOrderSchema = z.object({
  customerId: z.string().min(1),
  amount: z.coerce.number().positive(),
});

export async function createOrder(formData: FormData) {
  'use server';
  const raw = Object.fromEntries(formData);
  const parsed = CreateOrderSchema.safeParse(raw);

  if (!parsed.success) {
    return { error: parsed.error.flatten().fieldErrors };
  }

  const order = await db.order.create({ data: parsed.data });
  revalidatePath('/orders');
  return { error: null, order };
}

// Form component (Server Component)
import { createOrder } from './actions.js';

export default function CreateOrderPage() {
  return (
    <form action={createOrder} className="space-y-4">
      <input name="customerId" required />
      <input name="amount" type="number" step="0.01" required />
      <button type="submit">Create</button>
    </form>
  );
}

// Con useActionState para feedback
'use client';
import { useActionState } from 'react';

export function CreateOrderForm() {
  const [state, action, isPending] = useActionState(createOrder, { error: null, order: null });

  return (
    <form action={action}>
      {/* ... */}
      {isPending && <Spinner />}
      {state.error && <Alert>{JSON.stringify(state.error)}</Alert>}
      {state.order && <p>Created #{state.order.id}</p>}
    </form>
  );
}
```

---

## File Upload

```tsx
// Con React Hook Form
const FileUploadSchema = z.object({
  file: z.instanceof(File).refine(f => f.size <= 10 * 1024 * 1024, 'Max 10MB'),
  description: z.string().optional(),
});

export function UploadForm() {
  const { register, handleSubmit, watch } = useForm({
    resolver: zodResolver(FileUploadSchema),
  });

  const file = watch('file');

  return (
    <form onSubmit={handleSubmit(async (data) => {
      const formData = new FormData();
      formData.append('file', data.file);
      formData.append('description', data.description ?? '');
      await fetch('/api/upload', { method: 'POST', body: formData });
    })}>
      <input
        type="file"
        accept="image/*,.pdf"
        {...register('file', {
          onChange: (e) => e.target.files?.[0],
        })}
      />
      {file && <p>Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)</p>}

      <input {...register('description')} placeholder="Description" />
      <button type="submit">Upload</button>
    </form>
  );
}
```

---

## Controlled vs Uncontrolled

```tsx
// ✅ Controlled: React maneja el valor. Fuente de verdad = estado de React.
function ControlledInput() {
  const [value, setValue] = useState('');
  return <input value={value} onChange={e => setValue(e.target.value)} />;
}

// ✅ Uncontrolled: DOM maneja el valor. React Hook Form usa uncontrolled por defecto.
function UncontrolledForm() {
  return (
    <form action={serverAction}>
      <input name="customerId" defaultValue="CUST-" /> {/* DOM mantiene el valor */}
    </form>
  );
}
```

React Hook Form usa **uncontrolled** (mejor rendimiento, menos re-renders). Solo se vuelve controlled si usas `watch()` para reactividad.

---

## Validación server-side + client-side

```tsx
// Schema compartido entre client y server
// packages/shared/src/schemas/order-schema.ts
import { z } from 'zod';

export const CreateOrderSchema = z.object({
  customerId: z.string().min(1, 'Required'),
  amount: z.coerce.number().positive('Must be positive'),
});

// Client: validación con RHF
const form = useForm({ resolver: zodResolver(CreateOrderSchema) });

// Server: validación explícita
export async function createOrder(formData: FormData) {
  const parsed = CreateOrderSchema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) {
    return { errors: parsed.error.flatten().fieldErrors };
  }
  // ...proceed
}
```

---

## Checklist forms

- [ ] Zod schema compartido entre client y server
- [ ] React Hook Form para formularios complejos (>3 campos)
- [ ] Server Actions para mutaciones directas sin API route
- [ ] useActionState para feedback (loading, error, success)
- [ ] File upload con validación de tamaño y tipo
- [ ] useFieldArray para listas dinámicas (items, direcciones)
- [ ] Labels asociados (`htmlFor`/`id`) para accesibilidad
- [ ] Mensajes de error descriptivos junto al campo
- [ ] `disabled` en botón durante `isSubmitting`/`isPending`
