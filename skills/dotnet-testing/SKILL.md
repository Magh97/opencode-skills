---
name: dotnet-testing
description: Testing en .NET con xUnit, NSubstitute, FluentAssertions. Cubre unit tests, integration tests, TDD, fixtures, mocking, test containers, snapshot testing, y estrategias de cobertura. Incluye patrones de test (AAA, Given-When-Then), anti-patrones, y testing de EF Core, APIs y background services. Actívala al escribir tests, configurar CI/CD, o definir estrategia de testing.
disable-model-invocation: true
---

# Testing en .NET

Guía completa de testing moderno en .NET 9/10. Stack por defecto: **xUnit + NSubstitute + FluentAssertions + Testcontainers**.

---

## Stack y setup

```xml
<!-- Paquetes de test -->
<PackageReference Include="xunit" Version="*" />
<PackageReference Include="Microsoft.NET.Test.Sdk" Version="*" />
<PackageReference Include="xunit.runner.visualstudio" Version="*">
  <IncludeAssets>runtime; build; native; contentfiles; analyzers</IncludeAssets>
  <PrivateAssets>all</PrivateAssets>
</PackageReference>
<PackageReference Include="NSubstitute" Version="*" />
<PackageReference Include="FluentAssertions" Version="*" />
<PackageReference Include="coverlet.collector" Version="*">
  <IncludeAssets>runtime; build; native; contentfiles; analyzers</IncludeAssets>
  <PrivateAssets>all</PrivateAssets>
</PackageReference>

<!-- Integration tests -->
<PackageReference Include="Microsoft.AspNetCore.Mvc.Testing" Version="*" />
<PackageReference Include="Testcontainers.MsSql" Version="*" />
<PackageReference Include="Testcontainers.Redis" Version="*" />
```

---

## Unit Tests

### Estructura AAA (Arrange, Act, Assert)

```csharp
public class CancelOrderHandlerTests
{
    private readonly IOrderRepository _orderRepo = Substitute.For<IOrderRepository>();
    private readonly IUnitOfWork _unitOfWork = Substitute.For<IUnitOfWork>();
    private readonly CancelOrderHandler _sut; // System Under Test

    public CancelOrderHandlerTests()
    {
        _sut = new CancelOrderHandler(_orderRepo, _unitOfWork);
    }

    [Fact]
    public async Task Handle_WhenOrderExists_CancelsOrderSuccessfully()
    {
        // Arrange
        var order = OrderTestData.PendingOrder();
        var command = new CancelOrderCommand(order.Id, "Customer request");
        _orderRepo.GetByIdAsync(order.Id, Arg.Any<CancellationToken>()).Returns(order);

        // Act
        await _sut.Handle(command, CancellationToken.None);

        // Assert
        order.Status.Should().Be(OrderStatus.Cancelled);
        order.CancellationReason.Should().Be("Customer request");
        await _unitOfWork.Received(1).SaveChangesAsync(Arg.Any<CancellationToken>());
    }

    [Fact]
    public async Task Handle_WhenOrderNotFound_ThrowsNotFoundException()
    {
        // Arrange
        var command = new CancelOrderCommand(Guid.NewGuid(), "reason");
        _orderRepo.GetByIdAsync(Arg.Any<Guid>(), Arg.Any<CancellationToken>()).Returns((Order?)null);

        // Act
        var act = () => _sut.Handle(command, CancellationToken.None);

        // Assert
        await act.Should().ThrowAsync<NotFoundException>()
            .WithMessage($"*{command.OrderId}*");
    }
}
```

### Given-When-Then con FluentAssertions

```csharp
[Fact]
public void Order_CalculateTotal_WithDiscounts_ReturnsCorrectAmount()
{
    // Given
    var order = new OrderBuilder()
        .WithItem("SKU-1", price: 100m, quantity: 2)  // 200
        .WithItem("SKU-2", price: 50m, quantity: 1)    // 50
        .WithDiscount("PROMO10", 10m)                   // -10
        .Build();

    // When
    var total = order.CalculateTotal();

    // Then
    total.Amount.Should().Be(240m);
    total.Currency.Should().Be("MXN");
}
```

---

## NSubstitute: mocking idiomático

### Lo esencial

