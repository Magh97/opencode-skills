# Patrones del ecosistema .NET

> Referencia de `dotnet-patterns`. Cárgala solo cuando necesites el detalle.

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
