# Completeness

A document set can be well written, internally consistent, and **missing the spine**. This is the checklist that catches it.

Fourteen classes. A project is documented when all fourteen exist.

---

## The fourteen classes

| # | Class | File | What it must contain | The failure if absent |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **Functional requirements** | `REQUIREMENTS.md` | Every requirement with a **stable ID**, MoSCoW priority, target release, and a **verifiable** acceptance criterion | Nothing else can reference anything. No traceability, no coverage, no scope control |
| 2 | **Non-functional requirements** | `NFR.md` | Measurable targets with a verification method, grouped by category, plus the targets deliberately not set | "Fast", "secure" and "reliable" are not requirements. Nothing is testable |
| 3 | **Architecture** | `ARCHITECTURE.md` | C4 levels 1–3, module boundaries **enforced mechanically**, state machines with transition tables, cross-cutting concerns | Modules drift into a ball of mud; state transitions become whoever-remembers |
| 4 | **Data model** | `SCHEMA.md` | Conceptual, logical and physical. DDL, index strategy where **each index answers a named query**, and the deferral plan for anything not built yet | Indexes get added reactively, or not at all. The schema is not reviewable before it exists |
| 5 | **API contract** | `API.md` + `api/openapi.yaml` | Full operation inventory, realtime events, error codes, and an executable contract for the current release | Client and server drift. Nothing is specified before it is implemented |
| 6 | **UI specification** | `UI.md` | Every screen, its states (loading, empty, error, edge), its constraints, and the rules that apply across screens | Screens are invented during implementation. Empty and error states are afterthoughts |
| 7 | **Design system** | `DESIGN-SYSTEM.md` | Tokens, motion, light, components with every state specified, microcopy, and **explicit prohibitions** | Every component is styled ad hoc. The product looks generic because nothing constrains it |
| 8 | **Security design** | `SECURITY.md` | Assets, a threat model with **residual risk per threat**, controls by layer, and **declared gaps with closure dates** | Security is a list of good intentions. Nobody knows what is deliberately not protected |
| 9 | **Critical flows** | `FLOWS.md` | Sequence diagrams for the flows that carry correctness, each with its failure and edge paths | The happy path is designed and the failure paths are discovered in production |
| 10 | **Technical specification** | `SPEC.md` | Business rules as `condition → action`, validations, error scenarios, testing strategy | Rules live only in code, and in the reviewer's memory |
| 11 | **Traceability** | `TRACEABILITY.md` | Requirement → endpoint → table → test. Orphan analysis both ways | No proof the design is complete. No proof an endpoint serves anything |
| 12 | **Operations** | `OPERATIONS.md` | Deploy, rollback, backup **with a rehearsal log**, monitoring thresholds, incident playbooks, capacity model | An unrehearsed restore is not a backup. Incidents are improvised |
| 13 | **Decisions** | `adr/` | One file per decision with context, **alternatives rejected**, consequences, and acceptance criteria | "Why is it like this?" has no answer six months later |
| 14 | **Reference** | `GLOSSARY.md`, `ROADMAP.md` | Domain vocabulary with terms deliberately avoided, plus releases with a definition of done | The same concept gets three names. Releases never close |

### Recommended, not required

| Class | File | Why |
| :--- | :--- | :--- |
| Project front page | `README.md` | The entry point. States what the project is and what it is not |
| Onboarding | `ONBOARDING.md` | How to get productive. Also how the author resumes after two weeks away |
| Changelog | `CHANGELOG.md` | Release history |
| Agent docs | `docs/agent-docs/` | Nine token-efficient files for AI consumption |
| Scaffold | `SCAFFOLD.md` | Repository layout and the execution order for the first release |
| Dependencies | `DEPENDENCIAS.md` | Version policy and the expected inventory |
| Risks | `RIESGOS.md` | The risk register |
| Decision log | `ACLARACIONES.md` | The register that produced every other decision |

---

## What makes a requirement real

Three properties. Without all three it is a wish.

| Property | Test | Example |
| :--- | :--- | :--- |
| **Stable ID** | Never reused, never renumbered, even if the requirement is dropped | `ORD-06` |
| **Verifiable criterion** | Can be asserted true or false, by a person or a test | "Re-sending the same `event_id` produces no duplicate effect" |
| **Explicit release** | It is clear which release delivers it | `v0.3` |

