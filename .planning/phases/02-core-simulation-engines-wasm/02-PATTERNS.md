# Phase 02: Core Simulation Engines (WASM) - Pattern Map

**Mapped:** 2026-05-12
**Files analyzed:** 32 (to be created) + 3 (modified/consumed)
**Analogs found:** 16 / 32 (50% from codebase; remaining from RESEARCH.md code examples)

## File Classification

| New File | Role | Data Flow | Closest Analog | Match Quality |
|----------|------|-----------|----------------|---------------|
| `Cargo.toml` (root) | config | N/A (build infra) | `packages/data-pipeline/pyproject.toml` | structural-match |
| `packages/core/Cargo.toml` | config | N/A | `packages/data-pipeline/pyproject.toml` | structural-match |
| `packages/core/src/lib.rs` | module-root | N/A | RESEARCH.md Pattern 3 (lines 480-525) | research-pattern |
| `packages/core/src/types.rs` | model | data-holding | `packages/data-pipeline/src/validation/canonical_profiles.py` (data model pattern) | role-match |
| `packages/core/src/parameters.rs` | utility | data-loading | `packages/data-pipeline/src/yaml2json/convert.py` (load+parse) | role-match |
| `packages/core/src/profiles.rs` | utility | data-loading | `packages/data-pipeline/src/synthetic_pop/export.py` (validation pattern) | role-match |
| `packages/core/src/test_fixtures.rs` | utility | data-loading | `packages/data-pipeline/src/validation/export_fixtures.py` | exact-pattern |
| `packages/core/tests/parameter_tests.rs` | test | CRUD | `packages/data-pipeline/tests/test_validation.py` + RESEARCH.md proptest (lines 687-721) | role-match |
| `packages/core/tests/profile_tests.rs` | test | CRUD | `packages/data-pipeline/tests/test_validation.py` + RESEARCH.md proptest (lines 687-721) | role-match |
| `packages/wasm-micro/Cargo.toml` | config | N/A | `packages/data-pipeline/pyproject.toml` + RESEARCH.md (lines 159-178) | structural-match |
| `packages/wasm-micro/src/lib.rs` | controller | request-response (WASM boundary) | RESEARCH.md Pattern 1 (lines 371-380) | research-pattern |
| `packages/wasm-micro/src/system.rs` | service | CRUD | RESEARCH.md Pattern 3 (lines 476-525) | research-pattern |
| `packages/wasm-micro/src/simulation.rs` | service | CRUD | RESEARCH.md Pattern 1 (lines 329-369) | research-pattern |
| `packages/wasm-micro/src/generated/mod.rs` | auto-generated | N/A | N/A (codegen output — not hand-authored) | no-analog |
| `packages/wasm-micro/src/generated/ir.rs` | auto-generated | N/A | N/A (codegen output) | no-analog |
| `packages/wasm-micro/src/generated/is.rs` | auto-generated | N/A | N/A (codegen output) | no-analog |
| `packages/wasm-micro/src/generated/tva.rs` | auto-generated | N/A | N/A (codegen output) | no-analog |
| `packages/wasm-micro/src/generated/cotisations.rs` | auto-generated | N/A | N/A (codegen output) | no-analog |
| `packages/wasm-micro/src/generated/aides.rs` | auto-generated | N/A | N/A (codegen output) | no-analog |
| `packages/wasm-micro/tests/wasm_boundary.rs` | test | request-response (WASM) | RESEARCH.md WASM boundary test (lines 786-821) | research-pattern |
| `packages/wasm-micro/tests/bilingual.rs` | test | CRUD | `packages/data-pipeline/tests/test_validation.py` + RESEARCH.md bilingual (lines 725-782) | role-match |
| `packages/wasm-macro/Cargo.toml` | config | N/A | `packages/data-pipeline/pyproject.toml` + RESEARCH.md (lines 181-204) | structural-match |
| `packages/wasm-macro/src/lib.rs` | controller | request-response (WASM boundary) | RESEARCH.md Pattern 1 (lines 371-380) | research-pattern |
| `packages/wasm-macro/src/matrix.rs` | service | data-loading | `packages/data-pipeline/src/shock_matrix/export_parquet.py` (deserialize reverse) | role-match |
| `packages/wasm-macro/src/interpolate.rs` | service | transform | RESEARCH.md interpolation (lines 613-682) | research-pattern |
| `packages/wasm-macro/src/projection.rs` | utility | transform | RESEARCH.md code examples (lines 517-524 — MacroResult trajectory) | partial-analog |
| `packages/wasm-macro/tests/wasm_boundary.rs` | test | request-response (WASM) | RESEARCH.md WASM boundary test (lines 786-821) | research-pattern |
| `packages/wasm-macro/tests/interpolation_tests.rs` | test | transform | `packages/data-pipeline/tests/test_shock_matrix.py` + RESEARCH.md interpolation (lines 613-682) | role-match |
| `.github/workflows/phase2-wasm.yml` | config | N/A (CI pipeline) | `.github/workflows/phase1-validate.yml` | exact-match |
| `packages/data-pipeline/src/codegen/generate_rust.py` | utility | transform (Python→Rust codegen) | `packages/data-pipeline/src/validation/export_fixtures.py` (export + structured doc pattern) | role-match |
| `webapp/src/workers/micro-worker.ts` | controller/service | event-driven | RESEARCH.md Pattern 2 (lines 413-473) | research-pattern |
| `webapp/src/workers/macro-worker.ts` | controller/service | event-driven | RESEARCH.md Pattern 2 (lines 413-473) | research-pattern |
| `webapp/src/workers/orchestrator.ts` | controller | event-driven | RESEARCH.md Pattern 2 (lines 413-473) | research-pattern |
| `webapp/src/workers/index-map.ts` | config | N/A (shared constants) | RESEARCH.md Pattern 1 TypeScript side (lines 383-411) | research-pattern |

