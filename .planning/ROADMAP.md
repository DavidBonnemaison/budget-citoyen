# Roadmap: Budget Citoyen

## Overview

Budget Citoyen is built in 5 phases over 2 milestones, following a strict build-order dictated by dependency chains: data artifacts → computation engines → interactive UI → enhanced analysis → platform hardening. Phases 1-2 produce the invisible foundation (tax rules, synthetic population, shock matrix, WASM engines). Phase 3 delivers the first user-facing MVP (Citizen Explorer shell) as Milestone 1. Phase 4 adds distributional analysis and expert mode as Milestone 2. Phase 5 opens the platform to researchers and hardens for production launch.

Every phase incorporates its pitfall prevention at the earliest design stage — retrofitting accessibility, privacy budget architecture, or WASM boundary optimization after the fact would cost 2-3 weeks each.

## Milestones

- 🚧 **Milestone 1 — MVP Citoyen** — Phases 1-3 (first user-facing deliverable: interactive simulation with household impact, basic macro, shareable URLs, RGAA 4 core)
- 📋 **Milestone 2 — Plateforme Complète** — Phases 4-5 (distributional analysis, expert mode, REST API, security/privacy audit, human RGAA audit)

## Phases

- [ ] **Phase 1: Data Foundation & Rules Engine** — OpenFisca-compatible YAML tax rules, synthetic population pipeline (50K profiles, DP ε ≤ 1.0), Mésange shock matrix pre-computation
- [x] **Phase 2: Core Simulation Engines (WASM)** — Rust/WASM microsim engine + macro interpolation engine, batch interfaces, bilingual validation against OpenFisca Python reference
- [ ] **Phase 3: Interactive Simulation Shell (MVP)** — Citizen Explorer UI with sliders, real-time feedback (<200ms), household impact, macro charts, shareable URLs, RGAA 4 core, responsive layout
- [ ] **Phase 4: Enhanced Data & Expert Mode** — Full 50K profile distributional analysis, expert mode with multi-reform stacking, calculation tree transparency, data exports
- [ ] **Phase 5: Platform Expansion & Hardening** — REST API, security/privacy audit, human RGAA 4 audit, performance hardening

## Phase Details

### Phase 1: Data Foundation & Rules Engine
**Goal**: All reference data artifacts (tax rules, synthetic population, shock matrix) exist in auditable, version-locked form, ready for consumption by the WASM computation engines — no computation can proceed without these contracts.
**Depends on**: Nothing (first phase)
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04
**Success Criteria** (what must be TRUE):
  1. Tax rules for IR, IS, TVA, cotisations sociales, and aides sociales are encoded as auditable YAML files with referenced legislation sources and convertible to JSON for the WASM runtime
  2. A synthetic population of 50,000 profiles is generated with statistically valid multi-variable correlations (âge ↔ patrimoine ↔ revenus), and a formal differential privacy guarantee of ε ≤ 1.0 is proven (not estimated) via the OpenDP framework
  3. The Mésange-derived shock matrix is pre-computed as a compressed 3D look-up table (tax × spend × horizon) under 5 MB with convex hull boundaries documented — out-of-bounds regions are explicitly identified
     4. A bilingual Python→Rust validation framework confirms that 10-20 canonical household profiles produce identical results against the official impots.gouv.fr simulator; all data artifacts are version-locked to the same reference year with CI gate enforcement
**Plans**: 5 plans

- [x] 01-01-PLAN.md — YAML tax rules (IR, IS, TVA, cotisations, aides sociales), project foundation (pyproject.toml), JSON Schema definitions, YAML→JSON conversion + validation pipeline (DATA-01)
- [x] 01-02-PLAN.md — Synthetic population pipeline: CopulaGAN training, OpenDP differential privacy (ε ≤ 1.0), SDMetrics quality evaluation, JSON export with integrity hashes (DATA-02, DATA-03)
- [x] 01-03-PLAN.md — Shock matrix pre-computation: VAR bootstrap, 3D grid construction (max 4 dims, 10-15 breakpoints), convex hull bounds, Parquet/Zstd export under 5 MB (DATA-04)
- [x] 01-04-PLAN.md — Bilingual validation framework (10-20 canonical profiles, openfisca-france reference, JSON test fixtures), CI pipeline with version consistency gate and artifact integrity checks
- [x] 01-GAP-CLOSURE-PLAN.md — UAT gap closure: YAML parameter completeness (12→31 files across IR/IS/TVA/cotisations/aides, credits 3→25 entries), canonical profiles depth (16→32 with systematic 7-dimension coverage)

