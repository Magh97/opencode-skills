---
name: aspnet-middleware
description: Middleware, Filters, y Model Binding en ASP.NET Core. Cubre creación de middleware custom, filtros (Authorization, Resource, Action, Exception, Result), IEndpointFilter para Minimal APIs, model binding custom, validation, y pipeline HTTP en profundidad. Actívala al crear middleware reutilizable, implementar filtros cross-cutting, o extender el pipeline HTTP.
disable-model-invocation: true
---

# Middleware, Filters, y Model Binding

Guía completa para extender el pipeline HTTP de ASP.NET Core con middleware, filtros y model binders custom.

---

## Middleware

### Middleware como clase (reutilizable)

```csharp
public class RequestLoggingMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<RequestLoggingMiddleware> _logger;

    public RequestLoggingMiddleware(RequestDelegate next, ILogger<RequestLoggingMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        var stopwatch = Stopwatch.StartNew();

        try
        {
            await _next(context);
        }
        finally
        {
            stopwatch.Stop();

            _logger.LogInformation(
                "{Method} {Path} responded {StatusCode} in {ElapsedMs}ms",
                context.Request.Method,
                context.Request.Path,
                context.Response.StatusCode,
                stopwatch.ElapsedMilliseconds);
        }
    }
}

// Extension method para registro limpio
public static class RequestLoggingMiddlewareExtensions
{
    public static IApplicationBuilder UseRequestLogging(this IApplicationBuilder builder)
        => builder.UseMiddleware<RequestLoggingMiddleware>();
}

// Program.cs
app.UseRequestLogging();
```

### Middleware inline (para lógica simple)

```csharp
app.Use(async (context, next) =>
{
    // Pre-procesamiento
    var tenantId = context.Request.Headers["X-Tenant-Id"].FirstOrDefault();
    context.Items["TenantId"] = tenantId;

    await next(context);
});
```

### Middleware de excepción global

```csharp
app.UseExceptionHandler(errorApp =>
{
    errorApp.Run(async context =>
    {
        var exception = context.Features.Get<IExceptionHandlerFeature>()?.Error;
        var statusCode = exception switch
        {
            NotFoundException => 404,
            ValidationException => 400,
            UnauthorizedAccessException => 403,
            _ => 500
        };

        context.Response.StatusCode = statusCode;
        context.Response.ContentType = "application/json";

        await context.Response.WriteAsJsonAsync(new
        {
            error = exception?.Message ?? "Internal server error",
            statusCode
        });
    });
});
```

### Rama condicional del pipeline (Map/MapWhen)

```csharp
// Rama basada en path
app.Map("/admin", adminApp =>
{
    adminApp.UseAuthentication();
    adminApp.UseAuthorization();
    adminApp.MapRazorPages();
});

// Rama basada en condición
app.MapWhen(context =>
    context.Request.Headers.ContainsKey("X-API-Version"), apiApp =>
{
    apiApp.UseRouting();
    apiApp.UseEndpoints(endpoints => endpoints.MapControllers());
});
```

---

## Filtros en MVC / Controllers

### Action Filter

```csharp
public class LogActionFilter : IAsyncActionFilter
{
    private readonly ILogger<LogActionFilter> _logger;

    public LogActionFilter(ILogger<LogActionFilter> logger) => _logger = logger;

    public async Task OnActionExecutionAsync(
        ActionExecutingContext context,
        ActionExecutionDelegate next)
    {
        _logger.LogInformation("Executing {Action} with args {@Arguments}",
            context.ActionDescriptor.DisplayName,
            context.ActionArguments);

        var resultContext = await next();

        _logger.LogInformation("Executed {Action}",
            context.ActionDescriptor.DisplayName);
    }
}

// Registrar como servicio (para usar DI)
builder.Services.AddScoped<LogActionFilter>();

// Aplicar globalmente
builder.Services.AddControllersWithViews(options =>
{
    options.Filters.Add<LogActionFilter>();
});

// O en un controller/action específico
[ServiceFilter(typeof(LogActionFilter))]
public IActionResult Index() => View();
```

### Exception Filter

```csharp
public class DomainExceptionFilter : IAsyncExceptionFilter
{
    private readonly ILogger<DomainExceptionFilter> _logger;

    public DomainExceptionFilter(ILogger<DomainExceptionFilter> logger) => _logger = logger;

    public Task OnExceptionAsync(ExceptionContext context)
    {
        if (context.Exception is not DomainException domainEx)
            return Task.CompletedTask;

        context.Result = new ObjectResult(new ProblemDetails
        {
            Title = "Business Rule Violation",
            Detail = domainEx.Message,
            Status = StatusCodes.Status422UnprocessableEntity
        })
        {
            StatusCode = StatusCodes.Status422UnprocessableEntity
        };

        context.ExceptionHandled = true;
        return Task.CompletedTask;
    }
}
```

