---
name: dotnet-security
description: Seguridad en aplicaciones .NET 9/10. Cubre autenticación (JWT, OAuth2/OIDC, Identity), autorización (RBAC, políticas, claims), protección de datos (Data Protection API, secretos, cifrado), headers de seguridad (CSP, HSTS, X-Content-Type-Options), OWASP Top 10 mitigado en .NET, y hardening de configuración. Actívala al implementar auth, revisar vulnerabilidades, o configurar seguridad en APIs y aplicaciones web.
disable-model-invocation: true
---

# Seguridad en .NET

Guía de seguridad para aplicaciones .NET modernas. Cubre autenticación, autorización, protección de datos, hardening y mitigación del OWASP Top 10.

---

## Autenticación

### JWT Bearer con OAuth2 / OIDC

```csharp
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.Authority = builder.Configuration["Auth:Authority"];
        options.Audience = builder.Configuration["Auth:Audience"];
        options.RequireHttpsMetadata = !builder.Environment.IsDevelopment();

        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateLifetime = true,
            ValidateIssuerSigningKey = true,
            ClockSkew = TimeSpan.FromSeconds(30),
            ValidIssuer = builder.Configuration["Auth:Issuer"],
            ValidAudience = builder.Configuration["Auth:Audience"]
        };

        // Mapear claims de OIDC a roles de la app
        options.Events = new JwtBearerEvents
        {
            OnTokenValidated = context =>
            {
                // Ej: mapear "realm_access.roles" de Keycloak
                var claimsIdentity = (ClaimsIdentity)context.Principal!.Identity!;

                if (context.Principal.HasClaim(c => c.Type == "realm_access"))
                {
                    var realmAccess = context.Principal.FindFirst("realm_access")?.Value;
                    // Parse JSON y agregar claims de rol
                }

                return Task.CompletedTask;
            }
        };
    });

// Forzar autenticación globally (o por endpoint/group)
builder.Services.AddAuthorization();
app.UseAuthentication();
app.UseAuthorization();
```

### ASP.NET Core Identity

```csharp
builder.Services.AddDbContext<AppIdentityDbContext>(options =>
    options.UseSqlServer(connectionString));

builder.Services.AddIdentity<ApplicationUser, IdentityRole>(options =>
{
    // Password policy
    options.Password.RequiredLength = 12;
    options.Password.RequireDigit = true;
    options.Password.RequireLowercase = true;
    options.Password.RequireUppercase = true;
    options.Password.RequireNonAlphanumeric = true;
    options.Password.RequiredUniqueChars = 3;

    // Lockout
    options.Lockout.DefaultLockoutTimeSpan = TimeSpan.FromMinutes(15);
    options.Lockout.MaxFailedAccessAttempts = 5;
    options.Lockout.AllowedForNewUsers = true;

    // User
    options.User.RequireUniqueEmail = true;
})
.AddEntityFrameworkStores<AppIdentityDbContext>()
.AddDefaultTokenProviders();

// Configurar cookies seguras
builder.Services.ConfigureApplicationCookie(options =>
{
    options.Cookie.HttpOnly = true;
    options.Cookie.SecurePolicy = CookieSecurePolicy.Always;
    options.Cookie.SameSite = SameSiteMode.Strict;
    options.ExpireTimeSpan = TimeSpan.FromHours(1);
    options.SlidingExpiration = true;
});
```

### API Keys para servicios internos

