# Phase 2: Core Simulation Engines (WASM) - Research

**Researched:** 2026-05-12
**Domain:** Rust/WASM microsimulation (tax formulas) + N-dimensional multlinear interpolation (macro projections)
**Confidence:** HIGH

## Summary

Phase 2 delivers the computational heart of the platform: two WebAssembly engines executing in separate Web Workers. The micro engine ports OpenFisca-France's ~200+ variable tax-benefit system to Rust via automated code generation, computing IR, IS, TVA, cotisations sociales, and aides sociales for any profile. The macro engine performs multi-linear interpolation over the Phase 1 pre-computed shock matrix to project deficit, debt, GDP growth, and employment trajectories. Both engines run entirely client-side with zero data transfer.

**Primary recommendation:** Replace `interpolation 0.3.0` (animation easing, wrong crate) with `interpn 0.11.0` (no-std N-dimensional multilinear interpolation, WASM-optimized). The STACK.md reference to `interpolation` is incorrect for this use case — a STACK.md update should be scheduled. Additionally, verify Parquet/Zstd decompression in WASM early via a spike — the `parquet2` crate's zstd backend uses a C binding (`zstd` crate) that may not compile to `wasm32-unknown-unknown`. A pure-Rust fallback (`ruzstd`) or format conversion (gzip-compressed Parquet, or simpler binary format) should be validated before greenlighting the full implementation.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Tax formula evaluation (IR, IS, TVA, etc.) | Browser/WASM (Micro Worker) | — | Privacy-by-design: all computation client-side, zero data transfer |
| Parameter loading from JSON rules | Browser/WASM (Micro Worker) | CDN/Static | Rules fetched as static JSON assets, loaded at worker init |
| Multi-linear interpolation over shock matrix | Browser/WASM (Macro Worker) | — | Grid interpolation in microseconds; convex hull boundary check client-side |
| Shock matrix data loading (Parquet) | Browser/WASM (Macro Worker) | CDN/Static | Matrix fetched as static binary, decoded in WASM |
| Profile data storage (`Vec<Profile>`) | Browser/WASM (Micro Worker) | — | 50K profiles in WASM linear memory (~10MB), never leave browser |
| Bilingual validation (Python ↔ Rust) | CI/Build Server | Browser | Python reference computes expected outputs → JSON fixtures → cargo test compares |
| Worker orchestration (postMessage) | Browser/Main Thread | — | Main thread dispatches to workers, fans in results, never touches computation |
| Static asset delivery (rules, population, matrix) | CDN/Static | — | Immutable versioned assets with integrity hashes |

## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** 3 crates: `core` (shared types), `wasm-micro` (TaxBenefitSystem), `wasm-macro` (ShockMatrix + interpolation). Cargo workspace at repo root.
- **D-02:** Core crate scope: data types (Profile, Parameter), parameter tree loading from JSON, profile parsing, test fixtures. No engine logic in core.
- **D-03:** Crates live in `packages/` (flat): `packages/core`, `packages/wasm-micro`, `packages/wasm-macro`.
- **D-04:** Separate CI workflow `.github/workflows/phase2-wasm.yml` with `cargo test` + `wasm-pack test`. Phase 1's version-consistency gate runs first as prerequisite.
- **D-05:** Code generation from OpenFisca Python source. Python script introspects `openfisca-france` variable graph, generates Rust source files.
- **D-06:** Full OpenFisca-France variable tree (~200+ variables) — no subsetting for v1.
- **D-07:** Manual codegen run, commit generated code to repo. CI emits soft warning if upstream newer.
- **D-08:** Code generator output: pure Rust functions with typed inputs + match on period. One module per tax domain.
- **D-09:** Input: flat `&[f64]` slice + index-based setters. All slider values cross boundary in single slice. Zero serialization overhead.
- **D-10:** Output: structured result structs via `wasm-bindgen` + `serde-wasm-bindgen`. Typed `MicroResult` / `MacroResult` objects.
- **D-11:** Web Worker message protocol: typed request/response with correlation IDs. Main thread discards stale responses.
- **D-12:** Data loading: main thread fetches static assets, transfers to workers via `postMessage` with Transferable ArrayBuffers. Workers never touch network.
- **D-13:** Simplified flat `Profile` struct — all relevant attributes flattened. Code generator resolves cross-entity references at codegen time.
- **D-14:** Profile storage: `Vec<Profile>` in WASM linear memory. Single-profile: index into Vec.
- **D-15:** Profile struct definition derives from code generator output.
- **D-16:** Strict load-time validation: `serde` deserialize + `validate()` method. Returns `Result<Profile, LoadError>`.

### the agent's Discretion

- Exact index mapping for the flat `&[f64]` input array (which index maps to which parameter)
- Cargo workspace configuration details (workspace members, dependency versions, feature flags)
- Code generator implementation details (introspection API, Rust code formatting, output directory structure)
- Worker initialization sequencing (which worker to init first, timeout/retry strategy)
- Production service worker integration for asset caching (deferred to Phase 3/5)
- COOP/COEP header strategy (test on target platform early per STACK.md warning)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MICRO-01 | Moteur calcule IR pour un profil type, exécuté en WASM | Code generator produces `fn calculate_ir()` from OpenFisca-France IR formulas; proptest + bilingual fixtures validate |
| MICRO-02 | Moteur couvre TVA, IS, cotisations sociales | Full variable tree (~200+) includes all tax domains; code generator targets all per D-06 |
| MICRO-03 | Moteur calcule les aides sociales (prestations, allocations) | OpenFisca-France covers RSA, APL, allocations familiales, prime d'activité, AAH, ASPA, etc. |
| MICRO-04 | Calcul exécuté intégralement côté client sans transfert | Web Worker isolation; zero network access from workers per D-12 |
| MICRO-05 | Temps de réponse < 200ms pour calcul sur profil type | Flat `&[f64]` batch interface avoids serialization overhead per D-09; WASM linear execution in microseconds |
| MACRO-01 | Interpolation multi-linéaire estime trajectoire du déficit | `interpn 0.11.0` multilinear interpolation over shock matrix grid; convex hull bounds check per PITFALLS.md |
| MACRO-02 | Interpolation estime trajectoire de la dette souveraine | Same interpolation framework; shock matrix stores 4 output variables per grid cell |
| MACRO-03 | Interpolation estime projections de croissance (PIB) et d'emploi | Same; outputs from grid include GDP growth, employment change |
| MACRO-04 | Résultats macroéconomiques < 200ms après modification curseur | Interpolation is O(2^ndims) with ndims ≤ 4 — worst case 16 grid lookups + weighted sum, < 1ms in WASM |
| MACRO-05 | Taux d'intérêt lissés constants | No real-time rate component in warp engine; interpolation operates on pre-computed grid derived from constant-rate scenarios |

## Standard Stack

### Core (Rust/WASM)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| wasm-bindgen | 0.2.121 | JS ↔ WASM interop | Standard bridge; auto-generates TypeScript `.d.ts`; serde integration |
| wasm-pack | 0.14.0 | WASM build toolchain | One-command build (`--target web`); wasm-opt optimization; npm-ready pkg/ |
| serde | 1.0.228 | Serialization framework | Derive macros for all Rust types; the standard for Rust data interchange |
| serde-wasm-bindgen | 0.6.5 | WASM-specific serde | Converts Rust structs ↔ `JsValue` efficiently; avoids JSON stringification overhead |
| serde_json | 1.0.149 | JSON parsing (WASM) | Parses tax rules JSON loaded by browser; minimal WASM binary size |
| ndarray | 0.17.2 | N-dimensional arrays | Stores shock matrix data; broadcasting ops; `ArrayView::as_slice()` for zero-copy access |


