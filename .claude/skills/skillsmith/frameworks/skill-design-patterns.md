# Skill Design Patterns

Common patterns for building well-structured Claude Code skills. Reference these when
running `/skillsmith discover` or reviewing an existing skill's architecture.

---

## Pattern 1 — Single-Phase Command Skill

**Use when:** The skill does one well-defined job triggered by one command.
**Examples:** `/agent-specify`, `/agent-clarify`, `/agent-plan`

```
SKILL.md          ← entry point: persona + routing + greeting
tasks/
  run.md          ← the one task that does the work
checklists/
  output-review.md ← quality gate for the artifact this skill produces
```

**Routing:** All content loaded on command invocation. Nothing loaded at startup.
**Checklist structure:** Completeness | Clarity | No Leakage | Traceability | Compliance | Readiness Gate | Scoring

---

## Pattern 2 — Multi-Command Suite

**Use when:** The skill has several related sub-commands with different behaviors.
**Examples:** Skillsmith (`discover` / `scaffold` / `distill` / `audit`)

```
SKILL.md          ← entry point: lists commands in <commands> table + routing table
tasks/
  discover.md     ← loaded on /skillsmith discover
  scaffold.md     ← loaded on /skillsmith scaffold
  distill.md      ← loaded on /skillsmith distill
  audit.md        ← loaded on /skillsmith audit
specs/
  *.md            ← reference specs loaded on demand
frameworks/
  *.md            ← reusable content loaded on demand
```

**Routing:** `SKILL.md` is always-load; tasks are on-command; specs/frameworks are on-demand.
**Key rule:** Each task file is self-contained — it shouldn't assume the other tasks are loaded.

---

## Pattern 3 — Orchestrator Skill

**Use when:** The skill coordinates multiple agents through a pipeline.
**Examples:** `/agent-dev-team-fast`, `/agent-dev-team-pro`

```
SKILL.md          ← entry point: pipeline definition + role sequence
```

No sub-tasks needed — the pipeline IS the skill. The SKILL.md defines:
1. The role sequence (who does what, in what order)
2. The artifact contract between roles (what passes from step N to step N+1)
3. The gate conditions (when to stop vs. proceed)

**Key rule:** Orchestrators spawn subagents via the Agent tool. They don't do the work themselves.

---

## Pattern 4 — Stateful Skill with Memory

**Use when:** The skill produces a persistent artifact that gates future work.
**Examples:** `/agent-constitution` (produces `constitution.md`, gates all plans)

```
SKILL.md
tasks/
  create.md       ← creates the artifact
  amend.md        ← updates existing artifact
checklists/
  output-review.md
context/
  existing.md     ← loaded when artifact already exists, to preserve current content
```

**Key rule:** Always check if the artifact exists before overwriting. Load context files
that show existing state when the artifact is being amended, not created fresh.

---

## Checklist Design Guidelines

Every skill that produces an artifact should have a checklist. Standard structure:

| Section | Purpose |
| --- | --- |
| **Completeness** | Are all required fields/sections present? |
| **Clarity** | Is everything unambiguous and testable? |
| **No Leakage** | Are phase boundaries respected (no tech in spec, etc.)? |
| **Traceability** | Can artifacts be traced back to user intent/prior phase? |
| **Compliance** | Does this honor the constitution and prior phase decisions? |
| **Readiness Gate** | Pass/fail criteria for proceeding to next phase |
| **Scoring** | 100% / 75-99% / 50-74% / <50% → action table |

---

## Frontmatter Conventions

```yaml
---
name: skill-name            # kebab-case, matches directory name
type: skill                 # always "skill" for skills
version: 0.1.0              # semver; bump minor for new commands, patch for fixes
category: development       # development | design | security | infrastructure | meta
description: >-
  One sentence what it does. Triggers: "keyword1", "keyword2".
allowed-tools: [Read, Write, Edit, Glob, Grep]   # exact tools needed, not more
model: opus                 # opus | sonnet | haiku
---
```

**model guidance:**
- `opus` — complex reasoning, multi-step analysis, architecture decisions
- `sonnet` — structured writing, code generation from a clear spec, Q&A
- `haiku` — simple lookups, single-step transforms, fast formatting

---

## Placeholder Syntax

| Syntax | Meaning | Example |
| --- | --- | --- |
| `[square brackets]` | Prose placeholder — replace with written content | `[describe the persona's role]` |
| `{curly braces}` | Variable placeholder — replace with a value | `{feature-name}`, `{###}` |
| `<xml-tags>` | Structural sections in SKILL.md | `<activation>`, `<persona>`, `<routing>` |
| `@path/to/file.md` | Reference to another file loaded at routing time | `@tasks/run.md` |

---

## Anti-Patterns to Avoid

- **God skill**: one SKILL.md file that tries to do everything. Split into tasks.
- **Hardcoded persona in task**: the task file re-defines the persona instead of inheriting from SKILL.md.
- **Missing checklists**: a skill that produces an artifact with no quality gate.
- **Over-eager always-load**: loading large context files at startup even when they're rarely needed.
- **Leaking state between commands**: a task file assumes a previous task's output is in context.
