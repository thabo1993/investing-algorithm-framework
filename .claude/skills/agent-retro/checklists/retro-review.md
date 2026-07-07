# Retro Review Checklist

Validates a retrospective before its lessons are trusted by future runs. A bad lesson is worse
than no lesson — it silently misguides every subsequent run.

## Evidence & Validity

- [ ] Every lesson cites a concrete moment from the run (a correction, a redo, a stated assumption)
- [ ] No lesson is speculative or "nice to remember" without evidence
- [ ] User corrections are captured faithfully (not the agent's rationalization of them)
- [ ] An empty result is allowed — no filler lessons were invented to seem productive

## Classification

- [ ] Each lesson is tiered: project-local vs. universal
- [ ] Project-local lessons are genuinely repo-specific (not dressed-up universal truths)
- [ ] Universal lessons genuinely generalize (would help the agent in any project)
- [ ] When in doubt, the lesson was filed as project-local (the reversible default)

## Destination & Format

- [ ] Project-local lessons written to `.claude/learnings/<agent>.md` (correct agent name)
- [ ] Entries follow the learning-entry template (signal, evidence, lesson, scope)
- [ ] New entries appended — no existing learnings were overwritten or lost
- [ ] Duplicate/overlapping lessons were merged, not stacked
- [ ] Universal lessons written to `IMPROVEMENTS.md` as a reviewable proposed edit (file + change)

## Guardrail Safety

- [ ] No lesson weakens a read-only, no-deploy, or security guardrail
- [ ] No agent `.md` definition was edited directly (universal changes stay human-gated)
- [ ] Lessons adjust *how* an agent works, never *whether* it honors its constraints

## Hygiene

- [ ] If a learnings file exceeded ~20 entries, it was distilled/pruned
- [ ] Stale or superseded lessons were removed or updated
- [ ] The file still reads as focused guidance, not an unbounded log

## Scoring

| Score | Rating | Action |
|-------|--------|--------|
| 100% | Trusted | Lessons are safe for future runs to load |
| 75-99% | Tidy Up | Fix classification or format, then trust |
| 50-74% | Re-review | Evidence or guardrail concerns — revisit lessons |
| Below 50% | Discard | Lessons are speculative or unsafe — do not persist |