### ⚠️ Stack Correction: Multi-linear Interpolation

**CRITICAL FINDING:** The `interpolation 0.3.0` crate listed in STACK.md and CONTEXT.md is **not suitable** for N-dimensional grid interpolation. That crate provides animation easing functions (`lerp`, `cubic_bezier`, `quad_bezier`) for graphical transitions — it has no multi-dimensional grid interpolation capability.

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **interpn** | **0.11.0** | **N-dimensional multilinear/cubic interpolation** | **no-std and no-alloc compatible (WASM-optimized); supports regular and rectilinear grids; O(2^ndims) performance; up to 8 dimensions; non-allocating variants for pre-allocated outputs; matches numpy conventions for C-order arrays** |

**Evidence:**
- `interpn 0.11.0` verified via crates.io API (2026-05-12): "N-dimensional interpolation/extrapolation methods, no-std and no-alloc compatible, prioritizing correctness, performance, and compatibility with memory-constrained environments."
- `ndarray-interp 0.6.0` considered but rejected: limited to 1D/2D interpolation only. Shock matrix is 3D/4D.
- `interpolation 0.3.0` (STACK.md reference): docs.rs shows only easing functions (`Ease`, `Lerp`, `cubic_bezier`). Not designed for grid interpolation.

**Action:** Update STACK.md to replace `interpolation 0.3.0` with `interpn 0.11.0`. The planner should include this correction in the PLAN.md.

### Supporting (Data Loading & Testing)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| parquet2 | 0.17.2 | Parquet file reading | Shock matrix loading from Phase 1 export; see Parquet/WASM note below |
| ruzstd | 0.8.3 | Pure-Rust zstd decompression | WASM-safe zstd decoder if `parquet2`'s C-binding zstd backend fails WASM compilation |
| proptest | 1.11.0 | Property-based testing | Native `cargo test` with randomized input strategies; required by success criterion 5 |
| wasm-bindgen-test | 0.3.71 | WASM boundary tests | Browser-context tests via headless Chromium; validates JS↔WASM boundary only |
| wasm-bindgen-rayon | 1.3.0 | WASM parallelism (optional) | Batch profile simulation (Phase 4); not needed for single-profile Phase 2 requirement |

### ⚠️ Parquet/Zstd in WASM — Architectural Risk

The `parquet2` crate's default feature set includes `zstd` compression support, which depends on the C-binding `zstd` crate (v0.13.3). This C binding **may not compile** to the `wasm32-unknown-unknown` target. Verified alternatives:

1. **Use `parquet2` with `default-features = false, features = ["gzip"]`**: The `gzip` feature uses `flate2/rust_backend` (pure-Rust `miniz_oxide`), fully WASM-compatible. Requires adjusting Phase 1's `export_parquet.py` to use gzip instead of zstd compression (or exporting a WASM-specific variant).

2. **Pre-decompress with `ruzstd`**: Read the raw Parquet file bytes on the JS side, decompress zstd blocks with `ruzstd` (pure Rust, WASM-safe), then feed decompressed pages to `parquet2` with compression disabled.

3. **Simpler binary format**: Bypass Parquet entirely for WASM consumption — use `postcard` or `bincode` serialization of the shock matrix as a flat binary, compressed with gzip at the HTTP level. This is the simplest approach and avoids the parquet2 dependency entirely in WASM (reducing binary size). The JS side would `fetch()` the binary, decompress via `DecompressionStream('gzip')`, and `postMessage` the ArrayBuffer to the worker.

**Recommendation:** Spike option 3 first (simplest, smallest WASM binary). If Parquet features are needed (column selection, row filtering), evaluate option 1. Document the decision as a spike task in the plan.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| interpn 0.11.0 | Hand-rolled multilinear interpolation | ~200 LOC, more bugs, less tested. interpn has 81% documented API coverage, used in scientific computing. |
| ndarray 0.17.2 | flat Vec<f64> with manual indexing | Loses broadcasting and slicing; more error-prone for 4D grid indexing |
| serde-wasm-bindgen 0.6.5 | JSON serialization across WASM boundary | 5-15ms overhead per structured result vs ~0.1ms for JsValue bridge |
| proptest 1.11.0 | Hand-written test cases only | Misses edge cases; proptest discovers counterexamples automatically |
| Cargo workspace (3 crates) | Single monolithic crate | Violates D-01; prevents independent testing; forces full rebuild on any change |

**Installation:**
```bash
# Rust toolchain (must be installed on dev machine):
rustup target add wasm32-unknown-unknown
cargo install wasm-pack

# Verify:
wasm-pack --version  # => 0.14.0
rustc --version      # => 1.85+ (stable)
```

```toml
# packages/core/Cargo.toml
[package]
name = "budget-citoyen-core"
version = "0.1.0"
edition = "2021"

[dependencies]
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"

[dev-dependencies]
proptest = "1.11"
```

```toml
# packages/wasm-micro/Cargo.toml
[package]
name = "budget-citoyen-wasm-micro"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib", "rlib"]

[dependencies]
budget-citoyen-core = { path = "../core" }
wasm-bindgen = "0.2.121"
serde = { version = "1.0", features = ["derive"] }
serde-wasm-bindgen = "0.6.5"
serde_json = "1.0"

[dev-dependencies]
wasm-bindgen-test = "0.3.71"
```

```toml
# packages/wasm-macro/Cargo.toml
[package]
name = "budget-citoyen-wasm-macro"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib", "rlib"]

[dependencies]
budget-citoyen-core = { path = "../core" }
wasm-bindgen = "0.2.121"
serde = { version = "1.0", features = ["derive"] }
serde-wasm-bindgen = "0.6.5"
ndarray = "0.17"
interpn = "0.11"

# For Parquet reading (spike to verify WASM compatibility):
# parquet2 = { version = "0.17", default-features = false, features = ["gzip"] }
# Or skip parquet2 and use a simpler binary format

[dev-dependencies]
wasm-bindgen-test = "0.3.71"
```

```toml
# Cargo.toml (workspace root)
[workspace]
members = [
    "packages/core",
    "packages/wasm-micro",
    "packages/wasm-macro",
]
resolver = "2"
```

**Version verification:** All crate versions verified via crates.io API on 2026-05-12. wasm-bindgen 0.2.121, serde 1.0.228, serde_json 1.0.149, serde-wasm-bindgen 0.6.5, ndarray 0.17.2, interpn 0.11.0, proptest 1.11.0, wasm-bindgen-rayon 1.3.0, wasm-bindgen-test 0.3.71, parquet2 0.17.2, ruzstd 0.8.3. wasm-pack 0.14.0 verified via npm registry.

## Architecture Patterns

