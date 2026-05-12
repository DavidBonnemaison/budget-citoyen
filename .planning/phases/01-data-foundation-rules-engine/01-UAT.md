---
status: diagnosed
phase: 01-data-foundation-rules-engine
source: 01-01-SUMMARY.md, 01-02-SUMMARY.md, 01-03-SUMMARY.md, 01-04-SUMMARY.md
started: 2026-05-12T10:00:00Z
updated: 2026-05-12T13:15:00Z
---

## Current Test

[testing complete]

## Tests

### 1. YAML Tax Rules Parse Correctly
expected: All 17 YAML parameter files across 5 domains (IR, IS, TVA, cotisations, aides) parse without error via yaml.safe_load(). Each file contains description, metadata.reference (legifrance.gouv.fr), and values locked to 2025-01-01. Domain index.yaml files document their respective parameter inventories.
result: issue
reported: "why are there so few tax niches ? and more parameters overall ? weren't we supposed to implement all rules ?"
severity: major

### 2. YAML-to-JSON Conversion Pipeline
expected: Running `yaml2json/convert.py` on all 12 parameter YAML files produces valid JSON output preserving directory structure. JSON Schema Draft 2020-12 validation gate catches malformed input (missing description, invalid bracket format) and rejects it before any JSON is written.
result: pass

### 3. JSON Schema Self-Validation
expected: All 3 JSON Schema definitions (parameter.schema.json, tax_benefit_system.schema.json, synthetic_profile.schema.json) pass Draft202012Validator.check_schema() — confirming they are structurally valid against the JSON Schema meta-schema.
result: pass

### 4. Synthetic Population Pipeline Structure
expected: All 5 pipeline modules in `packages/data-pipeline/src/synthetic_pop/` exist (__init__, preprocess, train, dp_inject, evaluate, export). Train module uses CopulaGANSynthesizer with epochs=500. DP module uses OpenDP Laplace mechanism with .map(d_in=1) formal ε proof. Export module includes SHA-256 integrity hash and versioned .meta.json sidecar.
result: pass

### 5. Shock Matrix Pipeline Structure
expected: All 4 modules in `packages/data-pipeline/src/shock_matrix/` exist (__init__, bootstrap, grid_build, convex_hull, export_parquet). Grid construction enforces max 4 dimensions and 10-15 breakpoints per dimension. Convex hull uses scipy.spatial.ConvexHull (never hand-rolled). Parquet export uses Zstd compression_level=9 with <5 MB size assertion.
result: pass

### 6. Canonical Profiles Cover Edge Cases
expected: 16 canonical household profiles exist with name, description, situation_familiale, nb_enfants, revenus (salaires/pensions/bnc/fonciers), patrimoine (immobilier/financier), and zone_residence fields. All D-12 edge cases are represented: célibataire, couple, famille nombreuse, retraité, indépendant, multi-propriétaire, haut-revenu, étranger.
result: issue
reported: "16 might be too low, let's try 32 to cover more cases, with finer granularity"
severity: major

### 7. Test Suite Collects Without Errors
expected: `pytest --collect-only` in the data-pipeline package discovers tests from all 5 test files (test_conversion, test_schema_validation, test_synthetic_pop, test_shock_matrix, test_validation) without import errors or collection failures.
result: pass

### 8. GitHub Actions CI Pipeline
expected: `.github/workflows/phase1-validate.yml` exists with 7 jobs: schema-validation, conversion-test, version-consistency (enforced 2025 lock via Python `assert`), synth-pop-test, shock-matrix-test, validation-test, and artifact-integrity (SHA-256 hash check).
result: pass

## Summary

total: 8
passed: 6
issues: 2
pending: 0
skipped: 0
blocked: 0

## Gaps

