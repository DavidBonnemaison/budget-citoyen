---
phase: 03-interactive-simulation-shell-mvp
plan: 03
subsystem: ui
tags: [vega-lite, svg, patterns, charts, deutranopia-safe, aria, a11y]

# Dependency graph
requires:
  - phase: 03-01
    provides: Vite + React + TypeScript build system, npm scripts, vega-lite dependency
provides:
  - 4 SVG pattern definitions for differentiating macro chart series (A11Y-03)
  - Shared Vega-Lite Config with ARIA, deuteranopia-safe palette, transparent background
  - 4 declarative chart specs (deficit, debt, GDP growth, employment) ready for data injection

affects: [03-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Vega-Lite TopLevelSpec with empty data.values[] as render-time templates"
    - "SVG pattern fills via url(#pattern-*) for colorblind-safe series differentiation"
    - "description channel → aria-label on SVG output (A11Y-01)"
    - "shared Config object for cross-spec consistency (DRY theming)"

key-files:
  created:
    - webapp/src/charts/patterns.ts
    - webapp/src/charts/config.ts
    - webapp/src/charts/spec-deficit.ts
    - webapp/src/charts/spec-debt.ts
    - webapp/src/charts/spec-gdp.ts
    - webapp/src/charts/spec-employment.ts
  modified: []

key-decisions:
  - "Pattern injection via global <svg><defs> element (not patch option) — avoids vega-embed API dependency at spec level"
  - "All 4 specs pre-declare empty data.values[] — ChartCell populates at render time in Plan 03-06"

patterns-established:
  - "Pattern: SVG <pattern> with patternUnits='userSpaceOnUse' for consistent scaling across chart sizes"
  - "Pattern: Shared Config constant imported by all specs — single source of truth for chart theming"

requirements-completed: [UI-03, A11Y-01, A11Y-03]

# Metrics
duration: 18min
completed: 2026-05-13
---

# Phase 03-03: Chart Specification Layer Summary

**Vega-Lite chart spec layer: 4 SVG pattern definitions (A11Y-03 compliant), shared Config with deuteranopia-safe Wong 2011 palette, and 4 declarative TopLevelSpec exports — zero runtime rendering, ready for ChartCell data injection**

## Performance

- **Duration:** 18 min
- **Started:** 2026-05-13T21:06:00Z
- **Completed:** 2026-05-13T21:24:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- 4 SVG `<pattern>` elements with distinct geometric styles: diagonal lines (deficit), dots (debt), crosshatch (GDP), vertical stripes (employment)
- Shared Vega-Lite `Config` exporting deuteranopia-safe Wong 2011 palette `['#0072B2','#E69F00','#009E73','#CC79A7']`
- 4 `TopLevelSpec` chart exports with French `description` fields (auto-mapped to `aria-label`), v6 schema, responsive width, 250px height, empty data arrays
- All chart specs use `fill: 'url(#pattern-*)'` ensuring RGAA 4 A11Y-03 compliance (never color alone)

## Task Commits

1. **Task 1: SVG patterns + shared config** — `c5d4e38` (feat: patterns.ts with 4 `<pattern>` elements, config.ts with ARIA+palette)
2. **Task 2: 4 chart specs** — `86b4e36` (feat: spec-deficit, spec-debt, spec-gdp, spec-employment)

## Files Created/Modified

- `webapp/src/charts/patterns.ts` — `CHART_PATTERNS_SVG` constant with 4 distinct pattern fills
- `webapp/src/charts/config.ts` — `sharedConfig` with ARIA, font, axis, legend, view, and category palette
- `webapp/src/charts/spec-deficit.ts` — `deficitSpec`: deficit trajectory, diagonal lines, #0072B2
- `webapp/src/charts/spec-debt.ts` — `debtSpec`: debt trajectory, dots, #E69F00
- `webapp/src/charts/spec-gdp.ts` — `gdpSpec`: GDP growth trajectory, crosshatch, #009E73
- `webapp/src/charts/spec-employment.ts` — `employmentSpec`: employment trajectory, vertical stripes, #CC79A7

## Decisions Made

- **Pattern injection strategy:** Specs reference `url(#pattern-*)` but do NOT inject patterns themselves. The `CHART_PATTERNS_SVG` string will be rendered into a persistent `<svg><defs>` element by ChartGrid (Plan 03-06) — avoiding vega-embed API coupling at the spec level.
- **Empty data.values:** All specs pre-declare `data: { values: [] }` as render-time placeholders. ChartCell components in Plan 03-06 will populate via vega-embed's `patch` or by constructing new specs with filled data arrays.

## Deviations from Plan

None — plan executed exactly as written. All 6 files follow the RESEARCH.md Pattern 4 template.

## Issues Encountered

None.

## Next Phase Readiness

- All 4 chart specs ready for Plan 03-06 ChartGrid + ChartCell data injection
- Config + patterns ready for ChartCell `role="img"` + `aria-labelledby` integration
- No runtime dependencies beyond vega-lite type imports — zero runtime cost until chart rendering

---
*Phase: 03-interactive-simulation-shell-mvp*
*Completed: 2026-05-13*
