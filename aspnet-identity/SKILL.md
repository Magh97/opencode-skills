---
name: aspnet-identity
description: Autenticación y autorización en ASP.NET Core Identity. Cubre Identity framework, JWT Bearer, OAuth2/OIDC, cookies, roles, claims, policies, external providers (Google, Microsoft, Facebook), 2FA, password policies, lockout, y protección de datos. Actívala al implementar login, registro, gestión de usuarios, proteger endpoints o configurar autenticación en cualquier proyecto ASP.NET.
disable-model-invocation: true
---

# ASP.NET Core Identity

Guía completa de autenticación y autorización. Cubre Identity framework, JWT, OAuth2, cookies, y políticas.

---

## Setup Identity

```csharp
// 1. DbContext de Identity
public class AppIdentityDbContext(DbContextOptions<AppIdentityDbContext> options)
    : IdentityDbContext<ApplicationUser, IdentityRole, string>(options)
{
    protected override void OnModelCreating(ModelBuilder builder)
    {
        base.OnModelCreating(builder);
        // Configuraciones adicionales
    }
}

// 2. Entidad de usuario custom
public class ApplicationUser : IdentityUser
{
    [MaxLength(100)]
    public string FullName { get; set; } = string.Empty;

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime? LastLoginAt { get; set; }
    public bool IsActive { get; set; } = true;
}
```

### Registro en Program.cs

```csharp
builder.Services.AddDbContext<AppIdentityDbContext>(options =>
    options.UseSqlServer(builder.Configuration.GetConnectionString("Identity")));

builder.Services.AddIdentity<ApplicationUser, IdentityRole>(options =>
{
    // Password
    options.Password.RequiredLength = 12;
    options.Password.RequiredUniqueChars = 3;
    options.Password.RequireDigit = true;
    options.Password.RequireLowercase = true;
    options.Password.RequireUppercase = true;
    options.Password.RequireNonAlphanumeric = true;

    // Lockout
    options.Lockout.DefaultLockoutTimeSpan = TimeSpan.FromMinutes(15);
    options.Lockout.MaxFailedAccessAttempts = 5;
    options.Lockout.AllowedForNewUsers = true;

    // User
    options.User.RequireUniqueEmail = true;
    options.User.AllowedUserNameCharacters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-@";

    // SignIn
    options.SignIn.RequireConfirmedEmail = true;
    options.SignIn.RequireConfirmedAccount = true;
})
.AddEntityFrameworkStores<AppIdentityDbContext>()
.AddDefaultTokenProviders()
.AddSignInManager<SignInManager<ApplicationUser>>();

// Cookies seguras
builder.Services.ConfigureApplicationCookie(options =>
{
    options.Cookie.Name = ".MiApp.Auth";
    options.Cookie.HttpOnly = true;
    options.Cookie.SecurePolicy = CookieSecurePolicy.Always;
    options.Cookie.SameSite = SameSiteMode.Strict;
    options.ExpireTimeSpan = TimeSpan.FromHours(1);
    options.SlidingExpiration = true;
    options.LoginPath = "/Account/Login";
    options.LogoutPath = "/Account/Logout";
    options.AccessDeniedPath = "/Account/AccessDenied";
});
```

---

## Registro y Login

### Razor Pages con Identity

