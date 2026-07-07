# Artifact Consistency Checklist

Validates consistency and coverage across spec.md, plan.md, tasks.md, and (post-implementation) code before proceeding or shipping.

## Spec ↔ Plan Alignment

- [ ] Every user story (spec) is addressed in the plan
- [ ] Every functional requirement (FR-xxx from spec) is solved by plan components
- [ ] Success criteria (SC-xxx from spec) have measurable checkpoints in the plan
- [ ] No new scope has been added to the plan (everything in plan is in spec)
- [ ] No scope from spec has been dropped without documenting why

## Plan ↔ Tasks Alignment

- [ ] Every component in the plan has corresponding tasks
- [ ] Every data model entity is implemented by a task
- [ ] Every API endpoint (from plan) has a task for implementation + testing
- [ ] Task ordering respects plan dependencies
- [ ] No tasks exist that don't trace to the plan

## Tasks ↔ Code Alignment (Post-Implementation)

- [ ] All tasks are marked complete (acceptance criteria verified)
- [ ] Code artifacts match task descriptions (no unplanned changes)
- [ ] No code was written that wasn't in tasks.md
- [ ] All acceptance criteria pass (no workarounds or deferred items)
- [ ] Code reflects the architecture described in plan.md

## Constitution Adherence (All Phases)

- [ ] Plan was checked against constitution (recorded in plan.md)
- [ ] No code violates constitution rules
- [ ] If constitution trade-offs were made, they're documented with justification
- [ ] Any constitution violations are acknowledged and approved by stakeholder

## Gap Detection

- [ ] No [NEEDS CLARIFICATION] markers remain in spec
- [ ] No "TBD" or "TODO" items remain in plan or tasks
- [ ] No unresolved dependencies between tasks
- [ ] No features partially implemented (all-or-nothing per phase)

## Coverage Completeness

- [ ] All P1 user stories are implemented (code complete + tested)
- [ ] All FR-xxx functional requirements are implemented
- [ ] All SC-xxx success criteria have passing tests or metrics
- [ ] All edge cases (from spec) are addressed
- [ ] All assumptions (from spec) are still valid or documented as changed

## Quality Gates

- [ ] Security review completed (if required by constitution)
- [ ] Performance testing completed (if required by constitution)
- [ ] Accessibility tested (if required by constitution)
- [ ] Code review completed
- [ ] Acceptance tests passing

## Readiness Gate

- [ ] Zero gaps between spec, plan, tasks, and code
- [ ] Constitution is satisfied
- [ ] All quality gates passed
- [ ] Stakeholder approval received
- [ ] Ready to ship or proceed to next phase

## Scoring

| Score | Rating | Action |
|-------|--------|--------|
| 100% | Ship It | Ready for production or next phase |
| 75-99% | Fix & Ship | Address gaps, retest, then ship |
| 50-74% | Rework | Significant drift — revisit and realign |
| Below 50% | Stop | Fundamental mismatch — back to planning |
