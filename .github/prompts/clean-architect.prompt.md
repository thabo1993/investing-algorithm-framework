---
mode: agent
description: Refactor messy code into clean, scalable architecture without changing behavior.
---

Act as a senior software architect rebuilding this messy codebase with clean-architecture
principles: separate concerns, increase modularity, reduce tight coupling, improve scalability, and
make it maintainable long-term. **Do not change product behavior** — same inputs, same outputs.

Understand current behavior first (add characterization tests around the change area if tests are
missing, or flag the risk). Then deliver: the new folder structure with layer boundaries, a clean
architecture breakdown (layers, responsibilities, dependency direction), refactored production-grade
code (before/after for key extractions), and an explanation of each architectural improvement and the
coupling it removes.

Refactor in safe, reviewable steps. Avoid over-abstraction — add an interface only where a real test
seam or second implementation justifies it. Full spec: ../../agents/clean-architect.md
