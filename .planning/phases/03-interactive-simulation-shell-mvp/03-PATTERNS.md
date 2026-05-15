# Phase 03: Interactive Simulation Shell (MVP) - Pattern Map

**Mapped:** 2026-05-13
**Files analyzed:** 43 new files (+ 0 modified)
**Analogs found:** 18 / 43 (25 files have no direct analog — patterns from RESEARCH.md code examples or standard tool configs)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `webapp/package.json` | config | build-tool | None (new scaffolding) | none |
| `webapp/tsconfig.json` | config | build-tool | None (new scaffolding) | none |
| `webapp/vite.config.ts` | config | build-tool | None (new scaffolding) | none |
| `webapp/index.html` | entry | static | None (new scaffolding) | none |
| `webapp/sw.js` | utility | event-driven | `webapp/src/workers/citizen-worker.ts` (Worker message handler pattern) | partial |
| `webapp/workbox-config.js` | config | build-tool | None (new scaffolding) | none |
| `webapp/src/main.tsx` | entry | mount | None (first React entry) | none |
| `webapp/src/App.tsx` | component | request-response | None (first React component) | none |
| `webapp/src/index.css` | config | static | None (Tailwind 4 @theme) | none |
| `webapp/src/state/types.ts` | model | N/A | `webapp/src/engine/types.ts` | exact |
| `webapp/src/state/url-codec.ts` | utility | transform | `webapp/src/engine/scenario-cache.ts` (pure functions + error handling) | partial |
| `webapp/src/state/interpolation.ts` | service | transform | `webapp/src/engine/macro-interpolate.ts` | exact |
| `webapp/src/state/index-map.ts` | utility | config | `webapp/src/engine/types.ts` (constant/enum-like pattern) | partial |
| `webapp/src/hooks/useSimulation.ts` | hook | event-driven | RESEARCH.md Pattern 1 (useTransition) | research-ref |
| `webapp/src/hooks/useSliderWithUrl.ts` | hook | event-driven | RESEARCH.md Pattern 2 (useSlider) | research-ref |
| `webapp/src/hooks/useServiceWorker.ts` | hook | event-driven | None (no existing hooks) | none |
| `webapp/src/components/SplashScreen.tsx` | component | request-response | RESEARCH.md code examples | research-ref |
| `webapp/src/components/ScenarioGrid.tsx` | component | request-response | None (first grid component) | none |
| `webapp/src/components/ScenarioCard.tsx` | component | request-response | None (first card component) | none |
| `webapp/src/components/LeverSlider.tsx` | component | request-response | RESEARCH.md "Full Slider Component" code example | research-ref |
| `webapp/src/components/SliderGroup.tsx` | component | request-response | None (first collapsible group) | none |
| `webapp/src/components/AdvancedToggle.tsx` | component | request-response | None (first toggle component) | none |
| `webapp/src/components/ImpactDisplay.tsx` | component | request-response | None (first profile display) | none |
| `webapp/src/components/ImpactPill.tsx` | component | request-response | None (first pill component) | none |
| `webapp/src/components/ChartGrid.tsx` | component | request-response | RESEARCH.md "ChartCell" code example | research-ref |
| `webapp/src/components/ChartCell.tsx` | component | request-response | RESEARCH.md "ChartCell" code example | research-ref |
| `webapp/src/components/ChartTableFallback.tsx` | component | request-response | RESEARCH.md "ChartTableFallback" code example | research-ref |
| `webapp/src/components/Footer.tsx` | component | request-response | None (first footer component) | none |
| `webapp/src/components/ErrorScreen.tsx` | component | request-response | None (first error component) | none |
| `webapp/src/charts/patterns.ts` | utility | static | None (first SVG pattern defs) | none |
| `webapp/src/charts/spec-deficit.ts` | config | static | None (first Vega-Lite spec) | none |
| `webapp/src/charts/spec-debt.ts` | config | static | None (first Vega-Lite spec) | none |
| `webapp/src/charts/spec-gdp.ts` | config | static | None (first Vega-Lite spec) | none |
| `webapp/src/charts/spec-employment.ts` | config | static | None (first Vega-Lite spec) | none |
| `webapp/src/charts/config.ts` | config | static | None (first Vega-Lite shared config) | none |
| `webapp/src/pages/SimulatorPage.tsx` | component | request-response | None (first page component) | none |
| `webapp/src/pages/MethodologyPage.tsx` | component | request-response | None (first static page) | none |
| `vitest.config.ts` | config | test | None (new test scaffolding) | none |
| `playwright.config.ts` | config | test | None (new test scaffolding) | none |
| `webapp/src/state/__tests__/url-codec.test.ts` | test | unit | `webapp/src/engine/__tests__/scenario-cache.test.ts` | exact |
| `webapp/src/state/__tests__/interpolation.test.ts` | test | unit | `webapp/src/engine/__tests__/macro-interpolate.test.ts` | exact |
| `webapp/src/state/__tests__/index-map.test.ts` | test | unit | `webapp/src/engine/__tests__/scenario-cache.test.ts` | exact |
| `webapp/src/__tests__/simulator.spec.ts` | test | e2e | None (first Playwright E2E) | none |
| `webapp/src/__tests__/a11y.spec.ts` | test | e2e | None (first Playwright a11y) | none |
| `webapp/src/__tests__/components/LeverSlider.test.tsx` | test | component | None (first Vitest component test) | none |

---

## Pattern Assignments

### `webapp/src/state/types.ts` (model, N/A)

**Analog:** `webapp/src/engine/types.ts`

**Imports pattern** (lines 1-9):
```typescript
// webapp/src/state/types.ts
//
// Central TypeScript type definitions for Budget Citoyen UI state.
// Mirrors the engine/types.ts pattern — pure TypeScript interfaces only,
// zero runtime dependencies.
//
// These types define the slider-to-engine bridge: citizen lever positions,
// URL-sharing state, and interpolation results.
```

**Core pattern** (lines 11-16 — file-level banner comment):
```typescript
// ── Slider State ─────────────────────────────────────────────────────────
//
// D-08: 4-5 simplified citizen levers as aggregate controls.
```
The convention: section divider comments with `// ── Section Name ──` (dash-padded), JSDoc on each interface, explicit reference to CONTEXT.md decision IDs.