**Bad criterion:** "The system should handle mutations gracefully."
**Good criterion:** "An item in state `served` cannot be substituted; the request returns `ORDER_ITEM_ALREADY_SERVED`."

---

## What makes an NFR real

A target with a **number, a unit, and a measurement method**. If there is no way to measure it, it is not a requirement.

| Bad | Good |
| :--- | :--- |
| "Fast" | "Order → KDS delivery: p95 ≤ 2 s, measured from event emit to client receipt over 200 events" |
| "Secure" | "A rotated refresh token cannot be reused: 100% of reuse attempts invalidate the family" |
| "Reliable" | "RPO ≤ 24 h, RTO ≤ 4 h, verified by a timed restore rehearsal" |
| "Scalable" | "50 concurrent live orders per branch without degradation, verified by k6" |

**Also document the targets deliberately not set.** "Sub-100 ms p95 on writes" is not required because it would drive premature optimisation. Saying so prevents someone adding it later.

---

## The orphan analysis

The most valuable part of traceability. Run it in both directions.

### Forward — requirements with no design

| Orphan | Meaning | Resolution |
| :--- | :--- | :--- |
| Requirement with no endpoint | Either undesigned, or enforced internally | If internal (a state machine, a guard, a computed total), **declare it as such**. Do not leave it silent |
| Requirement with no test | No verification method | Add a test, or declare it as review-verified with a reason |
| Requirement with no release | Scope is undefined | Assign a release, or move it to the frozen exclusion list |

### Backward — design with no requirement

| Orphan | Meaning | Resolution |
| :--- | :--- | :--- |
| Endpoint with no requirement | Scope creep, or an operational need | Trace it to a requirement, or declare it in an explicit "operational need" table |
| Table with no requirement | Dead schema, or a missing requirement | Trace it, or remove it |
| Business rule with no requirement | A rule that exists only in prose | Give it a requirement ID |

> **A claim of "no orphans" is a claim that must be verified.** In a real case, the traceability matrix stated "Endpoints without a requirement: **None**" while listing six in an operational table. An automated check found **19**. The claim was false and only the check revealed it.

---

## Cross-consistency

Completeness and internal consistency are different failures. A set can be complete and contradict itself.

| Check | What it catches |
| :--- | :--- |
| **Count conflicts** | The same concept declared with different values in two documents |
| **ID references** | A document referencing a requirement or NFR that does not exist |
| **ADR references** | A document referencing a decision record that was never written |
| **Path references** | A document pointing at a file that does not exist |
| **Duplicated tables** | The same table in two documents, which drifts when one is updated |

Run these with `scripts/check-consistency.py`. They are mechanical and they catch what a human stops noticing after the second document.

---

## Completeness in the release cycle

Completeness is not a one-time gate. It degrades as the project evolves.

| Trigger | What to re-check |
| :--- | :--- |
| A new requirement is added | Does it have an ID, a criterion, a release, an endpoint and a test? |
| A release ships | Does the README state the actual scope? Do the counts still hold? |
| A decision changes | Is the ADR superseded rather than edited? Do the affected documents agree? |
| A document is rewritten | Are the cross-references still valid? |
| Before any commit | All three scripts |

---

## Anti-patterns

| Anti-pattern | Why it is wrong |
| :--- | :--- |
| Generating the fourteen classes before the premises are confirmed | Fourteen wrong documents, faster |
| Requirements without IDs | Nothing can reference them. Traceability becomes impossible retroactively |
| NFRs without numbers | Unverifiable. "Fast" survives every test |
| An ADR without rejected alternatives | It is a note, not a decision record. The reasoning is the value |
| A security section without declared gaps | Implies full coverage, which is never true and destroys trust in the document |
| An operations runbook with an untested restore | An unrehearsed restore is not a backup |
| Declaring "no orphans" without running the check | It is a claim, and claims need verification |
| Treating traceability as a one-time deliverable | It drifts on the first requirement change |
| Adding documents to reach fourteen | The classes are a checklist, not a quota. A missing class is a gap; a redundant one is noise |
