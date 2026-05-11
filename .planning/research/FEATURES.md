# Feature Research

**Domain:** Civic budget simulation platform (simulateur budgétaire citoyen interactif)
**Researched:** 2026-05-11
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete or untrustworthy.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Tax slider controls for major fiscal levers (IR, IS, TVA, cotisations) | SimuBudget and PolicyEngine both use sliders; users expect immediate manipulation of rates | MEDIUM | Must be real-time (< 200ms latency per PROJECT.md constraint). WAI-ARIA accessible (aria-valuenow, role="slider"). |
| Real-time feedback on budget impact (receipts, deficit, debt) | SimuBudget shows deficit/dette/pouvoir d'achat updating instantly. This is the core interaction loop. | MEDIUM | Tied to slider engine. Must recalc on every slider change. |
| Deficit and debt trajectory display | Every budget simulator shows these as primary outputs; users expect to see "where the money goes" | MEDIUM | Line/area charts for 5-year projections. Must have RGAA-compliant alternatives. |
| Simplified household impact calculator (vulgarisé) | LexImpact and PolicyEngine both let you see impact on a "cas type". Citizens won't use it otherwise. | HIGH | Requires the microsimulation engine. This is the hardest table-stakes feature. |
| Power-of-purchase impact indicator | SimuBudget has "Votre pouvoir d'achat" as a key output. Essential for citizen engagement. | LOW | Once microsim works, this is a derived output. |
| Public service quality indicator | SimuBudget has "Qualité des services publics" score. Sets expectations for budget trade-offs. | LOW | Simple weighted index from spending levels. |
| "Reset" button for simulation state | Universally expected in interactive simulators | LOW | Pure UI state management. |
| Shareable simulation results (link, image export) | SimuBudget has copy-link, create-image, email. Users expect to share results on social media. | MEDIUM | Requires URL state encoding + server-side image rendering or canvas export. |
| Data source attribution and methodology transparency | Institut Montaigne and LexImpact both emphasize methodology transparency. Critical for trust in public service. | LOW | Static content page + footer attribution. Must cite Insee, budget.gouv.fr, Mésange model. |
| Mobile-responsive layout | SimuBudget works on mobile. 60%+ of French civic engagement traffic is mobile during electoral periods. | MEDIUM | Responsive design from day 1. Sliders need touch targets ≥ 44px. |
| Loading state / "calcul en cours" indicator | PolicyEngine shows "computing" status. Users expect feedback during async calculations. | LOW | Standard UI pattern. Important for macro engine loads. |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable. Directly aligned with PROJECT.md Core Value.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Dual-mode simulation: micro (household) + macro (national) in single interaction** | No existing platform combines both. SimuBudget = macro only. LexImpact = micro only. PolicyEngine = micro only (economy-wide via aggregation). Budget Citoyen offers both simultaneously. | VERY HIGH | Requires WASM micro engine + pre-computed shock matrix + interpolation engine. Core architectural challenge. |
| **Privacy by Design: zero data transfer architecture** | All competitors send household data to servers. Budget Citoyen keeps everything in-browser via WASM. This is a hard legal requirement but also a unique trust advantage. | HIGH | WASM compilation of Rust microsim engine. No server-side personal data processing. Simplifies RGPD compliance. |
| **Synthetic population data (50,000 profiles) for distributional analysis** | No French platform offers this. PolicyEngine has it for US/UK but not France. Enables "who wins, who loses" by income decile without real taxpayer data. | VERY HIGH | Requires synthetic data generation pipeline (copulas, GAN, VAE) with differential privacy guarantees (epsilon budget tracking). |
| **RGAA 4 native accessibility** | Neither SimuBudget, LexImpact, nor the Institut Montaigne platforms meet RGAA 4. This is a legal requirement for public service but also a differentiator for inclusion. | HIGH | SVG with role="img" + aria-labelledby, Canvas fallback to `<table>`, animation controls (thématique 8), pattern-based data distinction (thématique 3), WAI-ARIA sliders (thématique 11). Built from design phase, not retrofitted. |
| **Expert mode with full reform program testing** | SimuBudget only offers pre-set policy toggles. LexImpact is limited to single amendments. Budget Citoyen lets experts stack multiple reforms and see combined trajectories. | HIGH | Requires scenario composition engine + shock matrix interpolation with multi-reform interaction effects. |
| **REST API with counterfactual analysis endpoint** | Only PolicyEngine offers a comparable API (US/UK only). Budget Citoyen's API targets French researchers with micro-data extraction, decile analysis, and counterfactual queries. | HIGH | API must expose: household calculation, distributional impact by decile, counterfactual scenario comparison, data exports (CSV, JSON, GeoPackage for circo-level). |
| **Rules as Code (YAML/JSON) auditable legislation** | OpenFisca pioneered this but the rules aren't consumer-visible. Budget Citoyen exposes the legislative logic in human-readable YAML that journalists and citizens can audit. | MEDIUM | Requires OpenFisca-compatible parameter serialization + a "show my calculation" tree view in the UI. |
| **Multi-persona progressive disclosure** | No existing platform adapts to user expertise level. Budget Citoyen offers: Citizen Explorer (vulgarisé), Expert/Media (advanced parameters), Analyst/Researcher (API + raw data). | MEDIUM | UI has mode switcher. Progressive complexity reveals (advanced parameters hidden in Citizen mode, visible in Expert mode). |
| **AI-generated policy impact narrative** | PolicyEngine has `/simulation-analysis` endpoint using Claude for narrative generation. Budget Citoyen adds this as a differentiator: plain-language explanation of what a reform means. | MEDIUM | Requires LLM integration with structured simulation output. Must work client-side (no data transfer) or use pre-computed template generation. |
| **Electoral program comparison tool** | Institut Montaigne does this manually. Budget Citoyen lets users load candidate programs side-by-side and compare macro trajectories. | HIGH | Requires program template engine + multi-scenario comparison view. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| User accounts and personal data storage | "Let users save their simulations" | Violates Privacy by Design architecture, requires RGPD consent management, data breach liability, server infrastructure cost. Explicitly out of scope per PROJECT.md. | URL-based state sharing (all simulation params encoded in URL). LocalStorage for recent simulations (browser-only). |
| Real-time tax rate scraping from legislation | "Keep the simulator always up to date" | French tax code changes via Loi de Finances annually + amendments. Real-time scraping is fragile and creates legal liability if outdated. | Scheduled annual update cycle aligned with PLF calendar. Version-pinned parameter files. Clear "last updated" date on all outputs. |
| Live stock market interest rate integration | "Show true cost of debt" | Interest rates (OAT) fluctuate intraday. Introducing market volatility creates noise that obscures policy impact. Explicitly out of scope per PROJECT.md. | Smoothed constant rates derived from Banque de France projections. Updated semi-annually. |
| AI chatbot for fiscal advice | "Help citizens understand what to do" | Enters regulated financial advice territory (conseil fiscal). Creates legal risk. AI hallucinations could give wrong tax advice. | Pre-written educational content validated by economists. "Show my calculation" transparency feature. |
| Individual taxpayer data matching | "Make it accurate for MY situation" | Requires access to DGFiP databases (illegal). Creates re-identification risk. Violates Privacy by Design. | Synthetic data matching: user inputs are matched to closest synthetic profile in the 50,000-profile dataset. |
| Gamification / budget "scores" | "Make it engaging like a game" | Gamification trivializes serious fiscal choices. "High score" incentives bias results. Undermines credibility as a public service tool. | Educational progress indicators (e.g., "You've explored 3 of 7 fiscal levers"). Contextual learning tips. |
| Real-time collaborative simulation | "Let groups negotiate budgets together" | Requires WebSocket infrastructure, session management, conflict resolution. Massive complexity for marginal value in v1. | Async sharing via URL. Program comparison tool covers multi-party use case. |
| Blockchain-based audit trail | "Immutable record of simulations" | Blockchain adds complexity, energy cost, and user friction without meaningful benefit. Existing transparency measures (open source, methodology docs, data attribution) are sufficient. | Open source code repository. Methodology page with data provenance. Reproducible parameter snapshots. |

