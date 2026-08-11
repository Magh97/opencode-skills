---
name: dotnet-performance
description: Rendimiento y optimización en .NET 9/10. Cubre caching (HybridCache, IDistributedCache, InMemory), async/await avanzado (ValueTask, IAsyncEnumerable, Channel<T>), pooling (ArrayPool, ObjectPool), Span<T> y Memory<T>, benchmarks con BenchmarkDotNet, profiling, y optimización de EF Core y APIs. Actívala al optimizar endpoints lentos, reducir memoria, o configurar estrategias de caché.
disable-model-invocation: true
---

# Rendimiento y Optimización en .NET

Guía de alto rendimiento en .NET moderno. Menos GC pressure, menos allocations, más throughput.

---

## Caching

### HybridCache (.NET 9+ — recomendado)

```csharp
// Registro
builder.Services.AddHybridCache(options =>
{
    options.MaximumPayloadBytes = 1024 * 1024; // 1 MB
    options.DefaultEntryOptions = new HybridCacheEntryOptions
    {
        Expiration = TimeSpan.FromMinutes(5),
        LocalCacheExpiration = TimeSpan.FromMinutes(1)
    };
});

// Uso
public class ProductService(HybridCache cache, AppDbContext db)
{
    public async Task<ProductDto?> GetProductAsync(string sku, CancellationToken ct)
    {
        return await cache.GetOrCreateAsync(
            $"product:{sku}",
            async entry =>
            {
                // Solo se ejecuta si no está en caché
                var product = await db.Products
                    .AsNoTracking()
                    .FirstOrDefaultAsync(p => p.Sku == sku, ct);

                return product is null ? null : ProductDto.From(product);
            },
            cancellationToken: ct);
    }

    // Invalidar
    public async Task InvalidateProductCacheAsync(string sku, CancellationToken ct)
        => await cache.RemoveAsync($"product:{sku}", ct);
}
```

### IDistributedCache (Redis, SQL Server)

```csharp
// Redis
builder.Services.AddStackExchangeRedisCache(options =>
{
    options.Configuration = builder.Configuration.GetConnectionString("Redis");
    options.InstanceName = "MiApp:";
});

// Consumo
public class CartService(IDistributedCache cache)
{
    public async Task<Cart?> GetCartAsync(string userId, CancellationToken ct)
    {
        var json = await cache.GetStringAsync($"cart:{userId}", ct);
        return json is null ? null : JsonSerializer.Deserialize<Cart>(json);
    }

    public async Task SaveCartAsync(string userId, Cart cart, CancellationToken ct)
    {
        var json = JsonSerializer.Serialize(cart);
        await cache.SetStringAsync(
            $"cart:{userId}",
            json,
            new DistributedCacheEntryOptions
            {
                AbsoluteExpirationRelativeToNow = TimeSpan.FromHours(24),
                SlidingExpiration = TimeSpan.FromMinutes(30)
            },
            ct);
    }
}
```

### In-Memory Cache (IMemoryCache)

```csharp
// Para datos de referencia que cambian poco (catálogos, config)
builder.Services.AddMemoryCache();

public class LookupService(IMemoryCache cache, AppDbContext db)
{
    public async Task<List<Country>> GetCountriesAsync(CancellationToken ct)
    {
        return await cache.GetOrCreateAsync("countries", async entry =>
        {
            entry.AbsoluteExpirationRelativeToNow = TimeSpan.FromHours(24);
            entry.SetPriority(CacheItemPriority.NeverRemove);
            return await db.Countries.AsNoTracking().ToListAsync(ct);
        }) ?? [];
    }
}
```

### Response caching (nivel HTTP)

```csharp
// Cache de respuesta HTTP completa
app.MapGet("/api/products", handler)
    .CacheOutput(policy => policy
        .Expire(TimeSpan.FromMinutes(5))
        .SetVaryByQuery("category", "page"));

// Vary por header
.CacheOutput(policy => policy.SetVaryByHeader("Accept-Language"));
```

### Estrategia de caché por niveles

```
L1: In-Memory (HybridCache L1)       → microsegundos
L2: Redis (HybridCache L2)           → ~1ms
L3: Database                          → ~5-50ms
L4: External API                      → ~50-500ms
```

---

## Async/Await Avanzado

### ValueTask vs Task

```csharp
// ✅ ValueTask cuando el resultado suele ser síncrono
public ValueTask<Product?> GetProductAsync(string sku, CancellationToken ct)
{
    // 90% de los casos: cache hit (síncrono)
    if (_cache.TryGetValue(sku, out var product))
        return new ValueTask<Product?>(product);

    // 10%: cache miss (async)
    return new ValueTask<Product?>(GetFromDbAsync(sku, ct));
}
```

