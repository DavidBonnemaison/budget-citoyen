# Project Research Summary

**Project:** Budget Citoyen — Simulateur Budgétaire Citoyen Interactif
**Domain:** Civic budget simulation platform (hybrid microsimulation + macroeconomic projection)
**Researched:** 2026-05-11
**Confidence:** HIGH

## Executive Summary

Budget Citoyen is an interactive civic budget simulation platform that lets French citizens explore the impacts of fiscal policy changes — both on their household and on the national economy — entirely within their browser. Unlike existing platforms (SimuBudget is macro-only, LexImpact is micro-only, PolicyEngine has no French equivalent), this product uniquely combines **microeconomic household simulation** (50,000 synthetic profiles) with **macroeconomic trajectory projection** (Mésange-derived shock matrix) in a single slider-driven interaction, all while maintaining zero server-side personal data processing.

The recommended approach is a **Privacy-Preserving Edge-Compute Architecture**: a React 19 frontend driving two Rust/WASM Web Workers (micro engine + macro engine) that perform all computation client-side. Tax rules are authored as auditable YAML and compiled to JSON for the WASM runtime. A Python offline pipeline generates the synthetic population and pre-computes the macro shock matrix as static CDN assets. Accessibility (RGAA 4 — a legal requirement for French public services) must be built into every component from Phase 1, not retrofitted.

The two highest-risk architectural elements are **(1) the dual WASM engine core**, where serialization overhead across the JS↔WASM boundary must be aggressively minimized through batch interfaces and shared linear memory, and **(2) the synthetic data pipeline**, where differential privacy budget exhaustion through repeated queries can render ε guarantees meaningless unless all public statistics are pre-computed with one-time DP noise injection. The architectural research is thorough with HIGH confidence across stack, features, and architecture; the main gaps involve the restricted availability of Mésange model source documentation and the need for a certified human RGAA 4 auditor before launch.

## Key Findings

### Recommended Stack

The stack is organized in three tiers: **frontend** (React 19.2, TypeScript 5.8+, Vite 6+, Tailwind CSS 4.3, React Aria, D3.js 7.9, Vega-Lite 6.4), **compute** (Rust → WASM via wasm-bindgen 0.2.121, wasm-pack 0.14.0, ndarray 0.17, interpolation 0.3, wasm-bindgen-rayon 1.3 for parallelism), and **offline data pipeline** (Python: SDV 2.x for copula-based synthetic generation, OpenDP 0.14.2 for differential privacy guarantees, SDMetrics for quality validation). Testing uses Vitest 3.x + Playwright 1.x + wasm-bindgen-test.

**Core technologies with rationale:**
- **React 19.2 + React Aria**: `useTransition` enables non-blocking slider updates for the <200ms latency target; React Aria's `useSlider` provides full WAI-ARIA implementation mandatory for RGAA 4 Thématique 11
- **Rust/WASM (wasm-bindgen + ndarray + interpolation)**: Client-side computation avoids server round-trips (privacy-by-design constraint); ndarray stores pre-computed shock matrices as N-dimensional tensors; interpolation crate performs microsecond-range multi-linear interpolation
- **D3.js 7.9 (primary) + Vega-Lite 6.4 (secondary)**: SVG-first rendering with full DOM control for RGAA 4 compliance (`role="img"`, `aria-labelledby`, pattern fills); Canvas-based alternatives (Chart.js, ECharts) are explicitly rejected as inaccessible
- **Python SDV + OpenDP (offline)**: CopulaGANSynthesizer models multi-variable fiscal correlations; OpenDP provides Laplace/Gaussian mechanisms with formal ε-differential privacy proofs required by CNIL
- **YAML → JSON rules pipeline**: YAML for human authoring (OpenFisca ecosystem standard); JSON for WASM runtime (smaller binary footprint, avoids deprecated `serde_yaml` crate)

**Critical version requirements:** wasm-bindgen 0.2.121 + wasm-pack 0.14.0 + serde-wasm-bindgen 0.6.5 must be version-aligned together. React 19 requires `@vitejs/plugin-react` v6+. Crate split (`core` library + `wasm` binding crate) is mandatory for testability.

