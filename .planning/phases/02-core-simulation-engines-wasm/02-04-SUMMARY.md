---
phase: 02-core-simulation-engines-wasm
plan: 04
subsystem: data-pipeline
tags: [python, openfisca-france, scenario-precompute, ci, data-pipeline]

# Dependency graph
requires:
  - phase: 01-data-foundation-rules-engine
    provides: openfisca-france dependency, canonical profiles (bilingual_test_fixtures.json)
  - phase: 02-core-simulation-engines-wasm
    provides: "plans 02-02, 02-03: core types (Profile, Parameters)"
provides:
  - Scenario data format definition matching TypeScript ScenarioDoc contract
  - Python pre-compute pipeline running openfisca-france for 3+ candidate scenarios
  - Versioned static scenario JSON (scenarios-v2025.1.json) for O(1) client-side lookups
  - CI staleness check for openfisca-france upstream version
affects: ["02-06", "02-07", "02-08", "03-ui"]

# Tech tracking
tech-stack:
  added: [openfisca-france (>=159,<200), openfisca_core.reforms]
  patterns:
    - "Scenario pre-compute: Python runs openfisca-france × canonical profiles, exports static JSON"
    - "Lazy openfisca imports for importability without runtime dependency (linting, CI dry-runs)"
    - "GitHub Actions ::warning annotation format for soft CI gates"
    - "Reform API: openfisca_core.reforms.Reform subclass with parameter overrides applied via modify_parameters()"

key-files:
  created:
    - packages/data-pipeline/src/scenarios/__init__.py
    - packages/data-pipeline/src/scenarios/scenario_definitions.py
    - packages/data-pipeline/src/scenarios/precompute.py
  modified:
    - packages/data-pipeline/pyproject.toml

key-decisions:
  - "Hybrid architecture: Python CI pre-computation replaces Rust/WASM formula engine — all microsimulation runs in CI, browser does O(1) lookups only"
  - "3 candidate scenarios defined (baseline-2025, expansion-2025, consolidation-2025) with distinct openfisca-france parameter overrides"
  - "ScenarioDoc JSON format mirrors TypeScript scenario-cache.ts contract exactly (definition + Record<number, ScenarioResult>)"
  - "Lazy openfisca imports: scenario_definitions.py importable without openfisca installed (linting, type-checking)"

patterns-established:
  - "Pattern 1: Scenario pre-compute pipeline — load fixtures → apply reform → compute → export JSON"
  - "Pattern 2: Reform API — openfisca_core.reforms.Reform subclass with lazy import"
  - "Pattern 3: Pre-compute staleness check — version consistency gate in CI (D-07)"

requirements-completed:
  - MICRO-01
  - MICRO-02
  - MICRO-03

# Metrics
duration: 23 min
completed: 2026-05-12
---

# Phase 2 Plan 4: Scenario Data Format & Pre-Compute Pipeline Summary

**Python pre-compute pipeline that runs openfisca-france for 3 candidate reform scenarios against 32 canonical profiles and exports versioned static JSON for O(1) client-side lookups — replaces the deprecated codegen pipeline**

> **Architecture note (02-11 gap closure):** The original Plan 02-04 implemented a Python→Rust codegen that auto-generated 340 Rust formula functions. This was replaced in the architecture simplification (Plans 02-09/02-10/02-11) with a Python CI pre-compute pipeline that runs openfisca-france in CI and exports static scenario JSON. The browser performs O(1) HashMap lookups — no computation, no WASM. This SUMMARY reflects the current simplified architecture.

## Performance

- **Duration:** 23 min (original codegen) + 8 min (02-11 rewrite)
- **Started:** 2026-05-12T18:28:32Z
- **Completed:** 2026-05-13 (rewritten for hybrid architecture)
- **Tasks:** 3 (original) + 1 (02-11 gap closure)
- **Files modified:** 4

## Accomplishments

- Scenario data format: `ScenarioDoc` JSON contract with `definition` (id, name, description, parameterOverrides) + `results` (Record<number, ScenarioResult>) — directly consumable by TypeScript `ScenarioCache.fromDocs()`
- 3 candidate reform scenarios using openfisca-france Reform API:
  1. **baseline-2025**: Status quo — current law, no overrides
  2. **expansion-2025**: Reduced IR (barème -10%) + increased RSA (+5%) and prime d'activité (+10%)
  3. **consolidation-2025**: TVA normal 22% (was 20%) + allocations familiales modulation 0.5 + APL freeze
- `precompute_scenarios()` pipeline: loads canonical profiles from bilingual_test_fixtures.json, runs computation for each scenario × profile, exports `scenarios-v2025.1.json` with version metadata
- Lazy openfisca imports: `scenario_definitions.py` importable without openfisca installed — enables linting/type-checking in environments without the full Python data science stack
- CI staleness check integrated into scenario-precompute job: validates openfisca-france version consistency

## Task Commits

1. **Task 1 (original): Spike 3-5 representative formulas** — `e563411` (feat)
2. **Task 2 (original): Full code generator for ~200+ variables** — `f61a3e3` (feat)
3. **Task 3 (original): CI staleness check (D-07)** — `0b66eca` (feat)
4. **Task 11-01 (02-11 gap closure): Implement Python scenario pre-compute pipeline** — `488630a` (feat)

## Files Created/Modified

- `packages/data-pipeline/src/scenarios/__init__.py` — Scenario pre-compute package init
- `packages/data-pipeline/src/scenarios/scenario_definitions.py` — 3 candidate reform scenarios with openfisca-france Reform API, lazy imports, `get_scenario_definitions()`
- `packages/data-pipeline/src/scenarios/precompute.py` — Pre-compute pipeline: load fixtures, compute scenario × profile, export JSON; CLI entry point
- `packages/data-pipeline/pyproject.toml` — Added `precompute-scenarios` script entry point

## Decisions Made

- **Hybrid architecture:** Moved all microsimulation computation to a Python CI pre-compute step. The browser performs O(1) HashMap lookups on pre-computed JSON — no computation, no WASM, zero data transfer. This satisfies the privacy-by-design constraint while avoiding the complexity of a Rust formula engine.
- **Reform API usage:** Each scenario defines parameter overrides via `openfisca_core.reforms.Reform` subclass. The `modify_parameters()` method applies overrides to the FranceTaxBenefitSystem. Lazy imports ensure the module is importable without openfisca installed.
- **Flat profile model:** IS and TVA are estimated from income/consumption patterns rather than computed from enterprise data — the flat Profile model lacks enterprise fields (chiffre d'affaires, effectif). IS defaults to 0.0 for individual profiles.

## Deviations from Plan

None — plan executed as designed. The architecture simplification (Plans 02-09/02-10/02-11) retired the codegen pipeline in favor of this pre-compute approach.

## Known Stubs

None — all 3 scenarios are fully defined with concrete parameter overrides and computation logic.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: network | precompute.py | Runs in CI only — queries PyPI for openfisca-france version (accepted risk at dev-time) |

## Issues Encountered

None.

## Next Phase Readiness

- Scenario data format contract is defined and implemented — ready for TypeScript `ScenarioCache.loadFromJSON()` consumption
- Pre-compute pipeline outputs `scenarios-v2025.1.json` with version-locked metadata
- CI integration complete — scenario pre-compute job gates all downstream TypeScript tests

---

*Phase: 02-core-simulation-engines-wasm*
*Completed: 2026-05-12 (original), rewritten: 2026-05-13 (02-11 gap closure)*
