---
phase: 03-interactive-simulation-shell-mvp
plan: 04
subsystem: ui
tags: [react, components, splash, error, scenario-grid, scenario-card, a11y]

# Dependency graph
requires:
  - phase: 03-01
    provides: Vite + React + TypeScript build system, Tailwind @theme tokens
  - phase: 03-02
    provides: ScenarioDefinition type
provides:
  - SplashScreen: branded loading screen with phase-based progress (D-27)
  - ErrorScreen: full-screen fetch error with retry button (D-30)
  - ScenarioGrid: responsive card grid for scenario selection (D-01, D-07)
  - ScenarioCard: interactive selection card with keyboard a11y (D-28, UI-06)

affects: [03-07]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pure presentation components: no hooks, no side effects, props-in JSX-out"
    - "<button> element for interactive cards (native keyboard, Screen Reader)"
    - "Tailwind arbitrary value for touch target: min-h-[44px]"
    - "ARIA attributes: role='progressbar', aria-pressed, aria-label on all containers"

key-files:
  created:
    - webapp/src/components/SplashScreen.tsx
    - webapp/src/components/ErrorScreen.tsx
    - webapp/src/components/ScenarioGrid.tsx
    - webapp/src/components/ScenarioCard.tsx
  modified: []

key-decisions:
  - "SplashScreen is pure presentation — orchestration delegated to useSimulation hook (Plan 03-07)"
  - "ScenarioCard uses <button> not <div> — native a11y without custom keyboard handlers"

patterns-established:
  - "Pattern: Tailwind @theme tokens (bg-primary, text-secondary) as the ONLY color source"
  - "Pattern: French copy exact as per UI-SPEC copywriting contract"

requirements-completed: [UI-01, UI-07]

# Metrics
duration: 15min
completed: 2026-05-13
---

# Phase 03-04: Onboarding and Scenario Selection Summary

**4 React components: branded SplashScreen with progress bar, ErrorScreen with retry, responsive ScenarioGrid (1→2→3 cols), and keyboard-accessible ScenarioCard with selection ring — all using Tailwind @theme tokens, French copy, ARIA attributes**

## Performance

- **Duration:** 15 min
- **Started:** 2026-05-13T21:26:00Z
- **Completed:** 2026-05-13T21:41:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- SplashScreen: progress bar with `role="progressbar"`, phase text, Display typography for "Budget Citoyen"
- ErrorScreen: error message + "Réessayer" button with focus outline (accent reserved-for list #7)
- ScenarioGrid: responsive grid 1→2→3 columns, semantic `<section aria-label>`, empty state handling
- ScenarioCard: `<button>` element with `aria-pressed`, hover scale(1.02), selected ring-2, touch target ≥44px

## Task Commits

1. **Task 1: SplashScreen + ErrorScreen** — `99508fd` (feat: 2 onboarding components)
2. **Task 2: ScenarioGrid + ScenarioCard** — `751e2ee` (feat: 2 scenario selection components)

## Files Created/Modified

- `webapp/src/components/SplashScreen.tsx` — Branded loading with progress bar (D-27)
- `webapp/src/components/ErrorScreen.tsx` — Full-screen error with retry (D-30)
- `webapp/src/components/ScenarioGrid.tsx` — Responsive card grid (D-01, D-07)
- `webapp/src/components/ScenarioCard.tsx` — Interactive selection card (D-28, UI-06)

## Decisions Made

None — followed plan exactly as specified.

## Deviations from Plan

None — plan executed exactly as written. All French copy matches UI-SPEC contract verbatim.

## Issues Encountered

None.

## Next Phase Readiness

- All 4 components ready for Plan 03-07 integration shell (useSimulation state machine routing)
- ScenarioGrid and ScenarioCard consume `ScenarioDefinition` from engine/types.ts (Plan 02-10)
- SplashScreen's `progress` prop matches useSimulation hook contract defined in RESEARCH.md

---
*Phase: 03-interactive-simulation-shell-mvp*
*Completed: 2026-05-13*