### Expected Features

**Must have for launch (Milestone 1 — Table Stakes):**
- **Tax slider controls** for major fiscal levers (IR, IS, TVA, cotisations) — core interaction mechanism; no product without this
- **Microsimulation engine (WASM)** — computational heart; all calculations depend on it
- **Simplified household impact calculator** (Citizen Explorer mode with vulgarisé presentation) — the "why should I care" hook
- **Basic macro outputs** (deficit, debt, basic 5-year trajectory) — the national picture grounding the simulation
- **Real-time feedback (< 200ms latency)** — performance is a feature; without it the experience collapses
- **Shareable results via URL encoding** — virality vector for electoral period traffic
- **Responsive layout** (mobile + desktop) — 60%+ of French civic engagement traffic is mobile
- **RGAA 4 Core Compliance** — legal requirement; sliders, charts with data table fallbacks, color independence, keyboard navigation
- **Data attribution & methodology page** — trust foundation citing Insee, budget.gouv.fr, Mésange model

**Should have after core validation (Milestone 2 — Differentiators):**
- **Synthetic population data pipeline** (50,000 profiles with DP guarantees) — enables distributional analysis; the key competitive differentiator
- **Shock matrix + macro interpolation engine** — enables full 5-year macro trajectories
- **Expert mode** (multi-reform program testing) — progressive disclosure from citizen to expert
- **Distributional impact charts** (by income decile) — "who wins, who loses"
- **Rules as Code transparency view** — "show my calculation" tree for legislative auditability
- **Data exports** (CSV, JSON) — first researcher-facing feature

**Defer to v2+ (Future Consideration):**
- Researcher REST API with counterfactual analysis endpoint
- AI-generated policy impact narrative (LLM-powered plain-language explanation)
- Electoral program comparison tool (side-by-side party program loading)
- Circonscription-level data dashboard (GeoPackage/Shapefile)

### Architecture Approach

The platform follows a **Privacy-Preserving Edge-Compute Architecture** with three execution tiers and zero server-side personal data:

1. **UI Layer (Browser main thread)** — React 19 + TypeScript SPA with persona-specific view composition (Citoyen/Expert/Chercheur). Simulation Orchestrator (Zustand stores) manages slider state, dispatches to workers, fans-in results, and updates D3.js charts. All user input stays in the browser.

2. **Compute Layer (Web Workers)** — Two independent WASM workers: **Micro Engine Worker** (Rust TaxBenefitSystem port, 50K profile simulation via Rayon parallelism, Reform.apply logic) and **Macro Engine Worker** (Rust ndarray-based shock matrix loader, multi-linear interpolation, trajectory projection with result caching). Workers communicate via `postMessage` with transferable ArrayBuffers for zero-copy data transfer.

3. **Static Data Layer (CDN/Edge)** — Pre-computed, immutable assets: shock matrix bundles (JSON/Parquet, 1-5 MB), synthetic population snapshots (50K profiles, ε≤1.0, 5-20 MB compressed), tax rules bundles (OpenFisca-compatible YAML→JSON, versioned by legislation year). No user data ever reaches this layer.

**Four key architectural patterns:**
- **Double Worker Isolation** — micro and macro engines in separate Web Workers; main thread never blocks; essential for <200ms slider SLA
- **Multi-Linear Interpolation over Pre-Computed Shock Matrix** — 3D look-up table (tax × spend × horizon) replaces real-time Mésange solving; interpolation error <1bp at policy-relevant grid densities; storage cost ~400 KB per output variable uncompressed
- **Persona-Specific View Composition** — same engine outputs, three different UI presentations: simplified vignettes for citizens, full dashboard for experts, API/export for researchers
- **Privacy by Design Data Flow** — zero-knowledge architecture: no `fetch` or `XMLHttpRequest` carries identifiable data; aggregate results pre-computed from synthetic data; `sessionStorage` only (no `localStorage`); explicit CSP headers blocking all third-party scripts

