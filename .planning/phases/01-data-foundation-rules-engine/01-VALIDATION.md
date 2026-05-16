---
phase: 01
slug: 01-data-foundation-rules-engine
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-16
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (Python) |
| **Config file** | packages/data-pipeline/pyproject.toml |
| **Quick run command** | `cd packages/data-pipeline && python3 -m pytest tests/test_rules_coverage.py tests/test_conversion.py tests/test_shock_matrix.py -v` |
| **Full suite command** | `cd packages/data-pipeline && python3 -m pytest tests/ -v --ignore=tests/test_synthetic_pop.py` |
| **Estimated runtime** | ~12s (full suite, 90 tests) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_rules_coverage.py tests/test_conversion.py tests/test_shock_matrix.py -v`
- **After every plan wave:** Run `pytest tests/ -v --ignore=tests/test_synthetic_pop.py`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-T1 | 01 | 1 | DATA-01 | T-01-01 | YAML files parse, JSON Schema validation gate | unit | `pytest tests/test_conversion.py::TestYamlToJsonConversion -v` | ✅ | ✅ green |
| 01-01-T2 | 01 | 1 | DATA-01 | T-01-01 | JSON Schema Draft 2020-12 self-validation | integration | `pytest tests/test_schema_validation.py::TestSchemaSelfValidation -v` | ✅ | ✅ green |
| 01-02-T1 | 02 | 1 | DATA-02 | — | SDV metadata + CopulaGAN training pipeline | integration | `pytest tests/test_synthetic_pop.py::TestSyntheticPopImports -v` | ✅ | ✅ green |
| 01-02-T2 | 02 | 1 | DATA-03 | — | OpenDP Laplace mechanism with formal ε proof | unit | `pytest tests/test_dp_inject.py::TestProveDpGuarantee -v` | ✅ | ✅ green |
| 01-03-T1 | 03 | 1 | DATA-04 | — | Grid construction with D-08/D-09 enforcement | unit | `pytest tests/test_shock_matrix.py::TestGridDimensionCap -v` | ✅ | ✅ green |
| 01-03-T2 | 03 | 1 | DATA-04 | — | Convex hull bounds + Parquet/Zstd export | integration | `pytest tests/test_shock_matrix.py::TestParquetExportConstraints -v` | ✅ | ✅ green |
| 01-04-T1 | 04 | 2 | DATA-01 | T-04-01 | Canonical profiles + bilingual validation framework | integration | `pytest tests/test_validation.py::TestCanonicalProfiles -v` | ✅ | ✅ green |
| 01-04-T2 | 04 | 2 | DATA-01 | T-01-06 | CI pipeline + 5 test skeleton files | integration | `pytest tests/test_schema_validation.py tests/test_conversion.py tests/test_shock_matrix.py tests/test_validation.py -v` | ✅ | ✅ green |
| 01-05-T1 | 05 | 1 | DATA-01 | T-01-05 | 19 new YAML files + credits expanded to 25 | integration | `pytest tests/test_rules_coverage.py -v` | ✅ | ✅ green |
| 01-05-T2 | 05 | 1 | DATA-01 | T-01-05 | Cotisations + aides domain expansion | integration | `pytest tests/test_rules_coverage.py::TestYamlParameterFileCount -v` | ✅ | ✅ green |
| 01-05-T3 | 05 | 1 | DATA-01 | T-01-08 | 32 canonical profiles with 7-dimension coverage | unit | `pytest tests/test_validation.py::TestCanonicalProfiles -v` | ✅ | ✅ green |

---

## Wave 0 Requirements

- [x] `tests/test_rules_coverage.py` — YAML file count, credits entries, domain index consistency, 7-dimension coverage (DATA-01)
- [x] `tests/test_conversion.py` — YAML→JSON roundtrip, missing field rejection, date key conversion regression (DATA-01)
- [x] `tests/test_schema_validation.py` — JSON Schema self-validation, IR bareme structure, missing value rejection (DATA-01)
- [x] `tests/test_validation.py` — Canonical profiles (count, fields, uniqueness, edge cases), reference sim (QF, IR, export) (DATA-01)
- [x] `tests/test_synthetic_pop.py` — Synthetic population pipeline imports, preprocess, metadata, SHA-256, full pipeline (DATA-02, DATA-03)
- [x] `tests/test_dp_inject.py` — OpenDP proof, DP injection, privacy statement, export metadata (DATA-03)
- [x] `tests/test_shock_matrix.py` — Grid dimension cap, breakpoints range, convex hull, Parquet export, bootstrap, Smolyak (DATA-04)
- [x] `tests/test_calibrate.py` — Calibrated grid shape, breakpoint ranges, convex hull, export (DATA-04)
- [x] `tests/test_insee_loader.py` — INSEE aggregate loader, columns, row count, categoricals (DATA-02)
- [x] `tests/test_scenario_precompute.py` — Scenario definitions, precompute pipeline, aides matching (MICRO-01)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| impots.gouv.fr validation protocol | DATA-01 | Requires human interaction with impots.gouv.fr simulator | Follow protocol in `packages/data-pipeline/src/validation/impots_gouv_validator.py` — navigate to simulator, enter canonical profile data, capture results |
| openfisca-france full API integration | DATA-01 | Input field mappings must be confirmed by domain experts | Run `reference_sim.py` against full openfisca-france once field mappings confirmed; compare against bilingual fixtures |
| Synthetic data quality at full scale (epochs=500, 50K rows) | DATA-02 | Computational cost prohibitive for CI; requires GPU | Run `pytest tests/test_synthetic_pop.py -m slow -v` on dedicated hardware |
| CI pipeline execution (GitHub Actions) | DATA-01 | CI workflows only execute in GitHub environment | Push to branch, observe CI jobs: schema-validation, conversion-test, version-consistency, synth-pop-test, shock-matrix-test, validation-test, artifact-integrity |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-05-16