```csharp
// Crear substitute
var repo = Substitute.For<IOrderRepository>();

// Configurar retorno
repo.GetByIdAsync(Arg.Any<Guid>(), Arg.Any<CancellationToken>())
    .Returns(Task.FromResult<Order?>(order));

// Retorno condicional
repo.GetByIdAsync(Arg.Is<Guid>(id => id == specificId), Arg.Any<CancellationToken>())
    .Returns(order);

// Método void
_repo.Received(1).Add(Arg.Is<Order>(o => o.CustomerId == "CUST-1"));

// No fue llamado
_repo.DidNotReceive().Delete(Arg.Any<Guid>());

// Async: NSubstitute maneja Task automáticamente
repo.GetByIdAsync(order.Id, Arg.Any<CancellationToken>()).Returns(order);
// No necesita Task.FromResult con NSubstitute 5+

// Lanzar excepción
repo.GetByIdAsync(Arg.Any<Guid>(), Arg.Any<CancellationToken>())
    .Returns<Task<Order?>>(_ => throw new NotFoundException("Order not found"));
```

### Lo que NO hacer con mocks

```csharp
// ❌ Mockear tipos concretos sin razón
var dbContext = Substitute.For<AppDbContext>(); // Muy complejo, usar Testcontainers/InMemory

// ❌ Mockear ILogger — usar NullLogger o ITestOutputHelper
var logger = Substitute.For<ILogger<OrderService>>(); // frágil, mucho setup

// ✅ En vez de mockear ILogger, inyectar NullLogger
var logger = NullLogger<OrderService>.Instance;

// ✅ O usar XunitLogger para ver logs en tests
services.AddSingleton<ILoggerFactory>(sp =>
    new XunitLoggerFactory(testOutputHelper));
```

---

## Test Data Builders

Patrón para construir objetos de prueba de forma legible:

```csharp
public class OrderBuilder
{
    private Guid _id = Guid.NewGuid();
    private string _customerId = "CUST-TEST";
    private OrderStatus _status = OrderStatus.Pending;
    private readonly List<OrderItem> _items = [];
    private readonly List<Discount> _discounts = [];
    private DateTime _createdAt = DateTime.UtcNow;

    public OrderBuilder WithId(Guid id) { _id = id; return this; }
    public OrderBuilder WithCustomer(string id) { _customerId = id; return this; }
    public OrderBuilder WithStatus(OrderStatus status) { _status = status; return this; }

    public OrderBuilder WithItem(string sku, decimal price, int quantity = 1)
    {
        _items.Add(new OrderItem(sku, price, quantity));
        return this;
    }

    public OrderBuilder WithDiscount(string code, decimal amount)
    {
        _discounts.Add(new Discount(code, amount));
        return this;
    }

    public OrderBuilder Cancelled(string reason = "Test cancellation")
    {
        _status = OrderStatus.Cancelled;
        return this;
    }

    public Order Build()
    {
        var order = Order.Create(_customerId, _items);
        typeof(Order).GetProperty(nameof(Order.Id))!.SetValue(order, _id);
        typeof(Order).GetProperty(nameof(Order.CreatedAt))!.SetValue(order, _createdAt);
        // Aplicar estado vía reflexión o factory method interno
        return order;
    }
}

// Uso
var order = new OrderBuilder()
    .WithCustomer("CUST-456")
    .WithItem("SKU1", 100m, 2)
    .WithItem("SKU2", 50m)
    .WithDiscount("SAVE10", 10m)
    .Build();
```

### Object Mother (datos predefinidos)

```csharp
public static class OrderTestData
{
    public static Order PendingOrder(string customerId = "CUST-001")
        => new OrderBuilder().WithCustomer(customerId).Build();

    public static Order LargeOrder()
        => new OrderBuilder()
            .WithItem("SKU1", 100m, 10)
            .WithItem("SKU2", 50m, 5)
            .Build();

    public static Order CancelledOrder()
        => new OrderBuilder().Cancelled().Build();
}
```

---

## Teorías y datos parametrizados

```csharp
// [Theory] con [InlineData] — para pocos casos
[Theory]
[InlineData(OrderStatus.Pending, true)]
[InlineData(OrderStatus.Confirmed, true)]
[InlineData(OrderStatus.Shipped, false)]
[InlineData(OrderStatus.Delivered, false)]
[InlineData(OrderStatus.Cancelled, false)]
public void Order_CanBeCancelled_OnlyInCertainStatuses(OrderStatus status, bool expected)
{
    var order = new OrderBuilder().WithStatus(status).Build();
    order.CanBeCancelled().Should().Be(expected);
}

// [ClassData] — para datos complejos
public class InvalidOrderData : TheoryData<string, List<OrderItem>, string>
{
    public InvalidOrderData()
    {
        Add("", [new("SKU1", 10, 1)], "CustomerId required");
        Add("CUST-1", [], "Must have at least one item");
        Add("CUST-1", [new("", 10, 1)], "SKU cannot be empty");
    }
}

[Theory]
[ClassData(typeof(InvalidOrderData))]
public void CreateOrder_WithInvalidData_ThrowsValidationException(
    string customerId, List<OrderItem> items, string expectedError)
{
    var act = () => Order.Create(customerId, items);
    act.Should().Throw<DomainException>().WithMessage($"*{expectedError}*");
}
```

