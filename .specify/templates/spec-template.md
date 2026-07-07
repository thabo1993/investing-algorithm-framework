# Feature Specification: [FEATURE NAME]

**Feature Branch:** `[###-feature-name]`
**Created:** [DATE]
**Status:** Draft
**Input:** [the original feature description / user request]

> Defines the **what** and the **why** — never the *how*. No tech stack, no APIs, no code here.
> That belongs in `plan.md`. Mark every guess or open question with **[NEEDS CLARIFICATION: …]**.

---

### Artifact Naming & Location Conventions

All SDD artifacts for this feature live under `specs/{###-feature-name}/`:

| Artifact | Path | Phase |
| --- | --- | --- |
| Specification | `specs/{###}/spec.md` | 1 · Specify |
| Design spec | `specs/{###}/design.md` | 1.75 · Design |
| Technical plan | `specs/{###}/plan.md` | 2 · Plan |
| Research notes | `specs/{###}/research.md` | 2 · Plan |
| Data model | `specs/{###}/data-model.md` | 2 · Plan |
| API contracts | `specs/{###}/contracts/*.md` | 2 · Plan |
| Task breakdown | `specs/{###}/tasks.md` | 3 · Tasks |
| Design system | `design-system/MASTER.md` | 1.75 · Design (global) |

**Naming rule:** `{###}` is a zero-padded 3-digit number (e.g., `001`, `012`) followed by a
short kebab-case slug (e.g., `001-user-auth`, `012-team-workspaces`). Numbers are assigned
sequentially and never reused — even if a feature is cancelled.

---

---

## User Scenarios & Testing *(mandatory)*

Each user story is an independently testable, deployable, demonstrable slice of value. Order by
priority; the highest priority alone should be a usable increment.

### User Story 1 — [short title] (Priority: P1)
[One or two sentences describing the journey from the user's perspective.]

**Why this priority:** [the value that justifies P1 — what breaks/blocks without it]

**Independent test:** [how this story can be tested on its own, with no later story present]

**Acceptance scenarios:**
1. **Given** [initial state], **When** [action], **Then** [observable outcome].
2. **Given** […], **When** […], **Then** […].

### User Story 2 — [short title] (Priority: P2)
[…] · **Why:** […] · **Independent test:** […]
**Acceptance scenarios:** 1. **Given** … **When** … **Then** …

### User Story 3 — [short title] (Priority: P3)
[…]

### Edge Cases
- What happens when [boundary / empty / huge / concurrent / offline / unauthorized input]?
- How does the system behave when [dependency fails / partial write / retry]?

---

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001:** The system MUST [capability, stated in user-observable terms].
- **FR-002:** The system MUST [capability].
- **FR-003:** Users MUST be able to [action].
- **FR-004:** The system MUST [data the system retains, without prescribing storage tech].
- *Example of an under-specified requirement to flag:*
  **FR-005:** The system MUST authenticate users via **[NEEDS CLARIFICATION: method not specified — SSO, email/password, passwordless?]**.

### Key Entities *(if the feature involves data)*
- **[Entity]:** [what it represents, its key attributes, and its relationships — conceptually, not as a schema].

---

## Success Criteria *(mandatory)*

Measurable, **technology-agnostic** outcomes that prove the feature works.
- **SC-001:** [e.g., "Users complete [task] in under 3 steps / 30 seconds."]
- **SC-002:** [e.g., "95% of [operations] succeed on first attempt."]
- **SC-003:** [a business/UX metric, not an implementation metric].

---

## Assumptions
- [Decisions made where the request was silent — state them so they can be corrected early.]

## Review & Acceptance Checklist
- [ ] No implementation detail (stack, APIs, code) has leaked into this spec.
- [ ] Every requirement is testable and unambiguous (no unresolved [NEEDS CLARIFICATION]).
- [ ] Each user story is independently testable and has a clear priority.
- [ ] Success criteria are measurable and technology-agnostic.
- [ ] Scope is bounded — out-of-scope items are listed under Assumptions.
