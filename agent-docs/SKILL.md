---
name: agent-docs
description: 'Generates agent-optimized documentation from existing human docs. Scans README.md, docs/, linter configs, and package.json to produce a docs/agent-docs/ folder with 9 token-efficient files: CONTEXT, STACK, RULES, ARCHITECTURE, SCHEMA, API, PATTERNS, DESIGN, WORKFLOWS. Use when user says "agent docs", "docs for agents", "agent dialect", "optimize docs for AI", "generate agent docs".'
requires-devkits: auto-detect
---

# Agent Docs -- Human Docs to Agent-Optimized Docs

Converts existing human documentation into a `docs/agent-docs/` folder designed for AI agents to consume efficiently. Every output file uses tables, code blocks, and concrete values -- zero prose fluff.

---

## Workflow

### Phase 1: Scan

Read all existing documentation sources:

| Source | Extract |
|--------|---------|
| `README.md` | Project name, purpose, stack summary, links |
| `docs/**/*.md` (all spec, architecture, api, data, design, testing, CI/CD, deployment, risks docs) | Modules, endpoints, entities, tokens, patterns, workflows |
| `.eslintrc.*` / `eslint.config.*` / `.editorconfig` | Code style rules for RULES.md |
| `package.json` | Dependencies + versions for STACK.md |
| `tsconfig.json` | Strictness settings |
| `.env.example` | Required env vars |
| `docker-compose.yml` | Local dev setup |
| Any `.cursorrules`, `.claude.md`, `.windsurfrules` | Additional conventions |

### Phase 2: Generate 9 Files

Always create `docs/agent-docs/` directory. Generate each file following the strict format template.

---

#### `CONTEXT.md` -- Entry Point (always generated)

```
# CONTEXT

Read this first. It describes the project, stack, structure, and key entry points.

## Project
[Name] -- [One-line purpose]

## Actors & Devices
| Actor | Device | Access |

## Stack
[One-line: runtime, framework, language, frontend, CSS, DB, ORM, realtime, auth, UI lib, icons]

## Repo Structure
```
root/
├── server/src/
│   ├── modules/  [list modules]
│   ├── shared/
│   ├── db/
│   └── index.ts
├── client/src/
│   ├── app/       [list routes]
│   ├── components/ [list directories]
│   ├── hooks/
│   └── lib/
├── docs/
│   └── agent-docs/   [list all 9 files with one-line purpose]
├── docker-compose.yml
└── README.md
```

## Key Files
| File | Purpose |

## Ports
| Service | Port |

## Read Order
1. CONTEXT.md → 2. STACK.md → 3. RULES.md → 4. ARCHITECTURE.md → 5. SCHEMA.md → 6. API.md → 7. PATTERNS.md → 8. DESIGN.md → 9. WORKFLOWS.md
```

---

#### `STACK.md` -- Versions Table (always generated)

```
# STACK

| Layer | Tech | Version | Dev-Kit |
|-------|------|---------|---------|
| Runtime | [node/python/.NET] | [version] | [dev-kit] |
| Language | [TypeScript/Python/C#] | [version] | [dev-kit] |
| ... | | | |

## Package Manager
[command]

## Module System
[ESM/CJS]

## Path Aliases
```json
{ "@/*": "./client/src/*", "@server/*": "./server/src/*" }
```
```

---

#### `RULES.md` -- Constraints (always generated)

Extract from linter configs, .editorconfig, existing docs, and conventions:

```
# RULES

Apply these before every file edit. Violations fail review.

## ALWAYS

```
// STRICT MODE
[TypeScript strict rules]

// ARCHITECTURE
[Layer rules: controller→service→repository]

// DATA TYPES
[Type rules for money, timestamps, etc.]

// STYLING
[Tailwind rules, component library rules]

// ACCESSIBILITY
[aria-label, role, aria-live rules]

// REACT PATTERNS
[State handling, exports, compound components]

// TESTING
[Co-location, AAA pattern]
```

## NEVER

```
// TYPES
No `any` type. No React.FC. No enums.

// IMPORTS
No barrel exports. No relative imports beyond ../../.
No `import *` for icon libraries.

// CODE QUALITY
No console.log in production. No raw SQL in services.
No `||` for defaults (use `??`). No `!` assertions.

// REACT
No default exports. No inline styles.
No `.env` in git.

// DATA
No deleting rows with FK refs (soft delete).
No skipping tenant/scope filter.
```

---

#### `ARCHITECTURE.md` -- Module Map (always generated)

```
# ARCHITECTURE

## Dependency Graph

```
A ──REST──► B ──► C
A ──WS──► D
```

## Server Modules

| Module | Path | Responsibility | Depends On |
|--------|------|---------------|------------|
| [name] | `src/modules/name/` | [1-line purpose] | [deps] |

## Client Routes

| Route | Layout | User | Nav Items |

## Data Flow (Main Use Case)

```
1. Actor → Action → Service → Repository → DB → Event
2. ...
```

## State Machine (if applicable)

```
state → state → state
```

## Component Tree (key screen)

```
Page
├── Component
│   └── ChildComponent
```
```

---

#### `SCHEMA.md` -- Database (generated if DB exists in stack)

```
# SCHEMA

## Enums

```
type: value | value | value
```

## Tables

