---
mode: agent
description: SDD Phase 4 — execute tasks.md to build the feature, then run the specialist polish pass.
---

Execute `specs/<feature>/tasks.md` in order. Prerequisite: `/agent-analyze` passed.

Complete Setup → Foundational first (don't start a story until the Foundational checkpoint is
green). Then build user stories in priority order: write the acceptance test first (per the spec's
Given/When/Then), implement until it passes, stop at the checkpoint and confirm the story is
independently demoable. Use `frontend-engineer` for UI and the plan's architecture for backend;
production-ready code with validation and error handling. Respect `[P]` (parallel) vs. sequential.

Polish phase — delegate: `security-auditor` (audit changed surface, fix Critical/High),
`performance-optimizer` (profile + optimize hot paths), `devops-engineer` (deploy/runbook, CI,
observability). Then run `/agent-analyze` once more to confirm code ↔ spec ↔ plan ↔ tasks agree.

Build only what the tasks specify; behavior must match the spec's acceptance criteria. All
in-session, no external LLM. Full spec: ../../skills/agent-implement/SKILL.md
