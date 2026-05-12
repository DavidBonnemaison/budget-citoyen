---
phase: 01-data-foundation-rules-engine
plan: 01
subsystem: data-pipeline
tags: [yaml, openfisca, json-schema, jsonschema, pyyaml, tax-rules, rules-as-code, ir, is, tva, cotisations, aides]

# Dependency graph
requires:
  - phase: 01-data-foundation-rules-engine
    provides: RESEARCH.md (OpenFisca YAML format, JSON Schema patterns, project structure)
provides:
  - OpenFisca-compatible YAML parameter files for all 5 tax domains with legislation references
  - Python project foundation with all Phase 1 dependencies at pinned versions
  - JSON Schema Draft 2020-12 definitions for parameter, tax_benefit_system, and synthetic_profile
  - YAML→JSON conversion pipeline with jsonschema validation gate (fail-early)
  - 12 validated JSON outputs from 5 domains confirming end-to-end pipeline works
affects:
  - Phase 2 (WASM Engine): JSON output consumed by serde_json
  - Plan 04 (bilingual validation): YAML file paths and pyproject.toml dependencies

# Tech tracking
tech-stack:
  added: [pyyaml 6.0.3, jsonschema 4.25.1, sdv 1.36.1, opendp 0.14.2, pyarrow 24.0.0, tomli 2.4.1]
  patterns:
    - "Pattern: OpenFisca YAML parameter format — description, metadata.reference, values.{date}.value, brackets[].threshold/rate"
    - "Pattern: Build-time YAML→JSON conversion with JSON Schema validation gate (fail-early)"
    - "Pattern: PyYAML datetime.date keys → ISO string conversion for JSON Schema compatibility"
    - "Pattern: _date_keys_to_strings() recursive conversion before validation"

key-files:
  created:
    - packages/tax-rules/parameters/ir/bareme.yaml (5 IR brackets, 10 date entries)
    - packages/tax-rules/parameters/ir/deductions.yaml (frais professionnels parameters)
    - packages/tax-rules/parameters/ir/credits.yaml (3 tax credits with references)
    - packages/tax-rules/parameters/is/taux.yaml (IS rates: normal 25%, PME 15%, contribution 3.3%)
    - packages/tax-rules/parameters/tva/taux.yaml (4 TVA rates: 20%, 10%, 5.5%, 2.1%)
    - packages/tax-rules/parameters/cotisations/salariales.yaml (8 employee contribution rates)
    - packages/tax-rules/parameters/cotisations/patronales.yaml (8 employer contribution rates)
    - packages/tax-rules/parameters/cotisations/csg_crds.yaml (CSG 6.8%+2.4%, CRDS 0.5%)
    - packages/tax-rules/parameters/aides/rsa.yaml (RSA 635.71€, formula)
    - packages/tax-rules/parameters/aides/apl.yaml (APL by zone, rent ceilings)
    - packages/tax-rules/parameters/aides/allocations_familiales.yaml (3 income tiers)
    - packages/tax-rules/parameters/aides/prime_activite.yaml (622.63€ base, 61% cumul)
    - packages/data-pipeline/pyproject.toml (12 deps, requires-python>=3.10)
    - packages/data-pipeline/src/schemas/parameter.schema.json (Draft 2020-12, brackets + values)
    - packages/data-pipeline/src/schemas/tax_benefit_system.schema.json (5-domain bundle)
    - packages/data-pipeline/src/schemas/synthetic_profile.schema.json (12 properties)
    - packages/data-pipeline/src/yaml2json/convert.py (188 lines, fail-early validation)
    - packages/data-pipeline/src/yaml2json/validate.py (load_schema, validate_rules, validate_file)
  modified: []

key-decisions:
  - "All date keys locked to 2025-01-01 per D-15 reference year — grep confirms 10+ occurrences per file"
  - "PyYAML datetime.date keys converted to ISO strings before JSON Schema validation (Draft202012Validator requires string property names)"
  - "index.yaml files excluded from JSON conversion (metadata-only, not parameters)"
  - "JSON output preserves directory structure: {yaml_dir}/ir/bareme.yaml → {output_dir}/ir/bareme.json"

patterns-established:
  - "Pattern: YAML tax rule authoring — description + metadata.reference (legifrance.gouv.fr) + values.{date} per parameter"
  - "Pattern: Brackets structure — threshold/rate pairs with sub-values at date keys for progressive taxation"
  - "Pattern: Build-time validation gate — jsonschema.Draft202012Validator.iter_errors() before json.dump()"

