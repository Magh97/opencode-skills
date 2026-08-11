---
name: agent-design
description: 'Agent-optimized system design. Given context, produces composable sections: architecture (text dependency graph + module table), API (endpoint table), data schema (table blocks + indexes). No C4 theory, no REST conventions primer, no normalization explanation. Use when user says "design the architecture", "design the API", "design the schema", "design the system".'
requires-devkits: auto-detect
---

# Agent Design -- Architecture, API, and Schema Design

Produces compact, composable design output in agent-consumable format. No theory, no diagrams (text graphs only), no style comparisons.

---

## Workflow

### Step 1: Detect Scope

Read the user's request to determine which sections to generate:
- "architecture" / "system" → Architecture section
- "API" / "endpoints" → API section
- "schema" / "database" / "data model" → Schema section
- No specific scope → generate all three

### Step 2: Read Context

Read from project:
- Existing `docs/agent-docs/ARCHITECTURE.md`, `API.md`, `SCHEMA.md`
- `package.json` for stack
- Entity descriptions from spec docs

### Step 3: Generate Requested Sections

Each section is independent. Generate only what was requested.

---

## Architecture Section Template

```
## Dependency Graph
```
[Client] ──PROTOCOL──► [Server] ──► [Database]
[Client] ──PROTOCOL──► [Realtime Server]
```

## Containers (deployable units)
| Container | Tech | Port | Purpose |

## Server Modules
| Module | Path | Responsibility | Depends On |
|--------|------|---------------|------------|
| [name] | `src/modules/[name]/` | [1-line] | [deps] |

## Client Routes
| Route | Layout | User | Components |

## Data Flow (Main Use Case)
```
1. Actor → Action → Endpoint → Service → Repository → DB → Event
2. Event → Listener → Handler → State Change → Notification
```

## State Machine (if applicable)
```
state1 → state2 → state3
state1 → state4 (alternative path)
```
Valid transitions: [table]
```

## Component Tree (key screen, if frontend)
```
PageName
├── LayoutComponent
│   ├── HeaderComponent
│   └── ContentArea
│       ├── ListComponent
│       │   └── ItemComponent[]
│       └── DetailComponent
```

## Cross-Cutting Concerns
| Concern | Implementation |
|---------|---------------|
| Auth | [JWT middleware, role guards] |
| Logging | [structured logger, level] |
| Error handling | [global error handler, AppError class] |
| Validation | [Zod/Pydantic/DataAnnotations at controller boundary] |
```

---

## API Section Template

```
# API

Base: `[protocol]://[host]:[port]/[prefix]`

## Auth
Header: `Authorization: Bearer <jwt>` (unless marked `--` in Auth column)

## Response Format
Success: `{ data: T }` or `{ data: T[], meta: { page, pageSize, totalItems, totalPages } }`
Error:   `{ error: { code: string, message: string, details?: [{ field: string, reason: string }] } }`

## Pagination
Query params: `?page=1&pageSize=20` (max pageSize=100)

## [Resource Group 1]
| Method | Path | Auth | Request | Response |

## [Resource Group 2]
| Method | Path | Auth | Request | Response |

## WebSocket/Real-Time Events (if applicable)
| Event | Direction | Payload | Description |

## Error Codes
| Code | HTTP | Meaning |
```

---

## Schema Section Template

```
# Schema

## Enums
```
type_name: value1 | value2 | value3
```

## Tables
```
TABLE table_name {
  id              SERIAL PK
  foreign_id      INTEGER NOT NULL FK→other_table.id ON DELETE CASCADE
  name            VARCHAR(100) NOT NULL
  status          enum_type NOT NULL DEFAULT 'default_value'
  amount          NUMERIC(19,4) NOT NULL CHECK(amount > 0)
  is_active       BOOLEAN NOT NULL DEFAULT true
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
  updated_at      TIMESTAMPTZ
}
```

## Indexes
```
TABLE        INDEX_NAME              COLUMNS                 TYPE      REASON
─────        ──────────              ───────                 ────      ──────
table_name   idx_table_name_lookup   (col1, col2 DESC)       B-tree    query pattern description
table_name   idx_table_name_partial  (col) WHERE col='value'  PARTIAL   filtered query
table_name   idx_table_name_search   USING GIN(tsvector col)  GIN       full-text search
```

## Notes
- [Design decision about data types]
- [Design decision about constraints]
- [Design decision about soft deletes]
```

---

## Format Rules

1. **Architecture: text graph, not Mermaid.** Use `A → B → C` chains. Use indentation for component trees.
2. **API: one table per resource group.** Auth column uses `JWT`, `admin`, `cashier`, or `--`.
3. **Schema: compact blocks.** Use indentation for fields, no markdown table for schema (tables use it for indexes only).
4. **No version numbers in path unless project already uses them.** Default: `/api/resource` not `/api/v1/resource`.
5. **Currency as NUMERIC(19,4).** Always. Never FLOAT, REAL, or bare DECIMAL.
6. **Timestamps as TIMESTAMPTZ.** Always. Never TIMESTAMP WITHOUT TIME ZONE.
7. **FKs include ON DELETE behavior.** `CASCADE` for owned children, `RESTRICT` for referenced parents.

---

## What NOT to do

- No C4 model explanations. No "Level 1 shows the system context, Level 2 shows containers..."
- No REST conventions primer. No "use nouns for resources, HTTP methods for actions..."
- No normalization theory. No "1NF requires atomic columns, 2NF requires..."
- No Mermaid/PlantUML diagrams. Use text graphs only.
- No architectural style comparisons (monolith vs microservices vs event-driven).
- No technology comparisons unless explicitly asked.
- No generating all three sections if only one was requested.
- No design doc template with Context/Decision/Alternatives/Impact sections. That's an ADR.
