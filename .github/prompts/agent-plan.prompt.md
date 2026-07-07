---
mode: agent
description: SDD Phase 2 — turn an approved spec into a technical plan (the how).
---

Adopt the right architect — `backend-architect` (service/API/data), `mvp-architect` (greenfield),
or `clean-architect` (rework) — and produce `plan.md` (+ `research.md`, `data-model.md`,
`contracts/`) from `specs/<feature>/spec.md` using `.specify/templates/plan-template.md`.

Prerequisite: the spec has **no open `[NEEDS CLARIFICATION]`** (else run `/agent-clarify` first).

Fill Summary + Technical Context, then the **Constitution Check** gate against
`.specify/memory/constitution.md` — any unchecked article must be justified in Complexity Tracking
or you fix the design. Phase 0 research resolves unknowns (decisions + alternatives + rationale);
Phase 1 design produces the data model, contracts, and per-critical-path test strategy; re-check the
constitution after design. Pick one source structure and say why.

Implement the spec, don't expand it. Minimal but scalable — name the seam, don't build it. No tasks
or code here. Next: `/agent-tasks`. Full spec: ../../skills/agent-plan/SKILL.md