**Project structure is monorepo with 6 packages:** `wasm-microengine` (Rust crate), `wasm-macroengine` (Rust crate), `data-pipeline` (offline Python), `webapp` (React SPA), `expert-api` (optional REST edge functions), `tax-rules` (OpenFisca-compatible YAML). Crates are split into `core`/`wasm` layers for native testability.

### Critical Pitfalls

The 10 identified pitfalls, ranked by severity and grouped by phase relevance:

1. **WASM Serialization Tax Dominates Compute Budget** — Crossing the JS↔WASM boundary per-parameter costs 5-15ms per call; with 12+ sliders at 60fps, this alone breaks the 200ms budget. **Prevention:** Design WASM boundary as a batch interface; update a pre-allocated `SimulationState` in WASM linear memory via index-based setters; profile boundary-crossing cost separately from computation cost. **Phase 2 (Micro Engine).**

2. **Extrapolation Beyond Pre-Computed Grid Produces Silent Wrong Answers** — Multi-linear interpolation outside the convex hull yields fantasy results (e.g., negative unemployment). **Prevention:** Clamp or clamp-and-warn at grid bounds; compute convex hull at build time; return `Option<None>` for out-of-bounds inputs with UI warning "résultats indicatifs uniquement." **Phase 3 (Macro Engine).**

3. **Differential Privacy Budget Exhaustion Invalidates ε Guarantee** — Sequential composition means t queries at ε each = t×ε total; by the time users explore 10 scenarios across 8 demographic slices, effective ε > 100. **Prevention:** Pre-compute ALL public statistics with one-time DP noise during data pipeline; use zCDP for tighter composition bounds; implement privacy budget tracker; document total ε consumption in published privacy statement. **Phase 4 (Synthetic Data).**

4. **Canvas-Only Charts Are Invisible to Screen Readers** — Fails RGAA 4 criteria 1.1, 1.3. **Prevention:** SVG-first rendering with proper ARIA roles; every chart gets a sibling HTML `<table>` with `<th scope>` markup; color differentiation supplemented by patterns/textures + text labels; text summary for every chart. **Phase 3 (Charts).**

5. **Version Mismatch Between Legislation Parameters and Synthetic Population** — 2023-based population evaluated against 2026 rules with no reweighting = silently wrong results. **Prevention:** Version-lock the simulated year; metadata coupling (`reference_year` field) with CI gate asserting population.year == legislation.year; regression suite of 10-20 canonical profiles validated against the official impots.gouv.fr simulator. **Phase 1 (Data Foundation) + Phase 4 (Synthetic Data).**

6. **Dynamic Slider → Screen Reader Chaos** — 60fps ARIA updates flood assistive tech with undecipherable chatter. **Prevention:** Dual update strategy — visual chart at 60fps for sighted users, ARIA announcements debounced to 500ms (only on `change` event, not `input`); step-based keyboard controls; text input fallback next to each slider. **Phase 3 (UI Components).**

7. **Browser Fingerprinting via WASM Memory Patterns** — Computation time variations, deterministic profile evaluation order, and `localStorage` persistence create identifiable computational fingerprints across sessions. **Prevention:** Constant-time simulation (or randomized batch order); `sessionStorage` only; randomize profile sampling order; no analytics scripts; CSP headers blocking third-party scripts. **Phase 5 (Security/Privacy Audit).**

8. **Untestable WASM Logic Through JS Bridge Only** — All tests exercise the engine through wasm-bindgen, making Rust bugs indistinguishable from serialization bugs. **Prevention:** Split crate into `core` (pure Rust, native `#[test]`, property-based tests via proptest) and `wasm` (binding glue, boundary-only tests via wasm-bindgen-test). **Phase 2 (Micro Engine).**

9. **Curse of Dimensionality in Look-Up Table** — 8 fiscal parameters × 10 grid points each = 10^8 points (3.2 GB) impossible to download or interpolate. **Prevention:** Limit interactive dimensions to ≤4; use sparse grid techniques (Smolyak); progressive loading with low-resolution matrix first; CI gate failing build if matrix exceeds 5 MB compressed. **Phase 3 (Macro Engine).**

