---
mode: agent
description: SDD Phase 1.75 — produce a complete design spec (IA, wireframes, design system, component map) before the technical plan.
---

Act as the `ux-designer`. Produce an implementation-ready design spec for the feature described in
`specs/<###-feature-name>/spec.md`. Work through all 6 steps:

**Step 0 — Industry reasoning.** Classify the product (Financial Dashboard / Fintech / SaaS / other)
and apply the matching style, color, typography, effects, and anti-pattern rules. For trading:
Dark Mode (OLED) + Data-Dense is mandatory; light mode default is an anti-pattern.

**Step 1 — Information architecture.** Content hierarchy (Critical/Important/Contextual/On-demand),
navigation map, layout grid (1440/768/375px breakpoints).

**Step 2 — User flows.** One flow per user story from spec.md. Mark loading / empty / error /
success at every async boundary.

**Step 3 — Wireframes.** Text/ASCII wireframe for every key screen. Use actual labels and content —
never vague placeholder boxes. Engineers build directly from these.

**Step 4 — Chart type selection.** For each visualization, state the data shape, the chosen chart
type and why it fits, when NOT to use it, and the recommended library.
Key chart rules: OHLC data → Candlestick (TradingView Lightweight Charts); Signal KPI →
Bullet Chart grid; Sentiment → Gauge dial (never pie); Real-time → Streaming Area with Pause/Resume;
Comparison → Horizontal Bar; Heat map → D3.js/Plotly (never pie for part-to-whole with > 5 slices).

**Step 5 — Design system.** Write `design-system/MASTER.md` (tokens, colors, type, animation, icons)
and `specs/<feature>/design.md` (the feature-specific spec). Color: semantic tokens not raw hex.
Icons: SVG only (Heroicons/Lucide). No emoji as icons.

**Step 6 — Component map.** Name, states (loading/empty/error/default/active/disabled), props
sketch, interaction spec (hover/click/keyboard/touch), a11y notes (ARIA, keyboard nav, WCAG level).

**Pre-Delivery Checklist.** Confirm before handoff: contrast ≥ 4.5:1 · visible focus rings ·
cursor-pointer on clickable · hover 150–300ms · touch targets ≥ 44×44px · streaming charts have
pause/resume · data freshness timestamps · colorblind fallbacks for all charts · no color-only
signal differentiation. Pass or fix — do not hand off with failures.

Next: `/agent-plan` reads `design.md` + `design-system/MASTER.md` alongside `spec.md`.
Full spec: ../../agents/ux-designer.md · phase skill: ../../skills/agent-design/SKILL.md
