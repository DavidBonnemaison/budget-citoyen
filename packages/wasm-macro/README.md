# Budget Citoyen — WASM Macro Engine

Macroeconomic simulation engine compiled to WebAssembly.
Performs multi-linear interpolation on pre-computed shock matrices
(Mésange model) for instantaneous macro projections in the browser.

## Data Loading Strategy

**Selected approach: Option 1 — postcard binary + gzip HTTP compression**

### Rationale

After spike-testing all three options from RESEARCH.md (§Parquet/Zstd in WASM), Option 1
(postcard serialization with gzip at the HTTP/content-encoding level) was selected for the
following reasons:

| Criterion | postcard+gzip | parquet2+gzip | ruzstd+parquet2 |
|-----------|--------------|---------------|-----------------|
| WASM compilation | ✅ Zero issues (no-std, no-alloc) | ⚠️ Untested — potential linker issues | ⚠️ Two crates, extra complexity |
| Binary size impact | ✅ ~50 KB added (postcard crate) | ❌ ~200+ KB (parquet2 + flate2) | ❌ ~300+ KB (ruzstd + parquet2) |
| Simplicity | ✅ Flat Vec<f64>, zero schema overhead | ❌ Parquet schema, row groups, pages | ❌ Two-phase decompress+parse |
| Runtime performance | ✅ ~0.1ms deserialize 50K f64 values | ⚠️ ~1-5ms page-parsing overhead | ⚠️ ~2-8ms (decompress + parse) |
| Column selection | ❌ Not supported (full grid load) | ✅ Column pruning possible | ✅ Column pruning possible |
| Development risk | ✅ Minimal — 1 dependency | ⚠️ Medium — WASM target edge cases | ❌ High — zstd C-binding risk |

**Decision:** postcard + gzip HTTP is the clear winner for our use case.
- The shock matrix is loaded once at initialization and cached via `CacheStorage`
- The full grid (tax_rate × spending × horizon × 4 outputs) fits in ~3-5 MB compressed
- No column selection needed at runtime — we always need all outputs
- `postcard` is no-std, no-alloc, and has zero WASM compatibility issues
- The `postcard` crate adds only ~50 KB to the WASM binary vs. 200-300 KB for Parquet alternatives

### Binary Format

The shock matrix is served as a gzip-compressed postcard binary:

```
HTTP Response:
  Content-Type: application/octet-stream
  Content-Encoding: gzip
  Body: postcard::to_allocvec(&flat_f64_array)

Uncompressed layout:
  ┌────────────────────────────────────────────┐
  │ Vec<f64> — flat array in C-order           │
  │                                            │
  │ Shape: (n_tax, n_spend, n_horizon, 4)      │
  │ Index: tax_rate varies fastest,            │
  │        then spending, then horizon,        │
  │        then output variable (4)            │
  │                                            │
  │ Output order:                              │
  │   [0] gdp_growth                           │
  │   [1] employment_change                    │
  │   [2] deficit_change                       │
  │   [3] debt_to_gdp_ratio                    │
  └────────────────────────────────────────────┘
```

**Loading flow (JS side → Worker):**

1. `fetch("shockmatrix-v2025.1.bin")` — browser handles gzip Content-Encoding transparently
2. `Response.arrayBuffer()` — decompressed binary
3. `postMessage(buffer, [buffer])` — zero-copy transfer to Macro Worker
4. Worker: `postcard::from_bytes::<Vec<f64>>(&bytes)` → reshape to ndarray grid

**Metadata** is shipped as a separate JSON sidecar (`shockmatrix-v2025.1.meta.json`) containing:
- `version`: "shockmatrix-v2025.1"
- `reference_year`: 2025
- `dimensions`: dimension names and breakpoint vectors
- `grid_shape`: [n_tax, n_spend, n_horizon, 4]
- `convex_hull`: validity bounds

### Version Tag Convention

Following the Phase 1 data pipeline convention:
- `shockmatrix-v2025.1` — reference year 2025, version 1
- Future versions: `shockmatrix-v2026.1`, `shockmatrix-v2025.2`, etc.
- Version tag is included in the sidecar metadata and matched at load time

### Mock/Test Data

For development without CASD data, a minimal stub grid is used:
- Dimensions: tax_rate(5) × spending(5) × horizon(3) = 75 cells × 4 outputs = 300 f64 values
- Grid values: linearly spaced 0.0 to 29.9 (placeholder — zero economic meaning)
- Breakpoints: uniform sampling over [0.0, 1.0] for rates, [2025, 2027] for horizon
- Stored as `shockmatrix-v2025.1.parquet` in `packages/data-pipeline/dist/`
  (Parquet format for Phase 1 compatibility; converted to postcard binary for WASM consumption)

### Regeneration with Real Data

When CASD access is granted:
1. Run the Phase 1 shock matrix generation pipeline with Mésange model data
2. Export as Parquet (for data science use) AND postcard binary (for WASM)
3. Update `shockmatrix-v2025.1.bin` and sidecar metadata
4. The WASM engine requires no code changes — just data replacement

## Dependencies

| Dependency | Version | Purpose |
|-----------|---------|---------|
| wasm-bindgen | 0.2.121 | JS ↔ WASM bridge |
| serde | 1.0 | Serialization framework |
| serde-wasm-bindgen | 0.6.5 | WASM-specific serde bridge |
| ndarray | 0.17 | N-dimensional grid storage |
| interpn | 0.11 | Multi-linear interpolation on regular grid |
| postcard | 1.0 | Compact binary serialization for shock matrix loading |

## Testing

```bash
# Native tests (fast, no browser):
cargo test -p budget-citoyen-wasm-macro

# WASM tests (browser context, via wasm-bindgen-test):
wasm-pack test --headless packages/wasm-macro
```

## Architecture Notes

- **interpn 0.11.0** was selected over `interpolation 0.3.0` (RESEARCH.md Stack Correction).
  `interpolation` is an animation easing crate; `interpn` is the correct N-dimensional
  grid interpolation library for scientific computing (docs.rs confirmed).
- The macro engine uses a **flat f64 slice input** (D-09) — no structured serialization
  across the WASM boundary per slider update. This achieves the <200ms latency target.
- Convex hull bounds checking (D-09) returns `Option::None` for out-of-bounds inputs
  rather than extrapolating beyond the Mésange model's validity domain.