```csharp
public static class ApiKeyValidation
{
    public static void AddApiKeyAuthentication(this IServiceCollection services)
    {
        services.AddAuthentication()
            .AddScheme<ApiKeyAuthenticationOptions, ApiKeyAuthHandler>(
                ApiKeyAuthHandler.SchemeName, null);
    }
}

public class ApiKeyAuthenticationOptions : AuthenticationSchemeOptions
{
    public const string DefaultHeader = "X-Api-Key";
}

public class ApiKeyAuthHandler(
    IOptionsMonitor<ApiKeyAuthenticationOptions> options,
    ILoggerFactory logger,
    UrlEncoder encoder) : AuthenticationHandler<ApiKeyAuthenticationOptions>(options, logger, encoder)
{
    public const string SchemeName = "ApiKey";

    protected override Task<AuthenticateResult> HandleAuthenticateAsync()
    {
        if (!Request.Headers.TryGetValue(ApiKeyAuthenticationOptions.DefaultHeader, out var apiKey))
            return Task.FromResult(AuthenticateResult.NoResult());

        // ⚠️ Validar contra almacenamiento seguro (Secret Manager, Key Vault, BD con hash)
        // NUNCA hardcodear keys
        var configuredKey = Context.RequestServices
            .GetRequiredService<IOptions<ApiKeysOptions>>().Value.ApiKey;

        if (!CryptographicOperations.FixedTimeEquals(
                Encoding.UTF8.GetBytes(apiKey!),
                Encoding.UTF8.GetBytes(configuredKey)))
        {
            return Task.FromResult(AuthenticateResult.Fail("Invalid API Key"));
        }

        var claims = new[] { new Claim(ClaimTypes.Name, "API Service") };
        var identity = new ClaimsIdentity(claims, SchemeName);
        return Task.FromResult(
            AuthenticateResult.Success(new AuthenticationTicket(
                new ClaimsPrincipal(identity), SchemeName)));
    }
}
```

**⚠️ Comparar API keys con `CryptographicOperations.FixedTimeEquals`** — evita timing attacks.

---

## Autorización

### Políticas basadas en claims

```csharp
builder.Services.AddAuthorization(options =>
{
    options.AddPolicy("admin", policy =>
        policy.RequireRole("Admin"));

    options.AddPolicy("orders:read", policy =>
        policy.RequireClaim("permissions", "orders:read"));

    options.AddPolicy("orders:create", policy =>
        policy.RequireClaim("permissions", "orders:create"));

    // Combinación
    options.AddPolicy("orders:manage", policy =>
        policy.RequireAssertion(context =>
            context.User.HasClaim("permissions", "orders:admin") ||
            (context.User.HasClaim("permissions", "orders:create") &&
             context.User.HasClaim("permissions", "orders:read"))));
});

// Uso
app.MapPost("/api/orders", handler).RequireAuthorization("orders:create");
```

### Resource-based authorization

```csharp
public class OrderOwnerAuthorizationHandler
    : AuthorizationHandler<OperationAuthorizationRequirement, Order>
{
    protected override Task HandleRequirementAsync(
        AuthorizationHandlerContext context,
        OperationAuthorizationRequirement requirement,
        Order resource)
    {
        var userId = context.User.FindFirst(ClaimTypes.NameIdentifier)?.Value;

        if (resource.CustomerId == userId || context.User.IsInRole("Admin"))
            context.Succeed(requirement);

        return Task.CompletedTask;
    }
}

// Uso en endpoint
var authResult = await _authService.AuthorizeAsync(User, order, "Cancel");
if (!authResult.Succeeded)
    return Results.Forbid();
```

---

## Protección de datos

### Data Protection API (DPAPI)

```csharp
// Configurar DPAPI con persistencia y protección
builder.Services.AddDataProtection()
    .PersistKeysToAzureBlobStorage(new Uri(blobSasUri))
    .ProtectKeysWithAzureKeyVault(keyUri, new DefaultAzureCredential())
    .SetApplicationName("MiApp");

// Uso
public class TokenService(IDataProtectionProvider provider)
{
    private readonly IDataProtector _protector =
        provider.CreateProtector("PasswordResetToken");

    public string GenerateToken(string userId)
    {
        // El token expira en 1 hora vía propósito limitado en el tiempo
        var timeLimited = _protector.ToTimeLimitedDataProtector();
        return timeLimited.Protect(userId, TimeSpan.FromHours(1));
    }

    public string? ValidateToken(string token)
    {
        try
        {
            var timeLimited = _protector.ToTimeLimitedDataProtector();
            return timeLimited.Unprotect(token);
        }
        catch (CryptographicException)
        {
            return null;
        }
    }
}
```

