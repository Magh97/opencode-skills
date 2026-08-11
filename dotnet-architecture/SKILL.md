---
name: dotnet-architecture
description: Arquitectura de software en .NET. Cubre N-Capas, Clean Architecture, Hexagonal (Ports & Adapters), Vertical Slices y Modular Monolith. Incluye diagramas de referencia, estructura de proyectos, flujo de dependencias, reglas de acoplamiento, y criterios para elegir arquitectura según tamaño y complejidad del sistema. Actívala al diseñar nuevos sistemas, evaluar migraciones arquitectónicas o decidir estructura de solución.
disable-model-invocation: true
---

# Arquitectura en .NET

Guía de estilos arquitectónicos aplicados al ecosistema .NET moderno. Cubre **cuándo** usar cada uno, **cómo** estructurar la solución, y **reglas de dependencia** para que la arquitectura no se degrade.

---

## Tabla de decisión

| Arquitectura | Tamaño del sistema | Complejidad de dominio | Curva de aprendizaje | Recomendado para |
|-------------|-------------------|----------------------|---------------------|-----------------|
| N-Capas tradicional | Pequeño-Mediano | Baja-Media | Baja | CRUD, APIs simples, equipos junior |
| Clean Architecture | Mediano-Grande | Alta | Media | Dominios ricos, DDD, largo plazo |
| Hexagonal (Ports & Adapters) | Mediano-Grande | Alta | Media-Alta | Alta testeabilidad, múltiples adapters |
| Vertical Slices | Pequeño-Mediano | Media | Baja | Entregas rápidas, equipos full-stack |
| Modular Monolith | Mediano-Grande | Alta | Media | Migrar de monolito a microservicios gradualmente |

---

## 1. N-Capas tradicional

### Estructura

```
Solution.sln
├── src/
│   ├── MiApp.Presentation/       # Controllers, Views, Razor Pages
│   ├── MiApp.Business/           # Services, lógica de negocio
│   ├── MiApp.Data/               # EF Core, repositorios, DbContext
│   └── MiApp.Common/             # DTOs, helpers, extensiones
```

### Regla de dependencia

```
Presentation → Business → Data → Common
     ↓            ↓        ↓
   (todos dependen de Common)
```

La capa superior conoce a la inferior. **Problema**: Business conoce Data (EF Core). Cambiar de SQL Server a MongoDB requiere modificar Business.

### Cuándo usarla

- APIs CRUD simples (poca lógica de negocio)
- Prototipos y MVPs
- Equipos que recién empiezan con .NET
- Sistemas que no crecerán significativamente

### Cuándo NO usarla

- Dominio complejo con reglas de negocio que cambian frecuentemente
- Necesidad de cambiar infraestructura (BD, proveedor de pagos) sin tocar negocio
- Alta cobertura de tests unitarios sin BD

### Ejemplo .sln

```xml
<!-- MiApp.Business.csproj — solo depende de Common -->
<ItemGroup>
  <ProjectReference Include="..\MiApp.Common\MiApp.Common.csproj" />
</ItemGroup>

<!-- MiApp.Data.csproj — depende de Business y Common -->
<ItemGroup>
  <ProjectReference Include="..\MiApp.Business\MiApp.Business.csproj" />
  <ProjectReference Include="..\MiApp.Common\MiApp.Common.csproj" />
  <PackageReference Include="Microsoft.EntityFrameworkCore.SqlServer" />
</ItemGroup>
```

---

## 2. Clean Architecture

### Principio

> Las dependencias apuntan hacia adentro. El dominio no conoce nada externo.

```
Frameworks & Drivers  ←  Interface Adapters  ←  Application  ←  Domain
   (Infrastructure)         (API/Presentation)      (Use Cases)      (Entities)
```

### Estructura

