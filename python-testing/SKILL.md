---
name: python-testing
description: "Testing en Python con pytest 9.1 y pytest-asyncio. Cubre fixtures, parametrización, mocking (unittest.mock, pytest-mock), Testcontainers, httpx para testing de APIs, coverage, y TDD. Actívala al escribir tests, configurar CI/CD, o definir estrategia de testing."
disable-model-invocation: true
---

# Python Testing

Guía de testing con pytest 9.1 + pytest-asyncio. Stack moderno y rápido.

---

## Setup

```bash
uv add --dev pytest pytest-asyncio pytest-cov httpx
```

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = ["-v", "--strict-markers", "--tb=short"]
```

---

## Unit tests con pytest

```python
# tests/modules/orders/test_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from miapp.modules.orders.service import OrderService
from miapp.modules.orders.schemas import OrderCreate

@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.find_by_id = AsyncMock()
    return repo

@pytest.fixture
def order_service(mock_repo):
    return OrderService(mock_repo)

class TestCreateOrder:
    async def test_creates_order_successfully(self, order_service, mock_repo):
        input_data = OrderCreate(customer_id="CUST-001", amount=150.0)
        expected = {"id": "1", "customer_id": "CUST-001", "status": "pending"}
        mock_repo.create.return_value = expected

        result = await order_service.create(input_data)

        assert result["id"] == "1"
        assert result["status"] == "pending"
        mock_repo.create.assert_awaited_once()

    async def test_raises_on_negative_amount(self, order_service):
        input_data = OrderCreate(customer_id="CUST-001", amount=-100)

        with pytest.raises(ValueError, match="amount must be positive"):
            await order_service.create(input_data)

    @pytest.mark.parametrize("status,expect_cancel", [
        ("pending", True),
        ("confirmed", True),
        ("shipped", False),
        ("delivered", False),
        ("cancelled", False),
    ])
    async def test_can_cancel_depends_on_status(
        self, status, expect_cancel, order_service
    ):
        order = {"id": "1", "status": status}
        assert order_service.can_cancel(order) == expect_cancel
```

---

## Fixtures

```python
# conftest.py — fixtures compartidos
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from miapp.shared.database import Base

TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5432/test"

@pytest_asyncio.fixture(scope="session")
async def async_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(async_engine):
    async_session = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
def sample_order_create():
    return OrderCreate(customer_id="CUST-001", amount=150.0, currency="MXN")
```

---

## API testing con httpx y AsyncClient

```python
from httpx import ASGITransport, AsyncClient
from miapp.main import app

@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

class TestOrdersAPI:
    async def test_create_order(self, client: AsyncClient):
        response = await client.post("/api/orders", json={
            "customer_id": "CUST-001",
            "amount": 150,
        })
        assert response.status_code == 201
        data = response.json()
        assert data["customer_id"] == "CUST-001"
        assert data["status"] == "pending"

    async def test_list_orders(self, client: AsyncClient):
        response = await client.get("/api/orders")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_validation_error(self, client: AsyncClient):
        response = await client.post("/api/orders", json={
            "customer_id": "",
            "amount": -5,
        })
        assert response.status_code == 422
        assert "error" in response.json()
```

---

## Testcontainers (base de datos real)

```python
# uv add --dev testcontainers
import pytest
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:18-alpine") as postgres:
        postgres.with_env("POSTGRES_USER", "test")
        postgres.with_env("POSTGRES_PASSWORD", "test")
        postgres.with_env("POSTGRES_DB", "test")
        yield postgres.get_connection_url()

@pytest_asyncio.fixture(scope="session")
async def async_engine(postgres_url: str):
    engine = create_async_engine(postgres_url.replace("postgresql://", "postgresql+asyncpg://"))
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
```

---

## pytest 9.1 nuevas features

```python
# ✅ pytest.register_fixture() — registrar fixtures imperativamente
import pytest

def my_fixture():
    return {"key": "value"}

pytest.register_fixture(name="my_data", scope="function")(my_fixture)

# ✅ --report-chars: cambiar caracteres de reporte
# pytest --report-chars=unicode  (✓ ✗ ⚡)

# ⚠️ Cuidado: autouse fixtures con scope module/package
# No ejecutarlas dos veces. Fixed en 9.1.1.
```

---

## Mocking

```python
from unittest.mock import AsyncMock, patch, MagicMock

# Mock de función asíncrona
async def test_with_mock():
    with patch("miapp.modules.orders.service.send_email", new_callable=AsyncMock) as mock:
        mock.return_value = {"status": "sent"}
        result = await send_email("test@test.com")
        assert result["status"] == "sent"

# Mock de datetime
from freezegun import freeze_time

@freeze_time("2026-06-23 12:00:00")
async def test_created_at_is_now(self, order_service):
    order = await order_service.create(sample_data)
    assert order.created_at.isoformat() == "2026-06-23T12:00:00"
```

---

## Coverage

```bash
uv run pytest --cov=src/miapp --cov-report=term --cov-report=html

# Configurar en pyproject.toml
[tool.coverage.run]
source = ["src/miapp"]
omit = ["tests/*", "*/migrations/*"]

[tool.coverage.report]
exclude_also = [
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
    "class .*\bProtocol\b:",
]
```

---

## Checklist testing

- [ ] pytest + pytest-asyncio (`asyncio_mode = "auto"`)
- [ ] Fixtures para setup de DB y client HTTP
- [ ] Testcontainers para integration tests con DB real
- [ ] httpx AsyncClient para testing de endpoints FastAPI
- [ ] Parametrize para múltiples escenarios
- [ ] AAA pattern (Arrange, Act, Assert)
- [ ] Mock solo de I/O externo (APIs, email), no de DB en integration tests
- [ ] Coverage ≥ 80% en lógica de negocio
- [ ] Tests independientes (sin orden, sin estado compartido)
- [ ] `uv run pytest` en CI antes de merge