10. **Automated-Tool-Passing Treated as Accessibility Compliance** — axe-core passing at 100% ≠ RGAA compliance; automated tools catch ~30% of issues. **Prevention:** Contract a certified RGAA auditor for design review and pre-launch audit; conduct screen reader UAT with actual AT users (NVDA + Firefox, JAWS + Chrome, VoiceOver + Safari); tab-through entire interface with keyboard only; accessibility is an acceptance criterion on every user story, not a final phase. **All UI phases.**

## Implications for Roadmap

Based on combined research (architecture build order, feature dependencies, pitfall prevention windows, and MVP definition), the recommended phase structure is **5 phases over 2 milestones plus future work**:

### Phase 1: Data Foundation & Rules Engine
**Rationale:** Pure data artifacts with zero UI dependency. Must exist before WASM engines can be built, tested, and validated. Tax rules YAML (OpenFisca compatibility layer), synthetic population generation pipeline (offline Python), and Mésange shock matrix pre-computation scripts form the foundation all computation depends on. This phase is also the window to establish the shared contract for year alignment between population and legislation — retrofitting this later costs 2-3 weeks.

**Delivers:**
- OpenFisca-compatible YAML tax rules by domain (IR, IS, TVA, cotisations, aides) with versioned legislation snapshots
- YAML → JSON build pipeline (avoids deprecated `serde_yaml` at runtime)
- Synthetic population pipeline: CopulaGAN generation, OpenDP differential privacy ε-budget architecture (DP-SGD, not post-hoc noise), SDMetrics quality validation, profile consistency checks (no contradictory variable combinations)
- Mésange-derived shock matrix pre-computation: 3D grid (tax × spend × horizon) with dimensionality budget ≤4, CI gate enforcing <5 MB compressed
- Bilingual Python→Rust validation framework: canonical profiles (10-20 households) tested against official impots.gouv.fr simulator

**Addresses features:** Data attribution & methodology page (foundation data), Rules as Code auditable parameters  
**Prevents pitfalls:** Pitfall 3 (DP budget architecture designed before generation), Pitfall 7 (year version-locking contract established), Pitfall 9 (dimensionality budget defined before computation)

### Phase 2: Core Simulation Engines (WASM)
**Rationale:** The computational heart of the platform. Both engines are pure Rust with no UI dependency, testable headlessly. The `core`/`wasm` crate split must be established in this phase to prevent untestable WASM logic (Pitfall 8). Micro and Macro engines are built in parallel as separate crates (anti-pattern: monolithic WASM bundle blocks parallel initialization and cache invalidation). This is the riskiest phase — the TaxBenefitSystem port from OpenFisca's Python logic must be validated via bilingual test suite passing with exact match within 1e-6.

**Delivers:**
- `wasm-microengine-core` crate: TaxBenefitSystem (Entity/Variable/Parameter model), formula evaluator, simulation runner, Reform.apply logic, differential privacy noise injection
- `wasm-microengine-wasm` crate: wasm-bindgen boundary with batch interface (full reform vector as single `&[f64]` slice), Web Worker message handler, `serde-wasm-bindgen` for zero-copy result transfer
- `wasm-macroengine-core` crate: shock matrix loader, multi-linear interpolation with bounds validation (convex hull check, `Option<None>` return for extrapolation), trajectory projection, MemoMap result caching
- `wasm-macroengine-wasm` crate: wasm-bindgen boundary, Web Worker integration
- Dual test suites: `cargo test` (native, proptest property-based) + `wasm-pack test` (boundary serialization only)
- Bilingual validation: identical inputs through OpenFisca Python (reference) and Rust/WASM engine, CI gate on exact match

