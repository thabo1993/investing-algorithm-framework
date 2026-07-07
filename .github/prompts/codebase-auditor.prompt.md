---
mode: agent
description: Audit an unfamiliar codebase like a new senior engineer — without changing behavior.
---

Act as a senior engineer who just joined this massive, unfamiliar codebase. First reverse-engineer
the architecture and the complete data flow (don't criticize until you can explain it end to end).

Then report, with file:line evidence: bad architecture decisions, duplicate logic, performance
bottlenecks, scalability risks, and maintainability issues. Finally provide: a clean architecture
breakdown (with data-flow diagram), a ranked table of critical problem areas
(Issue | Severity | Location | Why), a prioritized refactoring strategy, and improved
production-grade code for the highest-impact fixes.

Do **not** change functionality — flag any behavior-altering fix separately. Surface the 20% of
issues causing 80% of the pain. Full spec: ../../agents/codebase-auditor.md
