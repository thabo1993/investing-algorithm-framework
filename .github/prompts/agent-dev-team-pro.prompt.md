---
mode: agent
description: Build a feature through the full Spec-Driven Development lifecycle with the specialist team.
---

Run the engineering team through the full **Spec-Driven Development** lifecycle on this task,
working turn-by-turn **inside this one session** (no external LLM). Use the `.specify/` templates
and check work against `.specify/memory/constitution.md`.

Walk the phases in order, adopting the right persona at each and carrying each artifact into the next:

1. **Constitution** (`tech-lead`) — confirm/amend `.specify/memory/constitution.md`.
2. **Specify** (`tech-lead`/`mvp-architect`) — write `specs/<###-name>/spec.md` from the spec
   template: user stories (P1/P2/P3), testable requirements, measurable success criteria. Mark gaps
   `[NEEDS CLARIFICATION]`. No tech here.
3. **Clarify** (`tech-lead`) — ask the questions whose answers change the design; resolve the markers.
4. **Plan** (`backend-architect`/`mvp-architect`/`clean-architect`) — `plan.md` + research, data
   model, contracts. Run the **Constitution Check** gate.
5. **Tasks** — `tasks.md`: ordered phases (Setup → Foundational → user stories → Polish), `[P]`
   markers, `[US#]` tags.
6. **Analyze** (`codebase-auditor`) — verify spec ↔ plan ↔ tasks consistency; fix Critical/High before building.
7. **Implement** — build per tasks (acceptance test first per story, checkpoints between), then a
   polish pass: `security-auditor`, `performance-optimizer`, `devops-engineer`.

Honor the gates: don't plan with open clarifications, don't build on a failed Constitution Check or
a failing Analyze. Deliver: constitution status, spec, plan, tasks, analyze verdict, working
implementation, and a traceability note (story → tasks → code).

Full spec: ../../skills/agent-dev-team-pro/SKILL.md · phase skills: ../../skills/agent-*
