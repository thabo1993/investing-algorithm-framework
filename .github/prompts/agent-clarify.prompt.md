---
mode: agent
description: SDD Phase 1.5 — resolve spec ambiguities before planning.
---

Act as the `tech-lead`. Load `specs/<feature>/spec.md`, collect every `[NEEDS CLARIFICATION]`
marker plus any detectable ambiguity (undefined terms, unstated scale, missing error behavior,
vague success criteria, unbounded scope).

Ask the user only the questions whose answers would actually change the spec or plan — batched,
≤5, with concrete options where possible. Then update `spec.md` in place: replace each resolved
marker with the decision and fold new constraints into Requirements/Assumptions/Success Criteria.

Don't ask what you can reasonably assume — state the assumption instead. Output the updated spec
plus a clarification log (question → answer → where it changed the spec). Next: `/agent-plan`.
Full spec: ../../skills/agent-clarify/SKILL.md
