---
name: aspnet-core
description: "Guía principal de desarrollo ASP.NET Core (.NET 9/10). Cubre pipeline HTTP, hosting, startup, middleware, configuración, DI en contexto web, entornos, static files, routing, y fundamentos del framework. Actívala para cualquier tarea ASP.NET Core: nuevos proyectos, configuración del pipeline, diagnóstico de errores, o migración desde versiones anteriores."
---

# ASP.NET Core — Guía Principal

Fundamentos del framework para aplicaciones web modernas en .NET 9/10. Esta skill se mantiene siempre en contexto para cualquier tarea ASP.NET.

---

## Pipeline HTTP

```
HTTP Request
    ↓
Web Server (Kestrel / IIS / nginx)
    ↓
Middleware 1 (Exception Handler)
    ↓
Middleware 2 (HSTS / HTTPS Redirection)
    ↓
Middleware 3 (Static Files)
    ↓
Middleware 4 (Routing)
    ↓
Middleware 5 (CORS)
    ↓
Middleware 6 (Authentication)
    ↓
Middleware 7 (Authorization)
    ↓
Endpoint (Minimal API, Controller, Razor Page, Blazor)
    ↓
Response (flow reverses through middleware)
```

### Orden correcto del pipeline

```csharp
var app = builder.Build();

// 1. Manejo de errores (primero para capturar todo)
if (app.Environment.IsDevelopment())
    app.UseDeveloperExceptionPage();
else
    app.UseExceptionHandler("/Error");

app.UseStatusCodePages();
app.UseHsts();               // 2. Seguridad de transporte

// 3. Redirección y archivos estáticos
app.UseHttpsRedirection();
app.UseStaticFiles();

// 4. Routing (antes de middleware que dependen de endpoints)
app.UseRouting();

// 5. CORS (después de routing, antes de auth)
app.UseCors();

// 6. Auth + AuthZ (después de routing, antes de endpoints)
app.UseAuthentication();
app.UseAuthorization();

// 7. Endpoints
app.MapRazorPages();
app.MapControllers();
app.MapDefaultControllerRoute();
app.MapBlazorHub();

app.Run();
```

---

## Hosting y Startup

### WebApplication (minimal hosting, .NET 6+)

```csharp
// ⚠️ .NET 10: WebHostBuilder / IWebHost obsoletos. Usar siempre WebApplication.
var builder = WebApplication.CreateBuilder(args);

// Configuración
builder.Configuration
    .AddJsonFile("appsettings.local.json", optional: true)
    .AddUserSecrets<Program>()
    .AddEnvironmentVariables()
    .AddAzureKeyVault(/* ... */);

// Servicios
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseSqlServer(builder.Configuration.GetConnectionString("Default")));

builder.Services.AddRazorPages();
builder.Services.AddControllersWithViews();
builder.Services.AddEndpointsApiExplorer();

// Middleware por entorno
var app = builder.Build();

if (app.Environment.IsDevelopment())
    app.UseDeveloperExceptionPage();
else
    app.UseExceptionHandler("/Error");

app.Run();
```

### Entornos

```csharp
// Detectar entorno
if (app.Environment.IsDevelopment()) { /* Swagger, hot reload, etc. */ }
if (app.Environment.IsStaging()) { /* Pre-producción */ }
if (app.Environment.IsProduction()) { /* Hardening completo */ }

// Archivos de configuración por entorno (se cargan automáticamente)
// appsettings.json          → base
// appsettings.Development.json → solo en Development
// appsettings.Production.json  → solo en Production
```

### Kestrel configuration

```csharp
builder.WebHost.ConfigureKestrel(options =>
{
    // Límites
    options.Limits.MaxRequestBodySize = 50 * 1024 * 1024; // 50 MB
    options.Limits.MaxRequestLineSize = 8 * 1024;
    options.Limits.MaxRequestHeadersTotalSize = 32 * 1024;
    options.Limits.MaxConcurrentConnections = 5000;
    options.Limits.MaxConcurrentUpgradedConnections = 100;
    options.Limits.KeepAliveTimeout = TimeSpan.FromMinutes(2);
    options.Limits.RequestHeadersTimeout = TimeSpan.FromSeconds(30);

    // Seguridad
    options.AddServerHeader = false;

    // Puertos y certificados
    options.Listen(IPAddress.Any, 5000);
    options.Listen(IPAddress.Any, 5001, listenOptions =>
    {
        listenOptions.UseHttps("certificate.pfx", "password");
    });
});
```

