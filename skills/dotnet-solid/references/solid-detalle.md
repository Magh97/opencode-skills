# SOLID en detalle

> Referencia de `dotnet-solid`. Cárgala solo cuando necesites el detalle.

## SOLID

### S — Single Responsibility Principle (SRP)

> Una clase debe tener una sola razón para cambiar.

#### Violación

```csharp
// ❌ Esta clase cambia si cambia: lógica de negocio, formato de reporte, o envío de email
public class OrderProcessor
{
    public async Task ProcessAsync(Order order)
    {
        // Lógica de negocio
        if (order.Items.Count == 0)
            throw new InvalidOperationException("Empty order");
        order.Total = order.Items.Sum(i => i.Price * i.Quantity);

        // Reporte
        var html = $"<h1>Order {order.Id}</h1><p>Total: {order.Total:C}</p>";
        await File.WriteAllTextAsync($"report_{order.Id}.html", html);

        // Notificación
        await SendEmailAsync(order.CustomerEmail, "Order processed", html);
    }
}
```

#### Corrección

```csharp
// ✅ Una razón para cambiar cada una
public class OrderCalculator
{
    public Money CalculateTotal(Order order) =>
        order.Items.Aggregate(Money.Zero, (sum, item) => sum + item.LineTotal);
}

public class OrderHtmlReportGenerator
{
    public string Generate(Order order) => $"""
        <h1>Order {order.Id}</h1>
        <p>Total: {order.Total}</p>
        <p>Items: {order.Items.Count}</p>
        """;
}

public class OrderProcessor(
    OrderCalculator calculator,
    OrderHtmlReportGenerator reportGenerator,
    IEmailSender emailSender)
{
    public async Task ProcessAsync(Order order, CancellationToken ct)
    {
        order.Total = calculator.CalculateTotal(order);
        var report = reportGenerator.Generate(order);
        await emailSender.SendAsync(order.CustomerEmail, "Order processed", report, ct);
    }
}
```

#### Señales de violación

- La clase tiene más de ~200 líneas
- El nombre contiene "And" u "Or" (`OrderProcessorAndNotifier`)
- Los métodos no usen los mismos campos
- Tests de la clase mockean cosas no relacionadas

#### Cuándo ignorar SRP

- **Endpoints Minimal API**: un archivo que agrupa handler + request + response + ruta es aceptable. La "responsabilidad" es el endpoint completo.
- **DTOs anémicos**: no hay lógica que separar.
- **Configuración**: `appsettings.json` agrupa settings por sección, no es SRP pero es práctica estándar.

---

### O — Open/Closed Principle (OCP)

> Abierto a extensión, cerrado a modificación.

#### Estrategias .NET para OCP

**1. Strategy Pattern + DI**

```csharp
// Cerrado a modificación — no tocas esta interfaz
public interface IDiscountStrategy
{
    bool AppliesTo(Order order);
    Money Apply(Order order);
}

// Extensiones como nuevas clases
public class PercentageDiscount(decimal percentage) : IDiscountStrategy
{
    public bool AppliesTo(Order order) => order.Total > 100;
    public Money Apply(Order order) => order.Total * (1 - percentage);
}

public class FixedDiscount(decimal amount) : IDiscountStrategy
{
    public bool AppliesTo(Order order) => order.CustomerTier == Tier.Vip;
    public Money Apply(Order order) => order.Total - amount;
}

// El discountService no cambia al agregar nuevas estrategias
public class DiscountService(IEnumerable<IDiscountStrategy> strategies)
{
    public Money ApplyBestDiscount(Order order) =>
        strategies
            .Where(s => s.AppliesTo(order))
            .Select(s => s.Apply(order))
            .DefaultIfEmpty(order.Total)
            .Min()!;
}

// DI auto-descubre nuevas implementaciones
services.Scan(s => s
    .FromAssemblyOf<IDiscountStrategy>()
    .AddClasses(c => c.AssignableTo<IDiscountStrategy>())
    .AsImplementedInterfaces()
    .WithScopedLifetime());
```

**2. Middleware pipeline (ASP.NET Core)**

```csharp
// Cada middleware extiende el pipeline sin modificar los demás
app.UseExceptionHandler();
app.UseAuthentication();    // ← agregar autenticación no modifica nada existente
app.UseAuthorization();
app.UseRequestLogging();    // ← nuevo middleware, sin tocar los anteriores
```

