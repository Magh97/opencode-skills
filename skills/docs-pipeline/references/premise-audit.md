# Premise Audit

An idea document states what the system does. It never states what it assumes. **The assumptions are where the project dies.**

This step runs **before** any document is generated, and it blocks.

---

## The three premises that change everything

Ask these first. If any is wrong, the shape of the whole set changes.

### 1. Who builds it

| Answer | What changes |
| :--- | :--- |
| **A team of 3–8** | The roadmap can parallelise. Module boundaries matter for coordination. Documentation is an interface between people |
| **One person** | Every parallel workstream is fiction. The roadmap must be sequenced, not parallelised. Documentation is a memory aid |
| **One person, part-time, with AI** | CRUD compresses 2–3×; hard parts compress ~1.3×. The ordering must put the interesting work early, while motivation is highest |
| **An agency** | Estimates and handover documents matter more than design depth |

**The question to ask:** *"How many people will write this, and how many hours a week?"*

### 2. Who it is for

| Answer | What changes |
| :--- | :--- |
| **A paying client** | Requirements are demands. They can be validated, and someone can say no. Scope changes need approval |
| **The author's portfolio** | Every "requirement" is a design decision. Nobody can say no, so the author must. Deployment and demo matter more than completeness |
| **Internal users** | Adoption risk is real; the tool competes with a spreadsheet |
| **A spec exercise** | The deliverable is the document, and implementation is out of scope |

**The question to ask:** *"Who will use this, and who decides what goes in it?"*

> This is the highest-consequence premise. A portfolio project documented as a client project produces requirements with no owner, a stakeholder map with no stakeholders, and a timeline nobody agreed to.

### 3. Where it runs

| Answer | What changes |
| :--- | :--- |
| **One host the author controls** | Docker Compose. No Kubernetes. One `docker-compose.yml` is the deployment |
| **A cloud provider, undecided** | The architecture must not assume a provider. Avoid provider-specific APIs |
| **On-premise at the customer's site** | Hardware, network, backups and physical failure become real requirements |
| **The author's laptop, for a demo** | Deployment is not a requirement yet, and pretending otherwise wastes pages |
| **Undecided** | Say so, and design for portability. Do not invent a topology |

**The question to ask:** *"Where will this run, and who operates it?"*

---

## Secondary premises worth auditing

| Premise | Why it matters |
| :--- | :--- |
| **Is there a deadline?** | With no deadline, abandonment and perfectionism replace lateness as the top risks |
| **Is there a budget?** | Zero budget rules out managed databases, brokers and per-seat licensing |
| **Is the domain regulated?** | Health, finance and minors' data change the retention and audit requirements |
| **Does the author know the domain?** | If not, the "requirements" are plausible guesses and must be labelled as such |
| **Is the stack already chosen, and by whom?** | A stack chosen by the author is reversible; one imposed by a client or a team's skill set is not |
| **Does hardware exist?** | Features needing a printer, a scanner or a terminal cannot be tested or demoed without it |

---

## How to run the audit

### Step 1 — Extract the stated premises

Read the input and list every explicit claim: actors, scale, stack, phases, features.

### Step 2 — Extract the unstated premises

For each stated claim, ask what it presupposes.

| Stated | Presupposes |
| :--- | :--- |
| "Fase 1: MVP en 8–10 semanas" | A team, or a very small scope. Which? |
| "El Gerente configura el catálogo" | There is a Gerente, and they will use it |
| "Sincronización con la nube" | There is a cloud, and someone pays for it |
| "Impresión térmica de comandas" | There is a printer, and it has been tested |
| "Reporte consolidado de franquicia" | There is more than one branch, and they are real |
| "Auditoría del 100% de operaciones" | Someone reads the audit log |

### Step 3 — Classify each

| Class | Meaning | Action |
| :--- | :--- | :--- |
| **Verified** | The user confirmed it | Use as-is |
| **Plausible** | Reasonable but unchecked | Mark `[ASSUMED]` and list it for confirmation |
| **False** | Contradicted by another answer or by arithmetic | **Recompute everything that depends on it** |
| **Unknown** | Nobody knows yet | Design so it can be decided later, at low cost |

### Step 4 — Do the arithmetic on the false ones

A false premise usually means the plan does not fit. Show the number.

```
Stated:    MVP of 12 modules in 8–10 weeks
Implied:   3 developers × 10 weeks × 40 h = 1,200 h
Actual:    1 developer, 12 h/week
Result:    1,200 ÷ 12 = 100 weeks ≈ 2 years
```

**Do not soften this.** A plan that does not fit is the most valuable thing the audit produces.

### Step 5 — Present the corrected framing

Output, in this order:

1. **The three primary premises**, with the answer and the consequence
2. **The false premises** found, with the arithmetic
3. **What changes** in the document set as a result
4. **The questions that must be answered** before generating anything

---

## Anti-patterns

| Anti-pattern | Why it is wrong |
| :--- | :--- |
| Assuming a client because the document says "el cliente" | The document may be describing a hypothetical. Ask |
| Assuming a team because the roadmap has parallel tracks | A roadmap with parallel tracks written by one person is a wish |
| Accepting the proposed stack without asking who chose it | A stack imposed by team skill is a constraint; one chosen freely is a decision |
| Generating documents while the premises are open | Produces documents that must be archived. This is the expensive mistake |
| Softening the arithmetic to avoid discouraging the user | A plan that does not fit is the finding. Hiding it wastes months |
| Treating "portfolio project" as a downgrade | It is a different objective, not a lesser one. The rules change; the rigour does not |

---

## What the audit is not

- **Not a requirements elicitation.** It does not ask what the system should do. It asks what the plan assumes.
- **Not a feasibility study.** It checks whether the numbers fit, not whether the product will succeed.
- **Not a blocker on detail.** Tiers 1–5 of the decision register can stay open. Only the primary premises block.