---

## Configuración

### Proveedores en orden de prioridad

1. Command-line arguments (`--Key=Value`)
2. Environment variables (`ASPNETCORE_ENVIRONMENT`, `Key__Nested`)
3. Azure Key Vault / AWS Secrets Manager
4. User Secrets (solo Development)
5. `appsettings.{Environment}.json`
6. `appsettings.json`
7. In-memory (`.AddInMemoryCollection()`)

```csharp
// Configuración tipada — siempre, nunca IConfiguration directo
public class SmtpOptions
{
    public const string SectionName = "Smtp";

    [Required]
    public string Host { get; init; } = string.Empty;

    [Range(1, 65535)]
    public int Port { get; init; } = 587;
}

builder.Services.Configure<SmtpOptions>(
    builder.Configuration.GetSection(SmtpOptions.SectionName));
```

### User Secrets (desarrollo)

```bash
dotnet user-secrets init
dotnet user-secrets set "Smtp:Password" "super-secret"

# Archivo almacenado en:
# %APPDATA%\Microsoft\UserSecrets\<UserSecretsId>\secrets.json (Windows)
# ~/.microsoft/usersecrets/<UserSecretsId>/secrets.json (Linux/Mac)
```

---

## DI en ASP.NET Core

### Registro de servicios framework

```csharp
// HttpContext accesor (solo si necesitas HttpContext fuera de un endpoint)
builder.Services.AddHttpContextAccessor();

// Para consumir desde cualquier servicio
public class UserContext(IHttpContextAccessor httpContextAccessor)
{
    public string? UserId =>
        httpContextAccessor.HttpContext?.User.FindFirstValue(ClaimTypes.NameIdentifier);
}
```

### Scoped services y DbContext

```csharp
// DbContext se registra como Scoped. Un DbContext por request HTTP.
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseSqlServer(connectionString));

// ⚠️ Nunca inyectar Scoped en Singleton
builder.Services.AddSingleton<ICacheService, MemoryCacheService>(); // ✅
builder.Services.AddSingleton<IBackgroundQueue, BackgroundQueue>(); // ✅

// ❌ Esto falla en runtime:
// services.AddSingleton<OrderService>(); // OrderService depende de AppDbContext (Scoped)
```

### Keyed Services (.NET 8+)

```csharp
// Útil para multi-tenant o multi-provider
builder.Services.AddKeyedScoped<IPaymentService, StripeService>("stripe");
builder.Services.AddKeyedScoped<IPaymentService, PayPalService>("paypal");

// Consumo en endpoint
app.MapPost("/pay", async (
    [FromKeyedServices("stripe")] IPaymentService payment) => { ... });
```

---

## Routing

### Convención vs atributos

```csharp
// Routing por convención (Razor Pages, MVC)
app.MapControllerRoute(
    name: "default",
    pattern: "{controller=Home}/{action=Index}/{id?}");

// Routing por atributo (Web API, Minimal API)
[Route("api/[controller]")]
public class OrdersController : ControllerBase { }

// Minimal API routing
app.MapGet("/api/orders/{id:guid}", handler);

// Route constraints
app.MapGet("/api/orders/{id:guid}", handler);       // GUID
app.MapGet("/api/orders/{date:datetime}", handler); // DateTime
app.MapGet("/api/files/{filename:minlength(1)}", handler); // Min length
app.MapGet("/api/products/{sku:regex(^[A-Z]{{3}}-\d{{4}}$)}", handler); // Regex
```

### Route groups (.NET 7+)

```csharp
var orders = app.MapGroup("/api/orders")
    .WithTags("Orders")
    .RequireAuthorization();

orders.MapGet("/", GetAllOrders);
orders.MapGet("/{id}", GetOrderById);
orders.MapPost("/", CreateOrder);
```

---

## Static Files

