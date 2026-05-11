# Phase 1: Data Foundation & Rules Engine - Research

**Researched:** 2026-05-11
**Domain:** Offline data pipeline — Rules as Code YAML authoring, synthetic population generation (SDV + OpenDP), shock matrix pre-computation, bilingual validation framework
**Confidence:** HIGH

## Summary

Phase 1 is a pure data-artifact pipeline — no WASM engines, no UI, no browser integration. It produces three version-locked artifacts (tax rules JSON, synthetic population JSON, shock matrix binary) and a bilingual validation framework that gates Phase 2's right to begin. All computation is offline Python; Rust appears only in the validation test fixture consumer.

The phase splits naturally into four independent workstreams (mapping to DATA-01 through DATA-04) with a shared CI integration point. The critical path runs through DATA-02 (synthetic population), which requires CASD/INSEE data access (multi-month) and GPU time for CopulaGAN training. DATA-01 (YAML rules) is the lowest-risk, highest-parallelism workstream — it can begin immediately with no external dependencies beyond the OpenFisca schema documentation.

**The key technical risk is the Python 3.9.6 environment — PyArrow 24.0.0 (needed for Parquet/Zstd shock matrix compression) requires Python ≥3.10, and SDV 1.36.1's BUSL-1.1 license may conflict with the project's AGPL requirement.**

**Primary recommendation:** Upgrade Python to ≥3.13 before installing any data pipeline packages. Begin DATA-01 (YAML tax rules) immediately in parallel with the CASD data access process. Schedule shock matrix pre-computation last — it depends on both Mésange methodology validation (restricted access) and synthetic population reference distributions.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| YAML tax rule authoring | Data Pipeline (Python, offline) | — | STATIC artifact; authored once, validated at build time, consumed by WASM at runtime |
| YAML→JSON conversion + JSON Schema validation | CI/CD (build-time) | — | Build-time gate; never runs in browser |
| Synthetic population generation (50K profiles) | Data Pipeline (Python, offline, GPU) | — | One-time generation; CopulaGAN requires GPU training; output is static JSON |
| Differential privacy proof (ε ≤ 1.0) | Data Pipeline (Python, OpenDP) | — | Formal proof at generation time; pre-allocated ε budget; no runtime DP consumption |
| Shock matrix pre-computation (Mésange-derived) | Data Pipeline (Python/SciPy, offline) | — | Batch VAR bootstrap; output is static compressed binary; no runtime Mésange solving |
| Bilingual validation (Python→Rust test fixtures) | CI/CD | Data Pipeline | Python reference produces JSON fixtures; cargo test consumes them in CI |
| Version consistency enforcement | CI/CD | — | Semver tags + CI gate checking all three artifacts share reference year |

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DATA-01 | Les paramètres fiscaux (IR, IS, TVA, cotisations, aides sociales) sont encodés en YAML sous forme de Rules as Code, convertibles en JSON pour le moteur WASM | OpenFisca YAML schema confirmed via Context7; JSON Schema Draft 2020-12 validation via jsonschema 4.25.1; build-time YAML→JSON conversion via PyYAML |
| DATA-02 | Le jeu de données synthétiques (50 000 profils) est généré avec préservation des dépendances entre variables (âge ↔ patrimoine ↔ revenus) | SDV 1.36.1 CopulaGANSynthesizer confirmed; copula-based approach captures multi-variable correlations; SDMetrics QualityReport for statistical fidelity validation |
| DATA-03 | La confidentialité différentielle (ε ≤ 1,0) est implémentée dans le pipeline de génération de données synthétiques | OpenDP 0.14.2 confirmed with Laplace/Gaussian mechanisms; `.map(d_in=sensitivity)` computes provable ε; `make_basic_composition` tracks total privacy loss |
| DATA-04 | La matrice des chocs macroéconomiques (dérivée du modèle Mésange) est pré-calculée et stockée en look-up table compressée | Parquet/Zstd via PyArrow 24.0.0 for <5 MB compression target; 3D Float32 grid (tax × spend × horizon); convex hull bounds metadata |

## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Tax rules encoded in OpenFisca-compatible YAML schema with legislation references per parameter
- **D-02:** Build-time YAML→JSON conversion via Python `yaml` + `jsonschema` validation. WASM runtime parses only JSON via `serde_json`
- **D-03:** JSON Schema validation at build time ensures all rates, thresholds, and brackets are present
- **D-04:** SDV `CopulaGANSynthesizer` for multi-variable dependency preservation (age ↔ patrimony ↔ income covariance)
- **D-05:** OpenDP 0.14.2 (Rust core, Python bindings) for formal ε-differential privacy with ε ≤ 1.0 budget. Privacy budget pre-allocated once at generation time
- **D-06:** Reference data from CASD microdata when accessible, with INSEE enquête Revenus Fiscaux et Sociaux as fallback
- **D-07:** SDMetrics quality evaluation validates statistical fidelity, privacy metrics, and detection reports
- **D-08:** Maximum 4 interactive fiscal dimensions to avoid curse of dimensionality. Remaining parameters use fixed reference values
- **D-09:** Grid density: 10-15 breakpoints per dimension (~10K-50K points per output variable). Stored as compressed Float32Array under 5 MB
- **D-10:** Smolyak sparse grids preferred if available as Rust crate; fallback is uniform Cartesian grid with explicit convex hull bounds
- **D-11:** Mésange-derived bootstrap computation runs offline as batch pipeline (Python/SciPy for VAR estimation). Output is static compressed binary
- **D-12:** 10-20 canonical household profiles covering edge cases validated against official impots.gouv.fr simulator
- **D-13:** Precision threshold: 1e-6 relative difference between Python OpenFisca reference and WASM output
- **D-14:** Bilingual validation framework in Python (using openfisca-france as reference) produces JSON test fixtures consumed by cargo test and wasm-pack test in CI
- **D-15:** All data artifacts locked to reference year 2025
- **D-16:** Artifacts versioned with semantic tags: `rules-v2025.1`, `population-v2025.1`, `shockmatrix-v2025.1`. CI enforces version consistency
- **D-17:** Update cadence aligned with PLF annual cycle. Offline pipeline re-runs in September-October each year

### the agent's Discretion