### System Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│                           APPLICATION SHELL (Main Thread)                     │
│                                                                              │
│  ┌──────────────────────────────────────┐   ┌────────────────────────────┐  │
│  │         Data Loader (init)            │   │   Worker Orchestrator       │  │
│  │                                      │   │                              │  │
│  │  fetch("tax-rules-v2025.1.json")     │   │  Pending requests by ID      │  │
│  │  fetch("population-v2025.1.json")    │   │  Stale response discarding   │  │
│  │  fetch("shockmatrix-v2025.1.parquet")│   │  Correlation ID tracking     │  │
│  │                                      │   │                              │  │
│  │  postMessage(Transferable) ──────────┼───┼──► Workers (zero-copy)       │  │
│  └──────────────────────────────────────┘   └──────────┬─────────────────┘  │
│                                                        │                     │
│  ═══════════════════════ WORKER BOUNDARY ═══════════════╪══════════════════ │
│                                                        │                     │
│  ┌──────────────────────────────────────┐   ┌──────────┴─────────────────┐  │
│  │       Micro Engine Worker             │   │    Macro Engine Worker      │  │
│  │                                      │   │                              │  │
│  │  ┌────────────────────────────┐      │   │  ┌────────────────────────┐  │  │
│  │  │  TaxBenefitSystem           │      │   │  │  ShockMatrix            │  │  │
│  │  │  (generated Rust code)      │      │   │  │  (ndarray + interpn)    │  │  │
│  │  │                              │      │   │  │                          │  │  │
│  │  │  • Parameters tree (JSON)   │      │   │  │  • Grid data (Array4)    │  │  │
│  │  │  • Profile (Vec<Profile>)   │      │   │  │  • Breakpoint vectors    │  │  │
│  │  │  • ~200+ formula functions  │      │   │  │  • Convex hull bounds    │  │  │
│  │  │  • Reform application       │      │   │  │  • interpn::multilinear   │  │  │
│  │  │                              │      │   │  │                          │  │  │
│  │  │  Input:  &[f64] (flat array) │      │   │  │  Input:  &[f64] (params) │  │  │
│  │  │  Output: MicroResult struct  │      │   │  │  Output: MacroResult      │  │  │
│  │  └────────────────────────────┘      │   │  └────────────────────────┘  │  │
│  │                                      │   │                              │  │
│  │  Profile validation:                 │   │  Convex hull check:           │  │
│  │    Result<Profile, LoadError>         │   │    Option::None for out-of-   │  │
│  │    Invalid profiles rejected          │   │    bounds inputs per D-09     │  │
│  └──────────────────────────────────────┘   └──────────────────────────────┘  │
│                                                                              │
│  DATA FLOW (both workers):                                                    │
│    Main thread ──postMessage({id, type, payload})──► Worker                   │
│    Worker ──postMessage({id, type, result}, [transferable])──► Main thread    │
│                                                                              │
│  PRIVACY GUARANTEE:                                                           │
│    Workers never call fetch() or XMLHttpRequest                               │
│    All profile data stays in WASM linear memory                               │
│    Zero computation results leave the browser                                 │
└────────────────────────────────────────────────────────────────────────────┘
```

### Recommended Project Structure (Rust crates only — non-Rust packages omitted)

```
packages/
├── core/                          # Shared library crate (no WASM deps)
│   ├── src/
│   │   ├── lib.rs                 # Crate root: re-exports
│   │   ├── types.rs               # Profile, Parameter, LoadError, MicroResult, MacroResult
│   │   ├── parameters.rs          # Parameter tree loading from JSON, date-based lookup
│   │   ├── profiles.rs            # Profile parsing, deserialization, validate()
│   │   └── test_fixtures.rs       # Bilingual fixture loading (include_str! or test helper)
│   ├── tests/
│   │   ├── parameter_tests.rs     # proptest: parameter round-trip, date resolution
│   │   └── profile_tests.rs       # proptest: profile validation edge cases
│   └── Cargo.toml
│
├── wasm-micro/                    # WASM microsimulation engine
│   ├── src/
│   │   ├── lib.rs                 # wasm-bindgen exports (init, simulate, set_param)
│   │   ├── system.rs              # TaxBenefitSystem: owns parameter tree + profile vec
│   │   ├── simulation.rs          # State update from flat &[f64], formula dispatch
│   │   └── generated/             # AUTO-GENERATED (not hand-edited)
│   │       ├── mod.rs             # Re-exports all formula modules
│   │       ├── ir.rs              # fn calculate_ir(...) — generated from OpenFisca
│   │       ├── is.rs              # fn calculate_is(...)
│   │       ├── tva.rs             # fn calculate_tva(...)
│   │       ├── cotisations.rs     # fn calculate_cotisations_* (...)
│   │       └── aides.rs           # fn calculate_rsa, calculate_apl, ...
│   ├── tests/
│   │   ├── wasm_boundary.rs       # wasm-bindgen-test: JS↔WASM round-trip
│   │   └── bilingual.rs           # Load fixtures JSON, compare Rust output vs expected
│   └── Cargo.toml
│
├── wasm-macro/                    # WASM macroeconomic engine
│   ├── src/
│   │   ├── lib.rs                 # wasm-bindgen exports (init, interpolate)
│   │   ├── matrix.rs              # ShockMatrix: grid loading, breakpoint storage
│   │   ├── interpolate.rs         # interpn::multilinear call, convex hull check
│   │   └── projection.rs          # Trajectory projection over N horizon years
│   ├── tests/
│   │   ├── wasm_boundary.rs       # wasm-bindgen-test: boundary tests
│   │   └── interpolation_tests.rs # In-bounds/out-of-bounds validation
│   └── Cargo.toml
│
├── data-pipeline/                 # Phase 1 Python pipeline (existing)
│   └── src/validation/export_fixtures.py  # Produces bilingual_test_fixtures.json
│
└── tax-rules/                     # Phase 1 YAML rules (existing)
    └── parameters/                # 31 YAML files across IR/IS/TVA/cotisations/aides
```

### Pattern 1: Flat &[f64] Boundary Interface (D-09)

**What:** All simulation parameters cross the WASM boundary as a single `&[f64]` slice with a constant index-to-parameter mapping. Rust-side updates a pre-allocated `SimulationState` in-place — no serialization, no allocation per slider event.

**When to use:** Every slider interaction. This is the primary input path for the micro engine.

**Implementation:**
```rust
// packages/wasm-micro/src/simulation.rs
//
// INDEX MAPPING (documented constant module, shared with TypeScript):
//
// Index 0 : IR bracket 1 rate (fraction of reference)
// Index 1 : IR bracket 2 rate
// Index 2 : IR bracket 3 rate
// Index 3 : IR bracket 4 rate
// Index 4 : IR bracket 5 rate
// Index 5 : IS rate
// Index 6 : TVA normal rate
// Index 7 : TVA reduced rate
// Index 8 : CSG deductible rate
// Index 9 : CRDS rate
// Index 10: Cotisations salariales rate
// Index 11: Cotisations patronales rate
// Index 12: Dépenses publiques level
// Index 13: Effectifs de l'État factor
// ... (16 total for v1)

pub const NUM_SIMULATION_PARAMS: usize = 16;

pub struct SimulationState {
    params: [f64; NUM_SIMULATION_PARAMS],
    // ... cached computed values
}

