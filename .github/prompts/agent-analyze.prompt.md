---
mode: agent
description: SDD gate — cross-artifact consistency check across spec, plan, tasks, and code.
---

Act as the `codebase-auditor` (read-only, evidence over opinion). Load `spec.md`, `plan.md`,
`tasks.md` for the feature (and the code, if it exists) and verify they agree.

Check: every FR-### maps to a task (and eventually code); every user story has an acceptance-test
task and an implementation task; the plan's data model & contracts are reflected in tasks; no orphan
task invents scope; terminology is consistent; no `[NEEDS CLARIFICATION]` survived into plan/tasks.
Re-check the Constitution: behavior not silently changed under "refactor", secrets handled, critical
paths tested.

Report findings ranked by severity with `file:line` / `FR-###` / `T###` refs, and a verdict: PASS
or the gaps to close. This skill reports only — fix gaps at the source phase, don't edit here. Next:
fix, then `/agent-implement` (or ship, post-build). Full spec: ../../skills/agent-analyze/SKILL.md
