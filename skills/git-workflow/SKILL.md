---
name: git-workflow
description: "Buenas prácticas de Git para equipos. Cubre commits atómicos, Conventional Commits 1.0, branch naming, GitFlow detallado paso a paso, GitHub Flow, merge vs rebase vs squash, PRs efectivos, y configuración de equipo. Actívala al definir el flujo de trabajo del equipo, planear branching strategy, o cuando el usuario pida 'Git Flow', 'conventional commits', 'buenas prácticas git', 'cómo commitear', 'branch naming'."
disable-model-invocation: true
---

# Git Workflow: Buenas Prácticas

Guía de mejores prácticas para Git en equipos de desarrollo (2026).

---

## Reglas de oro

1. **Commits atómicos.** Un cambio lógico = un commit. No mezclar refactor + feature + fix.
2. **Mensajes descriptivos.** `feat(orders): add validation` no `fix stuff`.
3. **Pull con rebase.** `git pull --rebase` evita merge commits basura.
4. **Nunca commitear secrets.** `.env` en `.gitignore`. Usar `.env.example`.
5. **Push frecuente.** No acumular 3 días de trabajo local.
6. **Revisar `git status` y `git diff` antes de cada commit.**
7. **No versionar archivos generados** (`dist/`, `build/`, `node_modules/`).
8. **Un commit = un propósito.** Si el cambio sale mal y no quieres revertir todo el commit, divídelo.

---

## Conventional Commits

Especificación 1.0.0 para commits estructurados. Permite changelogs automáticos y versionado semántico con semantic-release.

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Tipos

| Type | Uso | Versión |
|------|-----|---------|
| `feat` | Nueva funcionalidad | MINOR |
| `fix` | Bug fix | PATCH |
| `docs` | Documentación | - |
| `style` | Formato (no lógica) | - |
| `refactor` | Cambio de código sin feature ni fix | - |
| `perf` | Mejora de rendimiento | - |
| `test` | Tests | - |
| `chore` | Build, CI, deps | - |
| `ci` | CI/CD | - |
| `build` | Sistema de build | - |
| `revert` | Revertir commit | - |

### Breaking changes

```bash
# Con footer
feat: allow provided config object to extend other configs

BREAKING CHANGE: `extends` key in config file is now used for extending other config files

# Con ! (más conciso)
feat(api)!: send an email to the customer when a product is shipped
```

### Ejemplos

```bash
feat(orders): add order cancellation endpoint
fix(payments): handle Stripe timeout gracefully
refactor(orders): extract validation to shared module
perf(orders): add covering index for customer queries
chore(deps): bump typescript to 7.0.0
docs(readme): update installation instructions
test(orders): add cancellation e2e test
```

### Configuración con commitlint + Husky

```bash
npm install -D @commitlint/cli @commitlint/config-conventional
npx husky init
echo "npx --no -- commitlint --edit \$1" > .husky/commit-msg
chmod +x .husky/commit-msg
```

```javascript
// commitlint.config.js
export default {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [2, 'always', [
      'feat', 'fix', 'docs', 'style', 'refactor', 'perf',
      'test', 'chore', 'ci', 'build', 'revert',
    ]],
    'scope-case': [2, 'always', 'kebab-case'],
    'subject-case': [2, 'always', 'lower-case'],
    'subject-max-length': [2, 'always', 72],
  },
};
```

### semantic-release

```bash
npm install -D semantic-release @semantic-release/git @semantic-release/changelog
```

```javascript
// release.config.js
export default {
  branches: ['main'],
  plugins: [
    '@semantic-release/commit-analyzer',
    '@semantic-release/release-notes-generator',
    '@semantic-release/changelog',
    '@semantic-release/npm',
    ['@semantic-release/git', {
      assets: ['package.json', 'CHANGELOG.md'],
      message: 'chore(release): ${nextRelease.version}\n\n${nextRelease.notes}',
    }],
  ],
};
```

```
feat commit → MINOR (1.2.0 → 1.3.0)
fix commit  → PATCH (1.2.0 → 1.2.1)
BREAKING CHANGE → MAJOR (1.2.0 → 2.0.0)
```

---

## Branch naming

### Formato

