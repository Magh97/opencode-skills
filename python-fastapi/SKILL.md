---
name: python-fastapi
description: "APIs REST con FastAPI y Pydantic v2. Cubre routers, dependency injection, middleware, validación automática, OpenAPI/Swagger, background tasks, WebSockets, lifespan events, y patrones de organización. Actívala al diseñar APIs HTTP en Python, implementar endpoints REST, o migrar de Flask/Django REST a FastAPI."
disable-model-invocation: true
---

# FastAPI Guide

Guía de APIs con FastAPI + Pydantic v2. Framework async moderno para Python con validación automática y OpenAPI.

---

## Setup

```bash
uv add fastapi uvicorn[standard] pydantic
```

```python
# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()

app = FastAPI(
    title="MiApp API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}
```

---

## Routers

```python
# modules/orders/router.py
from fastapi import APIRouter, Depends, status
from .service import OrderService
from .schemas import OrderCreate, OrderResponse, OrderListParams

router = APIRouter(prefix="/api/orders", tags=["Orders"])

@router.get("/", response_model=list[OrderResponse])
async def list_orders(
    params: OrderListParams = Depends(),
    service: OrderService = Depends(),
):
    return await service.list(params)

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    body: OrderCreate,
    service: OrderService = Depends(),
):
    return await service.create(body)

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    service: OrderService = Depends(),
):
    order = await service.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

# main.py — registrar
app.include_router(orders_router)
```

---

## Dependency Injection

```python
# shared/deps.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .database import async_session_factory

async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        yield session

# Uso en router
@router.get("/")
async def list_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    orders = await order_repo.find_by_customer(db, current_user.id)
    return orders

# Dependencia con parámetros
def get_order_service(
    db: AsyncSession = Depends(get_db),
) -> OrderService:
    repo = OrderRepository(db)
    return OrderService(repo)

# Dependencias encadenadas
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(token)
    user = await get_user_by_id(db, payload.sub)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user
```

---

## Pydantic Schemas

```python
# modules/orders/schemas.py
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from uuid import UUID
from enum import StrEnum

class OrderStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class OrderCreate(BaseModel):
    customer_id: str = Field(..., min_length=1, max_length=50)
    amount: float = Field(..., gt=0, le=9_999_999)
    currency: str = Field(default="MXN", pattern=r"^[A-Z]{3}$")
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("customer_id")
    @classmethod
    def strip_upper(cls, v: str) -> str:
        return v.strip().upper()

class OrderResponse(BaseModel):
    id: UUID
    order_number: int
    customer_id: str
    status: OrderStatus
    total_amount: float
    currency: str
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}  # Permite ORM mode

class OrderListParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    status: OrderStatus | None = None
    sort_by: str = Field(default="created_at")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")
```

---

## Error handling

```python
# shared/exceptions.py
class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = "ERROR"):
        self.message = message
        self.status_code = status_code
        self.code = code

class NotFoundError(AppException):
    def __init__(self, resource: str):
        super().__init__(
            message=f"{resource} not found",
            status_code=404,
            code="NOT_FOUND",
        )

# shared/error_handlers.py
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"message": exc.message, "code": exc.code}},
    )

@app.exception_handler(ValidationError)
async def validation_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": {"message": "Validation failed", "details": exc.errors()}},
    )
```

---

## Middleware

```python
from fastapi import Request
import time
import uuid

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
    request.state.request_id = request_id

    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start

    response.headers["X-Request-Id"] = request_id
    response.headers["X-Response-Time"] = f"{duration:.3f}s"
    return response
```

---

## Background Tasks

```python
from fastapi import BackgroundTasks

@router.post("/")
async def create_order(
    body: OrderCreate,
    background_tasks: BackgroundTasks,
    service: OrderService = Depends(),
):
    order = await service.create(body)
    background_tasks.add_task(send_confirmation_email, order.id)
    background_tasks.add_task(publish_order_event, order)
    return order

# Para tareas pesadas/largas → Celery, no BackgroundTasks
```

---

## File Upload

```python
from fastapi import UploadFile, File

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if file.content_type not in ("image/jpeg", "image/png", "application/pdf"):
        raise HTTPException(status_code=400, detail="Invalid file type")

    if file.size and file.size > 10 * 1024 * 1024:  # 10 MB
        raise HTTPException(status_code=400, detail="File too large")

    contents = await file.read()
    file_path = f"uploads/{uuid.uuid4()}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(contents)

    return {"filename": file.filename, "path": file_path, "size": len(contents)}
```

---

## OpenAPI / Swagger

FastAPI genera OpenAPI automáticamente desde Pydantic schemas y tipos.

```
GET  /docs     → Swagger UI (interactivo)
GET  /redoc    → ReDoc
GET  /openapi.json → Esquema OpenAPI
```

```python
# Customización
app = FastAPI(
    title="MiApp API",
    description="REST API for order management",
    version="2.0.0",
    docs_url="/api/docs",
    openapi_tags=[
        {"name": "Orders", "description": "Order management endpoints"},
        {"name": "Catalog", "description": "Product catalog"},
    ],
)
```

---

## Checklist FastAPI

- [ ] Routers agrupados por dominio (`modules/orders/router.py`)
- [ ] Pydantic schemas separados (Create, Response, ListParams)
- [ ] Dependency injection para DB, auth, servicios
- [ ] Lifespan para startup/shutdown (conexiones, pools)
- [ ] Error handlers globales con `AppException`
- [ ] CORS configurado con orígenes explícitos
- [ ] Request ID + Response time middleware
- [ ] `response_model` en todos los endpoints
- [ ] `from_attributes = True` en schemas para ORM mode
- [ ] Background tasks solo para cosas rápidas (<5s); Celery para lo demás
