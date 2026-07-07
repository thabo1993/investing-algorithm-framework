---
name: agent-tasks
type: standalone
version: 0.1.0
category: phase
description: >-
  Generate an ordered, dependency-aware tasks.md from an approved plan, grouped by phase and user
  story with [P] parallel markers. Spec Kit style. Triggers: /agent-tasks, "break this into
  tasks", "generate the task list".
allowed-tools: [Read, Write, Glob, Grep, Bash, AskUserQuestion]
model: opus
---

# /agent-tasks — break the plan into actionable tasks

Phase 3 of Spec-Driven Development. Convert `plan.md` (+ `data-model.md`, `contracts/`) into a
sequenced `tasks.md` that an engineer — or the `/agent-implement` pipeline — can execute.

## Prerequisite
`specs/<feature>/plan.md` exists and passed the Constitution Check.

## Steps
1. Start `tasks.md` from `.specify/templates/tasks-template.md`.
2. **Derive tasks** from the plan's artifacts:
   - Each contract/interface → an implementation task (and a contract test).
   - Each entity in `data-model.md` → a model/migration task.
   - Each user story in the spec → its own phase with an acceptance-test task **before** its
     implementation tasks.
3. **Order by phase:** Setup → Foundational (blocking) → User Story phases (priority order) →
   Polish. Put checkpoints between phases.
4. **Mark parallelism.** Tag `[P]` only where tasks touch different files with no unfinished
   dependency. Tag each story task with its `[US#]` for traceability.
5. **Use the format** `[ID] [P?] [Story] Description (file path)` and include concrete paths from
   the plan's chosen structure.
6. In the Polish phase, delegate cross-cutting tasks to specialists: `security-auditor`,
   `performance-optimizer`, `devops-engineer`.

## Output
- `specs/<feature>/tasks.md` — ordered, dependency-aware, with [P] markers and a final
  `/agent-analyze` task.
- A one-line summary: N tasks across M phases; the first usable increment is US1 (T###–T###).

## Guardrails
- Tasks come only from the plan — don't invent scope. A gap means the plan is incomplete; fix the plan.
- Every user story must remain independently testable. Next step: `/agent-analyze` then
  `/agent-implement`.
