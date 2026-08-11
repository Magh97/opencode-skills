---
name: dotnet-patterns
description: Patrones de diseño aplicados a .NET y C#. Cubre patrones creacionales, estructurales y de comportamiento con ejemplos prácticos en .NET 9/10. Incluye patrones nativos del ecosistema (Options, Pipeline, Retry, Circuit Breaker, Repository, Specification, Unit of Work) y antipatrones comunes. Actívala al diseñar o refactorizar componentes, implementar factories, strategies, decorators, o al evaluar arquitectura de servicios.
disable-model-invocation: true
---

# Patrones de Diseño en .NET

Guía práctica de patrones GoF y patrones específicos del ecosistema .NET. Cada patrón responde **qué problema resuelve**, **cuándo usarlo**, **cuándo NO usarlo**, y muestra implementación idiomática en C#.

## Índice

- [Creacionales](#creacionales)
  - [Factory Method](#factory-method)
  - [Abstract Factory](#abstract-factory)
  - [Builder](#builder)
  - [Singleton (en era DI)](#singleton-en-era-di)
  - [Prototype](#prototype)
- [Estructurales](#estructurales)
  - [Decorator](#decorator)
  - [Adapter](#adapter)
  - [Facade](#facade)
  - [Composite](#composite)
  - [Proxy](#proxy)
  - [Bridge](#bridge)
- [Comportamiento](#comportamiento)
  - [Strategy](#strategy)
  - [Observer](#observer)
  - [Template Method](#template-method)
  - [Command](#command)
  - [Mediator](#mediator)
  - [Chain of Responsibility](#chain-of-responsibility)
  - [State](#state)
  - [Visitor](#visitor)
- [Patrones del ecosistema .NET](#patrones-del-ecosistema-net)
  - [Options Pattern](#options-pattern)
  - [Pipeline / Middleware](#pipeline--middleware)
  - [Retry + Circuit Breaker](#retry--circuit-breaker)
  - [Repository](#repository)
  - [Unit of Work](#unit-of-work)
  - [Specification](#specification)
  - [Result Pattern](#result-pattern)
- [Anti-patrones y sobre-ingeniería](#anti-patrones-y-sobre-ingeniería)

---

## Creacionales

### Factory Method

**Problema**: Crear objetos cuya dependencia concreta no se conoce hasta runtime.

**En .NET moderno** dos enfoques principales:

#### 1. Factory vía DI — `Func<T>` inyectado

```csharp
// Registro
services.AddTransient<StripePaymentService>();
services.AddTransient<PayPalPaymentService>();

// Factoría resuelta por DI
services.AddTransient<Func<string, IPaymentService>>(sp => key => key switch
{
    "stripe" => sp.GetRequiredService<StripePaymentService>(),
    "paypal" => sp.GetRequiredService<PayPalPaymentService>(),
    _ => throw new ArgumentException($"Unknown provider: {key}")
});
```

#### 2. Factory con Keyed DI (.NET 8+) — preferido

```csharp
// Registro con clave
services.AddKeyedScoped<IPaymentService, StripePaymentService>("stripe");
services.AddKeyedScoped<IPaymentService, PayPalPaymentService>("paypal");

// Consumo
public class CheckoutService(
    [FromKeyedServices("stripe")] IPaymentService paymentService)
{
}
```

**Cuándo no**: si la creación es trivial (`new Order()`) o si Keyed DI cubre el caso.

---

### Abstract Factory

**Problema**: Familia de objetos relacionados que deben crearse juntos (ej. UI para Windows vs macOS).

```csharp
// Familia de productos
public interface IButton { void Render(); }
public interface ITextBox { void Render(); }

// Fábrica abstracta
public interface IUiFactory
{
    IButton CreateButton();
    ITextBox CreateTextBox();
}

// Fábricas concretas
public class WindowsUiFactory : IUiFactory
{
    public IButton CreateButton() => new WindowsButton();
    public ITextBox CreateTextBox() => new WindowsTextBox();
}

// Consumo vía DI según entorno
services.AddScoped<IUiFactory>(sp =>
    RuntimeInformation.IsOSPlatform(OSPlatform.Windows)
        ? new WindowsUiFactory()
        : new MacUiFactory());
```

**Cuándo sí**: sistema multi-plataforma real, multi-tenant, multi-proveedor.

**Cuándo no**: "por si acaso" — YAGNI.

---

### Builder

**Problema**: Construcción paso a paso de objetos complejos con muchas configuraciones opcionales.

#### Builder fluido tradicional

```csharp
public class EmailMessageBuilder
{
    private readonly EmailMessage _message = new();

    public EmailMessageBuilder To(string address)
    {
        _message.To.Add(address);
        return this;
    }

    public EmailMessageBuilder WithSubject(string subject)
    {
        _message.Subject = subject;
        return this;
    }

    public EmailMessageBuilder WithAttachment(string path, byte[] content)
    {
        _message.Attachments.Add(new Attachment(path, content));
        return this;
    }

    public EmailMessage Build() => _message;
}

// Uso
var email = new EmailMessageBuilder()
    .To("user@example.com")
    .WithSubject("Welcome!")
    .WithAttachment("invoice.pdf", pdfBytes)
    .Build();
```

#### Builder con `required` + `init` (.NET 6+) — para objetos planos

```csharp
public class EmailMessage
{
    public required List<string> To { get; init; }
    public string Subject { get; init; } = string.Empty;
    public List<Attachment> Attachments { get; init; } = new();
}

// Uso con object initializer — no necesita builder
var email = new EmailMessage
{
    To = ["user@example.com"],
    Subject = "Welcome!",
    Attachments = { new("invoice.pdf", pdfBytes) }
};
```

**Regla**: Builder solo si hay +5 propiedades opcionales con lógica de construcción _durante_ el build. Menos que eso → `required` + `init`.

---

### Singleton (en era DI)

**Problema**: Una única instancia compartida en toda la aplicación.

**En .NET**: el contenedor DI ya maneja el ciclo de vida. No implementar singleton manual.

```csharp
// ✅ Singleton vía DI
services.AddSingleton<IEmailTemplateCache, EmailTemplateCache>();

// ⬜ Singleton manual (solo legacy o sin DI)
public sealed class ConfigLoader
{
    private static readonly Lazy<ConfigLoader> _instance = new(() => new ConfigLoader());
    public static ConfigLoader Instance => _instance.Value;
    private ConfigLoader() { }
}
```

**⚠️ Peligro**: Singletons que dependen de servicios Scoped → error en runtime. El DI lanza `InvalidOperationException` en .NET 9+ con mensaje claro.

**Alternativa**: `AddSingleton` para cache en memoria, `IDistributedCache` para cache distribuida, `HybridCache` para dos niveles.

---

### Prototype

**Problema**: Crear objetos clonando una instancia existente en vez de construir desde cero.

```csharp
// ✅ ICloneable moderno con record
public record OrderTemplate(string CustomerTier, decimal DefaultDiscount, List<string> Tags);

var template = new OrderTemplate("Gold", 0.15m, ["priority", "vip"]);
var order1 = template with { };  // clone exacto
var order2 = template with { Tags = ["standard"] }; // clone con override

// ✅ Deep clone con JSON (simple, lento pero funciona)
var cloned = JsonSerializer.Deserialize<OrderTemplate>(
    JsonSerializer.Serialize(original));
```

---

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

## Patrones del ecosistema .NET

### Options Pattern

```csharp
public class SmtpOptions
{
    public const string SectionName = "Smtp";

    [Required, Host]
    public string Host { get; init; } = string.Empty;

    [Range(1, 65535)]
    public int Port { get; init; } = 587;

    [Required, EmailAddress]
    public string Username { get; init; } = string.Empty;

    [Required]
    public string Password { get; init; } = string.Empty;
}

// Registro con validación
services.AddOptions<SmtpOptions>()
    .Bind(configuration.GetSection(SmtpOptions.SectionName))
    .ValidateDataAnnotations()
    .ValidateOnStart();

// Consumo
public class EmailService(IOptionsSnapshot<SmtpOptions> options) { ... }
```

`IOptions<T>` → singleton (valores de startup).
`IOptionsSnapshot<T>` → scoped (recarga por request, útil para hot-reload).
`IOptionsMonitor<T>` → notifica cambios.

---

### Pipeline / Middleware

Pipeline behaviors con MediatR o middleware de ASP.NET Core:

```csharp
// Behavior de validación (MediatR)
public class ValidationBehavior<TRequest, TResponse>(
    IEnumerable<IValidator<TRequest>> validators)
    : IPipelineBehavior<TRequest, TResponse>
    where TRequest : IRequest<TResponse>
{
    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,
        CancellationToken ct)
    {
        var context = new ValidationContext<TRequest>(request);
        var failures = validators
            .Select(v => v.Validate(context))
            .SelectMany(r => r.Errors)
            .Where(f => f is not null)
            .ToList();

        if (failures.Count > 0)
            throw new ValidationException(failures);

        return await next();
    }
}

// Registro del behavior
services.AddTransient(typeof(IPipelineBehavior<,>), typeof(ValidationBehavior<,>));
```

---

### Retry + Circuit Breaker

Usar `Microsoft.Extensions.Resilience` (.NET 9+):

```csharp
// Retry simple + Circuit Breaker
services.AddResiliencePipeline("payment-pipeline", (builder, context) =>
{
    builder
        .AddRetry(new RetryStrategyOptions
        {
            MaxRetryAttempts = 3,
            BackoffType = DelayBackoffType.Exponential,
            Delay = TimeSpan.FromMilliseconds(200),
            UseJitter = true,
            OnRetry = args =>
            {
                context.ServiceProvider
                    .GetRequiredService<ILogger<Program>>()
                    .LogWarning("Retry {Attempt} for payment", args.AttemptNumber);
                return ValueTask.CompletedTask;
            }
        })
        .AddCircuitBreaker(new CircuitBreakerStrategyOptions
        {
            FailureRatio = 0.5,
            MinimumThroughput = 10,
            BreakDuration = TimeSpan.FromSeconds(30),
            SamplingDuration = TimeSpan.FromSeconds(60)
        })
        .AddTimeout(TimeSpan.FromSeconds(10));
});

// Uso
public class PaymentService(
    ResiliencePipelineProvider<string> pipelineProvider)
{
    public async Task<PaymentResult> ChargeAsync(decimal amount, CancellationToken ct)
    {
        var pipeline = pipelineProvider.GetPipeline("payment-pipeline");
        return await pipeline.ExecuteAsync(
            async token => await _gateway.ChargeAsync(amount, token), ct);
    }
}
```

---

### Repository

**Problema**: Abstraer acceso a datos. **¿Es necesario con EF Core?**

**Postura**: EF Core _es_ el repository (DbContext = Unit of Work, DbSet = Repository). Solo crear repos custom si:

```csharp
public interface IOrderRepository
{
    Task<Order?> GetByIdAsync(Guid id, CancellationToken ct);
    Task<List<Order>> GetPendingOrdersAsync(CancellationToken ct);
    void Add(Order order);
}

public class OrderRepository(AppDbContext db) : IOrderRepository
{
    public async Task<Order?> GetByIdAsync(Guid id, CancellationToken ct)
        => await db.Orders
            .Include(o => o.Items)
            .FirstOrDefaultAsync(o => o.Id == id, ct);

    public Task<List<Order>> GetPendingOrdersAsync(CancellationToken ct)
        => db.Orders
            .Where(o => o.Status == OrderStatus.Pending)
            .AsNoTracking()
            .ToListAsync(ct);

    public void Add(Order order) => db.Orders.Add(order);
}
```

**⚠️ No hacer**: Repository genérico `IRepository<T>` con 20 métodos que solo delegan a DbSet. Eso no agrega valor, solo indirección.

---

### Unit of Work

**EF Core DbContext = Unit of Work**. `SaveChangesAsync` es el commit.

```csharp
public interface IUnitOfWork
{
    Task<int> SaveChangesAsync(CancellationToken ct = default);
}

// DbContext ya implementa el patrón
public class AppDbContext(DbContextOptions<AppDbContext> options) : DbContext(options)
{
    // SaveChangesAsync es el commit transaccional
}
```

Solo abstraer con `IUnitOfWork` si necesitas testing sin EF Core o soporte multi-ORM.

---

### Specification

```csharp
public interface ISpecification<T>
{
    Expression<Func<T, bool>> Criteria { get; }
    List<Expression<Func<T, object>>> Includes { get; }
    Expression<Func<T, object>>? OrderBy { get; }
}

public class PendingOrdersSpec : ISpecification<Order>
{
    public Expression<Func<Order, bool>> Criteria => o => o.Status == OrderStatus.Pending;
    public List<Expression<Func<Order, object>>> Includes => [o => o.Items];
    public Expression<Func<Order, object>>? OrderBy => o => o.CreatedAt;
}

// Evaluador
public static class SpecificationEvaluator
{
    public static IQueryable<T> ApplySpecification<T>(
        this IQueryable<T> query, ISpecification<T> spec) where T : class
    {
        query = query.Where(spec.Criteria);
        query = spec.Includes.Aggregate(query, (current, include) => current.Include(include));
        if (spec.OrderBy is not null)
            query = query.OrderBy(spec.OrderBy);
        return query;
    }
}

// Uso
var pendingOrders = await db.Orders
    .ApplySpecification(new PendingOrdersSpec())
    .ToListAsync(ct);
```

**Alternativa más simple**: métodos de extensión con nombre en `IQueryable<T>`.

```csharp
public static IQueryable<Order> Pending(this IQueryable<Order> orders)
    => orders.Where(o => o.Status == OrderStatus.Pending);

// Uso
var pending = await db.Orders.Pending().ToListAsync(ct);
```

---

### Result Pattern

Alternativa a excepciones para errores esperados (validación, no encontrado, conflicto):

```csharp
public class Result<T>
{
    public bool IsSuccess { get; }
    public T? Value { get; }
    public string? Error { get; }

    private Result(bool isSuccess, T? value, string? error)
    {
        IsSuccess = isSuccess;
        Value = value;
        Error = error;
    }

    public static Result<T> Success(T value) => new(true, value, null);
    public static Result<T> Failure(string error) => new(false, default, error);

    public TResult Match<TResult>(Func<T, TResult> success, Func<string, TResult> failure)
        => IsSuccess ? success(Value!) : failure(Error!);
}

// Uso en Minimal API
app.MapGet("/api/orders/{id}", async (Guid id, OrderService svc, CancellationToken ct) =>
{
    var result = await svc.GetOrderAsync(id, ct);
    return result.Match(
        success: order => Results.Ok(order),
        failure: error => Results.NotFound(new { error }));
});
```

**Regla**: Result pattern para errores de dominio esperados. Excepciones para fallos inesperados (DB caída, bug, red).

---

## Anti-patrones y sobre-ingeniería

| Anti-patrón | Problema | Solución |
|-------------|----------|----------|
| `IRepository<T>` genérico | No agrega valor sobre `DbSet<T>` | Métodos de extensión o repos específicos con queries nombradas |
| Factory para 1 sola implementación | Indirección innecesaria | `new()` o DI directo |
| `IValidator` custom sin FluentValidation | Reinventar la rueda | FluentValidation + DataAnnotations |
| Strategy con 2 opciones que nunca cambiaron | Complejidad sin beneficio | `switch` o `Dictionary<string, Func<>>` |
| MediatR en CRUD sin eventos | Indirección pura | Llamar al handler/service directamente |
| Builder para objetos con 3 propiedades | Over-engineering | `required` + `init` o constructor |
| Interface con 1 sola implementación | "Por si acaso" | Borrar la interfaz. Crearla cuando surja la segunda implementación. |
| Singleton manual con `Lazy<T>` | DI lo maneja | `AddSingleton<T>()` |

---

## Checklist de decisión

Antes de implementar un patrón, responder:

1. ¿El patrón **resuelve un problema real** en este código o es "por si acaso"? → Si es especulativo, no.
2. ¿Hay una **forma más simple** de resolverlo sin el patrón? → Si sí, usar la simple.
3. ¿.NET ya lo ofrece nativamente? (DI, middleware, `IObservable`, `Channel`, Resilience) → Si sí, usar lo nativo.
4. ¿El equipo conoce el patrón? → Si no, pesa más la mantenibilidad que la elegancia.