---

## Pattern Assignments

### `Cargo.toml` (workspace root) — config

**Analog:** `packages/data-pipeline/pyproject.toml`

**Cargo workspace pattern** (from RESEARCH.md lines 206-215):
```toml
[workspace]
members = [
    "packages/core",
    "packages/wasm-micro",
    "packages/wasm-macro",
]
resolver = "2"
```

**Naming convention** (from `pyproject.toml` line 2):
- Package names: `budget-citoyen-data-pipeline` → `budget-citoyen-core`, `budget-citoyen-wasm-micro`, `budget-citoyen-wasm-macro`
- Edition: "2021" (modern Rust)

---

### `packages/core/Cargo.toml` — config

**Analog:** `packages/data-pipeline/pyproject.toml` (dependency version pinning pattern)

**Version pinning pattern** (from `pyproject.toml` lines 9-22):
```toml
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

**Key conventions from pyproject.toml:**
- `>=X,<Y` version ranges (`pyproject.toml` lines 10-22) → Rust equivalent: `"1.0"` (caret requirement, equivalent to `>=1.0.0,<2.0.0`)
- Optional dev dependencies (`pyproject.toml` lines 24-29) → `[dev-dependencies]` section
- No WASM dependencies allowed in core crate (D-02 mandate)

---

### `packages/core/src/types.rs` — model

**Analog:** `packages/data-pipeline/src/validation/canonical_profiles.py` (typed data structure definition)

**Data model pattern** (from `canonical_profiles.py` lines 19-41 — typed dicts with required fields):
```python
# Python analog: every profile is a typed dict with required keys
{
    "name": "celibataire_smic",
    "situation_familiale": "celibataire",
    "nb_enfants": 0,
    "revenus": { "salaires": [18801.0], "pensions": [], ... },
    "patrimoine": { "immobilier": 0.0, "financier": 0.0 },
}
```

**Rust translation pattern** (from RESEARCH.md lines 480-525):
```rust
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
    // Additional codegen-derived fields
}

impl Profile {
    pub fn validate(&self) -> Result<(), LoadError> {
        if self.age > 120 { return Err(LoadError::InvalidAge(self.age)); }
        if self.patrimoine < 0.0 { return Err(LoadError::NegativeWealth); }
        // ... further validation
        Ok(())
    }
}
```

**Validation pattern** (from `export_fixtures.py` lines 136-139 — required key checking):
```python
for key in ("test_fixtures", "reference_year", "generated_at"):
    if key not in doc:
        raise ValueError(f"Missing required key '{key}' in fixture file")
```
→ Rust equivalent: `validate()` method returning `Result<T, LoadError>` with explicit field checks.

---

### `packages/core/src/parameters.rs` — utility

**Analog:** `packages/data-pipeline/src/yaml2json/convert.py` (loading + format conversion)

**Loading pattern** (from `convert.py` lines 57-69):
```python
with open(yaml_path, "r", encoding="utf-8") as f:
    try:
        data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"YAML parse error in {yaml_path}: {e}") from e
if data is None:
    raise ValueError(f"Empty YAML file: {yaml_path}")
```

**Rust equivalent** (parameter tree loading from JSON):
- Use `serde_json::from_str` for JSON deserialization
- `BTreeMap<Date, Value>` for date-based parameter lookup
- Date resolution: closest past date (OpenFisca semantics)
- Error type: custom enum with variant per failure mode

---

### `packages/core/src/profiles.rs` — utility

**Analog:** `packages/data-pipeline/src/synthetic_pop/export.py` (validation + batch processing)

**Batch validation pattern** (from `export.py` lines 70-78):
```python
num_profiles = len(synthetic_df)
if num_profiles != 50_000:
    msg = f"Exporting {num_profiles} profiles instead of 50,000."
    logger.warning(msg)
