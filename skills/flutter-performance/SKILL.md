---
name: flutter-performance
description: "Rendimiento en Flutter. Cubre const widgets, RepaintBoundary, lazy loading (ListView.builder), DevTools profiling, memory leaks, isolate para tareas pesadas, y reducción de rebuilds. Actívala al optimizar pantallas lentas, reducir jank, o perfilar la app."
---

# Flutter Performance

Guía de rendimiento Flutter. 60fps en todo momento. Medir antes de optimizar.

---

## const widgets — la optimización #1

```dart
// ❌ Sin const — se reconstruye en cada build del padre
Padding(
  padding: EdgeInsets.all(16),
  child: Text('Hola'),
)

// ✅ Con const — creado una vez en tiempo de compilación, nunca se reconstruye
const Padding(
  padding: EdgeInsets.all(16),
  child: Text('Hola'),
)

// ✅ const en constructores de widgets propios
class OrderCard extends StatelessWidget {
  final Order order;
  const OrderCard({super.key, required this.order});  // ← const constructor
}
// Uso: const OrderCard(order: myOrder) — si order también es const
```

---

## Reducir rebuilds

```dart
// ❌ setState en todo el árbol
setState(() {
  _selectedIndex = index;  // Solo cambia un ícono, pero reconstruye toda la pantalla
});

// ✅ Extraer la parte que cambia a su propio widget
class _SelectableTab extends StatelessWidget {
  final bool isSelected;
  const _SelectableTab({required this.isSelected});

  @override
  Widget build(BuildContext context) {
    return Icon(
      Icons.receipt,
      color: isSelected ? Colors.blue : Colors.grey,
    );
  }
}

// ✅ Selector en Riverpod (solo rebuild si cambia ese campo)
final count = ref.watch(orderListProvider.select((value) => value.length));

// ✅ BlocBuilder con buildWhen (condición para rebuild)
BlocBuilder<OrderBloc, OrderState>(
  buildWhen: (prev, curr) => curr is OrdersLoaded,  // Solo rebuild en datos nuevos
  builder: (context, state) => ...,
)
```

---

## RepaintBoundary

```dart
// ✅ Aísla widgets que se repintan frecuentemente (animaciones, scroll)
RepaintBoundary(
  child: AnimatedChart(),  // Su repaint no afecta al resto de la pantalla
)
```

---

## ListView.builder (lazy loading)

```dart
// ❌ ListView(children: [...]) — construye todos los widgets, incluso los no visibles
ListView(children: orders.map((o) => OrderCard(order: o)).toList())

// ✅ ListView.builder — construye solo los visibles
ListView.builder(
  itemCount: orders.length,
  itemExtent: 72,  // Altura fija (mejor rendimiento que estimar)
  itemBuilder: (context, index) => OrderCard(order: orders[index]),
)

// ✅ ListView.separated — con separadores
ListView.separated(
  itemCount: orders.length,
  separatorBuilder: (_, __) => const Divider(height: 1),
  itemBuilder: (context, index) => OrderCard(order: orders[index]),
)
```

---

## Isolate (tareas pesadas sin bloquear UI)

```dart
// ✅ compute() para parsing de JSON grande o cálculos pesados
final orders = await compute(parseOrdersJson, response.data);

List<Order> parseOrdersJson(dynamic data) {
  final list = data as List;
  return list.map((j) => Order.fromJson(j)).toList();
}

// ✅ Isolate para tareas más complejas
import 'dart:isolate';

Future<void> processInBackground() async {
  final receivePort = ReceivePort();
  await Isolate.spawn(_heavyTask, receivePort.sendPort);
  final result = await receivePort.first;
}

void _heavyTask(SendPort sendPort) {
  // Tarea CPU-intensiva
  final result = complexCalculation();
  Isolate.exit(sendPort, result);
}
```

---

## DevTools

```bash
flutter run --profile  # Modo perfil (cercano a producción)
# Abrir DevTools en el navegador
flutter pub global run devtools
```

En DevTools:
- **Performance**: ver rebuilds, builds, layouts
- **CPU Profiler**: qué funciones consumen más tiempo
- **Memory**: leaks, snapshots
- **Widget Inspector**: qué widgets se están reconstruyendo

---

## Memory leaks

```dart
// ❌ Controller no dispuesto
class _MyScreenState extends State<MyScreen> {
  final _controller = TextEditingController();  // ❌ Nunca se hace dispose

  @override
  void dispose() {
    _controller.dispose();  // ✅ Siempre disponer controllers
    super.dispose();
  }
}

// ❌ Stream subscription no cancelada
late StreamSubscription _subscription;
@override
void initState() {
  super.initState();
  _subscription = stream.listen((data) { ... });
}
@override
void dispose() {
  _subscription.cancel();  // ✅ Cancelar subscription
  super.dispose();
}
```

---

## Imágenes optimizadas

```dart
// ✅ cacheWidth / cacheHeight (decodifica a tamaño exacto, ahorra memoria)
Image.network(
  url,
  cacheWidth: 200,
  cacheHeight: 150,
)

// ✅ cached_network_image (caché en disco)
CachedNetworkImage(
  imageUrl: url,
  placeholder: (_, __) => const SizedBox(width: 200, height: 150),
  errorWidget: (_, __, ___) => const Icon(Icons.error),
)

// ✅ fadeIn de placeholder
FadeInImage.assetNetwork(
  placeholder: 'assets/placeholder.png',
  image: url,
  width: 200, height: 150, fit: BoxFit.cover,
)
```

---

## Checklist performance

- [ ] `const` en todo widget y constructor que no dependa de estado
- [ ] `ListView.builder` para listas (nunca `ListView(children: [...])`)
- [ ] `itemExtent` en listas con altura fija
- [ ] `RepaintBoundary` para widgets con repaint frecuente
- [ ] `compute()` para parsing de JSON grande o cálculos pesados
- [ ] Controllers + subscriptions dispuestos en `dispose()`
- [ ] Imágenes con `cacheWidth`/`cacheHeight` o `cached_network_image`
- [ ] Perfilar con DevTools antes y después de optimizar
