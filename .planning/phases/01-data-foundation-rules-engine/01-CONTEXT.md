# Phase 1: Data Foundation & Rules Engine - Context

**Gathered:** 2026-05-11
**Status:** Ready for planning

## Phase Boundary

This phase delivers all reference data artifacts (tax rules, synthetic population, shock matrix) in auditable, version-locked form — ready for consumption by the WASM computation engines in Phase 2. No computation can proceed without these contracts.

## Implementation Decisions

### Rules as Code Format (DATA-01)
- **D-01:** Tax rules encoded in OpenFisca-compatible YAML schema with legislation references per parameter. Human-auditable, supports comments, follows OpenFisca's Entity/Parameter/Variable structure.
- **D-02:** Build-time YAML→JSON conversion via Python `yaml` + `jsonschema` validation. WASM runtime parses only JSON via `serde_json` — avoids deprecated `serde_yaml` and keeps WASM binary lightweight.
- **D-03:** JSON Schema validation at build time ensures all rates, thresholds, and brackets are present before reaching the WASM engine.

### Synthetic Data Pipeline (DATA-02, DATA-03)
- **D-04:** SDV `CopulaGANSynthesizer` for multi-variable dependency preservation (age ↔ patrimony ↔ income covariance). Copula-based approach is state-of-the-art for fiscal data as cited in the PRD.
- **D-05:** OpenDP 0.14.2 (Rust core, Python bindings) for formal ε-differential privacy with ε ≤ 1.0 budget. Privacy budget is pre-allocated once at generation time — NOT consumed by runtime dashboard queries.
- **D-06:** Reference data sourced from CASD (Centre d'Accès Sécurisé aux Données) microdata when accessible, with INSEE enquête Revenus Fiscaux et Sociaux as fallback.
- **D-07:** SDMetrics quality evaluation validates statistical fidelity, privacy metrics, and detection reports before accepting the synthetic population into CI.

### Shock Matrix Structure (DATA-04)
- **D-08:** Maximum 4 interactive fiscal dimensions (e.g., IR rate, IS rate, TVA rate, dépenses publiques level) to avoid curse of dimensionality. Remaining parameters use fixed reference values.
- **D-09:** Grid density: 10-15 breakpoints per dimension (~10K-50K points per output variable). Stored as compressed Float32Array under 5 MB total for the compressed matrix.
- **D-10:** Smolyak sparse grids preferred if available as a Rust crate compiling to WASM; fallback is uniform Cartesian grid with explicit convex hull bounds documentation.
- **D-11:** Mésange-derived bootstrap computation runs offline as a batch pipeline (Python/SciPy for VAR estimation and Monte Carlo sampling). Output is a static compressed binary consumed by the WASM macro engine in Phase 2.

### Validation Strategy (DATA-04 success criteria)
- **D-12:** 10-20 canonical household profiles covering edge cases (single, couple, families, retirees, self-employed, multi-property) validated against the official impots.gouv.fr simulator.
- **D-13:** Precision threshold: 1e-6 relative difference between Python OpenFisca reference and WASM output for all validated profiles.
- **D-14:** Bilingual validation framework in Python (using openfisca-france as reference) produces JSON test fixtures consumed by `cargo test` (proptest) and `wasm-pack test` in CI.

### Reference Year & Versioning
- **D-15:** All data artifacts locked to reference year 2025 (most recent complete budget year with available CASD/INSEE data).
- **D-16:** Artifacts versioned with semantic tags: `rules-v2025.1`, `population-v2025.1`, `shockmatrix-v2025.1`. CI enforces version consistency across all three.
- **D-17:** Update cadence aligned with PLF (Projet de Loi de Finances) annual cycle. Offline pipeline re-runs in September-October each year after PLF publication.

### the agent's Discretion
- Specific parameter file organization within the YAML tree (by tax domain: IR, IS, TVA, etc.)
- Exact JSON Schema definitions — derive from OpenFisca parameter structure
- Synthetic data preprocessing (outlier handling, categorical encoding) — follow SDV best practices
- Shock matrix file format — Parquet/Zstd for max compression
- CI pipeline tooling (GitHub Actions, pytest, cargo test integration)

## Canonical References

Downstream agents MUST read these before planning or implementing.

### Project-level
- `.planning/PROJECT.md` — Core value, constraints, out-of-scope boundaries
- `.planning/REQUIREMENTS.md` — v1 requirements (DATA-01 through DATA-04)
- `.planning/ROADMAP.md` — Phase ordering and dependencies

### Research (this project)
- `.planning/research/STACK.md` — Technology recommendations with versions and rationale
- `.planning/research/ARCHITECTURE.md` — System structure, component boundaries, data flow
- `.planning/research/PITFALLS.md` — Pitfalls 1 (WASM serialization tax), 3 (DP budget exhaustion), 7 (year mismatches), 9 (curse of dimensionality)

### Domain references (external)
- OpenFisca Core documentation — Entity / Parameter / Variable structure, YAML parameter format
- PolicyEngine Core (policyengine-core) — Formula evaluation, TaxBenefitSystem API patterns
- SDV CopulaGAN documentation — Synthesizer configuration and quality evaluation
- OpenDP documentation — ε-differential privacy mechanisms (Laplace, Gaussian)
- Mésange model documentation — VAR estimation, shock propagation (restricted access — requires Insee/Trésor agreement)
- CASD data access process — Secure data center application timeline (multi-month — start early)

## Existing Code Insights

### Reusable Assets
- None — greenfield project. First code artifacts will be the Python pipeline for synthetic data generation and the YAML rules files.

### Established Patterns
- None — conventions section of PROJECT.md states "Conventions not yet established." First patterns emerge in this phase.

### Integration Points
- Phase 2 (WASM Engines) consumes YAML→JSON rules, synthetic population JSON, and shock matrix binary from this phase.
- CI validation framework must produce test fixtures that Phase 2's `cargo test` can consume.
- Version-locking contract established here gates all downstream computation.

## Specific Ideas

Based on the PRD research:
- The YAML rules should be structured like OpenFisca's country packages (parameters per tax domain) for auditability by non-programmers.
- Synthetic data should target a population that matches INSEE's latest demographic pyramid and revenue distribution tables.
- The shock matrix should be thought of as a static asset, regenerated when PLF changes — not as a live database.

## Deferred Ideas

None — discussion stayed within phase scope.

---

*Phase: 1-Data Foundation & Rules Engine*
*Context gathered: 2026-05-11*
