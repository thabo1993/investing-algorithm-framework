---
name: agent-implement
type: standalone
version: 0.1.0
category: phase
description: >-
  Execute tasks.md to build the feature per the spec and plan, phase by phase, with checkpoints —
  then run the specialist polish pass (security, performance, deploy). Spec Kit style. Triggers:
  /agent-implement, "build it", "implement the tasks", "execute the plan".
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash]
model: opus
---

# /agent-implement — build the feature from the tasks

The final phase of Spec-Driven Development. Work through `tasks.md` in order, honoring the phase
checkpoints, and keep the code faithful to `spec.md` and `plan.md`.

## Prerequisite
`specs/<feature>/tasks.md` exists and `/agent-analyze` passed.

## Steps
1. **Setup → Foundational.** Complete these blocking phases first; do not start a user story until
   the Foundational checkpoint is green.
2. **User stories in priority order.** For each story: write its acceptance test first (Article V),
   then implement until the test passes. Stop at the checkpoint and confirm the story is
   independently demoable before moving on.
   - **Frontend/UI tasks:** spawn `frontend-engineer`, feeding it the **wireframes and component
     map from `specs/<feature>/design.md`** and the **design tokens from
     `design-system/MASTER.md`**. The engineer implements what the design specifies — it does not
     re-design. If the design spec is missing, stop and run `/agent-design` first.
   - **Backend tasks:** use the architect's plan for backend — production-ready code with
     validation and error handling.
3. **Respect `[P]`.** Parallelizable tasks (different files, no unfinished dependency) may be done
   together; everything else is sequential.
4. **Polish phase — delegate to specialists** (spawn via the Agent tool):
   - **`security-auditor`** → audit the changed surface; fix Critical/High.
   - **`performance-optimizer`** → profile and optimize the hot paths.
   - **`devops-engineer`** → deployment/runbook, CI, observability for what shipped.
5. **Close the loop.** Run `/agent-analyze` once more to confirm code ↔ spec ↔ plan ↔ tasks agree.

## Output
- The implemented feature (real files), with tasks checked off in `tasks.md`.
- Acceptance tests passing per user story.
- Polish summary: security findings fixed, performance wins, deployment notes.
- Final consistency verdict.

## Guardrails
- Build only what the tasks specify. A needed-but-missing task means the plan/tasks are incomplete —
  go back and add it, don't freelance scope.
- Behavior must match the spec's acceptance criteria; don't "improve" beyond it silently.
- Everything runs in-session via personas/subagents — no external LLM (Constitution Article VII).
- **Governance files are off-limits.** Implementation agents must not modify
  `.specify/memory/constitution.md`, `.specify/templates/`, `CLAUDE.md`, `INSTALL.md`,
  `README.md`, or `docs/security-report.md`. Changes to any governance file require a separate,
  explicit user request — they are never a side-effect of implementing a feature.
