---
name: aspnet-blazor
description: Blazor en todas sus variantes (Server, WebAssembly, Hybrid, .NET MAUI). Cubre componentes, ciclo de vida, parámetros, binding, EventCallback, state management, JS interop, autenticación, autorización, render modes (.NET 8+), prerendering, streaming rendering, y testing con bUnit. Actívala al construir aplicaciones Blazor, migrar de Razor/MVC a Blazor, o implementar componentes interactivos.
disable-model-invocation: true
---

# Blazor

Guía completa de Blazor en .NET 9/10. Cubre Blazor Server, WebAssembly (WASM), Auto Render Mode, y Hybrid.

---

## Render Modes (.NET 8+)

| Modo | Dónde ejecuta | Latencia | Offline | SEO |
|------|--------------|----------|---------|-----|
| **Static SSR** | Servidor (sin interactividad) | Baja | ❌ | ✅ |
| **Server** | Servidor (SignalR) | Requiere conexión | ❌ | ⬜ |
| **WebAssembly** | Cliente (navegador) | Alta (descarga inicial) | ✅ | ❌ |
| **Auto** | Server inicial, WASM después | Mejor de ambos | Eventual | ⬜ |

```csharp
// Configurar render modes
builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents()
    .AddInteractiveWebAssemblyComponents();

// Componentes con render mode
@* Siempre SSR *@
<StaticPage />

@* Server interactivo (necesita SignalR) *@
<Counter @rendermode="InteractiveServer" />

@* WASM interactivo *@
<WeatherWidget @rendermode="InteractiveWebAssembly" />

@* Auto: Server en primera carga, WASM después *@
<Dashboard @rendermode="InteractiveAuto" />
```

---

## Componentes

### Estructura canónica

```razor
@page "/orders"
@rendermode InteractiveServer

@using MiApp.Application.Orders
@inject IOrderService OrderService
@inject NavigationManager Navigation

<h1>Orders</h1>

@if (isLoading)
{
    <p><em>Loading...</em></p>
}
else if (orders is null || orders.Count == 0)
{
    <div class="alert alert-info">No orders found</div>
}
else
{
    <table class="table">
        <thead>
            <tr>
                <th>ID</th>
                <th>Customer</th>
                <th>Status</th>
                <th>Total</th>
                <th></th>
            </tr>
        </thead>
        <tbody>
            @foreach (var order in orders)
            {
                <tr>
                    <td>@order.Id</td>
                    <td>@order.CustomerName</td>
                    <td><StatusBadge Status="order.Status" /></td>
                    <td>@order.Total.ToString("C")</td>
                    <td>
                        <button class="btn btn-primary btn-sm"
                                @onclick="() => ViewOrder(order.Id)">
                            View
                        </button>
                    </td>
                </tr>
            }
        </tbody>
    </table>
}

@code {
    private List<OrderDto>? orders;
    private bool isLoading = true;

    protected override async Task OnInitializedAsync()
    {
        await LoadOrdersAsync();
    }

    private async Task LoadOrdersAsync()
    {
        isLoading = true;
        try
        {
            orders = await OrderService.GetAllAsync();
        }
        finally
        {
            isLoading = false;
        }
    }

    private void ViewOrder(Guid id)
        => Navigation.NavigateTo($"/orders/{id}");
}
```

### Parámetros

```razor
@* Componente hijo: OrderCard.razor *@
<div class="card">
    <h5>Order #@Id</h5>
    <p>@CustomerName</p>
</div>

@code {
    [Parameter]
    [EditorRequired]
    public Guid Id { get; set; }

    [Parameter]
    public string CustomerName { get; set; } = string.Empty;

    [Parameter]
    public EventCallback<Guid> OnSelected { get; set; }
}

@* Uso *@
<OrderCard Id="order.Id"
           CustomerName="order.CustomerName"
           OnSelected="id => Console.WriteLine($'Selected {id}')" />
```

### Cascading Parameters

```razor
@* Proveer valor en cascada *@
<CascadingValue Name="TenantId" Value="@CurrentTenantId">
    @Body
</CascadingValue>

@code {
    private string CurrentTenantId = "TENANT-001";
}

@* Consumir en cualquier componente hijo *@
@code {
    [CascadingParameter(Name = "TenantId")]
    public string TenantId { get; set; } = string.Empty;
}
```

---

## Ciclo de vida

```
SetParametersAsync()       → Recibir parámetros del padre
        ↓
OnInitialized() / OnInitializedAsync()  → Primera carga
        ↓
OnParametersSet() / OnParametersSetAsync() → Cada cambio de parámetros
        ↓
Render                     → Renderizar el componente
        ↓
OnAfterRender() / OnAfterRenderAsync(bool firstRender) → JS interop, animaciones
        ↓
Dispose() / DisposeAsync()  → Limpiar recursos (IDisposable/IAsyncDisposable)
```