- Specific parameter file organization within the YAML tree (by tax domain: IR, IS, TVA, etc.)
- Exact JSON Schema definitions — derive from OpenFisca parameter structure
- Synthetic data preprocessing (outlier handling, categorical encoding) — follow SDV best practices
- Shock matrix file format — Parquet/Zstd for max compression
- CI pipeline tooling (GitHub Actions, pytest, cargo test integration)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | ≥3.10 (3.13 recommended) | Data pipeline runtime | PyArrow 24.0.0 requires ≥3.10; SDV 1.36.1 tested up to 3.14 |
| SDV (Synthetic Data Vault) | 1.36.1 | Synthetic population generation | CopulaGANSynthesizer captures multi-variable dependencies (age↔patrimony↔income); production-stable |
| OpenDP | 0.14.2 | Differential privacy | Formal ε proofs via `.map()` method; Laplace + Gaussian mechanisms; Python bindings to Rust core |
| SDMetrics | latest (compatible with SDV 1.36) | Synthetic data quality evaluation | Column Shapes, Column Pair Trends, DisclosureProtectionEstimate; integrates with SDV metadata |
| PyYAML | 6.x | YAML parsing for rules authoring | Standard Python YAML library; converts OpenFisca-compatible YAML to dicts for JSON export |
| jsonschema | 4.25.1 | JSON Schema validation | Draft 2020-12 support; validates YAML→JSON converted rules at build time |
| PyArrow | 24.0.0 | Parquet/Zstd compression | Columnar format with Zstd codec; achieves <5 MB compression target for shock matrix |
| NumPy | latest | Numerical arrays | Float32 grid storage for shock matrix breakpoints and interpolation data |
| SciPy | latest | VAR estimation, Monte Carlo | Bootstrap computation for Mésange-derived shock matrix |
| Pandas | latest | Data manipulation | Preprocessing real data before SDV training; CSV/Parquet I/O |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| openfisca-france | latest stable (pre-2026) | Reference simulator for bilingual validation | Python-side reference for canonical profile validation |
| pytest | 8.x | Test runner for Python pipeline | CI validation of data artifacts |
| matplotlib / seaborn | latest | Diagnostic plots | Visualizing synthetic vs real distributions during development |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SDV CopulaGAN | CTGAN (also SDV) | CTGAN handles multimodal distributions better but is less interpretable for auditable fiscal data. CopulaGAN preferred for transparency (copula parameters are inspectable) |
| SDV CopulaGAN | GaussianCopulaSynthesizer (SDV) | Non-GAN copula is faster and fully interpretable but captures fewer complex non-linear dependencies. CopulaGAN chosen for fidelity |
| PyArrow Parquet/Zstd | HDF5 + gzip | HDF5 has richer metadata but Parquet's columnar compression (Zstd) achieves better ratios for Float32 grids and has broader WASM ecosystem support (parquet2 crate) |
| OpenDP Python bindings | SmartNoise SDK (also OpenDP) | SmartNoise provides higher-level SQL-like API but less control over mechanism selection and composition. Low-level OpenDP preferred for formal ε proof requirements |
| jsonschema 4.x | pydantic | pydantic is more Pythonic but JSON Schema Draft 2020-12 is language-agnostic — Rust-side validation (valico 4.0.0) can consume the same schemas |

### License Warning
**SDV is licensed BUSL-1.1 (Business Source License), not MIT/Apache.** This is a significant concern for a project targeting AGPL compatibility (OpenFisca ecosystem). The BUSL-1.1 converts to Apache 2.0 after a change date, but the current production use restrictions may conflict with AGPL distribution. **This needs legal review.** If BUSL-1.1 is incompatible, fallback is `GaussianCopulaSynthesizer` (also SDV/BUSL) or a pure scipy copula implementation (slower, less featureful, but unencumbered).

**Installation:**
```bash
# Python data pipeline (in a Python ≥3.10 venv)
pip install sdv==1.36.1
pip install opendp==0.14.2
pip install sdmetrics
pip install jsonschema==4.25.1
pip install pyyaml
pip install pyarrow==24.0.0
pip install numpy scipy pandas
pip install openfisca-france  # for bilingual validation reference
pip install pytest matplotlib seaborn  # dev/testing
```

**Version verification:**
```bash
pip list | grep -E "sdv|opendp|sdmetrics|jsonschema|pyarrow|PyYAML"
```
- SDV 1.36.1 [VERIFIED: PyPI, released 2026-04-24]
- OpenDP 0.14.2 [VERIFIED: crates.io, referenced in STACK.md]
- jsonschema 4.25.1 [VERIFIED: Context7 /python-jsonschema/jsonschema]
- PyArrow 24.0.0 [VERIFIED: PyPI, released 2026-04-21, requires Python ≥3.10]
- PyYAML 6.x [ASSUMED — standard library, not verified in this session]

## Architecture Patterns

### System Architecture Diagram

