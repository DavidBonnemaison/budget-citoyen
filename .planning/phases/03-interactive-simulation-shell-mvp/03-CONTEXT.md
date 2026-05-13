# Phase 3: Interactive Simulation Shell (MVP) - Context

**Gathered:** 2026-05-13
**Status:** Ready for planning

## Phase Boundary

This phase delivers the first user-facing UI: the Citizen Explorer shell — a responsive, accessible web application where citizens select fiscal reform scenarios, manipulate simplified fiscal levers, and see real-time household impact and 5-year macro trajectory projections. It bootstraps the React/Vite/Tailwind frontend and integrates the existing TypeScript engine + Web Worker infrastructure from Phase 2. All computation remains client-side; no personal data leaves the browser.

## Implementation Decisions

### Simulation UX Model

- **D-01:** Scenario selector + micro interpolation. Citizens select from 9-12 pre-computed candidate scenarios (Baseline 2025 + political programs + variants). Micro results are pre-computed via Python CI (openfisca-france) as O(1) HashMap lookups. The 4-5 simplified citizen levers interpolate between nearby pre-computed scenarios using per-tax interpolation — giving a continuous slider feel without live micro computation.
- **D-02:** Per-tax interpolation. Each tax slider (IR, IS, TVA, cotisations) interpolates independently between the nearest 2-3 pre-computed scenarios. This requires 9-12 scenarios to cover the parameter space adequately across at least 2 tax dimensions.
- **D-03:** 9-12 pre-computed scenarios at launch (Baseline 2025 + 3-5 political programs + tax-only/full-program variants). Scenario pre-compute runs in CI using openfisca-france, exports JSON consumed by the ScenarioCache.
- **D-04:** Simple micro result display — a single number with a small footnote "Basé sur les scénarios les plus proches." No numeric error bounds or confidence labels in citizen mode.
- **D-05:** Macro sliders (tax/spend driving deficit/debt/GDP charts) are scenario-synced. Selecting a scenario auto-positions the macro sliders to match that scenario's fiscal stance. Users can then tweak further.
- **D-06:** Three representative household profiles displayed simultaneously: bas revenu (SMIC ~14K€), médian (~26K€), aisé (~60K€). Each shows impact in €/mois.
- **D-07:** Primary flow: scenario selection first, sliders second. Selecting a scenario shows immediate pre-computed household results. Sliders then let the citizen explore variations via interpolation. New scenario selection resets sliders to that scenario's values.

### Slider Organization

- **D-08:** 4-5 simplified citizen levers: IR ménages, IS entreprises, TVA, Cotisations sociales, Dépenses publiques. Each lever is an aggregate — it controls multiple underlying index-map.ts parameters in fixed proportions.
- **D-09:** Sliders grouped in collapsible sections. Default: first section (IR ménages) expanded, others collapsed. "Mode avancé" toggle expands all sections and exposes individual bracket/parameter sliders.
- **D-10:** Slider axis represents percentage change from baseline (±%). Centered at 0% (baseline 2025). Value label shows both percentage and resulting rate (e.g., "+15% → Taux: 12,6%").
- **D-11:** Abstract levers + advanced toggle. Default citizen view: 5 grouped levers. Advanced toggle reveals individual IR brackets, TVA normal/réduit, CSG/CRDS, cotisations salariales/patronales, dépenses/effectifs.
- **D-12:** Weighted proportional lever mapping. "IR ménages" adjusts all 5 IR bracket rates proportionally. "TVA" blends normal and reduced rates. "Cotisations" blends salariales, patronales, CSG, CRDS. "Dépenses" scales spend level and effectifs together.
- **D-13:** Baseline notch + "Actuel" label at the 0% center position on each slider. Slider thumb snaps gently to the notch.
- **D-14:** Single "Réinitialiser" button resets all sliders to 0% (baseline 2025). Deselects any active scenario. Separate from scenario selection.
- **D-15:** Throttled drag (~50ms / 20 updates/sec) with instant computation on slider release. The WorkerOrchestrator's correlation-ID stale response discarding (Phase 2 D-11) handles rapid-fire requests during drag. Value labels update instantly during drag; charts update on throttle ticks.

### Chart Architecture

- **D-16:** Vega-Lite 6.4 for primary chart rendering. SVG output with declarative JSON specs. The `description` channel maps to `aria-label` on rendered SVG.
- **D-17:** 2x2 responsive grid layout for the 4 macro series: deficit (%PIB), debt (%PIB), GDP growth (%), employment (milliers). Shared x-axis convention (years 1-5). Grid collapses to stacked on narrow mobile.
- **D-18:** Line charts with semi-transparent area fill for trajectory projections. Standard macro forecast display convention (IMF/OECD/Insee style).
- **D-19:** RGAA 4 pattern-fill differentiation via Vega marks with custom SVG `<pattern>` encoding. Each of the 4 series gets a distinct pattern (dots, diagonal lines, crosshatch, vertical lines) plus a color from a deuteranopia-safe palette. Never color alone.
- **D-20:** Hover tooltips showing precise values. Legend hover highlights the selected series and dims others. Touch: tap for tooltip on mobile.
- **D-21:** Out-of-bounds macro results (interpolation returns null): chart area greys out with overlay text "Paramètres hors domaine de validité." The MacroResult.warningMessage is displayed above the chart. Partial validity: show valid years, mark invalid years with hatched zone.