requirements-completed: [DATA-01]

# Metrics
duration: 15min
completed: 2026-05-12
---

# Phase 1 Plan 01: Tax Rules YAML Authoring + JSON Schema Validation Pipeline Summary

**17 OpenFisca-compatible YAML parameter files across 5 tax domains with legislation references, automated YAML→JSON conversion with Draft 2020-12 JSON Schema validation gate proving 12 files convert without errors**

## Performance

- **Duration:** 15 min
- **Started:** 2026-05-12T06:24:15Z
- **Completed:** 2026-05-12T06:39:33Z
- **Tasks:** 2
- **Files modified:** 26

## Accomplishments
- 17 YAML parameter files (14 data + 3 domain indexes) across 5 domains: IR, IS, TVA, cotisations sociales, aides sociales — all with legifrance.gouv.fr legislation references and 2025 values
- 3 JSON Schema Draft 2020-12 definitions (parameter, tax_benefit_system, synthetic_profile) that self-validate via `Draft202012Validator.check_schema()`
- YAML→JSON conversion pipeline with fail-early validation — all 12 parameter files across all 5 domains convert without schema violations
- Python project foundation with all Phase 1 dependencies at pinned versions (sdv==1.36.1, opendp==0.14.2, pyarrow==24.0.0, jsonschema==4.25.1) and `requires-python >=3.10`
- Zero `serde_yaml` imports — YAML processing confined to build-time Python pipeline (D-02)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create project structure, pyproject.toml, and all YAML parameter files for 5 tax domains** - `99eb13c` (feat)
2. **Task 2: Create JSON Schema definitions and YAML→JSON conversion + validation pipeline** - `ca2d8be` (feat)

## Files Created/Modified

### Tax Rules YAML (17 files)
- `packages/tax-rules/parameters/ir/bareme.yaml` — IR brackets: thresholds [0, 11497, 29315, 83823, 180648], rates [0.0, 0.11, 0.30, 0.41, 0.45]
- `packages/tax-rules/parameters/ir/deductions.yaml` — Frais professionnels (10% abattement, plafond 14329€)
- `packages/tax-rules/parameters/ir/credits.yaml` — Crédits d'impôt (emploi à domicile 50%, dons 66%, garde enfants 50%)
- `packages/tax-rules/parameters/is/taux.yaml` — IS: normal 25%, réduit PME 15%, contribution sociale 3.3%
- `packages/tax-rules/parameters/tva/taux.yaml` — TVA: 20%, 10%, 5.5%, 2.1%
- `packages/tax-rules/parameters/cotisations/salariales.yaml` — 8 taux cotisations salariales (vieillesse, AGIRC-ARRCO)
- `packages/tax-rules/parameters/cotisations/patronales.yaml` — 8 taux cotisations patronales (maladie, allocations familiales, chômage)
- `packages/tax-rules/parameters/cotisations/csg_crds.yaml` — CSG 9.2% + CRDS 0.5% sur 98.25% du brut
- `packages/tax-rules/parameters/aides/rsa.yaml` — RSA 635.71€, formule avec taux cumul 38%
- `packages/tax-rules/parameters/aides/apl.yaml` — APL par zone géographique (loyers plafonds)
- `packages/tax-rules/parameters/aides/allocations_familiales.yaml` — Allocations familiales (3 tranches, modulation revenus)
- `packages/tax-rules/parameters/aides/prime_activite.yaml` — Prime d'activité 622.63€, bonification 181.87€
- 5 domain index files (`index.yaml`) documenting parameter file inventory
- `packages/tax-rules/README.md` — Domain structure, reference year 2025, legislation source format, update cadence
- `packages/tax-rules/variables/README.md` — Variable definition placeholder for Phase 2 contract

### Data Pipeline (9 files)
- `packages/data-pipeline/pyproject.toml` — 12 pinned dependencies, requires-python >=3.10, pytest config
- `packages/data-pipeline/src/schemas/parameter.schema.json` — Draft 2020-12 schema with values (date-keyed) + brackets (threshold/rate) support
- `packages/data-pipeline/src/schemas/tax_benefit_system.schema.json` — 5-domain top-level rules bundle schema
- `packages/data-pipeline/src/schemas/synthetic_profile.schema.json` — 12-property synthetic household profile schema
- `packages/data-pipeline/src/yaml2json/__init__.py` — Exports convert_all, validate_all
- `packages/data-pipeline/src/yaml2json/convert.py` — 188-line conversion module with _date_keys_to_strings(), convert_yaml_to_json()
- `packages/data-pipeline/src/yaml2json/validate.py` — load_schema(), validate_rules(), validate_file() with Draft202012Validator