**Interface pattern** (lines 23-36 from ScenarioResult):
```typescript
export interface ScenarioResult {
  /** Impôt sur le revenu. */
  ir: number;
  /** Impôt sur les sociétés (contribution du profil). */
  is: number;
  // ...
}
```
Every field gets a JSDoc comment with French description.

**Key difference:** `state/types.ts` imports from `../engine/types` for shared types (`ScenarioResult`, `ScenarioDefinition`, `MacroResult`):
```typescript
import type { ScenarioResult, ScenarioDefinition } from '../engine/types';
```

---

### `webapp/src/state/url-codec.ts` (utility, transform)

**Analog:** `webapp/src/engine/scenario-cache.ts` (pure function modules) + `webapp/src/engine/macro-interpolate.ts` (input validation)

**File banner** (lines 1-8 from scenario-cache.ts):
```typescript
// webapp/src/state/url-codec.ts
//
// URL state encoding/decoding for Budget Citoyen.
// Encodes the full simulation state (sliders, scenario, profile, advanced mode)
// into a single base64 `?state=` query parameter for URL sharing (D-23).
//
// D-23: Single `?state=<base64>` parameter. Decoded on load to restore state.
```

**Imports pattern** — pure functions, no class needed:
```typescript
import type { URLState } from './types';
```

**Pure function signature pattern** (from macro-interpolate.ts lines 67-72):
```typescript
export function encodeState(state: URLState): string {
  const json = JSON.stringify(state);
  return btoa(unescape(encodeURIComponent(json)));
}
```

**Error handling pattern** (from macro-interpolate.ts lines 117-119 — `if (!isFinite(...)) return null`):
```typescript
export function decodeState(encoded: string): URLState | null {
  try {
    const json = decodeURIComponent(escape(atob(encoded)));
    const state = JSON.parse(json);
    // Type-check scalar fields
    if (typeof state?.s !== 'string' && state?.s !== null) return null;
    if (typeof state?.f !== 'number') return null;
    if (typeof state?.a !== 'boolean') return null;
    return state as URLState;
  } catch {
    return null;
  }
}
```

**Key pattern:** Functions are pure (no side effects). Invalid input returns `null` (never throws). This matches the Phase 2 engine convention of `result | null` returns.

---

### `webapp/src/state/interpolation.ts` (service, transform)

**Analog:** `webapp/src/engine/macro-interpolate.ts`

**File banner** (lines 1-5):
```typescript
// webapp/src/state/interpolation.ts
//
// Scenario-to-scenario interpolation using inverse distance weighting (IDW).
// Blends pre-computed ScenarioResults from the 2-3 nearest scenarios in
// parameter space, giving citizens a continuous slider feel (D-01, D-02).
```

**Imports pattern** (from engine/types.ts + scenario-cache.ts):
```typescript
import type { ScenarioDefinition, ScenarioResult } from '../engine/types';
import type { ScenarioCache } from '../engine/scenario-cache';
import type { SliderState, InterpolationResult } from './types';
```

**Algorithm pattern** — numeric constants as module-level `const` (from macro-interpolate.ts lines 19-21):
```typescript
/** Default number of nearest scenarios to blend. */
const DEFAULT_K = 3;
/** Threshold below which an exact match is returned. */
const EXACT_MATCH_THRESHOLD = 1e-3;
```

**Core function** — pure, returns result | null, input validation guard (from macro-interpolate.ts lines 110-130):
```typescript
export function interpolateScenarios(
  sliderParams: SliderState,
  scenarioDefs: ScenarioDefinition[],
  scenarioCache: ScenarioCache,
  profileIndex: number,
  k: number = DEFAULT_K,
): InterpolationResult | null {
  if (scenarioDefs.length === 0) return null;
  if (profileIndex < 0) return null;
  // 1. Compute Euclidean distances...
  // 2. Sort, take k nearest...
  // 3. If exact match (dist < threshold), return scenario result directly
  // 4. Inverse distance weighting...
  // 5. Weighted blend...
}
```

**Key difference:** This module calls `ScenarioCache.lookup()` (O(1) read) — no side effects beyond reading from the cache. The actual RESEARCH.md provides the full algorithm.

---

### `webapp/src/state/index-map.ts` (utility, config)

**Analog:** `webapp/src/engine/types.ts` (type definition pattern for structured data) + constant conventions from `macro-interpolate.ts` (module-level `const`)

**File banner:**
```typescript
// webapp/src/state/index-map.ts
//
// Maps citizen fiscal levers to underlying OpenFisca parameter groups.
// Each lever controls multiple individual parameters in fixed proportions (D-08, D-12).
//
// Pattern: lever percentage change → distributed proportionally across sub-parameters.
```

**Type + constant pattern** — types first, then the constant object:
```typescript
// ── Lever Mapping Types ──────────────────────────────────────────────────

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

// ── Lever Mappings Constant ──────────────────────────────────────────────

/** Maps citizen lever keys to their parameter configuration. */
export const LEVER_MAPPINGS: Record<string, LeverMapping> = {
  ir: {
    name: 'IR ménages',
    subParams: [
      'ir.bareme.tranche1',
      'ir.bareme.tranche2',
      'ir.bareme.tranche3',
      'ir.bareme.tranche4',
      'ir.bareme.tranche5',
    ],
    weights: [0.2, 0.2, 0.2, 0.2, 0.2],
    baselineRate: 0.0,
    rateFormat: 'percent',
  },
  // ... is, tva, cotisations, depenses
};
```

**Key difference:** RESEARCH.md provides the full content — weights are initial guesses (RESEARCH.md A6). This is a static lookup table, not a computation engine.

---

### `webapp/src/hooks/useSimulation.ts` (hook, event-driven)

**Analog:** RESEARCH.md Pattern 1 (`useTransition`) + `webapp/src/workers/orchestrator.ts` (WorkerOrchestrator API)

**File banner:**
```typescript
// webapp/src/hooks/useSimulation.ts
//
// Central hook managing the WorkerOrchestrator lifecycle, simulation state,
// and coordination between scenario selection, slider interpolation, and
// macro projection requests.
//
// D-07: Primary flow — scenario selection first, sliders second.
// D-15: Throttled drag with instant value labels, deferred computation.
```

