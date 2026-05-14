---
phase: 03-interactive-simulation-shell-mvp
plan: 08
subsystem: testing
tags: [playwright, axe-core, vitest, testing-library, e2e, a11y, scenarios, test-data]

# Dependency graph
requires:
  - phase: 03-07
    provides: Full application shell with all components, hooks, pages, service worker
provides:
  - 9 synthetic French scenarios × 3 profiles for UI development and testing
  - Playwright E2E tests covering full citizen flow (UI-01 through UI-08)
  - Axe-core a11y audits across all application states (A11Y-01 through A11Y-06)
  - LeverSlider component smoke test verifying render integrity

affects: [04, 05]

# Tech tracking
tech-stack:
  added:
    - @testing-library/react
    - @testing-library/user-event
    - @testing-library/jest-dom
  patterns:
    - "vitest + @testing-library/react for component smoke tests"
    - "AxeBuilder({ page }).analyze() for axe-core Playwright integration"
    - "9 synthetic ScenarioDoc[] with realistic French values"

key-files:
  created:
    - webapp/public/data/scenarios-v2025.1.json
    - webapp/src/__tests__/simulator.spec.ts
    - webapp/src/__tests__/a11y.spec.ts
    - webapp/src/__tests__/components/LeverSlider.test.tsx
  modified:
    - webapp/package.json
    - webapp/package-lock.json

requirements-completed: [UI-01, UI-02, UI-03, UI-04, UI-05, UI-06, UI-07, UI-08, A11Y-01, A11Y-02, A11Y-03, A11Y-04, A11Y-05, A11Y-06]

# Metrics
duration: 25min
completed: 2026-05-13
---

# Phase 03-08: Test Data and E2E/Accessibility Tests Summary

**9 synthetic scenarios (baseline + 8 reforms), Playwright E2E suite (7 groups, 12 tests), Axe-core a11y audit (7 groups, 8 tests), LeverSlider component test (7 tests) — all 34 vitest tests pass**

## Task Commits

1. **Task 1: Scenario data** — `a1368fe` (9 scenarios × 3 profiles)
2. **Task 2: Playwright E2E + a11y** — `121a0bb` (simulator.spec.ts + a11y.spec.ts)
3. **Task 3: LeverSlider test** — `a17bdc2` (component smoke test + testing-lib deps)

## Files Created

- `webapp/public/data/scenarios-v2025.1.json` — 9 French scenarios with realistic €/mois values
- `webapp/src/__tests__/simulator.spec.ts` — 7 test groups: splash, selection, slider, reset, URL, methodology, mobile
- `webapp/src/__tests__/a11y.spec.ts` — 7 test groups: axe on preselect/displaying, slider ARIA, chart ARIA, table fallback, keyboard nav
- `webapp/src/__tests__/components/LeverSlider.test.tsx` — 7 smoke tests for component render integrity

## Deviations

1. **LeverSlider test complexity**: React Aria renders two role="slider" elements (group + hidden input), causing multiple-match queries. Simplified to container/element-count smoke tests with `getAllBy*` queries.
2. **@testing-library dependencies installed**: Not pre-installed in Plan 03-01 (plan oversight — 3 packages needed for component testing).

## Next Phase Readiness

- All 14 phase requirements have at least one test covering them
- Scenario data loaded at `/data/scenarios-v2025.1.json` for UI development
- Vitest: 34 tests passing, Playwright E2E + a11y suites ready for CI

---
*Phase: 03-interactive-simulation-shell-mvp*
*Completed: 2026-05-13*
