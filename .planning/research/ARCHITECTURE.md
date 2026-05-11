# Architecture Research

**Domain:** Hybrid Civic Budget Simulation Platform (Simulateur Budgétaire Citoyen)
**Researched:** 2026-05-11
**Confidence:** HIGH

## Standard Architecture

### System Overview

The platform follows a **Privacy-Preserving Edge-Compute Architecture** with three execution tiers: pure client-side computation (WASM microsimulation), lightweight server-side static serving (pre-computed shock matrices and synthetic data), and zero-knowledge interaction (no user data ever reaches the server).

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                           APPLICATION SHELL (Browser)                                 │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                          UI LAYER (React + TypeScript)                         │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌──────────────────────────┐  │   │
│  │  │  Citoyen   │  │   Expert   │  │ Chercheur  │  │ Accessibility Overlay    │  │   │
│  │  │   Mode     │  │    Mode    │  │    Mode    │  │ (RGAA 4 Compliance)      │  │   │
│  │  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └──────────────────────────┘  │   │
│  │        └───────────────┼───────────────┘                                      │   │
│  │                        ▼                                                       │   │
│  │  ┌──────────────────────────────────────────────────────────────────────────┐  │   │
│  │  │                    SIMULATION ORCHESTRATOR (State Manager)                  │  │   │
│  │  │  ┌─────────────────────┐  ┌─────────────────────┐  ┌────────────────────┐  │   │
│  │  │  │   Slider Controller  │  │   Scenario Manager   │  │ Chart Renderer     │  │   │
│  │  │  │  (debounced <200ms)  │  │   (JSON/Patch Ops)   │  │ (D3.js + Matrices) │  │   │
│  │  │  └─────────┬───────────┘  └─────────┬───────────┘  └────────┬───────────┘  │   │
│  │  └────────────┼───────────────────────┼───────────────────────┼──────────────┘  │   │
│  └───────────────┼───────────────────────┼───────────────────────┼─────────────────┘  │
│                  │                       │                       │                     │
│  ┌───────────────┼───────────────────────┼───────────────────────┼─────────────────┐  │
│  │               ▼                       ▼                       ▼                  │  │
│  │                         COMPUTE LAYER (Web Workers)                              │  │
│  │  ┌──────────────────────────────┐  ┌──────────────────────────────────────────┐ │  │
│  │  │  Micro Engine Worker          │  │  Macro Engine Worker                     │ │  │
│  │  │  (Rust → WASM + Rayon)       │  │  (Rust → WASM + ndarray)                 │ │  │
│  │  │                              │  │                                          │ │  │
│  │  │  • TaxBenefitSystem          │  │  • Shock Matrix Fetch (from server)       │ │  │
│  │  │  • Entity/Parameter/Variable │  │  • Multi-linear Interpolation             │ │  │
│  │  │  • Reform application        │  │  • Trajectory projection (N periods)      │ │  │
│  │  │  • 50 000 profiles batched   │  │  • Results cache (MemoMap)                │ │  │
│  │  │  • Differential privacy      │  │                                          │ │  │
│  │  └──────────────┬───────────────┘  └────────────────┬─────────────────────────┘ │  │
│  │                 │                                  │                            │  │
│  └─────────────────┼──────────────────────────────────┼────────────────────────────┘  │
│                    │                                  │                                │
├────────────────────┼──────────────────────────────────┼────────────────────────────────┤
│                    │ SERVER BOUNDARY                   │                                │
│  ┌─────────────────┼──────────────────────────────────┼────────────────────────────┐  │
│  │                 ▼                                  ▼                             │  │
│  │                         STATIC DATA LAYER (CDN / Edge)                           │  │
│  │  ┌──────────────────────────────────┐  ┌──────────────────────────────────────┐ │  │
│  │  │  Shock Matrix Bundle              │  │  Synthetic Population Snapshot        │ │  │
│  │  │  (JSON/Parquet, 1-5 MB)          │  │  (JSON/Parquet, 5-20 MB)              │ │  │
│  │  │  • Multi-dim grid: [tax param]   │  │  • 50 000 profiles (ε=1.0)            │ │  │
│  │  │    × [spend param] × [horizon]   │  │  • Copula-generated correlations       │ │  │
│  │  │  • Pre-signed ETags for cache    │  │  • Versioned + hash-verified            │ │  │
│  │  └──────────────────────────────────┘  └──────────────────────────────────────┘ │  │
│  │  ┌──────────────────────────────────┐  ┌──────────────────────────────────────┐ │  │
│  │  │  Tax Rules Bundle (YAML)          │  │  Expert API (REST, opt-in)            │ │  │
│  │  │  • OpenFisca-compatible params   │  │  • Export results as CSV/JSON          │ │  │
│  │  │  • Versioned legislation snapshots│  │  • Batch simulation endpoints          │ │  │
│  │  │  • Δ diff for rule changes        │  │  • Zero PII — aggregate only           │ │  │
│  │  └──────────────────────────────────┘  └──────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **Application Shell** | Routing, persona detection, layout, accessibility baseline, module lazy-loading | React 18+ with Suspense, React Router, Vite |
| **Simulation Orchestrator** | Central state management: slider values → dispatch to workers → fan-in results → update charts | Zustand or Jotai (lightweight, signal-based), debounced action queue |
| **Slider Controller** | Input normalization, debouncing (<200ms SLA), range clamping, aria-valuenow synchronization | Custom React hook wrapping `<input type="range">` with WAI-ARIA |
| **Scenario Manager** | Diff generation between baseline and reform, JSON Patch (RFC 6902) serialization, shareable URLs | Immer for immutable patches, LZ-String for shareable state compression |
| **Chart Renderer** | SVG-based accessible rendering with role="img", data table fallback, color-independent discrimination | D3.js v7 + customized aria labels, pattern fills via `<defs>` |
| **Micro Engine Worker** | Web Worker hosting Rust/WASM: loads TaxBenefitSystem, applies reform, computes N profiles via Rayon | wasm-pack compiled Rust, serde-wasm-bindgen for zero-copy data transfer |
| **Macro Engine Worker** | Web Worker for shock matrix interpolation: fetches matrix chunks from CDN, performs multi-linear interpolation via ndarray | Rust ndarray + linfa or hand-rolled interpolation, results cached per Scenario hash |
| **Shock Matrix Bundle** | Pre-computed Mésange-derived look-up tables (3D grid: tax_param × spend_param × horizon) | Static JSON served via CDN, optional range-requestable Parquet for larger matrices |
| **Synthetic Population Snapshot** | 50 000 statistically representative profiles with differential privacy guarantee (ε ≤ 1.0) | Generated offline via Copula-GAN pipeline, served as immutable CDN asset |
| **Tax Rules Bundle** | OpenFisca-compatible YAML parameter tree with versioned legislation snapshots | Served as static YAML bundle, loaded by WASM engine at init |
| **Expert API** | Optional REST endpoints for batch simulation and result export (researcher persona) | Lightweight Node.js/Bun edge function, stateless, aggregate-only |