**Imports pattern** — engine types + WorkerOrchestrator + React 19 hooks:
```typescript
import { useState, useTransition, useCallback, useEffect, useRef } from 'react';
import { WorkerOrchestrator } from '../workers/orchestrator';
import type { ScenarioResult, MacroResult, ScenarioDefinition } from '../engine/types';
import type { SliderState, InterpolationResult, URLState } from '../state/types';
```

**Core hook signature:**
```typescript
export function useSimulation() {
  const orchestratorRef = useRef<WorkerOrchestrator | null>(null);
  const [isPending, startTransition] = useTransition();
  const [phase, setPhase] = useState<'loading' | 'preselect' | 'displaying' | 'error'>('loading');
  const [scenarios, setScenarios] = useState<ScenarioDefinition[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string | null>(null);
  const [sliderState, setSliderState] = useState<SliderState>(DEFAULT_SLIDERS);
  const [microResults, setMicroResults] = useState<ScenarioResult[]>([]);
  const [macroResult, setMacroResult] = useState<MacroResult | null>(null);

  // Init: fetch assets → orchestrator.init() → setPhase('preselect')
  // Select scenario: orchestrator.simulate() → setMicroResults
  // Slider change: interpolation layer → setMicroResults → orchestrator.project() → setMacroResult
}
```

**Key difference:** The hook pattern is new (no existing React hooks in codebase). It patterns after:
- `orchestrator.ts` for the WorkerOrchestrator API surface (init, simulate, project, terminate)
- React 19 `useTransition` pattern from RESEARCH.md Pitfall 3: `startTransition` wraps `setIsComputing(true)`, worker results arrive outside the transition

---

### `webapp/src/hooks/useSliderWithUrl.ts` (hook, event-driven)

**Analog:** RESEARCH.md Pattern 2 (React Aria `useSlider`) + `webapp/src/state/url-codec.ts` (URL sync)

**File banner:**
```typescript
// webapp/src/hooks/useSliderWithUrl.ts
//
// Combines React Aria useSlider with URL state synchronization.
// Each slider draghook updates: (1) display value instantly,
// (2) URL search param via pushState (dragEnd), (3) calls onChange
// for interpolation/macro computation (throttled, 50ms).
//
// D-15: Throttled drag with instant computation on release.
// D-23: URL state encoding on drag-end.
```

**Imports pattern:**
```typescript
import { useRef, useState, useTransition, useCallback, useMemo } from 'react';
import { useSlider, useSliderThumb } from 'react-aria';
import { useSliderState } from 'react-stately';
import { pushState } from '../state/url-codec';
```

**Core pattern** — wraps React Aria hooks (from RESEARCH.md Code Example, lines 579-673):
```typescript
export function useSliderWithUrl({
  label, leverKey, minValue, maxValue, step, defaultValue = 0,
  disabled, onValueChange, onDragEnd,
}: FiscalSliderProps) {
  const trackRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [isPending, startTransition] = useTransition();

  const formatter = useMemo(
    () => new Intl.NumberFormat('fr-FR', {
      style: 'percent', signDisplay: 'always', maximumFractionDigits: 0,
    }),
    []
  );

  const state = useSliderState({
    value: [defaultValue],
    minValue, maxValue, step,
    onChange: ([v]) => onValueChange(leverKey, v),
    onChangeEnd: ([v]) => {
      startTransition(() => onDragEnd(leverKey, v));
    },
    label,
    numberFormatter: formatter,
    isDisabled: disabled,
  });

  // ... aria hooks, return props
}
```

---

### `webapp/src/hooks/useServiceWorker.ts` (hook, event-driven)

**Analog:** None in codebase. Pattern from standard React SW registration pattern:

```typescript
// webapp/src/hooks/useServiceWorker.ts
//
// Registers the Workbox service worker and manages update lifecycle.
// Strategy: cache-first for data assets (scenario JSON, shock matrix),
// network-first for app shell (HTML/JS/CSS). D-31.

export function useServiceWorker(): { isReady: boolean; hasUpdate: boolean } {
  const [isReady, setIsReady] = useState(false);
  const [hasUpdate, setHasUpdate] = useState(false);

  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').then(registration => {
        registration.onupdatefound = () => {
          const installingWorker = registration.installing;
          if (installingWorker) {
            installingWorker.onstatechange = () => {
              if (installingWorker.state === 'installed') {
                setHasUpdate(true);
                setIsReady(true);
              }
            };
          }
        };
        if (!registration.installing) setIsReady(true);
      }).catch(err => {
        console.warn('Service Worker registration failed:', err);
        setIsReady(true); // proceed without SW
      });
    } else {
      setIsReady(true);
    }
  }, []);

  return { isReady, hasUpdate };
}
```

---

### `webapp/src/main.tsx` (entry, mount)

**Analog:** None in codebase. Standard Vite React 19 entry pattern:

```typescript
// webapp/src/main.tsx
//
// React 19 entry point — mounts <App /> into the DOM.
// Uses createRoot (React 18+ concurrent root) for useTransition support.

import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './App';
import './index.css';

const root = document.getElementById('root');
if (!root) throw new Error('Root element not found');

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
```

---

### `webapp/src/App.tsx` (component, request-response)

**Analog:** None in codebase. Patterns from RESEARCH.md architecture diagram (splash gate → simulator/error):

```typescript
// webapp/src/App.tsx
//
// Top-level application component.
// State machine: LOADING → PRESELECT → SCENARIO_DISPLAYING → ERROR (RESEARCH.md)
//
// D-27: Branded splash screen on initial load.
// D-30: Full-screen error state on fetch failure.

import { useSimulation } from './hooks/useSimulation';
import { SplashScreen } from './components/SplashScreen';
import { ErrorScreen } from './components/ErrorScreen';
import { SimulatorPage } from './pages/SimulatorPage';

export function App() {
  const simulation = useSimulation();

  switch (simulation.phase) {
    case 'loading':
      return <SplashScreen progress={simulation.loadProgress} />;
    case 'error':
      return <ErrorScreen message={simulation.errorMessage} onRetry={simulation.retry} />;
    case 'preselect':
    case 'displaying':
      return <SimulatorPage simulation={simulation} />;
  }
}
```