```csharp
// Servir archivos estáticos de wwwroot
app.UseStaticFiles();

// Con cache headers agresivos para assets versionados
app.UseStaticFiles(new StaticFileOptions
{
    OnPrepareResponse = ctx =>
    {
        if (ctx.File.Name.EndsWith(".js") || ctx.File.Name.EndsWith(".css"))
            ctx.Context.Response.Headers.Append(
                "Cache-Control", "public,max-age=31536000,immutable");
    }
});

// Múltiples directorios de static files
app.UseStaticFiles(); // wwwroot
app.UseStaticFiles(new StaticFileOptions
{
    FileProvider = new PhysicalFileProvider(
        Path.Combine(builder.Environment.ContentRootPath, "Uploads")),
    RequestPath = "/uploads"
});
```

---

## Request / Response

### Leer request

```csharp
// Body como objeto tipado (binding automático)
app.MapPost("/api/orders", async (CreateOrderRequest request, ...) =>
{
    // request ya está deserializado y validado
});

// Query string, headers, route values (binding por nombre)
app.MapGet("/api/orders", async (
    [FromQuery] string? status,
    [FromHeader(Name = "X-Tenant-Id")] string? tenantId,
    [FromRoute] Guid id, ...) => { ... });

// Form data (upload de archivos)
app.MapPost("/upload", async (IFormFile file, CancellationToken ct) =>
{
    var path = Path.Combine("uploads", file.FileName);
    await using var stream = File.Create(path);
    await file.CopyToAsync(stream, ct);
    return Results.Ok(new { path });
});
```

### Escribir response

```csharp
// Results.* — tipados y semánticos
Results.Ok(data);                              // 200
Results.Created($"/api/orders/{id}", data);    // 201
Results.NoContent();                           // 204
Results.BadRequest(new { error });             // 400
Results.NotFound();                            // 404
Results.Conflict(new { error });               // 409
Results.Problem("Server error");               // 500

// Content negotiation (en Controllers)
return Ok(data); // Serializa a JSON/XML según Accept header

// File download
return Results.File(stream, "application/pdf", "report.pdf");

// Redirect
return Results.Redirect("/login");
return Results.LocalRedirect("/dashboard"); // Solo URLs locales

// Streaming response
return Results.Ok(GetStreamingData(ct)); // IAsyncEnumerable<T>
```

---

## Entornos y health checks

```csharp
// Health checks con múltiples probes
builder.Services.AddHealthChecks()
    .AddDbContextCheck<AppDbContext>(tags: ["database"])
    .AddRedis(redisConnection, tags: ["cache"])
    .AddUrlGroup(new Uri("https://api.stripe.com/health"), "stripe", tags: ["external"]);

// Mapear health checks
app.MapHealthChecks("/health", new HealthCheckOptions
{
    ResponseWriter = UIResponseWriter.WriteHealthCheckUIResponse
});

// Liveness probe (solo verifica que la app corre)
app.MapHealthChecks("/health/live", new HealthCheckOptions
{
    Predicate = _ => false // No ejecuta ningún check
});

// Readiness probe (verifica dependencias)
app.MapHealthChecks("/health/ready", new HealthCheckOptions
{
    Predicate = check => check.Tags.Contains("database")
});
```

---

## Logging en ASP.NET Core

### Configuración de Serilog

```csharp
// Program.cs
builder.Host.UseSerilog((context, config) =>
{
    config.ReadFrom.Configuration(context.Configuration)
          .Enrich.FromLogContext()
          .Enrich.WithMachineName()
          .Enrich.WithEnvironmentName()
          .WriteTo.Console()
          .WriteTo.ApplicationInsights(
              connectionString: context.Configuration["AppInsights:ConnectionString"],
              TelemetryConverter.Traces);
});

// Enrichment de request
app.UseSerilogRequestLogging(options =>
{
    options.EnrichDiagnosticContext = (diagnosticContext, httpContext) =>
    {
        diagnosticContext.Set("RequestHost", httpContext.Request.Host.Value);
        diagnosticContext.Set("RequestScheme", httpContext.Request.Scheme);
        diagnosticContext.Set("RemoteIp", httpContext.Connection.RemoteIpAddress);
        diagnosticContext.Set("UserAgent", httpContext.Request.Headers.UserAgent);
    };

    options.GetLevel = (httpContext, elapsedMs, ex) =>
        ex is not null || httpContext.Response.StatusCode >= 500
            ? LogEventLevel.Error
            : httpContext.Response.StatusCode >= 400
                ? LogEventLevel.Warning
                : LogEventLevel.Information;
});
```

