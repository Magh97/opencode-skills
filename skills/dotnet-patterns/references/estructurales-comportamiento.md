# Patrones estructurales y de comportamiento

> Referencia de `dotnet-patterns`. Cárgala solo cuando necesites el detalle.

## Estructurales

### Decorator

**Problema**: Agregar comportamiento a un objeto sin modificar su clase ni usar herencia.

**En .NET**: middleware, `IServiceCollection.Decorate` (Scrutor), o implementación manual vía DI.

```csharp
// Interfaz base
public interface IOrderRepository
{
    Task<Order?> GetByIdAsync(Guid id, CancellationToken ct);
}

// Implementación real
public class EfOrderRepository(AppDbContext db) : IOrderRepository
{
    public async Task<Order?> GetByIdAsync(Guid id, CancellationToken ct)
        => await db.Orders.FindAsync([id], ct);
}

// Decorador de caché
public class CachedOrderRepository(
    IOrderRepository inner,
    IMemoryCache cache) : IOrderRepository
{
    public async Task<Order?> GetByIdAsync(Guid id, CancellationToken ct)
    {
        var key = $"order:{id}";
        return await cache.GetOrCreateAsync(key, async entry =>
        {
            entry.AbsoluteExpirationRelativeToNow = TimeSpan.FromMinutes(5);
            return await inner.GetByIdAsync(id, ct);
        });
    }
}

// Registro encadenado con Scrutor
services.AddScoped<IOrderRepository, EfOrderRepository>();
services.Decorate<IOrderRepository, CachedOrderRepository>();
// → CachedOrderRepository(EfOrderRepository) inyectado
```

**Cuándo sí**: logging, caching, retry, métricas, validación — comportamientos transversales.

**Cuándo no**: si el comportamiento es parte intrínseca de la clase.

---

### Adapter

**Problema**: Hacer que dos interfaces incompatibles trabajen juntas.

```csharp
// API externa (no controlamos)
public class SendGridClient
{
    public Task<SendGridResponse> SendEmailAsync(SendGridMessage msg);
}

// Nuestra abstracción
public interface IEmailSender
{
    Task SendAsync(Email email, CancellationToken ct = default);
}

// Adapter
public class SendGridEmailAdapter(SendGridClient client) : IEmailSender
{
    public async Task SendAsync(Email email, CancellationToken ct = default)
    {
        var msg = new SendGridMessage
        {
            From = new EmailAddress(email.From),
            Subject = email.Subject,
            PlainTextContent = email.Body
        };
        msg.AddTo(email.To);
        await client.SendEmailAsync(msg);
    }
}

// DI
services.AddSingleton(new SendGridClient(apiKey));
services.AddScoped<IEmailSender, SendGridEmailAdapter>();
```

**Cuándo sí**: integrar librerías externas, servicios legacy, APIs de terceros. **Siempre** poner el adapter detrás de tu propia interfaz.

---

### Facade

**Problema**: Proporcionar una interfaz simplificada a un subsistema complejo.

```csharp
// Subsistemas complejos
public class InventoryService { ... }
public class PaymentGateway { ... }
public class ShipmentProvider { ... }
public class NotificationService { ... }

// Facade que orquesta
public class OrderProcessor(
    InventoryService inventory,
    PaymentGateway payment,
    ShipmentProvider shipment,
    NotificationService notification)
{
    public async Task<OrderResult> ProcessOrderAsync(Order order, CancellationToken ct)
    {
        await inventory.ReserveAsync(order.Items, ct);
        await payment.ChargeAsync(order.Total, order.PaymentMethod, ct);
        var tracking = await shipment.CreateShipmentAsync(order, ct);
        await notification.SendConfirmationAsync(order.CustomerEmail, tracking, ct);

        return new OrderResult(order.Id, OrderStatus.Completed, tracking.Number);
    }
}
```

**Regla**: El facade _orquesta_, no contiene lógica de negocio. Si hay if/switch sobre estados de negocio, eso va en el Domain.

---

### Composite

**Problema**: Tratar un grupo de objetos como uno solo (árbol jerárquico).

```csharp
public abstract class FileSystemItem(string name)
{
    public string Name { get; } = name;
    public abstract long GetSize();
}

public class File(string name, long size) : FileSystemItem(name)
{
    public override long GetSize() => size;
}

public class Directory(string name, List<FileSystemItem> items) : FileSystemItem(name)
{
    public override long GetSize() => items.Sum(i => i.GetSize());
    public void Add(FileSystemItem item) => items.Add(item);
}
```