---

### `webapp/src/components/ScenarioGrid.tsx` (component, request-response)

**Analog:** None (first grid component). Pattern from RESEARCH.md architecture (D-01, D-28):

```typescript
// webapp/src/components/ScenarioGrid.tsx
//
// Displays 9-12 scenario cards in a responsive grid.
// D-01: Scenario selector showing pre-computed candidate scenarios.
// D-28: Empty state with prompt "Choisissez un scénario pour commencer."

import type { ScenarioDefinition } from '../engine/types';
import { ScenarioCard } from './ScenarioCard';

interface ScenarioGridProps {
  scenarios: ScenarioDefinition[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function ScenarioGrid({ scenarios, selectedId, onSelect }: ScenarioGridProps) {
  return (
    <section aria-label="Scénarios disponibles">
      <h2 className="text-lg font-semibold mb-4">Choisissez un scénario pour commencer</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {scenarios.map(scenario => (
          <ScenarioCard
            key={scenario.id}
            scenario={scenario}
            isSelected={scenario.id === selectedId}
            onSelect={() => onSelect(scenario.id)}
          />
        ))}
      </div>
    </section>
  );
}
```

---

### `webapp/src/components/LeverSlider.tsx` (component, request-response)

**Analog:** RESEARCH.md "Full Slider Component" code example (lines 579-673)

**File banner:**
```typescript
// webapp/src/components/LeverSlider.tsx
//
// Single fiscal lever slider using React Aria.
// D-08: 5 aggregate citizen levers (IR, IS, TVA, cotisations, dépenses).
// D-10: Axis represents % change from baseline, centered at 0%.
// D-13: Baseline notch + "Actuel" label at center.
//
// A11Y-05: Full WAI-ARIA — aria-valuenow/min/max, keyboard navigation (Arrow,
// Page Up/Down, Home, End), touch support, hidden native input for screen readers.
```

**Imports** (from RESEARCH.md lines 564-567):
```typescript
import { useRef, useState, useTransition, useCallback, useMemo } from 'react';
import { useSlider, useSliderThumb } from 'react-aria';
import { useSliderState } from 'react-stately';
```

**Core markup** (from RESEARCH.md lines 619-673) — applies the RESEARCH.md code as the primary source, wrapped in a component. The exact `div` structure, baseline notch, "Actuel" label, thumb styling, and gradient track are all specified in the code example.

**Key patterns to copy:**
1. Track gradient: `background: linear-gradient(to right, #1E3A5F 0%, #1E3A5F ${pct}%, #CBD5E1 ${pct}%, #CBD5E1 100%)`
2. Thumb size: 44×44px (RGAA touch target)
3. Baseline notch at 0% position with `aria-hidden="true"`
4. "Actuel" label at 0% with `aria-hidden="true"`
5. Hidden native `<input {...inputProps} ref={inputRef} />` for touch screen readers

---

### `webapp/src/components/ChartCell.tsx` (component, request-response)

**Analog:** RESEARCH.md "ChartCell" code example (lines 700-726)

**File banner:**
```typescript
// webapp/src/components/ChartCell.tsx
//
// Renders a single Vega-Lite chart with accessibility affordances.
// D-16: Vega-Lite 6.4 for primary chart rendering, SVG output.
// D-19: Pattern-fill differentiation via SVG <pattern>.
//
// A11Y-01: role="img" + aria-labelledby on chart container.
// A11Y-02: Adjacent <table> fallback for screen readers (A11Y-02).
```

**Imports** (from RESEARCH.md):
```typescript
import { useRef, useEffect } from 'react';
import vegaEmbed from 'vega-embed';
import type { TopLevelSpec } from 'vega-lite';
import { ChartTableFallback } from './ChartTableFallback';
```

**Core pattern** (from RESEARCH.md lines 701-726):
- `useEffect` with dependency array `[data, spec, title, patternId]`
- `vegaEmbed(containerRef.current, specWithData, { actions: false, renderer: 'svg', patch: ... })`
- Container gets `role="img"` and `aria-labelledby` pointing to a `<figcaption>`
- Fallback `<ChartTableFallback>` always rendered in the DOM

---

### `webapp/src/components/ChartTableFallback.tsx` (component, request-response)

**Analog:** RESEARCH.md "ChartTableFallback" code example (lines 744-763)

**Complete pattern** — simple pure component:
```typescript
// webapp/src/components/ChartTableFallback.tsx
//
// HTML <table> with <th scope> for screen reader access to chart data.
// A11Y-02: Every chart must have an adjacent data table.
//
// Uses sr-only for visual users, aria-label for screen readers.

interface ChartTableFallbackProps {
  title: string;
  data: Array<Record<string, unknown>>;
}

export function ChartTableFallback({ title, data }: ChartTableFallbackProps) {
  const columns = data.length > 0 ? Object.keys(data[0]) : [];
  return (
    <table className="sr-only" aria-label={`Données tabulaires: ${title}`}>
      <caption>{title}</caption>
      <thead><tr>{columns.map(col => <th key={col} scope="col">{col}</th>)}</tr></thead>
      <tbody>
        {data.map((row, i) => (
          <tr key={i}>{columns.map(col => <td key={col}>{String(row[col])}</td>)}</tr>
        ))}
      </tbody>
    </table>
  );
}
```

---

### `webapp/src/charts/spec-deficit.ts` (config, static)

**Analog:** RESEARCH.md Pattern 4 (Vega-Lite spec example, lines 396-421)

**Pattern** — exports a `TopLevelSpec` object (not a function):
```typescript
// webapp/src/charts/spec-deficit.ts
//
// Vega-Lite 6.4 specification for Déficit Public chart.
// D-18: Line chart with semi-transparent area fill.
// D-19: Pattern fill via url(#pattern-deficit).

import type { TopLevelSpec } from 'vega-lite';
import { sharedConfig } from './config';

export const deficitSpec: TopLevelSpec = {
  $schema: 'https://vega.github.io/schema/vega-lite/v6.json',
  description: 'Projection du déficit public sur 5 ans en pourcentage du PIB',
  width: 'container',
  height: 250,
  data: { values: [] },
  mark: {
    type: 'area',
    fill: 'url(#pattern-deficit)',
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
  config: sharedConfig,
};
```