### Cifrado de campos sensibles en BD

```csharp
// EF Core Value Converter con cifrado
public class EncryptedStringConverter(
    IDataProtector protector) : ValueConverter<string, string>
{
    public EncryptedStringConverter()
        : base(
            v => protector.Protect(v),    // Guardar cifrado
            v => protector.Unprotect(v))  // Leer descifrado
    { }
}

// Config EF Core
builder.Entity<Customer>()
    .Property(c => c.TaxId)
    .HasConversion<EncryptedStringConverter>();
```

---

## Secretos y configuración sensible

### Jerarquía de secretos

```csharp
// 1. Desarrollo local: User Secrets
// dotnet user-secrets set "Stripe:ApiKey" "sk_test_..."
// El valor NO se commitea (.csproj tiene <UserSecretsId>)

// 2. Producción: Azure Key Vault / AWS Secrets Manager
builder.Configuration.AddAzureKeyVault(
    new Uri("https://miapp-vault.vault.azure.net/"),
    new DefaultAzureCredential());

// 3. Variables de entorno (convención __ para jerarquía)
// Stripe__ApiKey=sk_live_...
// ConnectionStrings__Default=Server=...

// 4. appsettings.json — NUNCA valores secretos aquí
// Solo config no sensible y placeholders
```

### Validar secretos al inicio

```csharp
services.AddOptions<StripeOptions>()
    .Bind(configuration.GetSection("Stripe"))
    .ValidateDataAnnotations()
    .ValidateOnStart(); // ← Lanza si falta o es inválido. La app no arranca.
```

---

## Headers de seguridad HTTP

```csharp
// Middleware custom o usar NetEscapades.AspNetCore.SecurityHeaders
app.Use(async (context, next) =>
{
    var headers = context.Response.Headers;

    // HSTS (solo HTTPS en producción)
    headers.Append("Strict-Transport-Security", "max-age=31536000; includeSubDomains; preload");

    // Previene MIME sniffing
    headers.Append("X-Content-Type-Options", "nosniff");

    // Previene clickjacking
    headers.Append("X-Frame-Options", "DENY");

    // XSS protection (legacy, pero no daña)
    headers.Append("X-XSS-Protection", "0");

    // Referrer Policy
    headers.Append("Referrer-Policy", "strict-origin-when-cross-origin");

    // Permissions Policy
    headers.Append("Permissions-Policy", "camera=(), microphone=(), geolocation=()");

    await next();
});

// Content-Security-Policy (la más compleja)
headers.Append("Content-Security-Policy",
    "default-src 'self'; " +
    "script-src 'self' https://cdn.miapp.com; " +
    "style-src 'self' 'unsafe-inline'; " +
    "img-src 'self' data: https:; " +
    "font-src 'self'; " +
    "frame-ancestors 'none'; " +
    "form-action 'self';");
```

---

## OWASP Top 10 mitigado en .NET

### A01: Broken Access Control

```csharp
// ❌ Validación solo en frontend, sin autorización en backend
app.MapGet("/api/orders/{id}", async (Guid id, AppDbContext db) =>
{
    return await db.Orders.FindAsync(id);
}); // ¡Cualquier usuario autenticado ve cualquier orden!

// ✅ Autorización en backend
app.MapGet("/api/orders/{id}", async (
    Guid id,
    AppDbContext db,
    IAuthorizationService auth,
    ClaimsPrincipal user,
    CancellationToken ct) =>
{
    var order = await db.Orders.FindAsync([id], ct);
    if (order is null) return Results.NotFound();

    var result = await auth.AuthorizeAsync(user, order, "Read");
    if (!result.Succeeded) return Results.Forbid();

    return Results.Ok(order);
}).RequireAuthorization();
```