**Ejemplo real .NET**: reglas de validación compuestas con FluentValidation — una `AbstractValidator` puede contener otras.

---

### Proxy

**Problema**: Controlar acceso a otro objeto (remoto, virtual, protección).

```csharp
// Lazy proxy: cargar bajo demanda
public class LazyOrderRepository(
    IServiceProvider serviceProvider) : IOrderRepository
{
    private IOrderRepository? _real;

    public Task<Order?> GetByIdAsync(Guid id, CancellationToken ct)
    {
        _real ??= serviceProvider.GetRequiredService<IOrderRepository>();
        return _real.GetByIdAsync(id, ct);
    }
}
```

**Nota**: `Lazy<T>` ya existe en .NET. Solo implementar proxy manual si necesitas lógica específica.

---

### Bridge

**Problema**: Separar abstracción de implementación para que varíen independientemente.

```csharp
// Abstracción (no cambia)
public abstract class Report(IRenderer renderer)
{
    public abstract string Generate();
}

// Implementación concreta de abstracción
public class SalesReport(IRenderer renderer, List<Sale> sales)
    : Report(renderer)
{
    public override string Generate() => renderer.Render(sales);
}

// Implementación de renderer (varía)
public interface IRenderer
{
    string Render(List<Sale> sales);
}

public class HtmlRenderer : IRenderer { ... }
public class PdfRenderer : IRenderer { ... }
public class CsvRenderer : IRenderer { ... }
```

---


## Comportamiento

### Strategy

**Problema**: Intercambiar algoritmos en runtime.

```csharp
public interface ITaxCalculator
{
    decimal Calculate(Order order);
}

public class MexicoTaxCalculator : ITaxCalculator
{
    public decimal Calculate(Order order) => order.Subtotal * 0.16m;
}

public class UsTaxCalculator : ITaxCalculator
{
    public decimal Calculate(Order order) => order.Subtotal * order.StateRate;
}

// Consumo con Strategy Pattern
public class TaxService(IEnumerable<ITaxCalculator> calculators)
{
    private readonly Dictionary<string, ITaxCalculator> _map = calculators
        .ToDictionary(c => c.GetType().Name.Replace("TaxCalculator", "").ToLowerInvariant());

    public decimal CalculateTax(string countryCode, Order order)
        => _map.TryGetValue(countryCode, out var calc)
            ? calc.Calculate(order)
            : throw new NotSupportedException($"No tax calculator for {countryCode}");
}

// Registro con scan
services.Scan(scan => scan
    .FromAssemblyOf<ITaxCalculator>()
    .AddClasses(c => c.AssignableTo<ITaxCalculator>())
    .AsImplementedInterfaces()
    .WithScopedLifetime());
```

**Alternativa simple**: `switch` con Keyed DI cuando son < 5 estrategias y no cambian frecuentemente.

---

### Observer

**Problema**: Notificar a múltiples suscriptores cuando un objeto cambia.

**En .NET moderno**: eventos nativos, `IObservable<T>`/`IObserver<T>`, o `Channel<T>` para async.

```csharp
// ✅ Eventos de dominio (forma preferida en DDD)
public record OrderCreatedEvent(Guid OrderId, string CustomerId, decimal Total);

public class Order
{
    private readonly List<object> _domainEvents = [];

    public IReadOnlyCollection<object> DomainEvents => _domainEvents;

    public void MarkAsCreated()
    {
        _domainEvents.Add(new OrderCreatedEvent(Id, CustomerId, Total));
    }
}

// Dispatcher con MediatR o manual
public class DomainEventDispatcher(AppDbContext db, IPublisher publisher)
{
    public async Task DispatchAsync(CancellationToken ct)
    {
        var events = db.ChangeTracker
            .Entries<IAggregateRoot>()
            .SelectMany(e => e.Entity.DomainEvents)
            .ToList();

        foreach (var domainEvent in events)
            await publisher.Publish(domainEvent, ct);
    }
}

// ✅ IObservable<T> (sistema reactivo)
public class StockTicker : IObservable<StockPrice>
{
    private readonly List<IObserver<StockPrice>> _observers = [];

    public IDisposable Subscribe(IObserver<StockPrice> observer)
    {
        _observers.Add(observer);
        return new Unsubscriber(_observers, observer);
    }
    // OnNext, OnError, OnCompleted...
}

// ✅ Channel<T> para productor/consumidor async
public class OrderProcessor(Channel<Order> channel) : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken ct)
    {
        await foreach (var order in channel.Reader.ReadAllAsync(ct))
            await ProcessAsync(order, ct);
    }
}
```