```

**Rust equivalent** (D-16: strict load-time validation):
- `Vec<Profile>` deserialized via serde
- Each profile passes `validate()` method
- Invalid profiles: counted and rejected, never silently loaded
- Returns `Result<Vec<Profile>, LoadError>` with error statistics

---

### `packages/core/src/test_fixtures.rs` — utility

**Analog:** `packages/data-pipeline/src/validation/export_fixtures.py` (fixture loading + format contract)

**Fixture loading pattern** (from `export_fixtures.py` lines 116-141):
```python
def load_test_fixtures(fixture_path: str) -> Dict[str, Any]:
    path = Path(fixture_path)
    if not path.exists():
        raise FileNotFoundError(f"Fixture file not found: {fixture_path}")
    with open(path, "r", encoding="utf-8") as f:
        doc = _json.load(f)
    # Validate required keys
    for key in ("test_fixtures", "reference_year", "generated_at"):
        if key not in doc:
            raise ValueError(f"Missing required key '{key}' in fixture file")
    return doc
```

**Rust equivalent** (from RESEARCH.md lines 754-781):
```rust
const PRECISION: f64 = 1e-6;

#[test]
fn bilingual_validation_all_fixtures() {
    let doc: FixtureDoc = serde_json::from_str(include_str!(
        "../../data-pipeline/dist/bilingual_test_fixtures.json"
    )).expect("Failed to parse test fixtures");
    
    assert!(!doc.test_fixtures.is_empty(), "No test fixtures found");
    
    for fixture in &doc.test_fixtures {
        let profile: Profile = parse_profile_from_fixture(&fixture.input).unwrap();
        let result = compute_all_taxes(&params, &profile);
        // Compare with 1e-6 precision
        if let Some(expected_ir) = fixture.expected.ir {
            assert!((result.ir - expected_ir).abs() < PRECISION * expected_ir.abs().max(1.0));
        }
    }
}
```

**Key convention:** `include_str!()` embeds fixture JSON at compile time. Path is relative to crate root (`../../data-pipeline/dist/`).

---

### `packages/core/tests/parameter_tests.rs` and `profile_tests.rs` — tests

**Analog:** `packages/data-pipeline/tests/test_validation.py` (test class structure + assert patterns)

**Test structure pattern** (from `test_validation.py` lines 16-66):
```python
class TestCanonicalProfiles:
    def test_profile_count_at_least_thirty(self):
        from validation.canonical_profiles import CANONICAL_PROFILES
        count = len(CANONICAL_PROFILES)
        assert count >= 30, f"Expected at least 30 canonical profiles, got {count}"

    def test_all_profiles_have_required_fields(self):
        required_fields = ["name", "description", "situation_familiale", "revenus"]
        for profile in CANONICAL_PROFILES:
            for field in required_fields:
                assert field in profile, f"Profile '{name}' is missing '{field}'"
```

**Rust proptest pattern** (from RESEARCH.md lines 687-721):
```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn valid_profiles_always_validate(
        age in 0u8..120,
        patrimoine in 0.0f64..10_000_000.0,
        revenu in 0.0f64..1_000_000.0,
    ) {
        let profile = Profile { age, patrimoine, revenu_fiscal: revenu, .. };
        assert!(profile.validate().is_ok());
    }
}
```

**Key conventions:**
- `proptest!` macro with inline strategy definitions
- Test file naming: `{domain}_tests.rs`
- Assertive test names describing the property being tested
- Native `cargo test` only (no WASM deps in core test files)

---

### `packages/wasm-micro/Cargo.toml` — config

**Analog:** `packages/data-pipeline/pyproject.toml` (version pinning)

**Crate config pattern** (from RESEARCH.md lines 159-178):
```toml
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

**Key patterns:**
- `crate-type = ["cdylib", "rlib"]` — required for WASM + native testing
- `path = "../core"` — workspace-local dependency (D-02)
- `wasm-bindgen-test` only in dev-dependencies

---

### `packages/wasm-micro/src/lib.rs` — controller (WASM boundary)

**Analog:** RESEARCH.md Pattern 1 (lines 371-380)