### Authorization Filter

```csharp
public class RequireTenantHeaderFilter : IAsyncAuthorizationFilter
{
    public async Task OnAuthorizationAsync(AuthorizationFilterContext context)
    {
        var tenantId = context.HttpContext.Request.Headers["X-Tenant-Id"].FirstOrDefault();
        if (string.IsNullOrEmpty(tenantId))
        {
            context.Result = new BadRequestObjectResult(new
            {
                error = "X-Tenant-Id header is required"
            });
            return;
        }

        // Validar tenant existe
        var tenantService = context.HttpContext.RequestServices
            .GetRequiredService<ITenantService>();

        if (!await tenantService.ExistsAsync(tenantId))
        {
            context.Result = new NotFoundObjectResult(new
            {
                error = $"Tenant {tenantId} not found"
            });
        }
    }
}
```

### Resource Filter

```csharp
public class ResponseTimeFilter : IAsyncResourceFilter
{
    public async Task OnResourceExecutionAsync(
        ResourceExecutingContext context,
        ResourceExecutionDelegate next)
    {
        var stopwatch = Stopwatch.StartNew();

        var executed = await next();

        stopwatch.Stop();
        context.HttpContext.Response.Headers["X-Response-Time-Ms"] =
            stopwatch.ElapsedMilliseconds.ToString();
    }
}
```

---

## IEndpointFilter (Minimal APIs)

Equivalente a filtros de MVC pero para Minimal APIs.

```csharp
public class AuditEndpointFilter : IEndpointFilter
{
    private readonly ILogger<AuditEndpointFilter> _logger;

    public AuditEndpointFilter(ILogger<AuditEndpointFilter> logger) => _logger = logger;

    public async ValueTask<object?> InvokeAsync(
        EndpointFilterInvocationContext context,
        EndpointFilterDelegate next)
    {
        var endpoint = context.HttpContext.GetEndpoint()?.DisplayName;
        _logger.LogInformation("Calling {Endpoint}", endpoint);

        var result = await next(context);

        _logger.LogInformation("Completed {Endpoint}", endpoint);
        return result;
    }
}

// Registrar para DI
builder.Services.AddScoped<AuditEndpointFilter>();

// Aplicar a endpoint
app.MapGet("/api/orders/{id}", handler)
    .AddEndpointFilter<AuditEndpointFilter>();

// Aplicar a grupo
var orders = app.MapGroup("/api/orders")
    .AddEndpointFilter<AuditEndpointFilter>();

// Filtro inline (para lógica simple)
app.MapPost("/api/orders", handler)
    .AddEndpointFilter(async (context, next) =>
    {
        var stopwatch = Stopwatch.StartNew();
        var result = await next(context);
        stopwatch.Stop();

        Console.WriteLine($"Request took {stopwatch.ElapsedMilliseconds}ms");
        return result;
    });
```

### Validation Filter reutilizable

```csharp
public class ValidationFilter<T> : IEndpointFilter where T : class
{
    public async ValueTask<object?> InvokeAsync(
        EndpointFilterInvocationContext context,
        EndpointFilterDelegate next)
    {
        var validator = context.HttpContext.RequestServices
            .GetRequiredService<IValidator<T>>();

        var argument = context.Arguments.OfType<T>().FirstOrDefault();
        if (argument is null)
            return Results.BadRequest("Invalid request");

        var result = await validator.ValidateAsync(argument);
        if (!result.IsValid)
            return Results.ValidationProblem(result.ToDictionary());

        return await next(context);
    }
}

public static class ValidationFilterExtensions
{
    public static RouteHandlerBuilder Validate<T>(this RouteHandlerBuilder builder) where T : class
    {
        builder.AddEndpointFilter<ValidationFilter<T>>();
        return builder;
    }
}

// Uso
app.MapPost("/api/orders", handler).Validate<CreateOrderRequest>();
```

---

## Model Binding

### Model Binder custom

```csharp
// Binder que parsea IDs encriptados
public class EncryptedIdModelBinder : IModelBinder
{
    private readonly IDataProtector _protector;

    public EncryptedIdModelBinder(IDataProtector protector) => _protector = protector;

    public Task BindModelAsync(ModelBindingContext bindingContext)
    {
        var valueProviderResult = bindingContext.ValueProvider
            .GetValue(bindingContext.ModelName);

        if (valueProviderResult == ValueProviderResult.None)
            return Task.CompletedTask;

        bindingContext.ModelState.SetModelValue(
            bindingContext.ModelName, valueProviderResult);

        var encryptedValue = valueProviderResult.FirstValue;
        if (string.IsNullOrEmpty(encryptedValue))
            return Task.CompletedTask;

        try
        {
            var decrypted = _protector.Unprotect(encryptedValue);
            if (Guid.TryParse(decrypted, out var guid))
                bindingContext.Result = ModelBindingResult.Success(guid);
        }
        catch (CryptographicException)
        {
            bindingContext.ModelState.TryAddModelError(
                bindingContext.ModelName, "Invalid encrypted ID");
        }

        return Task.CompletedTask;
    }
}

// Model Binder Provider
public class EncryptedIdModelBinderProvider : IModelBinderProvider
{
    public IModelBinder? GetBinder(ModelBinderProviderContext context)
    {
        if (context.Metadata.ModelType == typeof(Guid) &&
            context.BindingInfo.BindingSource == BindingSource.Query)
        {
            return new BinderTypeModelBinder(typeof(EncryptedIdModelBinder));
        }

        return null;
    }
}

// Registrar
builder.Services.AddControllersWithViews(options =>
{
    options.ModelBinderProviders.Insert(0, new EncryptedIdModelBinderProvider());
});
```