**Key pattern:** All 4 chart specs (`spec-deficit.ts`, `spec-debt.ts`, `spec-gdp.ts`, `spec-employment.ts`) follow the same structure — import `sharedConfig`, export a `TopLevelSpec` with `data: { values: [] }` (populated at render time).

---

### `webapp/src/charts/patterns.ts` (utility, static)

**Analog:** RESEARCH.md "patterns.ts" code example (lines 683-698)

**Pattern** — exports an SVG string with `<defs>` containing 4 `<pattern>` elements:
```typescript
// webapp/src/charts/patterns.ts
//
// Shared SVG <pattern> definitions for chart accessibility (A11Y-03).
// Each of the 4 macro series gets a distinct pattern + distinct color
// from a deuteranopia-safe palette.
//
// D-19: Never color alone — always combine pattern + color.

export const CHART_PATTERNS_SVG = `
<defs>
  <pattern id="pattern-deficit" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
    <line x1="0" y1="0" x2="0" y2="8" stroke="#0072B2" stroke-width="1.5" opacity="0.5"/>
  </pattern>
  <!-- ... 3 more patterns ... -->
</defs>`;
```

**Key difference:** These patterns are injected into Vega-Lite charts via the `patch` option in `vega-embed`. The `url(#pattern-*)` references in chart specs resolve to these `<defs>`.

---

### `webapp/src/charts/config.ts` (config, static)

**Analog:** None in codebase. Standard Vega-Lite shared config pattern:

```typescript
// webapp/src/charts/config.ts
//
// Shared Vega-Lite configuration for all macro charts.
// Defines color palette, font, responsive behavior, and ARIA settings.

import type { Config } from 'vega-lite';

export const sharedConfig: Config = {
  aria: true,
  background: 'transparent',
  font: 'Inter, system-ui, sans-serif',
  axis: {
    labelFontSize: 12,
    titleFontSize: 13,
    gridColor: '#E5E7EB',
    domainColor: '#9CA3AF',
  },
  view: {
    stroke: 'transparent',
  },
  legend: {
    orient: 'bottom',
    labelFontSize: 12,
  },
  // Deuteranopia-safe palette (D-19)
  range: {
    category: ['#0072B2', '#E69F00', '#009E73', '#CC79A7'],
  },
};
```

---

### `webapp/src/pages/SimulatorPage.tsx` (component, request-response)

**Analog:** None (first page component). Pattern from RESEARCH.md architecture:

```typescript
// webapp/src/pages/SimulatorPage.tsx
//
// Main simulator layout (split panel).
// D-22: Desktop — left panel (scenario + sliders, fixed ~380px), right panel (results).
// D-24: Mobile — vertical stack with accordion panels.

import { ScenarioGrid } from '../components/ScenarioGrid';
import { SliderGroup } from '../components/SliderGroup';
import { AdvancedToggle } from '../components/AdvancedToggle';
import { ImpactDisplay } from '../components/ImpactDisplay';
import { ChartGrid } from '../components/ChartGrid';
import { Footer } from '../components/Footer';

interface SimulatorPageProps { /* ... */ }

export function SimulatorPage(props: SimulatorPageProps) {
  return (
    <div className="flex flex-col lg:flex-row min-h-screen">
      {/* Left panel: scenarios + sliders */}
      <aside className="lg:w-[380px] lg:shrink-0 p-6 bg-white border-r overflow-y-auto">
        <ScenarioGrid ... />
        <SliderGroup ... />
        <AdvancedToggle ... />
      </aside>
      {/* Right panel: results */}
      <main className="flex-1 p-6 overflow-y-auto">
        <ImpactDisplay ... />
        <ChartGrid ... />
      </main>
      <Footer />
    </div>
  );
}
```

---

### `webapp/src/pages/MethodologyPage.tsx` (component, request-response)

**Analog:** None (first static page). Pattern from RESEARCH.md (D-25):

```typescript
// webapp/src/pages/MethodologyPage.tsx
//
// Static methodology page (D-25).
// Contains: data source attribution, interpolation explanation,
// synthetic data disclaimer, project contact.
// Niveau lycée (16-18 ans) reading level (D-26).

import { Footer } from '../components/Footer';

export function MethodologyPage() {
  return (
    <div className="max-w-prose mx-auto py-12 px-6">
      <h1 className="text-3xl font-bold mb-8">Méthodologie</h1>
      {/* Static content sections */}
      <Footer />
    </div>
  );
}
```

---

### `webapp/src/services/payment.ts` (service, CRUD)
> **Not applicable** — no payment service in Phase 3 scope.

---

## Test File Pattern Assignments

### `webapp/src/state/__tests__/url-codec.test.ts` (test, unit)

**Analog:** `webapp/src/engine/__tests__/scenario-cache.test.ts`

**Imports** (lines 1-8):
```typescript
// webapp/src/state/__tests__/url-codec.test.ts
//
// Unit tests for URL state encoding/decoding (D-23).

import { describe, it, expect } from 'vitest';
import { encodeState, decodeState, pushState } from '../url-codec';
import type { URLState } from '../types';
```

**Test structure** (from scenario-cache.test.ts):
```typescript
describe('encodeState', () => {
  it('encodes basic state to base64', () => {
    const state: URLState = { s: 'baseline', p: { ir: 15, is: 0, tva: -5, cotisations: 0, depenses: 0 }, f: 1, a: false };
    const encoded = encodeState(state);
    expect(typeof encoded).toBe('string');
    expect(() => atob(encoded)).not.toThrow();
  });
  // ... round-trip tests, edge cases (unicode, special chars)
});

describe('decodeState', () => {
  it('returns null for invalid base64', () => {
    expect(decodeState('!!!not-valid!!!')).toBeNull();
  });

  it('returns null for missing required fields', () => {
    const encoded = btoa(JSON.stringify({ s: 'baseline' })); // missing f, a
    expect(decodeState(encoded)).toBeNull();
  });

  it('round-trips full state', () => {
    const original: URLState = { s: 'reform-tva', p: { ir: 10, is: -5, tva: 22, cotisations: -3, depenses: 5 }, f: 2, a: true };
    const encoded = encodeState(original);
    const decoded = decodeState(encoded);
    expect(decoded).toEqual(original);
  });
});
```