---

## Integration Tests

### Testcontainers (preferido sobre InMemory)

```csharp
public class OrderRepositoryTests : IAsyncLifetime
{
    private readonly MsSqlContainer _sqlContainer = new MsSqlBuilder()
        .WithImage("mcr.microsoft.com/mssql/server:2022-latest")
        .WithPassword("Test@Pass123")
        .Build();

    private AppDbContext _db = null!;
    private OrderRepository _sut = null!;

    public async Task InitializeAsync()
    {
        await _sqlContainer.StartAsync();

        var options = new DbContextOptionsBuilder<AppDbContext>()
            .UseSqlServer(_sqlContainer.GetConnectionString())
            .Options;

        _db = new AppDbContext(options);
        await _db.Database.MigrateAsync(); // o EnsureCreatedAsync para simplicidad

        _sut = new OrderRepository(_db);
    }

    public async Task DisposeAsync()
    {
        await _db.DisposeAsync();
        await _sqlContainer.DisposeAsync();
    }

    [Fact]
    public async Task GetByIdAsync_WhenOrderExists_ReturnsOrder()
    {
        // Arrange
        var order = OrderTestData.PendingOrder();
        _db.Orders.Add(order);
        await _db.SaveChangesAsync();

        // Act
        var result = await _sut.GetByIdAsync(order.Id, CancellationToken.None);

        // Assert
        result.Should().NotBeNull();
        result!.Id.Should().Be(order.Id);
        result.Items.Should().HaveCount(order.Items.Count);
    }
}
```

### WebApplicationFactory (API integration tests)

```csharp
public class OrdersApiTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly WebApplicationFactory<Program> _factory;

    public OrdersApiTests(WebApplicationFactory<Program> factory)
    {
        _factory = factory.WithWebHostBuilder(builder =>
        {
            builder.ConfigureServices(services =>
            {
                // Reemplazar BD real con Testcontainer
                var dbDescriptor = services.Single(
                    d => d.ServiceType == typeof(DbContextOptions<AppDbContext>));
                services.Remove(dbDescriptor);

                services.AddDbContext<AppDbContext>(options =>
                    options.UseSqlServer(_testConnectionString));
            });
        });
    }

    [Fact]
    public async Task CreateOrder_WithValidData_ReturnsCreated()
    {
        // Arrange
        var client = _factory.CreateClient();
        var request = new { customerId = "CUST-1", items = new[] { new { sku = "SKU1", quantity = 1, price = 100m } } };

        // Act
        var response = await client.PostAsJsonAsync("/api/orders", request);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.Created);
        var body = await response.Content.ReadFromJsonAsync<OrderResponse>();
        body!.Id.Should().NotBeEmpty();
        body.Status.Should().Be("Pending");
    }
}
```

---

## TDD: Test-Driven Development

### Ciclo Red → Green → Refactor

```csharp
// 1. RED: escribir el test primero
[Fact]
public void CalculateShipping_WhenOrderAbove100_ReturnsFreeShipping()
{
    var order = new OrderBuilder().WithItem("SKU", 150m).Build();
    var result = ShippingCalculator.Calculate(order);
    result.Should().Be(0m);
}

// 2. GREEN: implementación mínima
public static class ShippingCalculator
{
    public static decimal Calculate(Order order) => 0m; // Suficiente para pasar el test
}

// 3. Segundo test: orden pequeña sí paga envío
[Fact]
public void CalculateShipping_WhenOrderBelow100_ReturnsShippingCost()
{
    var order = new OrderBuilder().WithItem("SKU", 50m).Build();
    var result = ShippingCalculator.Calculate(order);
    result.Should().Be(99m);
}

// 4. GREEN: implementación real
public static class ShippingCalculator
{
    public static decimal Calculate(Order order)
        => order.Total.Amount >= 100 ? 0m : 99m;
}

// 5. REFACTOR: extraer constantes y clarificar
public static class ShippingCalculator
{
    private const decimal FreeShippingThreshold = 100m;
    private const decimal StandardShippingCost = 99m;

    public static decimal Calculate(Order order)
        => order.Total.Amount >= FreeShippingThreshold ? 0m : StandardShippingCost;
}
```

---

## Snapshot Testing (Verify)

```csharp
// Instalar Verify.Xunit
[Fact]
public Task GetOrder_ReturnsExpectedJson()
{
    var order = OrderTestData.PendingOrder();
    var dto = OrderDto.From(order);

    return Verify(dto); // Genera GetOrder_ReturnsExpectedJson.verified.txt
    // Si el output cambia, el test falla. Revisar diff y aceptar o rechazar.
}
```