**WASM export pattern:**
```rust
use wasm_bindgen::prelude::*;
use serde_wasm_bindgen;

#[wasm_bindgen]
pub struct MicroEngine {
    state: SimulationState,
    profiles: Vec<Profile>,
}

#[wasm_bindgen]
impl MicroEngine {
    #[wasm_bindgen(constructor)]
    pub fn new(params_json: &str, population_json: &str) -> Result<MicroEngine, JsValue> {
        // D-12: All data loaded via main thread transfer, arrives as JSON strings at init
        let params = serde_json::from_str(params_json).map_err(|e| JsValue::from_str(&e.to_string()))?;
        let profiles = serde_json::from_str(population_json).map_err(|e| JsValue::from_str(&e.to_string()))?;
        Ok(MicroEngine { state: SimulationState::new(params), profiles })
    }

    pub fn update_and_simulate(&mut self, params: &[f64], profile_index: usize) -> JsValue {
        self.state.update_params(params).map_err(|e| JsValue::from_str(e))?;
        let result = self.state.compute_for_profile(&self.profiles[profile_index]);
        serde_wasm_bindgen::to_value(&result).unwrap()
    }
}
```

**Key WASM patterns:**
- `#[wasm_bindgen]` on struct and impl block
- `#[wasm_bindgen(constructor)]` on `new()`
- Returns `JsValue` for structured outputs via `serde-wasm-bindgen`
- Returns `Result<T, JsValue>` for fallible operations
- Input as `&[f64]` slice (flat array, D-09) — zero serialization
- String inputs for initialization data (loaded once at startup)

---

### `packages/wasm-micro/src/system.rs` — service

**Analog:** RESEARCH.md Pattern 3 (lines 476-525)

**TaxBenefitSystem pattern:**
```rust
pub struct TaxBenefitSystem {
    parameters: Parameters,
    // No wasm_bindgen imports allowed (D-02)
}

impl TaxBenefitSystem {
    pub fn new(parameters: Parameters) -> Self {
        TaxBenefitSystem { parameters }
    }

    pub fn compute_all_taxes(&self, profile: &Profile) -> MicroResult {
        let ir = calculate_ir(&self.parameters, &profile);
        let cotisations = calculate_cotisations(&self.parameters, &profile);
        let aides = calculate_aides(&self.parameters, &profile);
        // ...
        MicroResult { ir, cotisations_salariales: cotisations, aides, revenu_disponible, .. }
    }
}
```

**Key pattern:** Core-only dependencies. No `wasm_bindgen`. All business logic testable via `cargo test`.

---

### `packages/wasm-micro/src/simulation.rs` — service

**Analog:** RESEARCH.md Pattern 1 (lines 329-369)

**SimulationState pattern (flat `&[f64]` input):**
```rust
pub const NUM_SIMULATION_PARAMS: usize = 16;

pub struct SimulationState {
    params: [f64; NUM_SIMULATION_PARAMS],
    // cached computed values
}

impl SimulationState {
    pub fn update_params(&mut self, input: &[f64]) -> Result<(), &'static str> {
        if input.len() != NUM_SIMULATION_PARAMS {
            return Err("Input slice length mismatch");
        }
        self.params.copy_from_slice(input);
        self.validate_bounds()?;
        self.recompute()
    }
}
```

---

### `packages/wasm-micro/src/generated/*.rs` — auto-generated

**No analog** — these files are produced by the code generator, not hand-authored. The pattern is:
```rust
// AUTO-GENERATED by codegen. DO NOT EDIT.
// Source: openfisca-france v{version}
// Generated: {timestamp}

use budget_citoyen_core::types::{Profile, Parameters, Date};

pub fn calculate_ir(parameters: &Parameters, period: Date, profile: &Profile) -> f64 {
    // Generated formula implementation
    // Pattern: pure function, typed inputs, match on period
}
```

---

### `packages/wasm-micro/tests/wasm_boundary.rs` — test

**Analog:** RESEARCH.md lines 786-821

**WASM boundary test pattern:**
```rust
use wasm_bindgen_test::*;
wasm_bindgen_test_configure!(run_in_browser);

#[wasm_bindgen_test]
fn test_round_trip_simulation() {
    let engine = MicroEngine::new(
        include_str!("../../../tax-rules/dist/parameters-v2025.1.json"),
        include_str!("../../../data-pipeline/dist/population-v2025.1.json"),
    ).unwrap();
    
    let params: Vec<f64> = vec![1.0; 16]; // reference values
    let result = engine.update_and_simulate(&params, 0);
    assert!(result.is_object());
}
```

---

### `packages/wasm-micro/tests/bilingual.rs` — test (bilingual validation)

**Analog:** `packages/data-pipeline/tests/test_validation.py` (structured assertions on named profiles)

**Bilingual pattern** (from RESEARCH.md lines 725-782):
```rust
#[test]
fn bilingual_validation_all_fixtures() {
    let doc: FixtureDoc = serde_json::from_str(include_str!(
        "../../data-pipeline/dist/bilingual_test_fixtures.json"
    )).expect("Failed to parse test fixtures");
    // Iterate fixtures, compare Rust output vs Python expected with <=1e-6 tolerance
}
```

---

### `packages/wasm-macro/Cargo.toml` — config

