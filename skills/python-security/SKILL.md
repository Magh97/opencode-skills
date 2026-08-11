---
name: python-security
description: "Seguridad en aplicaciones Python. Cubre JWT/OAuth2 con FastAPI, CORS, rate limiting, input validation (Pydantic), SQL injection, CSRF, dependency audit (pip-audit), secrets management (Pydantic Settings), y hardening. Actívala al asegurar APIs, implementar autenticación, o auditar dependencias."
disable-model-invocation: true
---

# Python Security

Guía de seguridad para aplicaciones Python. Defensa en profundidad con FastAPI + Pydantic.

---

## JWT — Autenticación

```python
import jwt
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel

ALGORITHM = "HS256"

class TokenPayload(BaseModel):
    sub: str        # user_id
    role: str
    exp: datetime
    iat: datetime

def create_access_token(user_id: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = TokenPayload(
        sub=user_id,
        role=role,
        exp=now + timedelta(minutes=15),
        iat=now,
    )
    return jwt.encode(
        payload.model_dump(),
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

def create_refresh_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": user_id, "type": "refresh", "exp": now + timedelta(days=7)},
        REFRESH_SECRET_KEY,
        algorithm=ALGORITHM,
    )

def verify_token(token: str) -> TokenPayload:
    data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return TokenPayload.model_validate(data)

# FastAPI dependency
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = verify_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await get_user_by_id(db, payload.sub)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
```

---

## CORS

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # ["https://miapp.com"]
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
)
```

---

## Rate Limiting

```python
# slowapi — rate limiting para FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Endpoint general
@router.get("/")
@limiter.limit("100/minute")
async def list_orders(...):
    ...

# Auth endpoints más restrictivos
@router.post("/login")
@limiter.limit("5/minute")
async def login(...):
    ...
```

---

## Input Validation — Pydantic v2

```python
from pydantic import BaseModel, Field, field_validator, model_validator
import re

# ✅ SQL injection prevention: validar, no concatenar
class OrderCreate(BaseModel):
    customer_id: str = Field(..., min_length=1, max_length=50)
    amount: float = Field(..., gt=0, le=9_999_999)

    @field_validator("customer_id")
    @classmethod
    def sanitize(cls, v: str) -> str:
        # Solo alfanumérico + guiones
        if not re.match(r"^[A-Za-z0-9\-_]+$", v):
            raise ValueError("Invalid characters")
        return v.strip()

    @model_validator(mode="after")
    def validate_business_rules(self):
        # Validación cross-field
        if self.amount > 1000 and not self.approval_code:
            raise ValueError("Approval code required for amounts > 1000")
        return self
```

---

## Secrets Management

```python
# config.py — Pydantic Settings
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
    )

    # App
    APP_NAME: str = "MiApp API"
    DEBUG: bool = False

    # Security
    SECRET_KEY: str = Field(..., min_length=32)
    REFRESH_SECRET_KEY: str = Field(..., min_length=32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    # Database
    DATABASE_URL: str = Field(..., pattern=r"^postgresql\+asyncpg://")

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # Stripe
    STRIPE_API_KEY: str = Field(..., pattern=r"^sk_.+")

settings = Settings()
# Si falta alguna variable requerida → la app no arranca
```

---

## Hash de passwords

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

---

## Dependency Audit

```bash
# pip-audit: escanea vulnerabilidades conocidas
uv add --dev pip-audit
uv run pip-audit

# En CI: fallar si hay vulnerabilidades
uv run pip-audit --strict
```

---

## HTTPS y headers de seguridad

```python
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# Redirigir HTTP → HTTPS
if not settings.DEBUG:
    app.add_middleware(HTTPSRedirectMiddleware)

# Security headers via middleware
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "0"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response
```

---

## Checklist seguridad

- [ ] JWT con secret ≥32 chars, algoritmo HS256 mínimo, expiración corta
- [ ] Refresh tokens en httpOnly cookies, access token en memoria (no localStorage)
- [ ] CORS con orígenes explícitos
- [ ] Rate limiting en todos los endpoints (auth más restrictivo)
- [ ] Pydantic validación en todas las fronteras
- [ ] SQL siempre parametrizado (SQLAlchemy lo maneja)
- [ ] `pip-audit` en CI, sin vulnerabilidades altas
- [ ] Secrets en Pydantic Settings, nunca en código
- [ ] HTTPS en producción con HSTS
- [ ] Security headers configurados
- [ ] Passwords hasheados con bcrypt
- [ ] Sin `except Exception: pass` — loggear y manejar