## Feature Dependencies

```
[Tax Slider Controls]
    ├── requires──> [Microsim Engine (WASM)] — sliders drive parameter changes
    ├── requires──> [RGAA Slider Accessibility] — legal compliance
    └── enhances──> [Real-time Feedback] — the feedback IS the slider output

[Household Impact Calculator]
    ├── requires──> [Microsim Engine (WASM)] — computational core
    ├── requires──> [Synthetic Population Data] — distributional reference
    └── requires──> [RGAA Data Visualization] — all charts must be accessible

[Macro Trajectory Engine]
    ├── requires──> [Shock Matrix Interpolation] — avoids real-time Mésange solving
    └── feeds──> [Expert Mode Reform Programs] — multi-reform stacking

[Expert Mode]
    ├── requires──> [Microsim Engine]
    ├── requires──> [Macro Trajectory Engine]
    └── requires──> [Scenario Composition Engine] — multi-reform UI

[Researcher API]
    ├── requires──> [Microsim Engine] — for household calculations
    ├── requires──> [Synthetic Population Data] — for distributional queries
    └── requires──> [Counterfactual Analysis Engine] — for what-if comparisons

[Shareable Results]
    ├── requires──> [URL State Encoding] — serializable simulation state
    └── enhances──> [Electoral Program Comparison] — sharing is how comparison happens

[AI Narrative Generation]
    └── depends on──> [Micro + Macro Outputs] — needs results to explain them
```