```
TABLE name {
  col TYPE CONSTRAINTS FK→table.col
  col TYPE CONSTRAINTS
}
```

## Indexes

```
TABLE       INDEX                    COLUMNS              TYPE     REASON
```

## Notes
- [Design decision 1]
- [Design decision 2]
```

---

#### `API.md` -- Endpoints (generated if API exists)

```
# API

Base: `[url]/[prefix]`

Response: { data: T } or { data: T[], meta: { page, pageSize, totalItems, totalPages } }
Error:   { error: { code, message, details?: [{ field, reason }] } }

## [Resource Group]

| Method | Path | Auth | Request | Response |

## WebSocket Events (if applicable)

| Event | Direction | Payload | Description |

## Error Codes

| Code | HTTP | Meaning |
```

---

#### `PATTERNS.md` -- Code Patterns (always generated)

```
# PATTERNS

## Controller-Service-Repository
[Code block showing the pattern for this stack]

## State Machine
[Code block showing transition validation]

## Auth Middleware
[Code block]

## Error Class
[Code block]

## Optimistic Update (React) -- if frontend exists
[Code block]

## React State Pattern -- if frontend exists
[Code block]

## Compound Component -- if frontend exists
[Code block]

## Database Query Pattern
[Code block]

## File Naming Convention
Component: PascalCase.tsx    Hook: camelCase, use-     Util: camelCase
Schema: <module>.schema.ts   Test: <file>.test.ts      CSS: Never (Tailwind only)

## Test Pattern (AAA)
[Code block]
```

---

#### `DESIGN.md` -- Visual Tokens (generated if design tokens found)

```
# DESIGN

## [UI Library] Config
[Config JSON]

## Colors
```
primary: color-hex   accent: color-hex
success: color  error: color  warning: color  info: color
```

## Status → Color Maps
```
[Entity] status → color classes + icon
```

## Typography
```
xs:12px sm:14px base:16px lg:18px xl:20px 2xl:24px 3xl:30px 4xl:36px
[KDS/alternative scale if applicable]
```

## Spacing
```
Touch: min 48x48px, p-3/p-4
Click: min 32x32px, p-2/p-3
```

## Radius / Shadows
[Key=value format]

## Icons
Library: [name]   Import: [syntax]   Sizes per screen profile

## Layouts
[HTML structure per screen, classes only, no explanation]

## KDS/Alternative Theme (if applicable)
[Theme tokens as key=value]

## States
LOADING: [skeleton pattern]
EMPTY:   [empty state classes + structure]
ERROR:   [error alert classes + structure]

## Accessibility Checklist
- [Rule] (profile: required/recommended)
```

---

#### `WORKFLOWS.md` -- Dev Workflows (always generated)

```
# WORKFLOWS

## First Setup
```bash
[commands]
```

## Add Server Module
```bash
[commands]
```

## Add Client Page
```bash
[commands]
```

## Database Migration
```bash
[commands]
```

## Run Tests
```bash
[commands]
```

## Debug Real-Time (if applicable)
```bash
[commands]
```

## Seed Database (if seed exists)
```bash
[commands]
```

## Lint and Typecheck
```bash
[commands]
```

## Git Workflow
```bash
[commands]
```
Conventions: feat:|fix:|chore:|docs:|test:|refactor:

## Docker
```bash
[commands]
```

## CI Pipeline
```
Step 1 → Step 2 → Step 3
```
```

---

### Phase 3: Global Format Rules

Applied to every output file, no exceptions:

1. **Tables over paragraphs.** If the same info can be a table or a paragraph, use a table.
2. **Code blocks over descriptions.** If something is executable (command, config, query, pattern), put it in a code block.
3. **File paths as coordinates.** Use `server/src/modules/orders/orders.service.ts:45` instead of "in the orders service".
4. **Concrete values only.** No "around", "roughly", "usually", "typically". Use exact numbers and strings.
5. **No markdown decorations.** No `## Section` unless it is a functional label (used for scanning). No emojis. No horizontal rules unless separating major blocks.
6. **Target under 100 lines per file.** If a file exceeds this, the agent is including too much prose. Trim.
7. **RULES.md format.** Use ALL-CAPS sections (`ALWAYS:` / `NEVER:`) with bullet lists. Compact enough that an agent can prefix every prompt with these.
8. **Read order.** Every CONTEXT.md ends with numbered read order (1→9).
9. **Design values as key=value.** DESIGN.md uses `key: value` pairs or `key → value` maps. No paragraphs about color theory.
10. **Workflows as bash.** Every WORKFLOWS.md section is numbered commands starting with ````bash`.

---

## What NOT to do

- No generating files outside `docs/agent-docs/`. Never modify existing human docs.
- No prose explanations in output files. If a section would require a paragraph to explain, restructure it as a table or code block.
- No Mermaid diagrams. Use text dependency graphs (`A → B → C`).
- No inventing data. If the source docs don't specify a version, write `?` not a guess.
- No skipping the read order in CONTEXT.md. Every agent-docs folder must have a numbered read order.
- No generating SCHEMA.md if there's no database. No generating API.md if there's no API.
- No generating DESIGN.md if there are no design tokens anywhere in the project.
- CONTEXT.md, STACK.md, RULES.md, ARCHITECTURE.md, PATTERNS.md, WORKFLOWS.md are always generated regardless.
