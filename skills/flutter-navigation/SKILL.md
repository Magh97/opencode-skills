---
name: flutter-navigation
description: "Navegación en Flutter con GoRouter v17. Cubre rutas declarativas, deep linking (Universal Links, App Links), nested navigation (ShellRoute), guards de autenticación, paso de parámetros entre rutas, y transiciones personalizadas. Actívala al configurar navegación, implementar deep links, o proteger rutas con auth."
---

# Flutter Navigation — GoRouter v17

Guía de navegación con GoRouter v17.3 (2026). Deep linking nativo en móvil y web.

---

## Setup

```dart
// config/routes.dart
import 'package:go_router/go_router.dart';

final router = GoRouter(
  initialLocation: '/orders',
  routes: [
    GoRoute(
      path: '/login',
      builder: (context, state) => const LoginScreen(),
    ),
    ShellRoute(
      builder: (context, state, child) => AppShell(child: child),
      routes: [
        GoRoute(
          path: '/orders',
          builder: (context, state) => const OrdersListScreen(),
          routes: [
            GoRoute(
              path: 'create',
              builder: (context, state) => const CreateOrderScreen(),
            ),
            GoRoute(
              path: ':orderId',
              builder: (context, state) {
                final orderId = state.pathParameters['orderId']!;
                return OrderDetailScreen(orderId: orderId);
              },
            ),
          ],
        ),
        GoRoute(
          path: '/catalog',
          builder: (context, state) => const CatalogScreen(),
        ),
        GoRoute(
          path: '/settings',
          builder: (context, state) => const SettingsScreen(),
        ),
      ],
    ),
  ],
);
```

```dart
// main.dart
MaterialApp.router(
  routerConfig: router,
  theme: appTheme,
);
```

---

## Navegación

```dart
// ✅ Navegación declarativa
context.go('/orders');            // Reemplaza toda la pila
context.go('/orders/123');        // Con parámetro
context.push('/orders/create');   // Push en la pila
context.pop();                    // Volver atrás

// ✅ Navegación con parámetros nombrados
context.goNamed('order-detail', pathParameters: {'orderId': '123'});

// ✅ Navegación con query parameters
context.push('/orders?status=pending&page=2');

// Leer query params en el builder
final status = state.uri.queryParameters['status'];
```

---

## Deep Linking

### Android (App Links)

```xml
<!-- AndroidManifest.xml -->
<intent-filter android:autoVerify="true">
  <action android:name="android.intent.action.VIEW" />
  <category android:name="android.intent.category.DEFAULT" />
  <category android:name="android.intent.category.BROWSABLE" />
  <data android:scheme="https" android:host="miapp.com" android:pathPrefix="/orders" />
</intent-filter>
```

### iOS (Universal Links)

```json
// apple-app-site-association (en servidor)
{
  "applinks": {
    "details": [{
      "appID": "TEAM_ID.com.miapp.app",
      "paths": ["/orders/*"]
    }]
  }
}
```

### Flutter: GoRouter lo maneja automáticamente

```dart
// https://miapp.com/orders/123 → abre OrderDetailScreen(id: '123')
// https://miapp.com/orders/create → abre CreateOrderScreen
```

---

## Nested Navigation (ShellRoute)

```dart
// BottomNavigationBar + navegación independiente por tab
class AppShell extends StatelessWidget {
  const AppShell({super.key, required this.child});
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: child,  // Contenido de la ruta activa
      bottomNavigationBar: NavigationBar(
        selectedIndex: _calculateSelectedIndex(context),
        onDestinationSelected: (index) {
          switch (index) {
            case 0: context.go('/orders'); break;
            case 1: context.go('/catalog'); break;
            case 2: context.go('/settings'); break;
          }
        },
        destinations: const [
          NavigationDestination(icon: Icon(Icons.receipt), label: 'Órdenes'),
          NavigationDestination(icon: Icon(Icons.inventory), label: 'Catálogo'),
          NavigationDestination(icon: Icon(Icons.settings), label: 'Ajustes'),
        ],
      ),
    );
  }
}
```

---

## Auth Guard

```dart
final router = GoRouter(
  redirect: (context, state) {
    final isLoggedIn = AuthProvider.of(context).isLoggedIn;
    final isLoginRoute = state.matchedLocation == '/login';

    if (!isLoggedIn && !isLoginRoute) return '/login';
    if (isLoggedIn && isLoginRoute) return '/orders';
    return null;  // No redirect
  },
  routes: [...],
);
```

---

## Transiciones personalizadas

```dart
GoRoute(
  path: '/orders/create',
  pageBuilder: (context, state) => CustomTransitionPage(
    key: state.pageKey,
    child: const CreateOrderScreen(),
    transitionsBuilder: (context, animation, secondaryAnimation, child) {
      return SlideTransition(
        position: Tween<Offset>(
          begin: const Offset(0, 1),
          end: Offset.zero,
        ).animate(CurvedAnimation(
          parent: animation,
          curve: Curves.easeOut,
        )),
        child: child,
      );
    },
  ),
)
```

---

## Checklist navegación

- [ ] GoRouter v17 con rutas declarativas
- [ ] ShellRoute para BottomNavigationBar
- [ ] Deep links configurados (Android App Links + iOS Universal Links)
- [ ] Auth guard con `redirect`
- [ ] Parámetros de ruta (`:orderId`) y query params
- [ ] `context.pop()` con resultado (si aplica)
- [ ] Transiciones consistentes (slide up para modales, slide right para push)
