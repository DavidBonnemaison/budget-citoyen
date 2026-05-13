# Phase 3: Interactive Simulation Shell (MVP) - Research

**Researched:** 2026-05-13
**Domain:** React 19 frontend + Web Workers + Vega-Lite 6.4 accessible charts + Service Worker caching
**Confidence:** HIGH

## Summary

Phase 3 delivers the first user-facing UI — a responsive React 19 application that presents testable fiscal scenarios, interactive sliders, real-time household impact, and accessible 5-year macro trajectory charts. All computation runs client-side through the existing Phase 2 WorkerOrchestrator (correlation-ID-based stale response discarding) and ScenarioCache (O(1) pre-computed lookups). New work involves: (1) scaffolding a Vite 6 + React 19 + Tailwind CSS 4.3 project, (2) building the scenario selector + slider UI with React Aria's `useSlider`, (3) implementing a scenario-to-scenario interpolation layer for the continuous slider feel, (4) rendering 4 accessible Vega-Lite 6.4 charts with SVG pattern-fill differentiation, (5) encoding/decoding the full state in a base64 `?state=` query parameter, and (6) a Workbox service worker for <1s warm load.

The Phase 2 engine code requires no modification — all 8 TypeScript files (types, scenario-cache, macro-interpolate, orchestrator, citizen-worker, macro-worker) are consumed as-is. The `index-map.ts` referenced in CONTEXT.md does not exist yet and must be created in this phase to map the 5 citizen levers to underlying parameter groups. The UI-SPEC.md provides detailed design contracts (colors, spacing, typography, copy, layout at both desktop and mobile breakpoints, and a state machine covering LOADING → PRESELECT → SCENARIO_DISPLAYING → DRAG_ACTIVE → COMPUTING → UPDATED plus error states).

**Primary recommendation:** Scaffold the Vite+React+Tailwind project (Wave 0), then build in dependency order: splash/init → scenario selector + ScenarioCache integration → sliders with interpolation layer → chart grid → URL sharing → service worker → methodology page → axe-core CI.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Asset loading & worker init | Browser / Client | — | Main thread fetches scenario JSON + matrix binary; SplashScreen displays progress; WorkerOrchestrator.init() transfers data |
| Scenario selection & display | Browser / Client | Web Worker (citizen) | UI renders scenario cards; selection triggers WorkerOrchestrator.simulate() which uses ScenarioCache O(1) lookup in citizen-worker |
| Slider input & throttling | Browser / Client | — | React Aria useSlider with React 19 useTransition; 50ms throttle; value labels update instantly |
| Micro interpolation (scenario-to-scenario) | Browser / Client | Web Worker (citizen) | New interpolation layer calls ScenarioCache.lookup() for 2-3 nearest scenarios, blends weighted by inverse distance |
| Macro projection (charts) | Browser / Client | Web Worker (macro) | Slider values → WorkerOrchestrator.project(tax, spend, 5) → macro-worker trilinear interpolation |
| Chart rendering (Vega-Lite) | Browser / Client | — | Main thread receives MacroResult, updates Vega-Lite specs, re-renders SVG via vega-embed |
| URL state encoding/decoding | Browser / Client | — | JSON.stringify → base64 encode; decode → JSON.parse → restore state |
| Service Worker caching | Browser / Client (SW thread) | — | Workbox: CacheFirst for data assets, NetworkFirst for app shell |
| Methodology page | CDN / Static | — | Static Markdown-rendered page served as part of the Vite build |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React | 19.2.6 | UI framework | `useTransition` for non-blocking slider updates; mature accessibility ecosystem; `use()` for data fetching |
| React DOM | 19.2.6 | DOM rendering | Required peer of React 19 |
| TypeScript | 5.8+ | Type safety | Static typing across worker message protocol; no runtime cost |
| Vite | 6+ | Build tool | WASM-free setup for Phase 3; native TS/JSX transform; fast HMR |
| Tailwind CSS | 4.3.0 | Styling | CSS-first `@theme` directive; zero-runtime utilities; compose with unstyled React Aria components |
| @tailwindcss/vite | 4.3.0 | Tailwind Vite integration | Vite plugin for Tailwind 4; replaces PostCSS config |
| React Aria Components | 1.17.0 | Accessible UI primitives | `useSlider` provides aria-valuenow/min/max, keyboard nav, touch support — mandatory for RGAA 4 |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| lucide-react | 1.14.0 | Accessible icons | Tree-shakeable SVG icons with `aria-hidden="true"` by default; used for share/reset/expand buttons |
| react-router-dom | 7.15.0 | Client-side routing | `/` for simulator, `/methodologie` for methodology page; conditional rendering would work but React Router provides URL-based navigation |
| Vega-Lite | 6.4.3 | Declarative chart specification | `description` channel → `aria-label` on SVG; JSON specs are auditable; `layer` for pattern-fill composite marks |
| vega-embed | 7.1.0 | Vega-Lite embedding in DOM | Handles spec → SVG rendering lifecycle; tooltip integration; responsive resize |
| Workbox (workbox-webpack-plugin) | 7.4.1 | Service Worker generation | Precache manifest auto-generation; CacheFirst/NetworkFirst strategies; Vite integration via `workbox-build` or `vite-plugin-pwa` |
| axe-core | 4.11.3 | Accessibility testing engine | Used by `@axe-core/playwright` (4.11.3) for CI accessibility assertions |
| @playwright/test | 1.60.0 | E2E + accessibility testing | ARIA assertions; multi-browser; `expect().toHaveNoViolations()` |
| Vitest | 4.1.6 | Unit/integration tests | Vite-native; fast parallel execution; jsdom environment |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Workbox v7 | vite-plugin-pwa | vite-plugin-pwa wraps Workbox but adds Vite-specific abstractions. Workbox directly gives more control over strategies but requires manual precache manifest setup |
| react-router-dom 7 | Conditional rendering (no router) | Simpler for 2 routes; React Router adds ~13KB gzipped but future-proofs for Phase 4 (expert mode) and Phase 5 (API docs) |
| Vega-Lite 6.4 (SVG) | D3.js 7.9 (manual SVG) | D3 gives more ARIA control but requires ~3x more code per chart. Vega-Lite's `description` channel auto-generates `aria-label`. Use Vega-Lite for the 4 standard macro charts; reserve D3 for custom charts in Phase 4 |

**Installation:**
```bash
npm install react@^19.2 react-dom@^19.2
npm install react-aria-components lucide-react react-router-dom@^7
npm install vega-lite@^6.4 vega-embed@^7
npm install workbox-precaching workbox-routing workbox-strategies

npm install -D vite@^6 typescript@^5.8 @vitejs/plugin-react@^6
npm install -D tailwindcss@^4.3 @tailwindcss/vite@^4
npm install -D vitest@^4 @playwright/test@^1 jsdom@^26
npm install -D @axe-core/playwright@^4
npm install -D workbox-build  # for precache manifest generation at build time
```

