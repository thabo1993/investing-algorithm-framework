---
name: agent-plan
type: standalone
version: 0.1.0
category: phase
description: >-
  Turn an approved spec into a technical implementation plan (the HOW): tech context, constitution
  check, architecture, data model, contracts, research. Spec Kit style, executed by the architect
  agents. Triggers: /agent-plan, "plan the implementation", "how should we build this".
allowed-tools: [Read, Write, Glob, Grep, Bash, AskUserQuestion]
model: opus
---

# /agent-plan — design the implementation (how)

Phase 2 of Spec-Driven Development. Produce `plan.md` (+ `research.md`, `data-model.md`,
`contracts/`) from the spec. This is where architecture lives — and where the **Constitution
Check** gates the work.

## Prerequisites
- `specs/<feature>/spec.md` exists with **no open `[NEEDS CLARIFICATION]`**. If any remain, stop and run `/agent-clarify` first.
- **For UI-heavy features:** `specs/<feature>/design.md` and `design-system/MASTER.md` exist (produced by `/agent-design`). If absent, run `/agent-design` first — the architect plans the component structure *from* the wireframes, not by inventing it.

## Persona — pick the architect for the work
- Backend / API / data-heavy service → **`backend-architect`**
- Greenfield product / full-stack MVP → **`mvp-architect`**
- Refactor or rework of an existing system → **`clean-architect`**
- UI-led feature → **`ux-designer`** has already produced `design.md` (wireframes, component map,
  chart spec); feed that to the architect alongside `spec.md`. The architect plans *around* the
  design, not past it.
Spawn the chosen agent via the Agent tool, feeding it `spec.md` + `design.md` + `design-system/MASTER.md` (if they exist).

## Steps
1. Start `plan.md` from `.specify/templates/plan-template.md`.
2. **Summary + Technical Context** — language, dependencies, storage, testing, platform, project
   type, performance goals, constraints, scale. Mark unknowns `NEEDS CLARIFICATION`.
3. **Constitution Check (gate).** Fill the article table against `.specify/memory/constitution.md`.
   Any unchecked article must be justified in *Complexity Tracking* or the plan fails — fix the
   design instead of hand-waving.
4. **Phase 0 — Research** → `research.md`: resolve every unknown; record decisions, alternatives
   considered, and rationale.
5. **Phase 1 — Design** → `data-model.md` (entities, fields, relationships) and `contracts/`
   (API/interface definitions) + the test strategy for each critical path. Re-run the Constitution
   Check after design.
6. Choose ONE source-code structure option and note why.

## Output
- `plan.md`, `research.md`, `data-model.md`, `contracts/` under `specs/<feature>/`.
- Constitution Check result: PASS, or the justified deviations.

## Guardrails
- The plan implements the spec — it does not expand scope. New scope → back to `/agent-specify`.
- Minimal but scalable: name the scaling seam instead of building it now (Constitution Article II).
- Do not write task lists or code here. Next step: `/agent-tasks`.