```
Solution.sln
├── src/
│   ├── MiApp.Domain/                    # Entidades, Value Objects, Enums, interfaces de repos
│   │   ├── Orders/
│   │   │   ├── Order.cs
│   │   │   ├── OrderItem.cs
│   │   │   ├── OrderStatus.cs
│   │   │   └── IOrderRepository.cs      # ← interfaz definida AQUÍ
│   │   ├── Customers/
│   │   └── Common/
│   │       ├── ValueObjects/
│   │       │   ├── Money.cs
│   │       │   └── Email.cs
│   │       └── DomainException.cs
│   │
│   ├── MiApp.Application/               # Casos de uso, DTOs, interfaces externas
│   │   ├── Orders/
│   │   │   ├── CreateOrder/
│   │   │   │   ├── CreateOrderCommand.cs
│   │   │   │   ├── CreateOrderHandler.cs
│   │   │   │   └── CreateOrderValidator.cs
│   │   │   └── GetOrder/
│   │   │       ├── GetOrderQuery.cs
│   │   │       └── GetOrderHandler.cs
│   │   ├── Common/
│   │   │   ├── Interfaces/
│   │   │   │   ├── IEmailSender.cs      # ← abstracción definida por la app
│   │   │   │   ├── IPaymentGateway.cs
│   │   │   │   └── IUnitOfWork.cs
│   │   │   └── Behaviors/
│   │   │       └── ValidationBehavior.cs
│   │   └── DependencyInjection.cs       # Extensiones IServiceCollection
│   │
│   ├── MiApp.Infrastructure/            # Implementaciones concretas
│   │   ├── Data/
│   │   │   ├── AppDbContext.cs
│   │   │   ├── Configurations/
│   │   │   └── Repositories/
│   │   │       └── OrderRepository.cs   # ← implementa IOrderRepository
│   │   ├── Services/
│   │   │   ├── SmtpEmailSender.cs       # ← implementa IEmailSender
│   │   │   └── StripePaymentGateway.cs
│   │   └── DependencyInjection.cs
│   │
│   └── MiApp.Api/                       # Host, endpoints, middleware
│       ├── Endpoints/
│       │   └── Orders/
│       │       ├── CreateOrder.cs
│       │       └── GetOrder.cs
│       ├── Middleware/
│       ├── appsettings.json
│       └── Program.cs
```

### Reglas de dependencia (archivos .csproj)

```
MiApp.Domain        → sin dependencias externas (solo net10.0)
MiApp.Application   → MiApp.Domain (solo abstracciones)
MiApp.Infrastructure → MiApp.Application (implementa interfaces)
MiApp.Api           → MiApp.Application + MiApp.Infrastructure (compone DI)
```

### DependencyInjection en cada capa

```csharp
// MiApp.Application/DependencyInjection.cs
public static class ApplicationServiceExtensions
{
    public static IServiceCollection AddApplication(this IServiceCollection services)
    {
        services.AddMediatR(cfg => cfg.RegisterServicesFromAssembly(typeof(ApplicationServiceExtensions).Assembly));
        services.AddValidatorsFromAssembly(typeof(ApplicationServiceExtensions).Assembly);
        services.AddTransient(typeof(IPipelineBehavior<,>), typeof(ValidationBehavior<,>));
        return services;
    }
}

// MiApp.Infrastructure/DependencyInjection.cs
public static class InfrastructureServiceExtensions
{
    public static IServiceCollection AddInfrastructure(
        this IServiceCollection services, IConfiguration config)
    {
        services.AddDbContext<AppDbContext>(options =>
            options.UseSqlServer(config.GetConnectionString("Default")));

        services.AddScoped<IOrderRepository, OrderRepository>();
        services.AddScoped<IUnitOfWork>(sp => sp.GetRequiredService<AppDbContext>());
        services.AddScoped<IEmailSender, SmtpEmailSender>();

        return services;
    }
}

// MiApp.Api/Program.cs
var builder = WebApplication.CreateBuilder(args);
builder.Services
    .AddApplication()
    .AddInfrastructure(builder.Configuration);
```

### Flujo de una petición

```
HTTP Request → Api/Endpoints/CreateOrder.cs
    → MediatR → Application/Orders/CreateOrderHandler.cs
        → Domain/IOrderRepository.cs (abstracción)
        → Infrastructure/Repositories/OrderRepository.cs (implementación concreta, inyectada por DI)
        → Domain/Order.cs (entidad de negocio)
    → Response
```

### Cuándo usar Clean Architecture

- Dominio rico con reglas de negocio complejas
- Proyecto a largo plazo (+2 años)
- Equipo que crecerá y rotará
- Necesidad de testear lógica de negocio sin infraestructura
- Múltiples interfaces de entrada (API REST, gRPC, CLI, eventos)

### Cuándo NO

- CRUD simple con 10 endpoints. El overhead de 4 proyectos no se justifica.
- Prototipo de 2 semanas
- Equipo de 1-2 devs sin complejidad de dominio

---

## 3. Arquitectura Hexagonal (Ports & Adapters)

