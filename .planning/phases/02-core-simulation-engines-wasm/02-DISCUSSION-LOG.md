# Phase 2: Core Simulation Engines (WASM) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-12
**Phase:** 02-core-simulation-engines-wasm
**Areas discussed:** Crate architecture & code organization, Formula porting strategy, WASM boundary & worker protocol design, Profile data model

---

## Crate Architecture & Code Organization

| Option | Description | Selected |
|--------|-------------|----------|
| 3 crates: core + wasm-micro + wasm-macro | Shared core with common types, two separate wasm-* crates for each engine | ✓ |
| 2 crates: core + wasm-bindgen | Single wasm crate wrapping everything | |
| 4+ crates | Finer split: core-formula + core-interp + wasm-micro + wasm-macro | |

**User's choice:** 3 crates: core + wasm-micro + wasm-macro (Recommended)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Core: types + params + profiles + validation | Shared data types, parameter loading, profile parsing, test fixtures | ✓ |
| Core: just types and serialization | Minimal — each engine loads params/profiles independently | |
| Core: everything except wasm-bindgen exports | All logic in core, thin wasm-* wrappers | |

**User's choice:** Core: types + params + profiles + validation. Engines: their own logic (Recommended)
**Notes:** Engines import core. No engine-specific logic in core.

---

| Option | Description | Selected |
|--------|-------------|----------|
| packages/ (flat) | packages/core, packages/wasm-micro, packages/wasm-macro | ✓ |
| crates/ (separate dir) | Top-level crates/ directory for all Rust code | |
| packages/wasm/ (nested) | Single wasm directory with internal workspace features | |

**User's choice:** packages/ (flat, alongside tax-rules and data-pipeline) (Recommended)
**Notes:** Cargo workspace at repo root.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Separate Rust CI workflow | New phase2-wasm.yml + Phase 1 validation gate as prerequisite | ✓ |
| Single unified CI workflow | Extend Phase 1's workflow with Rust jobs | |
| cargo test only in CI | wasm-pack test as manual pre-commit | |

**User's choice:** Separate Rust CI workflow + Phase 1 validation gate as prerequisite (Recommended)
**Notes:** Phase 1 validation must pass first — produces JSON test fixtures consumed by cargo test.

---

## Formula Porting Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Code generation from OpenFisca Python source | Python script introspects variable graph, generates Rust source | ✓ |
| Idiomatic Rust reimplementation | Hand-write formulas with explicit typed dependency graph | |
| 1:1 port of Variable/Parameter architecture | Replicate OpenFisca abstractions in Rust traits/enums | |
| Hybrid: manual core + validation bridge | Manual port with tight validation loop | |