### IAsyncEnumerable<T> (streaming)

```csharp
// ✅ Streaming: procesar elementos uno a uno sin cargar todo en memoria
public async IAsyncEnumerable<OrderDto> GetOrdersStreaming(
    DateTime since,
    [EnumeratorCancellation] CancellationToken ct)
{
    await foreach (var order in _db.Orders
        .Where(o => o.CreatedAt > since)
        .AsNoTracking()
        .AsAsyncEnumerable()
        .WithCancellation(ct))
    {
        yield return OrderDto.From(order);
    }
}

// Endpoint que devuelve streaming
app.MapGet("/api/orders/stream", (DateTime since, AppDbContext db, CancellationToken ct) =>
{
    return Results.Ok(db.Orders
        .Where(o => o.CreatedAt > since)
        .AsNoTracking()
        .AsAsyncEnumerable());
});
```

### Channel<T> — Producer/Consumer

```csharp
// Productor
public async Task EnqueueOrdersAsync(IAsyncEnumerable<Order> orders, CancellationToken ct)
{
    await foreach (var order in orders.WithCancellation(ct))
        await _channel.Writer.WriteAsync(order, ct);

    _channel.Writer.Complete();
}

// Consumidor (BackgroundService)
protected override async Task ExecuteAsync(CancellationToken ct)
{
    await foreach (var order in _channel.Reader.ReadAllAsync(ct))
        await ProcessOrderAsync(order, ct);
}
```

### Task.WhenAll con límite (Parallel.ForEachAsync)

```csharp
// ✅ Procesar 10 en paralelo, no todos a la vez
var parallelOptions = new ParallelOptions
{
    MaxDegreeOfParallelism = 10,
    CancellationToken = ct
};

await Parallel.ForEachAsync(orderIds, parallelOptions, async (id, innerCt) =>
{
    await ProcessOrderAsync(id, innerCt);
});

// Alternativa con SemaphoreSlim para HttpClient
using var semaphore = new SemaphoreSlim(10);
var tasks = orderIds.Select(async id =>
{
    await semaphore.WaitAsync(ct);
    try { await ProcessOrderAsync(id, ct); }
    finally { semaphore.Release(); }
});
await Task.WhenAll(tasks);
```

### Evitar async void y fire-and-forget

```csharp
// ❌ Excepción se pierde
_ = SendEmailAsync(order); // Fire-and-forget sin manejo de errores

// ✅ Si realmente necesitas fire-and-forget: manejar errores
_ = Task.Run(async () =>
{
    try { await SendEmailAsync(order); }
    catch (Exception ex) { _logger.LogError(ex, "Background email failed"); }
});
```

---

## Pooling (ArrayPool, ObjectPool)

### ArrayPool<T>

```csharp
// ✅ Pool de arrays para buffers temporales
byte[]? rented = null;
try
{
    rented = ArrayPool<byte>.Shared.Rent(minimumLength);
    // Usar rented[..]
    _ = Whatever(rented.AsSpan(0, actualLength));
}
finally
{
    if (rented is not null)
        ArrayPool<byte>.Shared.Return(rented);
}
```

### ObjectPool (Microsoft.Extensions.ObjectPool)

```csharp
// Pool de objetos costosos (StringBuilder, listas, etc.)
var pool = new DefaultObjectPool<StringBuilder>(
    new DefaultPooledObjectPolicy<StringBuilder>());

var sb = pool.Get();
try
{
    sb.Append("Hello ");
    sb.Append("World");
    return sb.ToString();
}
finally
{
    sb.Clear();
    pool.Return(sb);
}
```

---

## Span<T> y Memory<T>

### Cuándo usar Span<T>

```csharp
// ✅ Parsing sin allocations
ReadOnlySpan<char> input = "123,456,789";
var sum = 0;
foreach (var range in input.Split(','))
{
    sum += int.Parse(input[range]);
}

// ✅ Manipulación de strings sin crear nuevos
ReadOnlySpan<char> path = "/api/orders/123";
var lastSlash = path.LastIndexOf('/');
var orderId = path[(lastSlash + 1)..]; // Slice, no allocation

// ✅ Stack-allocated buffers
Span<byte> buffer = stackalloc byte[256];
// Usar para operaciones pequeñas y temporales
```

### Reglas Span<T>

| Contexto | Permitido |
|----------|-----------|
| Parámetros de método | ✅ `Span<T>` |
| Campos de clase | ❌ Solo `Memory<T>` |
| Variables locales | ✅ |
| Async methods | ❌ Solo `Memory<T>` |
| Campos de ref struct | ✅ |