impl SimulationState {
    /// Update all parameters from a flat slice.
    /// Called from wasm-bindgen export on every slider change.
    /// Performs bounds validation, applies reform, recomputes cached values.
    pub fn update_params(&mut self, input: &[f64]) -> Result<(), &'static str> {
        if input.len() != NUM_SIMULATION_PARAMS {
            return Err("Input slice length mismatch");
        }
        self.params.copy_from_slice(input);
        self.validate_bounds()?;
        self.recompute()
    }
}

// wasm-bindgen export (in lib.rs):
#[wasm_bindgen]
impl MicroEngine {
    pub fn update_and_simulate(&mut self, params: &[f64], profile_index: usize) -> JsValue {
        self.state.update_params(params).unwrap();
        let result = self.state.compute_for_profile(profile_index);
        serde_wasm_bindgen::to_value(&result).unwrap()
    }
}
```

**TypeScript side:**
```typescript
// webapp/src/workers/index-map.ts
export const PARAM_INDICES = {
  IR_BRACKET_1_RATE: 0,
  IR_BRACKET_2_RATE: 1,
  IR_BRACKET_3_RATE: 2,
  IR_BRACKET_4_RATE: 3,
  IR_BRACKET_5_RATE: 4,
  IS_RATE: 5,
  TVA_NORMAL: 6,
  TVA_REDUCED: 7,
  CSG_DEDUCTIBLE: 8,
  CRDS: 9,
  COTIS_SALARIALES: 10,
  COTIS_PATRONALES: 11,
  SPEND_LEVEL: 12,
  EFFECTIFS_ETAT: 13,
} as const;

// Build the flat array for a slider change:
const params = new Float64Array(16);
params.fill(1.0); // reference values
params[PARAM_INDICES.TVA_NORMAL] = 0.22; // 22% TVA
worker.postMessage({
  id: crypto.randomUUID(),
  type: 'SIMULATE',
  payload: { params: Array.from(params), profileIndex: 0 }
});
```

### Pattern 2: Web Worker Message Protocol with Correlation IDs (D-11)

**What:** Typed request/response protocol with unique correlation IDs. Main thread tracks pending requests and discards stale responses if a newer request superseded it (e.g., rapid slider dragging produces 60 req/s but only latest matters).

**Implementation:**
```typescript
// webapp/src/workers/orchestrator.ts
type WorkerRequest = {
  id: string;
  type: 'INIT' | 'SIMULATE' | 'INTERPOLATE';
  payload: unknown;
};

type WorkerResponse = {
  id: string;
  type: 'READY' | 'MICRO_RESULT' | 'MACRO_RESULT' | 'ERROR';
  payload: unknown;
};

class WorkerOrchestrator {
  private microWorker: Worker;
  private macroWorker: Worker;
  private pending = new Map<string, { resolve: Function; timestamp: number }>();
  private latestMicroId: string | null = null;
  private latestMacroId: string | null = null;

  constructor() {
    this.microWorker = new Worker(new URL('./micro-worker.ts', import.meta.url), { type: 'module' });
    this.macroWorker = new Worker(new URL('./macro-worker.ts', import.meta.url), { type: 'module' });

    this.microWorker.onmessage = (e: MessageEvent<WorkerResponse>) => this.handleResponse(e.data, 'micro');
    this.macroWorker.onmessage = (e: MessageEvent<WorkerResponse>) => this.handleResponse(e.data, 'macro');
  }

  private handleResponse(response: WorkerResponse, source: 'micro' | 'macro') {
    const latest = source === 'micro' ? this.latestMicroId : this.latestMacroId;

    // Discard stale responses
    if (latest !== null && response.id !== latest) {
      console.debug(`Discarding stale ${source} response: ${response.id}`);
      return;
    }

    const pending = this.pending.get(response.id);
    if (pending) {
      pending.resolve(response.payload);
      this.pending.delete(response.id);
    }
  }

  async simulate(params: number[], profileIndex: number): Promise<MicroResult> {
    const id = crypto.randomUUID();
    this.latestMicroId = id;

    return new Promise((resolve) => {
      this.pending.set(id, { resolve, timestamp: Date.now() });
      this.microWorker.postMessage({ id, type: 'SIMULATE', payload: { params, profileIndex } });
    });
  }
}
```

### Pattern 3: Core/WASM Crate Split (D-01, D-02)

**What:** The `core` crate contains zero WASM dependencies — pure Rust with native `#[test]` functions. The `wasm-micro` and `wasm-macro` crates import `core` and add the `wasm-bindgen` boundary layer. This separation is critical for fast development iteration (`cargo test` in microseconds, not browser seconds) and prevents the `wasm_bindgen` import from leaking into business logic (Pitfall 8, PITFALLS.md).

**Implementation:**
```rust
// packages/core/src/types.rs
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Profile {
    pub profile_id: String,
    pub age: u8,
    pub patrimoine: f64,
    pub revenu_fiscal: f64,
    pub situation_familiale: SituationFamiliale,
    pub nombre_parts: f64,
    pub type_activite: TypeActivite,
    // ... additional codegen-derived fields
}

impl Profile {
    pub fn validate(&self) -> Result<(), LoadError> {
        if self.age > 120 { return Err(LoadError::InvalidAge(self.age)); }
        if self.patrimoine < 0.0 { return Err(LoadError::NegativeWealth); }
        // ... further validation
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MicroResult {
    pub ir: f64,                    // Impôt sur le revenu net
    pub is_contribution: f64,       // IS attributable to this profile
    pub tva_acquittee: f64,         // TVA paid (consumption-based estimate)
    pub cotisations_salariales: f64,
    pub csg_crds: f64,
    pub aides: AidesResult,
    pub revenu_disponible: f64,     // Net disposable income
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MacroResult {
    pub deficit_trajectory: Vec<f64>,    // 5 years
    pub debt_trajectory: Vec<f64>,       // 5 years
    pub gdp_growth_trajectory: Vec<f64>, // 5 years
    pub employment_trajectory: Vec<f64>, // 5 years
    pub is_out_of_bounds: bool,          // True if interpolation was clamped
    pub warning_message: Option<String>,
}
```

### Pattern 4: Code Generator Architecture (D-05, D-06, D-07, D-08)

**What:** A Python script (in `packages/data-pipeline/src/codegen/`) introspects the `openfisca-france` variable graph and generates Rust source files. The code generator:
1. Uses `openfisca_france.FranceTaxBenefitSystem().variables` to discover all ~200+ variables
2. Resolves dependency ordering (topological sort of the variable DAG)
3. Emits one Rust module per tax domain (`ir.rs`, `is.rs`, `tva.rs`, etc.)
4. Each formula becomes a pure function: `fn calculate_xxx(parameters: &Parameters, period: Date, profile: &Profile) -> f64`
5. Cross-entity references (Individu, Famille, FoyerFiscal, Menage) are resolved at codegen time by inlining relevant attributes into the flat `Profile` struct
6. Output writes to `packages/wasm-micro/src/generated/`

**Key design points:**
- Generated code is committed to git (D-07) — not regenerated at CI time
- CI only checks if upstream `openfisca-france` has newer version (soft warning)
- The code generator itself lives in the Phase 1 data-pipeline package (reuses existing `openfisca-france` dependency at `>=159,<200`)
- Error handling: if a formula can't be translated, the code generator emits a `// TODO: MANUAL_PORT` comment with the original Python source

