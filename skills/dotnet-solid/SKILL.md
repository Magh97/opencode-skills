---
name: dotnet-solid
description: Principios SOLID, DRY, KISS, YAGNI aplicados a .NET y C#. Cada principio con ejemplos de violación vs corrección, patrones .NET que los implementan naturalmente, y cuándo es razonable romperlos. Incluye Separation of Concerns, Law of Demeter, Composition over Inheritance, y otros principios complementarios. Actívala al diseñar clases, revisar acoplamiento o refactorizar código legacy.
disable-model-invocation: true
---

# SOLID y Principios de Diseño en .NET

Guía práctica. Cada principio responde **qué es**, **violación típica en .NET**, **corrección idiomática**, y **cuándo ignorarlo**.

---

## SOLID — resumen

| Principio | Idea | Idioma .NET |
|-----------|------|-------------|
| **SRP** | Una clase, una razón para cambiar | Separar orquestación, persistencia y presentación |
| **OCP** | Abierto a extensión, cerrado a modificación | Strategy/DI + interfaces; evitar `switch` creciente |
| **LSP** | Subtipos sustituibles sin sorpresas | No lanzar `NotSupportedException` en overrides |
| **ISP** | Interfaces pequeñas y específicas | Varias interfaces de rol, no una gorda |
| **DIP** | Depender de abstracciones | Inyectar `ILogger`, `IOrderRepository`, no `new` |

El detalle de cada principio (violación vs corrección, cuándo ignorarlo) está en `references/solid-detalle.md`.

---

## DRY — Don't Repeat Yourself

> Cada pieza de conocimiento debe tener una representación única y autoritativa.

### DRY bien aplicado

```csharp
// ❌ Lógica de cálculo de impuesto duplicada en 5 lugares
// OrderService.cs
var tax = order.Subtotal * 0.16m;
// InvoiceService.cs
var tax = subtotal * 0.16m;
// ReportService.cs
var tax = order.Subtotal * 0.16m;

// ✅ Única fuente de verdad
public static class TaxCalculator
{
    public const decimal IvaRate = 0.16m;

    public static Money CalculateIva(Money subtotal) =>
        subtotal * IvaRate;
}
```

### DRY mal aplicado (prematuro)

```csharp
// ❌ DRY prematuro: abstraer código que solo COINCIDE, no que comparte RAZÓN DE CAMBIO
public class OrderReportPdfGenerator { ... }
public class InvoicePdfGenerator { ... }

// Forzar DRY crea acoplamiento
public abstract class BasePdfGenerator<TData> // ← acopla cosas que cambian por razones distintas
{
    protected abstract string GenerateHeader(TData data);
    protected abstract string GenerateBody(TData data);
    // Si Invoice cambia su header, Order ahora también hereda el método
}
```

### La regla DRY

> Extraer solo cuando haya **3 o más repeticiones** Y compartan la misma **razón de cambio**. Dos repeticiones idénticas pero con razones de cambio distintas → dejarlas duplicadas temporalmente.

```csharp
// ✅ Duplicación aceptable: mismo código, distinta razón de cambio
// OrderValidator.cs — cambia cuando cambian reglas de órdenes
RuleFor(o => o.CustomerId).NotEmpty().MaximumLength(50);

// CustomerValidator.cs — cambia cuando cambian reglas de clientes
RuleFor(c => c.Id).NotEmpty().MaximumLength(50);

// Forzarlos a compartir una "base" los acoplaría incorrectamente.
```

---

## KISS — Keep It Simple, Stupid

> La solución más simple que funciona es la correcta.

### Ejemplos en .NET

```csharp
// ❌ Over-engineering: patrón Strategy para elegir entre 2 formatos fijos
public interface IDateFormatter { string Format(DateTime date); }
public class IsoDateFormatter : IDateFormatter { ... }
public class UsDateFormatter : IDateFormatter { ... }

// ✅ KISS: un método con parámetro
public static string FormatDate(DateTime date, string format = "yyyy-MM-dd")
    => date.ToString(format);

// ❌ Over-engineering: crear una clase para una validación simple
public class CustomerEmailValidator
{
    private readonly Regex _regex = new(@"^[^@\s]+@[^@\s]+\.[^@\s]+$");

    public ValidationResult Validate(string email)
    {
        if (string.IsNullOrWhiteSpace(email))
            return ValidationResult.Error("Email required");
        if (!_regex.IsMatch(email))
            return ValidationResult.Error("Invalid format");
        return ValidationResult.Success();
    }
}

// ✅ KISS: DataAnnotation + FluentValidation
public class CreateCustomerRequest
{
    [Required, EmailAddress]
    public string Email { get; init; } = string.Empty;
}
```

### KISS en arquitectura