```csharp
// ✅ Parámetro
public static int Sum(Span<int> numbers) { ... }

// ✅ Campo de ref struct (compilador C# 13+)
public ref struct Buffer { private Span<byte> _data; }

// ❌ Campo de clase — usar Memory<T>
public class Processor { private Memory<byte> _buffer; }

// ❌ En async — usar Memory<T>
public async Task ProcessAsync(Memory<byte> data) { ... }
```

---

## HttpClient: fábrica y resiliencia

```csharp
// ✅ IHttpClientFactory (nunca new HttpClient())
builder.Services.AddHttpClient<IStripeService, StripeService>(client =>
{
    client.BaseAddress = new Uri("https://api.stripe.com/v1/");
    client.DefaultRequestHeaders.Accept.Add(
        new MediaTypeWithQualityHeaderValue("application/json"));
    client.Timeout = TimeSpan.FromSeconds(10);
})
.AddResilienceHandler("stripe-pipeline", (builder, context) =>
{
    builder
        .AddRetry(new RetryStrategyOptions
        {
            MaxRetryAttempts = 3,
            BackoffType = DelayBackoffType.Exponential,
            Delay = TimeSpan.FromMilliseconds(100)
        })
        .AddCircuitBreaker(new CircuitBreakerStrategyOptions
        {
            FailureRatio = 0.5,
            MinimumThroughput = 10,
            BreakDuration = TimeSpan.FromSeconds(30)
        })
        .AddTimeout(TimeSpan.FromSeconds(10));
});

// ❌ HttpClient manual — agotamiento de sockets, falta de resiliencia
// using var client = new HttpClient(); — NUNCA
```

---

## Benchmarking con BenchmarkDotNet

```csharp
// Paquete: BenchmarkDotNet
[MemoryDiagnoser] // Mide allocations
[ShortRunJob]
public class OrderProcessingBenchmarks
{
    private readonly Order _order = OrderTestData.LargeOrder();
    private readonly OrderCalculator _calculator = new();

    [Benchmark(Baseline = true)]
    public Money CurrentImplementation()
        => _calculator.CalculateTotal(_order);

    [Benchmark]
    public Money OptimizedImplementation()
        => _calculator.CalculateTotalOptimized(_order);
}

// Ejecutar
// dotnet run -c Release
// Los resultados muestran: tiempo medio, memoria allocada, GC collections
```

---

## Optimización de EF Core

### Top 5 optimizaciones

```csharp
// 1. Proyección — #1 en reducción de tráfico y memoria
var dtos = await db.Orders
    .Where(o => o.CustomerId == customerId)
    .Select(o => new { o.Id, o.Status, o.Total.Amount })
    .ToListAsync(ct);

// 2. AsNoTracking — evita overhead del change tracker
var orders = await db.Orders.AsNoTracking().ToListAsync(ct);

// 3. Split queries — evita producto cartesiano
var orders = await db.Orders
    .Include(o => o.Items)
    .Include(o => o.Discounts)
    .AsSplitQuery()
    .ToListAsync(ct);

// 4. ExecuteUpdate / ExecuteDelete — batch sin cargar entidades
await db.Orders
    .Where(o => o.Status == OrderStatus.Pending && o.CreatedAt < cutoff)
    .ExecuteUpdateAsync(s => s.SetProperty(o => o.Status, OrderStatus.Expired), ct);

// 5. Pooling de DbContext
services.AddDbContextPool<AppDbContext>(options =>
    options.UseSqlServer(connectionString), poolSize: 128);
```

### Índices faltantes

```csharp
// Verificar queries lentas con ToQueryString()
var sql = query.ToQueryString();
// Ejecutar en SSMS/psql con EXPLAIN ANALYZE
// Crear índice faltante
builder.HasIndex(o => new { o.CustomerId, o.Status })
    .HasDatabaseName("IX_Orders_CustomerId_Status_Include_Total")
    .IncludeProperties(o => o.Total);
```

---

## JSON Serialization performance

```csharp
// ✅ Source-generated serializers (sin reflection, AOT-ready)
[JsonSerializable(typeof(List<OrderDto>))]
[JsonSerializable(typeof(OrderDto))]
[JsonSerializable(typeof(PaginatedResponse<OrderDto>))]
internal partial class AppJsonContext : JsonSerializerContext { }

// Registrar
services.ConfigureHttpJsonOptions(options =>
{
    options.SerializerOptions.TypeInfoResolverChain.Insert(0, AppJsonContext.Default);
});

// Uso
var json = JsonSerializer.Serialize(orders, AppJsonContext.Default.ListOrderDto);
// ~40% más rápido que reflection-based en .NET 10
```

### Configuraciones de rendimiento

