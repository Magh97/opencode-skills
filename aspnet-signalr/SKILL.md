---
name: aspnet-signalr
description: SignalR para comunicación en tiempo real en ASP.NET Core. Cubre Hubs, clientes, grupos, streaming, protocolos (WebSocket, SSE, Long Polling), autenticación y autorización, scale-out con Redis backplane, Azure SignalR Service, y rendimiento. Actívala al implementar notificaciones en tiempo real, dashboards live, chat, o pipelines de streaming.
disable-model-invocation: true
---

# SignalR

Guía de comunicación bidireccional en tiempo real con SignalR en .NET 9/10.

---

## Setup

```csharp
// Program.cs
builder.Services.AddSignalR(options =>
{
    options.EnableDetailedErrors = builder.Environment.IsDevelopment();
    options.MaximumReceiveMessageSize = 32 * 1024; // 32 KB
    options.KeepAliveInterval = TimeSpan.FromSeconds(15);
    options.ClientTimeoutInterval = TimeSpan.FromSeconds(30);
    options.HandshakeTimeout = TimeSpan.FromSeconds(15);
})
.AddStackExchangeRedis(builder.Configuration.GetConnectionString("Redis")!); // Scale-out

var app = builder.Build();
app.MapHub<OrderHub>("/hubs/orders");
```

---

## Hub

### Hub canónico

```csharp
public class OrderHub : Hub
{
    private readonly ILogger<OrderHub> _logger;

    public OrderHub(ILogger<OrderHub> logger) => _logger = logger;

    // Conectar
    public override async Task OnConnectedAsync()
    {
        var userId = Context.UserIdentifier;
        _logger.LogInformation("User {UserId} connected (connection {ConnectionId})",
            userId, Context.ConnectionId);

        await base.OnConnectedAsync();
    }

    // Desconectar
    public override async Task OnDisconnectedAsync(Exception? exception)
    {
        _logger.LogInformation("Connection {ConnectionId} disconnected: {Error}",
            Context.ConnectionId, exception?.Message ?? "Clean disconnect");

        await base.OnDisconnectedAsync(exception);
    }

    // Método que el cliente invoca
    public async Task SubscribeToOrder(string orderId)
    {
        var groupName = $"order-{orderId}";
        await Groups.AddToGroupAsync(Context.ConnectionId, groupName);
        _logger.LogInformation("Connection {ConnectionId} subscribed to {Group}",
            Context.ConnectionId, groupName);
    }

    public async Task UnsubscribeFromOrder(string orderId)
    {
        var groupName = $"order-{orderId}";
        await Groups.RemoveFromGroupAsync(Context.ConnectionId, groupName);
    }
}
```

### Enviar desde el servidor

```csharp
// Inyectar IHubContext en cualquier servicio
public class OrderService(
    IHubContext<OrderHub> hubContext,
    ILogger<OrderService> logger)
{
    public async Task UpdateOrderAsync(Order order, CancellationToken ct)
    {
        // Guardar...
        await db.SaveChangesAsync(ct);

        // Notificar a clientes específicos (grupo)
        var dto = OrderDto.From(order);
        await hubContext.Clients
            .Group($"order-{order.Id}")
            .SendAsync("OrderUpdated", dto, ct);

        // Notificar a usuario específico
        await hubContext.Clients
            .User(order.CustomerId)
            .SendAsync("Notification", $"Order {order.Id} updated", ct);

        // Notificar a todos
        await hubContext.Clients.All
            .SendAsync("GlobalNotification", "System update in 5 minutes", ct);

        // A todos excepto una conexión
        await hubContext.Clients.AllExcept(Context.ConnectionId)
            .SendAsync("UserJoined", userName, ct);
    }
}
```

---

## Streaming

### Server-to-Client Streaming

```csharp
// Hub con streaming desde servidor
public class DashboardHub : Hub
{
    public async IAsyncEnumerable<MetricPoint> StreamMetrics(
        int intervalSeconds,
        [EnumeratorCancellation] CancellationToken ct)
    {
        while (!ct.IsCancellationRequested)
        {
            var metrics = await _metricsService.GetCurrentMetricsAsync(ct);
            yield return metrics;
            await Task.Delay(TimeSpan.FromSeconds(intervalSeconds), ct);
        }
    }

    // Channel<T> reader
    public ChannelReader<OrderEvent> StreamOrders(CancellationToken ct)
    {
        var channel = Channel.CreateUnbounded<OrderEvent>();

        _ = WriteOrdersAsync(channel.Writer, ct);

        return channel.Reader;
    }

    private async Task WriteOrdersAsync(ChannelWriter<OrderEvent> writer, CancellationToken ct)
    {
        try
        {
            while (!ct.IsCancellationRequested)
            {
                var events = await _orderService.GetRecentEventsAsync(ct);
                foreach (var evt in events)
                    await writer.WriteAsync(evt, ct);

                await Task.Delay(1000, ct);
            }
        }
        finally
        {
            writer.Complete();
        }
    }
}
```