## Recommended Project Structure

```
budget-citoyen/
├── packages/
│   ├── wasm-microengine/       # Rust crate → WASM: microeconomic simulation engine
│   │   ├── src/
│   │   │   ├── lib.rs           # wasm-bindgen entry point, exports
│   │   │   ├── system.rs        # TaxBenefitSystem port (Entity, Variable, Parameter)
│   │   │   ├── simulation.rs    # Simulation runner, Reform application logic
│   │   │   ├── formula.rs       # Formula evaluator (ported from OpenFisca)
│   │   │   ├── privacy.rs       # Differential privacy noise injection (ε-budget)
│   │   │   └── data.rs          # Synthetic profile loader, batch operations
│   │   ├── tests/
│   │   ├── Cargo.toml
│   │   └── pkg/                 # Generated: WASM bindings + JS glue
│   │
│   ├── wasm-macroengine/       # Rust crate → WASM: macroeconomic shock interpolation
│   │   ├── src/
│   │   │   ├── lib.rs           # wasm-bindgen entry point
│   │   │   ├── matrix.rs        # Shock matrix loader, LUT indexing
│   │   │   ├── interpolate.rs   # Multi-linear interpolation (R^n → R^m)
│   │   │   ├── cache.rs         # Memoization: scenario hash → result
│   │   │   └── projection.rs    # Trajectory projection over N periods
│   │   ├── tests/
│   │   ├── Cargo.toml
│   │   └── pkg/
│   │
│   ├── data-pipeline/          # Offline: synthetic data generation + matrix pre-computation
│   │   ├── src/
│   │   │   ├── synthetic_pop/   # Copula-GAN/VAE for synthetic profile generation
│   │   │   ├── shock_matrix/    # Mésange bootstrap → multi-dimensional LUT generation
│   │   │   └── export/          # JSON/Parquet export to CDN with integrity hashes
│   │   ├── pyproject.toml
│   │   └── notebooks/
│   │
│   ├── webapp/                 # SPA: React + TypeScript + accessibility
│   │   ├── src/
│   │   │   ├── app/            # Routing, layout, persona switching
│   │   │   ├── features/
│   │   │   │   ├── simulation/  # Slider UI, scenario panel, worker orchestration
│   │   │   │   ├── charts/      # D3.js accessible chart components
│   │   │   │   ├── citizen/     # Simplified UX for "Citoyen Explorateur"
│   │   │   │   ├── expert/      # Advanced controls for "Expert Politique"
│   │   │   │   └── researcher/  # API client, batch export UI for "Chercheur"
│   │   │   ├── workers/         # Web Worker wrappers for WASM engines
│   │   │   ├── stores/          # Zustand state management
│   │   │   ├── a11y/            # RGAA 4 shared utilities (aria helpers, focus management)
│   │   │   └── shared/          # Types, constants, i18n
│   │   ├── public/
│   │   │   └── data/            # Static assets served by CDN (pop synced during build)
│   │   ├── package.json
│   │   └── vite.config.ts
│   │
│   ├── expert-api/             # Optional REST API for researcher persona
│   │   ├── src/
│   │   │   ├── routes/         # Batch simulation, export endpoints
│   │   │   └── middleware/     # CORS, rate limiting, no-PII validation
│   │   └── package.json
│   │
│   └── tax-rules/              # OpenFisca-compatible YAML rules (forked baseline)
│       ├── parameters/         # YAML parameter trees by tax domain
│       │   ├── ir/             # Impôt sur le Revenu
│       │   ├── is/             # Impôt sur les Sociétés
│       │   ├── tva/            # TVA
│       │   ├── cotisations/    # Cotisations sociales
│       │   └── aides/          # Aides sociales
│       ├── variables/          # Variable definitions (formula logic)
│       ├── reforms/            # Pre-built reform scenarios
│       └── package.json
│
├── .planning/                  # GSD planning artifacts
└── PROJECT.md
```