```
<tipo>/<descripcion-kebab-case>
<tipo>/<ticket-id>-<descripcion-kebab-case>
```

### Prefijos

| Prefijo | Uso | Ejemplo |
|---------|-----|---------|
| `feature/` | Nueva funcionalidad | `feature/order-cancellation` |
| `fix/` | Bug fix | `fix/duplicate-email-validation` |
| `hotfix/` | Fix urgente en producción | `hotfix/payment-timeout-npe` |
| `refactor/` | Refactor sin cambio funcional | `refactor/order-service-extract` |
| `chore/` | Mantenimiento | `chore/update-deps-2026-q2` |
| `docs/` | Documentación | `docs/api-order-cancellation` |
| `release/` | Preparación de release (Git Flow) | `release/1.2.0` |

### Reglas

- **Minúsculas + guiones.** `feature/AddLogin` no, `feature/add-login` sí.
- **3-5 palabras máximo.** Si necesitas más, el scope es muy grande.
- **Ticket ID opcional.** `feature/JIRA-123-order-creation` o `feature/order-creation`. Elegir una y mantenerla.
- **Solo `a-z`, `0-9`, `/`, `-`.** Nada de `_`, `.`, mayúsculas.
- **Sin nombres de persona.** `feature/miguel-fix` no. La rama vive después de que te vas de vacaciones.

---

## Estrategias de branching

| Estrategia | Ideal para | Deploy frequency | Complejidad |
|------------|-----------|------------------|-------------|
| **GitHub Flow** | Web apps, equipos con CI/CD | Continua | Baja |
| **Trunk-Based** | Alta madurez DevOps, deploys diarios | Horaria/diaria | Media |
| **GitFlow** | Software versionado, releases programadas | Semanal/mensual | Alta |

### GitHub Flow (recomendado para la mayoría)

```
main ──────────────────────────────────────────────
  │           │                    │
  └── feature/orders ──┘          └── fix/email ──┘
        PR + squash                    PR + squash
```

```bash
git checkout -b feature/order-cancellation
# ... commits ...
git push origin feature/order-cancellation
# → GitHub PR → review → squash merge → eliminar rama
```

**Reglas:**
- `main` siempre deployable (protegida, requiere PR + CI verde)
- Ramas cortas (< 2 días)
- Squash merge: un commit por feature en `main`
- Feature flags para features incompletas

### Trunk-Based Development

```
main ───────●──────●──────●────── (deploys continuos)
  │ │ │ │ │ │ │ │ │ │ │ │
  └─ ramas pequeñas (horas, no días)
```

**Reglas:**
- Ramas de máximo 1 día
- Feature flags para todo lo que no está listo
- Si rompe `main`, se arregla en minutos (CI/CD obligatorio)
- Commits pequeños y frecuentes

---

## Git Flow detallado

> ⚠️ Git Flow añade fricción para equipos que deployan frecuentemente. Solo para software con releases programadas (apps de escritorio, SDKs, librerías).

### Filosofía

Git Flow (Vincent Driessen, 2010) usa **dos ramas principales** y ramas de soporte para releases programadas.

```
main    ──○────────────────────○────────── (releases)
           │                    │
develop ───┼──○──○──○──○───────┼──○────── (integración)
           │  │       │         │
feature/   ┘  │       │         │
release/      ┘       │         │
hotfix/               ┘         │
```

### Ramas

| Rama | Base | Merge a | Propósito |
|------|------|---------|-----------|
| `main` | - | - | Historia oficial de releases. Solo `release/` o `hotfix/` mergean aquí |
| `develop` | `main` | - | Integración de features. Contiene todo lo que irá en la próxima release |
| `feature/*` | `develop` | `develop` | Nueva funcionalidad. Puede durar días o semanas |
| `release/*` | `develop` | `main` + `develop` | Preparación de release: solo bug fixes, docs, metadata |
| `hotfix/*` | `main` | `main` + `develop` | Fix urgente de producción, salta el ciclo de release |

### Feature branch

