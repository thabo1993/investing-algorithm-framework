# Learning Entry Template

Each lesson written to `.claude/learnings/<agent>.md` follows this format. Keep entries short,
evidence-backed, and actionable. Newest entries go at the top.

---

## [YYYY-MM-DD] [one-line title of the lesson]

**Signal:** correction | redo | false-assumption | reinforcer
**Evidence:** [what actually happened — quote the user's correction or describe the redo]
**Lesson:** [what to do differently next time, stated as a directive the agent can act on]
**Scope:** [optional — files, modules, or situations this applies to in this project]

---

### Example — project-local entry

## 2026-06-22 Auth uses Keycloak, not the built-in session model

**Signal:** correction
**Evidence:** Agent proposed a custom JWT session table; user replied "we use Keycloak for all auth,
never roll our own."
**Lesson:** In this repo, treat authentication and session management as owned by Keycloak. Integrate
against it; do not design custom auth tables or token logic.
**Scope:** any task touching `src/auth/`, login flows, or user identity.

---

### Example — reinforcer entry

## 2026-06-22 Reading the failing test first cut debugging time

**Signal:** reinforcer
**Evidence:** Starting from the assertion in the failing test located the root cause in one pass.
**Lesson:** Begin investigations from the failing test's assertion and walk outward, before reading
the implementation top-down.
**Scope:** all debugging tasks in this repo.
