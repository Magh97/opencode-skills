---
name: design-api
description: "Diseño de APIs contract-first con OpenAPI como fuente de verdad. Cubre RESTful design, versionado, paginación, manejo de errores, security schemes y HATEOAS opcional. Actívala al diseñar una API nueva, definir contratos entre backend y frontend, o cuando el usuario diga 'diseñar API', 'API contract', 'OpenAPI first', 'diseñar endpoints', 'API REST'."
---

# Design API — Contratos API-First

La API es el contrato entre frontend y backend. Diseñar el contrato antes que cualquiera de los dos.

---

## Principios API-first

1. **El contrato es fuente de verdad.** OpenAPI spec antes que código.
2. **Un endpoint = una responsabilidad.** No hagas `/api/orders?include=items,customer,payments,tracking` — mejor endpoints separados o GraphQL si realmente necesitas esa flexibilidad.
3. **Consistencia ante todo.** Mismo formato de error, mismos nombres de campos, mismas convenciones en toda la API.
4. **Versionado desde día 1.** Aunque solo tengas v1. Cambiar contratos sin versionar rompe clientes.
5. **Paginación siempre en listas.** Nunca devuelvas arrays sin límite.

---

## RESTful design — convenciones

### URLs

```
✅ GET    /api/orders          → Lista de órdenes
✅ GET    /api/orders/{id}     → Una orden específica
✅ POST   /api/orders          → Crear orden
✅ PUT    /api/orders/{id}     → Reemplazar orden completa
✅ PATCH  /api/orders/{id}     → Actualización parcial
✅ DELETE /api/orders/{id}     → Eliminar orden

✅ POST   /api/orders/{id}/cancel  → Acción (cuando no es CRUD puro)

❌ GET    /api/getOrders
❌ POST   /api/orders/create
❌ GET    /api/orders?id=123         → usar path param
```

### Recursos anidados (máximo 1 nivel)

```
✅ GET /api/orders/{id}/items        → Items de una orden
✅ GET /api/orders/{id}/items/{iid}  → Item específico

❌ GET /api/customers/{id}/orders/{oid}/items/{iid}  → demasiada profundidad
```

---

## Formato de respuesta estándar

```json
// ✅ Éxito (singular)
{
  "data": {
    "id": 42,
    "status": "pending",
    "total": 1500.00,
    "createdAt": "2026-06-23T15:30:00Z"
  }
}

// ✅ Éxito (colección paginada)
{
  "data": [ ... ],
  "meta": {
    "page": 1,
    "pageSize": 20,
    "totalItems": 156,
    "totalPages": 8
  }
}

// ✅ Error
{
  "error": {
    "code": "ORDER_NOT_FOUND",
    "message": "La orden con ID 999 no existe",
    "details": [
      {
        "field": "orderId",
        "reason": "No se encontró ninguna orden con ese identificador"
      }
    ]
  }
}
```

---

## Paginación

### Offset (default, para la mayoría de casos)

```
GET /api/orders?page=1&pageSize=20
```

- Simple de implementar, funciona con `OFFSET/LIMIT`.
- **No usar** para datos en tiempo real o feeds donde se insertan items entre requests (causa duplicados/huecos).

### Cursor-based (para feeds, timelines, datos en tiempo real)

```
GET /api/orders?cursor=eyJpZCI6NDJ9&limit=20
```

- El cursor es opaco (base64 de un objeto tipo `{id: 42}`).
- La respuesta incluye `nextCursor` para la siguiente página.

### Response header vs body

✅ En el body (más fácil para el frontend, visible en DevTools).
❌ En headers `X-Total-Count`, `Link` — más "REST puro" pero incómodo de consumir.

---

## Versionado

| Estrategia | Ejemplo | Cuándo |
|-----------|---------|--------|
| **URL path** (recomendado) | `/api/v1/orders` | Más explícito, fácil de routear |
| **Header** | `Accept: application/vnd.miapp.v1+json` | Más REST puro, pero menos visible |
| **Query param** | `/api/orders?version=1` | No recomendado (caching issues) |

**Regla:** Prefiere URL path. Es el más fácil de entender y debuggear.

---

## HTTP Status Codes — los que realmente usarás

| Código | Cuándo |
|--------|--------|
| `200 OK` | GET, PUT, PATCH exitoso |
| `201 Created` | POST que crea recurso. Incluir `Location` header con URL del nuevo recurso |
| `204 No Content` | DELETE exitoso, o POST sin body de respuesta |
| `400 Bad Request` | Validación fallida (body mal formado, campo requerido faltante) |
| `401 Unauthorized` | Sin token o token inválido/expirado |
| `403 Forbidden` | Token válido pero sin permisos para este recurso |
| `404 Not Found` | Recurso no existe (o no deberías saber que existe por seguridad) |
| `409 Conflict` | Violación de regla de negocio (ej: orden ya cancelada) |
| `422 Unprocessable Entity` | Validación de negocio (body válido sintácticamente pero no semánticamente) |
| `429 Too Many Requests` | Rate limit |
| `500 Internal Server Error` | Error inesperado. No exponer stack trace. |