Misma idea que Clean Architecture pero con terminología distinta. El dominio está en el centro. Todo lo externo es un "adapter" que se conecta a través de un "port" (interfaz).

```
                  ┌──────────────────────────┐
                  │      DOMAIN (Core)        │
                  │  Entities + Value Objects │
                  │  + Port interfaces        │
                  └──────┬──────────┬─────────┘
                         │          │
              ┌──────────┴──┐  ┌───┴──────────────┐
              │ Primary     │  │ Secondary          │
              │ (Driving)   │  │ (Driven)           │
              │ Ports       │  │ Ports              │
              └──────┬──────┘  └───┬───────────────┘
                     │              │
        ┌────────────┴─────┐  ┌────┴────────────────┐
        │ Primary Adapters │  │ Secondary Adapters   │
        │ REST, gRPC, CLI  │  │ SQL, Redis, Stripe   │
        │ Tests            │  │ Email, S3, Event Bus │
        └──────────────────┘  └──────────────────────┘
```

### Puertos primarios (Driving) — lo que llama al dominio

```csharp
// Domain/Ports/Primary/IOrderService.cs
public interface IOrderService
{
    Task<OrderDto> PlaceOrderAsync(PlaceOrderCommand command, CancellationToken ct);
    Task CancelOrderAsync(Guid orderId, CancellationToken ct);
}
```

### Puertos secundarios (Driven) — lo que el dominio necesita del exterior

```csharp
// Domain/Ports/Secondary/IOrderRepository.cs
public interface IOrderRepository
{
    Task<Order?> GetByIdAsync(Guid id, CancellationToken ct);
    void Add(Order order);
}

// Domain/Ports/Secondary/IPaymentGateway.cs
public interface IPaymentGateway
{
    Task<PaymentResult> ChargeAsync(Money amount, PaymentMethod method, CancellationToken ct);
}
```

### Diferencia con Clean Architecture

Hexagonal enfatiza la simetría (puertos de entrada y salida). Clean Architecture enfatiza las capas concéntricas. En la práctica .NET, Clean Architecture es más común y tiene más tooling. Elige la terminología que tu equipo entienda.

---

## 4. Vertical Slices

En vez de separar por capa técnica, separar por feature. Cada feature es un slice vertical que contiene todo lo necesario.

```
src/MiApp/
├── Orders/
│   ├── CreateOrder/
│   │   └── CreateOrderEndpoint.cs      # Endpoint + Command + Handler
│   ├── CancelOrder/
│   │   └── CancelOrderEndpoint.cs
│   └── GetOrder/
│       └── GetOrderEndpoint.cs
├── Customers/
│   ├── Register/
│   └── GetProfile/
├── Payments/
│   └── ProcessPayment/
└── Shared/                              # Código compartido entre features
    ├── Data/AppDbContext.cs
    ├── Middleware/
    └── Common/
```

### Endpoint como slice completo (Minimal API + Carter o manual)

```csharp
// Orders/CreateOrder/CreateOrderEndpoint.cs
public static class CreateOrderEndpoint
{
    public record Request(string CustomerId, List<OrderItemDto> Items);

    public static void Map(IEndpointRouteBuilder app)
    {
        app.MapPost("/api/orders", HandleAsync)
            .WithName("CreateOrder")
            .WithTags("Orders")
            .RequireAuthorization()
            .Produces<OrderResponse>(StatusCodes.Status201Created)
            .ProducesValidationProblem();
    }

    private static async Task<IResult> HandleAsync(
        Request request,
        AppDbContext db,
        IEmailSender emailSender,
        ILogger<CreateOrderEndpoint> logger,
        CancellationToken ct)
    {
        // Lógica directamente en el endpoint para features simples
        var customer = await db.Customers.FindAsync([request.CustomerId], ct);
        if (customer is null)
            return Results.NotFound("Customer not found");

        var order = Order.Create(customer, request.Items);
        db.Orders.Add(order);
        await db.SaveChangesAsync(ct);

        await emailSender.SendOrderConfirmationAsync(order, ct);
        logger.LogInformation("Order {OrderId} created", order.Id);

        return Results.Created($"/api/orders/{order.Id}", OrderResponse.From(order));
    }
}

// Program.cs
app.MapEndpoints(); // Extension method que llama CreateOrderEndpoint.Map(app);
```

### Cuándo usar Vertical Slices