### Anti-Patterns to Avoid

- **Monolithic WASM crate:** Never put engine logic behind `#[wasm_bindgen]` annotations. Core logic must be testable via `cargo test` without a browser. (Pitfall 8)
- **Per-parameter WASM calls:** Never call WASM for each individual slider change with a structured object. Always batch all parameters into a single `&[f64]` slice. (Pitfall 1)
- **Silent extrapolation:** Never return interpolated values for points outside the convex hull without a warning. Always return `Option::None` or set `is_out_of_bounds: true`. (Pitfall 2)
- **Hand-rolled interpolation:** Never implement multilinear interpolation from scratch. Use `interpn 0.11.0` which handles edge cases (degenerate grids, floating-point precision, C-order array conventions).
- **JSON across JS↔WASM boundary for inputs:** Never serialize inputs as JSON strings. Use the flat `&[f64]` slice for inputs, `serde-wasm-bindgen` only for structured results. (D-09, D-10)

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| N-dimensional multilinear interpolation | Custom trilinear/quadrilinear code | `interpn 0.11.0` | Handles edge cases (degenerate grids, precision, C-order conventions); 2^ndims weighting is error-prone; no-std compatible for WASM |
| Parameter tree loading with date-based lookup | Custom YAML/JSON parser with date matching | `serde_json` + typed struct with `BTreeMap<Date, Value>` | Date resolution logic (closest past date) is subtle; OpenFisca has well-defined parameter update semantics |
| Property-based testing strategies | Hand-written edge case lists | `proptest 1.11.0` | Generates counterexamples automatically; shrinks to minimal failing case; required by success criterion 5 |
| JS↔WASM structured object serialization | JSON.stringify/parse across the boundary | `serde-wasm-bindgen 0.6.5` | Converts Rust structs ↔ `JsValue` without JSON stringification; ~10x faster for typed results |
| Parquet file reading in WASM | Custom binary format parser | `parquet2 0.17.2` (with WASM-safe compression) or simpler binary format (`postcard` + gzip at HTTP level) | Parquet is a complex format (page headers, repetition/definition levels, encoding schemes); `parquet2` is the standard Rust implementation |
| Worker message protocol | Ad-hoc postMessage with string types | Typed request/response with discriminated union + correlation IDs per D-11 | Without correlation IDs, stale responses from rapid slider drags corrupt UI state |

**Key insight:** The riskiest hand-rolled component would be the formula translation from Python to Rust. CONTEXT.md wisely mandates automated code generation (D-05) — this avoids manual porting errors of ~200+ tax formulas. The code generator is the single most important tool built in this phase. A spike of 3-5 representative formulas should validate the code generation approach before scaling to the full variable tree.

## Common Pitfalls

### Pitfall 1: WASM Serialization Tax (from PITFALLS.md, verified)
**What goes wrong:** Crossing JS↔WASM boundary on every parameter change incurs 5-15ms serialization overhead per call. With rapid slider updates at 60fps, total latency breaks the 200ms budget.

**How to avoid (per D-09):** Flat `&[f64]` slice input — all slider values in one transfer, zero serialization. Pre-allocated `SimulationState` updated in-place.

**Warning signs:** Profiling shows >10ms in JS between slider `input` event and render. Each update creates a new Rust-side `Simulation` from scratch.

### Pitfall 2: Extrapolation Beyond Convex Hull (from PITFALLS.md, verified)
**What goes wrong:** Users set slider combinations outside the pre-computed grid's convex hull. Multilinear interpolation silently extrapolates, producing fantasy values (e.g., negative unemployment).

**How to avoid:** `interpn` implicitly handles extrapolation. Phase 1 exports convex hull boundaries (hyperplane equations from `scipy.spatial.ConvexHull`). The macro engine must check whether the requested point lies inside the hull before calling `interpn`. Return `MacroResult { is_out_of_bounds: true, warning_message: Some("...") }` when outside.

**Warning signs:** No bounds-checking code in the interpolation module. Slider ranges defined by UI convenience rather than model domain.

### Pitfall 3: Untestable WASM Logic (from PITFALLS.md Pitfall 8, verified)
**What goes wrong:** All Rust code imports `wasm_bindgen`, making `cargo test` impossible without a browser. Development velocity plummets.

**How to avoid (per D-01, D-02):** `core` crate with zero WASM dependencies. `wasm-micro` and `wasm-macro` only contain the boundary layer. All business logic testable via `cargo test` in the `core` crate.

**Warning signs:** `wasm_bindgen` imports in formula functions. `cargo test` fails with unresolved symbols.

### Pitfall 4: Code Generator Produces Incorrect Floating-Point Semantics (PHASE-SPECIFIC)
**What goes wrong:** Python's `float` (IEEE 754 double) and Rust's `f64` have identical representation but different intermediate rounding. OpenFisca uses Python's arbitrary-precision fractions for some tax calculations. A naive port to `f64` accumulates error beyond the 1e-6 precision threshold.

**How to avoid:**
- The bilingual validation suite (Phase 1 `export_fixtures.py`) catches precision drift immediately
- For critical calculations (tax bracket application, quotient familial), use `f64` but verify against Python reference
- If specific formulas require higher precision, use a fixed-point representation or `rust_decimal` crate
- CI gate: `cargo test` with bilingual fixtures fails if any value differs by > 1e-6

**Warning signs:** Bilingual tests pass for simple profiles but fail for edge cases (multi-property, high-income). Cumulative error from chained formulas.

### Pitfall 5: Parquet/Zstd Decompression Fails in WASM (PHASE-SPECIFIC, RESEARCH FINDING)
**What goes wrong:** The `parquet2` crate's `zstd` feature depends on the C-binding `zstd` crate, which links against libzstd C library. This C library may not cross-compile to `wasm32-unknown-unknown`, causing build failures late in development.

**How to avoid:**
- **Early spike (Week 1):** Verify `parquet2` with `default-features = false, features = ["gzip"]` compiles and works in WASM
- **Fallback A:** Adjust Phase 1 `export_parquet.py` to use gzip compression instead of zstd (gzip via `flate2/rust_backend` is pure Rust)
- **Fallback B:** Use `ruzstd 0.8.3` (pure-Rust zstd decoder) to pre-decompress the buffer before feeding to `parquet2`
- **Fallback C:** Bypass Parquet entirely — export the shock matrix as a flat binary (postcard/bincode + gzip HTTP compression) loaded as `Vec<f64>` via `js_sys::Uint8Array`

**Warning signs:** `parquet2` with default features fails `wasm-pack build`. Linker errors referencing `libzstd`. No spike performed before committing to the Parquet approach.

## Code Examples

### Multi-linear Interpolation with interpn (Macro Engine)