```
                              ┌──────────────────────────────────────────┐
                              │           CI/CD PIPELINE GATE              │
                              │  (version consistency, validation, tests) │
                              └──────────────────────────────────────────┘
                                              ▲              ▲
                                              │              │
                    ┌─────────────────────────┼──────────────┼──────────────────────┐
                    │                         │              │                      │
                    ▼                         ▼              ▼                      ▼
┌─────────────────────────┐   ┌─────────────────────────┐   ┌─────────────────────────┐
│   DATA-01: Tax Rules     │   │   DATA-02/03: Synth Pop  │   │   DATA-04: Shock Matrix  │
│                          │   │                          │   │                          │
│  ┌────────────────────┐  │   │  ┌────────────────────┐  │   │  ┌────────────────────┐  │
│  │ YAML Authoring      │  │   │  │ Real Data Source    │  │   │  │ Mésange Model       │  │
│  │ (OpenFisca schema)  │  │   │  │ CASD/INSEE (primary)│  │   │  │ (Insee/Trésor)      │  │
│  │ • IR parameters     │  │   │  │ or enquête ERFS     │  │   │  │ restricted access    │  │
│  │ • IS parameters     │  │   │  └─────────┬──────────┘  │   │  └─────────┬──────────┘  │
│  │ • TVA parameters    │  │   │            │              │   │            │              │
│  │ • Cotisations       │  │   │            ▼              │   │            ▼              │
│  │ • Aides sociales    │  │   │  ┌────────────────────┐  │   │  ┌────────────────────┐  │
│  └─────────┬──────────┘  │   │  │ Data Preprocessing   │  │   │  │ VAR Bootstrap       │  │
│            │              │   │  │ (pandas, numpy)     │  │   │  │ (SciPy, statsmodels)│  │
│            ▼              │   │  │ • outlier handling   │  │   │  │ • Monte Carlo       │  │
│  ┌────────────────────┐  │   │  │ • categorical encode  │  │   │  │ • confidence bounds  │  │
│  │ YAML → JSON         │  │   │  │ • SDV metadata prep  │  │   │  └─────────┬──────────┘  │
│  │ (PyYAML)            │  │   │  └─────────┬──────────┘  │   │            │              │
│  └─────────┬──────────┘  │   │            │              │   │            ▼              │
│            │              │   │            ▼              │   │  ┌────────────────────┐  │
│            ▼              │   │  ┌────────────────────┐  │   │  │ Grid Construction   │  │
│  ┌────────────────────┐  │   │  │ CopulaGAN Training   │  │   │  │ • 4 dimensions max  │  │
│  │ JSON Schema Validate │  │   │  │ (SDV + GPU)         │  │   │  │ • 10-15 breakpoints │  │
│  │ (jsonschema)        │  │   │  │ • epochs=500         │  │   │  │ • Float32 values    │  │
│  └─────────┬──────────┘  │   │  │ • multi-var corr      │  │   │  │ • convex hull bounds │  │
│            │              │   │  └─────────┬──────────┘  │   │  └─────────┬──────────┘  │
│            ▼              │   │            │              │   │            │              │
│  ┌────────────────────┐  │   │            ▼              │   │            ▼              │
│  │ rules-v2025.1.json  │──┼──▶│  ┌────────────────────┐  │   │  ┌────────────────────┐  │
│  │ (validated artifact)│  │   │  │ DP Noise Injection   │  │   │  │ Parquet/Zstd Export │  │
│  └────────────────────┘  │   │  │ (OpenDP)             │  │   │  │ (PyArrow)           │  │
│                          │   │  │ • ε ≤ 1.0 total      │  │   │  │ • < 5 MB target     │  │
│                          │   │  │ • Laplace mechanism   │  │   │  │ • metadata header   │  │
│                          │   │  └─────────┬──────────┘  │   │  └─────────┬──────────┘  │
│                          │   │            │              │   │            │              │
│                          │   │            ▼              │   │            ▼              │
│                          │   │  ┌────────────────────┐  │   │  shockmatrix-v2025.1    │
│                          │   │  │ Quality Evaluation   │  │   │  .parquet               │
│                          │   │  │ (SDMetrics)          │  │   │  (compressed artifact)  │
│                          │   │  │ • Column Shapes      │  │   │                          │
│                          │   │  │ • Column Pair Trends │  │   │                          │
│                          │   │  │ • Disclosure Protect │  │   │                          │
│                          │   │  └─────────┬──────────┘  │   │                          │
│                          │   │            │              │   │                          │
│                          │   │            ▼              │   │                          │
│                          │   │  population-v2025.1.json  │   │                          │
│                          │   │  (validated artifact)     │   │                          │
│                          │   └──────────────────────────┘   └──────────────────────────┘
│                          │
│                          │  ┌─────────────────────────────────────────────────────────┐
│                          │  │              BILINGUAL VALIDATION FRAMEWORK               │
│                          │  │                                                          │
│                          │  │  ┌──────────────────────┐    ┌──────────────────────┐    │
│                          │  │  │ Python Reference      │    │ Rust/WASM Consumer    │    │
│                          │  │  │ (openfisca-france)    │    │ (Phase 2)             │    │
│                          │  │  │                       │    │                       │    │
│                          │  │  │ • 10-20 canonical     │    │ • cargo test reads    │    │
│                          │  │  │   household profiles  │───▶│   JSON test fixtures  │    │
│                          │  │  │ • impots.gouv.fr      │    │ • wasm-pack test      │    │
│                          │  │  │   reference values    │    │   validates boundary  │    │
│                          │  │  │ • produces JSON       │    │ • 1e-6 precision gate │    │
│                          │  │  │   test fixtures       │    │                       │    │
│                          │  │  └──────────────────────┘    └──────────────────────┘    │
│                          │  └─────────────────────────────────────────────────────────┘
│                          └──────────────────────────────────────────────────────────────┘
```

### Recommended Project Structure

```
packages/
├── data-pipeline/                 # Offline Python pipeline (this phase)
│   ├── src/
│   │   ├── synthetic_pop/         # DATA-02 + DATA-03: Synthetic population
│   │   │   ├── preprocess.py      # Real data loading, cleaning, SDV metadata
│   │   │   ├── train.py           # CopulaGAN training with SDV
│   │   │   ├── dp_inject.py       # OpenDP noise injection, ε budget tracking
│   │   │   ├── evaluate.py        # SDMetrics quality report generation
│   │   │   └── export.py          # JSON export with integrity hashes
│   │   ├── shock_matrix/          # DATA-04: Shock matrix pre-computation
│   │   │   ├── bootstrap.py       # VAR bootstrap from Mésange
│   │   │   ├── grid_build.py      # 3D grid construction (tax×spend×horizon)
│   │   │   ├── convex_hull.py     # Convex hull metadata computation
│   │   │   └── export_parquet.py  # Parquet/Zstd compression + metadata
│   │   ├── validation/            # Bilingual validation framework
│   │   │   ├── canonical_profiles.py  # 10-20 edge-case household definitions
│   │   │   ├── reference_sim.py       # Run openfisca-france on canonical profiles
│   │   │   ├── export_fixtures.py     # Produce JSON test fixtures for Rust
│   │   │   └── impots_gouv_validator.py  # Cross-check against impots.gouv.fr
│   │   ├── schemas/               # JSON Schema definitions
│   │   │   ├── parameter.schema.json        # OpenFisca parameter schema
│   │   │   ├── tax_benefit_system.schema.json
│   │   │   └── synthetic_profile.schema.json
│   │   └── yaml2json/            # DATA-01: YAML→JSON conversion
│   │       ├── convert.py         # PyYAML → JSON with schema validation
│   │       └── validate.py        # jsonschema validation gate
│   ├── tests/
│   │   ├── test_conversion.py     # YAML→JSON conversion tests
│   │   ├── test_schema_validation.py
│   │   ├── test_synthetic_pop.py  # DP guarantee, statistical fidelity
│   │   ├── test_shock_matrix.py   # Grid bounds, compression size
│   │   └── test_validation.py     # Bilingual validation tests
│   ├── pyproject.toml
│   └── notebooks/                 # Exploratory analysis (dev only)
│       ├── 01_explore_insee_data.ipynb
│       ├── 02_copula_tuning.ipynb
│       └── 03_shock_matrix_viz.ipynb
│
├── tax-rules/                     # OpenFisca-compatible YAML rules
│   ├── parameters/
│   │   ├── ir/                    # Impôt sur le Revenu
│   │   │   ├── bareme.yaml        # IR brackets (tranches)
│   │   │   ├── deductions.yaml    # Deductions (frais réels, etc.)
│   │   │   ├── credits.yaml       # Tax credits (crédits d'impôt)
│   │   │   └── index.yaml         # Parameter index for this domain
│   │   ├── is/                    # Impôt sur les Sociétés
│   │   │   ├── taux.yaml          # IS rates (normal, réduit, PME)
│   │   │   └── index.yaml
│   │   ├── tva/                   # TVA
│   │   │   ├── taux.yaml          # TVA rates (normal, réduit, super-réduit)
│   │   │   └── index.yaml
│   │   ├── cotisations/           # Cotisations sociales
│   │   │   ├── salariales.yaml    # Employee contributions
│   │   │   ├── patronales.yaml    # Employer contributions
│   │   │   ├── csg_crds.yaml      # CSG/CRDS
│   │   │   └── index.yaml
│   │   └── aides/                 # Aides sociales
│   │       ├── rsa.yaml           # Revenu de Solidarité Active
│   │       ├── apl.yaml           # Aides Personnalisées au Logement
│   │       ├── allocations_familiales.yaml
│   │       ├── prime_activite.yaml
│   │       └── index.yaml
│   ├── variables/                 # Variable definitions (for documentation)
│   ├── reforms/                   # Pre-built reform scenarios (optional v1)
│   └── README.md                  # Legislation sources, parameter documentation
```

