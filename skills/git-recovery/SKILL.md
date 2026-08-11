---
name: git-recovery
description: "Recuperación y debugging en Git. Cubre reflog (recuperar commits perdidos), bisect (encontrar commit que introdujo bug), revert, reset (soft/mixed/hard), restore, y clean. Actívala al perder trabajo, encontrar regresiones, o deshacer cambios accidentales."
disable-model-invocation: true
---

# Git Recovery & Debugging

Guía de recuperación ante errores. Reflog, bisect, revert, reset. "Git no pierde nada, solo hay que saber encontrarlo."

---

## Reflog — tu máquina del tiempo

```bash
# Reflog registra TODOS los movimientos del HEAD (commits, rebases, resets...)
git reflog

# Salida típica:
# a1b2c3d HEAD@{0}: commit: feat(orders): add cancel
# e4f5g6h HEAD@{1}: rebase (finish): returning to refs/heads/feature
# i7j8k9l HEAD@{2}: commit: feat(orders): add list
# m0n1o2p HEAD@{3}: commit (initial): project setup

# Recuperar commit "perdido" después de un reset --hard
git reflog                          # Encontrar el hash perdido
git reset --hard HEAD@{3}           # Volver a ese estado
# o crear rama desde ese punto
git branch recovered-branch HEAD@{3}

# Reflog tiene 90 días de historia por defecto
```

---

## Bisect — búsqueda binaria de bugs

```bash
# Encontrar el commit exacto que introdujo un bug
git bisect start
git bisect bad HEAD              # El commit actual tiene el bug
git bisect good v1.2.0           # v1.2.0 no tenía el bug

# Git hace checkout de un commit intermedio
# Testear manualmente o con script:
npm test                         # ¿Falla?

git bisect bad                   # Si falla
# o
git bisect good                  # Si pasa

# Repetir hasta encontrar el commit exacto (~log2(N) pasos)
git bisect reset                 # Terminar bisect

# Automático con script
git bisect run npm test
```

---

## Revert (deshacer sin borrar historia)

```bash
# Crear un nuevo commit que deshace los cambios de otro commit
git revert a1b2c3d

# Revertir rango de commits (orden inverso)
git revert a1b2c3d..e4f5g6h
# ⚠️ Crea un commit de revert por cada commit en el rango

# Revertir merge commit
git revert -m 1 MERGE_COMMIT_HASH
# -m 1: mantener el lado del padre 1 (main)
```

✅ Revert es seguro para ramas compartidas (no reescribe historia).

---

## Reset (reescribir historia local)

```bash
# Tres niveles (de menos a más destructivo):

# --soft: mueve HEAD, mantiene staging y working tree
git reset --soft HEAD~3
# Commits eliminados, pero cambios quedan en staging
# Útil para: rehacer últimos 3 commits en uno solo

# --mixed (default): mueve HEAD, resetea staging, mantiene working tree
git reset HEAD~2
git reset HEAD file.ts           # Unstage archivo específico

# --hard: mueve HEAD, resetea staging y working tree
git reset --hard HEAD~1
# ⚠️ Cambios no commiteados se pierden permanentemente
```

---

## Restore (deshacer cambios en working tree)

```bash
# Descartar cambios en archivo (vuelve a HEAD)
git restore file.ts

# Descartar todos los cambios
git restore .

# Unstage (quitar del staging area)
git restore --staged file.ts
git restore --staged .

# Restaurar archivo desde commit específico
git restore --source=a1b2c3d file.ts
```

---

## Clean (limpiar archivos untracked)

```bash
# Ver qué se eliminaría
git clean -n

# Eliminar archivos untracked
git clean -f

# Eliminar también directorios
git clean -fd

# ⚠️ También ignorados
git clean -fdx
```

---

## Escenarios comunes de recuperación

```bash
# 1. "Hice commit en la rama equivocada"
git log --oneline -1              # Anotar hash
git checkout correct-branch
git cherry-pick <hash>
git checkout wrong-branch
git reset --hard HEAD~1           # Eliminar commit de rama incorrecta

# 2. "Hice reset --hard y perdí commits"
git reflog
git reset --hard HEAD@{2}         # HEAD@{2} era antes del reset

# 3. "Borré rama local por error"
git reflog | grep "checkout: moving from"
git checkout -b recovered-branch HEAD@{5}

# 4. "Quiero descartar todos los cambios locales y volver a HEAD"
git restore .
git clean -fd

# 5. "Merge salió mal, quiero volver atrás"
git merge --abort                 # Si el merge está en progreso
# o si ya commiteaste:
git reset --hard HEAD~1           # Deshacer merge commit (local)

# 6. "Commiteé un archivo con secrets"
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all
# ⚠️ Rotar todos los secrets expuestos DE INMEDIATO
```

---

## Checklist recovery

- [ ] Ante pánico: `git reflog` primero (todo está ahí 90 días)
- [ ] `git revert` para ramas compartidas (no reescribe historia)
- [ ] `git reset` solo para ramas locales/personales
- [ ] `git bisect` para bugs regresivos sin causa obvia
- [ ] `git restore` sobre `git checkout --` para deshacer cambios
- [ ] Si commiteaste secrets: rotar keys inmediatamente, luego limpiar historia