```rust
// packages/wasm-macro/src/interpolate.rs
// Source: docs.rs/interpn/0.11.0/interpn/multilinear/index.html
use interpn::multilinear::rectilinear;
use ndarray::Array4;

pub struct ShockMatrix {
    // Grid dimension breakpoints
    tax_bp: Vec<f64>,     // e.g., [0.5, 0.6, 0.7, ..., 2.0] (12 points)
    spend_bp: Vec<f64>,   // e.g., [0.7, 0.8, ..., 1.5] (12 points)
    horizon_bp: Vec<f64>, // e.g., [1.0, 2.0, 3.0, 4.0, 5.0] (5 years)
    // 4D grid: (tax_bp, spend_bp, horizon_bp, output_var)
    // output_var: [gdp_growth, employment_change, deficit_change, debt_to_gdp_ratio]
    grid: Vec<f64>,       // C-order flattened
    // Convex hull hyperplane equations (from Phase 1 scipy.spatial.ConvexHull)
    hull_equations: Vec<Vec<f64>>,  // Each: [a1, a2, a3, b] where a·x + b <= 0
}

impl ShockMatrix {
    /// Multi-linear interpolation. Returns None if input is outside the convex hull.
    pub fn interpolate(&self, tax: f64, spend: f64, horizon: f64) -> Option<MacroResult> {
        // Check convex hull containment
        let point = [tax, spend, horizon];
        if !self.is_inside_hull(&point) {
            return None;
        }

        // interpn expects grids as slices of slices
        let grids = &[
            &self.tax_bp[..],
            &self.spend_bp[..],
            &self.horizon_bp[..],
        ];

        // Observation point
        let obs = [&point[..]];  // interpn expects &[&[f64]] for multiple obs points

        // Output buffer
        let mut out = [0.0_f64; 4];

        // Perform multilinear interpolation
        rectilinear::interpn(
            grids,
            &self.grid,
            &obs,
            &mut out,
        ).expect("interpolation should succeed for in-bounds inputs");

        Some(MacroResult {
            gdp_growth: out[0],
            employment_change: out[1],
            deficit_change: out[2],
            debt_to_gdp_ratio: out[3],
            is_out_of_bounds: false,
            warning_message: None,
        })
    }

    /// Check if a point is inside the pre-computed convex hull.
    /// Uses the hyperplane equations from Phase 1's scipy.spatial.ConvexHull.
    fn is_inside_hull(&self, point: &[f64; 3]) -> bool {
        for eq in &self.hull_equations {
            let dot = eq[0] * point[0] + eq[1] * point[1] + eq[2] * point[2] + eq[3];
            if dot > 1e-10 {
                return false; // Outside this hyperplane
            }
        }
        true
    }
}
```

### Property-Based Testing with proptest

```rust
// packages/core/tests/parameter_tests.rs
use proptest::prelude::*;
use budget_citoyen_core::parameters::Parameters;
use budget_citoyen_core::types::Profile;

proptest! {
    /// Property: Any valid profile must pass validate() without error.
    #[test]
    fn valid_profiles_always_validate(
        age in 0u8..120,
        patrimoine in 0.0f64..10_000_000.0,
        revenu in 0.0f64..1_000_000.0,
    ) {
        let profile = Profile {
            profile_id: "test".into(),
            age,
            patrimoine,
            revenu_fiscal: revenu,
            situation_familiale: SituationFamiliale::Celibataire,
            nombre_parts: 1.0,
            type_activite: TypeActivite::Salarie,
        };
        assert!(profile.validate().is_ok());
    }

    /// Property: Negative values should always fail validation.
    #[test]
    fn negative_patrimoine_fails(patrimoine in f64::MIN..0.0) {
        let mut profile = valid_profile();
        profile.patrimoine = patrimoine;
        assert!(profile.validate().is_err());
    }
}
```

### Bilingual Validation Test (cargo test, NOT wasm-pack test)

```rust
// packages/core/tests/bilingual_tests.rs
// Consumes fixtures generated by Phase 1 export_fixtures.py
use serde::{Deserialize, Serialize};

#[derive(Deserialize)]
struct TestFixture {
    name: String,
    input: serde_json::Value,
    expected: ExpectedResults,
}

#[derive(Deserialize)]
struct ExpectedResults {
    ir: Option<f64>,
    cotisations_salariales: Option<f64>,
    csg_crds: Option<f64>,
    revenu_disponible: Option<f64>,
    // ... all expected outputs
}

#[derive(Deserialize)]
struct FixtureDoc {
    test_fixtures: Vec<TestFixture>,
    reference_year: u16,
}

const PRECISION: f64 = 1e-6;

#[test]
fn bilingual_validation_all_fixtures() {
    // include_str! bakes the fixture JSON into the test binary at compile time
    let doc: FixtureDoc = serde_json::from_str(include_str!(
        "../../data-pipeline/dist/bilingual_test_fixtures.json"
    )).expect("Failed to parse test fixtures");

    assert!(!doc.test_fixtures.is_empty(), "No test fixtures found");

    let params = Parameters::load_from_json(include_str!(
        "../../tax-rules/dist/parameters-v2025.1.json"
    )).unwrap();

    for fixture in &doc.test_fixtures {
        let profile: Profile = parse_profile_from_fixture(&fixture.input).unwrap();
        let result = compute_all_taxes(&params, &profile);

        // Compare each expected output with 1e-6 precision
        if let Some(expected_ir) = fixture.expected.ir {
            assert!(
                (result.ir - expected_ir).abs() < PRECISION * expected_ir.abs().max(1.0),
                "Fixture '{}': IR mismatch. Expected: {}, Got: {}",
                fixture.name, expected_ir, result.ir
            );
        }
        // ... repeat for all output fields
    }
}
```

### WASM Boundary Test (wasm-pack test)