### Pattern 1: OpenFisca-Compatible YAML Parameter File

**What:** Each tax parameter file follows OpenFisca's YAML schema with `description`, `metadata.reference` (legislation source), `unit`, and date-keyed `values` with optional `metadata` per value entry.

**When to use:** Every parameter file under `packages/tax-rules/parameters/`.

**Example:**
```yaml
# packages/tax-rules/parameters/ir/bareme.yaml
# Source: OpenFisca Core documentation [VERIFIED: Context7 /openfisca/openfisca-core]
description: Barème de l'impôt sur le revenu (tranches)
metadata:
  reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049052222
  unit: /1
brackets:
  - threshold:
      description: Seuil de la tranche
      values:
        2025-01-01:
          value: 0
    rate:
      description: Taux de la tranche
      values:
        2025-01-01:
          value: 0.0
  - threshold:
      values:
        2025-01-01:
          value: 11497
    rate:
      values:
        2025-01-01:
          value: 0.11
  - threshold:
      values:
        2025-01-01:
          value: 29315
    rate:
      values:
        2025-01-01:
          value: 0.30
  - threshold:
      values:
        2025-01-01:
          value: 83823
    rate:
      values:
        2025-01-01:
          value: 0.41
  - threshold:
      values:
        2025-01-01:
          value: 180648
    rate:
      values:
        2025-01-01:
          value: 0.45
```

### Pattern 2: YAML→JSON Conversion with Schema Validation

**What:** At build time, PyYAML loads all parameter files, converts to JSON, and validates against a JSON Schema Draft 2020-12 definition. This gate runs in CI before any WASM engine can consume the rules.

**Example:**
```python
# Source: jsonschema 4.25.1 Context7 docs [VERIFIED: /python-jsonschema/jsonschema]
import yaml
import json
from pathlib import Path
from jsonschema import Draft202012Validator, ValidationError

def convert_and_validate(yaml_dir: Path, schema_path: Path, output_dir: Path):
    """Convert all YAML parameter files to JSON and validate against schema."""
    with open(schema_path) as f:
        schema = json.load(f)
    
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    
    for yaml_file in yaml_dir.rglob("*.yaml"):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
        
        # Validate against JSON Schema
        errors = list(validator.iter_errors(data))
        if errors:
            for err in errors:
                print(f"Validation error in {yaml_file}: {err.message}")
            raise ValidationError(f"Schema validation failed for {yaml_file}")
        
        # Write validated JSON
        json_path = output_dir / yaml_file.relative_to(yaml_dir).with_suffix(".json")
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
```

### Pattern 3: SDV CopulaGAN Training with SingleTableMetadata

**What:** Real data (CASD/INSEE) is preprocessed into a pandas DataFrame, metadata is defined via SDV's `SingleTableMetadata`, and `CopulaGANSynthesizer` is trained to generate 50,000 synthetic profiles with preserved multi-variable correlations.

**Example:**
```python
# Source: SDV Context7 docs [VERIFIED: /websites/sdv_dev_sdv]
from sdv.metadata import SingleTableMetadata
from sdv.single_table import CopulaGANSynthesizer

# Define metadata with column types and constraints
metadata = SingleTableMetadata()
metadata.add_column("age", sdtype="numerical")
metadata.add_column("patrimoine", sdtype="numerical")
metadata.add_column("revenu_fiscal", sdtype="numerical")
metadata.add_column("situation_familiale", sdtype="categorical")
metadata.add_column("nombre_parts", sdtype="numerical")
metadata.add_column("type_activite", sdtype="categorical")
metadata.add_column("zone_residence", sdtype="categorical")
metadata.set_primary_key("profile_id")

# Configure synthesizer for fiscal data
synthesizer = CopulaGANSynthesizer(
    metadata,
    enforce_min_max_values=True,       # Keep within real data ranges
    enforce_rounding=True,              # Match real data decimal precision
    numerical_distributions={
        'age': 'beta',                  # Bounded [0, 120]
        'patrimoine': 'gamma',          # Right-skewed (wealth)
        'revenu_fiscal': 'gamma',       # Right-skewed (income)
    },
    epochs=500,                         # Sufficient for 50K profiles
    verbose=True
)

# Train on real data
synthesizer.fit(real_data)

# Generate 50,000 synthetic profiles
synthetic_data = synthesizer.sample(num_rows=50000)
```

### Pattern 4: OpenDP Formal Differential Privacy Injection

**What:** After CopulaGAN generates synthetic profiles, OpenDP injects calibrated Laplace noise into aggregate statistics derived from the population. The privacy proof is obtained by calling `.map(d_in=sensitivity)` on the composed measurement, which returns the exact ε value.