---

## OpenAPI 3.1 boilerplate

```yaml
openapi: "3.1.0"
info:
  title: Órdenes API
  version: "1.0.0"
  description: API de gestión de órdenes de compra.

servers:
  - url: https://api.miapp.com/v1
    description: Producción
  - url: https://staging.miapp.com/v1
    description: Staging

paths:
  /orders:
    get:
      summary: Listar órdenes
      operationId: listOrders
      tags: [Orders]
      parameters:
        - name: page
          in: query
          schema: { type: integer, default: 1 }
        - name: pageSize
          in: query
          schema: { type: integer, default: 20, maximum: 100 }
        - name: status
          in: query
          schema:
            type: string
            enum: [pending, confirmed, paid, cancelled]
      responses:
        "200":
          description: Lista paginada de órdenes
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/OrderListResponse"
        "401":
          $ref: "#/components/responses/Unauthorized"

    post:
      summary: Crear orden
      operationId: createOrder
      tags: [Orders]
      security: [{ bearerAuth: [] }]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/CreateOrderRequest"
      responses:
        "201":
          description: Orden creada
          headers:
            Location:
              schema: { type: string }
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/OrderResponse"
        "400":
          $ref: "#/components/responses/ValidationError"

  /orders/{orderId}:
    get:
      summary: Obtener orden
      operationId: getOrderById
      tags: [Orders]
      parameters:
        - name: orderId
          in: path
          required: true
          schema: { type: integer }
      responses:
        "200":
          description: Orden encontrada
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/OrderResponse"
        "404":
          $ref: "#/components/responses/NotFound"

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    OrderListResponse:
      type: object
      required: [data, meta]
      properties:
        data:
          type: array
          items:
            $ref: "#/components/schemas/OrderResponse"
        meta:
          $ref: "#/components/schemas/PaginationMeta"

    OrderResponse:
      type: object
      required: [id, status, total, createdAt]
      properties:
        id: { type: integer }
        status: { type: string, enum: [pending, confirmed, paid, shipped, delivered, cancelled] }
        total: { type: number }
        createdAt: { type: string, format: date-time }
        items:
          type: array
          items:
            $ref: "#/components/schemas/OrderItemResponse"

    CreateOrderRequest:
      type: object
      required: [items]
      properties:
        items:
          type: array
          minItems: 1
          items:
            type: object
            required: [productId, quantity]
            properties:
              productId: { type: integer }
              quantity: { type: integer, minimum: 1 }

    PaginationMeta:
      type: object
      properties:
        page: { type: integer }
        pageSize: { type: integer }
        totalItems: { type: integer }
        totalPages: { type: integer }

  responses:
    Unauthorized:
      description: No autenticado
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/ErrorResponse"
    NotFound:
      description: Recurso no encontrado
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/ErrorResponse"
    ValidationError:
      description: Error de validación
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/ErrorResponse"

    ErrorResponse:
      type: object
      required: [error]
      properties:
        error:
          type: object
          required: [code, message]
          properties:
            code: { type: string }
            message: { type: string }
            details:
              type: array
              items:
                type: object
                properties:
                  field: { type: string }
                  reason: { type: string }
```

---

## Workflow

1. **Recibe el contexto** (desde spec, design doc, o directo del usuario).
2. **Identifica los recursos** principales (Orders, Products, Customers...).
3. **Define operaciones CRUD + acciones** para cada recurso.
4. **Genera el contrato OpenAPI** completo con schemas, respuestas, errores y security.
5. **Revisa con el usuario:** "¿Falta algún endpoint? ¿Los campos son los correctos?"
6. **Guarda el archivo** `docs/api/openapi.yaml` o `docs/API.md` según prefiera el usuario.

---

## Lo que NO debe hacer

- No diseñar endpoints que el MVP no necesita (YAGNI aplica a APIs también).
- No mezclar estilos (REST + RPC en el mismo recurso).
- No usar status codes exóticos (418 I'm a teapot). Los 8 listados cubren todo.
- No exponer IDs internos si no son necesarios para el cliente.

## Stack-specific

Para mapear el diseño OpenAPI a implementación, carga el dev-kit del backend:
- .NET → `dotnet-api` (Minimal APIs o Controllers + OpenAPI nativo)
- Node.js → `nodejs-express` (Express + swagger-jsdoc o Zod + OpenAPI)
- Python → `python-fastapi` (FastAPI genera OpenAPI automáticamente desde Pydantic)