```bash
git checkout develop
git checkout -b feature/order-cancellation

# Trabajar con commits atómicos
git add src/orders/cancel.ts
git commit -m "feat(orders): add cancellation endpoint"
git add src/orders/cancel.test.ts
git commit -m "test(orders): add cancellation tests"

# Al terminar: merge --no-ff a develop
git checkout develop
git merge --no-ff feature/order-cancellation
git branch -d feature/order-cancellation
git push origin develop
```

> `--no-ff` fuerza un merge commit aunque sea fast-forward. En Git Flow se usa para preservar que existió una feature branch.

### Release branch

```bash
# Cuando develop tiene suficientes features
git checkout develop
git checkout -b release/1.2.0

# Solo bug fixes, nada de features nuevas
git commit -m "fix: correct price calculation on edge case"
git commit -m "chore: bump version to 1.2.0"

# Merge a main (producción)
git checkout main
git merge --no-ff release/1.2.0
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin main --tags

# Merge back a develop (por si hubo fixes)
git checkout develop
git merge --no-ff release/1.2.0
git branch -d release/1.2.0
```

### Hotfix branch

```bash
# Solo desde main (producción rota)
git checkout main
git checkout -b hotfix/1.2.1

git commit -m "fix: null pointer in payment gateway"

# Merge a main
git checkout main
git merge --no-ff hotfix/1.2.1
git tag -a v1.2.1 -m "Hotfix v1.2.1"
git push origin main --tags

# Merge a develop (el fix debe ir en desarrollo también)
git checkout develop
git merge --no-ff hotfix/1.2.1
git branch -d hotfix/1.2.1
```

### Cuándo NO usar Git Flow

| Situación | Alternativa |
|-----------|-------------|
| Deployas varias veces al día | GitHub Flow o Trunk-Based |
| Equipo pequeño (< 5 devs) | GitHub Flow (menos overhead) |
| No usas releases versionadas | GitHub Flow |
| Tus deploys son automáticos con CI/CD | Trunk-Based |

### Git Flow simplificado (GitHub Flow + releases)

```
main    ──○────────────○────────── (tags: v1.0, v1.1)
           │            │
develop ───○──○──○──────○──○────── (integración)
              │    │
feature/      └────┘
```

Variante ligera: solo `main` y `develop`. Features se mergean a `develop` via squash PRs. Cuando `develop` está listo, se mergea a `main` con tag. Sin `release/` ni `hotfix/` branches.

---

## Merge vs Rebase vs Squash

| Operación | Cuándo usarlo | Ejemplo |
|-----------|---------------|---------|
| **Merge** | Preservar historial exacto, integrar ramas compartidas | `--no-ff` en Git Flow |
| **Rebase** | Limpiar historial local antes de push | Reordenar/squashear commits en rama local |
| **Squash** | Comprimir múltiples commits en uno al mergear PR | GitHub: "Squash and merge" |

```bash
# Merge no-fast-forward (Git Flow)
git merge --no-ff feature/login

# Rebase interactivo (limpiar historia local)
git rebase -i HEAD~5

# Squash merge (GitHub)
# Opción "Squash and merge" en el PR
```

### Decision tree

```
¿Rama compartida con otros?
  ├─ Sí → Merge (--no-ff en Git Flow)
  └─ No → ¿Quieres historial limpio?
       ├─ Sí → Rebase interactivo
       └─ No → Merge normal

¿Estás mergeando un PR?
  ├─ GitHub Flow → Squash merge
  ├─ Git Flow feature → Merge --no-ff
  └─ Git Flow release/hotfix → Merge --no-ff
```

> **Regla de oro:** "No rebasees historia que otros hayan visto." Si la rama está en el remoto y alguien la clonó, usa merge.

---

## Pull Requests y code review

### Plantilla de PR

```markdown
## Descripción

## Tipo de cambio
- [ ] feat: nueva funcionalidad
- [ ] fix: corrección de bug
- [ ] refactor: mejora sin cambio funcional
- [ ] docs: documentación
- [ ] test: tests
- [ ] chore: mantenimiento

## Cómo probar

## Checklist
- [ ] Código sigue las guías de estilo
- [ ] Tests pasan localmente
- [ ] Documentación actualizada
- [ ] Sin secrets ni archivos generados
```

### Buenas prácticas de review