### General UI

- **D-22:** Split panel layout. Desktop: left panel (scenario selector + sliders, fixed width ~380px), right panel (household impact + 2x2 charts, scrollable). Mobile: panels stack vertically, each section becomes a collapsible accordion.
- **D-23:** Base64-encoded single `?state=<base64>` query parameter for URL sharing. Encodes: slider positions, selected scenario ID, profile selection, advanced mode toggle state. Decoded on load to restore full simulation state.
- **D-24:** Mobile adaptation: vertical stack with accordion panels. "Réglages" (scenario + sliders) is an expandable top section. "Résultats" (impact + charts) always visible, scrolls below. Touch targets ≥ 44px (UI-06).
- **D-25:** Dedicated `/methodologie` page linked from a persistent footer. Contains data source attribution (Insee, budget.gouv.fr, Mésange), interpolation methodology explanation, synthetic data disclaimer, and project contact. Required by UI-08.
- **D-26:** Niveau lycée (16-18 ans) reading level for all citizen-facing text. Short sentences, active voice. Economic terms have inline tooltip definitions (e.g., "PIB" → "tout ce que la France produit en un an"). Use of "vous" / "votre" for direct citizen address.

### Loading & Empty States

- **D-27:** Branded splash screen on initial load. Budget Citoyen logo + "Chargement du simulateur..." + progress indicator showing asset fetch progress then worker init status. Auto-transitions to the full UI when both workers report READY (WorkerOrchestrator.init resolves).
- **D-28:** Empty/preselect state: 9-12 scenario cards in a responsive grid with prompt "Choisissez un scénario pour commencer." Chart area shows placeholder "Sélectionnez un scénario pour voir les projections." Household impact shows "—". Sliders are disabled/greyed until a scenario is selected.
- **D-29:** During slider drag computation: affected chart areas get a subtle opacity pulse (CSS transition, ~300ms ease). Slider value labels update instantly (no computation needed). WorkerOrchestrator's stale response discarding silently drops superseded results.
- **D-30:** Fetch failure handling: full-screen error state with message "Impossible de charger les données. Vérifiez votre connexion." and a "Réessayer" button that retries asset fetch + worker init. Service Worker serves cached assets on warm reloads even when network is unavailable.
- **D-31:** Service Worker + Cache API strategy: cache-first for data assets (scenario JSON, shock matrix binary) with stale-while-revalidate. Network-first for app shell (HTML/JS/CSS). Enables <1s warm load by serving cached data immediately while workers init from memory. Cold load target: <3s.

### the agent's Discretion

The following are deferred to the planner and executor agents:
- Exact interpolation algorithm between scenario points (linear, nearest-neighbor, inverse distance weighting)
- Specific lever-to-parameter mapping proportions (e.g., how "IR ménages" distributes across 5 brackets)
- Exact slider range values (±X% for each lever)
- Tailwind CSS theme, color palette, and typography choices
- Vega-Lite spec structure, encoding channels, and axis configuration
- HTML table fallback format and markup for screen readers (A11Y-02)
- Service Worker implementation (Workbox vs manual, precache manifest)
- Exact progress indicator visual design for the splash screen
- React Aria component configuration (useSlider, useButton, etc.)
- Route structure (React Router vs simple conditional rendering)
- axe-core CI pipeline integration (A11Y-06)

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project-level
- `.planning/PROJECT.md` — Core value, constraints, out-of-scope boundaries
- `.planning/REQUIREMENTS.md` — v1 requirements (UI-01 through UI-08, A11Y-01 through A11Y-06)
- `.planning/ROADMAP.md` — Phase 3 goal, success criteria, dependency on Phase 2

### Phase 2 Context & Decisions
- `.planning/phases/02-core-simulation-engines-wasm/02-CONTEXT.md` — Hybrid architecture (D-05 through D-23), privacy boundary, worker model, scenario data format, correlation ID protocol
- `.planning/phases/01-data-foundation-rules-engine/01-CONTEXT.md` — Data artifact formats, versioning scheme (v2025.1), reference year 2025

### Research
- `.planning/research/STACK.md` — Technology stack (React 19, TypeScript 5.8+, Vite 6+, Tailwind CSS 4.3, React Aria, D3.js 7.9, Vega-Lite 6.4, Vitest 3.x, Playwright 1.x)