**Uses stack:** wasm-bindgen 0.2.121, wasm-pack 0.14.0, serde-wasm-bindgen 0.6.5, ndarray 0.17, interpolation 0.3, wasm-bindgen-rayon 1.3  
**Prevents pitfalls:** Pitfall 1 (batch interface avoids serialization tax), Pitfall 2 (bounds validation in interpolation), Pitfall 8 (core/wasm split enables native testing)

### Phase 3: Interactive Simulation Shell (MVP — Milestone 1)
**Rationale:** This is the first user-facing deliverable and the minimum viable product for pre-2027 electoral period testing. Everything in this phase gates on Phase 2 (engines) and Phase 1 (data). Accessibility is a build-time requirement — every chart ships with its HTML table fallback, every slider with WAI-ARIA attributes and keyboard controls, debounced ARIA announcements on drag-end only. This phase must pass screen reader UAT before milestone completion.

**Delivers:**
- React 19 + Vite 6 SPA scaffold with persona routing (Citoyen Explorateur as default, Expert/Chercheur as URL-accessible modes)
- Zustand simulation stores (slider-slice, scenario-slice, chart-slice)
- Slider Controller component: WAI-ARIA `useSlider` integration, dual update strategy (visual at 60fps, ARIA debounced to 500ms on `change`), keyboard step controls, text input fallback, `aria-valuetext` with human-readable formatting
- Web Worker wrappers for micro and macro engines (Double Worker Pattern)
- Simulation Orchestrator: fan-in results from both workers, request deduplication, optimistic chart skeletons
- Basic macro outputs: deficit, debt, GDP growth — D3.js SVG charts with `role="img"`, `aria-labelledby`, pattern fills, sibling HTML `<table>` with `<th scope>`
- Simplified household impact: one synthetic profile type, vulgarisé presentation, power-of-purchase indicator
- Shareable results via URL state encoding (JSON Patch → LZ-String compress → URL fragment)
- Responsive layout (touch targets ≥ 44px, mobile-first Tailwind 4 breakpoints)
- Data attribution & methodology page
- Loading state / "calcul en cours" indicators
- Initial load target: <3s cold, <1s warm (Service Worker + Cache API)

**Addresses features:** All P1 features (tax sliders, household impact, basic macro, real-time feedback, shareable results, responsive, RGAA core, attribution, loading states)  
**Prevents pitfalls:** Pitfall 4 (SVG-first + table fallbacks), Pitfall 5 (debounced ARIA + keyboard controls), Pitfall 10 (accessibility in definition of done, not a later phase)

### Phase 4: Enhanced Data & Distributional Analysis (Milestone 2)
**Rationale:** Once the core simulation loop is validated with users (Milestone 1), this phase adds the differentiators that set Budget Citoyen apart: full synthetic population enabling distributional analysis, advanced macro trajectories, and expert-mode progressive disclosure. The synthetic data pipeline must have its DP budget architecture already designed in Phase 1 — this phase executes it. The shock matrix must respect the dimensionality budget established in Phase 1.

**Delivers:**
- Full 50,000-profile synthetic population generation (CopulaGAN) with DP-SGD training, ε ≤ 1.0 guarantee, privacy budget tracker, pre-noised public aggregates for all dashboard queries
- Refined shock matrix with progressive loading (low-res first for interactivity, high-res streamed on-demand)
- Expert mode dashboard: multi-reform program testing, scenario composition engine, full parameter access with tooltips
- Distributional impact charts (by income decile, age group, region) — D3.js with RGAA 4 pattern differentiation
- Rules as Code transparency view: interactive "show my calculation" tree, parameter provenance
- Data exports (CSV, JSON) — client-side Blob download, no server round-trip
- Progressive disclosure: citizen mode hides advanced parameters, expert mode reveals them progressively with vulgarized tooltips

**Implements:** Persona-specific view composition pattern (full maturity across citizen + expert personas)  
**Addresses features:** All P2 features (synthetic data, shock matrix, expert mode, distributional charts, rules transparency, data exports)  
**Prevents pitfalls:** Pitfall 3 (pre-computed aggregates with one-time DP noise), Pitfall 7 (version coupling CI gate active)