### Binding en Minimal API

```csharp
// Parámetros compuestos (AsParameters)
app.MapGet("/api/orders", async ([AsParameters] OrderSearchParams search, ...) =>
{
    // search contiene Status, CustomerId, Page, PageSize
});

public record OrderSearchParams(
    string? Status,
    string? CustomerId,
    int Page = 1,
    int PageSize = 20);

// Binding de source específico
app.MapPost("/api/orders", async (
    [FromBody] CreateOrderRequest body,
    [FromHeader(Name = "X-Idempotency-Key")] string? idempotencyKey,
    [FromQuery] bool dryRun = false,
    CancellationToken ct) =>
{
    // ...
});

// Binding de IFormFileCollection
app.MapPost("/upload", async (IFormFileCollection files, CancellationToken ct) =>
{
    foreach (var file in files)
    {
        await using var stream = File.Create(Path.Combine("uploads", file.FileName));
        await file.CopyToAsync(stream, ct);
    }
});
```

---

## Short-circuit middleware

```csharp
// Middleware que corta el pipeline sin llamar al siguiente
app.UseWhen(context => context.Request.Path == "/health", appBuilder =>
{
    appBuilder.Run(async context =>
    {
        context.Response.StatusCode = 200;
        await context.Response.WriteAsync("Healthy");
    });
});

// En Minimal API: short-circuit nativo (.NET 8+)
app.MapGet("/health", () => Results.Ok("Healthy"))
    .ShortCircuit(); // No pasa por el resto del middleware
```

---

## Combinación de filtros y middleware

```
Request
    ↓
Middleware 1 (ej: Logging) → llaman a next()
    ↓
Middleware 2 (ej: Auth) → llaman a next()
    ↓
Routing
    ↓
Endpoint Filter 1 (IEndpointFilter)
    ↓
Endpoint Filter 2 (ValidationFilter)
    ↓
Endpoint Handler → Response
    ↑ (los filtros se ejecutan en reversa)
Endpoint Filter 2 (post-handler)
    ↑
Endpoint Filter 1 (post-handler)
    ↑
Middleware 2 (post-next)
    ↑
Middleware 1 (post-next)
```

### Cuándo usar middleware vs filtro

| Criterio | Middleware | Filter (MVC/Minimal) |
|----------|-----------|----------------------|
| Alcance | Toda la app / rama | Controller/endpoint específico |
| Acceso a routing | No (antes de routing) | Sí (después de routing) |
| Acceso a ModelState | No | Sí |
| Short-circuit | Sí (no llama a next) | Sí (devuelve result) |
| Modificar request | Sí (reescribir path, headers) | No recomendado |
| Ejemplo | Logging, CORS, Auth | Validación, caching, excepciones de dominio |

---

## Middleware de compresión

```csharp
builder.Services.AddResponseCompression(options =>
{
    options.EnableForHttps = true;
    options.Providers.Add<BrotliCompressionProvider>();
    options.Providers.Add<GzipCompressionProvider>();
    options.MimeTypes = ResponseCompressionDefaults.MimeTypes.Concat(
        ["application/json", "text/html", "text/css", "application/javascript"]);
});

builder.Services.Configure<BrotliCompressionProviderOptions>(options =>
{
    options.Level = CompressionLevel.Fastest;
});

app.UseResponseCompression(); // TEMPRANO en el pipeline
```

---

## Checklist Middleware/Filters

- [ ] Middleware para concerns transversales (logging, CORS, auth)
- [ ] Filters para concerns de endpoint (validación, caching, excepción de dominio)
- [ ] IEndpointFilter en Minimal APIs para lógica pre/post handler
- [ ] Extension methods para registro limpio de middleware
- [ ] Middleware registrado en el orden correcto (ver `aspnet-core`)
- [ ] No lógica de negocio en middleware/filters — delegar a servicios
- [ ] Excepciones atrapadas en el middleware/filter correcto
- [ ] Model binders custom registrados como provider
- [ ] Response compression en el pipeline temprano
