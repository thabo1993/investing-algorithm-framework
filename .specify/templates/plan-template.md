# Implementation Plan: [FEATURE NAME]

**Branch:** `[###-feature-name]` | **Spec:** [link to spec.md] | **Date:** [DATE]

> The **how**. Derived from `spec.md`. If the spec still has unresolved [NEEDS CLARIFICATION],
> stop and run `/agent-clarify` first. This plan, plus `research.md`, `data-model.md`, and
> `contracts/`, is the input to `/agent-tasks`.

## Summary
[The primary requirement (from the spec) + the chosen technical approach in 2–4 sentences.]

## Technical Context
- **Language / Version:** [e.g. TypeScript 5.x / Python 3.12 — or NEEDS CLARIFICATION]
- **Primary Dependencies:** [frameworks, libraries]
- **Storage:** [DB / files / N/A]
- **Testing:** [test framework + strategy]
- **Target Platform:** [server / browser / mobile / CLI]
- **Project Type:** [single | web (frontend + backend) | mobile + api]
- **Performance Goals:** [throughput, latency, or "domain-typical"]
- **Constraints:** [hard limits — latency budget, memory, offline, compliance]
- **Scale / Scope:** [users, data volume, request rate]

## Constitution Check
*Gate: must pass before Phase 0 and again after design. Map each article to this plan.*

| Article | Compliant? | Note / justification if not |
| --- | --- | --- |
| I — Spec before code | ☐ | spec.md approved, no open clarifications |
| II — Minimal but scalable | ☐ | the named scaling seam(s): … |
| III — Behavior is sacred | ☐ | N/A new feature / or: behavior preserved by … |
| IV — Evidence over opinion | ☐ | |
| V — Test-first for critical paths | ☐ | critical paths + their tests: … |
| VI — Security & operability | ☐ | input validation, secrets, authz, observability, rollback |
| VII — Stay in-session | ☐ | |
| VIII — Simplicity & reversibility | ☐ | one-way doors flagged: … |

Any ☐ left unchecked must appear in **Complexity Tracking** with a justification, or the plan
fails the gate.

> ⚠️ **Article VI (Security & operability) cannot be waived via Complexity Tracking.** It must
> check ✓ — or the plan must be redesigned until it does. "Security will be added later" is not
> an accepted justification. If compliance is genuinely impossible for this feature, that is a
> product decision requiring explicit user sign-off, not a planning shortcut.

## Project Structure

### Artifacts (this feature)
```
specs/[###-feature-name]/
├── spec.md          # the what/why (input)
├── plan.md          # this file
├── research.md      # decisions, alternatives considered, rationale
├── data-model.md    # entities, fields, relationships
├── contracts/       # API contracts / interface definitions
└── tasks.md         # produced by /agent-tasks
```

### Source code (choose ONE and delete the others)
```
# Option A — single project
src/{models,services,cli,lib}/         tests/{unit,integration}/

# Option B — web (frontend + backend)
backend/src/{models,services,api}/     backend/tests/
frontend/src/{components,pages,lib}/   frontend/tests/

# Option C — mobile + api
api/src/...                            mobile/src/...
```
**Chosen structure:** [A/B/C] — [one-line why].

## Phases
- **Phase 0 — Research** (`research.md`): resolve every Technical Context unknown; record decisions,
  the alternatives considered, and the rationale.
- **Phase 1 — Design** (`data-model.md`, `contracts/`): entities, interfaces/API contracts, and the
  test strategy per critical path. Re-run the Constitution Check after this phase.
- **Phase 2 — Tasks**: produced by `/agent-tasks` (do not write tasks here).

## Complexity Tracking
*Only fill this in if the Constitution Check has an unchecked article. Each row justifies a
deliberate deviation.*

| Article violated | Why it's necessary | Simpler alternative rejected because |
| --- | --- | --- |
| | | |