**3. Extension methods**

```csharp
// Extiendes string sin modificar System.String
public static class StringExtensions
{
    public static string Truncate(this string value, int maxLength) =>
        value.Length <= maxLength ? value : value[..maxLength] + "...";

    public static bool IsValidEmail(this string value) =>
        Regex.IsMatch(value, @"^[^@\s]+@[^@\s]+\.[^@\s]+$");
}
```

#### Cuándo NO aplicar OCP

No envolver en abstracción si:
- El comportamiento es parte del core y **no cambia** (ej. `CalculateTotal` en un carrito)
- Hay solo 2 variantes conocidas y no se prevén más
- La abstracción duplica el código sin beneficio claro

```csharp
// ❌ Sobre-ingeniería OCP: interfaz para algo que nunca variará
public interface IMathAdd { int Add(int a, int b); }
public class MathAdd : IMathAdd { public int Add(int a, int b) => a + b; }
```

---

### L — Liskov Substitution Principle (LSP)

> Las subclases deben ser sustituibles por sus clases base sin romper el sistema.

#### Violación clásica: Rectángulo y Cuadrado

```csharp
// ❌ Cuadrado rompe el contrato de Rectángulo
public class Rectangle
{
    public virtual int Width { get; set; }
    public virtual int Height { get; set; }
    public int Area() => Width * Height;
}

public class Square : Rectangle
{
    public override int Width  { set { base.Width = value; base.Height = value; } }
    public override int Height { set { base.Width = value; base.Height = value; } }
}

// Test que falla con Square
void TestArea(Rectangle rect)
{
    rect.Width = 5;
    rect.Height = 10;
    Assert.Equal(50, rect.Area()); // ❌ Square devuelve 100
}
```

#### Corrección: Preferir composición

```csharp
// ✅ No heredar. Usar una abstracción común inmutable
public interface IShape
{
    int Area();
}

public record Rectangle(int Width, int Height) : IShape
{
    public int Area() => Width * Height;
}

public record Square(int Side) : IShape
{
    public int Area() => Side * Side;
}
```

#### Violaciones comunes en .NET

```csharp
// ❌ Lanzar NotImplementedException en métodos heredados
public class ReadOnlyOrderRepository : IOrderRepository
{
    public Task SaveAsync(Order order, CancellationToken ct)
        => throw new NotImplementedException(); // Rompe LSP

    public Task<Order?> GetByIdAsync(Guid id, CancellationToken ct) { ... }
}

// ✅ Solución: dos interfaces segregadas
public interface IOrderReader { Task<Order?> GetByIdAsync(Guid id, CancellationToken ct); }
public interface IOrderWriter { Task SaveAsync(Order order, CancellationToken ct); }

public class ReadOnlyOrderRepository : IOrderReader { ... }
public class EfOrderRepository : IOrderReader, IOrderWriter { ... }
```

#### LSP Checklist

| Señal de violación | Acción |
|-------------------|--------|
| `NotImplementedException` en override | Separar interfaz (ISP) |
| `if (obj is DerivedType)` en código cliente | La abstracción no es suficiente |
| Subclase lanza excepciones que la base no declara | Repensar jerarquía |
| Subclase ignora parámetros o retorna `null` donde la base no | Contrato roto |

---

### I — Interface Segregation Principle (ISP)

> Una clase no debe depender de métodos que no usa.

#### Violación

```csharp
// ❌ Interfaz gorda: obliga a implementar métodos innecesarios
public interface IOrderRepository
{
    Task<Order?> GetByIdAsync(Guid id, CancellationToken ct);
    Task<List<Order>> GetAllAsync(CancellationToken ct);
    Task SaveAsync(Order order, CancellationToken ct);
    Task DeleteAsync(Guid id, CancellationToken ct);
    Task<List<Order>> SearchAsync(OrderSearchCriteria criteria, CancellationToken ct);
    Task<OrderStats> GetStatsAsync(CancellationToken ct);
}
```

La vista de reportes usa solo `GetStatsAsync` y `GetAllAsync`. El endpoint de búsqueda solo usa `SearchAsync`. Todos implementan todo.

#### Corrección

