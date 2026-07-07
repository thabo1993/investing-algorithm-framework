---
mode: agent
description: Run a full engineering team (Architect → Engineer → Reviewer → Optimizer) in one session.
---

Act as four elite engineering roles collaborating on this task, working the pipeline turn-by-turn
**inside this one session** (no external LLM):

1. **Architect** — design the scalable system architecture for the task.
2. **Engineer** — implement it as production-ready code.
3. **Reviewer** — perform a senior-level code review and list the required changes (critique, don't rewrite).
4. **Optimizer** — apply the review feedback and harden for production (performance, scalability, edge cases).

Carry each role's output into the next so context flows down the pipeline; re-anchor on the original
task at every handoff. If a role's output is weak, redo that role with specific feedback before
advancing. Match process weight to task size — collapse roles for small tasks.

Deliver, in order: **complete architecture**, **full implementation**, **review feedback**, and the
**final optimized version**, plus a short note on what each role contributed and any open decisions.
Full spec: ../../skills/agent-dev-team-fast/SKILL.md