**Same pattern as `wasm-micro/Cargo.toml`**, with additional deps:
```toml
[dependencies]
ndarray = "0.17"
interpn = "0.11"
# parquet2 = { version = "0.17", default-features = false, features = ["gzip"] }  # TBD after spike
```
(From RESEARCH.md lines 190-201)

---

### `packages/wasm-macro/src/matrix.rs` — service

**Analog:** `packages/data-pipeline/src/shock_matrix/export_parquet.py` (deserialize is the reverse of export)

**Data loading pattern** (reverse of `export_parquet.py` lines 50-174):
- `export_parquet.py` writes: Parquet/Zstd with breakpoints, convex hull, grid shape
- `matrix.rs` reads: Same structure, validates `version == "shockmatrix-v2025.1"`

```rust
pub struct ShockMatrix {
    tax_bp: Vec<f64>,
    spend_bp: Vec<f64>,
    horizon_bp: Vec<f64>,
    grid: Vec<f64>,          // C-order flattened 4D grid
    hull_equations: Vec<Vec<f64>>,
}
```

---

### `packages/wasm-macro/src/interpolate.rs` — service

**Analog:** RESEARCH.md lines 613-682

**Interpolation pattern:**
```rust
use interpn::multilinear::rectilinear;

impl ShockMatrix {
    pub fn interpolate(&self, tax: f64, spend: f64, horizon: f64) -> Option<MacroResult> {
        // 1. Check convex hull containment (Pitfall 2 prevention)
        let point = [tax, spend, horizon];
        if !self.is_inside_hull(&point) {
            return None;
        }
        
        // 2. Perform multilinear interpolation
        let grids = &[&self.tax_bp[..], &self.spend_bp[..], &self.horizon_bp[..]];
        let obs = [&point[..]];
        let mut out = [0.0_f64; 4];
        rectilinear::interpn(grids, &self.grid, &obs, &mut out)
            .expect("interpolation should succeed for in-bounds inputs");
        
        Some(MacroResult {
            gdp_growth: out[0],
            employment_change: out[1],
            deficit_change: out[2],
            debt_to_gdp_ratio: out[3],
            is_out_of_bounds: false,
            warning_message: None,
        })
    }
}
```

**Key patterns:**
- Convex hull check BEFORE interpolation (Pitfall 2)
- Returns `Option<MacroResult>` — `None` for out-of-bounds (never silent extrapolation)
- 4 output variables: GDP growth, employment change, deficit change, debt/GDP ratio

---

### `packages/wasm-macro/src/projection.rs` — utility

**Analog:** RESEARCH.md lines 517-524 (MacroResult trajectory structure)

**Trajectory projection pattern:**
```rust
pub fn project_trajectory(matrix: &ShockMatrix, tax: f64, spend: f64, horizon_years: usize) -> MacroResult {
    let mut gdp_traj = Vec::with_capacity(horizon_years);
    let mut debt_traj = Vec::with_capacity(horizon_years);
    // For each horizon year, call matrix.interpolate(tax, spend, year)
    // Accumulate trajectories
    MacroResult {
        deficit_trajectory,
        debt_trajectory,
        gdp_growth_trajectory,
        employment_trajectory,
        is_out_of_bounds: false,
        warning_message: None,
    }
}
```

---

### `packages/wasm-macro/tests/interpolation_tests.rs` — test

**Analog:** `packages/data-pipeline/tests/test_shock_matrix.py` (grid validation tests)

**Test pattern** (mirroring `test_validation.py` structure):
```rust
#[test]
fn interpolation_within_hull_returns_value() {
    // In-bounds point must return Some
    let result = matrix.interpolate(1.0, 1.0, 2.0);
    assert!(result.is_some());
}

#[test]
fn extrapolation_outside_hull_returns_none() {
    // Out-of-bounds point must return None (never silent extrapolation)
    let result = matrix.interpolate(5.0, 5.0, 10.0);
    assert!(result.is_none());
}
```

---

### `.github/workflows/phase2-wasm.yml` — config (CI)

**Analog:** `.github/workflows/phase1-validate.yml` (exact structural pattern)

**CI workflow pattern** (from `phase1-validate.yml` lines 22-387):

Key structural conventions to copy:
```yaml
name: Phase 2 — WASM Engine CI

on:
  push:
    branches: ['**']
  pull_request:
    branches: [main]
  workflow_dispatch:

env:
  PYTHON_VERSION: '3.10'

jobs:
  # ── Setup job ──
  setup:
    name: Rust Setup
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install Rust toolchain
        run: |
          rustup target add wasm32-unknown-unknown
          cargo install wasm-pack
      - name: Verify installation
        run: |
          rustc --version
          wasm-pack --version

  # ── Individual test jobs ──
  cargo-test-core:
    name: Core Crate Tests (native)
    runs-on: ubuntu-latest
    needs: [setup]
    steps:
      - uses: actions/checkout@v4
      - name: Run cargo test
        run: cargo test -p budget-citoyen-core

  # ── Final gate job ──
  ci-summary:
    name: CI Gate Summary
    needs: [cargo-test-core, wasm-test-micro, wasm-test-macro, ...]
    if: always()
    steps:
      - name: Check all required jobs
        run: |
          # Gate logic: all jobs must pass
```