```csharp
// ✅ Interfaces segregadas por consumidor (Role Interfaces)
public interface IOrderReader
{
    Task<Order?> GetByIdAsync(Guid id, CancellationToken ct);
}

public interface IOrderLister
{
    Task<List<Order>> GetAllAsync(CancellationToken ct);
}

public interface IOrderWriter
{
    Task SaveAsync(Order order, CancellationToken ct);
    Task DeleteAsync(Guid id, CancellationToken ct);
}

public interface IOrderSearcher
{
    Task<List<Order>> SearchAsync(OrderSearchCriteria criteria, CancellationToken ct);
}

public interface IOrderStatsProvider
{
    Task<OrderStats> GetStatsAsync(CancellationToken ct);
}

// Cada consumidor inyecta solo lo que necesita
public class OrderReportService(IOrderLister lister, IOrderStatsProvider stats) { ... }
public class OrderSearchEndpoint(IOrderSearcher searcher) { ... }
```

#### ISP aplicado a CQRS

Commands y queries ya segregan naturalmente:

```csharp
// ✅ CQRS como ISP natural: un handler por operación
public record GetOrderQuery(Guid Id) : IRequest<OrderDto>;

public class GetOrderHandler(IOrderReader reader)
    : IRequestHandler<GetOrderQuery, OrderDto> { ... }

public record CreateOrderCommand(...) : IRequest<Order>;

public class CreateOrderHandler(IOrderWriter writer)
    : IRequestHandler<CreateOrderCommand, Order> { ... }
```

Cada handler solo depende de lo que necesita.

---

### D — Dependency Inversion Principle (DIP)

> Depender de abstracciones, no de implementaciones concretas.

#### Los dos enunciados

1. Módulos de alto nivel no dependen de módulos de bajo nivel. Ambos dependen de abstracciones.
2. Abstracciones no dependen de detalles. Los detalles dependen de abstracciones.

#### Violación

```csharp
// ❌ OrderService (alto nivel) depende de SqlOrderRepository (bajo nivel)
public class OrderService
{
    private readonly SqlOrderRepository _repository = new("conn-string");

    public async Task<Order?> GetAsync(Guid id)
        => await _repository.FindByIdAsync(id);
}
```

#### Corrección vía DI

```csharp
// ✅ OrderService depende de IOrderRepository (abstracción)
// ✅ SqlOrderRepository depende de IOrderRepository (abstracción)
public interface IOrderRepository
{
    Task<Order?> GetByIdAsync(Guid id, CancellationToken ct);
}

public class OrderService(IOrderRepository repository)
{
    public async Task<Order?> GetAsync(Guid id, CancellationToken ct)
        => await repository.GetByIdAsync(id, ct);
}

public class SqlOrderRepository(AppDbContext db) : IOrderRepository
{
    public async Task<Order?> GetByIdAsync(Guid id, CancellationToken ct)
        => await db.Orders.FindAsync([id], ct);
}
```

#### DIP en la práctica .NET

```csharp
// ✅ Clean Architecture: Domain no depende de Infrastructure
// Domain/Orders/IOrderRepository.cs  ← abstracción en capa de dominio
// Infrastructure/Data/SqlOrderRepository.cs ← implementación en infraestructura

// ✅ Aplicación depende de abstracciones de dominio
public class CancelOrderHandler(
    IOrderRepository orders,     // ← abstracción
    IUnitOfWork unitOfWork,      // ← abstracción
    ILogger<CancelOrderHandler> logger) // ← abstracción de Microsoft
{
    public async Task Handle(CancelOrderCommand cmd, CancellationToken ct)
    {
        var order = await orders.GetByIdAsync(cmd.OrderId, ct)
            ?? throw new NotFoundException(nameof(Order), cmd.OrderId);

        order.Cancel();
        await unitOfWork.SaveChangesAsync(ct);
    }
}
```

#### La regla de la interfaz

> La interfaz la define el **consumidor**, no el implementador.

```csharp
// ✅ La interfaz vive en el proyecto del consumidor (Application/Domain)
// ❌ NO en el proyecto de infraestructura
// Correcto:
//   MiApp.Application/IOrderRepository.cs       ← definida por quien la usa
//   MiApp.Infrastructure/SqlOrderRepository.cs   ← implementa la abstracción
```

---
