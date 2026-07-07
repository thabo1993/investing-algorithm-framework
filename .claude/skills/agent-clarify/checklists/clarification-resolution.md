# Clarification Resolution Checklist

Validates that all [NEEDS CLARIFICATION] markers in a spec have been resolved before planning.

## Marker Resolution

- [ ] All [NEEDS CLARIFICATION: ...] markers in spec.md have been addressed
- [ ] For each resolved marker, user answer is documented inline in the spec
- [ ] No new ambiguities were introduced during clarification process
- [ ] Answers are definitive (not still tentative or "to be determined")

## Question Quality

- [ ] Questions asked were clarifying only (not prescriptive "you should use X")
- [ ] Questions addressed the actual gap (not tangential concerns)
- [ ] Questions were specific enough to resolve the ambiguity
- [ ] Follow-up questions (if any) closed the loop completely

## Spec Integrity After Clarification

- [ ] No implementation detail was introduced (still no tech stack)
- [ ] User stories remain independently testable and prioritized
- [ ] Success criteria remain measurable and technology-agnostic
- [ ] Scope boundaries are still clear (no scope creep)
- [ ] Assumptions are still valid or have been updated

## Traceability

- [ ] Each resolved clarification links back to a specific user story or functional requirement
- [ ] No answer introduced a new user story that is undocumented
- [ ] Resolved answers can be traced to user responses (not inferred by the agent)
- [ ] Spec still reflects original user intent — no intent drift during clarification

## Constitution Compliance

- [ ] No answers introduced a technology choice that would violate the constitution
- [ ] No answers expanded scope beyond what the constitution's MVP guideline allows
- [ ] If a clarification answer implies a new architectural concern, it is flagged for plan phase

## Readiness Gate

- [ ] Zero [NEEDS CLARIFICATION] markers remain in spec.md
- [ ] User has confirmed all answers capture their intent
- [ ] Spec is now unambiguous enough to plan against
- [ ] No new clarifications are anticipated during planning

## Scoring

| Score | Rating | Action |
|-------|--------|--------|
| 100% | Ready for Plan | Proceed to /agent-plan |
| 75-99% | One More Round | Address remaining gaps, re-clarify |
| Below 75% | Insufficient | Return to /agent-specify; spec not ready |