### A02: Cryptographic Failures

```csharp
// ✅ Siempre HTTPS
app.UseHttpsRedirection();
app.UseHsts();

// ✅ Cifrar cookies sensibles
options.Cookie.SecurePolicy = CookieSecurePolicy.Always;
options.Cookie.HttpOnly = true;
options.Cookie.SameSite = SameSiteMode.Strict;

// ✅ Hashear passwords con Identity (PBKDF2 por defecto)
// Identity ya usa PasswordHasher<TUser> con PBKDF2-SHA256
// Nunca SHA1, MD5, o custom crypto
```

### A03: Injection

```csharp
// ✅ EF Core parametriza automáticamente
var order = await db.Orders.FirstOrDefaultAsync(o => o.Id == id, ct);
// SQL: SELECT * FROM Orders WHERE Id = @p0  ← parametrizado

// ✅ Raw SQL parametrizado
var orders = await db.Orders
    .FromSql($"SELECT * FROM Orders WHERE CustomerId = {customerId}")
    .ToListAsync(ct);
// La interpolación parametriza automáticamente

// ❌ Concatenación manual
var sql = $"SELECT * FROM Orders WHERE CustomerId = '{customerId}'"; // SQL Injection

// ✅ LDAP / DirectoryServices
// Nunca concatenar filtros: usar clases tipadas o Encoding
```

### A04: Insecure Design

```csharp
// ✅ Rate limiting previene brute force
builder.Services.AddRateLimiter(...);

// ✅ Account lockout
options.Lockout.MaxFailedAccessAttempts = 5;

// ✅ Sesiones expiran
options.ExpireTimeSpan = TimeSpan.FromHours(1);
```

### A05: Security Misconfiguration

```csharp
// ✅ Quitar headers de servidor
builder.WebHost.ConfigureKestrel(options =>
{
    options.AddServerHeader = false; // Quita "Server: Kestrel"
});

// ✅ Error details solo en development
if (app.Environment.IsDevelopment())
    app.UseDeveloperExceptionPage();
else
    app.UseExceptionHandler(); // Sin stack traces al cliente

// ✅ No exponer Swagger/OpenAPI en producción
if (app.Environment.IsDevelopment())
    app.MapOpenApi();
```

### A06: Vulnerable Components

```bash
# Auditar paquetes con vulnerabilidades conocidas
dotnet list package --vulnerable

# Actualizar paquetes
dotnet list package --outdated
dotnet outdated --upgrade

# CI: fallar build si hay vulnerabilidades críticas
dotnet list package --vulnerable 2>&1 | tee vuln.log
if grep -q "Critical" vuln.log; then exit 1; fi
```

### A07: Auth Failures