### Structure Rationale

- **`packages/wasm-microengine/`:** Rust crate compiled to WASM via wasm-pack. Independent build artifact, testable in isolation with wasm-bindgen-test. Must never depend on browser APIs directly — all JS interop through wasm-bindgen externs.
- **`packages/wasm-macroengine/`:** Separate WASM crate for interpolation. Separation from micro engine allows independent versioning, smaller individual .wasm payloads (~500 KB each vs 1 MB monolithic), and parallel Web Worker instantiation.
- **`packages/data-pipeline/`:** Offline Python pipeline. Not bundled in the SPA. Generates static data assets consumed at build time or fetched at runtime. Uses the same Copula-GAN + DP approaches documented in PRD research.
- **`packages/webapp/`:** Single SPA. Feature-organized (not layer-organized) to keep persona-specific code colocated. Worker wrappers are thin — they import WASM glue and manage message passing.
- **`packages/tax-rules/`:** Standalone package so legislation updates need not trigger full app rebuild. Rules bundled as static JSON derived from YAML at build time, loaded lazily by WASM engine on init.
- **`packages/expert-api/`:** Optional. Can be deployed as edge functions (Cloudflare Workers / Deno Deploy) or a lightweight Express/Fastify server. Stateless by design — all PII stays client-side.

## Architectural Patterns

### Pattern 1: WASM Web Worker Isolation (Double Worker Pattern)

**What:** Each computational engine (micro and macro) runs in its own dedicated Web Worker. The main UI thread never blocks. Workers communicate via `postMessage` with transferable objects.

**When to use:** Any CPU-bound computation exceeding 16ms (one frame budget at 60fps). Critical for the <200ms slider SLA.

**Trade-offs:** Adds complexity (~150 LOC per worker wrapper). Web Workers lack DOM access (acceptable — engines are pure computation). SharedArrayBuffer requires cross-origin isolation headers (COOP/COEP on the server).