---

## Testing de Background Services

```csharp
[Fact]
public async Task OrderExpirationService_ExpiresOldPendingOrders()
{
    // Arrange
    var oldOrder = new OrderBuilder().WithStatus(OrderStatus.Pending).Build();
    typeof(Order).GetProperty(nameof(Order.CreatedAt))!.SetValue(oldOrder, DateTime.UtcNow.AddHours(-25));

    await using var db = CreateTestDbContext();
    db.Orders.Add(oldOrder);
    await db.SaveChangesAsync();

    var service = new OrderExpirationService(
        new TestScopeFactory(db),
        NullLogger<OrderExpirationService>.Instance);

    using var cts = new CancellationTokenSource();

    // Act
    var executeTask = service.StartAsync(cts.Token);
    await Task.Delay(200); // Dejar que ejecute una iteración
    cts.Cancel();
    await executeTask;

    // Assert
    var expired = await db.Orders.FindAsync(oldOrder.Id);
    expired!.Status.Should().Be(OrderStatus.Expired);
}

// Helper: IServiceScopeFactory para tests
public class TestScopeFactory(AppDbContext db) : IServiceScopeFactory
{
    public IServiceScope CreateScope() => new TestScope(db);
}
```

---

## Cobertura y métricas

### Qué medir

```bash
dotnet test /p:CollectCoverage=true /p:CoverletOutputFormat=cobertura
```

| Métrica | Objetivo realista |
|---------|-------------------|
| Line coverage | > 80% en Domain + Application |
| Branch coverage | > 70% |
| Lo que NO testear | Constructores de DI, mapeos automáticos, config binding |

### Estructura de proyecto de tests

```
tests/
├── MiApp.Domain.Tests/
│   └── Orders/
│       ├── OrderTests.cs
│       └── MoneyTests.cs
├── MiApp.Application.Tests/
│   └── Orders/
│       └── CancelOrderHandlerTests.cs
├── MiApp.Infrastructure.Tests/
│   └── Data/
│       └── OrderRepositoryTests.cs
└── MiApp.Api.Tests/
    ├── Integration/
    │   └── OrdersApiTests.cs
    └── Endpoints/
        └── CreateOrderEndpointTests.cs
```

---

## Anti-patrones de testing

### 1. Test frágil (acoplado a implementación)

```csharp
// ❌ Acoplado a implementación interna
_repo.Received(1).GetByIdAsync(order.Id, Arg.Any<CancellationToken>());
_repo.Received(1).SaveChangesAsync(Arg.Any<CancellationToken>());
// Si cambio GetByIdAsync por FindAsync, el test se rompe sin que la lógica cambie.

// ✅ Verificar resultado, no implementación
order.Status.Should().Be(OrderStatus.Cancelled);
// El test solo verifica el outcome. La implementación puede cambiar libremente.
```

### 2. Test que depende de orden de ejecución

```csharp
// ❌ Comparte estado mutable entre tests
private static Order _sharedOrder = new();

[Fact]
public void Test1() { _sharedOrder.Status = OrderStatus.Cancelled; }

[Fact]
public void Test2() { _sharedOrder.Status.Should().Be(OrderStatus.Pending); } // Fallará si Test1 corre primero
```

### 3. Test con lógica condicional

```csharp
// ❌ Si el test tiene if/switch/loops complejos: ¿quién testea al test?
[Fact]
public void ComplexTest()
{
    foreach (var status in Enum.GetValues<OrderStatus>())
    {
        if (status == OrderStatus.Cancelled) { ... }
        else if (...) { ... }
    }
}
// ✅ Usar [Theory] con datos parametrizados
```

### 4. Test que no falla nunca (falso positivo)

```csharp
// ❌ Assert genérico que siempre pasa
order.Should().NotBeNull();

// ❌ No esperar tareas async
_sut.Handle(command, CancellationToken.None); // No await → excepción se pierde

// ✅ Siempre await en tests async
await _sut.Handle(command, CancellationToken.None);
```

---

## Checklist de testing

- [ ] Cada handler/use case tiene al menos 2 tests: happy path + error
- [ ] Las entidades de dominio se testean sin mocks
- [ ] Los repositorios se testean con Testcontainers, no InMemory
- [ ] Las APIs se testean con WebApplicationFactory
- [ ] No se mockea ILogger (usar NullLogger o XunitLogger)
- [ ] No se mockea DbContext (usar Testcontainers)
- [ ] Tests usan builders/object mothers, no construyen objetos a mano
- [ ] Nombres de tests siguen `Method_Scenario_ExpectedResult`
- [ ] Tests son independientes entre sí (sin estado compartido)
