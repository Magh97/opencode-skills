# Publish

Git hygiene for a documentation repository. Every item here prevents a problem that is cheap now and annoying later.

---

## Before the first commit

### `.gitattributes` — fix line endings in the repository

Without it, a Windows machine commits `CRLF` and a Linux machine commits `LF`, and the same document shows as fully modified every time it crosses platforms. Diff review becomes impossible.

```gitattributes
* text=auto eol=lf

*.md   text eol=lf
*.yaml text eol=lf
*.yml  text eol=lf
*.json text eol=lf

*.png  binary
*.jpg  binary
*.pdf  binary
```

### `.gitignore` — minimal

For a documentation repository there is little to ignore. Keep it to OS and editor noise.

```gitignore
# OS
.DS_Store
Thumbs.db
desktop.ini

# Editors
.vscode/
.idea/
*.swp
*~

# Obsidian: keep the vault config, ignore the volatile workspace state
.obsidian/workspace.json
.obsidian/workspace-mobile.json

# Tooling
node_modules/
*.log
```

### Branch name

`main`, not `master`. `master` is Git's legacy default; `main` is the convention everywhere else. If the remote repository is empty, rename the unborn branch:

```bash
git symbolic-ref HEAD refs/heads/main
```

### Identity

Confirm before committing. A wrong author is in every commit forever.

```bash
git config --global user.name
git config --global user.email
```

---

## Linking to a remote

Check three things first, in this order.

```bash
# 1. Does the remote exist, and is it empty?
git ls-remote https://github.com/<owner>/<repo>.git

# 2. What is it, exactly? (visibility, default branch, emptiness)
gh repo view <owner>/<repo> --json name,visibility,defaultBranchRef,isEmpty

# 3. Are credentials configured?
gh auth status
```

An empty remote means no conflicts and no merge. A non-empty one means fetching and reconciling before pushing.

```bash
gh auth setup-git                          # configure the credential helper
git remote add origin https://github.com/<owner>/<repo>.git
git remote -v                              # verify
```

---

## The commit

### Conventional commits

```
docs(<project>): description
docs: add the <name> documentation set
feat(<project>): description
fix(<project>): description
chore: description
```

### The first commit of a document set

Describe **what the set contains**, not that it exists. A commit message is the only place the scope of a 60-file commit is stated.

```
docs: add the Mesa Viva design documentation set

A complete technical design for a restaurant POS and kitchen operations
system, built around post-send order mutation as an immutable item delta.

Contents:
- Requirements (133 with stable IDs), NFR (83 measurable targets),
  traceability matrix
- Architecture, data model (33 tables), API contract (78 operations)
- UI specification, design system, security threat model
- Critical flows, operations runbook, glossary
- 6 ADRs and a 48-entry decision log

Superseded material is kept under docs/archive/ so the reasoning behind
each change stays traceable.
```

### Commit messages with multiple paragraphs

```bash
git commit -m "docs: short subject" -m "Body paragraph one.

Body paragraph two."
```

Two `-m` flags, not a heredoc. Heredocs with markdown inside a shell command break on quoting.

---

## Push and verify

```bash
git push -u origin main

# Verify: local HEAD must equal the remote ref
git ls-remote --heads origin
git rev-parse HEAD
git status -sb
```

`git status -sb` must show no divergence. If it shows `[ahead 1]`, the push did not land.

---

## Archive, never delete

**A superseded document moves to `docs/archive/`. It is never deleted.**

| Repository | Archive |
| :--- | :--- |
| Private | Keep it in the repository. Preserving the reasoning costs nothing |
| Public | Move it out (a Gist, or an `archive` branch). A stack of superseded enterprise documents in a solo portfolio communicates misjudged effort |

Archived material is **excluded from every check**. A link in an archived document pointing at something that moved is expected, not a defect.

**Never rewrite an accepted ADR.** Mark it superseded and write a new one. The old record is the evidence that the decision was deliberate.

---

## Before every commit

```bash
python scripts/check-docs.py          <project-dir>
python scripts/check-traceability.py  <project-dir>
python scripts/check-consistency.py   <project-dir>
```

All three must pass. A failing check means either the document is wrong or the check has a documented false-positive class. **Never weaken a check to make it pass.**

---

## Anti-patterns

| Anti-pattern | Why it is wrong |
| :--- | :--- |
| Committing without `.gitattributes` | Line endings flip per platform; every diff shows the whole file as changed |
| `git add .` on a repository with a `.env` | Secrets in history. History is permanent |
| Committing 60 files with the message "initial commit" | The commit message is the only place the scope is recorded |
| Force-pushing a shared branch | Rewrites history others depend on |
| Deleting a superseded document | Destroys the reasoning. Archive it |
| Editing an accepted ADR | The decision history becomes a fiction |
| Pushing before verifying `git ls-remote` | Pushing into an unknown state, possibly a non-empty remote |
| Assuming the push worked | `git status -sb` shows divergence. Verify it |
| Making the repository public with the archive inside | A stack of superseded documents reads as misjudged effort |

---

## Repository-level index

A repository holding **more than one project** needs a root `README.md` that indexes them: what each is, its state, its thesis, and how to enter it.

It also states the conventions the repository follows — the document classes, the language split, the archive policy — so the second project does not have to rediscover them.