### Dependency Notes

- **Household Impact Calculator requires Synthetic Population Data:** Without reference data, the calculator can only show the user's own inputs—not position them relative to the population.
- **Expert Mode requires Scenario Composition Engine:** Multi-reform stacking is what differentiates expert mode from citizen mode. This composition must handle interaction effects between reforms.
- **Macro Trajectory Engine must precede Expert Mode:** The shock matrix and interpolation must be built before expert-level reform stacking can be tested.
- **Researcher API heavily depends on Counterfactual Analysis Engine:** The key API value proposition (counterfactual queries) requires infrastructure for running "what if" scenarios against the synthetic dataset.
- **Shareable Results enhances Electoral Program Comparison:** The sharing mechanism is the conduit through which program comparison becomes social/viral during electoral campaigns.

## MVP Definition

### Launch With (v1 — Milestone 1)

Minimum viable product — what's needed to validate the concept during pre-2027 testing.

- [ ] **Tax Slider Controls (IR, IS, TVA, cotisations)** — Core interaction mechanism; without this there is no product.
- [ ] **Microsim Engine (WASM)** — Computational heart; all calculations depend on it.
- [ ] **Simplified Household Impact (Citizen Explorer mode)** — The "why should I care" hook. One synthetic profile type.
- [ ] **Basic Macro Outputs (deficit, debt, basic trajectory)** — The "national picture" that grounds the simulation.
- [ ] **Real-time Feedback (< 200ms)** — Performance is a feature; without it the experience fails.
- [ ] **Shareable Results (URL encoding)** — Virality vector for electoral period traffic.
- [ ] **Responsive Layout (mobile + desktop)** — 60%+ mobile traffic expected.
- [ ] **RGAA 4 Compliance (Core)** — Legal requirement, non-negotiable. Sliders, basic charts, color independence.
- [ ] **Data Attribution & Methodology Page** — Trust foundation.

### Add After Validation (v1.1 — Milestone 2)

Features to add once core simulation is working and validated.

- [ ] **Synthetic Population Data Pipeline (50K profiles)** — Enables distributional analysis; trigger: micro engine validated.
- [ ] **Shock Matrix + Macro Interpolation Engine** — Enables full macro trajectories; trigger: basic macro outputs validated.
- [ ] **Expert Mode (multi-reform program testing)** — Trigger: scenario composition UI ready.
- [ ] **Distributional Impact Charts (by decile)** — Requires synthetic data pipeline.
- [ ] **Rules as Code Transparency View** — "Show my calculation" tree.
- [ ] **Data Exports (CSV, JSON)** — First researcher-facing feature.

### Future Consideration (v2+ — Post-MVP)

Features to defer until product-market fit is established.

- [ ] **Researcher REST API** — Requires stable data model and API design. Trigger: research community demand.
- [ ] **Counterfactual Analysis Endpoint** — Requires full API + synthetic data pipeline maturity.
- [ ] **AI-Generated Policy Narrative** — Trigger: LLM integration validated, user demand for plain-language explanation.
- [ ] **Electoral Program Comparison Tool** — Trigger: actual party programs published for 2027.
- [ ] **Circonscription-Level Data Dashboard** — LexImpact has this; valuable but complex (GeoPackage, Shapefile).
- [ ] **Advanced Persona: Analyst/Researcher Full Mode** — Triggers when API is stable.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Tax Slider Controls | HIGH | MEDIUM | P1 |
| Microsim Engine (WASM) | HIGH | VERY HIGH | P1 |
| Simplified Household Impact | HIGH | HIGH | P1 |
| Basic Macro Outputs | HIGH | HIGH | P1 |
| Real-time Feedback (< 200ms) | HIGH | MEDIUM | P1 |
| Shareable Results (URL) | HIGH | MEDIUM | P1 |
| Responsive Layout | HIGH | MEDIUM | P1 |
| RGAA 4 Core Compliance | HIGH | HIGH | P1 |
| Data Attribution Page | MEDIUM | LOW | P1 |
| Synthetic Population Data | HIGH | VERY HIGH | P2 |
| Shock Matrix / Macro Engine | HIGH | VERY HIGH | P2 |
| Expert Mode | MEDIUM | HIGH | P2 |
| Distributional Impact Charts | HIGH | HIGH | P2 |
| Rules as Code Transparency | MEDIUM | MEDIUM | P2 |
| Data Exports (CSV, JSON) | MEDIUM | LOW | P2 |
| Researcher API | MEDIUM | HIGH | P3 |
| AI Narrative Generation | LOW | MEDIUM | P3 |
| Electoral Program Comparison | MEDIUM | HIGH | P3 |
| Circonscription Data | LOW | VERY HIGH | P3 |