```razor
@implement IDisposable
@implements IAsyncDisposable

@code {
    protected override async Task OnInitializedAsync()
    {
        // Cargar datos iniciales (una vez)
        await LoadDataAsync();
    }

    protected override async Task OnParametersSetAsync()
    {
        // Reaccionar a cambios de parámetros del padre
        if (OrderId != _previousOrderId)
        {
            _previousOrderId = OrderId;
            await RefreshAsync();
        }
    }

    protected override async Task OnAfterRenderAsync(bool firstRender)
    {
        if (firstRender)
        {
            // Inicializar JS (gráficos, mapas, etc.)
            await JsRuntime.InvokeVoidAsync("initChart");
        }
    }

    public void Dispose()
    {
        // Liberar recursos síncronos
    }

    public async ValueTask DisposeAsync()
    {
        // Liberar recursos async
        await UnsubscribeAsync();
    }
}
```

---

## State Management

### 1. Component state (local)

```razor
@code {
    private int count = 0; // Vive mientras el componente existe
}
```

### 2. Servicio inyectado

```csharp
// Registrar estado compartido
builder.Services.AddScoped<CartState>();
builder.Services.AddSingleton<NotificationState>(); // Solo en Blazor Server

// Consumo
@inject CartState Cart

<p>Items in cart: @Cart.Items.Count</p>
```

### 3. AppState + Notifier

```csharp
public class CartState
{
    private List<CartItem> _items = [];

    public IReadOnlyList<CartItem> Items => _items;
    public int Count => _items.Count;
    public decimal Total => _items.Sum(i => i.Price * i.Quantity);

    public event Action? OnChange;
    private void NotifyStateChanged() => OnChange?.Invoke();

    public void AddItem(CartItem item)
    {
        _items.Add(item);
        NotifyStateChanged();
    }
}

// Componente suscriptor
@implements IDisposable
@inject CartState Cart

@code {
    protected override void OnInitialized()
    {
        Cart.OnChange += StateHasChanged;
    }

    public void Dispose() => Cart.OnChange -= StateHasChanged;
}
```

### 4. Blazor Fluent UI / Radzen / MudBlazor state

Usar los patrones que provee la librería de componentes (Form, DataGrid, etc.).

---

## JS Interop

### Llamar JS desde C#

```csharp
// Inyectar IJSRuntime / IJSInProcessRuntime
@inject IJSRuntime Js

// Async (seguro en todos los modos)
await Js.InvokeVoidAsync("console.log", "Hello from Blazor");
var result = await Js.InvokeAsync<string>("prompt", "Enter your name:");

// Sync (solo Blazor WASM, más rápido)
@inject IJSInProcessRuntime JsSync
JsSync.InvokeVoid("localStorage.setItem", "key", "value");
```

### Llamar C# desde JS

```javascript
// Desde JS: invocar método estático .NET
DotNet.invokeMethodAsync('MiApp.Web', 'GetServerTime')
    .then(time => console.log(time));

// Desde JS: invocar método de instancia (referencia a componente)
objRef.invokeMethodAsync('HandleEvent', eventData);
```

```csharp
// Registrar referencia desde C#
private DotNetObjectReference<MyComponent>? _objRef;

protected override void OnInitialized()
{
    _objRef = DotNetObjectReference.Create(this);
}

// Método que JS va a llamar
[JSInvokable]
public async Task HandleEventAsync(string data)
{
    // ...
}
```

### Módulos JavaScript (recomendado)

```csharp
private IJSObjectReference? _module;

protected override async Task OnAfterRenderAsync(bool firstRender)
{
    if (firstRender)
    {
        _module = await Js.InvokeAsync<IJSObjectReference>(
            "import", "./js/charts.js");

        await _module.InvokeVoidAsync("renderChart", data);
    }
}

public async ValueTask DisposeAsync()
{
    if (_module is not null)
        await _module.DisposeAsync();
}
```

---

## Formularios

```razor
@using System.ComponentModel.DataAnnotations

<EditForm Model="@order" OnValidSubmit="@HandleValidSubmit" OnInvalidSubmit="@HandleInvalidSubmit">
    <DataAnnotationsValidator />
    <ValidationSummary />

    <div class="mb-3">
        <label for="customer" class="form-label">Customer</label>
        <InputText id="customer" class="form-control" @bind-Value="order.CustomerName" />
        <ValidationMessage For="() => order.CustomerName" />
    </div>

    <div class="mb-3">
        <label for="quantity" class="form-label">Quantity</label>
        <InputNumber id="quantity" class="form-control" @bind-Value="order.Quantity" />
        <ValidationMessage For="() => order.Quantity" />
    </div>

    <button type="submit" class="btn btn-primary">Submit</button>
</EditForm>

@code {
    private CreateOrderModel order = new() { CustomerName = "", Quantity = 1 };

    private async Task HandleValidSubmit()
    {
        await OrderService.CreateAsync(order);
        Navigation.NavigateTo("/orders");
    }

    private void HandleInvalidSubmit()
    {
        Console.WriteLine("Form has validation errors");
    }
}
```

