# Decision Register

A list of 40 open questions is unusable. Deduplicated and ordered by what they block, it is 25 questions that can be answered in three batches.

The register is a **working document** that becomes the project's decision log. It is the most valuable single artifact the pipeline produces, because it records not only what was decided but which alternatives were rejected and why.

---

## Step 1 — Collect

Gather from every source:

- Assumptions marked `[ASSUMED]` in any generated document
- Decisions the design requires but nobody has made
- Open questions in any "what is not yet defined" section
- The premises that the audit could not resolve

---

## Step 2 — Deduplicate

Assumptions and decisions overlap heavily. Merge them.

| Assumption | Decision | Merged question |
| :--- | :--- | :--- |
| "The stack is Next.js + NestJS" | "Decide the stack" | **P01 · Stack definitivo** |
| "The ORM is Drizzle" | "Decide the ORM" | **P04 · ORM definitivo** |
| "The team is 3 developers" | "Confirm team size" | **P02 · Tamaño del equipo** |
| "Kickoff on 2026-10-05" | "Confirm dates" | **P02** (derived from team size) |

A real case: 24 assumptions + 15 decisions = **39 items**, which deduplicated to **29 questions**, of which 8 resolved two items at once.

**Rule:** if two items cannot be answered differently, they are one question.

---

## Step 3 — Tier by blocking power

**Not by topic.** A topic grouping produces a register where the trivial and the critical sit side by side, and the user answers the trivial ones first because they are easy.

| Tier | Name | Blocks | Example |
| :--- | :--- | :--- | :--- |
| **0** | Foundation | Everything | Stack, team, governance |
| **1** | Before the first migration | Scaffold, schema, CI | ORM, multi-tenancy, identifiers, money |
| **2** | Security and operations | The go-live | Auth lifetimes, backup objectives, migration policy |
| **3** | Business parameters | Acceptance criteria | Thresholds, tolerances, retention |
| **4** | Scope and delivery | The schedule and quality | Phases, target platform, pilot size |
| **5** | Minor and cosmetic | Nothing | Naming, timezone, archival |

**Tiers 3–5 should almost always be closable with a default.** If a tier-5 question is blocking, it was tiered wrong.

---

## Step 4 — Recommend a value for every question

Every question gets a recommendation with a reason. A register without recommendations forces the user to research 25 topics; with them, most are a single approval.

```markdown
| ID | Question | Recommendation | Why | Blocks | Answer |
| :--- | :--- | :--- | :--- | :--- | :--- |
| P15 | Cash variance threshold | $50.00 MXN | Already the schema default; configurable per branch | POS-11 | ⬜ |
```

**The reason matters more than the recommendation.** It is what lets the user disagree productively.

---

## Step 5 — Present, then ask by tier

Show the whole register so the user sees the shape and the total. Then ask about the tier that blocks.

**Ask format that works:**

```markdown
## Tier 0 — the three that block everything

### P01 · Stack
[context, options A–E, recommendation, consequences of each]

### P02 · Team
[options A–E, recommendation]

### P03 · Governance
[open questions, template to fill]

---
Respond P01–P03 and I close tiers 1–5 with the recommendations already written.
```

Then the user replies in one message. **Do not ask one question per turn across 30 turns.**

---

## Step 6 — Record the answers, with their consequences

Each answer records:

- The **decision**
- The **consequences**, including which documents change
- The **date**
- Any **follow-on questions** the answer creates

```markdown
**Respuesta P01 (2026-09-21):** ✅ Stack modificado y aceptado.

Frontend: React 19 + Vite + Chakra UI v3
Backend:  NestJS 11
Datos:    PostgreSQL 18 + Drizzle

| Cambio | Consecuencia |
| :--- | :--- |
| Next.js → React + Vite | The web container becomes static files. Better for offline |
| Ant Design + Tailwind → Chakra | One design system instead of two. Removes a dependency risk |

Documentos afectados: ARQUITECTURA, SPEC, SCAFFOLD, ONBOARDING, README,
DEPENDENCIAS, agent-docs/, ADR-0002. Se emite el ADR-0010.
```

**A new decision that contradicts an accepted ADR requires a new ADR**, marking the old one superseded. Never edit an accepted ADR in place.

---

## Step 7 — Add the questions the reframe creates

When the premises change, new questions appear that the original set could not have contained.

A real case: reframing a client project as a solo portfolio project added **15 questions** that were not about the product at all:

| Category | Example |
| :--- | :--- |
| Direction | Which role is the portfolio aimed at? |
| Execution | Is AI used for boilerplate only, or for the hard parts too? |
| Visibility | Public or private? Which license? |
| Demo | What does the 3-minute video show? |
| Discipline | What is the frozen "won't do" list? |

**These are not product decisions, and they are not optional.** A portfolio project that does not decide them produces a repository nobody looks at.

---

## Step 8 — Close with a severity, not a count

The register ends with a progress block and a list of what remains open, each with an owner and a due date.

```
Tier 0  [██████]  3 de 3    ✅
Tier 1  [██████]  6 de 6    ✅
Tier 2  [██████]  5 de 5    ✅
Tier 3  [██████]  7 de 7    ✅
Tier 4  [██████]  3 de 3    ✅
Tier 5  [██████]  5 de 5    ✅
Tier 6  [██████]  1 de 1    ✅
Tier 7  [██████] 15 de 15   ✅
─────────────────────────────────
TOTAL   [██████████] 48 de 48
```

---

## Anti-patterns

| Anti-pattern | Why it is wrong |
| :--- | :--- |
| Ordering by topic | Trivial and critical questions get answered in the same batch, and the trivial ones are answered first |
| No recommendation per question | Forces the user to research every topic. Most should be a single approval |
| One question per turn | 30 turns for 30 questions. Batch by tier |
| Treating all answers as equal | Tier 0 changes the document set; tier 5 changes a constant |
| Closing a tier-0 answer without listing the affected documents | The change is not propagated, and the documents contradict each other |
| Editing an accepted ADR instead of superseding it | The reasoning history is destroyed |
| Asking the user what they want when a default is defensible | Wastes their attention. Recommend, and let them disagree |
| Not adding the questions the reframe creates | The register closes complete and the project is still undecided about the things that matter |

---

## Where the register lives

`docs/ACLARACIONES.md` in the author's working language, because it is a working document. It is **never** part of the portfolio surface, and it is the one document that should not be translated.

Its value as a portfolio artifact is indirect but real: it demonstrates that the premises were questioned, that alternatives were weighed, and that the author can distinguish a client requirement from their own design decision.