**Version verification:** All versions confirmed via `npm view` on 2026-05-13.

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          BROWSER (Main Thread)                                   │
│                                                                                  │
│  ┌─────────────────────── INITIALIZATION PHASE ──────────────────────────────┐  │
│  │  index.html → splash.tsx (D-27)                                           │  │
│  │    │                                                                       │  │
│  │    ├─[1]─ fetch("scenarios-v2025.1.json") ──→ scenariosJson               │  │
│  │    ├─[2]─ fetch("shockmatrix-v2025.1.parquet") ──→ matrixBytes (AB)       │  │
│  │    └─[3]─ WorkerOrchestrator.init(scenariosJson, matrixBytes)              │  │
│  │             │                                                               │  │
│  │             ├─ citizen-worker: INIT → parse scenarios → ScenarioCache     │  │
│  │             └─ macro-worker:   INIT → parse binary matrix                 │  │
│  │                                  │                                         │  │
│  │                    both report READY → splash auto-transitions             │  │
│  └──────────────────────────────────┼─────────────────────────────────────────┘  │
│                                     ▼                                             │
│  ┌─────────────────────── PRESELECT STATE (D-28) ────────────────────────────┐  │
│  │  <ScenarioGrid cards={scenarioCache.listScenarios()} />                    │  │
│  │  <Sliders disabled />                                                      │  │
│  │  <ChartPlaceholder />                                                      │  │
│  │  <ImpactDisplay value="—" />                                               │  │
│  └──────────────────────────────────┼─────────────────────────────────────────┘  │
│                                     │ user clicks scenario card                  │
│                                     ▼                                             │
│  ┌─────────────────────── SCENARIO DISPLAYING (D-07) ────────────────────────┐  │
│  │  orchestrator.simulate(scenarioId, profileIndex)                           │  │
│  │    → citizen-worker: ScenarioCache.lookup(id, idx) → ScenarioResult        │  │
│  │                                                                             │  │
│  │  <ScenarioCard selected />          <ImpactDisplay result={...} />          │  │
│  │  <Sliders enabled, positioned />    <Charts initialized />                  │  │
│  └──────────────────────────────────┼─────────────────────────────────────────┘  │
│                                     │ user drags slider                          │
│                                     ▼                                             │
│  ┌─────────────────────── DRAG ACTIVE → COMPUTING → UPDATED ─────────────────┐  │
│  │                                                                             │  │
│  │  ┌──────────────┐    ┌───────────────────┐    ┌────────────────────────┐  │  │
│  │  │ useSlider     │───→│ INTERPOLATION     │───→│ ImpactDisplay          │  │  │
│  │  │ (React Aria)  │    │ LAYER (new)       │    │ (instantly via         │  │  │
│  │  │               │    │                   │    │  interpolated result)  │  │  │
│  │  │ 50ms throttle │    │ scenarioCache      │    └────────────────────────┘  │  │
│  │  │ (D-15)        │    │ .lookup(scenId1,   │                                │  │
│  │  │               │    │  profileIdx)       │    ┌────────────────────────┐  │  │
│  │  │ value label   │    │ + .lookup(scenId2, │    │ ChartGrid              │  │  │
│  │  │ updates        │    │  profileIdx)       │    │                        │  │  │
│  │  │ instantly      │    │ → weighted blend   │    │ orchestrator.project(  │  │  │
│  │  └──────────────┘    │   (inverse distance │    │   tax, spend, 5)       │  │  │
│  │                       │    weighting)       │    │   → MacroResult        │  │  │
│  │                       └───────────────────┘    │   → Vega-Lite spec      │  │  │
│  │                                                │   → vl.render()         │  │  │
│  │  ┌──────────────┐                              └────────────────────────┘  │  │
│  │  │ useTransition│  opacity pulse on charts                                  │  │
│  │  │ startTransi- │  (300ms CSS ease) while                                   │  │
│  │  │ tion()       │  stale responses discarded                                │  │
│  │  └──────────────┘                              ┌────────────────────────┐  │  │
│  │                                                │ URL State (D-23)       │  │  │
│  │  on drag-end:                                  │ base64 JSON encoding:  │  │  │
│  │  aria-valuetext                               │ {s, p, f, a}           │  │  │
│  │  announcement                                 │ → window.location      │  │  │
│  │                                                └────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│  ┌─────────────────────── SERVICE WORKER (separate thread) ───────────────────┐  │
│  │  Cache-First (data): scenarios-v2025.1.json, shockmatrix-v2025.1.parquet   │  │
│  │  Network-First (app): *.html, *.js, *.css, *.svg                           │  │
│  │  Stale-While-Revalidate: methodologie page, favicon, fonts                 │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────────────────────────┤
│                               NETWORK BOUNDARY                                   │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │  STATIC CDN: *.html, *.js, *.css, scenarios-v2025.1.json,                 │  │
│  │              shockmatrix-v2025.1.parquet, favicon.ico                       │  │
│  │  ZERO SERVER-SIDE COMPUTATION: No API calls, no server compute, no DB     │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### Recommended Project Structure
```
webapp/
├── index.html                    # Entry HTML template
├── package.json                  # Dependencies (new)
├── tsconfig.json                 # TypeScript config (new)
├── vite.config.ts                # Vite config (new)
├── sw.js                         # Service Worker entry (new, Workbox)
├── workbox-config.js             # Workbox precache manifest config (new)
├── public/
│   └── favicon.ico               # App favicon
├── src/
│   ├── main.tsx                  # React entry point — mounts <App />
│   ├── App.tsx                   # Top-level: splash gate → simulator or error
│   ├── index.css                 # Tailwind import + @theme customizations
│   │
│   ├── engine/                   # [REUSE] Phase 2 engine (no changes)
│   │   ├── types.ts              # MacroResult, ScenarioResult, WorkerRequest, etc.
│   │   ├── scenario-cache.ts     # ScenarioCache class (O(1) lookups)
│   │   ├── macro-interpolate.ts  # Pure TS trilinear interpolation
│   │   └── __tests__/
│   │       ├── scenario-cache.test.ts
│   │       └── macro-interpolate.test.ts
│   │
│   ├── workers/                  # [REUSE] Phase 2 workers (no changes)
│   │   ├── orchestrator.ts       # WorkerOrchestrator class
│   │   ├── citizen-worker.ts     # Citizen Web Worker
│   │   └── macro-worker.ts       # Macro Web Worker
│   │
│   ├── state/                    # State management (new)
│   │   ├── types.ts             # SliderState, URLState, InterpolationResult
│   │   ├── url-codec.ts         # encode/decode URL state (base64 JSON)
│   │   ├── interpolation.ts     # Scenario-to-scenario inverse distance weighting
│   │   ├── index-map.ts         # Lever → parameter mapping (PARAM_INDICES)
│   │   └── __tests__/
│   │       ├── url-codec.test.ts
│   │       ├── interpolation.test.ts
│   │       └── index-map.test.ts
│   │
│   ├── hooks/                    # Custom React hooks (new)
│   │   ├── useSimulation.ts     # Central hook: orchestrator lifecycle, state
│   │   ├── useSliderWithUrl.ts  # React Aria useSlider + URL sync + throttle
│   │   └── useServiceWorker.ts  # SW registration + update handling
│   │
│   ├── components/               # UI components (new)
│   │   ├── SplashScreen.tsx     # Branded loading screen (D-27)
│   │   ├── ScenarioGrid.tsx     # 9-12 scenario cards in grid (D-01, D-28)
│   │   ├── ScenarioCard.tsx     # Individual scenario card
│   │   ├── LeverSlider.tsx      # Single fiscal lever slider (React Aria useSlider)
│   │   ├── SliderGroup.tsx      # Collapsible slider section (D-09, D-10)
│   │   ├── AdvancedToggle.tsx   # "Mode avancé" toggle (D-11)
│   │   ├── ImpactDisplay.tsx    # 3 household profile cards (D-06)
│   │   ├── ImpactPill.tsx       # Single profile impact pill
│   │   ├── ChartGrid.tsx        # 2×2 Vega-Lite chart container (D-17, D-16)
│   │   ├── ChartCell.tsx        # Single Vega-Lite chart + HTML table fallback
│   │   ├── ChartTableFallback.tsx # <table> with <th scope> for A11Y-02
│   │   ├── Footer.tsx           # Persistent footer with methodology link (D-25)
│   │   └── ErrorScreen.tsx      # Full-screen fetch error (D-30)
│   │
│   ├── charts/                   # Vega-Lite specs (new)
│   │   ├── patterns.ts          # SVG <pattern> definitions (4 patterns)
│   │   ├── spec-deficit.ts      # Deficit %PIB line chart spec
│   │   ├── spec-debt.ts         # Debt %PIB line chart spec
│   │   ├── spec-gdp.ts          # GDP growth % line chart spec
│   │   ├── spec-employment.ts   # Employment in thousands line chart spec
│   │   └── config.ts            # Shared Vega-Lite config (theme, aria, axes)
│   │
│   ├── pages/                    # Route-level components (new)
│   │   ├── SimulatorPage.tsx    # Main simulator layout (split panel)
│   │   └── MethodologyPage.tsx  # Static methodology page (D-25)
│   │
│   └── __tests__/                # Integration/E2E tests (new)
│       ├── simulator.spec.ts    # Playwright E2E: full user flow
│       ├── a11y.spec.ts         # Playwright: axe-core assertions per state
│       └── components/          # Vitest component tests (slider, codec, interpolation)
│           ├── LeverSlider.test.tsx
│           └── url-codec.test.ts
```