---

### Template Method

**Problema**: Definir el esqueleto de un algoritmo dejando pasos para subclases.

```csharp
public abstract class DataImporter
{
    // Template method — no se sobreescribe
    public async Task ImportAsync(string filePath, CancellationToken ct)
    {
        var raw = await ReadFileAsync(filePath, ct);
        var parsed = Parse(raw);
        await ValidateAsync(parsed, ct);

        await SaveAsync(parsed, ct);
        await OnCompletedAsync(parsed, ct);
    }

    protected abstract List<Dictionary<string, string>> Parse(string raw);
    protected virtual Task ValidateAsync(List<Dictionary<string, string>> data, CancellationToken ct)
        => Task.CompletedTask;

    protected abstract Task SaveAsync(List<Dictionary<string, string>> data, CancellationToken ct);
    protected virtual Task OnCompletedAsync(List<Dictionary<string, string>> data, CancellationToken ct)
        => Task.CompletedTask;

    private static async Task<string> ReadFileAsync(string path, CancellationToken ct)
        => await File.ReadAllTextAsync(path, ct);
}

// Concreción
public class CsvOrderImporter : DataImporter
{
    protected override List<Dictionary<string, string>> Parse(string raw) { ... }
    protected override async Task SaveAsync(List<Dictionary<string, string>> data, CancellationToken ct) { ... }
}
```

**Alternativa moderna**: composición sobre herencia. Pasar `Func<>` o interfaces como dependencias en vez de forzar herencia. Pero Template Method sigue siendo válido cuando la secuencia es rígida y compartida.

---

### Command

**Problema**: Encapsular una petición como objeto, permitiendo parametrizar, encolar, loguear o deshacer operaciones.

**En .NET moderno**: Commands + Handlers (CQRS) o `IRequest<T>` de MediatR.

> Nota: desde MediatR v13 el uso comercial requiere licencia de pago; alternativas gratuitas: `Mediator` (martinothamar, source generators) o CQRS manual sin librería.

```csharp
// Command (inmutable)
public record CreateOrderCommand(
    string CustomerId,
    List<OrderItemDto> Items,
    string? CouponCode = null) : IRequest<OrderDto>;

// Handler
public class CreateOrderHandler(
    IOrderRepository orders,
    ICustomerRepository customers,
    IUnitOfWork uow) : IRequestHandler<CreateOrderCommand, OrderDto>
{
    public async Task<OrderDto> Handle(CreateOrderCommand cmd, CancellationToken ct)
    {
        var customer = await customers.GetByIdAsync(cmd.CustomerId, ct)
            ?? throw new NotFoundException(nameof(Customer), cmd.CustomerId);

        var order = Order.Create(customer, cmd.Items);
        if (cmd.CouponCode is not null)
            order.ApplyCoupon(cmd.CouponCode);

        orders.Add(order);
        await uow.SaveChangesAsync(ct);

        return OrderDto.From(order);
    }
}
```

---

### Mediator

**Problema**: Desacoplar emisores y receptores. Un objeto no llama a otro directamente, pasa por un mediador.

```csharp
// MediatR como implementación más común
public record OrderCompletedNotification(Guid OrderId) : INotification;

public class SendInvoiceHandler : INotificationHandler<OrderCompletedNotification>
{
    public Task Handle(OrderCompletedNotification notification, CancellationToken ct)
    {
        // Enviar factura
        return Task.CompletedTask;
    }
}

public class UpdateInventoryHandler : INotificationHandler<OrderCompletedNotification>
{
    public Task Handle(OrderCompletedNotification notification, CancellationToken ct)
    {
        // Actualizar inventario
        return Task.CompletedTask;
    }
}

// Uso (desde cualquier handler o endpoint)
await mediator.Publish(new OrderCompletedNotification(order.Id), ct);
```

**⚠️ Cuidado**: MediatR agrega indirección. Justificarlo solo si:
- Hay 3+ handlers para un mismo evento/mensaje
- Los handlers cambian frecuentemente en features distintas
- Se necesita pipeline behavior (logging, validación)

Para apps pequeñas/medianas: llamada directa entre servicios es más clara.