**Key testing conventions** (from existing tests):
1. Test file banner comment with path and purpose
2. Import only `describe`, `it`, `expect` from vitest (never `test` — use `it`)
3. Test fixtures as helper functions when complex
4. `describe` blocks match function/module names
5. Assertions on both success and failure/edge cases
6. No `beforeEach` unless state reset is needed

---

### `webapp/src/state/__tests__/interpolation.test.ts` (test, unit)

**Analog:** `webapp/src/engine/__tests__/macro-interpolate.test.ts`

**Imports** (lines 1-19):
```typescript
// webapp/src/state/__tests__/interpolation.test.ts
//
// Unit tests for scenario-to-scenario interpolation.

import { describe, it, expect } from 'vitest';
import { interpolateScenarios } from '../interpolation';
import { ScenarioCache } from '../../engine/scenario-cache';
import type { ScenarioDefinition, ScenarioResult } from '../../engine/types';
import type { SliderState } from '../types';
```

**Test fixture pattern** (from macro-interpolate.test.ts lines 31-54 — helper builds test data):
```typescript
function makeTestCache(): { cache: ScenarioCache; defs: ScenarioDefinition[] } {
  // Build a ScenarioCache with 3 synthetic scenarios for testing
  const cache = new ScenarioCache();
  // ... add scenario docs
  return { cache, defs };
}
```

**Core test patterns** (from macro-interpolate.test.ts):
```typescript
describe('interpolateScenarios', () => {
  it('returns exact match when slider matches a scenario (distance ≈ 0)', () => {
    // ...
  });

  it('returns weighted blend for between-scenario slider position', () => {
    // Using .toBeCloseTo() for floating-point weight sums
    expect(result.weights.reduce((a, b) => a + b, 0)).toBeCloseTo(1.0, 10);
  });

  it('returns null for empty scenario list', () => {
    expect(interpolateScenarios(/*...*/, [], cache, 0)).toBeNull();
  });
});
```

**Key difference:** The interpolation tests need a populated `ScenarioCache`. The test fixture `makeTestCache()` adds 3-5 `ScenarioDoc` entries with known parameter values for deterministic interpolation testing.

---

### `webapp/src/state/__tests__/index-map.test.ts` (test, unit)

**Analog:** `webapp/src/engine/__tests__/scenario-cache.test.ts`

```typescript
// webapp/src/state/__tests__/index-map.test.ts
//
// Unit tests for lever-to-parameter mappings.

import { describe, it, expect } from 'vitest';
import { LEVER_MAPPINGS, type LeverMapping } from '../index-map';

describe('LEVER_MAPPINGS', () => {
  it('contains all 5 citizen levers', () => {
    expect(Object.keys(LEVER_MAPPINGS)).toHaveLength(5);
    expect(LEVER_MAPPINGS).toHaveProperty('ir');
    expect(LEVER_MAPPINGS).toHaveProperty('is');
    expect(LEVER_MAPPINGS).toHaveProperty('tva');
    expect(LEVER_MAPPINGS).toHaveProperty('cotisations');
    expect(LEVER_MAPPINGS).toHaveProperty('depenses');
  });

  it('each lever has weights that sum to 1.0', () => {
    for (const lever of Object.values(LEVER_MAPPINGS)) {
      const sum = lever.weights.reduce((a, b) => a + b, 0);
      expect(sum).toBeCloseTo(1.0, 10);
    }
  });

  it('each lever has matching subParams and weights length', () => {
    for (const lever of Object.values(LEVER_MAPPINGS)) {
      expect(lever.subParams).toHaveLength(lever.weights.length);
    }
  });
});
```

---

### `webapp/src/__tests__/components/LeverSlider.test.tsx` (test, component)

**Analog:** None in codebase (first React component test). Standard Vitest + @testing-library/react pattern:

```typescript
// webapp/src/__tests__/components/LeverSlider.test.tsx
//
// Component tests for the LeverSlider (React Aria slider with ARIA assertions).

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LeverSlider } from '../../components/LeverSlider';

describe('LeverSlider', () => {
  it('renders with correct ARIA attributes', () => {
    render(<LeverSlider label="IR ménages" minValue={-30} maxValue={30} step={1} onValueChange={() => {}} onDragEnd={() => {}} />);
    const slider = screen.getByRole('slider');
    expect(slider).toHaveAttribute('aria-valuemin', '-30');
    expect(slider).toHaveAttribute('aria-valuemax', '30');
    expect(slider).toHaveAttribute('aria-valuenow', '0');
  });

  it('displays "Actuel" label at baseline', () => {
    render(/* ... */);
    expect(screen.getByText('Actuel')).toBeInTheDocument();
  });

  it('calls onChange with keyboard navigation', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(/* ... */);
    const slider = screen.getByRole('slider');
    slider.focus();
    await user.keyboard('{ArrowRight}');
    expect(onChange).toHaveBeenCalledWith(1);
  });
});
```

---

### `webapp/src/__tests__/simulator.spec.ts` (test, e2e)

**Analog:** None in codebase. Standard Playwright E2E pattern:

```typescript
// webapp/src/__tests__/simulator.spec.ts
//
// E2E tests for the full simulator user flow (Playwright).
// Covers: UI-01 through UI-08 (all user-facing requirements).

import { test, expect } from '@playwright/test';

test.describe('Simulator E2E', () => {
  test('loads splash screen then transitions to preselect', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Chargement du simulateur')).toBeVisible();
    // Wait for splash transition...
    await expect(page.getByText('Choisissez un scénario')).toBeVisible();
  });

  test('selects scenario and displays household impact', async ({ page }) => {
    // ...
  });

  test('slider drag updates impact and charts', async ({ page }) => {
    // ...
  });

  test('reset button clears selection and returns to empty state', async ({ page }) => {
    // ...
  });

  test('URL sharing encodes and restores full state', async ({ page }) => {
    // ...
  });
});
```

---

### `webapp/src/__tests__/a11y.spec.ts` (test, e2e)

**Analog:** None in codebase. Playwright + @axe-core/playwright pattern:

```typescript
// webapp/src/__tests__/a11y.spec.ts
//
// Accessibility audit tests using axe-core (A11Y-06).
// Tests all states: LOADING, PRESELECT, SCENARIO_DISPLAYING, ERROR.

import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Accessibility Audit', () => {
  test('preselect state has no a11y violations', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Choisissez un scénario')).toBeVisible();
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toEqual([]);
  });

  test('sliders have full ARIA attributes', async ({ page }) => {
    // A11Y-05
  });

  test('charts have role="img" and aria-labelledby', async ({ page }) => {
    // A11Y-01
  });

  test('chart tables have <th scope>', async ({ page }) => {
    // A11Y-02
  });

  test('pattern fills and deuteranopia-safe colors', async ({ page }) => {
    // A11Y-03
  });
});
```

---

## Shared Patterns

### TypeScript File Banner Convention
**Source:** All Phase 2 engine/worker files
**Apply to:** All new `.ts` and `.tsx` files

Each file starts with a 3-line banner comment:
```typescript
// webapp/src/<path>/<filename>.ts
//
// <One-line purpose description.>
// <Additional context line — references CONTEXT.md decisions.>
```

### Section Divider Comments
**Source:** `webapp/src/engine/types.ts` (line 11), `webapp/src/workers/orchestrator.ts` (line 28)
**Apply to:** Longer files (>50 lines) with multiple sections

```typescript
// ── Section Name ─────────────────────────────────────────────────────────
```
Using em-dash characters padded to 70 columns.

### Import Convention — `type` keyword + Path Aliases
**Source:** `webapp/src/engine/scenario-cache.ts` (line 14), `webapp/src/workers/orchestrator.ts` (lines 20-26)
**Apply to:** All TypeScript files

```typescript
import type { ScenarioDefinition, ScenarioResult } from './types';
// OR for runtime imports:
import { ScenarioCache, type ScenarioDoc } from '../engine/scenario-cache';
```

Key rules:
1. Use `import type` for type-only imports
2. Relative paths with `../` for cross-directory imports
3. No barrel files or index re-exports (direct path to source file)
4. No path aliases (`@/`) — use `../` relative paths

### Null-Return Error Handling
**Source:** `webapp/src/engine/macro-interpolate.ts` (lines 117-119, 128-130)
**Apply to:** All pure computation modules (state/ files, engine/ files)

```typescript
if (!isFinite(tax)) return null;
if (!isInsideHull(...)) return null;
```
Pure functions return `null` for invalid inputs — never throw. This matches the existing engine pattern.

### try/catch in Message Handlers
**Source:** `webapp/src/workers/citizen-worker.ts` (lines 91-98), `webapp/src/workers/macro-worker.ts` (lines 178-184)
**Apply to:** Worker message handlers, React event handlers with FFI risk

```typescript
} catch (err) {
  const response: WorkerResponse = {
    id,
    type: 'ERROR',
    payload: err instanceof Error ? err.message : String(err),
  };
  self.postMessage(response);
}
```

### Vitest Test Structure
**Source:** `webapp/src/engine/__tests__/scenario-cache.test.ts`, `webapp/src/engine/__tests__/macro-interpolate.test.ts`
**Apply to:** All unit tests in `webapp/src/*/__tests__/`

```typescript
import { describe, it, expect } from 'vitest';

describe('ModuleName', () => {
  describe('functionName()', () => {
    it('does something specific', () => {
      expect(actual).toBe(expected);
    });
  });
});
```

Conventions:
1. `describe` outer = module name, inner = function name
2. `it` for test cases (never `test`)
3. `.toBeCloseTo(number, 10)` for floating-point comparisons
4. `expect(result).toBeNull()` for null returns
5. `expect(result!).toBeDefined()` for non-null assertions
6. Test fixtures as module-level `function makeTestXxx()` helpers
7. `beforeEach` for shared state reset (only when needed)
8. At least 3 test cases per function: happy path, edge case, null/invalid

### Worker Message Protocol (Correlation IDs)
**Source:** `webapp/src/workers/orchestrator.ts` (lines 166-178)
**Apply to:** Any new worker message types added in Phase 3 (e.g., INTERPOLATE variant)

```typescript
const id = crypto.randomUUID();
this.latestCitizenId = id;
return new Promise((resolve, reject) => {
  this.pending.set(id, { resolve, reject, timestamp: Date.now() });
  this.citizenWorker.postMessage({
    id, type: 'SIMULATE', payload: { scenarioId, profileIndex },
  } satisfies WorkerRequest);
});
```

### React Component File Structure
**Source:** RESEARCH.md code examples (all components)
**Apply to:** All `src/components/*.tsx` and `src/pages/*.tsx`

```typescript
// webapp/src/components/ComponentName.tsx
//
// <Purpose — references CONTEXT.md decisions.>

import { /* React hooks */ } from 'react';
import { /* components */ } from './SiblingComponent';
import type { /* props */ } from '../engine/types';

interface ComponentNameProps {
  // Props with JSDoc if non-obvious
}

export function ComponentName({ ... }: ComponentNameProps) {
  return (
    <section aria-label="...">
      {/* JSX */}
    </section>
  );
}
```

### ARIA / Accessibility Conventions
**Source:** RESEARCH.md (D-16, D-19, A11Y-01 through A11Y-06)
**Apply to:** All interactive components

1. Every SVG chart container gets `role="img"` + `aria-labelledby`
2. Every chart has an adjacent `<table className="sr-only">` with `<th scope>`
3. Every slider has `aria-valuenow`, `aria-valuemin`, `aria-valuemax`
4. Touch targets ≥ 44px (Tailwind utility or inline style)
5. Hidden native `<input>` inside slider for touch screen readers
6. French `aria-label` values (Budget Citoyen is a French app)

### French Copy/Language Convention
**Source:** CONTEXT.md D-26
**Apply to:** All user-facing text in components

1. Niveau lycée (16-18 ans) reading level
2. Short sentences, active voice
3. Direct address: "vous", "votre"
4. Economic terms with inline `aria-label` definitions (no intrusive popovers)
5. French text content in JSX — no i18n library for this phase

### Tailwind CSS 4.3 — `@theme` Directive
**Source:** RESEARCH.md Standard Stack
**Apply to:** `webapp/src/index.css`