### Phase 5: Platform Expansion & Hardening
**Rationale:** Post-MVP expansion for researcher audience, electoral campaign use cases, and production hardening. Security/privacy audit is a blocking gate before any API launch. AI narrative generation is optional and depends on LLM integration validation. Electoral program comparison depends on actual party programs being published (target: 2027 presidential). This phase also includes the mandatory human RGAA 4 audit before public launch.

**Delivers:**
- Researcher REST API: stateless edge functions (Cloudflare Workers/Deno Deploy), household calculation endpoint, distributional impact by decile, counterfactual analysis, CSV/JSON/GeoPackage exports, rate limiting, no-PII validation middleware
- AI-generated policy impact narrative: LLM-powered plain-language explanation of reform impacts (must work with zero data transfer — either client-side via WebLLM or pre-computed template generation)
- Electoral program comparison tool: load party programs as reform templates, side-by-side macro trajectory comparison
- Security & privacy audit: browser side-channel analysis (WASM timing, memory access patterns, fingerprinting vectors), CSP hardening, `sessionStorage` enforcement, no analytics script verification, CNIL compliance review
- Performance optimization: Parquet/Zstd compression for shock matrix, WASM `.wasm.gz` serving with `Content-Encoding: gzip`, Service Worker aggressive precaching for election-night traffic spikes
- **Human RGAA 4 audit** by a certified auditor — all 106 criteria reviewed, AT user UAT with NVDA+Firefox, JAWS+Chrome, VoiceOver+Safari

**Uses stack:** Expert API edge functions, optional LLM integration  
**Addresses features:** All P3 features (REST API, AI narrative, electoral comparison, circonscription data)  
**Prevents pitfalls:** Pitfall 6 (side-channel audit, CSP hardening, no localStorage), Pitfall 10 (human RGAA audit)

### Phase Ordering Rationale

- **Data before computation:** Phase 1 (data foundation) must precede Phase 2 (WASM engines). Tax rules schema, population format, and shock matrix format are contracts that the engines consume. Building engines without reference data means building against undefined interfaces.
- **Engines before UI:** Phase 2 (WASM engines) must precede Phase 3 (UI). The Double Worker pattern wraps the engines — building UI first forces mock workers that must be thrown away when real engines arrive, doubling work.
- **Core MVP before differentiation:** Phase 3 (MVP shell) delivers the essential simulation loop for early validation. Phase 4 (enhanced data) adds the competitive differentiators. This sequencing de-risks: if the micro engine has issues, stakeholders see something working before the complex synthetic data pipeline is attempted.
- **Hardening gates public launch:** Phase 5 (expansion & hardening) includes the security/privacy audit and human RGAA audit — both are blocking gates that must pass before the platform is launched for real electoral use.
- **Pitfall prevention windows are time-sensitive:** Pits 1 (serialization tax), 2 (extrapolation), 3 (DP budget), 7 (version mismatch), 8 (untestable WASM), and 9 (dimensionality) each have a specific phase where prevention is cheap and retrofitting is expensive. The phase assignments above align prevention with the earliest possible design decisions.

### Research Flags

**Phases needing deeper research (`/gsd-research-phase` during planning):**

- **Phase 1 (Data Foundation):** Mésange model documentation is restricted (MEDIUM confidence source) — specific shock matrix generation methodology needs validation with Insee/Trésor contacts. OpenDP ε=1.0 configuration for copula-based fiscal data has no published reference implementation for the French context — a spike is recommended. OpenFisca-France parameter tree structure needs mapping to Rust `Parameter` indexing.

- **Phase 2 (WASM Engines):** Porting OpenFisca's Python formula evaluation to Rust requires detailed analysis of formula patterns, TAXIPP-style optimization strategies, and conditional parameter indexing. wasm-bindgen-rayon SharedArrayBuffer COOP/COEP header configuration differs per deployment target (needs target-specific spike). The bilingual test suite's canonical profile set needs to be defined with a fiscal expert.