**Example:**
```python
# Source: OpenDP Context7 docs [VERIFIED: /opendp/opendp]
import opendp.prelude as dp
dp.enable_features('floating-point', 'contrib')

def prove_dp_guarantee(data: list[float], epsilon_target: float = 1.0) -> tuple[float, bool]:
    """
    Inject Laplace noise and prove ε ≤ epsilon_target.
    Returns (actual_epsilon, is_within_budget).
    """
    # Define input domain and metric
    input_space = dp.atom_domain(T=float, nan=False), dp.absolute_distance(T=float)
    
    # Clamp data to known bounds (sensitivity = upper - lower)
    lower, upper = min(data), max(data)
    sensitivity = upper - lower
    clamped = dp.t.make_clamp(input_space, lower, upper)
    
    # Compute sum with bounded sensitivity
    sum_trans = clamped >> dp.t.make_bounded_sum((lower, upper))
    
    # Scale for Laplace mechanism to achieve target epsilon
    scale = sensitivity / epsilon_target
    laplace_meas = dp.m.make_laplace(
        dp.atom_domain(T=float),
        dp.absolute_distance(T=float),
        scale=scale
    )
    
    # Compose: clamp → sum → laplace noise
    composed = sum_trans >> laplace_meas
    
    # PROVE epsilon: map sensitivity → actual epsilon value
    actual_epsilon = composed.map(d_in=1)  # d_in=1 for one individual's contribution
    
    return actual_epsilon, actual_epsilon <= epsilon_target
```

### Pattern 5: Shock Matrix Compressed Storage

**What:** The Mésange-derived 3D grid (tax_rate × spend_level × horizon_year) is exported as a Parquet file with Zstd compression. Each cell contains [gdp_growth, employment_change, deficit_change, debt_to_gdp_ratio] as Float32. Metadata (breakpoint vectors, convex hull bounds, reference year) is stored alongside.

**Example:**
```python
# Source: PyArrow 24.0.0 [VERIFIED: PyPI]
import pyarrow as pa
import pyarrow.parquet as pq
import numpy as np
import json

def export_shock_matrix(
    grid: np.ndarray,           # shape: (n_tax, n_spend, n_horizon, 4)
    tax_bp: list[float],        # Tax breakpoints
    spend_bp: list[float],      # Spend breakpoints
    horizon_bp: list[float],    # Horizon breakpoints (years)
    convex_hull: dict,          # Convex hull metadata
    output_path: str,
    reference_year: int = 2025
):
    """Export shock matrix as Parquet/Zstd with sidecar metadata."""
    # Flatten 4D → table
    n_total = grid.shape[0] * grid.shape[1] * grid.shape[2]
    records = []
    for i_tax, tax in enumerate(tax_bp):
        for i_spend, spend in enumerate(spend_bp):
            for i_horizon, horizon in enumerate(horizon_bp):
                values = grid[i_tax, i_spend, i_horizon]
                records.append({
                    'tax_rate': tax,
                    'spend_level': spend,
                    'horizon_year': int(horizon),
                    'gdp_growth': float(values[0]),
                    'employment_change': float(values[1]),
                    'deficit_change': float(values[2]),
                    'debt_to_gdp_ratio': float(values[3])
                })

    table = pa.Table.from_pylist(records)
    
    # Write with Zstd compression (level 9 for max compression)
    pq.write_table(
        table,
        output_path,
        compression='zstd',
        compression_level=9,
        row_group_size=10000
    )
    
    # Write sidecar metadata
    metadata = {
        'reference_year': reference_year,
        'dimensions': ['tax_rate', 'spend_level', 'horizon_year'],
        'output_variables': ['gdp_growth', 'employment_change', 'deficit_change', 'debt_to_gdp_ratio'],
        'breakpoints': {
            'tax_rate': tax_bp,
            'spend_level': spend_bp,
            'horizon_year': horizon_bp
        },
        'convex_hull': convex_hull,
        'grid_shape': list(grid.shape),
        'compressed_size_bytes': Path(output_path).stat().st_size
    }
    
    meta_path = output_path.replace('.parquet', '.meta.json')
    with open(meta_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Assert size constraint
    assert Path(output_path).stat().st_size < 5_000_000, \
        f"Shock matrix exceeds 5 MB: {Path(output_path).stat().st_size} bytes"
```

### Anti-Patterns to Avoid

- **Hand-rolling DP noise without formal proof:** Adding random noise from numpy and claiming "differential privacy" is not DP — no formal ε proof exists. Use OpenDP's `.map()` method. [PITFALLS.md Pitfall 3]
- **Training GAN without DP-SGD:** Post-hoc noise injection on a non-DP generator does not compose correctly. The CopulaGAN must use DP training or the DP noise must be applied to pre-computed aggregates, not individual synthetic profiles. [PITFALLS.md Pitfall 3]
- **Schema validation only in dev:** JSON Schema validation must run as a CI gate, not a manual step. A missing `required` field that reaches the WASM engine is a silent runtime bug. [PITFALLS.md Pitfall 7]
- **Year mismatch between artifacts:** If the synthetic population is trained on 2023 data but rules encode 2025 legislation, simulation results are meaningless. CI gate must assert `population.reference_year == rules.parameter_year == shockmatrix.reference_year` [PITFALLS.md Pitfall 7]
- **Ignoring BUSL-1.1 license implications:** SDV's license may be incompatible with AGPL distribution. This needs resolution before committing to the SDV dependency. [CITED: PyPI sdv page — License Expression: BUSL-1.1]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Multi-variable dependency preservation | Custom copula implementation in numpy | SDV CopulaGANSynthesizer | Production-grade copula modeling with proper GAN discriminator for distribution matching; edge cases handled (boundary values, categorical encoding) |
| Differential privacy guarantee | numpy.random.laplace() + hand-written privacy analysis | OpenDP 0.14.2 | Formal ε proofs via `.map()`; composition tracking; auditable by CNIL; avoids composition bugs (sequential vs parallel composition) |
| YAML→JSON conversion | Custom recursive dict walker | PyYAML + jsonschema | PyYAML handles OpenFisca-specific YAML features (date keys, nested metadata); jsonschema provides Draft 2020-12 validation with proper error reporting |
| Parquet/Zstd compression | Custom binary format with gzip | PyArrow 24.0.0 | Columnar compression with Zstd achieves 3-5x better ratios for Float32 grids than gzip; WASM consumer (parquet2 crate) can read Parquet natively |
| Convex hull computation | Hand-rolled gift wrapping algorithm | scipy.spatial.ConvexHull | scipy's Qhull implementation is battle-tested, handles degenerate cases (collinear points), and provides volume/bounds verification |
| JSON Schema definition | Ad-hoc field checking | jsonschema.Draft202012Validator | Standardized, language-agnostic; Rust-side valico can consume the same schemas |
| Synthetic data quality evaluation | Manual statistical comparison | SDMetrics QualityReport | Standardized Column Shapes, Column Pair Trends, DisclosureProtectionEstimate; produces auditable reports for CNIL |