| Complejidad | Alternativa KISS |
|-------------|-----------------|
| Clean Architecture con 4 proyectos | 2 proyectos (Api + App) hasta que duela |
| CQRS con MediatR (nota: desde v13 requiere licencia de pago para uso comercial; alternativas gratuitas: `Mediator` de martinothamar o CQRS manual) | Llamada directa a servicio |
| Microservicios | Modular Monolith |
| Event Sourcing | CRUD con historial de cambios en una tabla de auditoría |
| Kubernetes para un monolito | App Service / VM |

---

## YAGNI — You Ain't Gonna Need It

> No implementar hasta que se necesite.

### Violaciones típicas en .NET

```csharp
// ❌ "Vamos a necesitar multi-tenancy en el futuro"
public interface ITenantProvider { ... }
public class SingleTenantProvider : ITenantProvider { ... }  // Solo hay 1 tenant

// ✅ Eliminar hasta que se necesite. Agregar en el PR que lo requiera.
// Si la feature de multi-tenancy nunca llega: código muerto eliminado.

// ❌ "Quizás cambiemos de SQL Server a PostgreSQL"
public interface IRepository<T> where T : class
{
    Task<T?> GetByIdAsync(int id);
    Task<List<T>> GetAllAsync();
    Task AddAsync(T entity);
    Task UpdateAsync(T entity);
    Task DeleteAsync(T entity);
    // 30 métodos más que solo delegan a DbSet
}

// ✅ EF Core ya abstrae el motor de BD. YAGNI el repo genérico.

// ❌ Configuración para un feature flag que nunca se activará
"Features": {
  "EnableNewCheckout": false,  // ← 2 años en false, nunca se activó
  "EnableDarkMode": false
}

// ✅ Borrar. Cuando se necesite, se agrega. Git tiene la historia.
```

---

## Principios complementarios

### Separation of Concerns (SoC)

```csharp
// ✅ Separación por responsabilidad
// Orders/CreateOrder/           ← carpeta = feature vertical
// ├── CreateOrderEndpoint.cs    ← HTTP concern
// ├── CreateOrderCommand.cs     ← contrato
// ├── CreateOrderHandler.cs     ← lógica de negocio
// └── CreateOrderValidator.cs   ← validación

// ❌ Separación técnica que esparce la feature en 5 proyectos
// Controllers/OrdersController.cs
// Services/OrderService.cs
// Models/OrderDto.cs
// Validators/OrderValidator.cs
// Data/OrderRepository.cs
```

### Composition over Inheritance

```csharp
// ❌ Herencia forzada
public class AuditableEntity
{
    public DateTime CreatedAt { get; set; }
    public string CreatedBy { get; set; }
    public DateTime? UpdatedAt { get; set; }
    public string UpdatedBy { get; set; }
}

public class Order : AuditableEntity { ... }  // Forzado a heredar campos que quizás no aplican

// ✅ Composición (opcional)
public interface IAuditable
{
    DateTime CreatedAt { get; }
    string CreatedBy { get; }
}

public record Order : IAuditable { ... }

// ✅ O mejor: interceptor que agrega auditoría sin tocar la entidad
public class AuditableInterceptor : SaveChangesInterceptor
{
    public override ValueTask<InterceptionResult<int>> SavingChangesAsync(
        DbContextEventData eventData,
        InterceptionResult<int> result,
        CancellationToken ct = default)
    {
        foreach (var entry in eventData.Context!.ChangeTracker.Entries<IAuditable>())
        {
            if (entry.State == EntityState.Added)
            {
                entry.Entity.CreatedAt = DateTime.UtcNow;
                // entry.Entity.CreatedBy = currentUser...
            }
        }
        return new(result);
    }
}
```

### Law of Demeter (LoD) — Principio de mínimo conocimiento

```csharp
// ❌ Tren de dependencias
var street = order.Customer.Address.Street.Name;
// order conoce Customer → Customer conoce Address → Address conoce Street → Street.Name

// ✅ Tell, Don't Ask
var street = order.GetDeliveryStreetName();

// En Order.cs:
public string GetDeliveryStreetName() => Customer.Address.Street.Name;
// La navegación queda encapsulada dentro de Order
```

### Fail Fast

```csharp
// ✅ Validar al inicio, no al final
public async Task ProcessOrderAsync(Order order, CancellationToken ct)
{
    ArgumentNullException.ThrowIfNull(order);
    if (order.Items.Count == 0)
        throw new ArgumentException("Order must have items", nameof(order));
    if (order.CustomerId == Guid.Empty)
        throw new ArgumentException("Order requires a customer", nameof(order));

    // Solo ahora, con estado válido, ejecutar lógica
    await _paymentService.ChargeAsync(order, ct);
}

// ❌ Validar tarde
public async Task ProcessOrderAsync(Order order, CancellationToken ct)
{
    await _paymentService.ChargeAsync(order, ct); // Cargo primero
    if (order.Items.Count == 0) // Valido después
        throw; // Ya cobré, ahora cómo revierto?
}
```

