---
name: git-advanced
description: "Git avanzado. Cubre hooks (Husky 9, config-based hooks Git 2.54), worktrees (múltiples ramas simultáneas), submodules y subtrees, git-lfs para archivos grandes, monorepo patterns, y filter-repo para limpieza de historial. Actívala al configurar hooks avanzados, trabajar en monorepos, o gestionar archivos binarios."
disable-model-invocation: true
---

# Git Advanced

Guía de features avanzadas de Git. Hooks, worktrees, monorepos, LFS.

---

## Hooks

### Husky 9 (recomendado para proyectos JS/TS)

```bash
npm install -D husky
npx husky init
```

```bash
# .husky/pre-commit
npm run lint-staged

# .husky/commit-msg
npx --no -- commitlint --edit "$1"

# .husky/pre-push
npm test
```

```json
// package.json
{
  "lint-staged": {
    "*.{ts,tsx}": ["eslint --fix", "prettier --write"],
    "*.py": ["ruff check --fix", "ruff format"],
    "*.{json,md,yaml}": ["prettier --write"]
  }
}
```

### Git 2.54 — Config-based hooks

```bash
# Definir hooks en config global o del repo (sin scripts en .git/hooks/)
git config core.hooksPath .githooks

# O definir inline:
git config hook.pre-commit.command "npm run lint-staged"
git config hook.commit-msg.command "npx commitlint --edit $1"
git config hook.pre-push.command "npm test"

# En Git 2.55 (próximo): hooks paralelos
git config hook.pre-commit.parallel true
```

---

## Worktrees

```bash
# Trabajar en múltiples ramas simultáneamente (sin stash ni clones extra)
# Cada worktree tiene su propio working directory

# Crear worktree para una feature
git worktree add ../miapp-hotfix hotfix/payment

# Crear worktree para nueva rama
git worktree add -b feature/analytics ../miapp-analytics main

# Listar worktrees
git worktree list
# /home/user/miapp             abc123 [main]
# /home/user/miapp-hotfix      def456 [hotfix/payment]
# /home/user/miapp-analytics   ghi789 [feature/analytics]

# Eliminar worktree
git worktree remove ../miapp-hotfix
```

Ideal para:
- Hacer hotfix sin interrumpir feature actual
- Correr CI en paralelo en ramas diferentes
- Comparar ramas sin cambiar de contexto

---

## Submodules

```bash
# Agregar submodule (repo dentro de otro repo)
git submodule add https://github.com/mi-org/shared-lib.git libs/shared

# Clonar con submodules
git clone --recurse-submodules https://github.com/mi-org/miapp.git
git submodule update --init --recursive   # Si ya clonaste sin --recurse

# Actualizar submodules
git submodule update --remote

# ⚠️ Submodules agregan complejidad. Evaluar alternativas:
# - Monorepo con Turborepo/Nx
# - Paquetes npm/pip publicados
# - Subtrees (menos complejos)
```

---

## Git LFS (Large File Storage)

```bash
# Instalar
git lfs install

# Trackear tipos de archivo
git lfs track "*.psd"
git lfs track "*.zip"
git lfs track "*.mp4"
git lfs track "models/*.pkl"

# .gitattributes se actualiza automáticamente
git add .gitattributes

# Usar normalmente
git add large-file.psd
git commit -m "add design file"
git push
```

---

## Filter-repo (limpieza de historial)

```bash
# Instalar
pip install git-filter-repo

# Eliminar archivo de TODO el historial
git filter-repo --path secrets.json --invert-paths

# Eliminar archivo grande que nunca debió estar en git
git filter-repo --path massive-dump.sql --invert-paths

# Mover directorio a otro repo (conservando historial)
git filter-repo --subdirectory-filter src/old-module

# Reemplazar texto en todo el historial (ej: email antiguo)
git filter-repo --email-callback 'return email.replace(b"old@example.com", b"new@example.com")'

# ⚠️ Después de filter-repo, todos deben re-clonar. Comunicar al equipo.
git push --force
```

---

## Monorepo patterns

```bash
# Monorepo con carpetas
packages/
├── apps/
│   ├── api/          # package.json (nombre: @miapp/api)
│   └── web/          # package.json (nombre: @miapp/web)
└── shared/
    ├── types/        # package.json (nombre: @miapp/types)
    └── ui/           # package.json (nombre: @miapp/ui)

# Commits con scope
git commit -m "feat(api): add order cancellation"
git commit -m "feat(web): add order detail page"
git commit -m "fix(types): export OrderStatus enum"
```

```bash
# Turborepo/Nx: solo build y test lo que cambió
# turbo.json
{
  "tasks": {
    "build": { "dependsOn": ["^build"] },
    "test": { "dependsOn": ["build"] }
  }
}
```

---

## Git aliases avanzados

```bash
git config --global alias.undo "reset --soft HEAD~1"
git config --global alias.amend "commit --amend --no-edit"
git config --global alias.ll "log --oneline --graph --decorate --all"
git config --global alias.cleanup "!git branch --merged | grep -v '\\*\\|main' | xargs -r git branch -d"
git config --global alias.contributors "shortlog -sn --no-merges"
git config --global alias.today "log --since=midnight --oneline"
```

---

## Checklist avanzado

- [ ] Hooks: lint-staged en pre-commit, commitlint en commit-msg
- [ ] Worktrees para trabajo paralelo en múltiples ramas
- [ ] Git LFS configurado para archivos binarios grandes
- [ ] Monorepo con Turborepo + conventional commits con scope
- [ ] filter-repo para limpiar secrets o archivos grandes del historial
- [ ] Submodules solo si no hay alternativa (monorepo/paquetes)
- [ ] Aliases para comandos frecuentes