### Pattern 1: Slider with useTransition (Non-Blocking Updates)

**What:** React 19 `useTransition` wraps heavy state updates (macro projection requests) so the UI remains responsive during slider dragging. Value labels update synchronously; chart data updates as a transition.

**When to use:** Every slider drag event that triggers a WorkerOrchestrator call.

**Example:**
```typescript
// Source: React 19 official docs (Context7 /reactjs/react.dev)
import { useState, useTransition, useCallback } from 'react';
import { useSlider } from 'react-aria';
import type { SliderState } from 'react-stately';

function LeverSlider({ onChange }: { onChange: (value: number) => void }) {
  const [isPending, startTransition] = useTransition();
  const [displayValue, setDisplayValue] = useState(0);

  // Value label updates synchronously — no computation needed
  const handleDrag = useCallback((newValue: number) => {
    setDisplayValue(newValue); // instant
    startTransition(() => {
      onChange(newValue); // triggers interpolate/project (non-blocking)
    });
  }, [onChange, startTransition]);

  // ... useSlider integration below
}
```

### Pattern 2: useSlider with Full WAI-ARIA (A11Y-05)

**What:** React Aria's `useSlider` provides `aria-valuenow`, `aria-valuemin`, `aria-valuemax`, keyboard navigation (Arrow, Page Up/Down, Home, End), touch support, and debounced ARIA announcements.

**When to use:** Every fiscal lever slider.

**Example:**
```typescript
// Source: React Aria docs (Context7 /websites/react-aria_adobe)
import { useSlider, useSliderThumb } from 'react-aria';
import { useSliderState } from 'react-stately';

function LeverSlider({ label, minValue, maxValue, step, onChange }: SliderProps) {
  const trackRef = useRef<HTMLDivElement>(null);
  const numberFormatter = useMemo(
    () => new Intl.NumberFormat('fr-FR', { style: 'percent', signDisplay: 'always' }),
    []
  );

  const state = useSliderState({
    minValue, maxValue, step,
    value: [0], // single thumb, starts at 0%
    onChange: ([v]) => onChange(v),
    label,
    numberFormatter,
  });

  const { groupProps, trackProps, labelProps, outputProps } = useSlider(
    { label, minValue, maxValue, step, 'aria-label': label },
    state,
    trackRef
  );

  const { thumbProps, inputProps } = useSliderThumb(
    { index: 0, trackRef, inputRef: useRef(null) },
    state
  );

  return (
    <div {...groupProps} className="relative py-4">
      <label {...labelProps}>{label}</label>
      <output {...outputProps}>{state.getThumbValueLabel(0)}</output>
      <div {...trackProps} ref={trackRef} className="h-2 bg-gray-200 rounded" />
      {/* Hidden native input for touch screen readers */}
      <input {...inputProps} />
    </div>
  );
}
```

### Pattern 3: Scenario-to-Scenario Interpolation (Inverse Distance Weighting)

**What:** When a citizen moves the "IR ménages" slider to +15%, the interpolation layer finds the 2-3 nearest scenarios in parameter space, looks up their pre-computed ScenarioResults, and blends them weighted by inverse distance.

**When to use:** Every slider change. Primary flow: scenario selected → sliders tweak → interpolated results.

**Algorithm (Linear Inverse Distance Weighting):**
```typescript
// Source: designed for this phase (D-01, D-02)
// Located in: webapp/src/state/interpolation.ts

interface WeightedScenario {
  scenarioId: string;
  distance: number;   // Euclidean distance in parameter space
  weight: number;     // 1/distance, normalized to sum=1.0
}

function interpolateScenarios(
  sliderParams: Record<string, number>,  // { ir: +15, is: 0, tva: -5, ... }
  scenarioDefs: ScenarioDefinition[],     // from ScenarioCache.listScenarios()
  scenarioCache: ScenarioCache,
  profileIndex: number,
  k: number = 3,                          // nearest-k scenarios
): ScenarioResult {
  // 1. Compute Euclidean distance to each scenario in parameter space
  const distances: WeightedScenario[] = scenarioDefs.map(def => {
    let sumSq = 0;
    for (const [param, target] of Object.entries(sliderParams)) {
      const scenarioVal = def.parameterOverrides[param] ?? 0;
      sumSq += (target - scenarioVal) ** 2;
    }
    return {
      scenarioId: def.id,
      distance: Math.sqrt(sumSq),
      weight: 0, // computed below
    };
  });

  // 2. Sort by distance, take k nearest
  distances.sort((a, b) => a.distance - b.distance);
  const nearest = distances.slice(0, k);

  // 3. If slider matches a scenario exactly (distance ≈ 0), return scenario result directly
  if (nearest[0].distance < 0.001) {
    return scenarioCache.lookup(nearest[0].scenarioId, profileIndex)!;
  }

  // 4. Inverse distance weighting: w_i = (1/d_i) / Σ(1/d_j)
  const invDistSum = nearest.reduce((sum, s) => sum + 1 / s.distance, 0);
  nearest.forEach(s => { s.weight = (1 / s.distance) / invDistSum; });

  // 5. Weighted blend of ScenarioResults
  const blended: ScenarioResult = { ir: 0, is: 0, tva: 0, cotisations: 0, aides: 0, revenuDisponible: 0 };
  for (const weighted of nearest) {
    const result = scenarioCache.lookup(weighted.scenarioId, profileIndex)!;
    blended.ir               += result.ir               * weighted.weight;
    blended.is               += result.is               * weighted.weight;
    blended.tva              += result.tva              * weighted.weight;
    blended.cotisations      += result.cotisations      * weighted.weight;
    blended.aides            += result.aides            * weighted.weight;
    blended.revenuDisponible += result.revenuDisponible * weighted.weight;
  }

  return blended;
}
```

**Confidence:** MEDIUM — algorithm is standard but exact weight distribution across the 5 levers needs tune-testing against real scenario data. `k=3` is recommended by CONTEXT.md; the planner should validate with actual scenario distances.

### Pattern 4: Vega-Lite Accessible Chart with Pattern Fill (A11Y-03)

**What:** Each of the 4 macro series gets a distinct SVG `<pattern>` fill (defined in `<defs>`) AND a distinct deuteranopia-safe color. The `description` channel provides `aria-label`. A sibling `<table>` with `<th scope>` provides screen reader fallback.

**When to use:** All 4 macro trajectory charts.

**Example (Deficit chart spec):**
```typescript
// Source: Vega-Lite docs + project pattern-fill research
// Located in: webapp/src/charts/spec-deficit.ts

const deficitSpec = {
  $schema: 'https://vega.github.io/schema/vega-lite/v6.json',
  description: 'Projection du déficit public sur 5 ans en pourcentage du PIB',
  width: 'container',
  height: 250,
  data: { values: [] }, // populated at render time
  mark: {
    type: 'area',
    fill: 'url(#pattern-deficit)', // SVG pattern reference
    stroke: '#0072B2',
    strokeWidth: 2,
    opacity: 0.7,
  },
  encoding: {
    x: { field: 'year', type: 'ordinal', title: 'Année' },
    y: { field: 'deficit', type: 'quantitative', title: '% du PIB' },
    tooltip: [
      { field: 'year', title: 'Année' },
      { field: 'deficit', title: 'Déficit (%PIB)', format: '.1f' },
    ],
  },
  config: {
    aria: true, // enable auto-generated aria-label
    background: 'transparent',
  },
};
```

