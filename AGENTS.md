<!-- GSD:project-start source:PROJECT.md -->
## Project

**Budget Citoyen**

Un simulateur budgétaire hybride et interactif permettant au grand public et aux équipes de campagne d'évaluer l'impact socio-fiscal et macroéconomique des réformes politiques. La plateforme combine un moteur microéconomique côté client (compilé en WebAssembly pour une exécution locale et privée) avec un moteur macroéconomique pré-calculé (matrice des chocs dérivée du modèle Mésange de l'Insee/Trésor) pour offrir des résultats instantanés sans transfert de données personnelles.

**Core Value:** Permettre à tout citoyen de comprendre en temps réel l'impact budgétaire et macroéconomique d'une réforme fiscale sur son foyer et sur l'économie nationale, sans vocabulaire comptable complexe et sans jamais transmettre ses données personnelles.

### Constraints

- **Performance** : Latence < 200ms pour l'actualisation des graphiques lors de la manipulation des curseurs
- **Sécurité** : Aucune donnée personnelle ne quitte le poste client (Privacy by Design)
- **Accessibilité** : Conformité RGAA 4 (critères 1.1, 1.3, thématiques 3, 8, 11)
- **Tech stack** : Moteur micro en Rust/WASM, interface web, données en JSON/YAML
- **Licence** : Open source (compatible AGPL d'OpenFisca)
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Recommended Stack
### Core Technologies (Frontend)
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| React | 19.2 | UI framework | `useTransition` enables non-blocking slider updates critical for <200ms latency target; largest ecosystem of accessible component libraries; strong TypeScript support; React Aria (Adobe) integration is best-in-class for RGAA 4 compliance |
| TypeScript | 5.8+ | Type safety | Static typing across the WASM-JS bridge eliminates a whole class of runtime bugs when marshalling complex fiscal data structures; `wasm-bindgen` auto-generates `.d.ts` declarations |
| Vite | 6+ | Build tool | Native WASM import via `?init` suffix; sub-second HMR; optimized production builds with code splitting; `vite-plugin-wasm` for edge cases. Vite 5.4+ has stable WASM support, 6+ adds `?init` refinements |
| Tailwind CSS | 4.3 | Styling | CSS-first configuration (`@theme`) eliminates separate config file; zero-runtime utility classes; works seamlessly with unstyled React Aria components; `@property` rules for accessible animations |
| React Aria | (latest) | Accessibility | Unstyled accessible primitives with full WAI-ARIA implementation; `useSlider` hook provides `aria-valuenow`, `aria-valuemin`, `aria-valuemax`, touch + keyboard support, screen reader announcements — all mandatory for RGAA 4 Thematique 11 |
### WASM Microsimulation Engine (Rust)
> **Phase 02 update (2026-05):** Architecture simplified to TypeScript engines for runtime, Python pre-compute for offline computation, Rust core crate for types/validation only. WASM dependencies below are no longer runtime requirements but remain documented for reference.
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| wasm-bindgen | 0.2.121 | JS ↔ WASM interop | The standard bridge. Automatically generates TypeScript `.d.ts` declarations for all exported Rust types; supports `serde-serialize` for complex struct transfer; `wasm-bindgen-rayon` enables multi-threaded WASM |
| wasm-pack | 0.14.0 | WASM build toolchain | One-command build (`wasm-pack build --target web`); generates npm-ready `pkg/` with JS bindings; handles `wasm-opt` optimization pass |
| serde | 1.0.228 | Serialization framework | Derive `Serialize`/`Deserialize` on Rust structs; the standard for all Rust data interchange |
| serde-wasm-bindgen | 0.6.5 | WASM-specific serde | Converts Rust structs ↔ `JsValue` efficiently; avoids JSON stringification overhead between Rust and JS |
| serde_json | 1.0.x | JSON parsing (WASM) | Parses the Rules as Code JSON definitions loaded by the browser; minimal WASM binary size compared to YAML parsers |
| ndarray | 0.17.2 | N-dimensional arrays | Stores pre-computed macroeconomic shock matrices (e.g., 4D tensors: tax_rate × spending × time × indicator); broadcasting operations for efficient matrix computations; slicing for extracting specific projections |
| interpolation | 0.3.0 | Multi-linear interpolation | Performs multi-linear interpolation on shock matrix look-up tables; ~1M downloads, well-tested; converts user slider positions to interpolated macroeconomic projections in microseconds |
| wasm-bindgen-rayon | 1.3.0 | WASM parallelism | Parallelizes microsimulation across 50,000 synthetic profiles using Web Workers + SharedArrayBuffer; critical for keeping batch simulation under 200ms |
### Data Visualization
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| D3.js | 7.9 | Primary visualization library | Full DOM control over SVG elements — essential for RGAA 4 compliance (role="img" on `<svg>`, `aria-labelledby`, adjacent HTML table fallbacks); `selection.join()` pattern for efficient data updates; no abstraction layer blocking accessibility attributes |
| Vega-Lite | 6.4 | Declarative charts (secondary) | Built-in `description` channel auto-maps to `aria-label` attribute on SVG output (`vl2svg`); JSON spec is auditable and human-readable; useful for standardized chart types (time series, bar charts) where D3 would be overkill |
| Observable Plot | (latest) | Exploratory analysis (dev only) | Rapid prototyping of visualizations during development; NOT for production — limited ARIA support compared to D3.js direct control |
### Synthetic Data Generation (Python — Offline/One-Time)
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| SDV (Synthetic Data Vault) | 2.x | Synthetic population generation | `CopulaGANSynthesizer` models multi-variable dependencies (age↔patrimony↔income covariance); copula-based approach is the state-of-the-art for fiscal data as described in the PRD; `HMASynthesizer` handles hierarchical/multi-table data if needed |
| OpenDP | 0.14.2 (Rust core) | Differential privacy guarantees | Production-ready differential privacy library; Rust core usable from Python via `opendp` package; Laplace and Gaussian mechanisms with formal ε-differential privacy proofs; directly addresses CNIL requirements about inference attack prevention |
| SDMetrics | (latest) | Synthetic data quality evaluation | Statistical fidelity metrics, privacy metrics, and detection reports; validates that synthetic data preserves real-world distributions without overfitting |
### Rules as Code Format & Validation
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| YAML | N/A | Human-readable rule authoring | Supports comments (unlike JSON), visually clean syntax for legal experts; OpenFisca ecosystem standard; enables "audit by non-programmers" |
| JSON Schema | Draft 2020-12 | Rule schema validation | Validates structure of fiscal parameter files at build time; ensures all required fields (rates, thresholds, brackets) are present before they reach the WASM engine |
| valico | 4.0.0 | Rust JSON Schema validator | Validates rule files in CI/CD and optionally at runtime in WASM; fast, well-maintained |
| jsonschema (Python) | 4.x | Build-time validation | Validates YAML→JSON converted rules during the data pipeline; Python ecosystem is richer for YAML tooling than Rust |
### Testing & Quality
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Vitest | 3.x | Unit/integration tests | Vite-native, fast parallel execution, snapshot testing, WASM-compatible via jsdom |
| Playwright | 1.x | E2E + accessibility testing | Built-in `@playwright/test` accessibility assertions; screen reader emulation; multi-browser testing (Chromium, Firefox, WebKit); checks aria-labels, roles, and contrast ratios |
| wasm-bindgen-test | 0.3.x | Rust WASM tests | Runs Rust tests in a browser context via headless Chromium; validates WASM engine correctness end-to-end |
| Storybook | 9.x | Component development | Isolated development of React Aria components; accessibility addon for axe-core audits in dev |
## Installation
# Frontend core
# Build tooling
# Data visualization
# Testing
# WASM integration
# Rust/Cargo.toml (microsimulation engine)
# Python (synthetic data pipeline — offline)
## Alternatives Considered
| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| React 19 + React Aria | Svelte 5 | Svelte has smaller bundles and simpler reactivity, but its accessibility ecosystem is immature compared to React Aria. Use Svelte ONLY if team has existing Svelte expertise and you accept building ARIA components from scratch |
| React 19 + React Aria | SolidJS | SolidJS offers better raw performance than React, but lacks React Aria and the mature accessible component ecosystem. The 200ms latency target is easily achievable in React with useTransition |
| D3.js 7 | Vega-Lite 6 (for everything) | Vega-Lite is excellent for standard charts but cannot match D3's fine-grained ARIA control needed for RGAA 4 compliance. Use Vega-Lite for 80% of charts, D3 for the 20% that need custom accessibility |
| Tailwind CSS 4 | CSS Modules / styled-components | CSS Modules work fine but add maintenance overhead. Tailwind's utility classes compose naturally with React Aria's unstyled components without fighting specificity |
| Vitest | Jest | Jest works but requires complex WASM mocking setup. Vitest shares Vite's config and transforms, making WASM testing seamless |
| ndarray + interpolation (Rust) | NumPy/SciPy (Python server) | Python would require server round-trips, violating the privacy-by-design constraint. All computation must happen client-side in WASM |
## What NOT to Use
| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Chart.js | Canvas-based rendering — inherently inaccessible for screen readers. No native ARIA support on `<canvas>` elements. Would require duplicating all data into hidden HTML tables, doubling maintenance | D3.js 7 (SVG with full DOM accessibility) or Vega-Lite 6 (declarative with `aria-label` on SVG output) |
| ECharts | Also Canvas-first by default; SVG mode lacks full ARIA support; very heavy bundle (~1MB) for a platform targeting <200ms interactivity | D3.js 7 for custom charts, Vega-Lite 6 for standard ones |
| Shadcn UI / Radix Primitives (alone) | Radix primitives provide good accessibility basics but lack the advanced screen-reader value formatting and internationalization that React Aria's `useSlider` provides for range sliders | React Aria for interactive controls (sliders, number inputs); Tailwind CSS for styling |
| serde_yaml (Rust crate) | Officially deprecated at v0.9.34 (since March 2024). The fork `serde_yml` (0.0.12) exists but is immature | Build-time YAML→JSON conversion; parse JSON in WASM via `serde_json`. This avoids the YAML parser dependency entirely at runtime, keeping WASM binary smaller |
| OpenFisca (Python) for runtime | Server-side execution requires data transmission, violating privacy-by-design. Python interpreter cannot run in browser efficiently | Rust/WASM engine inspired by OpenFisca's Rules as Code paradigm, compiled for client-side execution |
| Vite 7 or 8 (if unstable) | Vite releases major versions rapidly; version numbers may exceed stability. At time of research, Vite 8.0.12 is latest on npm but feature set is most proven on Vite 6.x stable track | **Use Vite 6+** (minimum). The WASM `?init` feature has been stable since Vite 4. Pinning to a specific major avoids churn |
## Version Compatibility
| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| React 19.2 | React Aria (latest), Tailwind CSS 4.3 | React 19 uses the new JSX transform; ensure `@vitejs/plugin-react` is v6+ |
| Vite 6.x | vite-plugin-wasm (latest), @vitejs/plugin-react 6.x | WASM `?init` is built-in since Vite 4; no plugin needed for standard WASM imports |
| wasm-bindgen 0.2.121 | serde-wasm-bindgen 0.6.5, wasm-pack 0.14.0 | Version alignment is critical — always use latest patch of all three together |
| ndarray 0.17 | interpolation 0.3 | interpolation crate accepts `&[f64]` slices; use `ndarray::ArrayView::as_slice()` methods for zero-copy access |
| D3.js 7.9 | TypeScript 5.8 | `@types/d3` is maintained separately; D3 7 ships partial types natively |
| Tailwind CSS 4.3 | @tailwindcss/vite 4.x | Tailwind 4 uses Vite plugin instead of PostCSS config; the `@theme` directive replaces `tailwind.config.js` |
## Stack Patterns by Variant
- Use `wasm-bindgen-rayon` with `SharedArrayBuffer`
- Requires COOP/COEP headers on the deployment server
- Enables parallel profile simulation (processing 50K profiles in batches across multiple Web Workers)
- Fallback: single-threaded WASM if COOP/COEP headers cannot be configured (some static hosting)
- Use `wasm-pack build --target web` (ES modules, no bundler required)
- The Vite dev server handles WASM automatically; production builds inline WASM < 4KB or serve as static assets
- COOP/COEP headers for parallel WASM require server configuration — test on target platform early
- Keep as an offline Python pipeline
- Pre-generate the 50,000 synthetic profiles as static JSON
- Serve as compressed static assets (gzip/brotli) from the CDN
- Load into WASM on first access, cache via `CacheStorage`
## Sources
- **Context7** — `/wasm-bindgen/wasm-pack` (wasm-pack builds and targets), `/websites/rustwasm_github_io_wasm-bindgen` (serde-wasm-bindgen integration), `/reactjs/react.dev` (React 19 hooks including useTransition), `/d3/d3` (selection.join pattern, SVG manipulation), `/vega/vega-lite` (aria-label channel, SVG output), `/websites/react-aria_adobe` (useSlider hook, ARIA attributes), `/websites/sdv_dev_sdv` (CopulaGANSynthesizer, HMASynthesizer), `/opendp/opendp` (differential privacy mechanisms), `/websites/rs_ndarray_ndarray` (broadcasting, slicing), `/tailwindlabs/tailwindcss.com` (v4.0 CSS-first configuration), `/vitejs/vite` (WASM ?init, documentation)
- **Official npm registry** — Version verification for React 19.2.6, D3.js 7.9.0, Vega-Lite 6.4.3, Tailwind CSS 4.3.0, Vite 8.0.12, Chart.js 4.5.1, ECharts 6.0.0 (verified 2026-05-11)
- **crates.io API** — Version verification for wasm-bindgen 0.2.121, serde 1.0.228, ndarray 0.17.2, serde-wasm-bindgen 0.6.5, interpolation 0.3.0, opendp 0.14.2, wasm-bindgen-rayon 1.3.0 (verified 2026-05-11)
- **PRD research document** — Architectural requirements (WASM compilation, multi-linear interpolation, RGAA 4 criteria), OpenFisca/PolicyEngine comparison, Mésange model methodology, synthetic data approaches (copulas, GAN, VAE), differential privacy requirements (verified against project docs)
- **serde_yaml deprecation** — Confirmed on crates.io: `serde_yaml` 0.9.34+deprecated (last updated 2024-03-25). The maintained fork is `serde_yml` 0.0.12 but this architecture avoids YAML dependency at WASM runtime
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