```csharp
public class RegisterModel : PageModel
{
    private readonly UserManager<ApplicationUser> _userManager;
    private readonly SignInManager<ApplicationUser> _signInManager;
    private readonly IEmailSender _emailSender;

    [BindProperty]
    public RegisterInput Input { get; set; } = new();

    public async Task<IActionResult> OnPostAsync(CancellationToken ct)
    {
        if (!ModelState.IsValid) return Page();

        var user = new ApplicationUser
        {
            UserName = Input.Email,
            Email = Input.Email,
            FullName = Input.FullName,
            CreatedAt = DateTime.UtcNow
        };

        var result = await _userManager.CreateAsync(user, Input.Password);
        if (!result.Succeeded)
        {
            foreach (var error in result.Errors)
                ModelState.AddModelError(string.Empty, error.Description);
            return Page();
        }

        // Email confirmation
        var token = await _userManager.GenerateEmailConfirmationTokenAsync(user);
        var callbackUrl = Url.Page(
            "/Account/ConfirmEmail",
            pageHandler: null,
            values: new { userId = user.Id, token },
            protocol: Request.Scheme)!;

        await _emailSender.SendEmailAsync(Input.Email, "Confirm your email",
            $"Please confirm your account by <a href='{callbackUrl}'>clicking here</a>.");

        return RedirectToPage("RegisterConfirmation");
    }
}

public class LoginModel : PageModel
{
    private readonly SignInManager<ApplicationUser> _signInManager;
    private readonly ILogger<LoginModel> _logger;

    [BindProperty]
    public LoginInput Input { get; set; } = new();

    public async Task<IActionResult> OnPostAsync(string? returnUrl = null)
    {
        if (!ModelState.IsValid) return Page();

        var result = await _signInManager.PasswordSignInAsync(
            Input.Email, Input.Password, Input.RememberMe, lockoutOnFailure: true);

        if (result.Succeeded)
        {
            _logger.LogInformation("User {Email} logged in", Input.Email);
            return LocalRedirect(returnUrl ?? "/");
        }

        if (result.IsLockedOut)
        {
            _logger.LogWarning("User {Email} locked out", Input.Email);
            return RedirectToPage("./Lockout");
        }

        if (result.RequiresTwoFactor)
            return RedirectToPage("./LoginWith2fa", new { returnUrl, Input.RememberMe });

        if (result.IsNotAllowed)
            ModelState.AddModelError(string.Empty, "Email not confirmed. Check your inbox.");

        ModelState.AddModelError(string.Empty, "Invalid login attempt.");
        return Page();
    }
}
```

---

## External Providers

### Google, Microsoft, Facebook

```csharp
builder.Services.AddAuthentication()
    .AddGoogle(options =>
    {
        options.ClientId = builder.Configuration["Google:ClientId"]!;
        options.ClientSecret = builder.Configuration["Google:ClientSecret"]!;
        options.SaveTokens = true;
    })
    .AddMicrosoftAccount(options =>
    {
        options.ClientId = builder.Configuration["Microsoft:ClientId"]!;
        options.ClientSecret = builder.Configuration["Microsoft:ClientSecret"]!;
        options.SaveTokens = true;
    })
    .AddFacebook(options =>
    {
        options.AppId = builder.Configuration["Facebook:AppId"]!;
        options.AppSecret = builder.Configuration["Facebook:AppSecret"]!;
        options.SaveTokens = true;
    });

// En Login page: botones de provider
// <a asp-page="./ExternalLogin" asp-route-provider="Google" asp-route-returnUrl="@returnUrl">
//     Login with Google
// </a>
```

### External login handler

```csharp
public async Task<IActionResult> OnGetCallbackAsync(string? returnUrl = null, string? remoteError = null)
{
    if (remoteError is not null)
        return RedirectToPage("./Login", new { ReturnUrl = returnUrl });

    var info = await _signInManager.GetExternalLoginInfoAsync();
    if (info is null)
        return RedirectToPage("./Login");

    // Si el usuario ya existe
    var result = await _signInManager.ExternalLoginSignInAsync(
        info.LoginProvider, info.ProviderKey, isPersistent: false);

    if (result.Succeeded)
        return LocalRedirect(returnUrl ?? "/");

    // Si no existe: registrar con email del provider
    var email = info.Principal.FindFirstValue(ClaimTypes.Email);
    if (email is null)
        return RedirectToPage("./Login");

    var user = new ApplicationUser
    {
        UserName = email,
        Email = email,
        FullName = info.Principal.FindFirstValue(ClaimTypes.Name) ?? email,
        EmailConfirmed = true // Confiable porque viene del provider
    };

    var createResult = await _userManager.CreateAsync(user);
    if (!createResult.Succeeded)
        return RedirectToPage("./Login");

    await _userManager.AddLoginAsync(user, info);
    await _signInManager.SignInAsync(user, isPersistent: false);

    return LocalRedirect(returnUrl ?? "/");
}
```

---