- truth: "All 17 YAML parameter files across 5 domains (IR, IS, TVA, cotisations, aides) parse without error via yaml.safe_load(). Each file contains description, metadata.reference (legifrance.gouv.fr), and values locked to 2025-01-01. Domain index.yaml files document their respective parameter inventories."
  status: failed
  reason: "User reported: why are there so few tax niches ? and more parameters overall ? weren't we supposed to implement all rules ?"
  severity: major
  test: 1
  root_cause: "Scope mismatch between broad DATA-01 requirement text and plan-level starter-skeleton scope. PLAN intentionally limited to 12 parameter files covering most visible items per domain, establishing YAML format/pipeline infrastructure. Acceptance criteria validated structural quality only (14+ files, legifrance references, date keys), not semantic completeness. Critical IR gaps: quotient_familial, décote, plafonnement_qf, CEHR. Aides gaps: AAH, ASPA, CSS, ARE. Only 3 tax credits out of ~474 dépenses fiscales."
  artifacts:
    - path: "packages/tax-rules/parameters/ir/"
      issue: "Missing: quotient_familial.yaml, decote.yaml, plafonnement_qf.yaml, cehr.yaml, etc."
    - path: "packages/tax-rules/parameters/aides/"
      issue: "Missing: aah.yaml, aspa.yaml, css.yaml, cheque_energie.yaml, allocation_rentree_scolaire.yaml, paje.yaml, are.yaml"
    - path: "packages/tax-rules/parameters/cotisations/"
      issue: "Missing: allegements_fillon.yaml, forfait_social.yaml, PASS standalone parameter, etc."
    - path: ".planning/REQUIREMENTS.md:12"
      issue: "DATA-01 requirement text ambiguous — reads as comprehensive but technically satisfied by any non-empty set per domain"
    - path: ".planning/phases/01-data-foundation-rules-engine/01-01-PLAN.md"
      issue: "Plan intentionally scoped to 12 files. Acceptance criteria never validated semantic sufficiency for Phase 2 computation"
  missing:
    - "Add quotient_familial.yaml (parts fiscales) — IR cannot be computed without it"
    - "Add decote.yaml and plafonnement_qf.yaml"
    - "Add AAH, ASPA parameters (critical social benefits)"
    - "Add allègements Fillon (réductions générales cotisations patronales)"
    - "Expand tax credits from 3 to 25-30 entries"
    - "Clarify DATA-01 requirement text in REQUIREMENTS.md with explicit scope tiers"
  debug_session: ".planning/debug/uat-01-yaml-parameter-gap.md"
- truth: "16 canonical household profiles exist with name, description, situation_familiale, nb_enfants, revenus, patrimoine, and zone_residence fields. All D-12 edge cases are represented."
  status: failed
  reason: "User reported: 16 might be too low, let's try 32 to cover more cases, with finer granularity"
  severity: major
  test: 6
  root_cause: "Same pattern as GAP #1 — scope definition issue. PLAN scoped to 10-20 profiles (delivered 16) to establish validation framework. D-12 wording set low floor. 16 profiles nominally cover all 8 D-12 edge cases but 7 of 8 cases have only 1-2 profiles. Only 9 distinct income levels, no profiles at CEHR thresholds/QF caps/IR bracket boundaries. zone3 tested at only 2 income points. Cross-category combinations absent."
  artifacts:
    - path: "packages/data-pipeline/src/validation/canonical_profiles.py"
      issue: "Only 16 profiles. Missing systematic income stratification, family structure × income intersection, zone3 coverage, cross-category combinations"
    - path: "packages/data-pipeline/tests/test_validation.py"
      issue: "Acceptance criteria floor (≥14) too low — should be ≥30 after expansion"
    - path: ".planning/phases/01-data-foundation-rules-engine/01-CONTEXT.md"
      issue: "D-12 wording '10-20 canonical profiles' is the root constraint enabling this gap"
  missing:
    - "Add 16+ profiles expanding total to 32 across 7 dimensions (income stratification, family structures, zone residence, asset profiles, profession types, social benefit edge cases, cross-category combinations)"
    - "Add profiles at CEHR thresholds (250K/500K), IR bracket boundaries, QF caps, décote thresholds"
    - "Add single-parent+1-child (France's most common single-parent config)"
    - "Add zone3 profiles for célibataire, retraité modeste, indépendant (>6 per zone)"
    - "Add cross-category: retraité+propriétaire, indépendant+famille, handicapé+revenu modeste"
    - "Update test_profile_count_at_least_fourteen threshold to ≥30"
  debug_session: ".planning/debug/uat-01-canonical-profiles-gap.md"
