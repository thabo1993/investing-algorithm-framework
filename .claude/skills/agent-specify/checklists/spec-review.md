# Spec Review Checklist

Validates a completed spec.md against Spec-Driven Development requirements before planning begins.

## Requirements Completeness

- [ ] All user stories have a priority (P1, P2, or P3)
- [ ] Each user story includes a "Why this priority" explanation
- [ ] Each user story includes an "Independent test" (testable in isolation)
- [ ] Each user story has acceptance scenarios in Given/When/Then format
- [ ] Functional Requirements (FR-xxx) are written in user-observable terms
- [ ] All Key Entities are defined conceptually (no schema/database design)
- [ ] Success Criteria (SC-xxx) are measurable and technology-agnostic
- [ ] Edge cases section identifies boundary conditions and failure modes
- [ ] Assumptions section documents decisions made where request was silent

## No Implementation Leakage

- [ ] No framework names (React, Django, PostgreSQL, etc.) appear in the spec
- [ ] No API endpoints or database schemas are specified
- [ ] No code snippets or pseudo-code present
- [ ] No tech stack decisions or architecture patterns mentioned
- [ ] "How" questions are deferred to plan.md, not answered here

## Clarity & Testability

- [ ] No [NEEDS CLARIFICATION] markers remain unresolved
- [ ] Every requirement is stated as a clear pass/fail criterion
- [ ] User stories are ordered by business priority (P1 should be usable alone)
- [ ] Feature scope is bounded — out-of-scope items listed in Assumptions
- [ ] Success criteria are specific (measurable, with numbers or timeframes)

## Constitution Compliance

- [ ] If a constitution exists (`.specify/memory/constitution.md`), the spec does not commit to anything that would violate it
- [ ] No technology decisions appear that would pre-empt the constitution's stack rules
- [ ] Scope is bounded within what the constitution's MVP/complexity guidelines allow
- [ ] If the feature requires a new architectural pattern, it is flagged for constitution review

## Readiness Gate

- [ ] Spec document matches `specs/{###-short-name}/spec.md` filename
- [ ] Original user request is captured in the "Input" field
- [ ] Status field reflects current state (Draft/Clarifying/Ready for Plan)
- [ ] Created date is present and current

## Scoring

| Score | Rating | Action |
|-------|--------|--------|
| 100% | Ready for Plan | Proceed to /agent-plan |
| 75-99% | Fix & Recheck | Address gaps, re-run this checklist |
| 50-74% | Clarify First | Run /agent-clarify before replanning |
| Below 50% | Restart Spec | Fundamental gaps — redesign with user |