**Priority key:**
- P1: Must have for launch (Milestone 1)
- P2: Should have, add when core validated (Milestone 2)
- P3: Nice to have, future consideration (v2+)

## Competitor Feature Analysis

| Feature | SimuBudget | LexImpact | PolicyEngine | Institut Montaigne | Budget Citoyen |
|---------|------------|-----------|--------------|---------------------|----------------|
| Tax sliders | Yes (discrete toggles) | No (form inputs) | No (parameter overrides) | No | Yes (continuous sliders) |
| Household impact | No (macro only) | Yes (cas types) | Yes (full household calc) | No | Yes (vulgarisé + detailed) |
| Macroeconomic trajectories | Simplified deficit/debt only | No | Economy-wide via microsim aggregation | One-time costing, no trajectory | Yes (5-year projections via shock matrix) |
| Privacy by Design (no server data) | No (server-side PHP) | No (OpenFisca server) | No (API calls to server) | N/A (manual analysis) | Yes (WASM edge computing) |
| RGAA 4 accessibility | No | Partial | No (US-focused, not RGAA) | No | Yes (built from design phase) |
| Expert/advanced mode | No | Parliamentarians only | Research/API mode | Expert analysis (manual) | Yes (progressive disclosure) |
| Public REST API | No | No | Yes (US/UK) | No | Planned (France-focused) |
| Synthetic population data | No | No | Yes (US/UK survey data) | No | Yes (50K profiles, DP-guaranteed) |
| Rules as Code auditable | No | Yes (OpenFisca) | Yes (policyengine-core) | No (manual methodology) | Yes (YAML parameters + tree view) |
| Program comparison | No | No | Policy reform vs baseline | Manual party program comparison | Planned (multi-program overlay) |
| AI narrative generation | No | No | Yes (Claude-based) | No | Planned |
| Mobile responsive | Yes | No | Partial | No | Yes |
| Open source | No (source not published) | Yes (AGPL-3.0) | Yes (AGPL-3.0) | No (proprietary methodology) | Yes (AGPL-compatible) |
| Multi-language | FR only | FR only | EN only | FR only | FR (primary), EN (research API) |
| Data exports | No | Limited | Python package + API JSON | PDF reports | CSV, JSON, GeoPackage (planned) |

**Key competitive insight:** No platform combines micro household impact AND macro trajectory in a single interaction. SimuBudget is macro-only. LexImpact is micro-only. PolicyEngine does micro then aggregates for macro, but doesn't do macroeconometric modeling (Mésange-style). Budget Citoyen's hybrid architecture fills this gap.

## Sources

- **SimuBudget** — https://simubudget.org/ (accessed 2026-05-11). French budget simulator with tax toggles and simplified macro outputs. Confidence: HIGH.
- **PolicyEngine** — https://policyengine.org/ (accessed 2026-05-11). US/UK tax-benefit microsimulation platform with household API, economy-wide analysis, and AI narrative. Confidence: HIGH.
- **PolicyEngine API** — Context7 documentation via `/policyengine/policyengine-api`. Two usage patterns: household calculation and economy-wide microsimulation. Confidence: HIGH.
- **LexImpact** — https://leximpact.an.fr/ and https://labo.societenumerique.gouv.fr/ (accessed 2026-05-11). French parliamentary microsimulation tool built on OpenFisca. Confidence: HIGH.
- **OpenFisca Core** — Context7 documentation via `/openfisca/openfisca-core`. Microsimulation engine with REST API, Rules as Code paradigm, YAML/JSON parameter serialization. Confidence: HIGH.
- **Institut Montaigne — Méthodologie Législatives 2024** — https://www.institutmontaigne.org/legislatives-2024/index.php/methodologie/ (accessed 2026-05-11). Manual program costing methodology with constitutional, European, and comparative analysis. Confidence: HIGH.
- **PROJECT.md and prd-research.md** — Internal project documentation defining Core Value, Requirements, Constraints, and architectural decisions. Confidence: HIGH.

---

*Feature research for: simulateur budgétaire citoyen interactif (Budget Citoyen)*
*Researched: 2026-05-11*
