---
name: git-workflow
description: "Buenas prácticas de commits en Git para equipos. Cubre commits atómicos, Conventional Commits 1.0 (formato, tipos, breaking changes, commitlint, semantic-release), y convención de branch naming. Actívala al definir cómo commitear, configurar commitlint, o cuando el usuario pida 'conventional commits', 'buenas prácticas de commit', 'cómo commitear', 'branch naming'."
disable-model-invocation: true
---

# Git Workflow: Commits Atómicos, Conventional Commits y Branch Naming

Guía de mejores prácticas para escribir commits y nombrar ramas en equipos de desarrollo (2026).

> Para estrategias de branching completas (GitFlow, GitHub Flow, Trunk-Based Development), ver `git-branching`.
> Para PRs efectivos, code review, y merge vs rebase vs squash, ver `git-collaboration`.

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

## Anti-patrones

| Anti-patrón | Por qué | Solución |
|-------------|---------|----------|
| **Commits gigantes** | No se pueden revertir parcialmente | Commits atómicos |
| **Mensajes como "fix" o "cambios"** | Inútiles en `git blame` y changelogs | Conventional Commits |
| **Mezclar refactor + feature + fix** | Imposible revertir solo el fix | Tres commits separados |
| **Nombres de rama en mayúsculas o con `_`** | Inconsistentes, difíciles de escribir | kebab-case todo |

---

## Checklist

- [ ] Commits atómicos (un cambio lógico = un commit)
- [ ] Conventional commits con commitlint (Husky o config hooks)
- [ ] Branch naming consistente (prefijo tipo/descripcion)
- [ ] `pull.rebase true` en config global
- [ ] `.gitignore` desde el primer commit
- [ ] Para branching strategy, ver `git-branching`
- [ ] Para PRs y code review, ver `git-collaboration`