---

### Chain of Responsibility

**Problema**: Pasar una petición a través de una cadena de handlers hasta que uno la procese.

```csharp
public interface IExpenseApprover
{
    void SetNext(IExpenseApprover next);
    Task<ApprovalResult> ApproveAsync(Expense expense, CancellationToken ct);
}

public abstract class Approver(decimal limit) : IExpenseApprover
{
    private IExpenseApprover? _next;
    protected decimal Limit { get; } = limit;

    public void SetNext(IExpenseApprover next) => _next = next;

    public virtual async Task<ApprovalResult> ApproveAsync(Expense expense, CancellationToken ct)
    {
        if (expense.Amount <= Limit)
            return await ProcessApprovalAsync(expense, ct);

        return _next is not null
            ? await _next.ApproveAsync(expense, ct)
            : ApprovalResult.Escalated();
    }

    protected abstract Task<ApprovalResult> ProcessApprovalAsync(Expense expense, CancellationToken ct);
}

public class ManagerApprover : Approver
{
    public ManagerApprover() : base(1000) { }
    protected override Task<ApprovalResult> ProcessApprovalAsync(Expense e, CancellationToken ct)
        => Task.FromResult(ApprovalResult.Approved("Manager"));
}

public class DirectorApprover : Approver
{
    public DirectorApprover() : base(5000) { }
    protected override Task<ApprovalResult> ProcessApprovalAsync(Expense e, CancellationToken ct)
        => Task.FromResult(ApprovalResult.Approved("Director"));
}

// Pipelines de ASP.NET Core son Chain of Responsibility nativamente
app.UseExceptionHandler()
   .UseAuthentication()
   .UseAuthorization()
   .UseEndpoints(…);
```

---

### State

**Problema**: Un objeto cambia su comportamiento cuando su estado interno cambia.

```csharp
// Enfoque funcional con switch expression (más simple para estados finitos)
public record Order
{
    public OrderStatus Status { get; private set; }

    public Result<Order> Submit()
    {
        return Status switch
        {
            OrderStatus.Draft => Mutate(s => s.Status = OrderStatus.PendingReview),
            OrderStatus.PendingReview => Result<Order>.Failure("Already submitted"),
            _ => Result<Order>.Failure($"Cannot submit from {Status}")
        };
    }

    public Result<Order> Approve()
    {
        return Status switch
        {
            OrderStatus.PendingReview => Mutate(s => s.Status = OrderStatus.Approved),
            _ => Result<Order>.Failure($"Cannot approve from {Status}")
        };
    }
}

// Enfoque con clases (estados complejos con lógica propia)
public interface IOrderState
{
    IOrderState Submit();
    IOrderState Approve();
    IOrderState Cancel();
}

public class DraftState : IOrderState
{
    public IOrderState Submit() => new PendingReviewState();
    public IOrderState Approve() => throw new InvalidOperationException("Cannot approve draft");
    public IOrderState Cancel() => new CancelledState();
}
```

**Regla**: Si los estados tienen > 2 transiciones con lógica distinta → State clásico. Si es CRUD de estados simples → `switch` expression.

---

### Visitor

**Problema**: Agregar operaciones a una jerarquía de clases sin modificarlas.

```csharp
// Jerarquía fija (pocos cambios)
public interface IExportable
{
    void Accept(IExportVisitor visitor);
}

public class Invoice : IExportable
{
    public string Number { get; set; }
    public decimal Total { get; set; }
    public void Accept(IExportVisitor visitor) => visitor.Visit(this);
}

public class CreditNote : IExportable
{
    public string Reference { get; set; }
    public decimal Amount { get; set; }
    public void Accept(IExportVisitor visitor) => visitor.Visit(this);
}

// Visitante
public interface IExportVisitor
{
    void Visit(Invoice invoice);
    void Visit(CreditNote creditNote);
}

public class PdfExportVisitor : IExportVisitor { ... }
public class XmlExportVisitor : IExportVisitor { ... }
```

**⚠️ Rara vez necesario en .NET moderno**. Pattern matching (`switch` expression sobre tipos) cubre el 90% de los casos de Visitor con menos código.

```csharp
string Export(IExportable doc) => doc switch
{
    Invoice i => $"INV-{i.Number}: {i.Total:C}",
    CreditNote cn => $"CN-{cn.Reference}: {cn.Amount:C}",
    _ => throw new NotSupportedException()
};
```

---