---

## Seguridad transversal

### Headers de seguridad (via middleware)

```csharp
app.Use(async (context, next) =>
{
    var headers = context.Response.Headers;

    headers["X-Content-Type-Options"] = "nosniff";
    headers["X-Frame-Options"] = "DENY";
    headers["X-XSS-Protection"] = "0";
    headers["Referrer-Policy"] = "strict-origin-when-cross-origin";
    headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()";

    await next();
});

// Usar librería para CSP y HSTS más fácil:
// NetEscapades.AspNetCore.SecurityHeaders
```

### Anti-forgery (CSRF)

```csharp
// Razor Pages y MVC lo tienen por defecto para POST
// No necesitas [ValidateAntiForgeryToken] explícito

// Para SPAs con tokens: configurar antiforgery
builder.Services.AddAntiforgery(options =>
{
    options.HeaderName = "X-CSRF-TOKEN";
    options.Cookie.Name = "XSRF-TOKEN";
    options.Cookie.HttpOnly = false; // Para que JS pueda leerlo
});
```

---

## Convenciones de proyecto ASP.NET

```
Solution.sln
├── src/
│   ├── MiApp.Web/                      # ASP.NET Core host
│   │   ├── Pages/                      # Razor Pages (si aplica)
│   │   ├── Views/                      # MVC Views (si aplica)
│   │   ├── Controllers/               # MVC / Web API Controllers (si aplica)
│   │   ├── Endpoints/                 # Minimal API endpoints
│   │   ├── Components/                # Blazor components (si aplica)
│   │   ├── Hubs/                      # SignalR hubs
│   │   ├── Middleware/
│   │   ├── Filters/
│   │   ├── wwwroot/                   # Static files
│   │   │   ├── css/
│   │   │   ├── js/
│   │   │   └── images/
│   │   ├── Program.cs
│   │   └── appsettings.json
│   ├── MiApp.Application/             # Lógica de negocio
│   ├── MiApp.Domain/                  # Entidades y reglas
│   └── MiApp.Infrastructure/          # EF Core, servicios externos
```

---

## Sub-skills del kit

> 📁 Cada sub-skill tiene su guía detallada en `./{nombre}/GUIDE.md`. Usa `read` para cargarla cuando el tema lo requiera.


| Skill                       | Cuándo cargarla                                |
|-----------------------------|------------------------------------------------|
| `aspnet-mvc`                | Controllers, Views, Tag Helpers, Layouts       |
| `aspnet-web-api`            | REST APIs con Controllers y Minimal APIs, AddValidation(), OpenAPI 3.1/YAML |
| `aspnet-razor-pages`        | Razor Pages, PageModel, handlers               |
| `aspnet-blazor`             | Blazor Server, WASM, Hybrid, WASM preloading    |
| `aspnet-identity`           | AuthN/AuthZ, Identity, JWT, OAuth              |
| `aspnet-ef-core`            | EF Core en contexto web (scoped, migraciones)  |
| `aspnet-signalr`            | Hubs, streaming, backplane Redis               |
| `aspnet-middleware`         | Custom middleware, filters, model binding      |
| `aspnet-testing`            | WebApplicationFactory, E2E, Playwright         |
| `aspnet-performance`        | Caching, compression, CDN, bundling            |
| `aspnet-deployment`         | IIS, Docker, Azure, nginx, CI/CD               |

---

## Checklist de proyecto nuevo

- [ ] `WebApplication.CreateBuilder(args)` como entry point
- [ ] HTTPS configurado (`UseHttpsRedirection`, `UseHsts`)
- [ ] Security headers via middleware
- [ ] Serilog configurado (o al menos `builder.Host.UseSerilog()`)
- [ ] Configuración tipada con `IOptions<T>` + `ValidateOnStart()`
- [ ] DbContext registrado como Scoped con resiliencia
- [ ] Health checks en `/health`, `/health/live`, `/health/ready`
- [ ] Exception handler global (`IExceptionHandler` o `UseExceptionHandler`)
- [ ] CORS con orígenes explícitos
- [ ] Static files con cache headers en producción
- [ ] Anti-forgery configurado para Razor Pages / MVC
- [ ] `AddServerHeader = false` en Kestrel
- [ ] Rate limiting en endpoints sensibles
- [ ] Response compression habilitada
