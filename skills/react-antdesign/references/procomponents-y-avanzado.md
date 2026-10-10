# ProComponents y componentes avanzados

> Referencia de `react-antdesign`. Cárgala solo cuando necesites el detalle.

## ProComponents v3

```bash
npm install @ant-design/pro-components  # Un solo paquete, reemplaza pro-table, pro-form, etc.
```

### ProTable — Tabla con búsqueda, filtros y paginación automática

```tsx
import { ProTable } from '@ant-design/pro-components';
import type { ProColumns, ActionType } from '@ant-design/pro-components';
import { useRef } from 'react';

export function OrderProTable() {
  const actionRef = useRef<ActionType>();

  const columns: ProColumns<OrderRecord>[] = [
    {
      title: 'N.° Orden',
      dataIndex: 'orderNumber',
      key: 'orderNumber',
      valueType: 'digit',
      sorter: true,
    },
    {
      title: 'Cliente',
      dataIndex: 'customerId',
      key: 'customerId',
      fieldProps: { placeholder: 'Buscar cliente...' },
    },
    {
      title: 'Estado',
      dataIndex: 'status',
      key: 'status',
      valueType: 'select',
      valueEnum: {
        pending: { text: 'Pendiente', status: 'Processing' },
        shipped: { text: 'Enviado', status: 'Success' },
        cancelled: { text: 'Cancelado', status: 'Error' },
      },
    },
    {
      title: 'Total',
      dataIndex: 'totalAmount',
      key: 'totalAmount',
      valueType: 'money',
      sorter: true,
    },
    {
      title: 'Fecha',
      dataIndex: 'createdAt',
      key: 'createdAt',
      valueType: 'dateTime',
      sorter: true,
    },
  ];

  return (
    <ProTable<OrderRecord>
      columns={columns}
      request={async (params, sort, filter) => {
        const { data, total } = await fetchOrders({
          page: params.current!,
          pageSize: params.pageSize!,
          ...params,
          sort,
          filter,
        });
        return { data, total, success: true };
      }}
      actionRef={actionRef}
      rowKey="id"
      search={{ labelWidth: 'auto' }}
      pagination={{ pageSize: 20 }}
      dateFormatter="string"
      headerTitle="Órdenes"
      toolBarRender={() => [
        <Button key="new" type="primary" onClick={handleCreate}>
          Nueva Orden
        </Button>,
      ]}
    />
  );
}
```

### ProForm — Formularios con diseño responsive

```tsx
import { ProForm, ProFormText, ProFormSelect, ProFormDigit } from '@ant-design/pro-components';

<ProForm
  onFinish={async (values) => {
    await createOrder(values);
    return true; // No cerrar drawer/modal
  }}
>
  <ProFormText
    name="customerId"
    label="ID del Cliente"
    rules={[{ required: true }]}
    placeholder="CUST-001"
  />
  <ProFormDigit
    name="amount"
    label="Monto"
    rules={[{ required: true }]}
    min={0.01}
    fieldProps={{ precision: 2 }}
  />
  <ProFormSelect
    name="currency"
    label="Moneda"
    options={[
      { label: 'MXN', value: 'MXN' },
      { label: 'USD', value: 'USD' },
      { label: 'EUR', value: 'EUR' },
    ]}
  />
</ProForm>
```

---


## Select con búsqueda remota (API)

```tsx
import { Select } from 'antd';
import { useState } from 'react';
import { useDebounce } from 'ahooks';

export function CustomerSelect({ onChange }: { onChange: (id: string) => void }) {
  const [options, setOptions] = useState<{ label: string; value: string }[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const debouncedSearch = useDebounce(search, { wait: 300 });

  useEffect(() => {
    if (!debouncedSearch) return;
    setLoading(true);
    fetch(`/api/customers?q=${debouncedSearch}`)
      .then(r => r.json())
      .then(data => setOptions(data.map((c: any) => ({ label: c.name, value: c.id }))))
      .finally(() => setLoading(false));
  }, [debouncedSearch]);

  return (
    <Select
      showSearch
      placeholder="Buscar cliente..."
      filterOption={false}
      onSearch={setSearch}
      loading={loading}
      options={options}
      onChange={onChange}
      style={{ width: '100%' }}
    />
  );
}
```

---


## Modal y Drawer

```tsx
import { Modal, Drawer, Button } from 'antd';

// Modal para confirmaciones
function CancelOrderModal({ orderId, onClose }: Props) {
  return (
    <Modal
      title="Cancelar Orden"
      open
      onOk={async () => {
        await cancelOrder(orderId);
        message.success('Orden cancelada');
        onClose();
      }}
      onCancel={onClose}
      okText="Sí, cancelar"
      cancelText="No"
      okButtonProps={{ danger: true }}
    >
      ¿Estás seguro de cancelar la orden?
    </Modal>
  );
}

// Drawer para formularios laterales
<Drawer
  title="Crear Orden"
  open={open}
  onClose={() => setOpen(false)}
  width={600}
>
  <CreateOrderForm onSuccess={() => setOpen(false)} />
</Drawer>
```

---


## Ant Design Pro v6 (scaffolding)

Ant Design Pro v6 es la plantilla completa para proyectos nuevos. Cambios clave vs v5:

| v5 | v6 |
|----|----|
| Less + CSS Modules | **Tailwind + antd-style + CSS Modules** |
| umi-request | **@tanstack/react-query** |
| Moment.js | **Day.js** |
| ESLint + Prettier | **Biome** |
| React 18 | **React 19** |

Proyectos nuevos del equipo Sputnik pueden usar Pro v6 como base. Proyectos existentes probablemente están en v5 → migrar gradualmente.

---
