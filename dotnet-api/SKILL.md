---
name: dotnet-api
description: APIs REST y Minimal APIs en .NET 9/10. Cubre Minimal APIs, Controllers, OpenAPI/Swagger, versioning, validación, HATEOAS, gRPC, SignalR, rate limiting, CORS, response caching, y documentación. Incluye patrones de organización de endpoints, mapeo de rutas, filtros, y mejores prácticas de diseño de API RESTful. Actívala al diseñar o implementar APIs HTTP.
disable-model-invocation: true
---

# APIs en .NET (REST, Minimal API, gRPC)

Guía de diseño e implementación de APIs HTTP en .NET 9/10. Foco en Minimal APIs para proyectos nuevos, Controllers cuando el equipo lo prefiere.

---

## Minimal APIs vs Controllers

| Aspecto | Minimal API | Controller-based |
|---------|-------------|------------------|
| Verbosidad | Baja | Alta (atributos, clases) |
| Performance | Mejor (menos middleware interno) | Base |
| AOT | ✅ Nativo | ⬜ Parcial |
| OpenAPI | `.WithOpenApi()` (built-in) | Swashbuckle / NSwag |
| Organización | Por feature / endpoint files | Por controllername |
| Filtros | `IEndpointFilter` | `IActionFilter`, `IAuthorizationFilter` |
| Model binding | `AsParameters` | `[FromBody]`, `[FromQuery]` |

**Recomendación 2026**: Minimal APIs para proyectos nuevos. Controllers si el equipo ya los domina.

---

## Minimal API — Estructura

### Endpoint como static method

```csharp
// Orders/CreateOrder.cs
public static class CreateOrderEndpoint
{
    public record Request(string CustomerId, List<OrderItemDto> Items);
    public record Response(Guid OrderId, string Status, decimal Total);

    public static void Map(IEndpointRouteBuilder app)
    {
        app.MapPost("/api/orders", HandleAsync)
            .WithName("CreateOrder")
            .WithTags("Orders")
            .WithSummary("Creates a new order")
            .WithDescription("Creates an order for the given customer and items.")
            .Produces<Response>(StatusCodes.Status201Created)
            .ProducesValidationProblem()
            .ProducesProblem(StatusCodes.Status409Conflict)
            .RequireAuthorization("orders:create")
            .Validate<Request>(); // FluentValidation endpoint filter
    }

    private static async Task<IResult> HandleAsync(
        Request request,
        IMediator mediator,
        CancellationToken ct)
    {
        var command = new CreateOrderCommand(request.CustomerId, request.Items);
        var result = await mediator.Send(command, ct);

        return Results.CreatedAtRoute(
            "GetOrder",
            new { id = result.OrderId },
            new Response(result.OrderId, result.Status, result.Total));
    }
}
```

### Mapeo automático de todos los endpoints

```csharp
// Program.cs
var app = builder.Build();

app.MapEndpoints(); // Extension method propio

// Extensions/EndpointExtensions.cs
public static class EndpointExtensions
{
    public static IEndpointRouteBuilder MapEndpoints(this IEndpointRouteBuilder app)
    {
        var endpointTypes = typeof(Program).Assembly
            .GetTypes()
            .Where(t => t.IsClass && !t.IsAbstract && t.GetMethod("Map") is not null);

        foreach (var type in endpointTypes)
        {
            var mapMethod = type.GetMethod("Map")!;
            mapMethod.Invoke(null, [app]);
        }

        return app;
    }
}
```

### Grupos de endpoints

```csharp
var orders = app.MapGroup("/api/orders")
    .WithTags("Orders")
    .RequireAuthorization();

orders.MapPost("/", CreateOrderEndpoint.HandleAsync);
orders.MapGet("/{id:guid}", GetOrderEndpoint.HandleAsync);
orders.MapPost("/{id:guid}/cancel", CancelOrderEndpoint.HandleAsync);

// Grupo con rate limiting
var payments = app.MapGroup("/api/payments")
    .RequireRateLimiting("payment-policy");
```

---

## Controller-based