**Key CI patterns from phase1-validate.yml:**
1. `name: Phase N — Description` header with detailed comments (lines 1-21)
2. `on: push/pull_request/workflow_dispatch` (lines 24-29)
3. `env:` for version constants (line 32)
4. Jobs structured as `{domain}-{action}` with `needs` for dependency ordering
5. Version consistency gates using grep-based checks (lines 122-166)
6. Final summary gate job with `needs: [...]` and `if: always()` (lines 355-387)
7. `echo "::error::..."` for GitHub Actions annotations (line 135)

**Phase 2 specific additions:**
- `cargo test -p budget-citoyen-core` (native, fast)
- `cargo test --workspace` (all native tests)
- `wasm-pack test --headless packages/wasm-micro` (browser context)
- `wasm-pack test --headless packages/wasm-macro` (browser context)
- Version-gate: OpenFisca-France staleness check (soft warning, D-07)
- Phase 1 prerequisite: `phase1-validate.yml` must pass first (D-04)

---

### `packages/data-pipeline/src/codegen/generate_rust.py` — utility (code generator)

**Analog:** `packages/data-pipeline/src/validation/export_fixtures.py` (Python script with structured output + error handling)

**Pattern to copy** (from `export_fixtures.py` lines 1-113):

1. **Module docstring** (lines 1-21): Description of purpose, output format, integration points
2. **Imports at top** (lines 22-28): Standard lib + project imports
3. **Function with explicit Args/Returns/Raises** (lines 30-53): Google-style docstrings
4. **Directory creation** (lines 53-55): `Path(output_dir).mkdir(parents=True, exist_ok=True)`
5. **Structured output** (lines 99-106): Build a typed document, serialize, write
6. **Error handling** (lines 50-51): Explicit exception types with clear messages

**Code generator specific pattern:**
```python
"""Code generator: OpenFisca-France Python → Rust/WASM.

Introspects the openfisca_france variable graph and generates:
  - Rust formula modules (one per tax domain)
  - Flat Profile struct definition  
  - Index mapping constants (shared Rust/TypeScript)

Output writes to packages/wasm-micro/src/generated/
"""

import datetime as _datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from openfisca_france import FranceTaxBenefitSystem


def generate_rust_formulas(
    output_dir: str,
    openfisca_version: str,
) -> Dict[str, int]:
    """Generate Rust source files from OpenFisca-France formulas.
    
    Args:
        output_dir: Path to packages/wasm-micro/src/generated/
        openfisca_version: Pinned openfisca-france version string.
    
    Returns:
        Dict mapping module name to number of generated functions.
    
    Raises:
        ImportError: If openfisca_france is not installed.
        OSError: If output directory cannot be created.
    """
    tax_benefit_system = FranceTaxBenefitSystem()
    variables = tax_benefit_system.variables
    
    # Topological sort of variable dependency graph (D-08)
    ordered_vars = _topological_sort(variables)
    
    # Group by tax domain
    domains = _group_by_domain(ordered_vars)
    
    # Generate one module per domain
    generated = {}
    for domain, vars in domains.items():
        module_path = Path(output_dir) / f"{domain}.rs"
        count = _write_module(module_path, domain, vars)
        generated[domain] = count
    
    return generated
```

**Key conventions from Phase 1 Python code:**
- `_` prefix for private helper functions (`export_fixtures.py` imports with `as _datetime`)
- Path handling via `pathlib.Path` (not `os.path`)
- Encoding: `utf-8` explicitly
- JSON output: `indent=2, ensure_ascii=False`
- Docstrings with Args/Returns/Raises sections

---

### `webapp/src/workers/index-map.ts` — config (shared constants)

**Analog:** RESEARCH.md Pattern 1 TypeScript side (lines 383-411)

```typescript
// webapp/src/workers/index-map.ts
// Shared with Rust: packages/wasm-micro/src/simulation.rs
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

export const NUM_SIMULATION_PARAMS = 16;
```

---

### `webapp/src/workers/orchestrator.ts` — controller

**Analog:** RESEARCH.md Pattern 2 (lines 413-473)

