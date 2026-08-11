---
name: flutter-networking
description: "Networking en Flutter con Dio. Cubre REST API calls, interceptors, autenticación (Bearer token), manejo de errores, caching de respuestas, WebSocket, y file upload. Actívala al implementar llamadas HTTP, configurar capa de red, o integrar con APIs REST."
---

# Flutter Networking — Dio

Guía de networking con Dio. Cliente HTTP para Flutter con interceptors, retry, caching.

---

## Setup

```bash
flutter pub add dio
```

```dart
// shared/http_client.dart
import 'package:dio/dio.dart';

Dio createDio({required String baseUrl, String? token}) {
  final dio = Dio(BaseOptions(
    baseUrl: baseUrl,
    connectTimeout: const Duration(seconds: 10),
    receiveTimeout: const Duration(seconds: 30),
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
  ));

  // Interceptor: auth token
  dio.interceptors.add(InterceptorsWrapper(
    onRequest: (options, handler) {
      if (token != null) {
        options.headers['Authorization'] = 'Bearer $token';
      }
      handler.next(options);
    },
    onError: (error, handler) {
      if (error.response?.statusCode == 401) {
        // Token expirado → refresh y reintentar
      }
      handler.next(error);
    },
  ));

  // Interceptor: logging (solo en debug)
  if (kDebugMode) {
    dio.interceptors.add(LogInterceptor(
      requestBody: true,
      responseBody: true,
    ));
  }

  return dio;
}
```

---

## Repository pattern

```dart
// modules/orders/repositories/order_repository.dart
class OrderRepository {
  final Dio _dio;

  OrderRepository(this._dio);

  // ✅ GET con parámetros
  Future<List<Order>> getByCustomer(String customerId, {int page = 1}) async {
    final response = await _dio.get('/api/orders', queryParameters: {
      'customerId': customerId,
      'page': page,
      'pageSize': 20,
    });
    final data = response.data as Map<String, dynamic>;
    return (data['data'] as List).map((j) => Order.fromJson(j)).toList();
  }

  // ✅ GET por ID
  Future<Order> getById(String id) async {
    final response = await _dio.get('/api/orders/$id');
    return Order.fromJson(response.data);
  }

  // ✅ POST con body
  Future<Order> create(CreateOrderInput input) async {
    final response = await _dio.post('/api/orders', data: input.toJson());
    return Order.fromJson(response.data);
  }

  // ✅ PUT
  Future<Order> update(String id, UpdateOrderInput input) async {
    final response = await _dio.put('/api/orders/$id', data: input.toJson());
    return Order.fromJson(response.data);
  }

  // ✅ DELETE
  Future<void> cancel(String id) async {
    await _dio.delete('/api/orders/$id');
  }
}
```

---

## Manejo de errores

```dart
// shared/exceptions.dart
class AppException implements Exception {
  final String message;
  final int? statusCode;

  AppException(this.message, [this.statusCode]);
}

class NetworkException extends AppException {
  NetworkException() : super('Sin conexión. Verifique su red.');
}

class ServerException extends AppException {
  ServerException({required String message, int? statusCode})
      : super(message, statusCode);
}

// Interceptor de errores
dio.interceptors.add(InterceptorsWrapper(
  onError: (error, handler) {
    if (error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.receiveTimeout) {
      return handler.reject(DioException(
        requestOptions: error.requestOptions,
        error: NetworkException(),
      ));
    }

    final statusCode = error.response?.statusCode ?? 0;
    final message = error.response?.data?['error']?['message'] ?? 'Error inesperado';

    return handler.reject(DioException(
      requestOptions: error.requestOptions,
      error: ServerException(message: message, statusCode: statusCode),
    ));
  },
));

// Uso en Riverpod
@riverpod
Future<List<Order>> orderList(OrderListRef ref, {required String customerId}) async {
  try {
    return await ref.read(orderRepositoryProvider).getByCustomer(customerId);
  } on NetworkException {
    throw 'Sin conexión a internet';
  } on ServerException catch (e) {
    throw e.message;
  }
}
```

---

## File Upload

```dart
Future<String> uploadFile(File file) async {
  final formData = FormData.fromMap({
    'file': await MultipartFile.fromFile(
      file.path,
      filename: file.uri.pathSegments.last,
    ),
  });

  // Con progreso
  final response = await _dio.post(
    '/api/upload',
    data: formData,
    onSendProgress: (sent, total) {
      final progress = (sent / total * 100).round();
      print('Upload: $progress%');
    },
  );

  return response.data['url'];
}
```

---

## Caching de respuestas

```dart
// Simple cache en memoria con TTL
class CacheManager {
  final _cache = <String, _CacheEntry>{};
  static const _defaultTtl = Duration(minutes: 5);

  T? get<T>(String key) {
    final entry = _cache[key];
    if (entry == null) return null;
    if (DateTime.now().difference(entry.timestamp) > entry.ttl) {
      _cache.remove(key);
      return null;
    }
    return entry.data as T;
  }

  void set<T>(String key, T data, {Duration? ttl}) {
    _cache[key] = _CacheEntry(data, ttl ?? _defaultTtl);
  }
}

// Repository con cache
Future<List<Order>> getByCustomer(String customerId) async {
  final cacheKey = 'orders_$customerId';
  final cached = _cache.get<List<Order>>(cacheKey);
  if (cached != null) return cached;

  final response = await _dio.get('/api/orders', queryParameters: {'customerId': customerId});
  final orders = (response.data['data'] as List).map((j) => Order.fromJson(j)).toList();

  _cache.set(cacheKey, orders);
  return orders;
}
```

---

## Checklist networking

- [ ] Dio con `BaseOptions` (timeouts, headers)
- [ ] Interceptor de auth (Bearer token)
- [ ] Interceptor de errores (NetworkException, ServerException)
- [ ] Repository pattern (no llamar Dio directamente desde widgets)
- [ ] File upload con `MultipartFile` + progreso
- [ ] Cache TTL para respuestas que no cambian frecuentemente
- [ ] Logging solo en debug (`LogInterceptor` condicional)
