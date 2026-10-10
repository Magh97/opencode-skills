# OpenAPI, versionado y protocolos

> Referencia de `dotnet-api`. Cárgala solo cuando necesites el detalle.

## OpenAPI / Swagger

### .NET 9+ (Microsoft.AspNetCore.OpenApi)

```csharp
// Program.cs
builder.Services.AddOpenApi();

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.MapOpenApi(); // GET /openapi/v1.json
}

// Con Scalar UI (alternativa ligera a Swagger UI)
// app.MapScalarApiReference(); — si usas Scalar.AspNetCore
```

### Documentación con .WithOpenApi()

```csharp
app.MapGet("/api/orders/{id}", async (Guid id, AppDbContext db, CancellationToken ct) =>
{
    var order = await db.Orders.FindAsync([id], ct);
    return order is not null ? Results.Ok(order) : Results.NotFound();
})
.WithName("GetOrder")
.WithOpenApi(operation =>
{
    operation.Summary = "Gets an order by ID";
    operation.Description = "Returns the order with its items and status.";
    operation.Parameters[0].Description = "The order unique identifier";

    // Ejemplo de respuesta
    operation.Responses[StatusCodes.Status200OK.ToString()] = new OpenApiResponse
    {
        Description = "Order found",
        Content = new Dictionary<string, OpenApiMediaType>
        {
            ["application/json"] = new() { Example = new OpenApiString("{\"id\": \"...\"}") }
        }
    };

    return operation;
});
```

### Generar OpenAPI desde código (source generators para AOT)

```csharp
// .NET 10 mejora la generación de OpenAPI en AOT.
// Los source generators producen el schema en build-time,
// eliminando reflection. Disponible con Microsoft.AspNetCore.OpenApi 10.x
```

---


## Versioning

### URL-based (recomendado)

```csharp
var v1 = app.MapGroup("/api/v1/orders").WithTags("Orders v1");
v1.MapPost("/", CreateOrderV1.HandleAsync);
v1.MapGet("/{id}", GetOrderV1.HandleAsync);

var v2 = app.MapGroup("/api/v2/orders").WithTags("Orders v2");
v2.MapPost("/", CreateOrderV2.HandleAsync);
v2.MapGet("/{id}", GetOrderV2.HandleAsync);
```

### Header-based con Asp.Versioning.Http

```csharp
// NuGet: Asp.Versioning.Http
builder.Services.AddApiVersioning(options =>
{
    options.DefaultApiVersion = new ApiVersion(1, 0);
    options.AssumeDefaultVersionWhenUnspecified = true;
    options.ReportApiVersions = true;
    options.ApiVersionReader = new HeaderApiVersionReader("api-version");
});
```

---


## gRPC

### Cuando usar gRPC sobre REST

- Comunicación servicio a servicio (microservicios)
- Streaming bidireccional
- Alta frecuencia de mensajes pequeños
- Contratos fuertemente tipados

```protobuf
// orders.proto
service OrderService {
  rpc CreateOrder (CreateOrderRequest) returns (CreateOrderResponse);
  rpc GetOrder (GetOrderRequest) returns (Order);
  rpc StreamOrders (OrderFilter) returns (stream Order);
}

message CreateOrderRequest {
  string customer_id = 1;
  repeated OrderItem items = 2;
}
```

```csharp
// Program.cs
builder.Services.AddGrpc();

var app = builder.Build();
app.MapGrpcService<OrderGrpcService>();
app.Run();

// Implementación
public class OrderGrpcService(IMediator mediator) : OrderService.OrderServiceBase
{
    public override async Task<CreateOrderResponse> CreateOrder(
        CreateOrderRequest request, ServerCallContext context)
    {
        var result = await mediator.Send(
            new CreateOrderCommand(request.CustomerId, request.Items.ToDto()),
            context.CancellationToken);

        return new CreateOrderResponse { OrderId = result.OrderId.ToString() };
    }
}
```

---


## SignalR (WebSockets)

```csharp
// Hub
public class OrderHub : Hub
{
    public async Task SubscribeToOrder(string orderId)
    {
        await Groups.AddToGroupAsync(Context.ConnectionId, $"order-{orderId}");
    }

    // Desde el backend: notificar cambios
    // IHubContext<OrderHub> hubContext;
    // await hubContext.Clients.Group($"order-{orderId}").SendAsync("OrderUpdated", dto);
}

// Program.cs
builder.Services.AddSignalR();
app.MapHub<OrderHub>("/hubs/orders");
```

---


## Content Negotiation & Output Formatters

```csharp
// Por defecto, ASP.NET Core acepta JSON y XML (si se configura)
builder.Services.ConfigureHttpJsonOptions(options =>
{
    options.SerializerOptions.PropertyNamingPolicy = JsonNamingPolicy.CamelCase;
    options.SerializerOptions.WriteIndented = app.Environment.IsDevelopment();
    options.SerializerOptions.Converters.Add(new JsonStringEnumConverter());
});

// Para XML
builder.Services.AddControllers()
    .AddXmlSerializerFormatters();
```

---


## HATEOAS (Hypermedia)

```csharp
public class OrderResponse
{
    public Guid Id { get; init; }
    public string Status { get; init; }
    public decimal Total { get; init; }
    public List<Link> Links { get; init; } = [];
}

public record Link(string Rel, string Href, string Method);

// Generar links
private static List<Link> BuildLinks(Guid orderId, OrderStatus status)
{
    var links = new List<Link>
    {
        new("self", $"/api/orders/{orderId}", "GET"),
        new("cancel", $"/api/orders/{orderId}/cancel", "POST")
    };

    if (status == OrderStatus.Confirmed)
        links.Add(new("ship", $"/api/orders/{orderId}/ship", "POST"));

    return links;
}
```

**Nota**: HATEOAS solo si el cliente lo consume (API pública, explorable). Si es API interna con contrato conocido, YAGNI.

---