**Worker orchestration pattern:**
```typescript
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
    this.microWorker = new Worker(
      new URL('./micro-worker.ts', import.meta.url),
      { type: 'module' }
    );
    this.macroWorker = new Worker(
      new URL('./macro-worker.ts', import.meta.url),
      { type: 'module' }
    );
    this.microWorker.onmessage = (e) => this.handleResponse(e.data, 'micro');
    this.macroWorker.onmessage = (e) => this.handleResponse(e.data, 'macro');
  }

  private handleResponse(response: WorkerResponse, source: 'micro' | 'macro') {
    const latest = source === 'micro' ? this.latestMicroId : this.latestMacroId;
    // Discard stale responses (D-11)
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

**Key patterns:**
- `import.meta.url` for Worker constructor (Vite-compatible)
- `{ type: 'module' }` for ES module Workers
- Discriminated union types (`'SIMULATE' | 'INTERPOLATE' | 'INIT'`)
- Correlation IDs via `crypto.randomUUID()` (D-11)
- Stale response discarding (D-11)
- `Promise` wrapper for request/response pairing

---

### `webapp/src/workers/micro-worker.ts` — controller/service

**Analog:** RESEARCH.md Pattern 2 (request handling side)

```typescript
// webapp/src/workers/micro-worker.ts
import init, { MicroEngine } from '../../wasm-micro/pkg';

let engine: MicroEngine | null = null;

self.onmessage = async (e: MessageEvent) => {
  const { id, type, payload } = e.data;
  
  switch (type) {
    case 'INIT': {
      await init(); // Initialize WASM
      engine = MicroEngine.new(payload.paramsJson, payload.populationJson);
      self.postMessage({ id, type: 'READY', payload: null });
      break;
    }
    case 'SIMULATE': {
      if (!engine) {
        self.postMessage({ id, type: 'ERROR', payload: 'Engine not initialized' });
        return;
      }
      const result = engine.update_and_simulate(
        new Float64Array(payload.params),
        payload.profileIndex
      );
      self.postMessage({ id, type: 'MICRO_RESULT', payload: result });
      break;
    }
  }
};
```

**Key patterns:**
- WASM import via `import init, { MicroEngine } from '...pkg'` (wasm-pack output)
- `self.onmessage` (not `onmessage`) to avoid TypeScript issues
- Switch on `type` field (discriminated union)
- D-12: Workers never call `fetch()` — all data arrives via `postMessage`

---

## Shared Patterns

### 1. Version Locking (D-04, D-16)
**Source:** Phase 1 artifacts + `phase1-validate.yml` lines 122-166
**Apply to:** All data-loading functions, CI workflow, `Cargo.toml`

Pattern: All artifacts use semantic version tags. Validate at load time.
```rust
const EXPECTED_RULES_VERSION: &str = "rules-v2025.1";
const EXPECTED_POPULATION_VERSION: &str = "population-v2025.1";
const EXPECTED_MATRIX_VERSION: &str = "shockmatrix-v2025.1";
// Check against loaded artifact metadata; reject on mismatch
```

CI gate pattern (from `phase1-validate.yml` lines 122-186):
```yaml
- name: Verify version tags
  run: |
    VPAT_FOUND=$(grep -r "v2025\\.1" packages/ | wc -l)
    if [ "$VPAT_FOUND" -lt N ]; then
      echo "::error::VERSION GATE FAILED"
      exit 1
    fi
```

### 2. Error Handling (D-16)
**Source:** `export_fixtures.py` lines 130-131 (explicit exception types)
**Apply to:** All Rust crates, all profile loading, all data parsing

Pattern: `Result<T, E>` with explicit error variants. Never panics in production WASM.
```rust
#[derive(Debug, thiserror::Error)]
pub enum LoadError {
    #[error("Invalid age: {0} (must be 0-120)")]
    InvalidAge(u8),
    #[error("Negative wealth: {0}")]
    NegativeWealth(f64),
    #[error("Missing field: {0}")]
    MissingField(String),
    #[error("Version mismatch: expected {expected}, got {actual}")]
    VersionMismatch { expected: String, actual: String },
}
```

### 3. Privacy Guarantee (MICRO-04, D-12)
**Source:** RESEARCH.md architecture diagram (lines 260-268)
**Apply to:** All Worker files, all `wasm-bindgen` exports

Pattern:
- Workers never call `fetch()` or `XMLHttpRequest`
- All data transferred via `postMessage` with Transferable ArrayBuffers
- Profile data stays in WASM linear memory
- Zero computation results leave the browser

### 4. Dependency Boundary (D-01, D-02)
**Source:** RESEARCH.md Pattern 3 (lines 475-525)
**Apply to:** All Rust source files

Pattern:
- `core` crate: ZERO WASM dependencies — pure Rust with `#[test]`
- `wasm-micro` / `wasm-macro`: only `#[wasm_bindgen]` in `lib.rs` boundary layer
- Business logic imports `core`, never `wasm_bindgen`
- Test strategy: `cargo test` for core logic; `wasm-pack test` only for boundary

