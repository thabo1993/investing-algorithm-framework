---
name: agent-design
description: SDD Phase 1.75 — run the ux-designer to produce a complete design spec (information architecture, wireframes, design-system/MASTER.md, component map, chart selection, pre-delivery checklist) BEFORE the technical plan is written.
---

# /agent-design — design before you build

Phase 1.75 of Spec-Driven Development. This phase exists because without it the `frontend-engineer`
invents the design while coding, producing interfaces that work but communicate poorly. The
`ux-designer` answers "what, how it looks, and how it behaves" — so the architect and engineer
answer only "how it is built."

## Where this sits

```
/agent-clarify  →  /agent-design  →  /agent-plan  →  /agent-tasks  →  /agent-implement
                        ↑
              produces design spec and design system
              that architect reads alongside spec.md
```

## Prerequisite

`specs/<feature>/spec.md` exists with no open `[NEEDS CLARIFICATION]`. The design spec
implements the *what* in the spec; it must not expand or contradict it.

## Spawn `ux-designer` via the Task tool

Feed it the complete `spec.md` and ask it to work through all 6 steps:
0. Industry reasoning — classify the product and apply the matching rules
1. Information architecture (content hierarchy + navigation map + layout grid)
2. User flows (one per user story, with loading/empty/error/success marked)
3. Wireframes (text/ASCII for every key screen — actual labels, not placeholders)
4. Chart type selection (data shape → chart type → why → library recommendation)
5. Design system output (`design-system/MASTER.md` + `specs/<feature>/design.md`)
6. Component map (name, states, props sketch, interaction spec, a11y notes)

Then run the Pre-Delivery Checklist and fix anything failing before handoff.

## Outputs — create these files

```
design-system/
└── MASTER.md               # global source of truth: tokens, colors, type, effects, charts

specs/<###-feature-name>/
└── design.md               # feature-specific: IA, user flows, wireframes, component map
```

The design system persists across features: if `MASTER.md` already exists, check whether this
feature extends it (add page-specific overrides in `design-system/pages/<feature>.md`) or
whether it introduces new patterns that belong in the master.

## What the plan reads from this

When `/agent-plan` runs next, it reads `design.md` and `design-system/MASTER.md` to:
- Choose the component structure around the wireframes (not invent it)
- Select the right charting libraries from the chart-type decisions
- Scope the frontend implementation around the component map and states
- Avoid redesigning what has already been designed

## Guardrails

- Design spec only — no framework code, no CSS. Implementation detail goes in the plan.
- Every wireframe must use actual content labels ("EUR/USD 1.0847 ▲+0.12%"), not "label here".
- Mark every design assumption that goes beyond the spec — the product owner can correct it.
- Pre-Delivery Checklist must pass before handoff; a failing checklist is a failing gate.
- For trading/financial dashboards: dark mode is not optional; light mode default is an
  anti-pattern (baked into the ux-designer's industry reasoning).