## JWT Bearer para APIs

```csharp
builder.Services.AddAuthentication(options =>
{
    options.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
    options.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
})
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

    // Para SignalR: token por query string
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
```

---

## Autorización

### Políticas basadas en Claims

```csharp
builder.Services.AddAuthorization(options =>
{
    options.AddPolicy("AdminOnly", policy =>
        policy.RequireRole("Admin"));

    options.AddPolicy("OrdersRead", policy =>
        policy.RequireClaim("permissions", "orders:read"));

    options.AddPolicy("OrdersManage", policy =>
        policy.RequireClaim("permissions", "orders:create", "orders:update", "orders:delete"));

    options.AddPolicy("Over18", policy =>
        policy.RequireAssertion(context =>
            context.User.HasClaim(c =>
                c.Type == ClaimTypes.DateOfBirth &&
                DateTime.Parse(c.Value).AddYears(18) <= DateTime.UtcNow)));
});
```

### Resource-based Authorization

```csharp
public class OrderOwnerAuthorizationHandler
    : AuthorizationHandler<OperationAuthorizationRequirement, Order>
{
    protected override Task HandleRequirementAsync(
        AuthorizationHandlerContext context,
        OperationAuthorizationRequirement requirement,
        Order resource)
    {
        var userId = context.User.FindFirstValue(ClaimTypes.NameIdentifier);

        if (resource.CustomerId == userId || context.User.IsInRole("Admin"))
            context.Succeed(requirement);

        return Task.CompletedTask;
    }
}

// Registrar
builder.Services.AddScoped<IAuthorizationHandler, OrderOwnerAuthorizationHandler>();

// Uso
var canCancel = await _authorization.AuthorizeAsync(User, order, "Cancel");
if (!canCancel.Succeeded)
    return Forbid();
```

### Roles vs Claims vs Permissions

```csharp
// ❌ Solo roles: no escala
[Authorize(Roles = "Admin")]
public IActionResult Dashboard() { ... }

// ✅ Permissions: granular y configurable
[Authorize(Policy = "orders:read")]
public IActionResult GetOrder() { ... }

// ✅ Combinación de claims con políticas
// Policy: Requiere claim "permissions" con valor "orders:read"
// El token JWT incluye: "permissions": ["orders:read", "orders:create"]
```

---

## 2FA (Two-Factor Authentication)

```csharp
// Configurar TOTP (Authenticator App)
public async Task<IActionResult> OnGetEnableAuthenticatorAsync()
{
    var user = await _userManager.GetUserAsync(User);
    var unformattedKey = await _userManager.GetAuthenticatorKeyAsync(user);
    if (string.IsNullOrEmpty(unformattedKey))
    {
        await _userManager.ResetAuthenticatorKeyAsync(user);
        unformattedKey = await _userManager.GetAuthenticatorKeyAsync(user);
    }

    var email = await _userManager.GetEmailAsync(user);
    AuthenticatorUri = GenerateQrCodeUri(email!, unformattedKey!);

    return Page();
}

// Verificar y habilitar
public async Task<IActionResult> OnPostEnableAuthenticatorAsync(string verificationCode)
{
    var user = await _userManager.GetUserAsync(User);
    var isValid = await _userManager.VerifyTwoFactorTokenAsync(
        user, _userManager.Options.Tokens.AuthenticatorTokenProvider, verificationCode);

    if (!isValid)
    {
        ModelState.AddModelError("VerificationCode", "Invalid code");
        return Page();
    }

    await _userManager.SetTwoFactorEnabledAsync(user, true);
    await _signInManager.RefreshSignInAsync(user);

    RecoveryCodes = await _userManager.GenerateNewTwoFactorRecoveryCodesAsync(user, 10);
    return Page();
}
```

---

## Password Reset y Email Confirmation

