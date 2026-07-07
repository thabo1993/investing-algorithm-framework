---
name: agent-retro
description: Run a retrospective after an agent or pipeline finishes — capture what the user corrected, what was redone, and what worked — then write structured lessons that future runs read back. The feedback loop that makes the library self-improving without any external service.
---

# /agent-retro — reflect and improve after a run

The closing half of the self-improvement loop. After any agent or `agent-dev-team-*` pipeline
finishes, this skill mines the just-completed work for lessons and writes them where the **next**
run will pick them up. No model is retrained — the *prompt artifacts* and the *project's learned
context* improve. Everything stays in-session (Constitution Article VII).

## What counts as a lesson

In priority order — the higher the signal, the more it matters:

1. **User corrections** — the strongest signal. The user changed, rejected, or redirected what an
   agent produced. *Why* did the first attempt miss?
2. **Redos** — the agent had to backtrack or fix its own output. What would have avoided it?
3. **False assumptions** — something the agent assumed turned out wrong (a path, a convention, a
   constraint).
4. **Reinforcers** — something that worked notably well and should become the default.

A "lesson" is only valid if it is **evidence-based** — tie it to a concrete moment in the run.
Do not invent lessons from vibes; an empty retro is a valid outcome.

## Steps

1. **Identify the subject.** Which agent(s) or pipeline ran? Each lesson is filed under the agent
   it applies to (e.g., `debug-investigator`), or `pipeline` for orchestration-level lessons.
2. **Mine the run** for the four signal types above. Quote the evidence (what the user said, what
   was redone).
3. **Classify each lesson** into one of two tiers — this is what makes the loop portable:

   | Tier | Test | Destination |
   |---|---|---|
   | **Project-local** | "True only in *this* repo" (this codebase uses Keycloak; tests live in `/spec`) | `.claude/learnings/<agent>.md` (Claude Code) and `.github/learnings/<agent>.md` (GitHub Copilot) |
   | **Universal** | "Would improve this agent *everywhere*" (always read logs before hypothesizing) | `IMPROVEMENTS.md` at repo root |

   When unsure, default to **project-local** — it is reversible and contained. Promote to universal
   only when the lesson clearly generalizes beyond this project.

4. **Write project-local lessons** to both `.claude/learnings/<agent>.md` (Claude Code) **and**
   `.github/learnings/<agent>.md` (GitHub Copilot) using the entry format in
   `templates/learning-entry.md`. Create each file/dir if absent; **append**, don't overwrite. If an
   existing entry covers the same ground, refine it instead of duplicating. Keep both files in sync —
   they should always contain the same lessons.
5. **Write universal lessons** to `IMPROVEMENTS.md` as a proposed edit to the agent's definition —
   quote the target file and the suggested change, so a human can review and PR it upstream. Never
   edit an agent's `.md` definition directly; universal changes are **human-gated**.
6. **Prune if bloated.** If a `.claude/learnings/<agent>.md` file grows past ~20 entries or starts
   repeating itself, distill it: merge related lessons, drop stale ones. (Skillsmith's `distill`
   task can help.) A learnings file that dilutes the prompt is worse than none.

## Output
- A short summary: N project-local lessons written, M universal improvements proposed, which files.
- If nothing rose to the bar of an evidence-backed lesson, say so plainly — no filler.

## Guardrails
- **Evidence or nothing.** Every lesson cites a concrete moment from the run. No speculation.
- **Lessons refine, never override.** A learning adjusts *how* an agent works; it can never relax a
  read-only, no-deploy, or security guardrail. If a "lesson" would weaken a guardrail, discard it.
- **Universal changes are human-gated.** Propose them in `IMPROVEMENTS.md`; do not modify
  `agents/*.md` or `skills/*/SKILL.md` definitions yourself.
- **Project-local stays local.** `.claude/learnings/` and `.github/learnings/` are *never*
  overwritten when agents are updated via `git pull` — that separation is what lets a consuming
  project keep its learned context across upgrades. Both paths exist so lessons are picked up
  whether the project uses Claude Code or GitHub Copilot (or both).
- **No external service.** All reflection happens in this session. No telemetry, no API calls.