```csharp
services.ConfigureHttpJsonOptions(options =>
{
    options.SerializerOptions.DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull;
    options.SerializerOptions.PropertyNameCaseInsensitive = false; // Case-sensitive es más rápido
    options.SerializerOptions.NumberHandling = JsonNumberHandling.AllowReadingFromString; // Solo si se necesita
});
```

---

## Profiling y diagnóstico

### dotnet-counters

```bash
# Monitoreo en tiempo real
dotnet-counters monitor -p <pid> --counters System.Runtime

# Métricas clave:
#   cpu-usage, gc-heap-size, alloc-rate, threadpool-thread-count
```

### dotnet-trace

```bash
# Capturar trace de rendimiento
dotnet-trace collect -p <pid> --duration 00:00:30
# Analizar con PerfView (Windows) o speedscope (web)
```

### MiniProfiler

```csharp
// Paquete: MiniProfiler.AspNetCore.Mvc
builder.Services.AddMiniProfiler(options =>
{
    options.RouteBasePath = "/profiler";
    options.EnableDebugMode = builder.Environment.IsDevelopment();
});

app.UseMiniProfiler();

// En endpoints: ver tiempos de cada paso, queries SQL, etc.
```

---

## Anti-patrones de rendimiento

| Anti-patrón | Impacto | Corrección |
|-------------|---------|------------|
| `ToList()` antes de `Where()` | Carga toda la tabla en memoria | `Where()` primero |
| `Include` de todo | Over-fetching masivo | Proyección `.Select()` |
| `new HttpClient()` por request | Socket exhaustion | `IHttpClientFactory` |
| `string + string` en loops | Allocations masivas | `StringBuilder` o `string.Join` |
| `async` sin `CancellationToken` | Request no cancelable | Propagar `ct` |
| `ConfigureAwait(false)` en ASP.NET Core | Sin efecto, ruido | Eliminar (no aplica desde .NET Core 3.0) |
| `Thread.Sleep` en async | Bloquea thread del pool | `await Task.Delay` |
| `JsonConvert.SerializeObject` | Allocation doble vs System.Text.Json | Migrar a System.Text.Json |
| Sin `AsNoTracking` en queries de lectura | Change tracker overhead | Siempre en GETs |
| GC pressure por `byte[]` temporales | Fragmentation LOH | `ArrayPool<byte>` |

---

## GC y memoria

```csharp
// Minimizar allocaciones en hot paths

// ❌ Allocación por boxing
int value = 42;
object boxed = value; // Boxing
string s = $"Value: {value}"; // Boxing implícito

// ✅ Evitar boxing
string s = $"Value: {value.ToString()}"; // No boxing si ToString en struct

// ❌ Allocación de delegate por iteración
orders.ForEach(o => Process(o)); // lambda capturada

// ✅ foreach sin lambda
foreach (var o in orders) Process(o);

// ✅ Usar structs para tipos pequeños y frecuentes (< 16 bytes)
public readonly record struct Point3D(float X, float Y, float Z);

// StackAlloc para buffers temporales pequeños (< 1KB)
Span<byte> buffer = stackalloc byte[256];
```

### Configurar GC para servidor

```xml
<!-- .csproj -->
<PropertyGroup>
  <ServerGarbageCollection>true</ServerGarbageCollection>
  <ConcurrentGarbageCollection>true</ConcurrentGarbageCollection>
</PropertyGroup>
```

O vía `runtimeconfig.json`:
```json
{
  "runtimeOptions": {
    "configProperties": {
      "System.GC.Server": true,
      "System.GC.Concurrent": true
    }
  }
}
```

---

## Checklist de rendimiento

- [ ] Caché en capas (L1 memory, L2 Redis) con HybridCache
- [ ] EF Core: proyección en vez de Include, AsNoTracking, split queries, batch updates
- [ ] HTTP: IHttpClientFactory con resiliencia, nunca `new HttpClient()`
- [ ] JSON: source-generated serializers
- [ ] Async: CancellationToken propagado, ValueTask donde aplique
- [ ] Streaming: IAsyncEnumerable para conjuntos grandes
- [ ] Pooling: ArrayPool<T> para buffers temporales
- [ ] GC: Server GC habilitado en producción
- [ ] Sin `ConfigureAwait(false)` en ASP.NET Core
- [ ] Sin `ToList()` antes de `Where()` en EF Core
- [ ] Paginación keyset en vez de offset para páginas profundas
- [ ] Compression middleware habilitado
- [ ] Response caching en endpoints de solo lectura
- [ ] Kestrel limits configurados (request body size, concurrency)
- [ ] `dotnet-counters` / Application Insights para monitoreo