### 5. Optional Dependency Pattern
**Source:** `packages/data-pipeline/src/shock_matrix/export_parquet.py` lines 25-32
**Apply to:** Any optional Rust dependencies (e.g., rayon)

```python
try:
    import pyarrow as pa
    _HAS_PYARROW = True
except ImportError:
    _HAS_PYARROW = False
```
Rust equivalent: feature-gated dependencies with `#[cfg(feature = "rayon")]`

### 6. Test Fixture Format Contract
**Source:** `packages/data-pipeline/src/validation/export_fixtures.py` lines 7-21, 99-113
**Apply to:** All bilingual test files, CI artifact exchange

JSON fixture format (shared contract between Phase 1 Python and Phase 2 Rust):
```json
{
  "test_fixtures": [
    {
      "name": "celibataire_smic",
      "input": { "situation_familiale": "celibataire", ... },
      "expected": { "ir": 0.0, "cotisations_salariales": 1234.56, ... }
    }
  ],
  "reference_year": 2025,
  "generated_at": "2026-05-12T...",
  "openfisca_version": "159.1.2"
}
```

---

## No Analog Found

Files with no close match in the codebase (planner should use RESEARCH.md code examples as primary pattern):

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `packages/wasm-micro/src/generated/mod.rs` | auto-generated | N/A | Generated by codegen; no existing analog in a Rust codebase. Follow RESEARCH.md Pattern 4 architecture. |
| `packages/wasm-micro/src/generated/ir.rs` | auto-generated | N/A | Generated formula code; pattern is pure function with typed inputs. |
| `packages/wasm-micro/src/generated/is.rs` | auto-generated | N/A | Same as above. |
| `packages/wasm-micro/src/generated/tva.rs` | auto-generated | N/A | Same as above. |
| `packages/wasm-micro/src/generated/cotisations.rs` | auto-generated | N/A | Same as above. |
| `packages/wasm-micro/src/generated/aides.rs` | auto-generated | N/A | Same as above. |
| `packages/wasm-macro/src/projection.rs` | utility | transform | No existing trajectory projection code. RESEARCH.md lines 517-524 provide the MacroResult trajectory structure. |
| `webapp/src/workers/micro-worker.ts` | controller | event-driven | No existing TypeScript worker files. RESEARCH.md Pattern 2 provides complete implementation template. |
| `webapp/src/workers/macro-worker.ts` | controller | event-driven | Same as above. |
| `webapp/src/workers/orchestrator.ts` | controller | event-driven | No existing orchestrator. RESEARCH.md Pattern 2 provides complete implementation template. |
| `webapp/src/workers/index-map.ts` | config | N/A | No existing TypeScript config files. RESEARCH.md Pattern 1 provides TypeScript constants. |
| `packages/core/src/parameters.rs` | utility | data-loading | No existing Rust parameter loading. `convert.py` provides the conceptual pattern (load + convert + validate) but uses different libraries. |
| `packages/core/src/profiles.rs` | utility | data-loading | No existing Rust profile loading. `synthetic_pop/export.py` provides validation pattern but uses different libraries. |
| `packages/core/src/lib.rs` | module-root | N/A | No existing Rust library root. Standard Rust convention: re-export public types. |
| `packages/wasm-micro/src/system.rs` | service | CRUD | No existing Rust tax system. RESEARCH.md Pattern 3 provides the TaxBenefitSystem pattern. |
| `packages/wasm-macro/src/matrix.rs` | service | data-loading | No existing Rust matrix loading. Reverse operation of `export_parquet.py`. |

---

## Metadata

**Analog search scope:**
- `packages/` — Phase 1 Python code (data-pipeline, tax-rules)
- `.github/workflows/` — CI workflow patterns
- `.planning/research/` — Architecture patterns, RESEARCH.md code examples
- No Rust, TypeScript, or JavaScript files exist in the repository

**Files scanned:** 24 Python files, 1 CI workflow, 1 TOML config, Research docs
**Pattern extraction date:** 2026-05-12

**Key findings:**
- The codebase is at Phase 1 completion — all Rust/WASM/TypeScript code is greenfield
- Phase 1 Python files provide excellent structural analogs for CI workflows, config files, and test patterns
- RESEARCH.md provides detailed, concrete code examples for all Rust and TypeScript patterns
- 50% of files have codebase analogs (configs, CI, tests, codegen); 50% rely on RESEARCH.md patterns
- The generated Rust formula code (`generated/*.rs`) has NO analog — it's produced by a code generator that itself needs to be built
- STACK.md correction needed: `interpolation 0.3.0` → `interpn 0.11.0` (documented in RESEARCH.md lines 88-101)
