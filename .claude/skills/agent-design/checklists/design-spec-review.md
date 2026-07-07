# Design Spec Review Checklist

Validates a complete design spec (information architecture, wireframes, design system, component map) before implementation begins.

## Information Architecture

- [ ] Site map / app structure is clearly documented
- [ ] User flows are mapped for each high-priority user story
- [ ] Information hierarchy is logical (primary → secondary → tertiary)
- [ ] Navigation model is consistent across all screens/pages
- [ ] Entry points and exit paths are clearly marked

## Wireframes & Layouts

- [ ] Wireframes exist for all primary user journeys (P1 stories minimum)
- [ ] Each wireframe includes annotations for interactive elements
- [ ] Responsive design approach is specified (mobile-first or desktop-first)
- [ ] Loading, empty, and error states are wireframed for data-driven screens
- [ ] Accessibility concerns are addressed (keyboard nav, screen reader hints)

## Design System / MASTER.md

- [ ] Color palette is defined with semantic naming (primary, success, alert, etc.)
- [ ] Typography system includes font families, sizes, weights, and line heights
- [ ] Spacing scale (padding, margin, gaps) is defined and named
- [ ] Component library is documented with states (default, hover, active, disabled)
- [ ] Tokens are exportable for implementation (CSS variables, design tokens format)

## Component Map

- [ ] All components used in wireframes are listed
- [ ] Each component includes its states: default, hover, active, disabled, loading, error
- [ ] Props and variations are clearly documented
- [ ] Interaction patterns (click, focus, hover) are specified
- [ ] Component nesting/composition rules are explicit

## Consistency & Alignment with Spec

- [ ] Design solves the user stories defined in spec.md
- [ ] Visual system supports the success criteria (measurable outcomes)
- [ ] No new scope has crept into the design (stays within spec bounds)
- [ ] Design language is appropriate for the product category
- [ ] Accessibility is built-in, not bolted-on (WCAG 2.1 AA at minimum)

## Constitution Compliance

- [ ] Design honors accessibility standards from the constitution (e.g., WCAG level)
- [ ] Chosen design patterns are compatible with the approved technology stack
- [ ] No design decision forces a framework or library not permitted by the constitution
- [ ] Performance approach (animations, real-time, asset size) meets any constitution SLAs

## Readiness Gate

- [ ] Frontend engineer can build from these wireframes without requesting clarification
- [ ] All design system tokens are defined (engineer won't invent values)
- [ ] Component interactions are specified (no ambiguity about behavior)
- [ ] Responsive breakpoints are defined
- [ ] Design-to-code handoff includes all necessary artifacts

## Scoring

| Score | Rating | Action |
|-------|--------|--------|
| 100% | Ready for Build | Proceed to frontend engineer |
| 75-99% | Polish & Ship | Address gaps, document missing detail |
| 50-74% | Rework Needed | Significant gaps — revisit architecture |
| Below 50% | Restart | Fundamental issues — redesign |
