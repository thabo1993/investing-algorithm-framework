# Constitution Review Checklist

Validates a project constitution (governing engineering principles) is complete and ready to gate all future plans.

## Coverage & Scope

- [ ] Constitution defines architectural principles (monolith vs. microservices, layers, patterns)
- [ ] Technology choices are stated (approved languages, frameworks, databases)
- [ ] Quality standards are explicit (testing approach, code review requirements)
- [ ] Deployment & operations approach is documented (CI/CD, monitoring, rollback)
- [ ] Security & compliance requirements are listed
- [ ] Performance baselines or SLAs are defined
- [ ] Accessibility standards are specified (WCAG level, minimum target)

## Clarity & Enforceability

- [ ] Each principle is stated as a clear rule, not a vague guideline
- [ ] Rules are specific enough to gate a plan (yes/no, not maybe)
- [ ] Rules include examples of what passes and what violates
- [ ] Escape hatches (exceptions and how to request them) are documented
- [ ] Decision-making process is clear (who approves exceptions)

## Completeness Across Dimensions

- [ ] Architecture dimension: system design, scaling approach
- [ ] Technology dimension: language, framework, database, deployment targets
- [ ] Quality dimension: testing, code review, standards
- [ ] People dimension: team size assumptions, skill requirements
- [ ] Timeline/Cost dimension: acceptable tech debt, MVP scope
- [ ] Risk dimension: acceptable failure modes, security posture

## Team Alignment

- [ ] Constitution was written or approved by technical leadership
- [ ] All team members have seen and understood the constitution
- [ ] Deviations require explicit approval (not implicit allowance)
- [ ] Rationale for each principle is documented (why this, not that)

## Operationalization

- [ ] Constitution includes a checklist or gate (used by /agent-plan)
- [ ] Plans are checked against constitution before proceeding
- [ ] Violations are logged (with justification if approved)
- [ ] Constitution is reviewed periodically (when to revisit, how to amend)

## Readiness Gate

- [ ] Constitution is complete and comprehensive
- [ ] Leadership has approved it
- [ ] Team understands it and the consequences of violating it
- [ ] Constitution is in `.specify/memory/constitution.md`
- [ ] Ready to gate all future plans and decisions

## Scoring

| Score | Rating | Action |
|-------|--------|--------|
| 100% | Approved | Adopt as gating rule for /agent-plan |
| 75-99% | One More Pass | Clarify ambiguous rules, add missing dimensions |
| 50-74% | Incomplete | Add missing coverage, define enforcement |
| Below 50% | Insufficient | Restart — constitution not ready |
