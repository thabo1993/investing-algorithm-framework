# Tasks Review Checklist

Validates a completed tasks.md (work breakdown) before implementation begins.

## Task Structure & Ordering

- [ ] Tasks are numbered sequentially and correspond to plan.md components
- [ ] Task dependencies are explicit (which tasks must complete before which)
- [ ] Critical path is identified (blocking tasks marked or documented)
- [ ] Parallel markers [P] are used correctly (indicates true independence)
- [ ] No circular dependencies exist
- [ ] Ordering supports phased rollout (MVP → V1 → V2)

## Task Completeness

- [ ] Each task has a clear title (what, not how)
- [ ] Each task has a description (why it matters, what success looks like)
- [ ] Each task has acceptance criteria (pass/fail checkpoints)
- [ ] Each task references relevant plan.md section or artifact
- [ ] Each task estimated or T-shirt-sized (S/M/L) if estimation is used

## Phasing & User Stories

- [ ] Tasks are grouped by phase (MVP, V1, V2, etc.)
- [ ] Each phase delivers measurable value (matches a user story or SC-xxx)
- [ ] Phase transitions are clear (what triggers moving to the next phase)
- [ ] P1 user stories have all their tasks in Phase 1
- [ ] Later phases don't block Phase 1 completion

## Acceptance Criteria Quality

- [ ] Acceptance criteria are specific and measurable (not vague)
- [ ] Criteria reference checklists where appropriate (e.g., "passes spec-review checklist")
- [ ] Criteria include QA/testing steps where needed
- [ ] Each criterion is pass/fail (no subjective "looks good")
- [ ] Criteria include security, performance, or accessibility checks where relevant

## Traceability to Spec & Plan

- [ ] Every user story (from spec) has corresponding tasks
- [ ] Every functional requirement (FR-xxx) is addressed by a task
- [ ] Success criteria (SC-xxx) have measurable task completion checkpoints
- [ ] No tasks exist that don't trace back to the plan or spec

## Constitution Compliance

- [ ] All tasks honor constitution rules (no forbidden tech, patterns, or approaches)
- [ ] Security tasks are included if the constitution requires security review
- [ ] Accessibility tasks are included if the constitution requires WCAG compliance
- [ ] No task implicitly defers a constitution-required deliverable to a later phase

## Readiness Gate

- [ ] Engineer can start work without requesting clarification
- [ ] Task descriptions are detailed enough for asynchronous execution
- [ ] All blockers and dependencies are documented
- [ ] Estimated effort is realistic (no 40-hour tasks)
- [ ] High-risk or unknown tasks are noted

## Scoring

| Score | Rating | Action |
|-------|--------|--------|
| 100% | Ready to Build | Proceed to /agent-implement |
| 75-99% | Fix & Ship | Address gaps, document unknowns |
| 50-74% | Reorder Required | Significant dependencies or phasing issues |
| Below 50% | Insufficient | Return to plan — tasks cannot be written |
