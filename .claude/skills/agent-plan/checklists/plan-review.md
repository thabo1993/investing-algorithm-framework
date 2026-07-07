# Plan Review Checklist

Validates a technical implementation plan (plan.md + supporting artifacts) against the spec and constitution before task generation.

## Constitution Alignment

- [ ] Plan has been checked against `.specify/memory/constitution.md`
- [ ] All constitution rules are honored (no violations)
- [ ] If any rule would be broken, violation is documented with justification
- [ ] Plan passes or explicitly acknowledges constitution trade-offs

## Spec-to-Plan Traceability

- [ ] Each user story (from spec) maps to one or more plan components
- [ ] All functional requirements (FR-xxx) are addressed in architecture or tech decisions
- [ ] Success criteria (SC-xxx) have measurable implementation checkpoints
- [ ] No user stories have been dropped or deprioritized without noting why
- [ ] Scope stays within spec bounds (no undocumented additions)

## Technical Architecture

- [ ] System components are clearly identified and their responsibilities defined
- [ ] Data flow between components is explicitly documented
- [ ] External dependencies (APIs, services, libraries) are listed with versions
- [ ] Scalability approach matches spec requirements (no over-engineering)
- [ ] Security, performance, and reliability approaches are addressed
- [ ] Trade-offs and alternatives are documented (why this choice over that one)

## Data Model

- [ ] Key entities from spec are modeled (tables, collections, or domain objects)
- [ ] Relationships between entities are defined and cardinality is clear
- [ ] Primary keys, foreign keys, and unique constraints are specified
- [ ] No implementation detail leaks in from earlier phases (still conceptual)
- [ ] Data persistence strategy is chosen (database type, caching, storage)

## Contracts & APIs

- [ ] Public API endpoints are defined (method, path, request/response schema)
- [ ] Message formats (JSON, protobuf, etc.) are specified
- [ ] Error codes and error handling strategy are documented
- [ ] Rate limits or quotas are defined if applicable
- [ ] Authentication and authorization approach is specified

## Research & Decisions

- [ ] Research artifacts (if any) are included and summarized
- [ ] Open questions or unknowns are documented
- [ ] Alternative approaches considered are listed with pros/cons
- [ ] Decision rationale is clear (why this tech, not that tech)

## Readiness for Task Breakdown

- [ ] Plan is detailed enough to generate tasks from
- [ ] Engineer can begin implementation without asking for clarification
- [ ] All critical unknowns have been resolved (no "TBD" items)
- [ ] Phasing strategy is clear (MVP → V1 → V2)

## Scoring

| Score | Rating | Action |
|-------|--------|--------|
| 100% | Ready for Tasks | Proceed to /agent-tasks |
| 75-99% | Fix & Recheck | Address gaps, document unknowns |
| 50-74% | Rework Required | Significant gaps — revisit architecture |
| Below 50% | Insufficient | Return to spec — plan cannot be written |