**Example:**
```typescript
// webapp/src/workers/micro-worker.ts
import init, { MicroEngine, SimulationInput } from '@budget-citoyen/wasm-microengine';

let engine: MicroEngine;

self.onmessage = async (e: MessageEvent<{ type: string; payload: unknown }>) => {
  switch (e.data.type) {
    case 'INIT': {
      const { rulesBundle, populationSnapshot } = e.data.payload as InitPayload;
      await init(); // wasm-bindgen init
      engine = MicroEngine.new(rulesBundle, populationSnapshot);
      self.postMessage({ type: 'READY' });
      break;
    }
    case 'SIMULATE': {
      const input = e.data.payload as SimulationInput;
      const result = engine.simulate(input);
      // Transfer ArrayBuffer back to main thread (zero copy)
      self.postMessage({ type: 'RESULT', payload: result }, [result.buffer]);
      break;
    }
  }
};
```

```typescript
// webapp/src/features/simulation/hooks/useMicroWorker.ts
import { useEffect, useRef } from 'react';

export function useMicroWorker() {
  const workerRef = useRef<Worker>();

  useEffect(() => {
    workerRef.current = new Worker(
      new URL('../../workers/micro-worker.ts', import.meta.url),
      { type: 'module' }
    );
    return () => workerRef.current?.terminate();
  }, []);

  const simulate = (input: SimulationInput): Promise<SimulationResult> => {
    return new Promise((resolve) => {
      workerRef.current!.onmessage = (e) => resolve(e.data.payload);
      workerRef.current!.postMessage({ type: 'SIMULATE', payload: input });
    });
  };

  return { simulate };
}
```

### Pattern 2: Multi-Linear Interpolation over Pre-Computed Shock Matrix

**What:** Instead of solving macroeconomic equations in real time, a 3D look-up table (tax_change × spend_change × horizon_year) is pre-computed from Mésange bootstraps. The client interpolates between grid points using multi-linear interpolation.

**When to use:** Any system where the underlying model is too computationally expensive for real-time (<200ms) but has a bounded input space (sliders are constrained to reasonable ranges).

**Trade-offs:** Storage cost vs. computation cost. A 3D grid with 100×100×10 points (~100 000 entries) per output variable stored as Float32Array costs ~400 KB uncompressed. Interpolation error is negligible (< 1 bp) if the grid is dense enough at policy-relevant points. Grid generation is upfront cost (hours on HPC), never at runtime.

**Example:**
```rust
// wasm-macroengine/src/interpolate.rs
use ndarray::Array3;
use wasm_bindgen::prelude::*;

#[wasm_bindgen]
pub struct ShockMatrix {
    /// 3D grid: [tax_param_idx][spend_param_idx][horizon_year]
    /// Each cell contains [gdp_growth, employment, deficit, debt_to_gdp]
    grid: Array3<[f64; 4]>,
    tax_bp: Vec<f64>,    // Breakpoints for tax parameter axis
    spend_bp: Vec<f64>,  // Breakpoints for spend parameter axis
    horizon_bp: Vec<f64>,// Breakpoints for horizon axis
}

#[wasm_bindgen]
impl ShockMatrix {
    pub fn new(data: &[u8]) -> Self {
        // Deserialize from pre-computed grid (bincode or postcard format)
        // ...
    }

    /// Multi-linear interpolation: finds the 8 surrounding grid points
    /// and performs trilinear interpolation for each output variable.
    pub fn interpolate(&self, tax: f64, spend: f64, horizon: f64) -> Vec<f64> {
        let (i_low, i_high, frac_t) = self.find_bracket(&self.tax_bp, tax);
        let (j_low, j_high, frac_s) = self.find_bracket(&self.spend_bp, spend);
        let (k_low, k_high, frac_h) = self.find_bracket(&self.horizon_bp, horizon);

        // Trilinear interpolation weights
        let w000 = (1.0 - frac_t) * (1.0 - frac_s) * (1.0 - frac_h);
        let w100 = frac_t * (1.0 - frac_s) * (1.0 - frac_h);
        let w010 = (1.0 - frac_t) * frac_s * (1.0 - frac_h);
        let w110 = frac_t * frac_s * (1.0 - frac_h);
        let w001 = (1.0 - frac_t) * (1.0 - frac_s) * frac_h;
        let w101 = frac_t * (1.0 - frac_s) * frac_h;
        let w011 = (1.0 - frac_t) * frac_s * frac_h;
        let w111 = frac_t * frac_s * frac_h;

        let c000 = self.grid[[i_low, j_low, k_low]];
        let c100 = self.grid[[i_high, j_low, k_low]];
        let c010 = self.grid[[i_low, j_high, k_low]];
        let c110 = self.grid[[i_high, j_high, k_low]];
        let c001 = self.grid[[i_low, j_low, k_high]];
        let c101 = self.grid[[i_high, j_low, k_high]];
        let c011 = self.grid[[i_low, j_high, k_high]];
        let c111 = self.grid[[i_high, j_high, k_high]];

        (0..4).map(|var_idx| {
            w000 * c000[var_idx] + w100 * c100[var_idx] +
            w010 * c010[var_idx] + w110 * c110[var_idx] +
            w001 * c001[var_idx] + w101 * c101[var_idx] +
            w011 * c011[var_idx] + w111 * c111[var_idx]
        }).collect()
    }
}
```