- **Siempre como organización de archivos dentro de cualquier arquitectura.** Podés tener Clean Architecture con slices verticales internos.
- Aplicaciones medianas con features independientes
- Equipos con propiedad por feature (cada dev dueño de 2-3 slices)

### Combinación recomendada: Vertical Slices + Clean Architecture

```
MiApp.Api/
└── Orders/
    └── CreateOrder/
        └── CreateOrderEndpoint.cs   # Minimal API + llamada a MediatR

MiApp.Application/
└── Orders/
    └── CreateOrder/
        ├── CreateOrderCommand.cs
        └── CreateOrderHandler.cs    # Lógica de negocio

MiApp.Domain/
└── Orders/
    ├── Order.cs
    └── IOrderRepository.cs

MiApp.Infrastructure/
└── Data/Repositories/
    └── OrderRepository.cs
```

---

## 5. Modular Monolith

Monolito desplegado como una unidad, pero organizado en módulos independientes con comunicación interna vía contratos (interfaces + eventos).

```
Solution.sln
├── src/
│   ├── MiApp.Api/                           # Host
│   ├── Modules/
│   │   ├── Orders/
│   │   │   ├── MiApp.Modules.Orders.Api/    # Endpoints del módulo
│   │   │   ├── MiApp.Modules.Orders.Application/
│   │   │   ├── MiApp.Modules.Orders.Domain/
│   │   │   └── MiApp.Modules.Orders.Infrastructure/
│   │   ├── Customers/
│   │   │   ├── MiApp.Modules.Customers.Api/
│   │   │   ├── MiApp.Modules.Customers.Application/
│   │   │   └── MiApp.Modules.Customers.Domain/
│   │   └── Payments/
│   │       ├── MiApp.Modules.Payments.Api/
│   │       └── MiApp.Modules.Payments.Application/
│   └── Shared/
│       └── MiApp.Shared.Abstractions/       # Interfaces y DTOs compartidos
```

### Reglas de acoplamiento entre módulos

1. Un módulo solo referencia a las abstracciones del otro módulo, **nunca** a su implementación interna.
2. Comunicación síncrona: vía interfaz + DI.
3. Comunicación asíncrona: eventos de integración.

```csharp
// Orders quiere saber si un Customer existe

// ❌ Orders referencia la entidad Customer de Customers.Domain
// Orders depende de Customers.Domain — acoplamiento fuerte

// ✅ Orders depende de una abstracción en Shared
// Shared/MiApp.Shared.Abstractions/Customers/ICustomerChecker.cs
public interface ICustomerChecker
{
    Task<bool> ExistsAsync(string customerId, CancellationToken ct);
}

// Modules/Customers/MiApp.Modules.Customers.Infrastructure/CustomerChecker.cs
internal class CustomerChecker(AppDbContext db) : ICustomerChecker
{
    public async Task<bool> ExistsAsync(string customerId, CancellationToken ct)
        => await db.Customers.AnyAsync(c => c.Id == customerId, ct);
}

// Customers module registra su implementación
services.AddScoped<ICustomerChecker, CustomerChecker>();

// Orders consume la abstracción
public class CreateOrderHandler(
    ICustomerChecker customerChecker,
    IOrderRepository orderRepository) : IRequestHandler<...>
{
    public async Task<OrderDto> Handle(CreateOrderCommand cmd, CancellationToken ct)
    {
        if (!await customerChecker.ExistsAsync(cmd.CustomerId, ct))
            throw new DomainException("Customer not found");
        // ...
    }
}
```

### Comunicación asíncrona entre módulos

```csharp
// Shared/MiApp.Shared.Abstractions/Events/OrderCompletedIntegrationEvent.cs
public record OrderCompletedIntegrationEvent(Guid OrderId, string CustomerId, decimal Total);

// Orders module publica
await _eventBus.PublishAsync(new OrderCompletedIntegrationEvent(order.Id, customerId, total));

// Customers module escucha
public class OrderCompletedHandler : IIntegrationEventHandler<OrderCompletedIntegrationEvent>
{
    public async Task Handle(OrderCompletedIntegrationEvent @event)
    {
        // Actualizar CustomerStats, enviar email, etc.
    }
}
```

### Cuándo migrar un módulo a microservicio

- El módulo tiene necesidades de escalado distintas
- El módulo tiene un ciclo de release independiente
- El módulo requiere un stack tecnológico diferente
- El equipo dueño del módulo necesita deploy independiente

