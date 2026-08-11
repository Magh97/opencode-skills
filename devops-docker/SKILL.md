---
name: devops-docker
description: "Contenedores con Docker v29. Cubre multi-stage builds, BuildKit, docker-compose, Kaniko para builds en Kubernetes, mejores prácticas de seguridad (rootless, multi-stage, distroless), image signing con Cosign, y optimización de imágenes. Actívala al crear Dockerfiles, configurar builds en CI, o migrar a contenedores."
disable-model-invocation: true
---

# Docker & Containers

Guía de contenedores con Docker v29 (2026). Builds eficientes, imágenes seguras, multi-stage.

---

## Dockerfile — Mejores prácticas 2026

```dockerfile
# syntax=docker/dockerfile:1
# ✅ Multi-stage, distroless, usuario no-root

# Stage 1: Build
FROM python:3.14-slim AS build
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY src/ src/

# Stage 2: Runtime
FROM gcr.io/distroless/python3.14-debian13 AS production
WORKDIR /app

# Copiar solo lo necesario del stage de build
COPY --from=build /app/.venv/lib/python3.14/site-packages /app/.venv/lib/python3.14/site-packages
COPY --from=build /app/src /app/src

ENV PYTHONPATH=/app/.venv/lib/python3.14/site-packages
ENV PYTHONUNBUFFERED=1

# Usuario no-root (distroless ya lo maneja)
EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=3s \
  CMD ["/app/.venv/bin/python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:3000/health')"]

CMD ["/app/.venv/bin/gunicorn", "miapp.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", "--bind", "0.0.0.0:3000"]
```

### Reglas de oro del Dockerfile

```dockerfile
# 1. ✅ Pinear versiones exactas (no :latest)
FROM node:24.14.0-alpine  # ✅
FROM node:alpine          # ❌ (flota, rompe builds)

# 2. ✅ Copiar lock file primero (cache de capas)
COPY package.json package-lock.json ./
RUN npm ci --omit=dev
COPY src/ src/   # Después, porque cambia frecuentemente

# 3. ✅ Multi-stage: build tools no van a producción
# 4. ✅ Usar distroless o alpine; nunca full OS
# 5. ✅ HEALTHCHECK definido
# 6. ✅ .dockerignore (node_modules, .git, .env, dist, __pycache__)
# 7. ✅ No secrets en capas: usar --mount=type=secret
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc npm ci
```

---

## BuildKit (habilitado por defecto en Docker 29)

```bash
# BuildKit permite:
# - Secrets en build sin dejar rastro en capas
# - Cache mounts (persisten entre builds)
# - SSH forwarding
# - Multi-platform builds

# Build con secrets
docker build --secret id=npmrc,src=$HOME/.npmrc -t miapp .

# Multi-plataforma
docker buildx build --platform linux/amd64,linux/arm64 -t miapp --push .

# Cache remoto
docker buildx build --cache-to=type=registry,ref=ghcr.io/mi-org/cache:miapp \
                    --cache-from=type=registry,ref=ghcr.io/mi-org/cache:miapp \
                    -t miapp .
```

---

## Kaniko — Builds en Kubernetes (sin Docker daemon)

```yaml
# Build en CI (GitHub Actions) o en cluster sin privilegios
apiVersion: batch/v1
kind: Job
metadata:
  name: kaniko-build
spec:
  template:
    spec:
      containers:
      - name: kaniko
        image: osscontainertools/kaniko:latest  # Fork comunitario (original archivado Jun 2025)
        args:
        - "--context=git://github.com/mi-org/miapp.git#refs/heads/main"
        - "--destination=ghcr.io/mi-org/miapp:$BUILD_ID"
        volumeMounts:
        - name: docker-config
          mountPath: /kaniko/.docker
      restartPolicy: Never
      volumes:
      - name: docker-config
        secret:
          secretName: registry-credentials
```

---

## Docker Compose (desarrollo)

```yaml
# docker-compose.yml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports: ["3000:3000"]
    environment:
      - DATABASE_URL=postgresql://app_user:dev_pass@postgres:5432/miapp
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./src:/app/src  # Hot reload sin rebuild
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  postgres:
    image: postgres:18-alpine
    environment:
      POSTGRES_DB: miapp
      POSTGRES_USER: app_user
      POSTGRES_PASSWORD: dev_pass
    ports: ["5432:5432"]
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app_user -d miapp"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]

volumes:
  pgdata:
```

---

## Seguridad de imágenes

```bash
# Trivy — escaneo de vulnerabilidades
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image ghcr.io/mi-org/miapp:latest

# En CI: fallar si hay vulnerabilidades críticas
trivy image --severity CRITICAL --exit-code 1 ghcr.io/mi-org/miapp:latest

# Cosign — firmar imágenes
cosign sign --key cosign.key ghcr.io/mi-org/miapp:latest
cosign verify --key cosign.pub ghcr.io/mi-org/miapp:latest

# Keyless signing (OIDC) con GitHub Actions
cosign sign ghcr.io/mi-org/miapp:${{ github.sha }}
```

---

## Optimización de imágenes

| Técnica | Ahorro | Cuándo |
|---------|--------|--------|
| Multi-stage | 40-60% | Siempre ✅ |
| Distroless base | 50-80% vs full Debian | Producción |
| Alpine base | 80-95% vs full OS | Si no necesitas glibc |
| `--no-install-recommends` (apt) | 20-30% | Cuando uses apt |
| Docker squash | 15-25% | Antes de push final |
| `.dockerignore` | Variable | Siempre ✅ |

```bash
# Analizar capas
docker history ghcr.io/mi-org/miapp:latest

# Ver tamaño de cada capa
dive ghcr.io/mi-org/miapp:latest
```

---

## Checklist Docker

- [ ] Multi-stage build (separar build de runtime)
- [ ] Distroless o Alpine como base de producción
- [ ] Usuario no-root
- [ ] HEALTHCHECK definido
- [ ] `.dockerignore` excluye node_modules, .git, .env, dist
- [ ] Secrets via `--mount=type=secret` (no en capas)
- [ ] Versiones pineadas (no `:latest`)
- [ ] Trivy scan en CI (sin CRITICAL en producción)
- [ ] Cosign sign + verify
- [ ] BuildKit cache para builds rápidos en CI