### Client-to-Server Streaming

```csharp
// Hub recibe streaming del cliente
public class UploadHub : Hub
{
    public async Task UploadData(IAsyncEnumerable<string> data, CancellationToken ct)
    {
        await foreach (var item in data.WithCancellation(ct))
        {
            await ProcessItemAsync(item, ct);
        }
    }
}
```

---

## Cliente JavaScript

```javascript
// npm install @microsoft/signalr

const connection = new signalR.HubConnectionBuilder()
    .withUrl("/hubs/orders", {
        accessTokenFactory: () => getToken()
    })
    .withAutomaticReconnect([0, 2000, 5000, 10000, 30000]) // Reintentos
    .configureLogging(signalR.LogLevel.Information)
    .build();

// Recibir mensajes del servidor
connection.on("OrderUpdated", (order) => {
    console.log("Order updated:", order);
    updateOrderCard(order);
});

connection.on("Notification", (message) => {
    showToast(message);
});

// Enviar mensajes al servidor
await connection.invoke("SubscribeToOrder", orderId);

// Streaming del servidor
connection.stream("StreamMetrics", 5)
    .subscribe({
        next: (metric) => updateChart(metric),
        error: (err) => console.error(err),
        complete: () => console.log("Stream completed")
    });

// Iniciar conexión
try {
    await connection.start();
    console.log("Connected:", connection.connectionId);
} catch (err) {
    console.error("Connection failed:", err);
}

// Reconexión
connection.onreconnecting((error) => {
    console.log("Reconnecting:", error);
});

connection.onreconnected((connectionId) => {
    console.log("Reconnected:", connectionId);
    // Re-subscribir a grupos
    connection.invoke("SubscribeToOrder", orderId);
});

connection.onclose(() => {
    console.log("Connection closed");
});
```

### Cliente .NET

```csharp
// Paquete: Microsoft.AspNetCore.SignalR.Client
var connection = new HubConnectionBuilder()
    .WithUrl("https://miapp.com/hubs/orders", options =>
    {
        options.AccessTokenProvider = () => Task.FromResult(token)!;
    })
    .WithAutomaticReconnect()
    .Build();

connection.On<OrderDto>("OrderUpdated", order =>
{
    Console.WriteLine($"Order {order.Id}: {order.Status}");
});

await connection.StartAsync();
await connection.InvokeAsync("SubscribeToOrder", "order-123");

// Streaming
var stream = connection.StreamAsync<MetricPoint>("StreamMetrics", 5, CancellationToken.None);
await foreach (var metric in stream)
{
    Console.WriteLine($"CPU: {metric.CpuUsage}%");
}
```

---

## Autenticación

### Cookie auth (misma app)

```csharp
// SignalR usa la cookie de autenticación por defecto.
// Si ya estás autenticado en el sitio web, el hub recibe el User.

// Para enviar token explícitamente (SPA / mobile):
[Authorize]
public class OrderHub : Hub
{
    public override async Task OnConnectedAsync()
    {
        var userId = Context.UserIdentifier; // Desde JWT o cookie
        var userName = Context.User?.Identity?.Name;
    }
}
```

### JWT token en query string

```csharp
// Servidor: configurar evento para extraer token del query string
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.Events = new JwtBearerEvents
        {
            OnMessageReceived = context =>
            {
                var accessToken = context.Request.Query["access_token"];
                var path = context.HttpContext.Request.Path;

                if (!string.IsNullOrEmpty(accessToken) && path.StartsWithSegments("/hubs"))
                    context.Token = accessToken;

                return Task.CompletedTask;
            }
        };
    });

// Cliente JavaScript: enviar token en query string
const connection = new signalR.HubConnectionBuilder()
    .withUrl("/hubs/orders", { accessTokenFactory: () => token })
    .build();

// Cliente .NET
var connection = new HubConnectionBuilder()
    .WithUrl("https://miapp.com/hubs/orders", options =>
        options.AccessTokenProvider = () => Task.FromResult(token)!)
    .Build();
```