### Pattern 3: Persona-Specific View Composition (Multi-Faceted UI)

**What:** Three personas (Citoyen Explorateur, Expert Politique/Médias, Chercheur) share the same simulation engine but expose different UI layers. The persona is detected at entry (URL path or toggle) and controls which components mount.

**When to use:** When the same computational output needs to be consumed by audiences with drastically different expertise levels and interaction needs.

**Trade-offs:** Increases UI surface area (~3x components). Must ensure engine invariants are identical across personas (same simulation logic, only presentation differs). Risk of "expert leak" — advanced controls accidentally visible in citizen mode.

**Example:**
```typescript
// webapp/src/app/routes.tsx
export const PersonaRoutes = () => {
  const persona = usePersonaStore(s => s.current);

  return (
    <PersonaLayout persona={persona}>
      <Suspense fallback={<SimulationSkeleton />}>
        {persona === 'citoyen' && <CitizenDashboard />}
        {persona === 'expert' && <ExpertDashboard />}
        {persona === 'chercheur' && <ResearcherDashboard />}
      </Suspense>
    </PersonaLayout>
  );
};

// All dashboards consume the same orchestration store:
function CitizenDashboard() {
  const result = useSimulationStore(s => s.microResult);
  return (
    <SimpleVignette result={result}>
      <PlainLanguageSummary />   {/* No jargon */}
      <HouseholdImpactChart />   {/* Just the user's decile */}
    </SimpleVignette>
  );
}

function ExpertDashboard() {
  const { microResult, macroResult } = useSimulationStore();
  return (
    <FullDashboard>
      <MacroTrajectoryChart data={macroResult} />   {/* All variables */}
      <DistributionalImpactChart data={microResult} /> {/* All deciles */}
      <FinancingGapAnalysis />
    </FullDashboard>
  );
}
```

### Pattern 4: Privacy by Design Data Flow (Zero-Knowledge Architecture)

**What:** User input data (household characteristics, income bracket, etc.) is stored exclusively in the browser's WASM linear memory and IndexedDB (for scenario persistence). No `fetch` or `XMLHttpRequest` ever carries identifiable data. Aggregate simulation results are pre-computed from synthetic data and shipped as static assets.

**When to use:** Any application processing financial/personal data where regulatory compliance (RGPD/CNIL) is mandatory and trust is a core differentiator.

**Trade-offs:** Cannot serve personalized content server-side. Cannot use server-rendered charts with user data. All computation must be feasible client-side. This is acceptable because WASM delivers sufficient performance for the microsimulation workload.

## Data Flow

### Primary Interaction Flow (Slider Adjustment — <200ms SLA)

```
User drags slider (e.g., TVA rate: 20% → 22%)
    │
    ▼
Slider Controller (React)
    │ debounce 16ms (1 frame), clamp to bounds, update aria-valuenow
    ▼
Simulation Orchestrator (Zustand store)
    │ Dispatch { type: 'PARAM_CHANGE', param: 'tva_rate', value: 0.22 }
    ├──────────────────┬────────────────────┐
    ▼                  ▼                    ▼
Micro Worker          Macro Worker         Chart Updater
(postMessage)         (postMessage)        (optimistic skeleton)
    │                    │
    ▼                    ▼
WASM Micro Engine     WASM Macro Engine
Reform.apply()        Matrix.interpolate()
Profile loop (Rayon)  Cache check (hash)
    │                    │
    ▼ (1-50ms)           ▼ (1-5ms)
Result (ArrayBuffer)  Projection (Vec<f64>)
    │ postMessage         │ postMessage
    ▼                    ▼
Orchestrator fan-in (Promise.all)
    │ All results received
    ▼
Chart Renderer (D3.js)
    │ transition < 100ms, SVG update
    ▼
Accessible Data Table (HTML table, adjacent to chart)
    │ aria-live="polite" announcement: "TVA à 22%, impact estimé: +12 Md€"
    ▼
User sees updated chart + data table within 150-200ms total
```