- **PRs pequeños.** Máximo 200-300 líneas. Un PR de 500 no se revisa bien.
- **Review en < 24h.** El código fresco se revisa mejor.
- **Sé específico.** "Esto no me gusta" no ayuda. "Extrae esta lógica a un método porque se repite en la línea 45" sí.
- **Distingue blocking vs nit.** `nit:` para sugerencias menores que no bloquean el merge.
- **Agradece el buen código.** No solo señales problemas.
- **El autor responde.** Cada comentario merece una respuesta.

### Regla de la puerta

> **main protegida.** Nadie hace push directo a `main`.
> 1. Rama desde `main` → 2. PR a `main` → 3. CI verde → 4. ≥ 1 approval → 5. Squash merge

---

## Configuración de equipo

### Configuración global recomendada

```bash
git config --global user.name "Tu Nombre"
git config --global user.email "tu@email.com"
git config --global core.editor "code --wait"
git config --global pull.rebase true
git config --global push.default simple
git config --global diff.algorithm histogram
git config --global diff.colorMoved zebra
git config --global help.autocorrect 20

# Aliases
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.st status
git config --global alias.unstage "reset HEAD --"
git config --global alias.lg "log --oneline --graph --decorate --all -20"
git config --global alias.last "log -1 HEAD"
git config --global alias.undo "reset --soft HEAD~1"
```

### .gitignore base

```gitignore
# Dependencias
node_modules/
__pycache__/
.venv/
*.pyc

# Build
dist/
build/
*.tsbuildinfo

# Secrets
.env
.env.local
*.pem
*.key

# IDE
.vscode/settings.json
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/
```

### Hooks de equipo

```bash
git config core.hooksPath .githooks

# .githooks/pre-commit
cat > .githooks/pre-commit << 'EOF'
#!/bin/sh
npm run lint-staged
EOF
chmod +x .githooks/pre-commit

# .githooks/commit-msg
cat > .githooks/commit-msg << 'EOF'
#!/bin/sh
npx --no -- commitlint --edit "$1"
EOF
chmod +x .githooks/commit-msg
```

### Proteger ramas (GitHub)

```
Settings → Branches → Add rule → main

✅ Require a pull request before merging
  ✅ Require approvals: 1
✅ Require status checks to pass (CI)
✅ Require conversation resolution
✅ Require branches to be up to date
❌ Do not allow bypassing
```

---

## Anti-patrones

| Anti-patrón | Por qué | Solución |
|-------------|---------|----------|
| **Commits gigantes** | No se pueden revertir parcialmente | Commits atómicos |
| **Mensajes como "fix" o "cambios"** | Inútiles en `git blame` y changelogs | Conventional Commits |
| **Push directo a main** | Rompe producción sin revisión | Rama protegida + PRs |
| **Rebase de ramas compartidas** | Reescribe historia que otros tienen | Merge en ramas compartidas |
| **Ramas long-lived (semanas)** | Merges monstruosos, conflictos eternos | Ramas < 2 días, feature flags |
| **Mezclar refactor + feature + fix** | Imposible revertir solo el fix | Tres commits separados |
| **Nombres de rama en mayúsculas o con **_'** | Inconsistentes, difíciles de escribir | kebab-case todo |
| **Git Flow + deploys diarios** | Demasiada ceremonia para poco beneficio | GitHub Flow o Trunk-Based |
| **Hotfix sin merge a develop** | El fix se pierde en la siguiente release | Siempre mergear hotfix a develop |

---

## Checklist

- [ ] Estrategia de branching elegida según frecuencia de deploy
- [ ] Conventional commits con commitlint (Husky o config hooks)
- [ ] Branch naming consistente (prefijo tipo/descripcion)
- [ ] Ramas cortas (< 2 días GitHub Flow, < 1 día Trunk-Based)
- [ ] Squash merge en PRs (un commit lógico = un commit en main)
- [ ] `main` protegida (PR + CI + approval)
- [ ] `pull.rebase true` en config global
- [ ] Hooks de equipo (lint, commitlint)
- [ ] Git Flow solo si hay releases programadas
- [ ] `.gitignore` desde el primer commit
- [ ] Agregar esta skill a `.pi/settings.json` del proyecto