Hasta que alguna de estas condiciones se cumpla: mantener como módulo dentro del monolito.

---

## Comparativa .csproj dependencies

### N-Capas

```
Api → Business → Data → Common
     (Api conoce Data indirectamente vía Business)
```

### Clean Architecture

```
Api → Application → Domain
Api → Infrastructure → Application → Domain
     (Domain no conoce a nadie)
```

### Vertical Slices

```
Api → Domain (referencia directa, sin capas intermedias)
```

### Modular Monolith

```
Api → Modules/Orders/Api
Api → Modules/Customers/Api
Modules/Orders/Domain → Shared/Abstractions (solo interfaces)
Modules/Orders/Infrastructure → Shared/Abstractions
     (Módulos no se conocen entre sí; solo vía Shared)
```

---

## Reglas de oro transversales

### 1. Domain no depende de nadie

Nunca referenciar `Microsoft.EntityFrameworkCore` o `System.Net.Http` desde Domain. Domain es C# puro.

### 2. Inyección de dependencias como pegamento

La composición de objetos ocurre en el entry point (Api/Program.cs o módulo). Las capas internas no hacen `new` de dependencias externas.

### 3. Interfaces definidas por el consumidor

```csharp
// ✅ IOrderRepository definida en Domain (el consumidor)
// ✅ implementada en Infrastructure

// ❌ IOrderRepository definida en Infrastructure
//    → Domain depende de Infrastructure (violación DIP)
```

### 4. Cada capa registra sus propias dependencias

```csharp
// ✅ Cada proyecto tiene su propio AddXxx extension method
services.AddApplication();
services.AddInfrastructure(configuration);
services.AddModules(builder.Configuration); // Modular Monolith

// ❌ Program.cs con 50 líneas de registros manuales
services.AddScoped<IOrderRepository, OrderRepository>();
services.AddScoped<ICustomerRepository, CustomerRepository>();
services.AddScoped<IEmailSender, SmtpEmailSender>();
// ... 47 más
```

### 5. Testeabilidad como métrica

Si para testear lógica de negocio necesitas montar una BD: la arquitectura está mal. La lógica de dominio se debe testear con unit tests puros (sin infraestructura).

```csharp
// ✅ Test unitario de dominio — sin DB, sin DI
[Fact]
public void Order_Cancel_WhenPending_Succeeds()
{
    var order = Order.Create(/* ... */);
    order.Cancel("Customer request");
    Assert.Equal(OrderStatus.Cancelled, order.Status);
}

// ✅ Test de handler — mocks de interfaces, no de EF
[Fact]
public async Task CancelOrderHandler_WhenOrderExists_Cancels()
{
    var order = Order.Create(/* ... */);
    var repo = Substitute.For<IOrderRepository>();
    repo.GetByIdAsync(order.Id, Arg.Any<CancellationToken>()).Returns(order);

    var handler = new CancelOrderHandler(repo, Substitute.For<IUnitOfWork>());
    await handler.Handle(new CancelOrderCommand(order.Id), CancellationToken.None);

    Assert.Equal(OrderStatus.Cancelled, order.Status);
}
```

---

## Checklist de decisión arquitectónica

| Pregunta | Respuesta | Arquitectura sugerida |
|----------|-----------|----------------------|
| ¿El dominio tiene reglas de negocio complejas? | Sí | Clean Architecture o Hexagonal |
| ¿El dominio tiene reglas de negocio complejas? | No (CRUD) | N-Capas o Vertical Slices |
| ¿El sistema crecerá a 50+ features? | Sí | Modular Monolith |
| ¿El equipo es de 2-3 devs? | Sí | Vertical Slices dentro de Clean |
| ¿Necesitamos desplegar partes independientemente? | Sí | Modular Monolith → extraer microservicios |
| ¿Necesitamos cambiar de SQL Server a otra BD? | Sí | Clean Architecture (domain sin dependencia de EF) |
| ¿MVP en 2 semanas? | Sí | N-Capas o Vertical Slices. Migrar a Clean después. |
| ¿Múltiples interfaces de entrada (REST, gRPC, eventos)? | Sí | Clean o Hexagonal |

### Regla pragmática

> Empieza con Vertical Slices. Si el dominio se vuelve complejo, extrae Domain + Application. Si el sistema crece, modulariza. Si necesitas escalado independiente, extrae microservicios. No empieces por el final.
