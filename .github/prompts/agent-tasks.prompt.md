---
mode: agent
description: SDD Phase 3 — generate an ordered, dependency-aware tasks.md from the plan.
---

Convert `specs/<feature>/plan.md` (+ data-model, contracts) into `tasks.md` using
`.specify/templates/tasks-template.md`. Prerequisite: the plan passed its Constitution Check.

Derive tasks from the artifacts: each contract → an implementation task + contract test; each entity
→ a model/migration task; each user story → its own phase with an acceptance-test task **before**
implementation tasks. Order by phase: Setup → Foundational (blocking) → user-story phases (priority
order) → Polish, with checkpoints between. Use the format `[ID] [P?] [Story] Description (path)`;
tag `[P]` only for different-file, no-dependency tasks. In Polish, delegate cross-cutting tasks to
`security-auditor`, `performance-optimizer`, `devops-engineer`, and end with a `/agent-analyze` task.

Tasks come only from the plan — a gap means the plan is incomplete. Next: `/agent-analyze` then
`/agent-implement`. Full spec: ../../skills/agent-tasks/SKILL.md