### State Management Flow

```
                              ┌──────────────────────┐
                              │  Zustand Global Store  │
                              │  simulation-slice.ts   │
                              └──────┬───────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         ▼                           ▼                           ▼
┌─────────────────┐    ┌─────────────────────────┐    ┌─────────────────┐
│ slider-slice.ts  │    │    scenario-slice.ts     │    │   chart-slice   │
│                  │    │                          │    │                 │
│ • taxParams      │    │ • baselineId             │    │ • microResult   │
│ • spendParams    │    │ • reformPatch (JSON)     │    │ • macroResult   │
│ • isDirty        │    │ • history (undo/redo)    │    │ • isLoading     │
│ • isValid        │    │ • shareUrl               │    │ • errorState    │
└────────┬────────┘    └────────────┬─────────────┘    └────────┬────────┘
         │                          │                            │
         └──────────────────────────┼────────────────────────────┘
                                    │
                            Subscribe (React hooks)
                                    │
                     ┌──────────────┼──────────────┐
                     ▼              ▼              ▼
              SliderInput     ScenarioPanel    ChartCanvas
```

### Data Loading Flow (Initial Load)

```
User opens https://budget-citoyen.fr
    │
    ▼
App Shell mounts → detect persona (URL path / default)
    │
    ▼
Lazy-load WASM bundles (micro.wasm + macro.wasm) ─────── parallel ──────┐
Lazy-load Tax Rules (YAML→JSON bundle, ~200 KB) ──────── parallel ──────┤
Lazy-load Synthetic Population (Parquet/JSON, ~10 MB)─── parallel ──────┤
Lazy-load Shock Matrix (JSON, ~5 MB) ─────────────────── parallel ──────┤
    │                    │                    │                    │
    ▼                    ▼                    ▼                    ▼
All loaded ──► Initialize Micro Worker (rules + pop) ──► 'READY' signal
            ──► Initialize Macro Worker (matrix) ──────► 'READY' signal
    │
    ▼
Render default scenario (baseline) → initial micro + macro simulation
    │
    ▼
User sees initial charts — interactive ready in ~2-3 seconds total (cold load)
Subsequent loads: Service Worker + Cache API → < 1 second
```

### Key Data Flows

1. **Slider → Simulation:** Param change event → debounce 16ms → dispatch to both workers → fan-in results → update reactive stores. Total: 50-150ms (within SLA).
2. **Scenario Save/Share:** Current reform JSON Patch → LZ-String compress → Base64 URL-safe → append to URL hash → copy to clipboard. On load: parse URL hash → decompress → apply patch → simulate.
3. **Persona Switch:** URL route change → mount different dashboard component tree → same simulation store subscriptions → no re-computation needed.
4. **Expert API Export (Chercheur mode):** User clicks "Export CSV" → orchestration store serializes current results → Blob → download via `<a>` tag. No server round-trip.
5. **Matrix Cache Invalidation:** CDN serves matrix with ETag. Service Worker checks ETag on navigation. If stale → background fetch new matrix → re-initialize Macro Worker → emit 'STALE_MATRIX' event → re-simulate if scenario active.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-10K users | Single CDN origin (GitHub Pages / Netlify / Vercel). Expert API as serverless functions. WASM loaded from CDN edge nodes. |
| 10K-1M users | Multi-region CDN (Cloudflare / Fastly). Shock matrix served with range requests for progressive loading. Expert API scaled via edge functions. Synthetic population compressed with Parquet (Zstd) — decode in WASM. |
| 1M+ users (election peak) | Pre-warm CDN edges. Service Worker with aggressive precaching of all static assets (rules, population, matrix). WASM instantiated from Cache API only. Expert API moved to dedicated workers with queue-based rate limiting. |

### Scaling Priorities

1. **First bottleneck:** Shock matrix JSON parsing (5 MB). **Fix:** Serve as Parquet with Zstd compression (→ ~1 MB), decode in WASM via parquet2 crate, or as FlatBuffers with lazy zero-copy access.
2. **Second bottleneck:** Microsimulation over 50 000 profiles in a single Worker. **Fix:** wasm-bindgen-rayon already parallelizes across CPU cores. For extreme loads, split profile batch across multiple browser tabs via BroadcastChannel (not needed for initial launch).
3. **Third bottleneck:** Expert API rate limiting during high traffic. **Fix:** Stateless API can be cloned across N edge function instances. Use token bucket per IP. Since no PII — no sticky sessions needed.

