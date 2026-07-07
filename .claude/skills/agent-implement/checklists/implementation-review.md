# Implementation Review Checklist

Validates that completed code matches the spec, plan, and tasks.md before delivery.

## Spec Fidelity

- [ ] All user stories (from spec) have working implementations
- [ ] All functional requirements (FR-xxx) are implemented
- [ ] Code behavior matches the acceptance scenarios (Given/When/Then)
- [ ] No user stories were skipped or partially implemented
- [ ] Success criteria (SC-xxx) are measurable and metrics are available

## Code Quality

- [ ] Code follows team coding standards (or documented exceptions exist)
- [ ] Code is readable and maintainable (not premature optimization)
- [ ] No dead code, unused imports, or commented-out sections
- [ ] Naming conventions are consistent (variables, functions, classes)
- [ ] Functions are focused (single responsibility, reasonable length)

## Testing Coverage

- [ ] Unit tests exist for business logic
- [ ] Integration tests cover user story flows
- [ ] Edge cases (from spec) are tested
- [ ] Error handling is tested (invalid input, boundary conditions)
- [ ] All tests pass (no skipped or xfail tests)

## Acceptance Criteria Verification

- [ ] Every task acceptance criterion is verified as passing
- [ ] QA checklist (if applicable) is complete and signed off
- [ ] No workarounds or deferred items in completed tasks
- [ ] All [P] parallel tasks completed and integrated successfully

## Architecture & Design

- [ ] Code structure matches plan.md architecture
- [ ] Data model matches plan (tables, schemas, entities)
- [ ] API contracts match plan (endpoints, request/response formats)
- [ ] No architectural shortcuts or "technical debt" introduced
- [ ] Performance approach (caching, indexing, etc.) is implemented

## Security & Compliance

- [ ] Sensitive data is not logged or exposed in error messages
- [ ] Input validation is in place for user input
- [ ] Authentication/authorization is implemented per plan
- [ ] Security review completed (if required by constitution)
- [ ] No hardcoded secrets or credentials in code

## Documentation

- [ ] Code comments explain the "why", not the "what"
- [ ] Public APIs/functions have docstrings
- [ ] README or runbook explains how to run/deploy the code
- [ ] Data schemas are documented
- [ ] Known limitations or future work are noted (if any)

## Deployment Readiness

- [ ] Code builds and runs without errors
- [ ] All dependencies are explicitly declared (no implicit versions)
- [ ] Environment variables are documented
- [ ] Database migrations (if any) are reversible
- [ ] Deployment checklist (if applicable) is complete

## Scoring

| Score | Rating | Action |
|-------|--------|--------|
| 100% | Ship It | Ready for production deployment |
| 75-99% | Fix & Ship | Address gaps, test, then deploy |
| 50-74% | Rework | Significant quality issues — revisit code |
| Below 50% | Restart | Critical failures — back to tasks |
