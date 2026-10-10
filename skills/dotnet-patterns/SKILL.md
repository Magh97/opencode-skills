---
name: dotnet-patterns
description: "Patrones de diseño en .NET y C#: creacionales, estructurales y de comportamiento, más patrones del ecosistema (Options, Pipeline, Retry, Circuit Breaker, Repository, Specification) y antipatrones. Úsala al diseñar o refactorizar componentes."
disable-model-invocation: true
---

# Patrones de Diseño en .NET

Guía práctica de patrones GoF y patrones específicos del ecosistema .NET. Cada patrón responde **qué problema resuelve**, **cuándo usarlo**, **cuándo NO usarlo**, y muestra implementación idiomática en C#.

## Índice

- [Creacionales](#creacionales)
  - [Factory Method](#factory-method)
  - [Abstract Factory](#abstract-factory)
  - [Builder](#builder)
  - [Singleton (en era DI)](#singleton-en-era-di)
  - [Prototype](#prototype)
- **Estructurales y comportamiento** → `references/estructurales-comportamiento.md`
  - Decorator, Adapter, Facade, Composite, Proxy, Bridge, Strategy, Observer, Template Method, Command, Mediator, Chain of Responsibility, State, Visitor
- **Patrones del ecosistema .NET** → `references/ecosistema.md`
  - Options, Pipeline/Middleware, Retry + Circuit Breaker, Repository, Unit of Work, Specification, Result Pattern
- [Anti-patrones y sobre-ingeniería](#anti-patrones-y-sobre-ingeniería)

---

## Creacionales

### Factory Method

**Problema**: Crear objetos cuya dependencia concreta no se conoce hasta runtime.

**En .NET moderno** dos enfoques principales:

#### 1. Factory vía DI — `Func<T>` inyectado

```csharp
// Registro
services.AddTransient<StripePaymentService>();
services.AddTransient<PayPalPaymentService>();

// Factoría resuelta por DI
services.AddTransient<Func<string, IPaymentService>>(sp => key => key switch
{
    "stripe" => sp.GetRequiredService<StripePaymentService>(),
    "paypal" => sp.GetRequiredService<PayPalPaymentService>(),
    _ => throw new ArgumentException($"Unknown provider: {key}")
});
```

#### 2. Factory con Keyed DI (.NET 8+) — preferido

```csharp
// Registro con clave
services.AddKeyedScoped<IPaymentService, StripePaymentService>("stripe");
services.AddKeyedScoped<IPaymentService, PayPalPaymentService>("paypal");

// Consumo
public class CheckoutService(
    [FromKeyedServices("stripe")] IPaymentService paymentService)
{
}
```

**Cuándo no**: si la creación es trivial (`new Order()`) o si Keyed DI cubre el caso.

---

### Abstract Factory

**Problema**: Familia de objetos relacionados que deben crearse juntos (ej. UI para Windows vs macOS).

```csharp
// Familia de productos
public interface IButton { void Render(); }
public interface ITextBox { void Render(); }

// Fábrica abstracta
public interface IUiFactory
{
    IButton CreateButton();
    ITextBox CreateTextBox();
}

// Fábricas concretas
public class WindowsUiFactory : IUiFactory
{
    public IButton CreateButton() => new WindowsButton();
    public ITextBox CreateTextBox() => new WindowsTextBox();
}

// Consumo vía DI según entorno
services.AddScoped<IUiFactory>(sp =>
    RuntimeInformation.IsOSPlatform(OSPlatform.Windows)
        ? new WindowsUiFactory()
        : new MacUiFactory());
```

**Cuándo sí**: sistema multi-plataforma real, multi-tenant, multi-proveedor.

**Cuándo no**: "por si acaso" — YAGNI.

---

### Builder

**Problema**: Construcción paso a paso de objetos complejos con muchas configuraciones opcionales.

#### Builder fluido tradicional

```csharp
public class EmailMessageBuilder
{
    private readonly EmailMessage _message = new();

    public EmailMessageBuilder To(string address)
    {
        _message.To.Add(address);
        return this;
    }

    public EmailMessageBuilder WithSubject(string subject)
    {
        _message.Subject = subject;
        return this;
    }

    public EmailMessageBuilder WithAttachment(string path, byte[] content)
    {
        _message.Attachments.Add(new Attachment(path, content));
        return this;
    }

    public EmailMessage Build() => _message;
}

// Uso
var email = new EmailMessageBuilder()
    .To("user@example.com")
    .WithSubject("Welcome!")
    .WithAttachment("invoice.pdf", pdfBytes)
    .Build();
```

#### Builder con `required` + `init` (.NET 6+) — para objetos planos

```csharp
public class EmailMessage
{
    public required List<string> To { get; init; }
    public string Subject { get; init; } = string.Empty;
    public List<Attachment> Attachments { get; init; } = new();
}

// Uso con object initializer — no necesita builder
var email = new EmailMessage
{
    To = ["user@example.com"],
    Subject = "Welcome!",
    Attachments = { new("invoice.pdf", pdfBytes) }
};
```

**Regla**: Builder solo si hay +5 propiedades opcionales con lógica de construcción _durante_ el build. Menos que eso → `required` + `init`.

---

### Singleton (en era DI)

**Problema**: Una única instancia compartida en toda la aplicación.

**En .NET**: el contenedor DI ya maneja el ciclo de vida. No implementar singleton manual.

```csharp
// ✅ Singleton vía DI
services.AddSingleton<IEmailTemplateCache, EmailTemplateCache>();

// ⬜ Singleton manual (solo legacy o sin DI)
public sealed class ConfigLoader
{
    private static readonly Lazy<ConfigLoader> _instance = new(() => new ConfigLoader());
    public static ConfigLoader Instance => _instance.Value;
    private ConfigLoader() { }
}
```

**⚠️ Peligro**: Singletons que dependen de servicios Scoped → error en runtime. El DI lanza `InvalidOperationException` en .NET 9+ con mensaje claro.

**Alternativa**: `AddSingleton` para cache en memoria, `IDistributedCache` para cache distribuida, `HybridCache` para dos niveles.

---

### Prototype

**Problema**: Crear objetos clonando una instancia existente en vez de construir desde cero.

```csharp
// ✅ ICloneable moderno con record
public record OrderTemplate(string CustomerTier, decimal DefaultDiscount, List<string> Tags);

var template = new OrderTemplate("Gold", 0.15m, ["priority", "vip"]);
var order1 = template with { };  // clone exacto
var order2 = template with { Tags = ["standard"] }; // clone con override

// ✅ Deep clone con JSON (simple, lento pero funciona)
var cloned = JsonSerializer.Deserialize<OrderTemplate>(
    JsonSerializer.Serialize(original));
```

---


## Anti-patrones y sobre-ingeniería

| Anti-patrón | Problema | Solución |
|-------------|----------|----------|
| `IRepository<T>` genérico | No agrega valor sobre `DbSet<T>` | Métodos de extensión o repos específicos con queries nombradas |
| Factory para 1 sola implementación | Indirección innecesaria | `new()` o DI directo |
| `IValidator` custom sin FluentValidation | Reinventar la rueda | FluentValidation + DataAnnotations |
| Strategy con 2 opciones que nunca cambiaron | Complejidad sin beneficio | `switch` o `Dictionary<string, Func<>>` |
| MediatR en CRUD sin eventos | Indirección pura | Llamar al handler/service directamente |
| Builder para objetos con 3 propiedades | Over-engineering | `required` + `init` o constructor |
| Interface con 1 sola implementación | "Por si acaso" | Borrar la interfaz. Crearla cuando surja la segunda implementación. |
| Singleton manual con `Lazy<T>` | DI lo maneja | `AddSingleton<T>()` |

---

## Checklist de decisión

Antes de implementar un patrón, responder:

1. ¿El patrón **resuelve un problema real** en este código o es "por si acaso"? → Si es especulativo, no.
2. ¿Hay una **forma más simple** de resolverlo sin el patrón? → Si sí, usar la simple.
3. ¿.NET ya lo ofrece nativamente? (DI, middleware, `IObservable`, `Channel`, Resilience) → Si sí, usar lo nativo.
4. ¿El equipo conoce el patrón? → Si no, pesa más la mantenibilidad que la elegancia.

---

## Referencias

- `references/estructurales-comportamiento.md` — catálogo completo de patrones estructurales y de comportamiento (Decorator, Adapter, Facade, Composite, Proxy, Bridge, Strategy, Observer, Template Method, Command, Mediator, Chain of Responsibility, State, Visitor).
- `references/ecosistema.md` — patrones del ecosistema .NET: Options, Pipeline/Middleware, Retry + Circuit Breaker, Repository, Unit of Work, Specification y Result Pattern.
