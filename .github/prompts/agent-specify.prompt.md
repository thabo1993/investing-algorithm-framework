---
mode: agent
description: SDD Phase 1 — write a spec.md (what & why) from a feature idea.
---

Act as the `tech-lead` (bring in `mvp-architect` for greenfield product framing). Turn the feature
request into `specs/<###-short-name>/spec.md` using `.specify/templates/spec-template.md`.

Capture: user stories with priorities (P1/P2/P3), each with a *why this priority*, an *independent
test*, and Given/When/Then acceptance scenarios; functional requirements (FR-###, testable,
user-observable); key entities (conceptual, no schema); measurable, **technology-agnostic** success
criteria (SC-###); edge cases; assumptions. Mark every gap `[NEEDS CLARIFICATION: …]` — never guess.

**No implementation detail** (no stack, APIs, schemas, code). Run the template's Review & Acceptance
Checklist. Next: `/agent-clarify` if any markers remain, else `/agent-plan`.
Full spec: ../../skills/agent-specify/SKILL.md
