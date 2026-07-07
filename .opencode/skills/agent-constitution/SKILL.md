---
name: agent-constitution
description: Create or amend the project's governing principles in .specify/memory/constitution.md. Use when starting a project, setting engineering standards, or changing the rules that every plan is checked against.
---

# /agent-constitution — establish governing principles

Phase 0 of Spec-Driven Development. The constitution is the rule set every `/agent-plan` is
gated against. Drive this with the **`tech-lead`** persona — it's a long-term, judgment call.

## Steps
1. **Read the current constitution** at `.specify/memory/constitution.md` if it exists. If not,
   start from the repo's default (this repo ships one — treat it as the baseline).
2. **Adopt the `tech-lead` persona** (spawn it via the Task tool, or reason as it) to draft or
   amend articles. Each article must be: concrete, testable against a plan, and justified by a real
   risk it removes — no vague platitudes.
3. **Resolve placeholders.** No `[BRACKETED]` text may remain. Every principle states what it
   forbids/requires and why.
4. **Version it.** Bump per semantic rules — MAJOR: remove/redefine an article; MINOR: add an
   article or materially expand; PATCH: clarify wording. Update the ratified/amended dates.
5. **Propagate.** If an amendment changes what plans must satisfy, update the Constitution Check
   table in `.specify/templates/plan-template.md` to match.

## Output
- The written `constitution.md` (or the amended version).
- A short **amendment summary**: version bump, what changed, and which templates/skills it affects.

## Guardrails
- The constitution governs *how* the team works; it is not a spec for *what* to build.
- Keep it short and enforceable. A principle nobody checks is decoration — every article must be
  something a plan can be measured against.
- Next step: `/agent-specify` to define a feature.
- **Article VI (Security and operability) is a protected article.** It may be expanded or
  strengthened but must never be removed, renamed, substantially weakened, or re-framed as an
  optional gate. An amendment that would allow security requirements to be deferred or bypassed
  is a gate-fail — reject it and flag it to the user. If the user insists, surface it as an
  explicit conscious decision with documented risk, not a silent constitution change.
