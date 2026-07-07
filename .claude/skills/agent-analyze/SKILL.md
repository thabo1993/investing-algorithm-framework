---
name: agent-analyze
type: standalone
version: 0.1.0
category: phase
description: >-
  Cross-artifact consistency and coverage check across spec.md, plan.md, tasks.md (and code), run
  by the codebase-auditor persona. Catches drift, gaps, and constitution violations before
  implementation. Spec Kit style. Triggers: /agent-analyze, "check consistency", "validate the spec/plan/tasks".
allowed-tools: [Read, Glob, Grep, Bash]
model: opus
---

# /agent-analyze — validate consistency before (and after) building

A read-only gate. Confirm the artifacts agree with each other and with the constitution before you
implement — and again after, to confirm the code matches. Drive this with the **`codebase-auditor`**
persona: evidence over opinion, no behavior changes.

## Steps
1. **Load** `spec.md`, `plan.md`, `tasks.md` for the feature (and the implementation, if it exists).
2. **Check coverage & consistency:**
   - Every functional requirement (FR-###) maps to at least one task and, eventually, to code.
   - Every user story has an acceptance test task and an implementation task.
   - The plan's data model & contracts are reflected in tasks; no orphan tasks invent scope.
   - Terminology is consistent across artifacts (same entity = same name).
   - No `[NEEDS CLARIFICATION]` survives into plan or tasks.
3. **Constitution re-check:** confirm the plan's Constitution Check still holds and the tasks don't
   violate an article (e.g. behavior changes smuggled into a "refactor", secrets handling, missing
   tests on critical paths).
4. **Report**, with `file:line` / `FR-###` / `T###` references — ranked by severity.

## Output
- **Consistency report:** table of findings — Issue | Severity | Artifact ref | Fix.
- A verdict: **PASS** (ready to implement / shippable), or the specific gaps to close first.

## Guardrails
- Read-only. This skill reports; it does not edit spec/plan/tasks/code — it sends you back to the
  right phase to fix the gap.
- Don't pass the gate with unresolved Critical/High findings. Next step: fix at the source phase,
  then `/agent-implement` (or ship, if this is the post-build check).