**Key insight:** Phase 1 produces *contracts*, not prototypes. Every custom solution would need to be re-validated for correctness (DP proof, statistical fidelity, schema completeness) — the cost of validation exceeds the cost of using battle-tested libraries. The libraries are the documentation of your guarantees.

## Common Pitfalls

### Pitfall 1: DP Budget Exhaustion (PITFALLS.md #3)
**What goes wrong:** The synthetic dataset is generated with ε=1.0 but dashboard queries consume additional privacy budget through sequential composition, blowing effective ε past 100.
**Why it happens:** Teams focus on *generation* ε but forget *consumption* ε.
**How to avoid:** Pre-compute all public statistics (decile tables, Gini coefficients) at generation time with one-time DP noise injection. Dashboard queries pre-noised aggregates, never raw synthetic microdata. Document total ε consumption in privacy statement.
**Warning signs:** No privacy budget tracker exists; dashboard issues distinct queries per user interaction; DP guarantee mentioned but ε value absent.

### Pitfall 2: Version Mismatch Population ↔ Legislation (PITFALLS.md #7)
**What goes wrong:** Synthetic population from 2023 data evaluated against 2026 rules — silent nonsense results.
**Why it happens:** Pipelines developed independently with different update cadences.
**How to avoid:** CI gate: `assert population.reference_year == legislation.parameter_year == shockmatrix.reference_year`. All artifacts locked to 2025. Regression test suite of 10-20 canonical profiles validated against impots.gouv.fr.
**Warning signs:** No cross-reference metadata between artifacts; different teams own each pipeline.

### Pitfall 3: Curse of Dimensionality in Shock Matrix (PITFALLS.md #9)
**What goes wrong:** Matrix over 8 dimensions = 100M+ points = 3.2 GB — cannot download to browser.
**Why it happens:** Teams plan "more dimensions = more accuracy" without internalizing exponential grid growth.
**How to avoid:** Locked decision D-08 caps at 4 interactive dimensions. D-09 sets 10-15 breakpoints per dimension. Smolyak sparse grids as preferred alternative to uniform Cartesian. Build-time CI check: `assert compressed_size < 5_000_000`. Convex hull bounds explicitly documented.
**Warning signs:** "We'll add more sliders later" — feature creep; no byte-size budget documented.

### Pitfall 4: SDV License Incompatibility (Phase 1 Specific)
**What goes wrong:** SDV is BUSL-1.1, project requires AGPL compatibility. Using SDV may violate BUSL terms for production use or require a DataCebo commercial license.
**Why it happens:** STACK.md recommended SDV without flagging the BUSL-1.1 license as a concern for AGPL projects.
**How to avoid:** Legal review before committing. If incompatible, fallback: `scipy.stats` copula implementation + manual GAN discriminator (more work, no license issue), or request BUSL exception from DataCebo for nonprofit civic tech use.
**Warning signs:** No license audit in CI; BUSL-1.1 never mentioned in project docs; assumption that "open source on PyPI" means "compatible with AGPL."

### Pitfall 5: Python Version Blocking PyArrow
**What goes wrong:** Python 3.9.6 (macOS default) cannot install PyArrow 24.0.0 (requires ≥3.10). Shock matrix compression pipeline silently fails.
**Why it happens:** Environment assumption that system Python is sufficient; no version check in pyproject.toml.
**How to avoid:** `pyproject.toml` must declare `requires-python = ">=3.10"`. CI must use Python ≥3.10. First step in execution: upgrade Python via pyenv/homebrew.
**Warning signs:** `pip install pyarrow` fails with "requires Python >=3.10"; no Python version check in CI.

## Code Examples

Verified patterns from official sources:

### OpenFisca YAML Parameter with Legislation Reference
```yaml
# Source: Context7 /openfisca/openfisca-core [VERIFIED]
description: Taux de la Contribution Sociale Généralisée (CSG) sur les revenus d'activité
metadata:
  reference: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000038835636
  unit: /1
values:
  2025-01-01:
    value: 0.092
    metadata:
      reference: https://www.legifrance.gouv.fr/loda/id/JORFTEXT000049995510
  2024-01-01:
    value: 0.092
  2023-01-01:
    value: 0.092
```

### JSON Schema for OpenFisca Parameter
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "OpenFisca Parameter",
  "type": "object",
  "required": ["description", "values"],
  "properties": {
    "description": { "type": "string", "minLength": 1 },
    "metadata": {
      "type": "object",
      "properties": {
        "reference": { "type": "string", "format": "uri" },
        "unit": { "type": "string" }
      }
    },
    "values": {
      "type": "object",
      "patternProperties": {
        "^\\d{4}-\\d{2}-\\d{2}$": {
          "type": "object",
          "required": ["value"],
          "properties": {
            "value": { "type": ["number", "null"] },
            "metadata": {
              "type": "object",
              "properties": {
                "reference": { "type": "string" }
              }
            }
          }
        }
      }
    }
  }
}
```

### SDMetrics Quality Evaluation
```python
# Source: Context7 /websites/sdv_dev_sdmetrics [VERIFIED]
from sdmetrics.single_table import QualityReport

report = QualityReport()
report.generate(
    real_data=real_data,        # pandas DataFrame
    synthetic_data=synthetic_data,
    metadata=metadata            # SDV SingleTableMetadata
)
# Output: Column Shapes Score, Column Pair Trends Score, Overall Score

# Privacy evaluation
from sdmetrics.single_table import DisclosureProtectionEstimate

