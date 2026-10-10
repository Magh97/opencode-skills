# Refactoring y condicionales

> Referencia de `dotnet-clean-code`. Cárgala solo cuando necesites el detalle.

## Conditionals

### Early return sobre anidamiento

```csharp
// ❌ Pirámide del horror
public async Task<IActionResult> GetOrderAsync(Guid id)
{
    var order = await _repository.GetByIdAsync(id);
    if (order is not null)
    {
        if (order.Status != OrderStatus.Deleted)
        {
            if (_authorization.CanView(User, order))
            {
                return Ok(OrderDto.From(order));
            }
            else
            {
                return Forbid();
            }
        }
        else
        {
            return NotFound();
        }
    }
    else
    {
        return NotFound();
    }
}

// ✅ Early returns — flujo principal sin indentación
public async Task<IActionResult> GetOrderAsync(Guid id)
{
    var order = await _repository.GetByIdAsync(id);
    if (order is null) return NotFound();
    if (order.Status == OrderStatus.Deleted) return NotFound();
    if (!_authorization.CanView(User, order)) return Forbid();

    return Ok(OrderDto.From(order));
}
```

### Switch expression sobre if-else en cadena

```csharp
// ✅ Switch expression para mapeos
string GetStatusLabel(OrderStatus status) => status switch
{
    OrderStatus.Pending => "Pending Review",
    OrderStatus.Confirmed => "Confirmed",
    OrderStatus.Shipped => "Shipped",
    OrderStatus.Delivered => "Delivered",
    OrderStatus.Cancelled => "Cancelled",
    _ => "Unknown"
};

// ✅ Pattern matching con propiedades
string DescribeOrder(Order order) => order switch
{
    { Status: OrderStatus.Pending, Items.Count: > 10 } => "Large pending order",
    { Status: OrderStatus.Pending } => "Pending order",
    { Total: > 1000 } => "High-value order",
    _ => "Standard order"
};
```

---


## Refactoring: code smells .NET

### 1. Método largo → Extract Method

```csharp
// ❌ Todo en uno
public async Task ProcessAsync(Order order, CancellationToken ct)
{
    // validar
    if (order.Items.Count == 0) throw new...
    // calcular
    order.Total = order.Items.Sum(...)
    // guardar
    await _db.SaveChangesAsync(ct);
    // notificar
    await _email.SendAsync(...)
}

// ✅ Extraer a métodos privados nombrados → luego a clases si crecen
public async Task ProcessAsync(Order order, CancellationToken ct)
{
    ValidateOrder(order);
    CalculateTotals(order);
    await SaveAsync(order, ct);
    await NotifyAsync(order, ct);
}
```

### 2. Feature Envy → Move Method

```csharp
// ❌ OrderService obsesionado con los datos de Order
public class OrderService
{
    public decimal CalculateTotal(Order order)
    {
        return order.Items.Sum(i => i.Price * i.Quantity)
               - order.Discounts.Sum(d => d.Amount)
               + order.Taxes.Sum(t => t.Amount);
    }
}

// ✅ El cálculo pertenece a Order
public class Order
{
    public Money CalculateTotal() =>
        Items.Sum(i => i.LineTotal) - Discounts.Sum(d => d.Amount) + Taxes.Sum(t => t.Amount);
}
```

### 3. Primitive Obsession → Value Objects

```csharp
// ❌ Primitivos para conceptos de dominio
public class Order
{
    public string CustomerEmail { get; set; }        // string cualquiera
    public string Currency { get; set; }             // "USD", "MXN", "eur"?
    public decimal Total { get; set; }               // ¿IVA incluido?
}

// ✅ Value objects
public record Email
{
    public string Value { get; }
    public Email(string value)
    {
        if (string.IsNullOrWhiteSpace(value) || !value.Contains('@'))
            throw new ArgumentException("Invalid email", nameof(value));
        Value = value.Trim().ToLowerInvariant();
    }
}

public record Money(decimal Amount, string Currency)
{
    public static Money Zero(string currency = "MXN") => new(0, currency);
    public static Money operator +(Money a, Money b) =>
        a.Currency == b.Currency ? new(a.Amount + b.Amount, a.Currency)
        : throw new InvalidOperationException("Currency mismatch");
}

public class Order
{
    public Email CustomerEmail { get; set; }
    public Money Total { get; set; }
}
```

### 4. Shotgun Surgery → Consolidar responsabilidad

Si un cambio de negocio te obliga a modificar 6 archivos, la responsabilidad está dispersa.

```csharp
// ❌ Agregar un campo "TaxId" al cliente requiere tocar:
// - Customer.cs (entidad)
// - CustomerDto.cs
// - CreateCustomerRequest.cs
// - UpdateCustomerRequest.cs
// - CustomerConfiguration.cs (EF)
// - CustomerValidator.cs
// - CustomerMappingProfile.cs
// --- 7 archivos para 1 campo ---

// ✅ Solución: definir el concepto una vez
// Domain/Customers/Customer.cs → el resto se deriva o se genera
// Si usas source generators: el DTO, el validator parcial, y el mapping
// se actualizan automáticamente.
```

### 5. Dead Code → Delete

```csharp
// ❌ Código comentado "por si acaso"
// private void OldPaymentMethod() { ... }

// ❌ Método sin referencias
public void LegacyExport() { ... } // Ningún caller, 3 años así

// ❌ Enum values no usados
public enum OrderStatus
{
    Draft,         // ✅ usado
    Pending,       // ✅ usado
    Confirmed,     // ✅ usado
    Archived,      // ❌ nunca se usó. Borrar.
    Legacy_Migrated // ❌ código de migración de hace 2 años
}
```

---
