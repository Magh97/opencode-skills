---
name: agent-spec
description: 'Agent-optimized technical specification. Given a user story or feature description, produces a structured spec: endpoints, entities, business rules, states, UI components. No iterative questioning -- auto-fill assumptions and flag them for review. Use when user says "spec this", "technical spec", "specification for", "define this feature".'
requires-devkits: auto-detect
---

# Agent Spec -- User Story to Technical Specification

Converts user stories into structured specs. Auto-fills assumptions, flags them. No iterative questioning.

---

## Workflow

### Step 1: Receive Input

Accept any of:
- User story: "As a [user], I want to [action], so that [benefit]"
- Feature description: "Add a payment form for..."
- Bug report: "When [action], [unexpected behavior]"
- Loose idea: "We need a way to..."

### Step 2: Detect Stack

Read project files:
- `package.json` → runtime, framework
- `STACK.md` if in `docs/agent-docs/`
- Config files → DB, ORM, UI library

If no project: ask "What stack?" once.

### Step 3: Auto-Fill and Generate

Generate spec with intelligent defaults. Mark auto-filled assumptions with `[ASSUMED]` prefix.

```
# Spec: [Feature Name]

## Stack
| Layer | Tech | Version |

## Assumptions (review before implementing)
[ASSUMED] 1. [Auto-filled assumption]
[ASSUMED] 2. [Auto-filled assumption]

## Endpoints (new/modified)
| Method | Path | Auth | Request Body | Response | Errors |

## Entities (new/modified)
| Entity | Fields | Relations | Notes |

## Business Rules
- [Rule 1: condition → action]
- [Rule 2: condition → constraint]

## States / Transitions (if applicable)
```
state1 → state2 → state3
```

## UI Components (if frontend)
| Component | Screen | Props | States (loading/empty/error/edge) |

## Validation Rules
| Field | Rule | Error Code |

## Error Scenarios
| Scenario | Expected Behavior | Error Code |

## What's NOT Defined
- [ ] [Gap that needs human decision]
- [ ] [Gap that needs human decision]
```

### Step 4: Flag for Review

Always output: `> [ASSUMED] = auto-filled. Review these before implementing.`

---

## Auto-Fill Conventions

When the source doesn't specify, assume these defaults:

| Domain | Default |
|--------|---------|
| Auth | JWT Bearer (if users exist). No auth for public endpoints. |
| Pagination | `?page=1&pageSize=20&pageSize=max=100` for all GET list endpoints |
| Response format | `{ data }` / `{ error: { code, message } }` |
| Soft delete | `is_active=false` for users, products. Hard delete for items within a transaction. |
| IDs | Auto-increment integer, exposed in API |
| Timestamps | `created_at`, `updated_at` on every table |
| Currency | `NUMERIC(19,4)`, never FLOAT |
| Validation | Zod (Node), Pydantic (Python), DataAnnotations (.NET) |
| Error codes | `NOT_FOUND`, `VALIDATION_ERROR`, `CONFLICT`, `FORBIDDEN`, `UNAUTHORIZED` |

---

## Format Rules

- Tables for endpoints, entities, business rules. Never paragraphs.
- States as `→` chains: `draft → in_kitchen → ready → closed`.
- Business rules as `condition → action` one-liners.
- Error scenarios as table rows, not prose.
- UI components include "States" column listing loading/empty/error/edge cases.

---

## What NOT to do

- No iterative questioning. Auto-fill, flag, output. User can correct after.
- No Fase 0-4 with progress bars. Generate spec in one pass.
- No "Suposiciones Asumidas" with descriptions. `[ASSUMED]` prefix + one-liner.
- No prose explanations of why an assumption was made.
- No generating what's already defined in existing docs. Reference existing entities/endpoints.
- No stakeholder analysis, no budget, no timeline. That's agent-planning.