## Anti-Patterns

### Anti-Pattern 1: Monolithic WASM Bundle

**What people do:** Compile all Rust logic (micro engine + macro engine + parameter parsing + interpolation) into a single `.wasm` file.

**Why it's wrong:** Single 2+ MB wasm file blocks startup. Cannot parallel-initialize engines. Changing any Rust code invalidates the entire bundle cache.

**Do this instead:** Separate crates (`wasm-microengine`, `wasm-macroengine`) compiled independently. Each ~500 KB. Loaders can instantiate them in parallel via `Promise.all`. Tax rules and population data are loaded as data (not baked into wasm), enabling updates without recompilation.

### Anti-Pattern 2: Synchronous Simulation in Main Thread

**What people do:** Call `wasmEngine.simulate(input)` directly from a React event handler.

**Why it's wrong:** Blocks the UI thread. Even a 50ms computation causes a visible frame drop. Slider drag generates 30-60 events/second — each blocking call compounds into a frozen UI.

**Do this instead:** Always route simulation calls through Web Workers. Use `postMessage` with transferable ArrayBuffers. Apply request deduplication: if a new slider event arrives while a simulation is in-flight, enqueue it and cancel stale in-flight requests (via `AbortController` equivalent in worker messaging).

### Anti-Pattern 3: Server-Side Rendering of Personalized Results

**What people do:** Send user's income bracket to server, compute on server, return personalized HTML.

**Why it's wrong:** Violates Privacy by Design. Transmits PII over network. Creates server-side state. Subjects to RGPD data processing obligations. Erodes user trust.

**Do this instead:** All personalized computation in WASM workers. Server serves only static, aggregate, anonymized data (shock matrix, synthetic population, rules). The `Expert API` accepts only aggregate queries (no PII), validated by server-side schema checks that reject any field resembling personal data.

### Anti-Pattern 4: Color-Only Chart Differentiation

**What people do:** Use D3.js color scales without alternative encodings (e.g., "the blue line is GDP, the red line is deficit").

**Why it's wrong:** Fails RGAA 4 Thématique 3 (information must not rely solely on color). Excludes users with color vision deficiency. Violates legal accessibility requirements for public services.

**Do this instead:** Every data series must have distinct SVG patterns (hash patterns via `<pattern>` in `<defs>`), distinct marker shapes (circles, squares, triangles, diamonds), AND text labels directly attached to line endpoints. Color is supplementary, never primary. Adjacent HTML `<table>` with `scope` attributes provides text-equivalent for screen readers.

### Anti-Pattern 5: "Accessibility Last" Development

**What people do:** Build all features, then run an accessibility audit in the final phase.

**Why it's wrong:** Canvas/SVG charts built without ARIA roles require full rebuild to add text alternatives. Slider components without WAI-ARIA attributes break screen reader interaction. Remediation cost is 3-5x building accessibly from the start. RGAA 4 compliance is a blocking legal requirement, not a nice-to-have.

**Do this instead:** Accessibility criteria are acceptance criteria for every phase. Each chart component ships with its data table counterpart. Each slider ships with aria-valuenow/aria-valuemin/aria-valuemax. Automated axe-core audits in CI with RGAA-specific rules. Manual screen reader testing (NVDA + VoiceOver) on every release candidate.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| CDN (shock matrix, population, rules) | HTTP GET with ETag/If-None-Match for cache validation | Static assets. Immutable versions identified by content hash in filename. |
| Expert API | REST (fetch), JSON request/response | Opt-in. Stateless. Rate limited. No PII accepted — validated server-side. |
| Browser Cache API / Service Worker | Service Worker intercepts CDN requests → Cache API → serve cached on match | Enables offline-adjacent operation after first load. Critical for election-night traffic spikes. |
| OpenFisca-Core (baseline reference) | Dependency forked as Rust rewrite, not API call | YAML rules remain OpenFisca-compatible for auditability and upstream sync. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| App Shell ↔ Micro Worker | `postMessage` / `MessageChannel` | ArrayBuffer transfer for zero-copy. Typed protocol (discriminated union). |
| App Shell ↔ Macro Worker | `postMessage` / `MessageChannel` | Independent worker. Can be initialized before Micro Worker is ready. |
| Micro Worker ↔ Macro Worker | None | Workers are independent. Orchestration fan-in happens in the main thread. |
| UI Components ↔ Zustand Stores | React hooks (`useStore` selector) | Components subscribe to slices. No prop drilling. |
| WASM ↔ JavaScript (within Worker) | `wasm-bindgen` generated bindings | Serialization via `serde-wasm-bindgen` (bypasses JSON for arrays). |
| Data Pipeline → CDN | CI/CD artifact upload | Generated data is committed to a `data/` branch or uploaded as release assets. Integrity hashes stored in `webapp/` build configuration. |
| Tax Rules ↔ WASM Engine | YAML → JSON build step → loaded at WASM init | Rules bundled as static JSON within the webapp. Versioned with semver. |

