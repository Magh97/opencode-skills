# Performance y patrones avanzados

> Referencia de `dotnet-ef-core`. Cárgala solo cuando necesites el detalle.

## Performance

### Find vs FirstOrDefault

```csharp
// Find: busca por PK, revisa el tracker primero. Para operaciones frecuentes.
var order = await db.Orders.FindAsync([id], ct);

// FirstOrDefault: siempre va a la BD (si no está tracked). Para queries con filtros.
var order = await db.Orders.FirstOrDefaultAsync(o => o.Id == id, ct);
```

### Paginación eficiente (Keyset / Seek)

```csharp
// ❌ Offset pagination — lento en páginas altas
var page = await db.Orders
    .OrderBy(o => o.CreatedAt)
    .Skip(pageSize * pageNumber)
    .Take(pageSize)
    .ToListAsync(ct);

// ✅ Keyset pagination — usa índice, rendimiento constante
var page = await db.Orders
    .Where(o => o.CreatedAt > lastCreatedAt)
    .OrderBy(o => o.CreatedAt)
    .Take(pageSize)
    .ToListAsync(ct);
```

### Batch updates / deletes (.NET 7+)

```csharp
// ❌ Cargar entidades, modificar, guardar: N roundtrips
var orders = await db.Orders.Where(o => o.Status == OrderStatus.Pending).ToListAsync(ct);
foreach (var o in orders) o.Status = OrderStatus.Expired;
await db.SaveChangesAsync(ct);

// ✅ ExecuteUpdate: 1 roundtrip, sin cargar entidades
await db.Orders
    .Where(o => o.Status == OrderStatus.Pending && o.CreatedAt < cutoff)
    .ExecuteUpdateAsync(s => s.SetProperty(o => o.Status, OrderStatus.Expired), ct);
```

### Plan de consulta: ToQueryString()

```csharp
var query = db.Orders
    .Include(o => o.Items)
    .Where(o => o.Total.Amount > 1000);

Console.WriteLine(query.ToQueryString());
// Muestra el SQL generado — copiar a SSMS y ver plan de ejecución
```

---


## Patrones avanzados

### Vector Search (.NET 10 + SQL Server 2025)

```csharp
// EF Core 10 soporta búsqueda por similitud vectorial
// Requiere SQL Server 2025 o Azure SQL con vector type

// Almacenar embeddings
modelBuilder.Entity<Product>()
    .Property(p => p.DescriptionEmbedding)
    .HasColumnType("vector(1536)"); // 1536-dimensiones (modelo OpenAI Ada)

// Búsqueda por similitud
var queryEmbedding = await embeddingService.GetEmbeddingAsync(searchText);

var results = await db.Products
    .OrderBy(p => EF.Functions.VectorDistance(p.DescriptionEmbedding, queryEmbedding))
    .Take(top: 10)
    .Select(p => new { p.Name, p.Description, p.Price })
    .ToListAsync(ct);
```

### Value Converters

```csharp
// Guardar enum como string
builder.Property(o => o.Status)
    .HasConversion<string>()
    .HasMaxLength(20);

// Value Object ↔ columna(s)
builder.ComplexProperty(o => o.Total); // .NET 8+ (antes Owned Type)

// Custom converter
builder.Property(o => o.Tags)
    .HasConversion(
        v => string.Join(',', v),
        v => v.Split(',', StringSplitOptions.RemoveEmptyEntries).ToList())
    .HasMaxLength(500);
```

### Shadow Properties

```csharp
// Definir propiedad que no está en el modelo C#
modelBuilder.Entity<Order>().Property<DateTime>("LastModified");

// Usar en queries
var orders = await db.Orders
    .Where(o => EF.Property<DateTime>(o, "LastModified") > DateTime.UtcNow.AddDays(-7))
    .ToListAsync(ct);

// Actualizar vía interceptor, no en código de negocio
```

### TPH / TPT / TPC Inheritance

```csharp
// TPH (Table Per Hierarchy) — default, todo en una tabla con discriminador
public abstract class Payment { public int Id { get; set; } }
public class CreditCardPayment : Payment { public string LastFour { get; set; } }
public class BankTransferPayment : Payment { public string BankCode { get; set; } }

// Config
modelBuilder.Entity<Payment>()
    .HasDiscriminator<string>("PaymentType")
    .HasValue<CreditCardPayment>("CC")
    .HasValue<BankTransferPayment>("TRANSFER");

// TPT (Table Per Type) — tablas separadas para cada tipo — .NET 5+
modelBuilder.Entity<Payment>().UseTptStrategy();

// TPC (Table Per Concrete Type) — .NET 7+
modelBuilder.Entity<Payment>().UseTpcStrategy();
```

### Global Query Filters

```csharp
// Soft delete automático
builder.HasQueryFilter(o => o.Status != OrderStatus.Deleted);

// Multi-tenant
builder.HasQueryFilter(o => o.TenantId == _currentTenantId);

// Ignorar filtro cuando sea necesario
var allOrders = await db.Orders.IgnoreQueryFilters().ToListAsync(ct);
```

### HiLo / Sequence para keys

```csharp
// Sequences para IDs numéricos (reduce roundtrips vs IDENTITY)
modelBuilder.HasSequence<int>("OrderNumbers", schema: "sales")
    .StartsAt(1000)
    .IncrementsBy(10);

builder.Property(o => o.OrderNumber)
    .HasDefaultValueSql("NEXT VALUE FOR sales.OrderNumbers");
```

---
