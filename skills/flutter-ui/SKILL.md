---
name: flutter-ui
description: "UI en Flutter con Material 3. Cubre temas, diseño responsive (LayoutBuilder, MediaQuery), formularios avanzados, animaciones (AnimationController, Hero, staggered), y componentes reutilizables. Actívala al diseñar pantallas, crear Design System, o implementar animaciones."
---

# Flutter UI & Material 3

Guía de UI en Flutter 3.44. Material 3, responsive, formularios, animaciones.

---

## Material 3 Theme

```dart
MaterialApp(
  theme: ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: const Color(0xFF1677FF),  // Primary
      brightness: Brightness.light,
    ),
    inputDecorationTheme: InputDecorationTheme(
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        minimumSize: const Size(double.infinity, 48),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      ),
    ),
    cardTheme: CardTheme(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
    ),
  ),
  home: const OrdersPage(),
);
```

---

## Responsive

```dart
// ✅ LayoutBuilder (reacciona a constraints del padre)
LayoutBuilder(
  builder: (context, constraints) {
    if (constraints.maxWidth > 600) {
      return const TwoColumnLayout();  // Tablet/desktop
    }
    return const SingleColumnLayout();  // Phone
  },
)

// ✅ MediaQuery (tamaño de pantalla)
final size = MediaQuery.of(context).size;
final isLandscape = size.width > size.height;
final padding = MediaQuery.of(context).padding;  // Notch, status bar

// ✅ OrientationBuilder
OrientationBuilder(
  builder: (context, orientation) {
    if (orientation == Orientation.landscape) {
      return const Row(children: [FormSection(), PreviewSection()]);
    }
    return const Column(children: [FormSection(), PreviewSection()]);
  },
)
```

---

## Formularios avanzados

```dart
class CreateOrderScreen extends StatefulWidget {
  const CreateOrderScreen({super.key});
  @override
  State<CreateOrderScreen> createState() => _CreateOrderScreenState();
}

class _CreateOrderScreenState extends State<CreateOrderScreen> {
  final _formKey = GlobalKey<FormState>();
  final _customerController = TextEditingController();
  final _amountController = TextEditingController();
  String _currency = 'MXN';
  final List<_OrderItem> _items = [];
  bool _isSubmitting = false;

  void _addItem() {
    setState(() => _items.add(_OrderItem()));
  }

  void _removeItem(int index) {
    setState(() => _items.removeAt(index));
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _isSubmitting = true);
    try {
      final input = CreateOrderInput(
        customerId: _customerController.text,
        amount: double.parse(_amountController.text),
        currency: _currency,
        items: _items.map((i) => OrderItemInput(
          sku: i.skuController.text,
          quantity: int.parse(i.qtyController.text),
        )).toList(),
      );
      await context.read<OrderBloc>().add(CreateOrder(input));
      if (mounted) Navigator.of(context).pop();
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Nueva Orden')),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            TextFormField(
              controller: _customerController,
              decoration: const InputDecoration(labelText: 'ID del Cliente'),
              validator: (v) => v == null || v.isEmpty ? 'Requerido' : null,
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _amountController,
              decoration: const InputDecoration(labelText: 'Monto'),
              keyboardType: TextInputType.number,
              validator: _validateAmount,
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              value: _currency,
              items: const [
                DropdownMenuItem(value: 'MXN', child: Text('MXN')),
                DropdownMenuItem(value: 'USD', child: Text('USD')),
              ],
              onChanged: (v) => setState(() => _currency = v!),
            ),
            const SizedBox(height: 16),
            Text('Ítems', style: Theme.of(context).textTheme.titleMedium),
            ..._items.asMap().entries.map((entry) => _buildItemRow(entry.key, entry.value)),
            TextButton.icon(
              onPressed: _addItem,
              icon: const Icon(Icons.add),
              label: const Text('Agregar ítem'),
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: _isSubmitting ? null : _submit,
              child: Text(_isSubmitting ? 'Creando...' : 'Crear Orden'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildItemRow(int index, _OrderItem item) {
    return Row(children: [
      Expanded(
        child: TextFormField(
          controller: item.skuController,
          decoration: const InputDecoration(labelText: 'SKU'),
        ),
      ),
      const SizedBox(width: 8),
      SizedBox(
        width: 80,
        child: TextFormField(
          controller: item.qtyController,
          decoration: const InputDecoration(labelText: 'Cant'),
          keyboardType: TextInputType.number,
        ),
      ),
      IconButton(
        icon: const Icon(Icons.remove_circle_outline),
        onPressed: () => _removeItem(index),
      ),
    ]);
  }
}

class _OrderItem {
  final skuController = TextEditingController();
  final qtyController = TextEditingController(text: '1');
}
```

---

## Animaciones

```dart
// ✅ Hero (transición entre pantallas)
Hero(
  tag: 'order-${order.id}',
  child: OrderCard(order: order),
)

// ✅ AnimatedContainer (transiciones simples)
AnimatedContainer(
  duration: const Duration(milliseconds: 300),
  curve: Curves.easeInOut,
  height: _expanded ? 200 : 60,
  color: _expanded ? Colors.blue.shade50 : Colors.white,
  child: ...,
)

// ✅ Staggered animations (secuencia)
class _OrderDetailState extends State<OrderDetailScreen>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _fadeIn;
  late final Animation<Offset> _slideIn;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 600),
      vsync: this,
    );
    _fadeIn = Tween(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: const Interval(0, 0.5)),
    );
    _slideIn = Tween(begin: const Offset(0, 0.05), end: Offset.zero).animate(
      CurvedAnimation(parent: _controller, curve: const Interval(0.3, 1.0)),
    );
    _controller.forward();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _fadeIn,
      child: SlideTransition(position: _slideIn, child: ...),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }
}
```

---

## Checklist UI

- [ ] Material 3 (`useMaterial3: true`) con `ColorScheme.fromSeed`
- [ ] `LayoutBuilder` para responsive (phone vs tablet)
- [ ] Formularios con `Form` + `TextFormField` + validación
- [ ] `Hero` para transiciones entre pantallas
- [ ] `AnimatedContainer`/`AnimatedOpacity` para micro-interacciones
- [ ] Temas de texto con `Theme.of(context).textTheme`
- [ ] Botones con tamaño mínimo 48px (accesibilidad touch)