---

## Scale-out con Redis

```csharp
// Redis backplane: mensajes se publican a todos los servidores
builder.Services.AddSignalR()
    .AddStackExchangeRedis(options =>
    {
        options.Configuration = builder.Configuration.GetConnectionString("Redis");
        options.Configuration.ChannelPrefix = "MiAppSignalR";
    });

// Azure SignalR Service (manejado, sin preocuparse de conexiones WebSocket)
builder.Services.AddSignalR()
    .AddAzureSignalR(options =>
    {
        options.ConnectionString = builder.Configuration["Azure:SignalR:ConnectionString"];
    });
```

---

## Grupos

```csharp
public class NotificationHub : Hub
{
    // Agregar a grupo
    public async Task JoinDepartment(string department)
    {
        await Groups.AddToGroupAsync(Context.ConnectionId, $"dept-{department}");
    }

    // Remover
    public async Task LeaveDepartment(string department)
    {
        await Groups.RemoveFromGroupAsync(Context.ConnectionId, $"dept-{department}");
    }
}

// Enviar a grupo (desde servicio externo)
await hubContext.Clients
    .Group("dept-Sales")
    .SendAsync("DepartmentNotification", message, ct);
```

---

## Manejo de errores y reconexión

```csharp
// Servidor: enviar errores al cliente que invocó
public async Task SubscribeToOrder(string orderId)
{
    if (string.IsNullOrWhiteSpace(orderId))
        throw new HubException("OrderId is required");

    // ...
}

// Cliente: capturar errores
connection.on("OrderError", (error) => {
    showError(error.message);
});

// Reconexión automática configurada en cliente:
// .withAutomaticReconnect([0, 2000, 5000, 10000, 30000])
```

---

## Rendimiento SignalR

```csharp
// Tamaño de mensajes
options.MaximumReceiveMessageSize = 32 * 1024; // 32 KB
// Para mensajes grandes (>32KB), usar streaming en vez de SendAsync

// Compresión
// WebSocket ya usa compresión per-message-deflate

// Serialización
// Por defecto: JSON. Para mayor rendimiento: MessagePack
builder.Services.AddSignalR()
    .AddMessagePackProtocol();

// Paquete: Microsoft.AspNetCore.SignalR.Protocols.MessagePack

// Cliente JS:
// npm install @microsoft/signalr-protocol-msgpack
// .withHubProtocol(new signalR.protocols.msgpack.MessagePackHubProtocol())
```

---

## Anti-patrones SignalR

| Anti-patrón | Problema | Corrección |
|-------------|----------|------------|
| Hub con lógica de negocio | Hub = transporte, no servicio | Inyectar servicio, Hub solo enruta |
| `IHubContext` en Singleton sin suscripción | Funciona, pero cuidado con DI | Usar `IServiceScopeFactory` si necesita Scoped |
| Sin scale-out en producción | Un servidor no escala horizontalmente | Redis backplane o Azure SignalR |
| Sin reconexión automática | Usuario pierde mensajes al desconectar | `WithAutomaticReconnect()` |
| Mensajes grandes vía `SendAsync` | Bloquea el hub | Usar streaming para datos grandes |
| Sin autenticación | Cualquiera se conecta al hub | `[Authorize]` en el Hub o `RequireAuthorization` en MapHub |
| Grupos no limpiados | Memory leak en Redis backplane | Remover al desconectar |

---

## Checklist SignalR

- [ ] Hub mapeado con `MapHub<T>()`
- [ ] Autenticación configurada (JWT vía query string para SPAs)
- [ ] Autorización con `[Authorize]` en Hub o endpoints
- [ ] Redis backplane en producción (o Azure SignalR Service)
- [ ] Reconexión automática configurada en cliente
- [ ] Manejo de errores con `HubException` y captura en cliente
- [ ] Grupos gestionados (add en connect, remove en disconnect)
- [ ] Streaming para datos continuos (no polling manual)
- [ ] MessagePack para mensajes grandes o alto throughput
- [ ] Logging de conexiones, desconexiones, y errores
- [ ] Sin lógica de negocio en Hub — delegar a servicios
- [ ] `CancellationToken` propagado en streaming