### Build Order Implications (for Roadmap)

Based on dependency analysis, the recommended build order is:

1. **Phase 1: Data Foundation** — Tax rules YAML (OpenFisca compatibility layer), synthetic population generation pipeline, shock matrix pre-computation scripts. These are pure data artifacts with no UI dependency. Must exist before WASM engines can be built and tested.

2. **Phase 2: WASM Micro Engine** — Rust crate: TaxBenefitSystem port, formula evaluator, simulation runner, Reform.apply(). Depends on Phase 1 for tax rules schema and population format. Testable headlessly (Rust tests + wasm-bindgen-test). This is the riskiest component — start early.

3. **Phase 3: WASM Macro Engine** — Rust crate: Shock matrix loader, multi-linear interpolation, projection engine. Depends on Phase 1 for matrix format. Testable independently. Lower risk than micro engine (pure math, no legal logic).

4. **Phase 4: Webapp Shell + Persona Routing** — React app scaffold, persona detection, layout system, Zustand stores. Depends on nothing except the decision on framework (React). Can be built in parallel with Phase 2-3 if using mock workers.

5. **Phase 5: Simulation Orchestration** — Worker wrappers, Slider Controller, Scenario Manager, integration of WASM engines with UI. Depends on Phase 2, 3, and 4.

6. **Phase 6: Charts + Accessibility** — D3.js chart components with RGAA 4 compliance (aria roles, pattern fills, data tables). Depends on Phase 5 for data format from simulation results.

7. **Phase 7: Expert API** — REST endpoints for batch simulation and export. Depends on Phase 5 for result schema. Lowest priority — researcher persona is the smallest audience.

## Sources

- **OpenFisca Core Architecture** — Context7 docs (`/openfisca/openfisca-core`): Entity/Parameter/Variable model, Reform system, Simulation builder. HIGH confidence.
- **PolicyEngine Core** — GitHub README (`PolicyEngine/policyengine-core`): Fork of OpenFisca-Core with performance optimizations for tax liability minimization and ML-based data imputation. HIGH confidence.
- **wasm-bindgen** — Context7 docs (`/websites/rustwasm_github_io_wasm-bindgen`): Web Worker patterns, JS interop, synchronous instantiation. HIGH confidence.
- **wasm-bindgen-rayon** — Context7 docs (`/rreverser/wasm-bindgen-rayon`): Thread pool initialization, parallel computation with Rayon in WASM. HIGH confidence.
- **serde-wasm-bindgen** — Context7 docs (`/websites/rs_serde-wasm-bindgen`): Zero-copy serialization between Rust and JS arrays. HIGH confidence.
- **Mésange Model (Insee/Trésor)** — PRD research (Section 4): Neo-Keynesian macroeconomic model, multiplicateur budgétaire values, VAR bootstrap methodology. MEDIUM confidence (secondary source, model documentation is restricted).
- **RGAA 4** — PRD research (Section 5): Criteria 1.1, 1.3 (image alternatives), Thématique 3 (color independence), Thématique 8 (animation control), Thématique 11 (form controls with WAI-ARIA). HIGH confidence.
- **Synthetic Data Generation** — PRD research (Section 5): Copula-based approaches, GAN/VAE, Differential Privacy (ε-budget), membership inference attack prevention. MEDIUM confidence (implementation details from secondary literature).
- **Project PRD** — `prd-research.md`: Full architecture specifications, persona definitions, Mésange model details, compliance requirements. HIGH confidence (internal project document).

---

*Architecture research for: Budget Citoyen — Simulateur Budgétaire Hybride*
*Researched: 2026-05-11*