```csharp
[ApiController]
[Route("api/[controller]")]
[Authorize]
public class OrdersController(IMediator mediator) : ControllerBase
{
    [HttpPost]
    [ProducesResponseType(typeof(OrderResponse), StatusCodes.Status201Created)]
    [ProducesResponseType(typeof(ValidationProblemDetails), StatusCodes.Status400BadRequest)]
    [Authorize("orders:create")]
    public async Task<IActionResult> Create(
        [FromBody] CreateOrderRequest request,
        CancellationToken ct)
    {
        var command = new CreateOrderCommand(request.CustomerId, request.Items);
        var result = await mediator.Send(command, ct);

        return CreatedAtAction(nameof(GetById), new { id = result.OrderId }, OrderResponse.From(result));
    }

    [HttpGet("{id:guid}")]
    [ProducesResponseType(typeof(OrderResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetById(Guid id, CancellationToken ct)
    {
        var result = await mediator.Send(new GetOrderQuery(id), ct);
        return result is not null ? Ok(result) : NotFound();
    }
}
```

---

## Validación

### FluentValidation + Endpoint filter (Minimal API)

```csharp
// Filtro reutilizable
public class ValidationFilter<T> : IEndpointFilter where T : class
{
    public async ValueTask<object?> InvokeAsync(
        EndpointFilterInvocationContext context,
        EndpointFilterDelegate next)
    {
        var validator = context.HttpContext.RequestServices
            .GetRequiredService<IValidator<T>>();

        var argument = context.Arguments
            .OfType<T>()
            .FirstOrDefault();

        if (argument is null)
            return Results.BadRequest("Invalid request body");

        var validationResult = await validator.ValidateAsync(argument);

        if (!validationResult.IsValid)
        {
            return Results.ValidationProblem(
                validationResult.ToDictionary(),
                detail: "Validation failed",
                instance: context.HttpContext.Request.Path);
        }

        return await next(context);
    }
}

// Extension method para registro limpio
public static class ValidationFilterExtensions
{
    public static RouteHandlerBuilder Validate<T>(
        this RouteHandlerBuilder builder) where T : class
    {
        builder.AddEndpointFilter<ValidationFilter<T>>();
        return builder;
    }
}

// Uso
app.MapPost("/api/orders", handler)
    .Validate<CreateOrderRequest>();
```

### Validación de configuración en startup

```csharp
services.AddOptions<StripeOptions>()
    .Bind(configuration.GetSection("Stripe"))
    .ValidateDataAnnotations()
    .ValidateOnStart(); // ← Falla al arrancar si la config es inválida
```

---

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

## Respuestas HTTP idiomáticas

```csharp
// ✅ Results.* — helpers tipados para respuestas comunes
Results.Ok(data);                    // 200
Results.Created($"/api/orders/{id}", data); // 201
Results.CreatedAtRoute("GetOrder", new { id }, data); // 201 con Location header
Results.NoContent();                 // 204
Results.BadRequest(new { error });   // 400
Results.NotFound(new { error });     // 404
Results.Conflict(new { error });     // 409
Results.UnprocessableEntity(new { error }); // 422
Results.Problem("Internal error");   // 500 con ProblemDetails
Results.ValidationProblem(errors);   // 400 con validation errors

// Tipado genérico con TypedResults (.NET 7+)
// Permite que OpenAPI infiera el tipo de respuesta
static async Task<Results<Ok<OrderResponse>, NotFound>> GetOrder(Guid id, ...)
{
    var order = await ...;
    return order is not null
        ? TypedResults.Ok(OrderResponse.From(order))
        : TypedResults.NotFound();
}
```

---

## Manejo global de errores

```csharp
public class GlobalExceptionHandler(ILogger<GlobalExceptionHandler> logger)
    : IExceptionHandler
{
    public async ValueTask<bool> TryHandleAsync(
        HttpContext context,
        Exception exception,
        CancellationToken ct)
    {
        var (statusCode, title) = exception switch
        {
            ValidationException => (StatusCodes.Status400BadRequest, "Validation failed"),
            NotFoundException => (StatusCodes.Status404NotFound, "Resource not found"),
            DomainException => (StatusCodes.Status422UnprocessableEntity, "Business rule violation"),
            UnauthorizedAccessException => (StatusCodes.Status403Forbidden, "Access denied"),
            _ => (StatusCodes.Status500InternalServerError, "Internal server error")
        };

        if (statusCode == StatusCodes.Status500InternalServerError)
            logger.LogError(exception, "Unhandled exception");

        var problem = new ProblemDetails
        {
            Status = statusCode,
            Title = title,
            Detail = exception.Message,
            Instance = context.Request.Path,
            Type = $"https://httpstatuses.io/{statusCode}"
        };

        if (exception is ValidationException ve)
            problem.Extensions["errors"] = ve.Errors;

        context.Response.StatusCode = statusCode;
        await context.Response.WriteAsJsonAsync(problem, ct);

        return true;
    }
}

// Program.cs
builder.Services.AddExceptionHandler<GlobalExceptionHandler>();
builder.Services.AddProblemDetails();

var app = builder.Build();
app.UseExceptionHandler(); // Solo esta línea, sin configurar opciones
app.UseStatusCodePages();  // Para 404s que no son excepciones
```