### Pattern 5: URL State Encoding (D-23)

**What:** Single `?state=<base64>` query parameter encoding: slider positions, selected scenario, profile index, advanced toggle. Decoded on load → full state restoration.

**When to use:** On every `dragEnd` (update URL) and on initial load (decode URL).

```typescript
// Located in: webapp/src/state/url-codec.ts

interface URLState {
  s: string | null;  // scenarioId
  p: Record<string, number>;  // { ir: +15, is: 0, tva: -5, cotisations: 0, depenses: +3 }
  f: number;         // profileIndex (0,1,2)
  a: boolean;        // advancedMode
}

function encodeState(state: URLState): string {
  const json = JSON.stringify(state);
  return btoa(unescape(encodeURIComponent(json)));
}

function decodeState(encoded: string): URLState | null {
  try {
    const json = decodeURIComponent(escape(atob(encoded)));
    return JSON.parse(json);
  } catch {
    return null;
  }
}

function pushState(state: URLState): void {
  const encoded = encodeState(state);
  const url = new URL(window.location.href);
  url.searchParams.set('state', encoded);
  window.history.replaceState(null, '', url.toString());
}
```

### Anti-Patterns to Avoid

- **Passing slider values directly to interpolateAtPoint:** The macro-worker's `interpolateAtPoint` takes raw grid coordinates (tax, spend, horizon). Slider values go through `index-map.ts` to convert from citizen lever % changes to actual grid parameters.
- **Re-creating Vega-Lite specs on every render:** Vega-Lite specs should be computed via `useMemo` and only re-created when the underlying data changes. Use `vega-embed`'s `view.change()` for data-only updates when possible.
- **Calling orchestrator directly from slider onChange:** Always go through the interpolation layer for micro results, and throttled orchestrator.project() for macro. Never call orchestrator.simulate() during drag — that's for initial scenario selection only.
- **Storing slider values in React state without URL sync:** Slider values must live in a shared state (URL-first) so the "Partager" button always reflects the current simulation. React state is the cache; URL is the source of truth.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Slider accessibility | `<input type="range">` with manual ARIA | React Aria `useSlider` | React Aria handles touch screen readers (hidden native input), keyboard nav, 14 ARIA attributes, and RTL mirroring — hand-rolling would miss edge cases |
| Chart rendering | Manual SVG construction | Vega-Lite 6.4 + vega-embed | Vega-Lite's `description` channel auto-generates `aria-label`; `vl2svg` produces consistent SVG; hand-rolling 4 accessible charts would be ~2000 lines of fragile D3 code |
| Service Worker | Manual `self.addEventListener('fetch', ...)` | Workbox 7.4 | Workbox handles cache versioning, precache manifest generation, strategy composition, and update flows — manual SW is notoriously buggy |
| URL state compression | Custom binary encoding | JSON → base64 | base64 is universally URL-safe, requires no custom decoder; JSON is human-debuggable; 5 sliders + scenario + profile ≈ 200 bytes |
| SVG pattern fills | Inline pattern markup per chart | Shared `<defs>` in chart config | Reusing 4 `<pattern>` definitions avoids duplication; `patterns.ts` exports them once, each chart references via `url(#pattern-*)` |
| axe-core CI integration | Manual axe-core script | `@axe-core/playwright` | Playwright-native integration with `expect(page).toHaveNoViolations()` — runs in CI without separate tooling |

**Key insight:** The "don't hand-roll" philosophy for Phase 3 is about accessibility. Every slider, chart, and interactive element has legal compliance requirements (RGAA 4). Established libraries (React Aria, Vega-Lite) have been battle-tested for WAI-ARIA conformance — hand-rolling would require accessibility expert review per component.

## Common Pitfalls

### Pitfall 1: WorkerOrchestrator.init() Called Before splash Assets Fetched

**What goes wrong:** The splash screen calls `orchestrator.init()` before `fetch()` completes for scenarios JSON and shock matrix. Workers receive partial/empty data, report ERROR, splash screen hangs.

**Why it happens:** Async confusion — `Promise.all([fetchA, fetchB]).then(() => orchestrator.init(dataA, dataB))` looks correct but `dataA` needs `.json()` parsing and `dataB` needs `.arrayBuffer()`.

**How to avoid:**
```typescript
const [scenariosRes, matrixRes] = await Promise.all([
  fetch('/data/scenarios-v2025.1.json'),
  fetch('/data/shockmatrix-v2025.1.parquet'),
]);
const scenariosJson = await scenariosRes.text();
const matrixBytes = await matrixRes.arrayBuffer();
await orchestrator.init(scenariosJson, matrixBytes);
```

**Warning signs:** Splash screen shows "Initialisation du moteur..." forever. Console shows "Cache not initialized — send INIT first" errors.

### Pitfall 2: Vega-Lite Pattern Fills Don't Render in All Browsers

**What goes wrong:** SVG `<pattern>` elements defined in Vega-Lite's config don't propagate to the rendered output. Charts show solid colors only, violating A11Y-03.

**Why it happens:** Vega-Lite's `config.style` doesn't directly support custom `<pattern>` fills. The pattern must be injected into the SVG `<defs>` at the Vega spec level (not Vega-Lite), using a Vega `signal` or a post-render hook.

**How to avoid:** Use `vega-embed`'s `patch` option to inject pattern `<defs>` after render, OR use Vega (not Vega-Lite) layer for the area fill with explicit `fill="url(#pattern-*)"`. Alternatively: define patterns in a global `<svg><defs>` element in the page and reference via URL — this works because SVG `url()` references are document-global.

**Warning signs:** Charts render with solid colors in Firefox. `fill: url(#pattern-deficit)` appears in devtools but no pattern visible.

### Pitfall 3: useTransition Doesn't Work Properly with Web Worker Results

**What goes wrong:** `startTransition(() => { const result = await orchestrator.project(...); setChartData(result); })` doesn't mark the update as a transition because `startTransition` doesn't handle async functions natively in React 19's standard API.

**Why it happens:** `startTransition` only marks synchronous state updates as transitions. The async response from the worker arrives outside the transition scope. The `isPending` flag flips to `false` before the worker responds.

**How to avoid:** Use the pattern: `startTransition` wraps a synchronous `setIsComputing(true)`. The actual worker result updates state normally (already behind the transition). The opacity pulse is driven by `isComputing` which was set inside the transition.

```typescript
function handleSliderChange(value: number) {
  setDisplayValue(value); // instant (synchronous)
  startTransition(() => {
    setIsComputing(true); // triggers opacity pulse (inside transition)
  });
  orchestrator.project(tax, spend, 5).then(result => {
    setChartData(result); // normal update (not in transition — acceptable)
    setIsComputing(false);
  });
}
```

**Warning signs:** `isPending` returns to `false` before charts update. No visible loading indicator during computation.

### Pitfall 4: URL State Encoding/Decoding with Unicode Characters

**What goes wrong:** `btoa(JSON.stringify(state))` throws `InvalidCharacterError` when the JSON contains non-Latin1 characters (e.g., "é" in scenario descriptions). Or `atob()` fails silently, losing the state.

**Why it happens:** `btoa`/`atob` only support Latin1 (0-255 code points). French text with accents exceeds this range. CONTEXT.md examples show only ASCII, but real scenario descriptions and methodology text contain French characters.

**How to avoid:** Always use the `unescape(encodeURIComponent(...))` wrapper for `btoa` and `decodeURIComponent(escape(...))` for `atob`. This converts multi-byte characters to %XX sequences that fit in Latin1.