**User's choice:** Code generation from OpenFisca Python source
**Notes:** User initially chose codegen, then questioned whether Rust was overengineering vs Python. After clarifying that Rust/WASM is locked by privacy+latency constraints (Python can't run client-side efficiently), user re-confirmed code generation. The code generator discovers formula dependencies from OpenFisca's variable graph automatically.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Everything: full variable tree | All ~200+ OpenFisca-France variables | ✓ |
| Domain-based subset | 5 target domains (IR/IS/TVA/cotisations/aides) + transitive dependencies | |
| Minimal: terminal formulas only | Hardcoded approximations for intermediates | |

**User's choice:** Everything: full OpenFisca-France variable tree
**Notes:** User opted to not leave anything out of scope for v1, questioning whether subsetting was worth the risk.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Manual codegen run, commit, CI warns | Staleness warning if openfisca-france has newer version | ✓ |
| Commit + CI regenerates and diffs | Hard gate that fails on diff | |
| Generate in CI only, never commit | Requires Python + openfisca-france for local dev | |
| Run once, commit, treat as frozen | Simplest but risks divergence | |

**User's choice:** Manual codegen run, commit generated code, CI emits a soft warning if openfisca-france upstream has newer version

---

| Option | Description | Selected |
|--------|-------------|----------|
| Pure Rust functions with typed inputs + match on period | Generated module per tax domain, dependency ordering resolved at codegen time | ✓ |
| Trait-based variable system | Variable trait + impl blocks, runtime resolution | |
| Flat lookup table generation | Pre-computed const arrays | |

**User's choice:** Pure Rust functions with typed inputs + match on period (Recommended)
**Notes:** Each formula becomes `fn calculate_xxx(parameters: &Parameters, period: Date, profile: &Profile) -> f64`.

---

## WASM Boundary & Worker Protocol Design

| Option | Description | Selected |
|--------|-------------|----------|
| Flat f64 array + index-based setters | Single &[f64] slice, pre-allocated SimulationState updated in-place | ✓ |
| serde-wasm-bindgen Reform struct | Typed struct with named fields, small serialization overhead | |
| SharedArrayBuffer + Atomics | Truly zero-copy but requires COOP/COEP headers | |

**User's choice:** Flat f64 array + index-based setters (Recommended)
**Notes:** A companion constant module documents the index→parameter mapping for both Rust and TypeScript.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Structured struct via wasm-bindgen | serde-wasm-bindgen deserializes typed result objects once per interaction | ✓ |
| Flat f64 array for results too | Symmetric input/output but fragile index mapping | |
| JSON string | serde_json, simple but ~1-2ms overhead | |

**User's choice:** Structured struct via wasm-bindgen (serde-wasm-bindgen) (Recommended)
**Notes:** Result struct auto-generates TypeScript declarations. Acceptable overhead since results produced once per slider interaction.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Typed request/response with correlation IDs | { id, type, payload }, stale responses discarded by ID matching | ✓ |
| Comlink-style RPC wrapper | Library-based, hides message lifecycle | |
| Simple fire-and-forget | Worker processes latest message, drops queued stale ones | |

**User's choice:** Typed request/response with correlation IDs (Recommended)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Main thread fetches, transfers to workers | Transferable ArrayBuffers, no network access in workers | ✓ |
| Workers fetch independently | More parallel but CORS complexity in workers | |
| Bundle into WASM binary | Embed via include_bytes!(), huge binary, defeats caching | |

**User's choice:** Main thread fetches, transfers to workers via postMessage (Recommended)

---

## Profile Data Model

| Option | Description | Selected |
|--------|-------------|----------|
| Simplified flat profile struct | All attributes flattened, codegen resolves cross-entity references | ✓ |
| Full OpenFisca entity model | Individu, Famille, FoyerFiscal, Menage as Rust structs with Vec references | |
| Key-value attribute bag | HashMap<String, f64> with string-key lookups | |

**User's choice:** Simplified flat profile struct (Recommended)
**Notes:** The code generator resolves OpenFisca's entity hierarchy at codegen time, so the Rust runtime never traverses entity relationships.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Vec<Profile> with rayon parallel iteration | All 50K profiles in WASM memory, par_iter for batch | ✓ |
| Struct of Arrays (SoA) | Separate Vec<f64> per attribute, better cache locality | |
| Lazy/streaming chunks | Load 1K at a time, aggregate, discard | |

**User's choice:** Vec<Profile> with rayon parallel iteration (Recommended)
**Notes:** ~10MB for 50K profiles in memory — acceptable. Single-profile: index into Vec.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Profile derives from code generator output | Codegen introspects OpenFisca inputs, emits Rust struct with exact fields | ✓ |
| Manually designed struct | ~50 hand-crafted fields, stable but manual maintenance | |
| Dynamic serde_json::Value wrapper | String-key field access, maximum flexibility | |

**User's choice:** Profile derives from code generator output (Recommended)
**Notes:** CI regenerates struct when OpenFisca-France updates. Synthetic population export adapts JSON keys to match.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Strict validation at load time | Result<Profile, LoadError>, rejects invalid profiles with count | ✓ |
| Liberal: defaults + clamping | Silent fill/correction of invalid data | |
| Load raw, validate lazily | Option::None propagation at formula access time | |

**User's choice:** Strict validation at load time with Result<Profile, LoadError> (Recommended)

---

## the agent's Discretion

- Exact index mapping for the flat `&[f64]` input array
- Cargo workspace configuration details (workspace members, dependency versions, feature flags)
- Code generator implementation details (introspection API, Rust code formatting, output directory structure)
- Worker initialization sequencing (which worker to init first, timeout/retry strategy)
- Production service worker integration for asset caching (deferred to Phase 3/5)
- COOP/COEP header strategy (test on target platform early per STACK.md warning)

## Deferred Ideas

None — discussion stayed within phase scope.