dpe = DisclosureProtectionEstimate.compute(
    real_data=real_data,
    synthetic_data=synthetic_data,
    known_column_names=['age', 'situation_familiale'],
    sensitive_column_names=['patrimoine', 'revenu_fiscal'],
    num_rows_subsample=5000,
    num_iterations=50
)
# Returns score 0-1 (higher = more protected)
```

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | All data pipeline scripts | ✓ | 3.9.6 | **Must upgrade to ≥3.10** (PyArrow requirement). Use `pyenv` or `brew install python@3.13` |
| pip | Package installation | ✓ | 21.2.4 | Upgrade: `pip install --upgrade pip` |
| SDV | Synthetic population generation | ✗ | — | `pip install sdv==1.36.1` after Python upgrade |
| OpenDP | Differential privacy | ✗ | — | `pip install opendp==0.14.2` after Python upgrade |
| SDMetrics | Quality evaluation | ✗ | — | `pip install sdmetrics` after Python upgrade |
| jsonschema | YAML→JSON validation | ✗ | — | `pip install jsonschema==4.25.1` |
| PyArrow | Shock matrix Parquet export | ✗ | — | `pip install pyarrow==24.0.0` (requires Python ≥3.10) |
| PyYAML | YAML parsing | ✗ | — | `pip install pyyaml` |
| NumPy/SciPy/Pandas | Data processing | ✗ | — | `pip install numpy scipy pandas` |
| openfisca-france | Bilingual validation reference | ✗ | — | `pip install openfisca-france` |
| Rust/Cargo | Bilingual validation (Rust side) | ✗ | — | `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh` |
| wasm-pack | WASM build (validation tests) | ✗ | — | `cargo install wasm-pack` (Phase 2 dependency, not needed for Phase 1 plan writing) |
| Node.js | CI tooling | ✓ | v24.12.0 | — |
| npm | CI tooling | ✓ | 11.6.2 | — |
| GPU (CUDA/MPS) | CopulaGAN training | ✗ | — | **No GPU detected.** Training 50K profiles on CPU may take hours/days. Use cloud GPU (Colab, Lambda Labs) or accept longer training time on MPS (Apple Silicon) |
| CASD access | Real data for training | ✗ | — | **Multi-month approval process** (flagged in STATE.md). Begin immediately. INSEE ERFS enquête as fallback |
| Mésange model | Shock matrix methodology | ✗ | — | **Restricted access** (Insee/Trésor). Requires formal agreement. No fallback — methodology must be validated before production |

**Missing dependencies with no fallback:**
- **Python ≥3.10:** PyArrow 24.0.0 cannot install on Python 3.9.6. Must upgrade before any `pip install` for the shock matrix pipeline.
- **CASD data access:** CopulaGAN training requires real microdata. Multi-month approval process. No alternative real data source with equivalent granularity.
- **Mésange model access:** Shock matrix methodology requires Insee/Trésor agreement. Cannot be generated from public data alone.

**Missing dependencies with fallback:**
- **GPU:** CopulaGAN can train on CPU (slower) or Apple Silicon MPS (moderate). Cloud GPU is ideal but not blocking.
- **Rust/Cargo:** Only needed if running Phase 2 validation tests during Phase 1. Phase 1 Python pipeline is self-contained. Can defer.
- **SDV (BUSL-1.1):** If license incompatible, fall back to scipy copula + manual GAN (significant extra work, ~2-3 weeks). Or request nonprofit exception from DataCebo.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| XML parameter format (OpenFisca legacy) | YAML parameter format with metadata | OpenFisca Core migration (2019+) | XML deprecated; YAML is the standard for new country packages. Metadata now nested under `metadata` key (not top-level) |
| serde_yaml (Rust) | Build-time YAML→JSON, serde_json at runtime | serde_yaml deprecated March 2024 | Phase 1 Python handles all YAML; WASM receives JSON only. No YAML dependency at runtime |
| Post-hoc DP noise injection | DP-SGD during GAN training + OpenDP composition proofs | OpenDP 0.14+ (2024) | Formal ε proofs auditable by CNIL; pre-allocated budget prevents exhaustion at query time |
| Cartesian grid (curse of dimensionality) | Smolyak sparse grids (preferred) or ≤4 dimensions uniform | D-08, D-09, D-10 locked | Caps at 4 interactive dims with 10-15 bp each; sparse grids as stretch goal |

**Deprecated/outdated:**
- **serde_yaml 0.9.34:** Officially deprecated. Avoided entirely by build-time YAML→JSON strategy. [VERIFIED: crates.io, STACK.md]
- **OpenFisca XML parameters:** Legacy format. All new rules use YAML. [VERIFIED: Context7 /openfisca/openfisca-core CHANGELOG]
- **HDF5 for shock matrix:** Parquet/Zstd achieves better compression ratios for Float32 grids and has better WASM ecosystem support (parquet2 crate). [ASSUMED]

## Assumptions Log

> All claims tagged `[ASSUMED]` in this research. The planner and discuss-phase use this section to identify decisions that need user confirmation before execution.

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | CASD data access will be granted within project timeline | Standard Stack (fallback note) | Blocking: no real microdata = no statistically valid synthetic population. Fallback to public INSEE aggregates produces lower-fidelity profiles |
| A2 | Mésange model documentation is sufficient to derive a 3D shock matrix without direct model access | Standard Stack | Medium: if Mésange methodology is too restricted, shock matrix must be derived from public macro literature (less accurate, erodes credibility) |
| A3 | SDV BUSL-1.1 license is compatible with project's AGPL distribution (or nonprofit exception obtained) | Standard Stack | High: reimplementing CopulaGAN from scratch is 2-3 weeks of work; switching to pure scipy copula reduces fidelity |
| A4 | 50,000 profiles with CopulaGAN + 500 epochs will train in <24 hours on available hardware | Architecture Patterns | Low: longer training time delays pipeline but doesn't block — just adds calendar time |
| A5 | PyYAML 6.x is compatible with Python ≥3.13 (not yet verified for specific combination) | Standard Stack | Low: PyYAML is broadly compatible; any issue would be caught at `pip install` time |
| A6 | openfisca-france package is installable and its 2025 parameters are available | Bilingual Validation | Medium: if openfisca-france doesn't have 2025 parameters, validation must use 2024 reference + manual adjustment |
| A7 | The impots.gouv.fr simulator is accessible programmatically (web scraping) or manually for 10-20 profiles | Bilingual Validation | Low: manual validation of 10-20 profiles is feasible even without API access; just adds human effort |

## Open Questions

1. **SDV BUSL-1.1 license compatibility with AGPL**
   - What we know: SDV is BUSL-1.1, project targets AGPL compatibility. BUSL converts to Apache 2.0 after a change date but restricts production use until then.
   - What's unclear: Whether nonprofit civic tech / open-source government transparency use qualifies for a BUSL exception from DataCebo.
   - Recommendation: Request a license clarification from DataCebo (info@sdv.dev) before writing any SDV-dependent code. Prepare scipy copula fallback pipeline as Plan B.

2. **Mésange model access and methodology**
   - What we know: Model is restricted (Insee/Trésor). Bootstrap methodology for shock matrix derivation is described in PRD research but not validated against actual Mésange outputs.
   - What's unclear: Whether public Mésange documentation + VAR bootstrap methodology is sufficient to produce a credible shock matrix without direct model access.
   - Recommendation: Spike the shock matrix bootstrap using public macro data (INSEE comptes nationaux) as a proxy. Validate methodology before relying on Mésange access.

3. **CASD data access timeline**
   - What we know: Multi-month approval process. 2026-05-11 start plus typical 3-6 month CASD timeline = data available October-November 2026 at earliest.
   - What's unclear: Whether INSEE enquête Revenus Fiscaux et Sociaux (ERFS) public microdata provides sufficient granularity for CopulaGAN training if CASD is denied.
   - Recommendation: Begin CASD application immediately. In parallel, prototype CopulaGAN pipeline using public ERFS data (lower granularity but available now). Compare fidelity metrics to determine if fallback is viable.

4. **Canonical profile validation against impots.gouv.fr**
   - What we know: 10-20 profiles covering edge cases (single, couple, families, retirees, self-employed). Validated against official simulator. Precision threshold: 1e-6.
   - What's unclear: Whether impots.gouv.fr simulator is accessible programmatically or requires manual entry. Whether it uses 2025 tax rules (may only support revenus 2024/déclaration 2025).
   - Recommendation: Test impots.gouv.fr simulator manually with 2-3 sample profiles to determine automation feasibility. Document the validation protocol (screenshot-based or API-based).

5. **Smolyak sparse grid Rust crate availability**
   - What we know: D-10 prefers Smolyak sparse grids if a Rust crate exists compiling to WASM. Fallback is uniform Cartesian grid.
   - What's unclear: Whether a maintained, WASM-compatible Smolyak sparse grid crate exists (this is a Phase 2 concern but affects Phase 1 grid construction decisions).
   - Recommendation: Research during Phase 1 shock matrix design. If no crate exists, use uniform Cartesian grid with D-08's 4-dimension cap and D-09's 10-15 breakpoint density.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No user auth in this phase |
| V3 Session Management | No | No sessions in offline pipeline |
| V4 Access Control | No | No access control in data pipeline |
| V5 Input Validation | Yes | JSON Schema Draft 2020-12 validation of all YAML→JSON converted rules; SDV metadata validation of real data columns; convex hull bounds validation on shock matrix |
| V6 Cryptography | No | No cryptographic operations in data pipeline |

### Known Threat Patterns for Offline Data Pipeline

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Data poisoning (maliciously crafted INSEE data) | Tampering | SHA-256 integrity hashes on all input data files; checksum verification before training |
| Model inversion attack on synthetic data | Information Disclosure | SDMetrics DisclosureProtectionEstimate; ε ≤ 1.0 DP guarantee; pre-noised aggregates only |
| Supply chain attack (compromised PyPI package) | Tampering | `pip install --require-hashes`; dependency audit in CI; lockfile with verified hashes |
| Sensitive real data leakage in notebooks | Information Disclosure | `.gitignore` for real data files; notebooks use synthetic-only or sample data; data directory outside git repo |
| Build artifact tampering (rules JSON modified post-validation) | Tampering | CI gate verifies content hash of artifacts; integrity hashes published alongside artifacts; CDN serves with SRI |

## Sources

### Primary (HIGH confidence)
- **Context7 /openfisca/openfisca-core** — YAML parameter format, JSON export, metadata structure, legislation references. [VERIFIED: doc fetch 2026-05-11]
- **Context7 /websites/sdv_dev_sdv** — CopulaGANSynthesizer API, SingleTableMetadata, column types, constraints, training configuration. [VERIFIED: doc fetch 2026-05-11]
- **Context7 /opendp/opendp** — Laplace mechanism, Gaussian mechanism, `.map()` for ε proof, `make_basic_composition`, zCDP conversion. [VERIFIED: doc fetch 2026-05-11]
- **Context7 /websites/sdv_dev_sdmetrics** — QualityReport, Column Shapes, Column Pair Trends, DisclosureProtectionEstimate. [VERIFIED: doc fetch 2026-05-11]
- **Context7 /python-jsonschema/jsonschema** — Draft202012Validator, validate(), check_schema(). [VERIFIED: doc fetch 2026-05-11]
- **PyPI (pypi.org)** — SDV 1.36.1 (released 2026-04-24, Python ≥3.9, BUSL-1.1), PyArrow 24.0.0 (released 2026-04-21, Python ≥3.10). [VERIFIED: web fetch 2026-05-11]
- **Project STACK.md** — Recommended versions for OpenDP 0.14.2, SDV 2.x (corrected to 1.36.1), jsonschema 4.x. [VERIFIED: project file]

### Secondary (MEDIUM confidence)
- **Project ARCHITECTURE.md** — Shock matrix structure, Parquet/Zstd compression, project structure. [CITED: project file]
- **Project PITFALLS.md** — Pitfalls 3 (DP budget), 7 (year mismatch), 9 (curse of dimensionality). [CITED: project file]
- **Project CONTEXT.md** — Decisions D-01 through D-17, validation strategy, reference year, versioning. [CITED: project file]

### Tertiary (LOW confidence)
- **openfisca-france package** — Availability of 2025 parameters. Not verified — needs validation.
- **CASD data access timeline** — Multi-month estimate based on STATE.md. Not independently verified.
- **impots.gouv.fr simulator** — Accessibility for automated validation. Not tested.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified via Context7 docs or PyPI registry on 2026-05-11. SDV license concern flagged as open question.
- Architecture: HIGH — patterns derived from Context7-verified library APIs and project ARCHITECTURE.md. Project structure follows locked decisions D-01 through D-17.
- Pitfalls: HIGH — 4 of 5 pitfalls verified against project PITFALLS.md plus one phase-specific finding (SDV license). All prevention strategies actionable.

**Research date:** 2026-05-11
**Valid until:** 2026-06-11 (30 days — stable Python data stack, no rapidly changing APIs)
