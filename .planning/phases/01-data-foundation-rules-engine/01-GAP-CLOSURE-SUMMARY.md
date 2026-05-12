---
phase: 01-data-foundation-rules-engine
plan: 05
type: gap-closure
tags: [yaml, openfisca, canonical-profiles, uat, gap-closure, tax-rules, ir, is, tva, cotisations, aides]
status: complete
completed: 2026-05-12

requires:
  - phase: 01-data-foundation-rules-engine
    provides: 01-01-SUMMARY.md (YAML authoring patterns, JSON Schema validation), 01-UAT.md (gap diagnoses)
provides:
  - 19 new YAML parameter files (9 tax + 10 cotisations/aides) with legifrance.gouv.fr references
  - credits.yaml expanded from 3 to 25 entries with legislation references
  - 32 canonical household profiles with systematic 7-dimension coverage
  - Updated test threshold (>=14 -> >=30)
affects:
  - Phase 2 (WASM Engine): Complete parameter data for IR, IS, TVA, cotisations, aides computation
  - Phase 2 (bilingual validation): 32 test profiles covering all fiscal edge cases

tech-stack:
  added: []
  patterns:
    - "Pattern: OpenFisca YAML parameter format — description + metadata.reference + values.{date}.value"
    - "Pattern: Brackets structure for progressive taxation (CEHR, chèque énergie)"
    - "Pattern: values type for scalar and nested parameters (décote, quotient familial, PASS)"

key-files:
  created:
    # Task 1 — IR, IS, TVA (9 new files + credits expanded)
    - packages/tax-rules/parameters/ir/quotient_familial.yaml
    - packages/tax-rules/parameters/ir/decote.yaml
    - packages/tax-rules/parameters/ir/plafonnement_qf.yaml
    - packages/tax-rules/parameters/ir/cehr.yaml
    - packages/tax-rules/parameters/is/exonerations.yaml
    - packages/tax-rules/parameters/is/report_deficits.yaml
    - packages/tax-rules/parameters/is/CVAE.yaml
    - packages/tax-rules/parameters/tva/franchise.yaml
    - packages/tax-rules/parameters/tva/exonerations.yaml
    # Task 2 — Cotisations, Aides (10 new files)
    - packages/tax-rules/parameters/cotisations/allegements_fillon.yaml
    - packages/tax-rules/parameters/cotisations/forfait_social.yaml
    - packages/tax-rules/parameters/cotisations/pass.yaml
    - packages/tax-rules/parameters/aides/aah.yaml
    - packages/tax-rules/parameters/aides/aspa.yaml
    - packages/tax-rules/parameters/aides/css.yaml
    - packages/tax-rules/parameters/aides/cheque_energie.yaml
    - packages/tax-rules/parameters/aides/allocation_rentree_scolaire.yaml
    - packages/tax-rules/parameters/aides/paje.yaml
    - packages/tax-rules/parameters/aides/are.yaml
  modified:
    # Expanded
    - packages/tax-rules/parameters/ir/credits.yaml (3 -> 25 entries)
    # Updated index files (5)
    - packages/tax-rules/parameters/ir/index.yaml
    - packages/tax-rules/parameters/is/index.yaml
    - packages/tax-rules/parameters/tva/index.yaml
    - packages/tax-rules/parameters/cotisations/index.yaml
    - packages/tax-rules/parameters/aides/index.yaml
    # Task 3 — canonical profiles
    - packages/data-pipeline/src/validation/canonical_profiles.py (16 -> 32 profiles)
    - packages/data-pipeline/tests/test_validation.py (>=14 -> >=30)

key-decisions:
  - "Removed celibataire_100k_patrimoine from original 17-profile list to achieve exactly 32 profiles — coverage overlaps with celibataire_250k_cehr and celibataire_cadre"
  - "chèque_energie uses brackets structure (like bareme.yaml and CEHR) for progressive RFR/UC tiers"
  - "All 31 YAML parameter files validate through JSON Schema Draft 2020-12 pipeline with zero errors"
  - "pass.yaml (PASS) uses standard values type — Plafond Annuel de la Sécurité Sociale is a reference value, not progressive"

patterns-established:
  - "Pattern: values type for domain reference constants (PASS 47,100€, franchise TVA thresholds)"
  - "Pattern: brackets type for progressive eligibility tiers (chèque énergie, CEHR)"
  - "Pattern: exposition de formule — key parameters include 'formule' description for auditability"

requirements-completed: [DATA-01]

# Metrics
duration: 20min
completed: 2026-05-12
---

# Phase 1 Plan 05: Gap Closure — YAML Parameter Completeness + Canonical Profiles Depth