- Identidad ya cubierta en [Autenticación](#autenticación)
- `ValidateLifetime = true` siempre
- JWT con expiración corta (15-60 min) + refresh tokens

### A08: Software & Data Integrity

```csharp
// ✅ Verificar hash de archivos descargados
// ✅ NuGet package signing (aceptado por defecto en .NET)
// ✅ Deserialización segura
```

### A09: Logging & Monitoring Failures

```csharp
// ✅ Loggear eventos de seguridad
_logger.LogInformation("User {UserId} logged in from IP {IpAddress}", userId, ip);
_logger.LogWarning("Failed login attempt for user {UserId}", userId);
_logger.LogCritical("Admin action: {Action} by {UserId}", action, userId);

// ❌ NUNCA loggear datos sensibles
_logger.LogInformation("User {Email} with password {Password}", email, password); // NO
_logger.LogInformation("Credit card: {CardNumber}", cardNumber); // NO

// ✅ Redactar datos sensibles al loggear
_logger.LogInformation("Payment processed for card ending in {LastFour}", cardNumber[^4..]);
```

### A10: SSRF (Server-Side Request Forgery)

```csharp
// ❌ HttpClient que sigue redirects a URLs de usuario
var url = request.Url; // input del usuario
var response = await _httpClient.GetAsync(url); // SSRF

// ✅ Validar y restringir URLs
public static bool IsSafeUrl(string url)
{
    if (!Uri.TryCreate(url, UriKind.Absolute, out var uri))
        return false;

    // Solo HTTP/HTTPS
    if (uri.Scheme != "https" && uri.Scheme != "http")
        return false;

    // Bloquear IPs privadas
    var host = uri.Host;
    if (host == "localhost" || host == "127.0.0.1" || host.StartsWith("192.168."))
        return false;

    // Whitelist de dominios
    return _allowedDomains.Any(d => host.EndsWith(d));
}

// ✅ Timeout obligatorio en HttpClient
_httpClient.Timeout = TimeSpan.FromSeconds(10);
```

---

## Hardening de Kestrel

```csharp
builder.WebHost.ConfigureKestrel(options =>
{
    options.Limits.MaxRequestBodySize = 10 * 1024 * 1024; // 10 MB
    options.Limits.MaxRequestLineSize = 8 * 1024; // 8 KB
    options.Limits.MaxRequestHeadersTotalSize = 32 * 1024; // 32 KB
    options.Limits.MaxConcurrentConnections = 1000;
    options.Limits.MaxConcurrentUpgradedConnections = 100;
    options.Limits.KeepAliveTimeout = TimeSpan.FromMinutes(2);
    options.Limits.RequestHeadersTimeout = TimeSpan.FromSeconds(30);

    options.AddServerHeader = false;
    options.AllowSynchronousIO = false; // Default en .NET 6+
});
```

---

## Anti-patterns de seguridad

| Anti-patrón | Corrección |
|-------------|------------|
| `AllowAnyOrigin()` en CORS | Whitelist explícita de orígenes |
| Swagger en producción | Solo development |
| Stack traces al cliente | `UseExceptionHandler()` |
| Secretos en `appsettings.json` | User Secrets (dev) / Key Vault (prod) |
| Hardcodear API keys | Configuración + `IOptions<T>` |
| `[AllowAnonymous]` en todo el controller | Solo en endpoints públicos |
| Comparar strings con `==` para auth | `CryptographicOperations.FixedTimeEquals` |
| IDs incrementales expuestos en URLs | GUIDs o IDs no predecibles |
| Confiar en validación del frontend | Validar siempre en backend |

---

## Checklist de seguridad

- [ ] HTTPS forzado (`UseHttpsRedirection` + `UseHsts`)
- [ ] Headers de seguridad configurados (HSTS, CSP, X-Frame-Options, X-Content-Type-Options)
- [ ] Autenticación JWT con `ValidateLifetime=true`
- [ ] Autorización por claims/políticas, no solo `[Authorize]` vacío
- [ ] Rate limiting en login, registro, y endpoints críticos
- [ ] Account lockout configurado
- [ ] Cookies `HttpOnly`, `Secure`, `SameSite=Strict`
- [ ] DPAPI con persistencia en producción (no en memoria)
- [ ] Secretos en Key Vault / Secrets Manager, nunca en código
- [ ] `ValidateOnStart()` para configuración requerida
- [ ] Sin stack traces en producción
- [ ] Sin Swagger/OpenAPI en producción
- [ ] CORS con orígenes explícitos, no `AllowAnyOrigin`
- [ ] `dotnet list package --vulnerable` en CI
- [ ] `CryptographicOperations.FixedTimeEquals` para comparar tokens/secrets
- [ ] Logs no contienen PII (emails completos, passwords, credit cards)
- [ ] Input validation en backend, no solo frontend
- [ ] Kestrel limits configurados (body size, timeouts, headers)
- [ ] `AddServerHeader = false`