- **Phase 5 (Platform Expansion):** AI narrative generation must resolve whether to use client-side inference (WebLLM — limited model quality) or pre-computed template generation (no real-time adaptability). CNIL-specific privacy audit requirements for the "zero data transfer" claim need legal review. Electoral program comparison template format needs to be designed in consultation with actual party program structures.

**Phases with well-documented patterns (skip research-phase, go to `/gsd-discuss-phase`):**

- **Phase 3 (MVP Shell):** React 19 + D3.js + Vite + WASM Web Worker patterns are extensively documented. The Double Worker pattern is a standard architecture with clear reference implementations in the Rust WASM book and wasm-bindgen guide. RGAA 4 criteria for sliders, charts, and color independence are well-specified with compliance checklists.

- **Phase 4 (Enhanced Data):** CopulaGAN architecture is well-documented in SDV literature. Progressive disclosure UI patterns are standard React patterns. Data export as client-side Blob downloads is a solved problem. The risk is in the data quality validation, not the software patterns.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All versions verified via npm registry and crates.io API on 2026-05-11. React 19.2, Vite 6+, wasm-bindgen 0.2.121, ndarray 0.17 all current. Serde_yaml deprecation confirmed; alternative pipeline validated. D3.js 7.9 confirmed accessible SVG output pattern. |
| Features | HIGH | Competitive analysis verified against live SimuBudget, PolicyEngine, LexImpact, and Institut Montaigne platforms. MVP definition grounded in competitor gaps. Feature dependencies mapped to architectural build order. Anti-features explicitly justified with legal/architectural rationale. |
| Architecture | HIGH | Web Worker + WASM patterns sourced from official wasm-bindgen and Rust WASM book documentation. OpenFisca architecture (Entity/Variable/Parameter) verified via Context7. Data flow and state management patterns use established React+Zustand conventions. Build order derived from explicit dependency analysis. |
| Pitfalls | HIGH | Top 10 pitfalls sourced from official documentation (RGAA 4 criteria, wasm-bindgen guide, CNIL guidance on synthetic data and differential privacy) and academic literature (Dwork et al. on DP, Numerical Recipes on interpolation, Smolyak sparse grid literature). Each pitfall has a prevention strategy and verification checkpoint. |

**Overall confidence: HIGH**

The research is thorough and sourced from primary official documentation, live competitor analysis, and established academic references. The main confidence gaps are in implementation-level details that require domain expert consultation (Mésange model internals, CNIL-specific audit thresholds, OpenFisca formula porting strategy) — these are flagged as research-phase triggers above and are appropriate to resolve during planning phases, not during upfront research.

### Gaps to Address

- **Mésange model source access:** The shock matrix generation methodology references Mésange bootstraps, but model documentation is restricted (Insee/Trésor). During Phase 1 planning, validate whether the published multiplicateur budgétaire values and VAR methodology are sufficient for pre-computation, or whether licensed access to the full Mésange codebase is needed.

- **OpenFisca-France formula porting strategy:** The TaxBenefitSystem architecture assumes a direct port of OpenFisca's Python formula evaluation to Rust. During Phase 2 planning, spike the port of 3-5 representative formulas to validate feasibility and estimate the per-formula porting cost. Some formulas may reference Python-specific patterns (numpy vectorization, dynamic dispatch) that require Rust idiomatic equivalents.

- **CNIL privacy audit scope:** The "zero data transfer" architecture is well-documented, but CNIL's specific requirements for browser-side computation (WASM memory as processing, `sessionStorage` as personal data, side-channel audit scope) need validation with a privacy legal expert before the Phase 5 audit. The synthetic data ε=1.0 guarantee methodology should be reviewed by a DP specialist.

- **RGAA 4 audit capacity:** The HUMAN audit requirement (106 criteria, ~70% of which automated tools cannot verify) requires a certified RGAA auditor. This is a procurement dependency — identify and budget for this during Phase 3 planning so the auditor can review wireframes/designs before implementation begins.