**Warning signs:** URL state silently fails to decode. `InvalidCharacterError` in console on share. French-named scenarios break URL sharing.

### Pitfall 5: Slider Debounce Causes Visual Disconnect

**What goes wrong:** Debouncing slider ARIA announcements to drag-end creates a gap where the visual slider position doesn't match the screen reader announcement. Intermediate slider positions are silently skipped.

**Why it happens:** A11Y-05 requires debounced announcements on drag-end to avoid chatter. But if `aria-valuenow` is also debounced, screen readers see stale values during drag.

**How to avoid:** Update `aria-valuenow` continuously during drag. Only debounce `aria-valuetext` (the human-readable announcement). Screen readers track `aria-valuenow` for current position and only read the announcement once on drag-end.

**Warning signs:** Screen reader reads value after drag stops that doesn't match where the thumb is. Or screen reader reads nothing during drag (correct: should be silent) but reads wrong value at end (bug).

## Code Examples

### Full Slider Component with useTransition + useSlider

```typescript
// Source: React Aria (Context7 /websites/react-aria_adobe) + React 19 (Context7 /reactjs/react.dev)
// Combined pattern for Budget Citoyen

import { useRef, useState, useTransition, useCallback, useMemo } from 'react';
import { useSlider, useSliderThumb } from 'react-aria';
import { useSliderState } from 'react-stately';

interface FiscalSliderProps {
  label: string;
  minValue: number;
  maxValue: number;
  step: number;
  defaultValue?: number;
  onDragEnd: (value: number) => void;   // triggers macro projection
  onValueChange: (value: number) => void; // instant value label update
  disabled?: boolean;
}

export function FiscalSlider({
  label, minValue, maxValue, step, defaultValue = 0,
  onDragEnd, onValueChange, disabled = false,
}: FiscalSliderProps) {
  const trackRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [isPending, startTransition] = useTransition();

  const formatter = useMemo(
    () => new Intl.NumberFormat('fr-FR', {
      style: 'percent',
      signDisplay: 'always',
      maximumFractionDigits: 0,
    }),
    []
  );

  const state = useSliderState({
    value: [defaultValue],
    minValue, maxValue, step,
    onChange: ([v]) => onValueChange(v),
    onChangeEnd: ([v]) => {
      startTransition(() => onDragEnd(v));
    },
    label,
    numberFormatter: formatter,
    isDisabled: disabled,
  });

  const { groupProps, trackProps, labelProps, outputProps } = useSlider(
    { label, minValue, maxValue, step, 'aria-label': label },
    state,
    trackRef,
  );

  const { thumbProps, inputProps } = useSliderThumb(
    { index: 0, trackRef, inputRef },
    state,
  );

  return (
    <div {...groupProps} className="relative py-6 touch-target-min">
      <div className="flex justify-between items-baseline mb-2">
        <label {...labelProps} className="text-sm font-normal text-slate-700">
          {label}
        </label>
        <output {...outputProps} className="text-sm font-semibold text-slate-900 tabular-nums">
          {formatter.format(state.values[0] / 100)}
        </output>
      </div>
      {/* Track */}
      <div
        {...trackProps}
        ref={trackRef}
        className={`
          relative h-3 rounded-full cursor-pointer
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
          ${isPending ? 'animate-pulse' : ''}
        `}
        style={{
          background: `linear-gradient(to right, #1E3A5F 0%, #1E3A5F ${
            ((state.values[0] - minValue) / (maxValue - minValue)) * 100
          }%, #CBD5E1 ${((state.values[0] - minValue) / (maxValue - minValue)) * 100}%, #CBD5E1 100%)`,
        }}
      >
        {/* Thumb */}
        <div
          {...thumbProps}
          className="absolute top-1/2 -translate-y-1/2 w-11 h-11 bg-[#1E3A5F] rounded-full shadow-md cursor-grab active:cursor-grabbing focus:outline-2 focus:outline-offset-2 focus:outline-[#1E3A5F]"
          style={{ left: `${((state.values[0] - minValue) / (maxValue - minValue)) * 100}%` }}
        />
        {/* Baseline notch at 0% */}
        {minValue <= 0 && maxValue >= 0 && (
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-white/50"
            style={{ left: `${((-minValue) / (maxValue - minValue)) * 100}%` }}
            aria-hidden="true"
          />
        )}
      </div>
      {/* Hidden native input for touch screen readers */}
      <input {...inputProps} ref={inputRef} />
      {/* "Actuel" label at 0% */}
      {minValue <= 0 && maxValue >= 0 && (
        <span
          className="absolute text-xs text-slate-400 mt-1"
          style={{ left: `${((-minValue) / (maxValue - minValue)) * 100}%`, transform: 'translateX(-50%)' }}
          aria-hidden="true"
        >
          Actuel
        </span>
      )}
    </div>
  );
}
```

### Vega-Lite Chart with Pattern Fill (RGAA 4)

```typescript
// Source: Vega-Lite 6.4 docs (webfetch: vega.github.io/vega-lite/docs/encoding.html)
// Pattern integration via Vega-level config

// patterns.ts — shared SVG pattern definitions
export const CHART_PATTERNS_SVG = `
<defs>
  <pattern id="pattern-deficit" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
    <line x1="0" y1="0" x2="0" y2="8" stroke="#0072B2" stroke-width="1.5" opacity="0.5"/>
  </pattern>
  <pattern id="pattern-debt" width="6" height="6" patternUnits="userSpaceOnUse">
    <circle cx="3" cy="3" r="1.5" fill="#E69F00" opacity="0.5"/>
  </pattern>
  <pattern id="pattern-gdp" width="8" height="8" patternUnits="userSpaceOnUse">
    <line x1="0" y1="0" x2="8" y2="8" stroke="#009E73" stroke-width="1" opacity="0.5"/>
    <line x1="8" y1="0" x2="0" y2="8" stroke="#009E73" stroke-width="1" opacity="0.5"/>
  </pattern>
  <pattern id="pattern-employment" width="6" height="6" patternUnits="userSpaceOnUse">
    <rect x="0" y="0" width="2" height="6" fill="#CC79A7" opacity="0.5"/>
  </pattern>
</defs>`;

// ChartCell.tsx — renders a single accessible chart
function ChartCell({ data, spec, patternId, title, tableData }: ChartCellProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const specWithData = {
      ...spec,
      data: { values: data },
      description: `${title} — projection sur 5 ans`,
    };
    vegaEmbed(containerRef.current, specWithData, {
      actions: false, // no export menu for citizen mode
      renderer: 'svg', // SVG only, no canvas for RGAA 4
      patch: (spec) => {
        // Inject pattern defs into the rendered Vega spec
        if (!spec.marks) spec.marks = [];
        // Add a background rect with pattern fill
        spec.marks[0] = {
          ...spec.marks[0],
          fill: `url(#${patternId})`,
        };
        return spec;
      },
    });
  }, [data, spec, title, patternId]);

  return (
    <figure className="relative">
      <figcaption id={`chart-title-${patternId}`} className="text-lg font-semibold mb-2">
        {title}
      </figcaption>
      <div
        ref={containerRef}
        role="img"
        aria-labelledby={`chart-title-${patternId}`}
        className="w-full"
      />
      <ChartTableFallback title={title} data={tableData} />
    </figure>
  );
}

