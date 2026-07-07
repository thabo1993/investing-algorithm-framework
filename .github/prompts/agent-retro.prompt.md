---
mode: agent
description: Reflect after a run — capture lessons that future runs read back. The self-improvement loop.
---

Run a retrospective on the agent or pipeline work that just completed. Mine it for lessons, in
priority order: **user corrections** (strongest signal), **redos** (the agent backtracked),
**false assumptions** (something assumed turned out wrong), and **reinforcers** (worked well, make
it the default). A lesson is valid only if it's tied to concrete evidence from the run — never
invent lessons; an empty retro is a fine outcome.

Classify each lesson into one of two tiers:
- **Project-local** — true only in *this* repo → append to `.claude/learnings/<agent>.md` (one file
  per agent; create if absent; never overwrite existing entries).
- **Universal** — would improve the agent *everywhere* → propose in `IMPROVEMENTS.md` at repo root as
  a reviewable edit to the agent's definition, for a human to PR upstream.

When unsure, file as project-local (the reversible default). Each entry records: signal, evidence,
the actionable lesson, and optional scope.

**Guardrails:** lessons refine *how* an agent works — they never relax a read-only, no-deploy, or
security guardrail. Never edit an agent definition directly; universal changes stay human-gated. If
a learnings file grows past ~20 entries, distill it.

Full spec: ../../skills/agent-retro/SKILL.md