### Convention over Configuration

```csharp
// ✅ EF Core: convención de nombres evita configuración explícita
public class Order
{
    public int Id { get; set; }           // → PK por convención
    public int CustomerId { get; set; }   // → FK por convención
    public Customer Customer { get; set; } // → Navigation property
    public decimal Total { get; set; }    // → decimal(18,2) por convención
}

// No se necesita:
// modelBuilder.Entity<Order>().HasKey(o => o.Id);
// modelBuilder.Entity<Order>().Property(o => o.Total).HasColumnType("decimal(18,2)");
```

---

## Tabla de decisión rápida

| Principio | Aplicar cuando | Ignorar cuando |
|-----------|---------------|----------------|
| SRP | Clase > 200 líneas, métodos no usan mismos campos | DTO anémico, Minimal API endpoint file |
| OCP | Nuevas variantes cada sprint, plugin system | 2 opciones fijas, nunca cambiaron |
| LSP | Jerarquía con polimorfismo real | Herencia por reuso de código (usar composición) |
| ISP | Consumidores usan subconjuntos distintos de la interfaz | Consumidores usan todos los métodos |
| DIP | Capa de dominio/aplicación, integraciones externas | Clases internas de infraestructura |
| DRY | 3+ duplicaciones con misma razón de cambio | 2 coincidencias con distinta razón de cambio |
| KISS | Siempre por defecto | — |
| YAGNI | Feature especulativa, "por si acaso" | Requerimiento confirmado para próximo sprint |

---

## Violaciones frecuentes en código .NET real

### 1. Constructor con lógica pesada

```csharp
// ❌ Constructor llama a la BD
public class OrderService
{
    private readonly List<Product> _products;

    public OrderService(AppDbContext db)
    {
        _products = db.Products.ToList(); // ← WTF
    }
}

// ✅ Solo asignar dependencias
public class OrderService(IProductRepository products)
{
    // Ya está. products se usa en los métodos cuando se necesita.
}
```

### 2. Excepciones como flujo de control

```csharp
// ❌ Usar excepción para "no encontrado" esperado
try
{
    var user = await _userService.GetByIdAsync(id);
}
catch (NotFoundException)
{
    return NotFound();
}

// ✅ Result Pattern o null check
var result = await _userService.GetByIdAsync(id);
if (result is null)
    return NotFound();

// O con Result<T>
var result = await _userService.GetByIdAsync(id);
return result.Match(
    success: user => Ok(user),
    failure: _ => NotFound());
```

### 3. Mutar entidades desde fuera

```csharp
// ❌ Modificar estado de Order desde un servicio externo
order.Status = OrderStatus.Cancelled;
order.CancelledAt = DateTime.UtcNow;

// ✅ Método de dominio que encapsula la lógica
public class Order
{
    public void Cancel(string reason)
    {
        if (Status != OrderStatus.Pending && Status != OrderStatus.Confirmed)
            throw new DomainException($"Cannot cancel order in {Status} state");

        Status = OrderStatus.Cancelled;
        CancelledAt = DateTime.UtcNow;
        CancellationReason = reason;

        AddDomainEvent(new OrderCancelledEvent(Id, reason));
    }
}
```

### 4. `async void` fuera de event handlers

```csharp
// ❌ async void en método de servicio — las excepciones no se capturan
public async void ProcessOrderAsync(Order order)
{
    await _payment.ChargeAsync(order);
}

// ✅ async Task siempre
public async Task ProcessOrderAsync(Order order, CancellationToken ct)
{
    await _payment.ChargeAsync(order, ct);
}
```

### 5. Magic strings para identificadores de política/feature

```csharp
// ❌
pipelineProvider.GetPipeline("payment-pipeline"); // typo silencioso
_httpClient.GetAsync("https://api.stripe.com/v1/charges"); // URL hardcodeada

// ✅ Constantes tipadas
public static class ResiliencePipelines
{
    public const string Payment = "payment-pipeline";
    public const string Email = "email-pipeline";
}

pipelineProvider.GetPipeline(ResiliencePipelines.Payment);

// Para URLs: IOptions<T> con sección de configuración o constantes tipadas
public static class ExternalServices
{
    public const string StripeBaseUrl = "https://api.stripe.com/v1";
}
```

---

## Referencias

- `references/solid-detalle.md` — detalle de cada principio SOLID (SRP, OCP, LSP, ISP, DIP) con violación típica en .NET y corrección idiomática.
