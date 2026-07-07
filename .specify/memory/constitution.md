# Engineering Team Constitution

The governing principles for any work this engineering team produces. Every `/agent-plan`
runs a **Constitution Check** against these articles; a violation must be either fixed or
explicitly justified in the plan's *Complexity Tracking* table before implementation proceeds.

**Version:** 1.2.0 | **Ratified:** 2026-06-11 | **Last amended:** 2026-07-04

---

## Article I — Specification before code
No implementation begins without an approved `spec.md` (the *what* and *why*) and a `plan.md`
(the *how*). Code serves the spec; the spec is the source of truth. Ambiguities are resolved via
`/agent-clarify` **before** planning — not discovered during implementation.

## Article II — Minimal but scalable
Build the smallest thing that satisfies the spec and could scale to many times current load
**without a rewrite**. Do not build machinery the current scale doesn't need; instead *name the
seam* in the plan where future complexity will go. Premature abstraction is a defect.

## Article III — Behavior is sacred
Refactor, optimization, and audit work preserves observable behavior. Same inputs produce the
same outputs. Any change to behavior is a spec change and must be surfaced as a separate decision,
never smuggled in under "cleanup."

## Article IV — Evidence over opinion
Every finding, root cause, and risk cites concrete evidence (`file:line`, a measurement, a failing
test). "It feels slow" is not a bottleneck; a profile is. Debugging traces to a root cause — it
does not guess.

## Article V — Test-first, always
Acceptance criteria in the spec are testable (Given/When/Then). Each user story is independently
testable and ships with tests before the implementation is considered complete. Every new module,
data provider, executor, or domain model must have at least a unit test covering its public API.
Bug fixes ship with a regression test that would have caught the bug. Critical paths (auth,
payments, data integrity, forex pips/lots/margin) are covered before they are optimized. No code
enters the main branch without a passing test suite.

## Article VI — Security and operability are requirements, not phases
Untrusted input is validated at the boundary; secrets never live in code or images; auth and
access control are designed in, not bolted on. Anything shipped is observable (logs, metrics,
alerts) and reversible (a documented rollback). These are acceptance gates, not nice-to-haves.

## Article VII — Stay in-session, no external LLM
The team's reasoning runs inside the host model (Claude Code or Copilot). Orchestration is prompt
structure and host-native subagents — not an external LLM service, API key, or orchestration
server. Specialist roles are personas the host adopts, not microservices.

## Article VIII — Simplicity and reversibility
Prefer the boring, proven solution a junior can maintain. Optimize for five-year total cost of
ownership. Distinguish reversible decisions (decide fast) from one-way doors (slow down, get them
right). Justify every added dependency and every added layer by the concrete risk it removes.

## Article IX — Navigate via graph, not raw files
Before reading source files, browsing directories, or searching the codebase, query the
graphify knowledge graph (`graphify-out/`) for architecture context, file relationships,
and relevant code locations. Reading the graph costs a fraction of the tokens that scanning
raw source files does. Only read a file directly after the graph has pointed you to the
exact line numbers needed. This applies to all agents, personas, and skills operating in
this repository.

---

### Amendment procedure
Amend via `/agent-constitution`. Bump the version per semantic rules: **MAJOR** for removing or
redefining an article, **MINOR** for adding an article or materially expanding guidance, **PATCH**
for clarifications. Record the date and propagate changes to the templates that reference these
articles.