```css
/* webapp/src/index.css */
@import "tailwindcss";

@theme {
  --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
  --color-primary: #1E3A5F;
  --color-secondary: #2563EB;
  --color-accent: #0072B2;
  /* ... */
}
```

---

## No Analog Found

Files with no close match in the codebase (planner should use RESEARCH.md patterns or standard tool configurations):

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `webapp/package.json` | config | build-tool | No existing `package.json` — first frontend dependency manifest |
| `webapp/tsconfig.json` | config | build-tool | No existing TS config — use Vite's `tsconfig.app.json` conventions |
| `webapp/vite.config.ts` | config | build-tool | No existing Vite config — use standard React + Tailwind plugin setup |
| `webapp/index.html` | entry | static | No existing HTML template — standard Vite entry with `<div id="root">` |
| `webapp/sw.js` | utility | event-driven | No existing Service Worker — Workbox manual setup with CacheFirst/NetworkFirst |
| `webapp/workbox-config.js` | config | build-tool | No existing Workbox config |
| `webapp/src/main.tsx` | entry | mount | No React entry file exists — standard `createRoot(document.getElementById('root')).render(<App />)` |
| `webapp/src/App.tsx` | component | request-response | No React components exist — state machine from RESEARCH.md architecture |
| `webapp/src/index.css` | config | static | No Tailwind config exists — use `@theme` directive (Tailwind 4) |
| `webapp/src/hooks/useServiceWorker.ts` | hook | event-driven | No React hooks exist — standard SW registration pattern |
| `webapp/src/components/SplashScreen.tsx` | component | request-response | No UI components exist — pattern from RESEARCH.md (D-27) |
| `webapp/src/components/ScenarioGrid.tsx` | component | request-response | No grid components exist — RESPONSIVE card grid |
| `webapp/src/components/ScenarioCard.tsx` | component | request-response | No card components exist — simple card with selection state |
| `webapp/src/components/SliderGroup.tsx` | component | request-response | No collapsible sections exist — collapsible accordion (D-09) |
| `webapp/src/components/AdvancedToggle.tsx` | component | request-response | No toggle components exist — simple toggle button |
| `webapp/src/components/ImpactDisplay.tsx` | component | request-response | No profile displays exist — 3 household profile cards (D-06) |
| `webapp/src/components/ImpactPill.tsx` | component | request-response | No pill components exist — single profile pill |
| `webapp/src/components/ChartGrid.tsx` | component | request-response | No chart grids exist — 2×2 responsive grid (D-17) |
| `webapp/src/components/Footer.tsx` | component | request-response | No footer components exist — persistent footer with link |
| `webapp/src/components/ErrorScreen.tsx` | component | request-response | No error screens exist — full-screen error (D-30) |
| `webapp/src/charts/config.ts` | config | static | No Vega-Lite config exists — shared theme/ARIA config |
| `webapp/src/pages/SimulatorPage.tsx` | component | request-response | No page components exist — split panel layout (D-22) |
| `webapp/src/pages/MethodologyPage.tsx` | component | request-response | No static pages exist — prose layout |
| `vitest.config.ts` | config | test | No Vitest config exists — standard Vite-native vitest setup |
| `playwright.config.ts` | config | test | No Playwright config exists — standard multi-browser Playwright setup |
| `webapp/src/__tests__/simulator.spec.ts` | test | e2e | No Playwright E2E tests exist — full user flow |
| `webapp/src/__tests__/a11y.spec.ts` | test | e2e | No Playwright a11y tests exist — axe-core assertions |
| `webapp/src/__tests__/components/LeverSlider.test.tsx` | test | component | No React component tests exist — @testing-library/react + vitest |

**For these files, the planner should reference:**
1. **RESEARCH.md code examples** for component structure, Tailwind classes, ARIA patterns
2. **Standard tool configurations** for build tool files (Vite, TypeScript, Vitest, Playwright docs)
3. **Shared patterns above** for file banners, import conventions, error handling

---

## Metadata

**Analog search scope:**
- `webapp/src/engine/` — Phase 2 engine files (4 files)
- `webapp/src/workers/` — Phase 2 worker files (3 files)
- `webapp/src/engine/__tests__/` — Phase 2 test files (2 files)

**Files scanned:** 9 existing source files + 2 existing test files
**Pattern extraction date:** 2026-05-13

### Coverage Summary
- Files with exact analog: 7 (types.ts, url-codec.test.ts, interpolation.test.ts, index-map.test.ts, interpolation.ts, macro-interpolate test patterns)
- Files with partial analog (Phase 2 pattern + RESEARCH.md): 6 (url-codec.ts, index-map.ts, useSimulation, useSliderWithUrl, LeverSlider, ChartCell, ChartTableFallback, 4 chart specs, patterns.ts)
- Files with only RESEARCH.md reference: 5 (ScenarioGrid, ChartGrid, splash/config/entry scaffolding)
- Files with no analog (standard tool configs): 25 (package.json, tsconfig.json, vite.config.ts, index.html, sw.js, workbox-config.js, main.tsx, App.tsx, index.css, useServiceWorker, SplashScreen, ScenarioCard, SliderGroup, AdvancedToggle, ImpactDisplay, ImpactPill, Footer, ErrorScreen, config.ts, SimulatorPage, MethodologyPage, vitest.config.ts, playwright.config.ts, simulator.spec.ts, a11y.spec.ts, LeverSlider.test.tsx)

### Key Patterns Identified
- **TypeScript file banner:** 3-line comment with path, purpose, and decision reference — used in all Phase 2 files
- **Section dividers:** `─ Section Name ─` padded to 70 columns — used in longer engine/worker files
- **Import convention:** `import type` for types, relative paths, no barrel files
- **Null-return error handling:** Pure functions return `null` for invalid inputs, never throw
- **Vitest test structure:** `describe`/`it` with `.toBeCloseTo(10)` for floats and `expect(result).toBeNull()`
- **React Aria slider:** `useSlider` + `useSliderState` + hidden native `<input>` for touch SR
- **Vega-Lite 6.4 charts:** `export const spec: TopLevelSpec` with `data: { values: [] }`, SVG rendering, `patch` for patterns