- **Synthetic population base data access:** CopulaGAN training requires real fiscal microdata (ERFS, Filosofi, POTE). Access to Insee's CASD (Centre d'Accès Sécurisé aux Données) or equivalent may require a multi-month approval process. Initiate this during Phase 1 planning — synthetic data generation cannot proceed without training data.

## Sources

### Primary (HIGH confidence)
- **Context7:** `/wasm-bindgen/wasm-pack` (build targets), `/websites/rustwasm_github_io_wasm-bindgen` (JS interop), `/reactjs/react.dev` (React 19 hooks), `/d3/d3` (SVG manipulation), `/vega/vega-lite` (ARIA channels), `/websites/react-aria_adobe` (useSlider), `/websites/sdv_dev_sdv` (CopulaGAN), `/opendp/opendp` (DP mechanisms), `/websites/rs_ndarray_ndarray` (broadcasting), `/tailwindlabs/tailwindcss.com` (v4.0), `/vitejs/vite` (WASM ?init), `/openfisca/openfisca-core` (variable/reform architecture), `/policyengine/policyengine-api` (API patterns)
- **Official npm registry:** Version verification for React 19.2.6, D3.js 7.9.0, Vega-Lite 6.4.3, Tailwind CSS 4.3.0, Vite 8.0.12 (all verified 2026-05-11)
- **crates.io API:** Version verification for wasm-bindgen 0.2.121, serde 1.0.228, ndarray 0.17.2, serde-wasm-bindgen 0.6.5, interpolation 0.3.0, opendp 0.14.2, wasm-bindgen-rayon 1.3.0 (all verified 2026-05-11)
- **W3C/WAI:** Web accessibility fundamentals, custom controls tutorial, WAI-ARIA authoring practices
- **RGAA 4.1.2:** Criteria 1.1, 1.3, Thématiques 3, 8, 11 — French legal requirements for public service digital accessibility
- **GDPR:** Article 4(1) (definition of personal data), Article 25 (Data Protection by Design and by Default)
- **Serde_yaml deprecation:** Confirmed on crates.io — `serde_yaml` 0.9.34+deprecated (last updated 2024-03-25)
- **Rust WASM book:** Debugging, profiling, code size optimization, JS interop patterns
- **Live competitor analysis:** SimuBudget (https://simubudget.org/), PolicyEngine (https://policyengine.org/), LexImpact (https://leximpact.an.fr/), Institut Montaigne méthodologie (accessed 2026-05-11)

### Secondary (MEDIUM confidence)
- **Mésange model documentation (Insee/DGT):** Referenced in PRD Section 4-5. Neo-Keynesian macroeconomic model structure, multiplicateur budgétaire values, VAR bootstrap methodology. MEDIUM confidence because model source code is restricted; analysis based on published methodology papers.
- **Synthetic Data Generation methodology:** Copula-based approaches, GAN/VAE trade-offs, membership inference attack prevention. MEDIUM confidence because specific hyperparameters for French fiscal data require experimental validation.
- **CNIL guidance on browser fingerprinting:** Position on local storage and side channels as personal data processing. MEDIUM confidence because specific thresholds for "reasonable identifiability" in WASM computation context are not formally published.
- **Smolyak sparse grid literature:** Dimensionality reduction techniques for high-dimensional interpolation. MEDIUM confidence because applicability to Mésange-derived shock matrices (vs. standard mathematical functions) needs validation.

### Tertiary (LOW confidence — needs validation)
- **OpenFisca formula porting feasibility:** Assumption that Python formula evaluation logic can be directly ported to Rust. LOW confidence until a representative sample of formulas is ported and validated via bilingual test suite.
- **Mésange shock matrix dimensionality budget:** Assumption that 4 parameter dimensions at moderate grid density provide sufficient accuracy. LOW confidence until sensitivity analysis is performed on the actual Mésange bootstraps.
- **AI narrative generation approach:** Assumption that pre-computed template generation or client-side LLM can produce useful plain-language explanations. LOW confidence until a prototype is evaluated against real simulation outputs.

---

*Research completed: 2026-05-11*
*Ready for roadmap: yes*