### FluentValidation en Blazor

```csharp
// Paquete: Blazored.FluentValidation
<FluentValidationValidator />

// La validación usa IValidator<T> inyectado desde DI
// Registro: services.AddScoped<IValidator<CreateOrderModel>, CreateOrderValidator>();
```

---

## Autenticación en Blazor

### Blazor Server / WASM con Identity

```csharp
// Server: usa cookies/Identity como cualquier app ASP.NET Core
builder.Services.AddAuthentication(CookieAuthenticationDefaults.AuthenticationScheme)
    .AddCookie();

// En componente: mostrar contenido autenticado
<AuthorizeView>
    <Authorized>
        <p>Welcome, @context.User.Identity?.Name</p>
    </Authorized>
    <NotAuthorized>
        <p>Please <a href="/login">log in</a></p>
    </NotAuthorized>
</AuthorizeView>

// Restringir página
@attribute [Authorize]
@attribute [Authorize(Roles = "Admin")]

// Verificar en código
@inject AuthenticationStateProvider AuthState

@code {
    protected override async Task OnInitializedAsync()
    {
        var authState = await AuthState.GetAuthenticationStateAsync();
        var user = authState.User;

        if (user.Identity?.IsAuthenticated == true)
        {
            var userId = user.FindFirst(ClaimTypes.NameIdentifier)?.Value;
        }
    }
}
```

### Blazor WASM standalone (API externa)

```csharp
// NuGet: Microsoft.AspNetCore.Components.WebAssembly.Authentication
builder.Services.AddOidcAuthentication(options =>
{
    builder.Configuration.Bind("Auth", options.ProviderOptions);
    options.ProviderOptions.ResponseType = "code";
});

// appsettings.json
{
  "Auth": {
    "Authority": "https://auth.miapp.com",
    "ClientId": "blazor-wasm-client",
    "PostLogoutRedirectUri": "https://miapp.com/authentication/logout-callback",
    "RedirectUri": "https://miapp.com/authentication/login-callback",
    "DefaultScopes": ["openid", "profile", "email", "api"]
  }
}
```

---

## Rendimiento Blazor

```csharp
// ✅ ShouldRender — evitar re-renders innecesarios
protected override bool ShouldRender()
{
    return _lastData != _currentData;
}

// ✅ @key para identidad de elementos en loops
@foreach (var order in orders)
{
    <OrderCard @key="order.Id" Order="order" />
}

// ✅ @rendermode pragmático
// Static SSR para contenido sin interactividad
// InteractiveServer solo donde se necesita interactividad

// ✅ Virtualize para listas grandes
<Virtualize Items="orders" Context="order">
    <OrderCard Order="order" />
</Virtualize>

// ✅ Deferred loading
@if (showChart)
{
    <LazyLoader>
        <ExpensiveChart Data="chartData" />
    </LazyLoader>
}
```

---

## Testing con bUnit

```csharp
// Paquete: bUnit
[Fact]
public void OrderCard_RendersCorrectly()
{
    // Arrange
    using var ctx = new TestContext();
    ctx.Services.AddSingleton<NavigationManager>(new FakeNavigationManager());

    var order = new OrderDto { Id = Guid.NewGuid(), CustomerName = "Test", Total = 150m };

    // Act
    var cut = ctx.RenderComponent<OrderCard>(parameters => parameters
        .Add(p => p.Order, order));

    // Assert
    cut.Markup.Should().Contain("Test");
    cut.Find(".total").TextContent.Should().Be("$150.00");
}

[Fact]
public void OrderCard_OnClick_CallsEventCallback()
{
    using var ctx = new TestContext();
    Guid? selectedId = null;

    var order = new OrderDto { Id = Guid.NewGuid(), CustomerName = "Test", Total = 150m };

    var cut = ctx.RenderComponent<OrderCard>(parameters => parameters
        .Add(p => p.Order, order)
        .Add(p => p.OnSelected, id => selectedId = id));

    cut.Find("button").Click();

    selectedId.Should().Be(order.Id);
}
```

---

## Checklist Blazor

- [ ] Render mode definido (Static SSR, Server, WASM, Auto)
- [ ] Componentes pequeños y enfocados (SRP)
- [ ] Parámetros con `[EditorRequired]` donde aplique
- [ ] `StateHasChanged()` solo cuando necesario
- [ ] `IDisposable`/`IAsyncDisposable` para limpiar suscripciones
- [ ] JS interop vía módulos (`IJSObjectReference`)
- [ ] `@key` en loops para identidad de elementos
- [ ] `Virtualize` para listas > 100 elementos
- [ ] Formularios con `EditForm` + validación
- [ ] Auth con `AuthorizeView` / `[Authorize]`
- [ ] Error boundaries con `ErrorBoundary` componente
- [ ] `ShouldRender()` para evitar re-renders
- [ ] Tests con bUnit para componentes interactivos