```rust
// packages/wasm-micro/tests/wasm_boundary.rs
use wasm_bindgen_test::*;
use budget_citoyen_wasm_micro::MicroEngine;

wasm_bindgen_test_configure!(run_in_browser);

#[wasm_bindgen_test]
fn test_round_trip_simulation() {
    let engine = MicroEngine::new(
        include_str!("../../../tax-rules/dist/parameters-v2025.1.json"),
        include_str!("../../../data-pipeline/dist/population-v2025.1.json"),
    ).unwrap();

    // Build a flat params array matching the index mapping
    let params: Vec<f64> = vec![
        1.0, 1.0, 1.0, 1.0, 1.0,  // IR brackets (reference)
        1.0,  // IS rate (reference)
        1.0,  // TVA normal (reference)
        1.0,  // TVA reduced
        1.0,  // CSG deductible
        1.0,  // CRDS
        1.0,  // Cotisations salariales
        1.0,  // Cotisations patronales
        1.0,  // Spend level
        1.0,  // Effectifs État
    ];

    let result = engine.update_and_simulate(&params, 0);
    assert!(result.is_object(), "Result should be a JsValue object");

    // Verify the result has expected fields
    let ir = js_sys::Reflect::get(&result, &"ir".into()).unwrap();
    assert!(ir.as_f64().is_some(), "IR should be a number");
}
```

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Rust toolchain (rustup, rustc, cargo) | WASM compilation, cargo test | ✗ | — | **BLOCKING — must install**: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \| sh` |
| wasm32-unknown-unknown target | WASM compilation | ✗ | — | `rustup target add wasm32-unknown-unknown` |
| wasm-pack | WASM build toolchain | ✗ | — | `cargo install wasm-pack` or `npm install -g wasm-pack` |
| Node.js | CI, test runner (wasm-bindgen-test) | ✓ | v24.12.0 | — |
| npm | Package management | ✓ | 11.6.2 | — |
| Python 3.10+ | Code generator (data-pipeline) | ✓ (via Phase 1 venv) | 3.13 (in .venv) | — |
| openfisca-france | Code generator introspection | ✓ (in Phase 1 .venv) | >=159, <200 | Pin in pyproject.toml |
| Chromium (headless) | wasm-pack test | ✗ | — | `wasm-pack test` downloads its own chromedriver; `playwright install chromium` if using Playwright tests |

**Missing dependencies with no fallback (BLOCKING):**
- **Rust toolchain** — Required for all Rust compilation. Must be installed before any Phase 2 work.
- **wasm32-unknown-unknown target** — Required for WASM compilation target.
- **wasm-pack** — Required for `wasm-pack build --target web` and `wasm-pack test`.

**Missing dependencies with fallback:**
- None — all missing items are prerequisites with no viable alternatives.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | cargo test (native) + wasm-pack test (browser) + proptest 1.11.0 (property-based) |
| Config file | `Cargo.toml` per crate (no separate test config needed for Rust) |
| Quick run command | `cargo test -p budget-citoyen-core` (native, fast) |
| Full suite command | `cargo test --workspace && wasm-pack test --headless packages/wasm-micro packages/wasm-macro` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MICRO-01 | IR computation matches OpenFisca reference | integration | `cargo test -p budget-citoyen-core -- bilingual` | ❌ Wave 0 |
| MICRO-02 | IS, TVA, cotisations match reference | integration | `cargo test -p budget-citoyen-core -- bilingual` | ❌ Wave 0 |
| MICRO-03 | Aides sociales match reference | integration | `cargo test -p budget-citoyen-core -- bilingual` | ❌ Wave 0 |
| MICRO-04 | Zero network access from workers | architecture | Manual verification + CSP audit | ❌ Wave 0 |
| MICRO-05 | <200ms single-profile calculation | performance | `wasm-pack test` with performance assertion | ❌ Wave 0 |
| MACRO-01 | Deficit trajectory interpolation | unit | `cargo test -p budget-citoyen-core -- interpolation` | ❌ Wave 0 |
| MACRO-02 | Debt trajectory interpolation | unit | `cargo test -p budget-citoyen-core -- interpolation` | ❌ Wave 0 |
| MACRO-03 | GDP and employment projections | unit | `cargo test -p budget-citoyen-core -- interpolation` | ❌ Wave 0 |
| MACRO-04 | Macro interpolation < 50ms | performance | `wasm-pack test` with performance assertion | ❌ Wave 0 |
| MACRO-05 | Constant interest rates | unit | `cargo test -p budget-citoyen-core -- interpolation` — assert no rate variation code | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cargo test -p budget-citoyen-core` (native core tests, < 1s)
- **Per wave merge:** `cargo test --workspace && wasm-pack test --headless` (full suite)
- **Phase gate:** Full suite green + bilingual fixtures pass at ≤ 1e-6 precision

### Wave 0 Gaps
- [ ] `packages/core/Cargo.toml` — Crate initialization
- [ ] `packages/core/tests/bilingual_tests.rs` — Bilingual validation harness (loads Phase 1 fixtures)
- [ ] `packages/core/tests/parameter_tests.rs` — proptest property-based strategies
- [ ] `packages/core/tests/profile_tests.rs` — Profile validation edge cases
- [ ] `packages/wasm-micro/Cargo.toml` — WASM crate initialization
- [ ] `packages/wasm-micro/tests/wasm_boundary.rs` — JS↔WASM boundary tests
- [ ] `packages/wasm-macro/Cargo.toml` — WASM crate initialization
- [ ] `packages/wasm-macro/tests/interpolation_tests.rs` — In-bounds/out-of-bounds validation
- [ ] `packages/wasm-macro/tests/wasm_boundary.rs` — WASM boundary tests
- [ ] `Cargo.toml` — Workspace root
- [ ] `.github/workflows/phase2-wasm.yml` — CI workflow
- [ ] Rust toolchain installation verification script
- [ ] Pre-commit hook: `cargo fmt --check && cargo clippy -- -D warnings`

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Not applicable — no user accounts |
| V3 Session Management | no | Not applicable — no server-side sessions |
| V4 Access Control | no | Not applicable — all computation is local |
| V5 Input Validation | yes | `Profile::validate()` method (D-16); `&[f64]` bounds checking; convex hull containment check; JSON Schema validation at build time (Phase 1) |
| V6 Cryptography | no | Not applicable — no cryptographic operations in WASM engines |
| V7 Error Handling | yes | Panic hook returns controlled error, never dumps memory (PITFALLS.md Pitfall: WASM panic → memory leak); `Result<T, E>` for all fallible operations |

### Known Threat Patterns for WASM Client-Side Computation

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| WASM panic → linear memory dump in browser console | Information Disclosure | `console_error_panic_hook` in debug builds only; `std::panic::set_hook` in production returning controlled error code; never expose memory contents (PITFALLS.md) |
| Malicious profile JSON with extreme values causing infinite loops | Denial of Service | Strict `validate()` bounds (age 0-120, revenue caps, asset caps); `#[wasm_bindgen]` function timeout pattern; profile count limit |
| Deterministic profile ordering enabling session correlation | Information Disclosure | Randomize profile evaluation order (PITFALLS.md Pitfall 6) |
| Third-party dependency with telemetry in WASM build | Information Disclosure | Audit all crate dependencies; `cargo-deny` in CI; no `web_sys` network APIs in engine crates |
| Integer overflow in tax bracket calculations | Tampering | Rust's debug-mode overflow checks; `saturating_*` operations for financial calculations; proptest edge case coverage |

## Sources

### Primary (HIGH confidence)
- **crates.io API** — Version verification for all Rust crates (2026-05-12):
  - wasm-bindgen 0.2.121, serde 1.0.228, serde-wasm-bindgen 0.6.5, serde_json 1.0.149
  - ndarray 0.17.2, interpn 0.11.0, parquet2 0.17.2, ruzstd 0.8.3
  - proptest 1.11.0, wasm-bindgen-test 0.3.71, wasm-bindgen-rayon 1.3.0
- **npm registry** — wasm-pack 0.14.0, Vite 8.0.12, TypeScript 6.0.3, Vitest 4.1.6 (verified 2026-05-12)
- **docs.rs/interpn/0.11.0** — N-dimensional multilinear interpolation API, no-std compatibility, C-order array conventions
- **docs.rs/ndarray-interp/0.6.0** — Confirmed limited to 1D/2D (unsuitable for N-dimensional shock matrix)
- **docs.rs/interpolation/0.3.0** — Confirmed animation easing only (Ease, Lerp, cubic_bezier) — not grid interpolation
- **docs.rs/parquet2/0.17.2** — Parquet reading API, feature flags, compression backends
- **Project Phase 1 artifacts** (`export_fixtures.py`, `canonical_profiles.py`, `reference_sim.py`, `convex_hull.py`, `grid_build.py`, `export_parquet.py`, phase1-validate.yml) — Validated data contracts consumed by Phase 2
- **02-CONTEXT.md** — 16 locked decisions (D-01 through D-16) constraining implementation

