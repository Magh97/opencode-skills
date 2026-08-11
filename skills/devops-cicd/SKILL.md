---
name: devops-cicd
description: "CI/CD moderno con GitHub Actions 2026. Cubre reusable workflows, workflow execution protections, agentic workflows, progressive delivery (canary, blue-green), Argo Rollouts, feature flags, y pipelines seguros. Actívala al diseñar pipelines de CI/CD, migrar de Jenkins, o implementar despliegues progresivos."
disable-model-invocation: true
---

# CI/CD & Progressive Delivery

Guía de CI/CD con GitHub Actions 2026. Pipelines seguros, despliegues progresivos.

---

## GitHub Actions — Pipeline estándar

```yaml
# .github/workflows/ci.yml
name: CI

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '24' }
      - run: npm ci
      - run: npm run lint

  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '24' }
      - run: npm ci
      - run: npm run typecheck

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:18-alpine
        env:
          POSTGRES_DB: test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports: ["5432:5432"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '24' }
      - run: npm ci
      - run: npm test -- --coverage
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/test
```

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]
    paths-ignore: ['docs/**', 'README.md']

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
      id-token: write
    outputs:
      image_tag: ${{ steps.meta.outputs.version }}
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}
          tags: type=sha,type=ref,event=branch
      - uses: docker/build-push-action@v6
        with:
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
      - uses: sigstore/cosign-installer@v3
      - run: cosign sign ghcr.io/${{ github.repository }}@${{ steps.meta.outputs.digest }}

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: |
          sed -i "s|image:.*|image: ghcr.io/${{ github.repository }}:${{ github.sha }}|" \
            k8s/overlays/production/kustomization.yaml
          git config user.name "github-actions"
          git config user.email "actions@github.com"
          git add k8s/
          git commit -m "deploy: ${{ github.sha }}"
          git push
```

---

## Reusable workflows

```yaml
# .github/workflows/_node-ci.yml (reusable)
name: Node.js CI

on:
  workflow_call:
    inputs:
      node-version:
        type: string
        default: '24'

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '${{ inputs.node-version }}' }
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck
      - run: npm test

# Uso en otro workflow
jobs:
  ci:
    uses: ./.github/workflows/_node-ci.yml
    with:
      node-version: '24'
```

---

## Workflow Execution Protections (2026)

```yaml
# Solo ciertos actores/eventos pueden disparar workflows
# Configurable en Settings → Actions → General → Workflow permissions

# En el workflow:
on:
  pull_request:
    branches: [main]
  # push solo de ciertos equipos
  push:
    branches: [main]
```

Las protecciones permiten definir una **allow list** de quién y qué eventos pueden ejecutar workflows. Previene modificaciones maliciosas en PRs.

---

## Agentic Workflows (GitHub 2026 preview)

```markdown
# .github/agents/triage.md
name: Issue Triage Agent
on:
  issues:
    types: [opened]

This agent analyzes incoming issues and applies labels, assigns reviewers,
and suggests related issues.

1. Read the issue title and body
2. Classify it as: bug, feature, documentation, or question
3. Apply the corresponding label
4. If bug, check for stack traces and suggest the CODEOWNERS file
5. Comment with a summary and next steps
```

GitHub compila el markdown a Actions YAML automáticamente. El agente usa IA para razonar sobre issues, CI failures, etc.

---

## Progressive Delivery

### Blue-Green

```
Active (Blue)  ← 100% traffic
Inactive (Green) ← 0% traffic, nueva versión

1. Deploy Green con nueva versión
2. Smoke test en Green
3. Switch traffic: Blue → Green
4. Blue queda como rollback instantáneo
```

### Canary con Argo Rollouts

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: miapp-api
spec:
  replicas: 5
  strategy:
    canary:
      steps:
      - setWeight: 20      # 20% tráfico a nueva versión
      - pause: { duration: 5m }  # Esperar 5 min
      - setWeight: 50
      - pause: { duration: 5m }
      - setWeight: 100     # 100% tráfico
      # Análisis automático con Prometheus
      analysis:
        templates:
        - templateName: error-rate-check
        startingStep: 1
```

---

## Feature Flags (LaunchDarkly)

```typescript
// Desacoplar deploy de release
const useNewOrderFlow = await client.variation('new-order-flow', user, false);

if (useNewOrderFlow) {
  return <NewOrderFlow />;
}
return <LegacyOrderFlow />;
```

El código se despliega pero la feature se activa vía flag. Rollback instantáneo sin redeploy.

---

## Checklist CI/CD

- [ ] Pipeline: lint → typecheck → test → build → push → deploy
- [ ] Reusable workflows para evitar duplicación (un CI para todos los servicios)
- [ ] Workflow protections: solo ciertos actores pueden disparar deploys
- [ ] Imágenes firmadas con Cosign en CI
- [ ] Cache de dependencias (npm, uv, NuGet) + BuildKit cache
- [ ] Progressive delivery: canary o blue-green (no big-bang deploys)
- [ ] Smoke tests automáticos post-deploy
- [ ] Rollback automatizado si smoke test o métricas fallan
- [ ] Feature flags para desacoplar deploy de release
