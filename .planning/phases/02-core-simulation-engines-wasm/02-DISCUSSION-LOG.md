# Phase 02: Core Simulation Engines (WASM) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-13
**Phase:** 02-core-simulation-engines-wasm
**Areas discussed:** Formula Porting Strategy

---

## Formula Porting Strategy

### Initial State

The original CONTEXT.md (2026-05-12) prescribed:
- **D-05:** Code generation from OpenFisca Python source — Python script introspects variable graph and generates Rust source files
- **D-06:** Full OpenFisca-France variable tree (~200+ variables) — no subsetting
- **D-07:** Manual codegen run, commit generated code to repo
- **D-08:** Code generator output: pure Rust functions per formula

Implementation: 3,336 lines of generated Rust across 7 files (`ir.rs`, `is.rs`, `tva.rs`, `cotisations.rs`, `aides.rs`, `profile_fields.rs`, `mod.rs`), called by `TaxBenefitSystem::compute_all_taxes()` in `system.rs`.

### User's Concern

The Python-to-Rust formula port carries permanent maintenance burden — tracking OpenFisca-France upstream changes annually (PLF cycle), achieving code parity with 200+ variables, and maintaining the codegen pipeline. The user questioned whether the cost justifies the benefit.

### Alternatives Considered

| Option | Description | Selected |
|--------|-------------|----------|
| Full codegen WASM port (current) | Python codegen produces Rust formulas, all compute in browser | |
| Pre-computation matrix (Option A) | Run OpenFisca in CI against all slider combos, static lookup file in browser. No formula logic in browser. | ✓ (for citizens) |
| Scenario pre-compute (Option B) | Pre-compute a few candidate scenarios, discrete results. | |
| Backend on-demand (Option C) | Python OpenFisca server-side compute, no 200ms constraint. Privacy tradeoff for experts. | ✓ (for experts) |
| Dependency graph extraction | AST traversal + micro-transpilation of isolated formulas | |

### Decision

**Hybrid architecture: Scenario pre-compute for citizens + backend compute for experts.**

- **Citizen mode:** User picks from candidate list (e.g., 2027 presidential candidates). Pre-computed results loaded as static data file. Zero data transfer, instant lookup. Macro engine sliders remain for trajectory exploration.
- **Expert mode:** Backend Python OpenFisca compute triggered by "calculate" button. No 200ms latency constraint. Privacy tradeoff accepted and documented.

**Rationale:**
- Eliminates permanent tax law maintenance burden (no Rust formula code to keep in sync)
- Citizen privacy guarantee is stronger (no code running on their data — pure static lookup)
- Expert mode is a known tradeoff for analysts/journalists who need full computation power
- Macro engine (interpn + shock matrix) stays — pure math, zero legal logic, low maintenance

### Notes

- The 3,336 lines of generated Rust (`packages/wasm-micro/src/generated/`) become dead code — removable in a subsequent plan
- Sub-scenarios per candidate (Option A+) acknowledged as future enhancement, not v1
- Scenario selector starts simple: candidate name + brief reform summary. No sliders for micro parameters.

---

## the agent's Discretion

- Scenario data file format (Parquet vs JSON vs binary)
- Scenario lookup table schema (candidate × profile × metric dimensions)
- Micro crate disposition (skeleton, gutted, or removed entirely)
- Worker architecture refinement (single macro worker vs dual-worker)
- Macro engine `&[f64]` index mapping

## Deferred Ideas

- **Option A+ (sub-scenarios per candidate):** Policy variants per candidate. Future phase.
- **Fine-tuning sliders within scenarios:** Individual parameter adjustment beyond pre-computed programs. Future phase.