// ChartTableFallback.tsx — HTML table for screen readers (A11Y-02)
function ChartTableFallback({ title, data }: { title: string; data: Array<Record<string, unknown>> }) {
  const columns = data.length > 0 ? Object.keys(data[0]) : [];
  return (
    <table className="sr-only" aria-label={`Données tabulaires: ${title}`}>
      <caption>{title}</caption>
      <thead>
        <tr>
          {columns.map(col => <th key={col} scope="col">{col}</th>)}
        </tr>
      </thead>
      <tbody>
        {data.map((row, i) => (
          <tr key={i}>
            {columns.map(col => <td key={col}>{String(row[col])}</td>)}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| WASM microsimulation (Rust) | Pure TS scenario cache + WorkerOrchestrator | Phase 2 (2026-05) | No WASM toolchain needed for Phase 3; all computation is pure TS in Web Workers |
| Rust `interpn` interpolation | Pure TS `macro-interpolate.ts` | Phase 2 (2026-05) | Same trilinear interpolation algorithm, now in TypeScript — no serialization overhead |
| D3.js for all charts | Vega-Lite 6.4 for standard macro charts | Decision D-16 | Declarative specs reduce chart code by ~70%; D3 reserved for Phase 4 custom charts |
| Inline patterns per chart | Shared SVG `<defs>` in `patterns.ts` | Phase 3 design | 4 patterns defined once, referenced by all charts — DRY, consistent |
| `tailwind.config.js` | CSS-first `@theme` directive | Tailwind 4.3 (2025) | No separate config file; theme variables in `index.css` with `@theme` |

**Deprecated/outdated:**
- `wasm-micro` and `wasm-macro` crates: Removed in Phase 2. Phase 3 uses pure TS equivalents.
- `tailwind.config.js`: Tailwind 4 uses `@theme` in CSS. No config file needed.
- `serde_yaml` (Rust crate): Deprecated at v0.9.34. Phase 3 doesn't touch Rust at all — irrelevant.

## Integration Map

### Phase 2 Artifacts → Phase 3 Consumption

| Phase 2 Artifact | Phase 3 Consumer | Interface | New Types Needed |
|-----------------|------------------|-----------|-----------------|
| `WorkerOrchestrator` (orchestrator.ts) | `useSimulation` hook → `SplashScreen` → `SimulatorPage` | `init(scenariosJson, matrixBytes)` then `simulate()`, `project()`, `interpolate()` | `SliderState`, `URLState` |
| `ScenarioCache` (scenario-cache.ts) | Interpolation layer (interpolation.ts) + `ScenarioGrid` | `listScenarios()` for grid, `lookup()` for interpolation | `WeightedScenario` |
| `macro-interpolate.ts` | Macro worker (consumed as-is) → `ChartGrid` | `MacroResult` → Vega-Lite chart specs | Chart data transform types |
| `engine/types.ts` | All UI components | `ScenarioResult`, `MacroResult`, `ScenarioDefinition` | `InterpolationResult`, slider payload types |
| `citizen-worker.ts` | WorkerOrchestrator → interpolation layer | Via orchestrator.simulate() | None |
| `macro-worker.ts` | WorkerOrchestrator → ChartGrid | Via orchestrator.project() | None |
| `parameters-v2025.1.json` | `index-map.ts` (to determine default rates for lever labels) | Read at build-time or load-time | PARAM_INDICES constant map |
| `shockmatrix-v2025.1.parquet` | SplashScreen → WorkerOrchestrator.init() → macro-worker | ArrayBuffer transfer | None |

### New Types to Add

```typescript
// webapp/src/state/types.ts

/** Positions des 5 curseurs citoyens (pourcentage de changement par rapport à la baseline). */
export interface SliderState {
  ir: number;           // IR ménages (±30%)
  is: number;           // IS entreprises (±30%)
  tva: number;          // TVA (±30%)
  cotisations: number;  // Cotisations sociales (±30%)
  depenses: number;     // Dépenses publiques (±30%)
}

/** État complet encodé dans l'URL. */
export interface URLState {
  s: string | null;                 // scenarioId (null = aucun scénario sélectionné)
  p: SliderState;                   // positions des curseurs
  f: number;                        // profileIndex (0=modeste, 1=médian, 2=aisé)
  a: boolean;                       // advancedMode
}

/** Résultat d'interpolation entre scénarios. */
export interface InterpolationResult {
  scenarioResult: ScenarioResult;   // blended household impact
  sourceScenarios: string[];        // IDs des scénarios sources
  weights: number[];                // poids correspondants
  isExact: boolean;                 // true si slider correspond exactement à un scénario
}

/** Paramètre fiscal mappé depuis un levier citoyen. */
export interface ParameterMapping {
  citizenLever: string;             // e.g., "ir"
  parameterKeys: string[];          // e.g., ["ir.bareme.tranche1", "ir.bareme.tranche2", ...]
  proportions: number[];            // distribution proportionnelle (poids par paramètre)
}
```

### index-map.ts Content (to Create)

```typescript
// webapp/src/state/index-map.ts
//
// Maps citizen levers to underlying parameter groups.
// Each citizen lever controls multiple individual parameters in fixed proportions.
// Pattern: lever percentage change → distributed proportionally across sub-parameters.

export interface LeverMapping {
  /** Citizen lever name. */
  name: string;
  /** Sub-parameter keys (match ScenarioDefinition.parameterOverrides keys). */
  subParams: string[];
  /** Proportional weights for distributing the % change (must sum to 1.0). */
  weights: number[];
  /** Default baseline rate for this lever (used for "Taux: X%" display). */
  baselineRate: number;
  /** Display format for the rate label. */
  rateFormat: 'percent' | 'currency' | 'none';
}

export const LEVER_MAPPINGS: Record<string, LeverMapping> = {
  ir: {
    name: 'IR ménages',
    subParams: ['ir.bareme.tranche1', 'ir.bareme.tranche2', 'ir.bareme.tranche3', 'ir.bareme.tranche4', 'ir.bareme.tranche5'],
    weights: [0.2, 0.2, 0.2, 0.2, 0.2], // equal proportional adjustment
    baselineRate: 0.0, // placeholder — derive from parameters JSON
    rateFormat: 'percent',
  },
  is: {
    name: 'IS entreprises',
    subParams: ['is.taux'],
    weights: [1.0],
    baselineRate: 0.0,
    rateFormat: 'percent',
  },
  tva: {
    name: 'TVA',
    subParams: ['tva.taux.normal', 'tva.taux.reduit'],
    weights: [0.7, 0.3], // normal rate gets 70% of adjustment weight
    baselineRate: 0.0,
    rateFormat: 'percent',
  },
  cotisations: {
    name: 'Cotisations sociales',
    subParams: ['cotisations.salariales', 'cotisations.patronales', 'cotisations.csg_crds'],
    weights: [0.35, 0.35, 0.3],
    baselineRate: 0.0,
    rateFormat: 'percent',
  },
  depenses: {
    name: 'Dépenses publiques',
    subParams: ['depenses.spend_level', 'depenses.effectifs'],
    weights: [0.7, 0.3],
    baselineRate: 0.0,
    rateFormat: 'percent',
  },
};
```

## Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Scenario pre-compute data doesn't exist yet (CI pipeline needed) | MEDIUM | CRITICAL | Phase 3 requires at least 9 scenario JSON files. Plan should include a Wave 0 task to generate synthetic scenario data or flag as blocker if CI pipeline isn't ready |
| Vega-Lite pattern fills don't work cross-browser | MEDIUM | HIGH | Mitigation: test pattern rendering in Chromium + Firefox + WebKit early. Fallback: D3.js manual SVG construction if Vega-Lite can't support it |
| useTransition + Worker async pattern causes timing issues | LOW | MEDIUM | Mitigation: use `startTransition` only for `setIsComputing()`; actual worker result updates happen outside transition (acceptable UX) |
| Service Worker aggressively caches and breaks app update | MEDIUM | MEDIUM | Mitigation: Workbox's `skipWaiting()` + `clientsClaim()` + versioned asset URLs. "New version available" prompt for major updates |
| Mobile slider touch targets < 44px on small screens | LOW | LOW | Mitigation: UI-SPEC mandates 44px touch targets; Tailwind's `touch-target-min` custom utility. Playwright mobile viewport tests verify |
| URL state too long for some browsers/sharers (>2000 chars) | LOW | LOW | Mitigation: base64 JSON of 5 sliders + 1 scenario + 1 profile + 1 boolean ≈ 200 chars. Well under limits. Monitor if advanced mode adds many parameters |
| axe-core CI finds false positives that block merge | LOW | LOW | Mitigation: axe-core Playwright supports `.toHaveNoViolations({ excludedRules: [...] })` for known false positives. Document any exclusions |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest 4.1.6 (unit/integration) + Playwright 1.60.0 (E2E/a11y) |
| Config file | `vitest.config.ts` + `playwright.config.ts` (new — Wave 0) |
| Quick run command | `vitest run src/state/__tests__/url-codec.test.ts` (unit) |
| Full suite command | `vitest run && npx playwright test` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| UI-01 | Sliders adjust fiscal levers (IR, IS, TVA, cotisations) | e2e | `npx playwright test tests/a11y.spec.ts` — ARIA assertions on all 5 levers | ❌ Wave 0 |
| UI-02 | Household impact updates in real time | e2e + unit | `vitest run src/state/__tests__/interpolation.test.ts` | ❌ Wave 0 |
| UI-03 | Deficit/debt/GDP/employment charts render | e2e | `npx playwright test tests/simulator.spec.ts:chart-render` | ❌ Wave 0 |
| UI-04 | Reset button returns to initial state | e2e | `npx playwright test tests/simulator.spec.ts:reset` | ❌ Wave 0 |
| UI-05 | Share via URL captures complete state | unit + e2e | `vitest run src/state/__tests__/url-codec.test.ts` | ❌ Wave 0 |
| UI-06 | Responsive layout, touch targets ≥ 44px | e2e | `npx playwright test tests/simulator.spec.ts:mobile --viewport='iPhone 13'` | ❌ Wave 0 |
| UI-07 | Loading indicator during async computation | e2e | `npx playwright test tests/simulator.spec.ts:loading` | ❌ Wave 0 |
| UI-08 | Methodology page with data attribution | e2e | `npx playwright test tests/simulator.spec.ts:methodology` | ❌ Wave 0 |
| A11Y-01 | SVG charts have role="img", aria-labelledby | e2e (a11y) | `npx playwright test tests/a11y.spec.ts:charts` | ❌ Wave 0 |
| A11Y-02 | HTML table with `<th scope>` adjacent to each chart | e2e (a11y) | `npx playwright test tests/a11y.spec.ts:tables` | ❌ Wave 0 |
| A11Y-03 | Pattern fills + deuteranopia-safe colors | e2e (a11y) | `npx playwright test tests/a11y.spec.ts:patterns` | ❌ Wave 0 |
| A11Y-04 | Animations > 5s have interruption (N/A — no long animations) | manual-only | N/A — opacity pulse is 300ms, well under 5s threshold | N/A |
| A11Y-05 | Sliders have full WAI-ARIA + keyboard nav | e2e (a11y) | `npx playwright test tests/a11y.spec.ts:sliders` | ❌ Wave 0 |
| A11Y-06 | axe-core passes in CI | ci-gate | `npx playwright test tests/a11y.spec.ts` (all tests run axe assertions) | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `vitest run src/state/__tests__/` (unit tests for codec/interpolation/index-map)
- **Per wave merge:** `vitest run && npx playwright test tests/a11y.spec.ts` (unit + accessibility)
- **Phase gate:** `vitest run && npx playwright test` (full suite green before `/gsd-verify-work`)

### Wave 0 Gaps
- [ ] `vitest.config.ts` — Vitest configuration (new)
- [ ] `playwright.config.ts` — Playwright configuration (new)
- [ ] `src/state/__tests__/url-codec.test.ts` — URL state codec unit tests
- [ ] `src/state/__tests__/interpolation.test.ts` — Interpolation algorithm tests
- [ ] `src/state/__tests__/index-map.test.ts` — Lever→parameter mapping tests
- [ ] `tests/simulator.spec.ts` — E2E user flow tests
- [ ] `tests/a11y.spec.ts` — Accessibility audit tests (axe-core)
- [ ] Framework install: `npm install -D vitest @playwright/test jsdom @axe-core/playwright`

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No authentication in citizen mode |
| V3 Session Management | No | No server-side session. Simulation state is URL-encoded, client-side only |
| V4 Access Control | No | No role-based access. All computation is client-side |
| V5 Input Validation | Yes | Slider values validated: range check (min/max), finite check, type coercion defense. Macro parameters validated by convex hull gating in interpolateAtPoint |
| V6 Cryptography | No | No encryption needed — data never leaves the client |

### Known Threat Patterns for React 19 + Web Workers + Vegalite

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| URL state parameter injection (malicious base64) | Tampering | `decodeState()` validates JSON structure; unrecognized fields ignored; scalar values type-checked (number, boolean, string|null) |
| XSS via Vega-Lite spec injection | Tampering | Vega-Lite specs are pre-defined in code, not dynamically constructed from user input. User data values (slider positions) are always numbers, not strings |
| Service Worker cache poisoning | Spoofing | Workbox cache versioning; `Cache-Control: immutable` for versioned assets; integrity hashes verified |
| postMessage spoofing to workers | Spoofing | WorkerRequest.type whitelist (INIT/SIMULATE/INTERPOLATE/PROJECT only); unknown types rejected. Workers verify payload structure before processing |
| Timing side-channel via macro interpolation | Information Disclosure | Convex hull gating returns null (constant time) for all out-of-bounds inputs; no differentiation between "near boundary" and "far outside" |

## Environment Availability

> Step 2.6: SKIPPED (Phase 3 dependencies are npm packages, all installable via `npm install`. No system-level dependencies beyond Node.js and npm which are already available in the project environment.)

**Note:** The following npm packages are new for Phase 3 and will be installed by the build plan:

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| react | UI framework | ✓ (installable) | 19.2.6 | — |
| react-aria-components | Accessible sliders | ✓ (installable) | 1.17.0 | — |
| vega-lite | Chart specs | ✓ (installable) | 6.4.3 | D3.js 7.9 if pattern fills fail |
| vega-embed | Chart rendering | ✓ (installable) | 7.1.0 | — |
| workbox-build | Service worker | ✓ (installable) | 7.4.1 | Manual SW or vite-plugin-pwa |
| @axe-core/playwright | CI a11y testing | ✓ (installable) | 4.11.3 | — |
| lucide-react | Icons | ✓ (installable) | 1.14.0 | — |
| react-router-dom | Routing | ✓ (installable) | 7.15.0 | Conditional rendering (simpler, no routes) |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | 9-12 pre-computed scenario JSON files exist or can be generated as part of Phase 3 | Risk Analysis | HIGH — Phase 3 cannot render anything without scenario data. If CI pipeline isn't ready, Plan must include synthetic/minimal scenario generation task |
| A2 | The shock matrix binary (2.6KB Parquet) works with the macro-worker's binary parser | Integration Map | MEDIUM — parser is tested against synthetic grid from Phase 2 tests, but hasn't been tested with real Parquet data. A mismatch would require parser update |
| A3 | React Router 7 is the right choice for 2 routes (simulator + methodology) | Standard Stack | LOW — if React Router 7 has breaking changes vs v6, fall back to manual conditional rendering (simpler, acceptable for 2 routes) |
| A4 | Vega-Lite SVG pattern fills work in all target browsers (Chromium, Firefox, Safari) | Common Pitfalls | MEDIUM — SVG `<pattern>` is well-supported but Vega-Lite's integration path is untested. Manual Vega-level pattern injection may be needed |
| A5 | SharedArrayBuffer is NOT needed for Phase 3 (no wasm-bindgen-rayon, no multi-threaded WASM) | Architecture | LOW — Phase 2 removed WASM; workers use postMessage Transferable, not SharedArrayBuffer. COOP/COEP headers not required |
| A6 | `index-map.ts` proportional weights (e.g., 0.2 per IR bracket) produce acceptable slider behavior | State Design | MEDIUM — weights are initial guesses. Real-world tuning with scenario data may require adjustment. Plan should include adjustable-weight interface |

## Open Questions (RESOLVED)

1. **Where do the 9-12 scenario JSON files come from?** — RESOLVED
   - **Decision:** Synthetic generation via Plan 03-08 Task 1. The CI pipeline (Phase 2 Plan 02-04, openfisca-france pre-compute) may not be finalized; this plan includes a data-generation task that constructs 9 structurally correct ScenarioDoc objects programmatically from a Baseline 2025 definition + 8 reform/program variants with realistic French names and per-profile household impacts. The generated `public/data/scenarios-v2025.1.json` is served as a static asset by Vite and loadable via `ScenarioCache.loadFromJSON()`.
   - **Plan reference:** 03-08-PLAN.md, Task 1 — "Generate minimal synthetic scenario data for UI development"
   - **Rationale:** Unblocks UI development and testing without waiting for CI pipeline maturity. The synthetic data is structurally identical to CI-generated data — swapping in real pre-computed scenarios later requires no code changes.

2. **What are the exact slider ranges for each lever?** — RESOLVED
   - **Decision:** ±30% for all 5 levers (IR ménages, IS entreprises, TVA, Cotisations sociales, Dépenses publiques). This is consistent with UI-SPEC's `aria-valuemin=-30`, `aria-valuemax=+30` defaults. All levers share the same range for UI consistency and simplicity in citizen mode.
   - **Plan reference:** 03-05-PLAN.md, Task 2 SliderGroup — all levers initialized with minValue=-30, maxValue=30, step=1.
   - **Rationale:** Convex hull gating in macro-interpolate naturally handles out-of-bounds macro results (returns null → greyed chart overlay per D-21). Citizen-mode doesn't need lever-specific ranges — the advanced mode (D-11) exposes individual sub-parameter sliders that may have narrower bands in a future phase. Uniform ±30% keeps the mental model simple for niveau-lycée users (D-26).

3. **Should the interpolation layer run on main thread or in a worker?** — RESOLVED
   - **Decision:** Main-thread interpolation via `ScenarioCache.lookup()` O(1) HashMap calls. The interpolation module (`interpolateScenarios()` in Plan 03-02) runs on the main thread, computing Euclidean distances across ≤12 scenarios, sorting, and blending — all <1ms operations. ScenarioCache is instantiated on the main thread via `ScenarioCache.loadFromJSON()` after the citizen-worker reports READY; the worker's cache is used for heavy batch simulation, not per-slider interpolation.
   - **Plan reference:** 03-02-PLAN.md, Module 3 — `interpolateScenarios()` main-thread pure function; 03-07-PLAN.md, useSimulation hook — `handleSliderChange` calls interpolation synchronously.
   - **Rationale:** The original recommendation (Option A: add INTERPOLATE message type to citizen-worker) was reconsidered for MVP. For ≤12 scenarios × 3 profiles × O(1) lookups, the worker message round-trip overhead (~0.5-1ms postMessage serialization + event loop) exceeds the computation time (<0.1ms). Main-thread interpolation is simpler, faster for this data scale, and avoids duplicating the stale-response-discarding protocol for a sub-millisecond operation. If scenario count grows significantly (Phase 4+), the INTERPOLATE worker message type can be added without changing the caller API.

4. **Service Worker: Workbox manual config vs vite-plugin-pwa?** — RESOLVED
   - **Decision:** Direct Workbox 7.4.1 manual configuration. The Service Worker (`sw.js`) uses `importScripts` to load Workbox from CDN and manually registers CacheFirst (data assets), NetworkFirst (app shell), and StaleWhileRevalidate (methodology page) routes. The precache manifest is generated at build time via `workbox-build` CLI invoked as a post-build step in `package.json` scripts.
   - **Plan reference:** 03-07-PLAN.md, Task 3 — "Create Service Worker and Workbox configuration"
   - **Rationale:** Direct Workbox configuration gives more predictable strategy composition than vite-plugin-pwa's abstraction layer. The specific strategy requirements (CacheFirst for `/data/*`, NetworkFirst for `*.html|js|css|svg`, StaleWhileRevalidate for `/methodologie`) map directly to Workbox's `registerRoute` API. Manual config avoids plugin version compatibility issues and is well-documented in Workbox 7.4. If maintenance burden proves high in later phases, migrating to vite-plugin-pwa is straightforward since it wraps the same Workbox runtime.

## Sources

### Primary (HIGH confidence)
- Context7 `/reactjs/react.dev` — React 19 `useTransition` hook, `startTransition` pattern, `isPending` state — verified 2026-05-13
- Context7 `/websites/react-aria_adobe` — `useSlider` hook API, `aria-valuenow`/`aria-valuemin`/`aria-valuemax`, keyboard navigation, touch support — verified 2026-05-13
- Context7 `/vega/vega-lite` — `description` channel for ARIA accessibility, `vl2svg` rendering, encoding channel reference — verified 2026-05-13
- Official Vega-Lite docs (`vega.github.io/vega-lite/docs/encoding.html`) — `description` channel maps to `aria-label` on SVG; `config.aria` for auto-generated descriptions — verified via WebFetch 2026-05-13
- Official Tailwind CSS docs (`tailwindcss.com/docs/theme`) — `@theme` directive, namespace-based utility generation, CSS-first configuration — verified via WebFetch 2026-05-13
- Official Workbox docs (`developer.chrome.com/docs/workbox/service-worker-overview`) — CacheFirst, NetworkFirst, StaleWhileRevalidate strategies; precaching vs runtime caching — verified via WebFetch 2026-05-13
- `npm view` (npm registry) — All version numbers: React 19.2.6, React Aria 1.17.0, Vega-Lite 6.4.3, Vega-Embed 7.1.0, Workbox 7.4.1, Tailwind CSS 4.3.0, Vitest 4.1.6, Playwright 1.60.0, axe-core 4.11.3, lucide-react 1.14.0, react-router-dom 7.15.0 — verified 2026-05-13
- Phase 2 Source Code (`webapp/src/engine/types.ts`, `workers/orchestrator.ts`, `engine/scenario-cache.ts`, `engine/macro-interpolate.ts`, `workers/citizen-worker.ts`, `workers/macro-worker.ts`) — existing API contracts, correlation ID protocol, stale response discarding — verified by file read 2026-05-13
- Phase 3 UI-SPEC.md — Design system (color, typography, spacing, copy, layout, state machine) — verified by file read 2026-05-13

### Secondary (MEDIUM confidence)
- CONTEXT.md Phase 3 decisions (D-01 through D-31) — interpolation model, slider organization, chart architecture, UI layout, loading states — verified against discussed decisions
- CONTEXT.md Phase 2 decisions (D-05 through D-23) — hybrid architecture, privacy boundary, correlation ID protocol — cross-referenced with Phase 2 source code
- ARCHITECTURE.md (research) — component responsibilities, data flow, Web Worker isolation — partially outdated (references WASM) but UI layer patterns still applicable

### Tertiary (LOW confidence)
- Scenario data availability — assumed that 9-12 pre-computed scenarios exist or can be generated. This is the highest-risk assumption and must be validated first in planning
- `index-map.ts` proportional weights — initial guesses based on reasonable defaults. Will need tuning against real scenario data
- Vega-Lite pattern fill integration — assumed to work via Vega-level `patch` option. Needs browser testing to confirm

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions verified via npm registry on 2026-05-13
- Architecture: HIGH — based on existing Phase 2 code (read + understood) and UI-SPEC.md design contracts
- Integration: MEDIUM — interpolation layer and index-map are new designs; scenario data availability unconfirmed
- Pitfalls: HIGH — identified from React 19 docs, Vega-Lite docs, and project-specific Phase 2 patterns

**Research date:** 2026-05-13
**Valid until:** 2026-06-13 (30 days — stable stack, minor risk of React 19 patch releases)
