---
phase: 03-interactive-simulation-shell-mvp
plan: 07
subsystem: ui
tags: [react, hooks, router, service-worker, workbox, state-machine, integration]

# Dependency graph
requires:
  - phase: 03-04
    provides: SplashScreen, ErrorScreen, ScenarioGrid, ScenarioCard
  - phase: 03-05
    provides: LeverSlider, SliderGroup, AdvancedToggle, Footer
  - phase: 03-06
    provides: ImpactDisplay, ImpactPill, ChartGrid, ChartCell, ChartTableFallback
provides:
  - useSimulation: central state machine hook with WorkerOrchestrator coordination
  - useSliderWithUrl: slider-to-URL sync hook (D-23)
  - useServiceWorker: SW registration lifecycle hook (D-31)
  - App.tsx: React Router + state-machine routing
  - SimulatorPage: 380px split-panel layout (D-22), mobile accordion (D-24)
  - MethodologyPage: static methodology page (D-25)
  - sw.js: Workbox SW (CacheFirst/NetworkFirst/StaleWhileRevalidate)
  - workbox-config.js: precache manifest config

affects: [03-08]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "State machine: 'loading' | 'preselect' | 'displaying' | 'error'"
    - "WorkerOrchestrator + interpolation on main thread (OQ3 MVP decision)"
    - "startTransition for macro projection to avoid blocking UI (Pitfall 3)"
    - "Workbox importScripts CDN pattern for SW context"

key-files:
  created:
    - webapp/src/hooks/useSimulation.ts
    - webapp/src/hooks/useSliderWithUrl.ts
    - webapp/src/hooks/useServiceWorker.ts
    - webapp/src/pages/SimulatorPage.tsx
    - webapp/src/pages/MethodologyPage.tsx
    - webapp/sw.js
    - webapp/workbox-config.js
  modified:
    - webapp/src/App.tsx
    - webapp/src/workers/orchestrator.ts
    - webapp/tsconfig.json

key-decisions:
  - "Main-thread interpolation for MVP (OQ3) — citizen worker handles initial load but interpolation runs on main thread for <1ms"
  - "PendingEntry uses (value: unknown) => void for resolve — avoids contravariant type errors in strict mode"
  - "useRouterRef for WorkerOrchestrator — instantiated once, never recreated on re-renders"

requirements-completed: [UI-04, UI-05, UI-06, UI-07, UI-08, A11Y-04]

# Metrics
duration: 30min
completed: 2026-05-13
---

# Phase 03-07: Application Shell Integration Summary

**Full integration: 3 custom hooks (useSimulation state machine, useSliderWithUrl sync, useServiceWorker), React Router routing, 380px split-panel SimulatorPage, MethodologyPage, and Workbox Service Worker — all UI components wired to Phase 2 engines**

## Task Commits

1. **Task 1: 3 hooks** — `ecf2c9c` (useSimulation, useSliderWithUrl, useServiceWorker)
2. **Task 2: App.tsx + pages** — `cfd30e3` (state machine, split-panel, methodology, orchestrator fix)
3. **Task 3: SW + Workbox** — `b7ae200` (sw.js, workbox-config.js)

## Auto-fixed Deviations

1. **[Rule 3] orchestrator.ts PendingEntry contravariant type** — Changed `resolve: (value: T) => void` to `(value: unknown) => void` with cast assertions in call sites
2. **[Rule 3] SliderState not assignable to Record<string, number>** — Added useMemo conversion in SimulatorPage

## Next Phase Readiness

- Full application shell ready for Plan 03-08 test data + E2E/accessibility tests
- All components wired end-to-end: Splash→Preselect→Scenario→Slider→Impact→Chart→Reset→Share

---
*Phase: 03-interactive-simulation-shell-mvp*
*Completed: 2026-05-13*