---

## CORS

```csharp
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowedOrigins", policy =>
    {
        policy.WithOrigins("https://miapp.com", "https://admin.miapp.com")
              .AllowAnyHeader()
              .AllowAnyMethod()
              .AllowCredentials();

        // Para desarrollo
        if (builder.Environment.IsDevelopment())
            policy.WithOrigins("http://localhost:5173");
    });
});

app.UseCors("AllowedOrigins"); // Antes de MapEndpoints()
```

---

## Autenticación y Autorización

### JWT Bearer

```csharp
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.Authority = "https://auth.miapp.com";
        options.Audience = "miapp-api";

        // Validación adicional
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateLifetime = true,
            ValidateIssuerSigningKey = true,
            ClockSkew = TimeSpan.FromSeconds(30) // Margen para clock drift
        };

        // Eventos para debug / custom claims
        options.Events = new JwtBearerEvents
        {
            OnTokenValidated = context =>
            {
                // Mapear claims a roles personalizados
                var claims = context.Principal!.Claims;
                // ...
                return Task.CompletedTask;
            }
        };
    });

builder.Services.AddAuthorization(options =>
{
    options.AddPolicy("orders:create", policy =>
        policy.RequireClaim("permissions", "orders:create"));

    options.AddPolicy("admin", policy =>
        policy.RequireRole("Admin"));
});
```

### API Key para integraciones

```csharp
public class ApiKeyAuthenticationHandler(
    IOptionsMonitor<AuthenticationSchemeOptions> options,
    ILoggerFactory logger,
    UrlEncoder encoder) : AuthenticationHandler<AuthenticationSchemeOptions>(options, logger, encoder)
{
    public const string ApiKeyHeaderName = "X-Api-Key";
    public const string SchemeName = "ApiKey";

    protected override Task<AuthenticateResult> HandleAuthenticateAsync()
    {
        if (!Request.Headers.TryGetValue(ApiKeyHeaderName, out var apiKey))
            return Task.FromResult(AuthenticateResult.NoResult());

        // Validar contra BD o configuración
        var isValid = apiKey == "test-key"; // Ejemplo — usar IOptions en prod
        if (!isValid)
            return Task.FromResult(AuthenticateResult.Fail("Invalid API Key"));

        var claims = new[] { new Claim(ClaimTypes.Name, "API Client") };
        var identity = new ClaimsIdentity(claims, SchemeName);
        var principal = new ClaimsPrincipal(identity);
        var ticket = new AuthenticationTicket(principal, SchemeName);

        return Task.FromResult(AuthenticateResult.Success(ticket));
    }
}

// Registro
builder.Services.AddAuthentication()
    .AddScheme<AuthenticationSchemeOptions, ApiKeyAuthenticationHandler>(
        "ApiKey", null);
```

---

## Response Caching

```csharp
// Cache en memoria por 5 minutos
app.MapGet("/api/products", async (AppDbContext db, CancellationToken ct) =>
{
    return await db.Products.AsNoTracking().ToListAsync(ct);
})
.CacheOutput(policy => policy.Expire(TimeSpan.FromMinutes(5)));

// Vary por query string
.CacheOutput(policy => policy
    .SetVaryByQuery("category")
    .Expire(TimeSpan.FromMinutes(10)));

// Output cache con Redis (producción)
builder.Services.AddStackExchangeRedisOutputCache(options =>
{
    options.Configuration = builder.Configuration.GetConnectionString("Redis");
});
```

---

## Rate Limiting

```csharp
builder.Services.AddRateLimiter(options =>
{
    // Política global
    options.AddFixedWindowLimiter("global", config =>
    {
        config.PermitLimit = 1000;
        config.Window = TimeSpan.FromMinutes(1);
    });

    // Política por endpoint crítico
    options.AddFixedWindowLimiter("auth", config =>
    {
        config.PermitLimit = 5;
        config.Window = TimeSpan.FromMinutes(1);
    });

    // Política por IP
    options.AddPolicy("by-ip", context =>
        RateLimitPartition.GetFixedWindowLimiter(
            context.Connection.RemoteIpAddress?.ToString() ?? "unknown",
            _ => new FixedWindowRateLimiterOptions
            {
                PermitLimit = 100,
                Window = TimeSpan.FromMinutes(1)
            }));

    options.RejectionStatusCode = StatusCodes.Status429TooManyRequests;
});

app.UseRateLimiter();

// Endpoint específico
app.MapPost("/api/auth/login", handler)
    .RequireRateLimiting("auth");
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

## Buenas prácticas REST

### Nombrado de endpoints

```
✅ GET    /api/orders                   # Listar
✅ GET    /api/orders/{id}              # Obtener
✅ POST   /api/orders                   # Crear
✅ PUT    /api/orders/{id}              # Reemplazar
✅ PATCH  /api/orders/{id}              # Actualización parcial
✅ DELETE /api/orders/{id}              # Eliminar
✅ POST   /api/orders/{id}/cancel       # Acción (verbo)
✅ GET    /api/orders/{id}/items        # Sub-recurso

