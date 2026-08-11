---
name: python-database
description: "Acceso a datos en Python con SQLAlchemy 2.0 async y Alembic. Cubre modelos, repositorios, migraciones, PostgreSQL + SQL Server, connection pooling, queries optimizadas, y patrones de acceso a datos. Actívala al configurar ORM, diseñar esquemas, o migrar desde Django ORM/Peewee."
disable-model-invocation: true
---

# Python Database Access

Guía de acceso a datos con SQLAlchemy 2.0 (async) + Alembic. PostgreSQL y SQL Server.

---

## SQLAlchemy 2.0 — Async Setup

```bash
uv add sqlalchemy[asyncio] asyncpg alembic
# Para SQL Server: uv add aioodbc
```

```python
# shared/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# PostgreSQL
engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost:5432/miapp",
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,  # Verificar conexión antes de usar
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
```

---

## Modelos

```python
# modules/orders/models.py
from sqlalchemy import String, Numeric, DateTime, Integer, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from uuid import uuid4
from miapp.shared.database import Base

class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        Index("idx_orders_customer_id_status", "customer_id", "status"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    order_number: Mapped[int] = mapped_column(
        Integer, autoincrement=True, unique=True
    )
    customer_id: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    total_amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="MXN")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )

class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    order_id: Mapped[str] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    sku: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")
```

---

## Repositorios (async)

```python
# modules/orders/repository.py
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from .models import Order

class OrderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, order: Order) -> Order:
        self.db.add(order)
        await self.db.flush()
        return order

    async def find_by_id(self, order_id: str) -> Order | None:
        stmt = (
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_customer(
        self, customer_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[Order], int]:
        # Query de conteo
        count_stmt = select(func.count(Order.id)).where(
            Order.customer_id == customer_id
        )
        total = (await self.db.execute(count_stmt)).scalar() or 0

        # Query paginada
        stmt = (
            select(Order)
            .where(Order.customer_id == customer_id)
            .order_by(Order.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all(), total

    async def batch_update_status(
        self, customer_id: str, old_status: str, new_status: str
    ) -> int:
        stmt = (
            update(Order)
            .where(Order.customer_id == customer_id, Order.status == old_status)
            .values(status=new_status, updated_at=func.now())
        )
        result = await self.db.execute(stmt)
        return result.rowcount
```

---

## Alembic — Migraciones

```bash
# Inicializar
uv run alembic init migrations

# Generar migración automática desde modelos
uv run alembic revision --autogenerate -m "add orders table"

# Aplicar migraciones
uv run alembic upgrade head

# Rollback
uv run alembic downgrade -1

# Ver estado
uv run alembic current
uv run alembic history
```

```python
# migrations/env.py — configuración async
from sqlalchemy.ext.asyncio import create_async_engine
from miapp.shared.database import Base
from miapp.config import settings

target_metadata = Base.metadata

def run_migrations_online():
    connectable = create_async_engine(settings.DATABASE_URL)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
```

---

## SQL Server con SQLAlchemy

```bash
uv add aioodbc pyodbc
```

```python
# Connection string SQL Server
DATABASE_URL = (
    "mssql+aioodbc://user:pass@localhost:1433/miapp"
    "?driver=ODBC+Driver+18+for+SQL+Server"
    "&TrustServerCertificate=yes"
)

engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    pool_pre_ping=True,
)
```

---

## Buenas prácticas

```python
# ✅ Inyección de sesión por request (FastAPI)
async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

# ✅ selectinload sobre joinedload (evita JOIN explosivo)
stmt = select(Order).options(
    selectinload(Order.items),
    selectinload(Order.payments),
)

# ✅ Session por operación lógica, no por query
# ❌
async def bad_example(db: AsyncSession):
    orders = await db.execute(select(Order))
    for o in orders:
        await db.refresh(o)  # No necesario
# ✅
async def good_example(db: AsyncSession):
    stmt = select(Order).options(selectinload(Order.items))
    result = await db.execute(stmt)
    return result.scalars().all()
```

---

## Checklist database

- [ ] SQLAlchemy 2.0 con async (async_sessionmaker)
- [ ] Modelos tipados con `Mapped[T]` y `mapped_column()`
- [ ] Alembic para migraciones versionadas
- [ ] `pool_pre_ping=True` para conexiones saludables
- [ ] `selectinload` sobre `joinedload` para relaciones múltiples
- [ ] Proyección (`select(Order.id, Order.status)`) para queries de solo lectura
- [ ] Batch updates con `update().values()` sobre loop + save
- [ ] Session por request HTTP (FastAPI dependency)
- [ ] Rollback en excepción, commit al final