### Phase 2: Core Simulation Engines (WASM)
**Goal**: Both the microeconomic engine (IR, IS, TVA, cotisations, aides sociales) and macroeconomic engine (multi-linear interpolation over shock matrix) execute correctly in the browser via WebAssembly Web Workers, with batch interfaces avoiding serialization overhead, and pass bilingual validation against the OpenFisca Python reference — this is the computational heart of the platform.
**Depends on**: Phase 1
**Requirements**: MICRO-01, MICRO-02, MICRO-03, MICRO-04, MICRO-05, MACRO-01, MACRO-02, MACRO-03, MACRO-04, MACRO-05
**Success Criteria** (what must be TRUE):
  1. The micro engine computes IR, IS, TVA, cotisations sociales, and aides sociales for any profile type, with results matching the OpenFisca Python reference to within 1e-6 precision across the bilingual test suite
  2. The macro engine performs multi-linear interpolation over the pre-computed shock matrix to project deficit, debt, GDP growth, and employment trajectories; interpolation returns `Option::None` for inputs outside the convex hull (with a documented warning contract for the UI layer)
  3. Both engines run entirely client-side in separate Web Workers — no computation data, profile information, or intermediate results leave the browser; zero server round-trips are required for any simulation result
  4. A single-profile micro calculation completes in under 200ms (WASM execution + JS↔WASM serialization combined); a full macro interpolation completes in under 50ms
  5. Native Rust tests (`cargo test` with proptest property-based strategies) and WASM boundary tests (`wasm-pack test`) both pass in CI, confirming the `core`/`wasm` crate split prevents untestable logic
**Plans**: 8 plans

Plans:
- [x] 02-01-PLAN.md — Environment setup, Rust toolchain install, Cargo workspace scaffolding, Phase 1 artifact generation, Parquet/WASM spike
- [x] 02-02-PLAN.md — TDD: Profile validation & core types (Profile, LoadError, MicroResult, MacroResult)
- [x] 02-03-PLAN.md — TDD: Parameter tree loading with date-based resolution & version checking
- [x] 02-04-PLAN.md — Code generator script (Python→Rust), full variable tree compilation, CI staleness check
- [x] 02-05-PLAN.md — TDD: Macro interpolation engine (ShockMatrix, interpn, convex hull, trajectory projection)
- [x] 02-06-PLAN.md — TDD: Bilingual tax validation & TaxBenefitSystem (32 canonical profiles, ≤1e-6 precision)
- [x] 02-07-PLAN.md — WASM boundary layers (MicroEngine + MacroEngine), boundary tests, core test verification
- [x] 02-08-PLAN.md — Web Workers (micro/macro workers, orchestrator, index-map), CI pipeline, release profile