❌ GET    /api/GetOrders                # Verbo en URL
❌ POST   /api/orders/create            # Verbo redundante
❌ GET    /api/orders?id=123            # ID en query string
```

### Paginación, filtrado, ordenamiento

```csharp
app.MapGet("/api/orders", async (
    [AsParameters] OrderListRequest request,
    AppDbContext db,
    CancellationToken ct) =>
{
    var query = db.Orders.AsNoTracking();

    // Filtros
    if (request.Status is not null)
        query = query.Where(o => o.Status == request.Status);
    if (request.CustomerId is not null)
        query = query.Where(o => o.CustomerId == request.CustomerId);

    // Ordenamiento
    query = request.SortBy?.ToLower() switch
    {
        "createdat" => request.SortDescending ?? false
            ? query.OrderByDescending(o => o.CreatedAt)
            : query.OrderBy(o => o.CreatedAt),
        "total" => request.SortDescending ?? false
            ? query.OrderByDescending(o => o.Total.Amount)
            : query.OrderBy(o => o.Total.Amount),
        _ => query.OrderByDescending(o => o.CreatedAt)
    };

    // Paginación
    var total = await query.CountAsync(ct);
    var items = await query
        .Skip((request.Page - 1) * request.PageSize)
        .Take(request.PageSize)
        .Select(o => new OrderSummaryDto(o.Id, o.Status, o.Total.Amount, o.CreatedAt))
        .ToListAsync(ct);

    return Results.Ok(new PaginatedResponse<OrderSummaryDto>(
        items, request.Page, request.PageSize, total));
});

public record OrderListRequest(
    OrderStatus? Status = null,
    string? CustomerId = null,
    string? SortBy = "createdat",
    bool? SortDescending = true,
    int Page = 1,
    int PageSize = 20);
```

### Formato de respuesta estándar

```csharp
// Envoltorio consistente
public class ApiResponse<T>
{
    public bool Success { get; init; }
    public T? Data { get; init; }
    public string? Error { get; init; }
    public string? TraceId { get; init; }
}

public class PaginatedResponse<T> : ApiResponse<List<T>>
{
    public int Page { get; init; }
    public int PageSize { get; init; }
    public int Total { get; init; }
    public int TotalPages => (int)Math.Ceiling((double)Total / PageSize);
}
```

---

## Checklist de API

- [ ] Endpoints usan nombres de recurso (plural), no verbos
- [ ] Validación de entrada con FluentValidation
- [ ] Respuestas usan `Results.*` tipados
- [ ] Errores usan `ProblemDetails` (estándar RFC 7807)
- [ ] `AddExceptionHandler` global registrado
- [ ] Autenticación JWT con políticas de autorización por scope/permiso
- [ ] CORS configurado explícitamente (no AllowAnyOrigin en prod)
- [ ] Rate limiting en endpoints sensibles (login, creación, pagos)
- [ ] Response caching en endpoints de solo lectura
- [ ] OpenAPI disponible en development
- [ ] CancellationToken propagado a todas las operaciones async
- [ ] Paginación, filtrado, ordenamiento en endpoints de lista
- [ ] Health checks en `/health` para orquestadores

---

## Health Checks

```csharp
builder.Services.AddHealthChecks()
    .AddDbContextCheck<AppDbContext>()
    .AddUrlGroup(new Uri("https://api.stripe.com/health"), "Stripe")
    .AddRedis(redisConnectionString);

app.MapHealthChecks("/health", new HealthCheckOptions
{
    ResponseWriter = async (context, report) =>
    {
        var result = new
        {
            status = report.Status.ToString(),
            checks = report.Entries.Select(e => new
            {
                name = e.Key,
                status = e.Value.Status.ToString(),
                description = e.Value.Description
            })
        };

        context.Response.ContentType = "application/json";
        await context.Response.WriteAsJsonAsync(result);
    }
});
```
