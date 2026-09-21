# Language Split

Documents are written for a reader. Different readers need different languages, and translating a working document is effort with no benefit.

**The split is by audience, not by preference.**

---

## The rule

| Surface | Language | Reader |
| :--- | :--- | :--- |
| `README.md` | **English** | The first thing an external reader opens |
| `ARCHITECTURE.md`, `API.md`, `SCHEMA.md`, `UI.md`, `SECURITY.md`, `FLOWS.md`, `SPEC.md`, `TRACEABILITY.md`, `NFR.md`, `REQUIREMENTS.md`, `DESIGN-SYSTEM.md` | **English** | A reviewer, an implementer, or a model |
| `adr/` | **English** | The reasoning is read by whoever inherits the project |
| `agent-docs/` | **English** | Models perform better and the technical vocabulary is more precise |
| `CHANGELOG.md` | **English** | Conventional commits are English |
| Code identifiers, database tables, columns, enums | **English** | Industry standard. Nobody writes `crearOrden()` on an international team |
| API endpoints and business error messages | **English** | The contract is public |
| `ACLARACIONES.md` (decision log) | **Author's language** | A working document. The author reads it, nobody else does |
| `ROADMAP.md`, `RIESGOS.md`, `DEPENDENCIAS.md`, `SCAFFOLD.md` | **Author's language** | Working documents |
| `STATUS.md` | **Author's language** | A personal progress note |

---

## Why not one language everywhere

| Option | Cost | Benefit |
| :--- | :--- | :--- |
| **Everything in English** | High. Translating a 1,200-line decision log is a day of work | None. Nobody external reads it |
| **Everything in the author's language** | Closes the international market at near-zero saving | None. The portfolio surface becomes unreadable to a reviewer |
| **Split by audience** | None. Each document is written once, in the language its reader uses | Every document is readable by its actual reader |

---

## When to decide

**Before the first migration.** Identifier names are the expensive part:

```
Before implementation   rename 33 tables in one document        ~1 hour
After v0.2 ships        migrations over live data + rename
                        types, endpoints and components          days
```

If the target market is international, decide English identifiers immediately. If the market is local, the author's language is a genuine advantage: the domain vocabulary is native and the documents read better.

**Either choice is defensible. Not deciding is not**, because the cost grows with every table.

---

## What the split looks like in practice

```
project/
├── README.md                        English
├── ONBOARDING.md                    English
├── CHANGELOG.md                     English
└── docs/
    ├── REQUIREMENTS.md              English
    ├── NFR.md                       English
    ├── ARCHITECTURE.md              English
    ├── SCHEMA.md                    English
    ├── API.md                       English
    ├── api/openapi.yaml             English
    ├── UI.md                        English
    ├── DESIGN-SYSTEM.md             English
    ├── SECURITY.md                  English
    ├── FLOWS.md                     English
    ├── SPEC.md                      English
    ├── TRACEABILITY.md              English
    ├── OPERATIONS.md                English
    ├── GLOSSARY.md                  English
    ├── ROADMAP.md                   working language
    ├── RIESGOS.md                   working language
    ├── DEPENDENCIAS.md              working language
    ├── SCAFFOLD.md                  working language
    ├── ACLARACIONES.md              working language
    ├── adr/                         English
    ├── agent-docs/                  English
    └── archive/                     mixed, preserved as-is
```

---

## UI copy is a separate decision

The language of the **interface** is not the language of the **documentation**. It follows the market the product serves.

| Situation | UI copy |
| :--- | :--- |
| A real restaurant in Mexico | Spanish |
| An international demo | English |
| Unknown | English, and treat it as a placeholder |

Write the design system's microcopy in one language and **flag it as the tone reference** rather than the final copy. The tone survives translation; the words do not.

---

## Anti-patterns

| Anti-pattern | Why it is wrong |
| :--- | :--- |
| Mixed languages within one document | The reader switches cognitive mode every paragraph |
| Spanish identifiers with English documentation | The reviewer reads `orden_detalle` in an English schema table and slows down |
| Translating the decision log | A day of work for a document nobody external reads |
| Deciding the language after the schema exists | Renaming 33 tables over live data is a migration, not a rename |
| Translating the design system's microcopy word for word | The tone is what transfers. A literal translation loses the voice |
| Assuming "English = professional" | A well-written document in the author's language beats a clumsy translation |

---

## The check

`scripts/check-docs.py` detects the language of each document by counting function words and applies the emoji rule accordingly: emoji are forbidden in English documents and allowed in working documents.

That is deliberate. A design system has a legitimate typographic character set (`→` in a state machine, `✓` in a table). A working document uses emoji as structure, which is fine. An English technical document using emoji is a convention violation.