### Engine & Worker Code (Phase 2 output)
- `webapp/src/engine/types.ts` — All TS types: MacroResult, ScenarioResult, ScenarioDefinition, ShockMatrixData, WorkerRequest/Response, payload types
- `webapp/src/workers/orchestrator.ts` — WorkerOrchestrator class: init, simulate, interpolate, project, terminate
- `webapp/src/workers/citizen-worker.ts` — Citizen Web Worker: INIT/SIMULATE message handlers
- `webapp/src/workers/macro-worker.ts` — Macro Web Worker: INIT/INTERPOLATE/PROJECT message handlers, binary matrix parser
- `webapp/src/workers/index-map.ts` — 14 parameter index constants (PARAM_INDICES)
- `webapp/src/engine/macro-interpolate.ts` — Pure TS multi-linear interpolation, convex hull gating, trajectory projection
- `webapp/src/engine/scenario-cache.ts` — ScenarioCache class: O(1) HashMap lookup, addScenario, fromDocs, loadFromJSON

### Data Artifacts (Phase 1 output)
- `packages/data-pipeline/dist/parameters-v2025.1.json` — Complete tax parameters (60KB JSON)
- `packages/data-pipeline/dist/shockmatrix-v2025.1.parquet` — Pre-computed shock matrix (2.6KB Parquet)
- `packages/data-pipeline/dist/bilingual_test_fixtures.json` — Canonical profile test fixtures

### External References
- Vega-Lite 6.4 documentation — Declarative chart specs, `description` channel for ARIA, `vl2svg`, custom Vega marks for pattern fills
- React 19 documentation — `useTransition` for non-blocking slider updates
- React Aria documentation — `useSlider` hook (aria-valuenow, aria-valuemin, aria-valuemax, keyboard navigation)
- Tailwind CSS 4.3 documentation — CSS-first `@theme` configuration, responsive utilities
- Vite 6+ documentation — WASM-free setup, Service Worker integration, build optimization

## Existing Code Insights

### Reusable Assets
- `WorkerOrchestrator` (orchestrator.ts): Fully tested worker coordinator with correlation IDs and stale response discarding. Phase 3 integrates this directly — no modification needed.
- `ScenarioCache` (scenario-cache.ts): O(1) HashMap lookup for pre-computed results. Used by citizen-worker. Phase 3 extends it with interpolation logic between scenarios.
- `macro-interpolate.ts`: Pure TS trilinear interpolation + hull gating. Consumed by macro-worker. No changes needed — Phase 3 charts consume MacroResult output.
- `engine/types.ts`: Complete type definitions. Phase 3 adds UI-specific types (slider state, URL state, interpolation result) but reuses all engine types as-is.
- `workers/index-map.ts`: Parameter index constants. Used to map slider UI controls to underlying parameter arrays.

### Established Patterns
- Version locking: all artifacts tagged `-v2025.1`. Phase 3 scenario data and UI follow this convention.
- Correlation ID protocol (Phase 2 D-11): every WorkerRequest carries a crypto.randomUUID(). Phase 3 slider drag emits follow this pattern through the existing orchestrator.
- Zero-copy data transfer (Phase 2 D-12): ArrayBuffer transferred via postMessage. Phase 3 splash screen fetch → worker init preserves this.
- Stale response discarding: orchestrator already drops superseded responses. Phase 3 slider throttling leverages this directly.

### Integration Points
- Splash screen → WorkerOrchestrator.init(scenariosJson, matrixBytes) → workers report READY → UI renders
- Scenario selector → ScenarioCache.lookup(scenarioId, profileIndex) → ScenarioResult displayed
- Slider change → interpolation logic (new in Phase 3) → estimated ScenarioResult displayed
- Macro slider change → WorkerOrchestrator.project(tax, spend, 5) → MacroResult → Vega-Lite chart update
- URL state → parse on load → restore slider positions and scenario selection → trigger computation
- Reset button → set all sliders to 0% → deselect scenario → clear results → return to empty state

### Deprecatable Code
- None — all Phase 2 code is preserved. This is additive only.

## Specific Ideas

- The scenario selector should present candidate programs with their real names and a brief summary of fiscal commitments. Cards should show: candidate/program name, brief description, default fiscal position indicators.
- Interpolation between scenarios should use inverse distance weighting in parameter space — closer scenarios get more weight. A minimum of 2 scenarios with interpolation weights summing to 1.0.
- The 3 household profiles should be presented as compact cards/pills side by side, each showing: profile label (e.g., "Foyer modeste"), monthly income, and the +/- € impact.
- Charts should use the same y-axis conventions as Insee/OFCE publications for familiarity: deficit as % of GDP (inverted convention — negative is good), debt as % GDP, GDP growth as % annual change, employment as thousands.
- The methodology page should be a static markdown-rendered page — no interactivity needed besides the attribution links.
- Tooltip definitions for economic terms should use a simple `<abbr>` or info-icon hover pattern, not intrusive popovers.

## Deferred Ideas

None — discussion stayed within Phase 3 scope.

---

*Phase: 3-Interactive Simulation Shell (MVP)*
*Context gathered: 2026-05-13*
