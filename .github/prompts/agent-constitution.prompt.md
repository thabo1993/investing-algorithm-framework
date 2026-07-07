---
mode: agent
description: SDD Phase 0 — create/amend the project constitution (governing principles).
---

Act as the `tech-lead`. Create or amend `.specify/memory/constitution.md` — the governing
principles every implementation plan is checked against. Read the current constitution first.

Each article must be concrete, testable against a plan, and justified by a real risk it removes —
no vague platitudes, no leftover `[BRACKETS]`. Version it semantically (MAJOR: remove/redefine an
article; MINOR: add/expand; PATCH: clarify) and update the ratified/amended dates. If an amendment
changes what plans must satisfy, update the Constitution Check table in
`.specify/templates/plan-template.md`.

Output the constitution plus an amendment summary (version bump, what changed, affected templates).
Next: `/agent-specify`. Full spec: ../../skills/agent-constitution/SKILL.md