## Decisions Made
- All date keys locked to `2025-01-01` per D-15 — verified via grep showing 10+ occurrences per domain
- PyYAML `datetime.date` keys converted to ISO strings via recursive `_date_keys_to_strings()` before JSON Schema validation (jsonschema patternProperties requires string keys)
- `index.yaml` files excluded from JSON conversion (domain metadata only, not parameters)
- JSON output preserves YAML directory structure for Phase 2 consumption via serde_json

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed YAML colon-in-string syntax error in prime_activite.yaml**
- **Found during:** Task 1 (YAML authoring)
- **Issue:** Description text "Bonification individuelle (condition: revenu d'activité ≥ 0,5 SMIC sur 3 mois)" contained an unquoted colon, causing PyYAML to interpret it as a key-value separator
- **Fix:** Wrapped description in double quotes to treat colon as literal text
- **Files modified:** `packages/tax-rules/parameters/aides/prime_activite.yaml`
- **Verification:** All 17 YAML files parse without error via `yaml.safe_load()`
- **Committed in:** `99eb13c` (part of Task 1 commit)

**2. [Rule 3 - Blocking] datetime.date keys incompatible with JSON Schema patternProperties**
- **Found during:** Task 2 (JSON conversion pipeline)
- **Issue:** PyYAML parses `2025-01-01` as `datetime.date` objects, but `jsonschema.Draft202012Validator` expects string property names for `patternProperties` matching. Conversion failed with "expected string or bytes-like object"
- **Fix:** Added `_date_keys_to_strings()` recursive converter that transforms all `datetime.date` keys to ISO format strings before validation. Applied as pre-processing step in `convert_yaml_to_json()` before the schema validation gate.
- **Files modified:** `packages/data-pipeline/src/yaml2json/convert.py`
- **Verification:** All 12 parameter files across 5 domains convert and validate without errors
- **Committed in:** `ca2d8be` (part of Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both fixes essential for pipeline operation. No architectural changes — date-to-string conversion is the standard approach for bridging PyYAML's type-rich parsing with JSON Schema's string-based pattern matching. No scope creep.

## Issues Encountered
- Python 3.9.6 on macOS cannot use `tomllib` (3.11+); installed `tomli` for TOML validation and `pyyaml` + `jsonschema` for test verification. The `pyproject.toml` correctly declares `requires-python >=3.10` — the system Python needs upgrading before full dependency installation.
- Plan acceptance criteria says schemas must contain "Draft 2020-12" substring, but the standard `$schema` URL uses lowercase `draft/2020-12`. Verified schemas self-validate via `Draft202012Validator.check_schema()` which is the authoritative test.

## User Setup Required

None — no external service configuration required for this plan. The Python virtual environment setup and dependency installation will be documented in Plan 03 (synthetic data pipeline).

## Threat Mitigation Status

| Threat ID | Status | Evidence |
|-----------|--------|----------|
| T-01-01 (YAML parsing tampering) | **Mitigated** | JSON Schema Draft 2020-12 validation gate runs BEFORE any JSON is written. Missing `description` correctly caught by negative test. |
| T-01-02 (output artifact tampering) | **Deferred to Plan 04** | SHA-256 integrity hashes on output JSON implemented in Plan 04 CI |
| T-01-03 (dependency version tampering) | **Partially mitigated** | Pinned versions in pyproject.toml (sdv==1.36.1, opendp==0.14.2, pyarrow==24.0.0, jsonschema==4.25.1). `pip install --require-hashes` enforced in Plan 04 CI. |
| T-01-04 (legifrance references disclosure) | **Accepted** | Legislation references are public URLs. No sensitive data exposure. |

## Next Phase Readiness
- 12 validated JSON parameter files ready for Phase 2 WASM engine consumption via `serde_json`
- YAML file paths locked — Plan 04 (bilingual validation) can reference exact paths from `files_modified` interface contract
- `pyproject.toml` contains all Phase 1 dependencies — Plans 02, 03, and 04 do not modify it
- Ready for Plan 02 (synthetic data pipeline infrastructure)

---
*Phase: 01-data-foundation-rules-engine*
*Plan: 01*
*Completed: 2026-05-12*