```csharp
// Generar token para reset
public async Task<IActionResult> OnPostForgotPasswordAsync(ForgotPasswordInput input)
{
    var user = await _userManager.FindByEmailAsync(input.Email);
    if (user is null || !await _userManager.IsEmailConfirmedAsync(user))
        // No revelar si el email existe
        return RedirectToPage("./ForgotPasswordConfirmation");

    var token = await _userManager.GeneratePasswordResetTokenAsync(user);
    var callbackUrl = Url.Page(
        "/Account/ResetPassword",
        pageHandler: null,
        values: new { token, email = input.Email },
        protocol: Request.Scheme)!;

    await _emailSender.SendEmailAsync(input.Email, "Reset Password",
        $"Reset your password by <a href='{callbackUrl}'>clicking here</a>.");

    return RedirectToPage("./ForgotPasswordConfirmation");
}

// Reset password
public async Task<IActionResult> OnPostResetPasswordAsync(ResetPasswordInput input)
{
    var user = await _userManager.FindByEmailAsync(input.Email);
    if (user is null) return RedirectToPage("./ResetPasswordConfirmation");

    var result = await _userManager.ResetPasswordAsync(user, input.Token, input.Password);
    if (!result.Succeeded)
    {
        foreach (var error in result.Errors)
            ModelState.AddModelError(string.Empty, error.Description);
        return Page();
    }

    return RedirectToPage("./ResetPasswordConfirmation");
}
```

---

## Personalización de Claims

```csharp
public class CustomClaimsPrincipalFactory(
    UserManager<ApplicationUser> userManager,
    IOptions<IdentityOptions> optionsAccessor)
    : UserClaimsPrincipalFactory<ApplicationUser>(userManager, optionsAccessor)
{
    protected override async Task<ClaimsIdentity> GenerateClaimsAsync(ApplicationUser user)
    {
        var identity = await base.GenerateClaimsAsync(user);

        // Agregar claims de dominio
        identity.AddClaim(new Claim("full_name", user.FullName));
        identity.AddClaim(new Claim("created_at", user.CreatedAt.ToString("O")));

        // Cargar claims de roles con permisos
        var roles = await UserManager.GetRolesAsync(user);
        foreach (var role in roles)
            identity.AddClaim(new Claim(ClaimTypes.Role, role));

        return identity;
    }
}

// Registrar
builder.Services.AddScoped<IUserClaimsPrincipalFactory<ApplicationUser>, CustomClaimsPrincipalFactory>();
```

---

## Seguridad adicional

### Cambio de password invalida sesiones

```csharp
// Identity regenera SecurityStamp automáticamente al cambiar password.
// Validar stamp en cookie cada X minutos:
options.ValidationInterval = TimeSpan.FromMinutes(10);
```

### Protección contra account enumeration

```csharp
// En login: mismo mensaje genérico sin revelar si el usuario existe
if (result.Succeeded)
    return Redirect(returnUrl);

ModelState.AddModelError(string.Empty, "Invalid email or password");
// No: "Email not found" vs "Incorrect password"
```

### Login con Identity + JWT simultáneo (Cookies para web, JWT para API)

```csharp
builder.Services.AddAuthentication(options =>
{
    options.DefaultScheme = "Identity.Application"; // Prioriza cookies
})
.AddCookie("Identity.Application", options => { /* configuración cookies */ })
.AddJwtBearer("Identity.Bearer", options => { /* configuración JWT */ });

// En endpoint: elegir esquema
[Authorize(AuthenticationSchemes = "Identity.Bearer")]
```

---

## Checklist de Identity

- [ ] Password policy configurada (12+ chars, complejidad)
- [ ] Lockout configurado (5 intentos, 15 min)
- [ ] Email confirmation requerido (`RequireConfirmedEmail = true`)
- [ ] Cookies `HttpOnly`, `Secure`, `SameSite=Strict`
- [ ] 2FA disponible (Authenticator app)
- [ ] Recovery codes para 2FA
- [ ] Password reset sin enumeración de usuarios
- [ ] SecurityStamp validado periódicamente
- [ ] Claims custom para datos de dominio
- [ ] External providers configurados (Google, Microsoft)
- [ ] JWT con `ValidateLifetime = true`
- [ ] Políticas de autorización basadas en claims, no solo roles
- [ ] Resource-based authorization para recursos propios
- [ ] Anti-forgery configurado
- [ ] Datos sensibles no se loguean (passwords, tokens)
