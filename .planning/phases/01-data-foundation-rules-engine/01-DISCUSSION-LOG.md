# Phase 1: Data Foundation & Rules Engine - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-11
**Phase:** 01-data-foundation-rules-engine
**Areas discussed:** Rules as Code format, Synthetic data pipeline, Shock matrix structure, Validation strategy, Reference year & versioning

---

## Rules as Code Format

| Option | Description | Selected |
|--------|-------------|----------|
| OpenFisca-compatible YAML with build-time JSON conversion | YAML for authoring (comments, human audit), JSON for WASM runtime. Avoids deprecated serde_yaml in binary. | ✓ |
| Custom YAML schema | Define own parameter structure, no OpenFisca compatibility | |
| Direct JSON authoring | Skip YAML entirely, author rules directly in JSON | |

**Auto-selected:** OpenFisca-compatible YAML with build-time JSON conversion (recommended — ecosystem compatibility + WASM binary size optimization)
**Notes:** The `serde_yaml` crate is deprecated at 0.9.34. `serde_yml` is immature. Build-time conversion avoids YAML parsing at WASM runtime entirely.

---

## Synthetic Data Pipeline

| Option | Description | Selected |
|--------|-------------|----------|
| SDV CopulaGANSynthesizer + OpenDP ε=1.0 | Industry-standard copula-based synthesis with formal DP guarantees | ✓ |
| Custom GAN implementation | Build GAN from scratch for maximum control | |
| Iterative Proportional Fitting (IPF) | Traditional statistical approach, simpler but poorer correlation preservation | |

**Auto-selected:** SDV CopulaGANSynthesizer + OpenDP ε=1.0 (recommended — state-of-the-art for fiscal multi-variable dependencies, formal CNIL-compliant DP proof)
**Notes:** IPF fails with high-dimensional fiscal data. Custom GAN requires extensive hyperparameter tuning. SDV is production-proven for this exact use case.

---

## Shock Matrix Structure

| Option | Description | Selected |
|--------|-------------|----------|
| 4 interactive dims, 10-15 grid pts, ≤5 MB compressed | Conservative dimensionality with sparse grid support | ✓ |
| 6-8 interactive dims, 5-8 grid pts | Higher dimensionality, coarser per-dimension resolution | |
| Full 8-dim dense grid | Maximum fiscal realism, high storage cost (3.2 GB) | |

**Auto-selected:** 4 interactive dims, 10-15 grid points each, ≤5 MB compressed (recommended — balances realism with PITFALLS.md curse-of-dimensionality guidance)
**Notes:** 8 dims × 10 points = 10⁸ entries = 3.2 GB. PITFALLS.md explicitly warns against this. Sparse grids (Smolyak) or capped dimensionality prevents the issue.

---

## Validation Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| 10-20 canonical profiles, 1e-6 precision, impots.gouv.fr reference | Practical coverage with numerical precision threshold | ✓ |
| 100+ profiles with statistical sampling | Comprehensive but high maintenance burden | |
| Ad-hoc manual testing | No structured validation framework | |

**Auto-selected:** 10-20 canonical profiles covering edge cases, validated against impots.gouv.fr, 1e-6 precision (recommended — tight precision with manageable test maintenance)
**Notes:** Phase 2 can expand this test suite. The key is having a structured bilingual validation framework (Python→Rust fixture pipeline) from the start.

---

## Reference Year & Versioning

| Option | Description | Selected |
|--------|-------------|----------|
| 2025 reference, PLF-aligned annual updates | Most recent complete data, synchronized with budget calendar | ✓ |
| 2024 reference | Available now but one year behind | |
| Rolling updates on INSEE data release | Maximum freshness, complex versioning | |

**Auto-selected:** 2025 reference year, PLF-aligned annual update cycle with semantic version tags (recommended — balances freshness with stable versioning)
**Notes:** All three artifacts (rules, population, shock matrix) must share the same reference year. CI enforces this via version consistency gates.

---

## the agent's Discretion

- YAML parameter file organization by tax domain (IR, IS, TVA, etc.)
- JSON Schema definitions derived from OpenFisca parameter structure
- Synthetic data preprocessing pipeline (outlier handling, categorical encoding)
- Shock matrix file format (Parquet/Zstd)
- CI pipeline tooling (GitHub Actions, pytest, cargo test)

## Deferred Ideas

None — discussion stayed within phase scope.