**19 new YAML parameter files across all 5 tax domains + credits.yaml expanded to 25 entries + 16 new canonical profiles for 32 total — closing UAT gaps #1 and #2**

## Performance

- **Duration:** 20 min
- **Started:** 2026-05-12
- **Completed:** 2026-05-12
- **Tasks:** 3
- **Files modified:** 27

## Gap Closure Status

| UAT Gap | Status | Evidence |
|---------|--------|----------|
| Gap #1 — YAML parameter completeness (12→30+) | **Closed** | 31 YAML parameter files across 5 domains, credits expanded to 25 entries |
| Gap #2 — Canonical profiles depth (16→32) | **Closed** | 32 profiles with 7-dimension systematic coverage, 8 zone3, all edge cases represented |

## Accomplishments

- **IR domain** (7 files): bareme, deductions, credits (25 entries), quotient_familial, décote, plafonnement_qf, CEHR — full IR computation pipeline can now be modeled
- **IS domain** (4 files): taux, exonerations (5 regimes), report_deficits (carry-back/forward), CVAE (abolition path 2025-2028)
- **TVA domain** (3 files): taux, franchise_en_base (3 regimes), exonerations (8 sectorial exemptions)
- **Cotisations domaine** (6 files): salariales, patronales, CSG/CRDS, allegements_fillon, forfait_social, PASS
- **Aides domaine** (11 files): RSA, APL, allocations familiales, prime_activité, AAH, ASPA, CSS, chèque_energie, ARS, PAJE, ARE
- **32 canonical profiles** with 7-dimension coverage: income stratification (CEHR thresholds at 250K/500K), zone residence (8 zone3 profiles), asset profiles (IFI, pure financial wealth), profession types (agriculteur, micro-entrepreneur), social benefit edge cases (AAH, ASPA, ARE cumul), cross-category combinations (retraite+proprietaire, independant+famille)
- **Test threshold** updated from >=14 to >=30 — all 12 tests pass

## Task Commits

1. `b376ce3` — feat(01-05): expand IR, IS, TVA YAML parameters (9 new files + credits 25 entries)
2. `bc0b668` — feat(01-05): expand cotisations and aides YAML parameters (10 new files)
3. `fba8256` — feat(01-05): expand canonical profiles from 16 to 32 with systematic dimensional coverage

## Deviations from Plan

### Plan numbering inconsistency resolved

The plan listed 17 profiles (numbered 17-33) but stated "16 new profiles" and "exactly 32 total." This is an off-by-one error in the plan numbering. Resolution: removed `celibataire_100k_patrimoine` whose coverage (high-income single with financial assets) overlaps with both `celibataire_cadre` (80K salary + 50K financial) and `celibataire_250k_cehr` (250K salary + 200K financial). No loss of dimensional coverage — income stratification dimension remains covered through 5 remaining profiles at SMIC, 250K CEHR, couple_500k CEHR, and other income points.

## Verification Results

| Check | Result |
|-------|--------|
| All 36 YAML files parse via yaml.safe_load() | PASS |
| 31 parameter files convert to JSON with zero schema violations | PASS |
| 5 domain index.yaml files consistent with file inventory | PASS |
| 32 canonical profiles with unique names and required fields | PASS |
| 7-dimensional coverage verified (income, zone, assets, professions, benefits, cross-category) | PASS |
| Test threshold updated to >=30 | PASS |
| All 12 tests pass (8 canonical profile + 4 reference sim) | PASS |

## Threat Mitigation Status

| Threat ID | Status | Evidence |
|-----------|--------|----------|
| T-01-05 (New YAML tampering) | **Mitigated** | All 19 new files pass JSON Schema Draft 2020-12 validation with zero errors |
| T-01-06 (Information disclosure) | **Accepted** | No PII in YAML — only public fiscal parameter values |
| T-01-07 (credits.yaml tampering) | **Mitigated** | 25 entries with legifrance.gouv.fr references validated through schema |
| T-01-08 (DoS via profiles) | **Accepted** | 32 profiles negligible import cost — Python dicts <10ms load |
| T-01-09 (test threshold tampering) | **Mitigated** | Threshold at >=30, source-controlled, verified passing |

## Next Phase Readiness

- 31 validated JSON parameter files with complete semantic coverage (from 12 skeleton files) ready for Phase 2 WASM microsimulation engine
- 32 canonical profiles hitting all critical fiscal thresholds (CEHR, décote, QF caps, IR brackets) ready for bilingual validation in Phase 2
- No remaining UAT gaps for Phase 1 — both gap #1 (YAML completeness) and gap #2 (profiles depth) are closed
- Ready for Phase 2: Core Simulation Engines (WASM)

---
*Phase: 01-data-foundation-rules-engine*
*Plan: 05 — Gap Closure*
*Completed: 2026-05-12*