### Phase 3: Interactive Simulation Shell (MVP)
**Goal**: A citizen can visit the platform on any device, manipulate fiscal sliders, and see in real time (<200ms) the impact on a typical household's purchasing power and the national deficit/debt trajectory — all in accessible, vulgarized French, shareable via URL, and compliant with RGAA 4 core criteria. This is the first user-facing deliverable (Milestone 1).
**Depends on**: Phase 2
**Requirements**: UI-01, UI-02, UI-03, UI-04, UI-05, UI-06, UI-07, UI-08, A11Y-01, A11Y-02, A11Y-03, A11Y-04, A11Y-05, A11Y-06
**Success Criteria** (what must be TRUE):
  1. A citizen can manipulate fiscal sliders (IR, IS, TVA, cotisations) on a responsive, mobile-friendly interface and see real-time updates under 200ms, with visible loading indicators during asynchronous computation
  2. The simplified household purchasing-power impact updates in real time as sliders move (vulgarized French presentation), and the citizen can reset all fiscal parameters to their initial values with a single action
  3. Deficit, debt, and GDP trajectory charts (5-year projection) render as RGAA 4-compliant SVGs with `role="img"`, `aria-labelledby`, pattern-fill differentiation (never color alone), and sibling HTML tables with `<th scope>` markup for screen readers
  4. The citizen can share their exact simulation state via a URL that captures the complete parameter state (slider positions, selected views); all sliders are keyboard-navigable with full WAI-ARIA attributes (`aria-valuenow`, `aria-valuemin`, `aria-valuemax`) and debounced ARIA announcements on drag-end only
  5. The platform loads in under 3 seconds (cold) and under 1 second (warm via Service Worker + Cache API); animations over 5 seconds have interruption mechanisms; automated accessibility tests (axe-core) pass in CI; and a methodology page attributes data sources (Insee, budget.gouv.fr, Mésange) with documented methodology
**Plans**: TBD
**UI hint**: yes

### Phase 4: Enhanced Data & Expert Mode
**Goal**: Expert users (analysts, journalists, campaign teams) can stack multiple reforms, access advanced parameters, and explore full distributional impact across the 50,000-profile synthetic population — with complete transparency into the legislative logic applied to each calculation. This phase delivers the competitive differentiators as Milestone 2.
**Depends on**: Phase 3
**Requirements**: EXP-01, EXP-02, EXP-04
**Success Criteria** (what must be TRUE):
  1. An expert user can stack multiple fiscal reforms in a single scenario and observe their combined 5-year macroeconomic trajectories with confidence bounds
  2. Advanced parameters (effectifs de l'État, taux de remplacement, etc.) are exposed in the expert interface with progressive disclosure from citizen mode, including vulgarized tooltips explaining each parameter
  3. The user can inspect the full "show my calculation" interactive tree to audit exactly which legislative rules, parameter values, and formula paths were applied to produce a simulation result
  4. Distributional impact charts (by income decile, age group) show who gains and who loses from a reform, powered by the full 50,000 synthetic profiles with DP guarantees preserved (pre-noised public aggregates only, no per-query DP budget consumption)
**Plans**: TBD

### Phase 5: Platform Expansion & Hardening
**Goal**: Researchers can access simulation results programmatically via a REST API; the platform passes both a formal security/privacy audit and a certified human RGAA 4 accessibility audit; and performance hardening ensures election-night traffic resilience. This phase gates public launch.
**Depends on**: Phase 4
**Requirements**: EXP-03
**Success Criteria** (what must be TRUE):
  1. A stateless REST API (edge functions) exposes simulation calculations, distributional impact by decile, and structured exports (CSV, JSON) with rate limiting and PII-free validation middleware — no request body ever contains identifiable data
  2. The platform passes a human RGAA 4 audit by a certified auditor — all 106 criteria reviewed, including assistive technology user testing with NVDA+Firefox, JAWS+Chrome, and VoiceOver+Safari
  3. A security and privacy audit confirms: no browser fingerprinting vectors via WASM memory timing, no `localStorage` usage (only `sessionStorage`), CSP headers blocking all third-party scripts, and CNIL compliance for the "zero data transfer" architecture claim
  4. WASM payloads are served with `Content-Encoding: gzip`, the shock matrix uses Parquet/Zstd compression, and Service Worker precaching ensures <1s warm load under election-night traffic conditions
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Data Foundation & Rules Engine | 5/5 | Complete | 2026-05-12 |
| 2. Core Simulation Engines (WASM) | 8/8 | Complete | 2026-05-12 |
| 3. Interactive Simulation Shell (MVP) | 0/TBD | Not started | - |
| 4. Enhanced Data & Expert Mode | 0/TBD | Not started | - |
| 5. Platform Expansion & Hardening | 0/TBD | Not started | - |