### Secondary (MEDIUM confidence)
- **STACK.md (project)** — Technology stack recommendations (with correction needed for `interpolation` crate)
- **ARCHITECTURE.md (project)** — System architecture, Web Worker isolation, data flow patterns
- **PITFALLS.md (project)** — Verified pitfall prevention strategies (Pitfalls 1, 2, 8 most relevant to Phase 2)
- **crates.io API metadata** — Feature flag details for parquet2 (zstd, gzip, snappy backends)

### Tertiary (LOW confidence)
- [CITED: parquet2 GitHub] — General approach to reading Parquet files; WASM-specific zstd compilation not tested
- [ASSUMED] `zstd` C binding v0.13.3 may fail WASM compilation — verified that `ruzstd` 0.8.3 exists as pure-Rust alternative, but not yet tested in a WASM build

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `interpn 0.11.0` is the correct replacement for `interpolation 0.3.0` — verified via docs.rs showing N-dimensional multilinear API suitable for shock matrix | Standard Stack (Correction) | LOW — docs.rs and crates.io both confirm N-dimensional interpolation capability; `interpn` is specifically designed for scientific grid interpolation |
| A2 | `parquet2` with zstd feature may not compile to WASM; `ruzstd` 0.8.3 or gzip compression are viable fallbacks | Standard Stack (Parquet/WASM note) | MEDIUM — if zstd DOES compile to WASM, the concern is overstated; early spike will resolve definitively |
| A3 | Phase 1's `bilingual_test_fixtures.json` has the expected structure (test_fixtures array with name, input, expected fields) — confirmed by reading `export_fixtures.py` | Code Examples (Bilingual Validation) | LOW — the fixture format is controlled by project code, not an external dependency |
| A4 | `openfisca-france >=159,<200` in pyproject.toml provides access to all ~200+ variable definitions needed by the code generator | Code Generator Architecture | MEDIUM — some variables may use Python-specific constructs (dynamic dispatch, closures) that are harder to translate; spike of 3-5 representative formulas should validate |
| A5 | COOP/COEP headers are NOT required for Phase 2 single-threaded WASM — only needed for `wasm-bindgen-rayon` with `SharedArrayBuffer` (deferred to Phase 4) | Architecture Patterns | LOW — single-threaded WASM works without COOP/COEP on all modern browsers |

## Open Questions (RESOLVED)

1. **Parquet/Zstd in WASM — Spike needed** **(RESOLVED — Plan 02-01 Task 3: Parquet/WASM loading spike tests all 3 options [postcard+gzip, parquet2+gzip, ruzstd+parquet2] and documents the chosen strategy in packages/wasm-macro/README.md)**
   - What we know: `parquet2 0.17.2` has zstd support via C-binding; `ruzstd 0.8.3` is pure-Rust zstd decoder; `flate2/rust_backend` is pure-Rust gzip
   - What's unclear: Does `parquet2` with `default-features = false, features = ["gzip"]` compile and work under `wasm32-unknown-unknown`? Does the zstd feature work with the `wasm32-unknown-unknown` target?
   - Recommendation: Spike as the **first task** in Wave 0. Test all three approaches (parquet2+gzip, parquet2+zstd, ruzstd+parquet2) with a small test Parquet file. If none work, fall back to flat binary format (postcard + gzip HTTP).

2. **Code Generator Feasibility — Representative formula spike** **(RESOLVED — Plan 02-04 Task 1: Spike validates 3-5 representative formulas [TVA simple, IR bracket-based, RSA cross-entity, APL multi-condition, décote conditional] with documented findings in SPIKE_RESULTS.md before scaling to full ~200+ variable tree)**
   - What we know: OpenFisca-France has ~200+ variables; code generator must resolve entity hierarchy into flat Profile struct
   - What's unclear: Can the Python introspection API produce correct Rust code for all formula patterns? Which formulas require manual porting?
   - Recommendation: Spike 3-5 representative formulas (one simple: TVA, one complex: IR with quotient familial, one with cross-entity: RSA, one with period handling: PLF updates) before scaling to full variable tree.

3. **Profile struct field count — Code generator output size** **(RESOLVED — Deferred review after codegen spike [Plan 02-04 Task 2]. Profile struct size bounded at ~50-80 leaf input variables per OpenFisca-France entity hierarchy. Acceptable for single-profile WASM linear memory. No serialization performance concern with serde-wasm-bindgen JsValue bridge per D-10.)**
   - What we know: OpenFisca's entity hierarchy (Individu, Famille, FoyerFiscal, Menage) has ~50+ input variables; D-13 mandates flattening
   - What's unclear: Will the resulting flat Profile struct have >100 fields? Does this impact WASM linear memory or serialization performance?
   - Recommendation: Profile struct size is bounded by OpenFisca's leaf input variables (~50-80 fields). Acceptable for single-profile storage. Review after code generator spike.

4. **Index mapping documentation — Shared Rust/TypeScript constant module** **(RESOLVED — Plan 02-08 Task 1: index-map.ts [TypeScript PARAM_INDICES const object with 14+ entries and NUM_SIMULATION_PARAMS=16]. Rust counterpart at packages/wasm-micro/src/simulation.rs [pub const NUM_SIMULATION_PARAMS: usize = 16]. Both kept in sync via shared documentation comment referencing the authoritative definition source.)**
   - What we know: D-09 requires flat `&[f64]` input; the agent determines exact index mapping
   - What's unclear: Should index constants be a hand-maintained file or code-generated alongside the parameter list?
   - Recommendation: Code-generate the index mapping as both a Rust `const` module and a TypeScript `const` object from the same source (the parameter definition order). Ensures Rust and TS stay in sync.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| OpenFisca Python runtime (server-side) | Rust/WASM compiled for client-side execution | Phase 2 design (per PRD) | Enables privacy-by-design; eliminates server compute costs |
| `interpolation 0.3.0` (animation easing) | `interpn 0.11.0` (N-dimensional grid interpolation) | This research (2026-05-12) | Correct crate for shock matrix; wasm-compatible (no-std, no-alloc) |
| Manual formula porting (error-prone) | Automated code generation from OpenFisca variable graph | D-05 | Eliminates manual porting errors; ~200+ formulas generated consistently |
| Monolithic WASM crate | Core/wasm split (3 crates, cargo workspace) | D-01, D-02 | Enables fast `cargo test` without browser; prevents untestable logic |
| Structured input crossing WASM boundary per slider | Flat `&[f64]` slice batch interface | D-09 | Eliminates serialization overhead; achieves <200ms latency target |

**Deprecated/outdated:**
- `serde_yaml 0.9.34` — deprecated March 2024. Phase 2 avoids YAML entirely at WASM runtime (consumes JSON from Phase 1 build step).
- `interpolation 0.3.0` — NOT deprecated, but wrong tool for N-dimensional grid interpolation. Replace with `interpn 0.11.0`.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all crate versions verified via crates.io API and npm registry (2026-05-12). `interpn` substitution confirmed via docs.rs.
- Architecture: HIGH — 16 locked decisions from CONTEXT.md provide detailed implementation constraints. Patterns validated against PITFALLS.md prevention strategies.
- Pitfalls: HIGH — PITFALLS.md research cross-referenced; Phase 2-specific Parquet/WASM risk identified from crate dependency analysis.

**Research date:** 2026-05-12
**Valid until:** 2026-06-12 (30 days — stable Rust/WASM ecosystem; `interpn` and `parquet2` are mature crates with infrequent major releases)
